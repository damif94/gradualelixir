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
class CastAnnotatedPattern(pattern.Pattern):
    pattern: expression.Expression
    left_type: gtypes.Type
    right_type: gtypes.Type

    def __str__(self):
        if self.left_type == self.right_type:
            return str(self.pattern)
        return f"({self.pattern} | {self.left_type} ~> {self.right_type})"


@dataclass
class CastAnnotatedExpression(expression.Expression):
    expression: expression.Expression
    left_type: gtypes.Type
    right_type: gtypes.Type

    def __str__(self):
        if self.left_type == self.right_type:
            return str(self.expression)
        return f"({self.expression} | {self.left_type} ~> {self.right_type})"


@dataclass
class CastAnnotatedVarCallExpression(expression.Expression):
    expression: expression.VarCallExpression
    ident_left_type: gtypes.Type
    ident_right_type: gtypes.Type

    def __str__(self):
        if self.ident_left_type == self.ident_right_type:
            return str(self.expression)
        arguments_str = ",".join([str(arg) for arg in self.expression.arguments])
        return f"({self.expression.ident} | {self.ident_left_type} ~> {self.ident_right_type}).({arguments_str})"


@dataclass
class AnnotatedModule:
    name: str
    annotated_definitions: t.List[t.Tuple[module.Spec, module.Definition]]

    def __str__(self):
        msg = f"defmodule {self.name} do\n"
        msg += "  use UseCast\n\n"
        for definition in self.annotated_definitions:
            msg += f"{definition[0]}\n{definition[1]}\n\n"
        msg += "end"
        return msg


def make_annotated_expression(type_check_result: expression.ExpressionTypeCheckSuccess) -> AnnotatedExpression:
    return AnnotatedExpression(type_check_result.expression, type_check_result.type)


