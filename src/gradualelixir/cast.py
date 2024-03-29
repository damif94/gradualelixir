import typing as t
from dataclasses import dataclass

from gradualelixir import expression, gtypes, module, pattern


@dataclass
class AnnotatedPattern(pattern.Pattern):
    pattern: expression.Expression
    type: gtypes.Type

    def __str__(self):
        return f"({self.pattern} | {self.type})"


@dataclass
class AnnotatedExpression(expression.Expression):
    expression: expression.Expression
    type: gtypes.Type

    def __str__(self):
        return f"({self.expression} | {self.type})"


@dataclass
class CastAnnotatedExpression(expression.Expression):
    expression: expression.Expression
    left_type: gtypes.Type
    right_type: gtypes.Type

    def __init__(self, expression: "expression.Expression", left_type: gtypes.Type, right_type: gtypes.Type):
        self.left_type = left_type
        self.right_type = right_type
        self.expression = expression

    def __str__(self):
        if self.left_type == self.right_type:
            return str(self.expression)
        return f"({self.expression} | {self.left_type} ~> {self.right_type})"


@dataclass
class AnnotatedModule:
    name: str
    annotated_definitions: t.List[t.Tuple[module.Spec, module.Definition]]
    specs: t.List[module.Spec]

    def __str__(self):
        msg = f"defmodule {self.name} do\n"
        msg += "  use UseCast\n\n"
        specs_set = set()
        for spec in self.specs:
            specs_set.add((spec.name, spec.arity))
        processed_definitions: t.Set[t.Tuple[str, int]] = set()
        for definition in self.annotated_definitions:
            if (d := (definition[1].name, definition[1].arity)) in processed_definitions or d not in specs_set:
                msg += f"{definition[1]}\n\n"
            else:
                msg += f"{definition[0]}\n{definition[1]}\n\n"
            processed_definitions.add((definition[1].name, definition[1].arity))
        msg += "end"
        return msg


