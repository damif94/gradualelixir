import typing as t
from dataclasses import dataclass

from gradualelixir import expression, gtypes, module, pattern


@dataclass
class AnnotatedExpression(expression.Expression):
    expression: expression.Expression
    type: gtypes.Type

    def __str__(self):
        return f'({self.expression} ||| {self.type})'


@dataclass
class AnnotatedPattern(pattern.Pattern):
    pattern: expression.Expression
    type: gtypes.Type

    def __str__(self):
        return f'({self.pattern} ||| {self.type})'


def make_annotated_expression(type_check_result: expression.ExpressionTypeCheckSuccess) -> AnnotatedExpression:
    return AnnotatedExpression(type_check_result.expression, type_check_result.type)


def annotate_expression(type_derivation: expression.ExpressionTypeCheckSuccess) -> expression.Expression:
    expr = type_derivation.expression
    if isinstance(expr, expression.PatternMatchExpression):
        annotated_expression = annotate_expression(type_derivation.children['expression'])
        return AnnotatedExpression(
            expression=expression.PatternMatchExpression(type_derivation.children['pattern'], annotated_expression),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.IfElseExpression):
        # TODO[personal] PR walrus operator type inference mypy
        annotated_condition = annotate_expression(type_derivation.children['condition'])
        annotated_if_clause = annotate_expression(type_derivation.children['if_clause'])
        annotated_else_clause = None
        if expr.else_clause:
            annotated_else_clause = annotate_expression(type_derivation.children['else_clause'])
        return AnnotatedExpression(
            expression=expression.IfElseExpression(
                condition=annotated_condition,
                if_clause=annotated_if_clause,
                else_clause=annotated_else_clause,
            ),
            type=type_derivation.type,
        )
    if isinstance(expr, expression.CondExpression):
        annotated_cond_clauses = []
        for cond_type_derivation, do_type_derivation in type_derivation.children['clauses']:
            annotated_cond = annotate_expression(cond_type_derivation)
            annotated_do = annotate_expression(do_type_derivation)
            annotated_cond_clauses.append((annotated_cond, annotated_do))
        return AnnotatedExpression(
            expression=expression.CondExpression(annotated_cond_clauses), type=type_derivation.type
        )
    if isinstance(expr, expression.CaseExpression):
        annotated_test = annotate_expression(type_derivation.children['test'])
        annotated_case_clauses: t.List[t.Tuple[pattern.Pattern, expression.Expression]] = []
        for pattern_match_type_derivation, do_type_derivation in type_derivation.children['clauses']:
            annotated_pattern = AnnotatedPattern(
                pattern_match_type_derivation.patern, pattern_match_type_derivation.type
            )
            annotated_do = annotate_expression(do_type_derivation)
            annotated_case_clauses.append((annotated_pattern, annotated_do))
        return AnnotatedExpression(
            expression=expression.CaseExpression(annotated_test, annotated_case_clauses), type=type_derivation.type
        )
    else:
        return AnnotatedExpression(expr, type_derivation.type)


def annotate_module(type_derivation: module.TypeCheckSuccess) -> module.AnnotatedModule:
    annotated_definitions = []
    for spec, definition in type_derivation.module.annotated_definitions:
        body_derivation = type_derivation.definitions_success[(definition.name, definition.arity)]
        annotated_body = annotate_expression(body_derivation)
        annotated_definitions.append(
            (spec, module.Definition(name=definition.name, parameters=definition.parameters, body=annotated_body))
        )
    return module.AnnotatedModule(name=type_derivation.module.name, annotated_definitions=annotated_definitions)