def annotate_expression(type_derivation: expression.ExpressionTypeCheckSuccess, **kwargs) -> expression.Expression:
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
                head=annotate_expression(type_derivation.children["head"]),
                tail=annotate_expression(type_derivation.children["tail"])
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.TupleExpression):
        return AnnotatedExpression(
            expression=expression.TupleExpression(
                items=[
                    annotate_expression(type_derivation.children["items"][i], skip_ident=True)
                    for i in range(len(expr.items))
                ]
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.MapExpression):
        keys_with_positions = [(k, list(expr.map.keys()).index(k)) for k in expr.map.keys()]
        return AnnotatedExpression(
            expression=expression.MapExpression(
                map=expression.OrderedDict({
                    k: annotate_expression(type_derivation.children["map"][pos], skip_ident=True)
                    for k, pos in keys_with_positions
                })
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.UnaryOpExpression):
        annotated_argument = annotate_expression(type_derivation.children["argument"], skip_ident=True)
        return AnnotatedExpression(
            expression=expression.UnaryOpExpression(
                op=expr.op, argument=AnnotatedExpression(annotated_argument, type_derivation.children["argument"].type)
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.BinaryOpExpression):
        annotated_left = annotate_expression(type_derivation.children["left"], skip_ident=True)
        annotated_right = annotate_expression(type_derivation.children["right"], skip_ident=True)
        return AnnotatedExpression(
            expression=expression.BinaryOpExpression(
                op=expr.op,
                left=annotated_left,
                right=annotated_right
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.PatternMatchExpression):
        annotated_expression = annotate_expression(type_derivation.children["expression"])
        return AnnotatedExpression(
            expression=expression.PatternMatchExpression(expr.pattern, annotated_expression),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.IfElseExpression):
        # TODO[personal] PR walrus operator type inference mypy
        annotated_condition = annotate_expression(type_derivation.children["condition"])
        annotated_if_clause = annotate_expression(type_derivation.children["if_clause"])
        annotated_else_clause = None
        if expr.else_clause:
            annotated_else_clause = annotate_expression(type_derivation.children["else_clause"])
        return AnnotatedExpression(
            expression=expression.IfElseExpression(
                condition=annotated_condition,
                if_clause=annotated_if_clause,
                else_clause=annotated_else_clause,
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.SeqExpression):
        annotated_left = annotate_expression(type_derivation.children["left"])
        annotated_right = annotate_expression(type_derivation.children["right"])
        return expression.SeqExpression(annotated_left, annotated_right)
    if isinstance(expr, expression.CondExpression):
        annotated_cond_clauses = []
        for cond_type_derivation, do_type_derivation in type_derivation.children["clauses"]:
            annotated_cond = annotate_expression(cond_type_derivation)
            annotated_do = annotate_expression(do_type_derivation)
            annotated_cond_clauses.append((annotated_cond, annotated_do))
        return AnnotatedExpression(
            expression=expression.CondExpression(annotated_cond_clauses), type=type_derivation.type
        )
    if isinstance(expr, expression.CaseExpression):
        annotated_test = annotate_expression(type_derivation.children["test"])
        annotated_case_clauses: t.List[t.Tuple[pattern.Pattern, expression.Expression]] = []
        for pattern_match_type_derivation, do_type_derivation in type_derivation.children["clauses"]:
            annotated_do = annotate_expression(do_type_derivation)
            annotated_case_clauses.append((pattern_match_type_derivation.pattern, annotated_do))
        return AnnotatedExpression(
            expression=expression.CaseExpression(annotated_test, annotated_case_clauses), type=type_derivation.type
        )
    if isinstance(expr, expression.AnonymizedFunctionExpression):
        return AnnotatedExpression(
            expression=expr, type=type_derivation.type
        )
    if isinstance(expr, expression.FunctionCallExpression):
        annotated_arguments = []
        for argument_type_derivation in type_derivation.children["arguments"]:
            annotated_argument = annotate_expression(argument_type_derivation)
            annotated_arguments.append(annotated_argument)
        return AnnotatedExpression(
            expression=expression.FunctionCallExpression(
                function_name=expr.function_name, arguments=annotated_arguments
            ),
            type=type_derivation.type
        )
    if isinstance(expr, expression.VarCallExpression):
        annotated_arguments = []
        for argument_type_derivation in type_derivation.children["arguments"]:
            annotated_argument = annotate_expression(argument_type_derivation)
            annotated_arguments.append(annotated_argument)

        signature = type_derivation.env[expr.ident]
        assert isinstance(signature, gtypes.FunctionType)
        return AnnotatedExpression(
            expression=expression.VarCallExpression(
                ident=expr.ident, arguments=annotated_arguments
            ),
            type=type_derivation.type
        )
    else:
        return expr


def cast_annotate_expression(type_derivation: expression.ExpressionTypeCheckSuccess) -> expression.Expression:
    expr = type_derivation.expression
    if isinstance(expr, expression.IdentExpression):
        return CastAnnotatedExpression(expr, type_derivation.env[expr.identifier], type_derivation.type)
    if isinstance(expr, expression.LiteralExpression):
        return expr
    if isinstance(expr, expression.ElistExpression):
        return expr
    if isinstance(expr, expression.ListExpression):
        return expression.ListExpression(
            head=CastAnnotatedExpression(
                expr.head, type_derivation.children["head"].type, type_derivation.type
            ),
            tail=CastAnnotatedExpression(
                expr.tail, type_derivation.children["tail"].type, type_derivation.type
            ),
        )
    if isinstance(expr, expression.TupleExpression):
        return expression.TupleExpression([
            cast_annotate_expression(type_derivation.children["items"][i]) for i in range(len(expr.items))
        ])
    if isinstance(expr, expression.MapExpression):
        keys_with_positions = [(k, list(expr.map.keys()).index(k)) for k in expr.map.keys()]
        return expression.MapExpression(
            map=expression.OrderedDict({
                k: cast_annotate_expression(type_derivation.children["map"][pos])
                for k, pos in keys_with_positions
            })
        )
    if isinstance(expr, expression.BinaryOpExpression):
        annotated_left = cast_annotate_expression(type_derivation.children["left"])
        annotated_right = cast_annotate_expression(type_derivation.children["right"])
        return expression.BinaryOpExpression(
            op=expr.op,
            left=CastAnnotatedExpression(annotated_left, type_derivation.children["left"].type, type_derivation.type),
            right=CastAnnotatedExpression(
                annotated_right, type_derivation.children["right"].type, type_derivation.type
            ),
        )
    if isinstance(expr, expression.IfElseExpression):
        annotated_condition = cast_annotate_expression(type_derivation.children["condition"])
        annotated_if_clause = cast_annotate_expression(type_derivation.children["if_clause"])
        annotated_else_clause = None
        if expr.else_clause:
            annotated_else_clause = annotate_expression(type_derivation.children["else_clause"])
        return expression.IfElseExpression(
            condition=annotated_condition,
            if_clause=annotated_if_clause,
            else_clause=annotated_else_clause,
        )
    if isinstance(expr, expression.SeqExpression):
        annotated_left = cast_annotate_expression(type_derivation.children["left"])
        annotated_right = cast_annotate_expression(type_derivation.children["right"])
        return expression.SeqExpression(annotated_left, annotated_right)
    if isinstance(expr, expression.CondExpression):
        annotated_cond_clauses: t.List[t.Tuple[expression.Expression, expression.Expression]] = []
        for cond_type_derivation, do_type_derivation in type_derivation.children["clauses"]:
            annotated_cond = cast_annotate_expression(cond_type_derivation)
            annotated_do = cast_annotate_expression(do_type_derivation)
            annotated_cond_clauses.append(
                (annotated_cond, CastAnnotatedExpression(annotated_do, do_type_derivation.type, type_derivation.type))
            )
        return expression.CondExpression(annotated_cond_clauses)
    if isinstance(expr, expression.AnonymizedFunctionExpression):
        return expr
    if isinstance(expr, expression.FunctionCallExpression):
        annotated_arguments = []
        for i in range(len(expr.arguments)):
            argument_type_derivation = type_derivation.children["arguments"][i]
            annotated_argument = CastAnnotatedExpression(
                expression=cast_annotate_expression(argument_type_derivation),
                left_type=argument_type_derivation.type,
                right_type=type_derivation.specs_env[(expr.function_name, len(expr.arguments))][0][i]
            )
            annotated_arguments.append(annotated_argument)
        return AnnotatedExpression(
            expression=expression.FunctionCallExpression(
                function_name=expr.function_name, arguments=annotated_arguments
            ),
            type=type_derivation.type
        )
    if isinstance(expr, expression.VarCallExpression):
        annotated_arguments = []
        for i in range(len(expr.arguments)):
            argument_type_derivation = type_derivation.children["arguments"][i]
            annotated_argument = CastAnnotatedExpression(
                expression=cast_annotate_expression(argument_type_derivation),
                left_type=argument_type_derivation.type,
                right_type=type_derivation.specs_env[(expr.ident, len(expr.arguments))][0][i]
            )
            annotated_arguments.append(annotated_argument)

        ident_right_type = type_derivation.env[expr.ident]
        if isinstance(any := type_derivation.env[expr.ident], gtypes.AnyType):
            ident_right_type = gtypes.FunctionType(arg_types=[any for _ in expr.arguments], ret_type=any)

        return AnnotatedExpression(
            expression=CastAnnotatedVarCallExpression(
                expression=expression.VarCallExpression(ident=expr.ident, arguments=annotated_arguments),
                ident_left_type=type_derivation.env[expr.ident],
                ident_right_type=ident_right_type
            ),
            type=type_derivation.type
        )
    else:
        return expr


def annotate_module(type_derivation: module.TypeCheckSuccess, casts: bool) -> AnnotatedModule:
    annotated_definitions = []
    for definition in type_derivation.module.definitions:
        specs_env = type_derivation.specs_refinement_success.refined_specs_env
        body_derivation = type_derivation.definitions_success[definition]
        spec = module.Spec(
            name=definition.name,
            parameter_types=specs_env[(definition.name, definition.arity)][0],
            return_type=specs_env[(definition.name, definition.arity)][1],
        )
        if not casts:
            annotated_body = annotate_expression(body_derivation)
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
            annotated_body = cast_annotate_expression(body_derivation)
            annotated_definition = module.Definition(
                name=definition.name,
                parameters=definition.parameters,
                body=CastAnnotatedExpression(
                    annotated_body, type_derivation.definitions_success[definition].type, spec.return_type
                ),
            )
        annotated_definitions.append((spec, annotated_definition))
    return AnnotatedModule(name=type_derivation.module.name, annotated_definitions=annotated_definitions)