def translate_expression_types(type_derivation: expression.ExpressionTypeCheckSuccess, **kwargs) -> expression.Expression:
    expr = type_derivation.expression
    if isinstance(expr, expression.IdentExpression):
        if kwargs.get("skip_ident"):
            return expr
        return AnnotatedExpression(expr, type_derivation.type)
    if isinstance(expr, expression.LiteralExpression):
        return expr
    if isinstance(expr, expression.ElistExpression):
        return expr
    if isinstance(expr, expression.ListExpression):
        return AnnotatedExpression(
            expression=expression.ListExpression(
                head=translate_expression_types(type_derivation.children["head"]),
                tail=translate_expression_types(type_derivation.children["tail"]),
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.TupleExpression):
        return AnnotatedExpression(
            expression=expression.TupleExpression(
                items=[
                    translate_expression_types(type_derivation.children["items"][i], skip_ident=True)
                    for i in range(len(expr.items))
                ]
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.MapExpression):
        keys_with_positions = [(k, list(expr.map.keys()).index(k)) for k in expr.map.keys()]
        return AnnotatedExpression(
            expression=expression.MapExpression(
                map=expression.OrderedDict(
                    {
                        k: translate_expression_types(type_derivation.children["map"][pos], skip_ident=True)
                        for k, pos in keys_with_positions
                    }
                )
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.UnaryOpExpression):
        annotated_argument = translate_expression_types(type_derivation.children["argument"], skip_ident=True)
        return AnnotatedExpression(
            expression=expression.UnaryOpExpression(
                op=expr.op, argument=AnnotatedExpression(annotated_argument, type_derivation.children["argument"].type)
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.BinaryOpExpression):
        annotated_left = translate_expression_types(type_derivation.children["left"], skip_ident=True)
        annotated_right = translate_expression_types(type_derivation.children["right"], skip_ident=True)
        return AnnotatedExpression(
            expression=expression.BinaryOpExpression(op=expr.op, left=annotated_left, right=annotated_right),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.PatternMatchExpression):
        annotated_expression = translate_expression_types(type_derivation.children["expression"])
        return AnnotatedExpression(
            expression=expression.PatternMatchExpression(expr.pattern, annotated_expression),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.IfElseExpression):
        # TODO[personal] PR walrus operator type inference mypy
        annotated_condition = translate_expression_types(type_derivation.children["condition"])
        annotated_if_clause = translate_expression_types(type_derivation.children["if_clause"])
        annotated_else_clause = translate_expression_types(type_derivation.children["else_clause"])
        return AnnotatedExpression(
            expression=expression.IfElseExpression(
                condition=annotated_condition,
                if_clause=annotated_if_clause,
                else_clause=annotated_else_clause,
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.SeqExpression):
        annotated_left = translate_expression_types(type_derivation.children["left"])
        annotated_right = translate_expression_types(type_derivation.children["right"])
        return expression.SeqExpression(annotated_left, annotated_right)
    if isinstance(expr, expression.CondExpression):
        annotated_cond_clauses = []
        for cond_type_derivation, do_type_derivation in type_derivation.children["clauses"]:
            annotated_cond = translate_expression_types(cond_type_derivation)
            annotated_do = translate_expression_types(do_type_derivation)
            annotated_cond_clauses.append((annotated_cond, annotated_do))
        return AnnotatedExpression(
            expression=expression.CondExpression(annotated_cond_clauses), type=type_derivation.type
        )
    if isinstance(expr, expression.CaseExpression):
        annotated_test = translate_expression_types(type_derivation.children["test"])
        annotated_case_clauses: t.List[t.Tuple[pattern.Pattern, expression.Expression]] = []
        for pattern_match_type_derivation, do_type_derivation in type_derivation.children["clauses"]:
            annotated_do = translate_expression_types(do_type_derivation)
            annotated_case_clauses.append((pattern_match_type_derivation.pattern, annotated_do))
        return AnnotatedExpression(
            expression=expression.CaseExpression(annotated_test, annotated_case_clauses), type=type_derivation.type
        )
    if isinstance(expr, expression.AnonymizedFunctionExpression):
        return AnnotatedExpression(expression=expr, type=type_derivation.type)
    if isinstance(expr, expression.FunctionCallExpression):
        annotated_arguments = []
        for argument_type_derivation in type_derivation.children["arguments"]:
            annotated_argument = translate_expression_types(argument_type_derivation)
            annotated_arguments.append(annotated_argument)
        return AnnotatedExpression(
            expression=expression.FunctionCallExpression(
                function_name=expr.function_name, arguments=annotated_arguments
            ),
            type=type_derivation.type,
        )
    else:
        assert isinstance(expr, expression.AnonCallExpression)
        annotated_arguments = []
        for argument_type_derivation in type_derivation.children["arguments"]:
            annotated_argument = translate_expression_types(argument_type_derivation)
            annotated_arguments.append(annotated_argument)

        function_type = type_derivation.children["function"].type
        assert isinstance(function_type, gtypes.FunctionType) or isinstance(function_type, gtypes.AnyType)
        return AnnotatedExpression(
            expression=expression.AnonCallExpression(
                function=translate_expression_types(type_derivation.children["function"]), arguments=annotated_arguments,
            ),
            type=type_derivation.type,
        )


def cast(expression: expression.Expression, left_type: gtypes.Type, right_type: gtypes.Type) -> expression.Expression:
    right_type = gtypes.merge_operator(left_type, right_type)
    if left_type == right_type:
        return expression
    else:
        return CastAnnotatedExpression(expression, left_type, right_type)


def translate_expression_casts(type_derivation: expression.ExpressionTypeCheckSuccess) -> expression.Expression:
    expr = type_derivation.expression
    if isinstance(expr, expression.IdentExpression):
        return expr
    if isinstance(expr, expression.LiteralExpression):
        return expr
    if isinstance(expr, expression.ElistExpression):
        return expr
    if isinstance(expr, expression.ListExpression):
        assert isinstance(type_derivation.type, gtypes.ListType)
        return expression.ListExpression(
            head=cast(
                expression=translate_expression_casts(type_derivation.children["head"]),
                left_type=type_derivation.children["head"].type,
                right_type=type_derivation.type.type
            ),
            tail=cast(
                expression=translate_expression_casts(type_derivation.children["tail"]),
                left_type=type_derivation.children["tail"].type,
                right_type=type_derivation.type
            )
        )
    if isinstance(expr, expression.TupleExpression):
        return expression.TupleExpression(
            [translate_expression_casts(type_derivation.children["items"][i]) for i in range(len(expr.items))]
        )
    if isinstance(expr, expression.MapExpression):
        keys_with_positions = [(k, list(expr.map.keys()).index(k)) for k in expr.map.keys()]
        return expression.MapExpression(
            map=expression.OrderedDict(
                {k: translate_expression_casts(type_derivation.children["map"][pos]) for k, pos in keys_with_positions}
            )
        )
    if isinstance(expr, expression.UnaryOpExpression):
        annotated_argument = translate_expression_casts(type_derivation.children["argument"])
        maximal_argument_for_type = expr.op.maximal_argument_type
        right_type = gtypes.merge_operator(type_derivation.children["argument"].type, maximal_argument_for_type)
        if isinstance(any := type_derivation.children["argument"].type, gtypes.AnyType):
            annotated_argument = cast(
                annotated_argument, left_type=any, right_type=right_type
            )
            return cast(
                expression=expression.UnaryOpExpression(op=expr.op, argument=annotated_argument),
                left_type=expr.op.get_return_type(right_type),
                right_type=expr.op.get_return_type(type_derivation.children["argument"].type)
            )
        return expression.UnaryOpExpression(op=expr.op, argument=annotated_argument)
    if isinstance(expr, expression.BinaryOpExpression):
        annotated_left = translate_expression_casts(type_derivation.children["left"])
        annotated_right = translate_expression_casts(type_derivation.children["right"])
        maximal_argument_types_for_op = expr.op.get_maximal_argument_types
        left_right_type = gtypes.merge_operator(
            type_derivation.children["left"].type, maximal_argument_types_for_op[0]
        )
        right_right_type = gtypes.merge_operator(
            type_derivation.children["right"].type, maximal_argument_types_for_op[1]
        )
        return cast(
            expression=expression.BinaryOpExpression(
                op=expr.op,
                left=cast(
                    expression=annotated_left,
                    left_type=type_derivation.children["left"].type,
                    right_type=left_right_type
                ),
                right=cast(
                    expression=annotated_right,
                    left_type=type_derivation.children["right"].type,
                    right_type=right_right_type
                )
            ),
            left_type=expr.op.get_return_type(left_right_type, right_right_type),
            right_type=expr.op.get_return_type(
                type_derivation.children["left"].type, type_derivation.children["right"].type
            ),
        )
    if isinstance(expr, expression.PatternMatchExpression):
        annotated_expression = translate_expression_casts(type_derivation.children["expression"])
        return expression.PatternMatchExpression(
            pattern=expr.pattern, expression=annotated_expression
        )
    if isinstance(expr, expression.IfElseExpression):
        return expression.IfElseExpression(
            condition=cast(
                expression=translate_expression_casts(type_derivation.children["condition"]),
                left_type=type_derivation.children["condition"].type,
                right_type=gtypes.BooleanType()
            ),
            if_clause=cast(
                expression=translate_expression_casts(type_derivation.children["if_clause"]),
                left_type=type_derivation.children["if_clause"].type,
                right_type=type_derivation.type
            ),
            else_clause=cast(
                expression=translate_expression_casts(type_derivation.children["else_clause"]),
                left_type=type_derivation.children["else_clause"].type,
                right_type=type_derivation.type
            ),
        )
    if isinstance(expr, expression.SeqExpression):
        annotated_left = translate_expression_casts(type_derivation.children["left"])
        annotated_right = translate_expression_casts(type_derivation.children["right"])
        return expression.SeqExpression(annotated_left, annotated_right)
    if isinstance(expr, expression.CondExpression):
        annotated_cond_clauses: t.List[t.Tuple[expression.Expression, expression.Expression]] = []
        for cond_type_derivation, do_type_derivation in type_derivation.children["clauses"]:
            annotated_cond = cast(
                expression=translate_expression_casts(cond_type_derivation),
                left_type=cond_type_derivation.type,
                right_type=gtypes.BooleanType()
            )
            annotated_do = cast(
                expression=translate_expression_casts(do_type_derivation),
                left_type=do_type_derivation.type,
                right_type=type_derivation.type
            )
            annotated_cond_clauses.append((annotated_cond, annotated_do))
        return expression.CondExpression(annotated_cond_clauses)
    if isinstance(expr, expression.CaseExpression):
        annotated_test = translate_expression_casts(type_derivation.children["test"])
        annotated_case_clauses: t.List[t.Tuple[pattern.Pattern, expression.Expression]] = []
        for pattern_match_type_derivation, do_type_derivation in type_derivation.children["clauses"]:
            annotated_do = cast(
                expression=translate_expression_casts(do_type_derivation),
                left_type=do_type_derivation.type,
                right_type=type_derivation.type
            )
            annotated_case_clauses.append((pattern_match_type_derivation.pattern, annotated_do))
        return expression.CaseExpression(annotated_test, annotated_case_clauses)
    if isinstance(expr, expression.AnonymizedFunctionExpression):
        return expr
    if isinstance(expr, expression.FunctionCallExpression):
        annotated_arguments: t.List[expression.Expression] = []
        for i in range(len(expr.arguments)):
            argument_type_derivation = type_derivation.children["arguments"][i]
            annotated_argument = cast(
                expression=translate_expression_casts(argument_type_derivation),
                left_type=argument_type_derivation.type,
                right_type=type_derivation.specs_env[(expr.function_name, len(expr.arguments))][0][i]
            )
            annotated_arguments.append(annotated_argument)
        return expression.FunctionCallExpression(function_name=expr.function_name, arguments=annotated_arguments)
    else:
        assert isinstance(expr, expression.AnonCallExpression)
        left_type = type_derivation.children["function"].type
        right_type = type_derivation.children["function"].type
        if isinstance(any := right_type, gtypes.AnyType):
            right_type = gtypes.FunctionType(arg_types=[any for _ in expr.arguments], ret_type=any)
        assert isinstance(right_type, gtypes.FunctionType)
        annotated_arguments = []
        for i in range(len(expr.arguments)):
            argument_type_derivation = type_derivation.children["arguments"][i]
            annotated_argument = cast(
                expression=translate_expression_casts(argument_type_derivation),
                left_type=argument_type_derivation.type,
                right_type=right_type.arg_types[i]
            )
            annotated_arguments.append(annotated_argument)
        return expression.AnonCallExpression(
            function=cast(
                expression=translate_expression_casts(type_derivation.children["function"]),
                left_type=left_type,
                right_type=right_type
            ),
            arguments=annotated_arguments,
        )


def translate_module(type_derivation: module.TypeCheckSuccess, casts: bool) -> AnnotatedModule:
    annotated_definitions = []
    for definition in type_derivation.module.definitions:
        collect_success = type_derivation.collect_success
        body_derivation = type_derivation.definitions_success[definition]
        spec = module.Spec(
            name=definition.name,
            parameter_types=collect_success.specs_env[(definition.name, definition.arity)][0],
            return_type=collect_success.specs_env[(definition.name, definition.arity)][1],
        )
        if not casts:
            annotated_body = translate_expression_types(body_derivation)
            last_expression = annotated_body
            if isinstance(annotated_body, expression.SeqExpression):
                last_expression = annotated_body.right
            if (
                not isinstance(last_expression, AnnotatedExpression)
                or last_expression.type != type_derivation.definitions_success[definition].type
            ):
                annotated_body = AnnotatedExpression(
                    annotated_body, type_derivation.definitions_success[definition].type
                )
            annotated_definition = module.Definition(
                name=definition.name, parameters=definition.parameters, body=annotated_body
            )
        else:
            annotated_body = translate_expression_casts(body_derivation)
            annotated_definition = module.Definition(
                name=definition.name,
                parameters=definition.parameters,
                body=cast(
                    annotated_body, type_derivation.definitions_success[definition].type, spec.return_type
                ),
            )
        annotated_definitions.append((spec, annotated_definition))
    return AnnotatedModule(
        name=type_derivation.module.name,
        annotated_definitions=annotated_definitions,
        specs=type_derivation.module.specs,
    )
