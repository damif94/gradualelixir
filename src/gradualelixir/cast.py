from dataclasses import dataclass

from gradualelixir import expression, gtypes


@dataclass
class AnnotatedExpression(expression.Expression):
    expression: expression.Expression
    type: gtypes.Type

    def __str__(self):
        return f"({self.expression} | {self.type})"


def make_annotated_expression(type_check_result: expression.ExpressionTypeCheckSuccess) -> AnnotatedExpression:
    return AnnotatedExpression(type_check_result.expression, type_check_result.type)


def annotate_expression(type_derivation: expression.ExpressionTypeCheckSuccess) -> expression.Expression:
    expr = type_derivation.expression
    if isinstance(expr, expression.IfElseExpression):
        # TODO[personal] PR walrus operator type inference mypy
        annotated_condition_expression = annotate_expression(type_derivation.children["condition"])
        annotated_if_clause_expression = annotate_expression(type_derivation.children["if_clause"])
        annotated_else_clause_expression = None
        if expr.else_clause:
            annotated_else_clause_expression = annotate_expression(type_derivation.children["else_clause"])
        return AnnotatedExpression(
            expression=expression.IfElseExpression(
                condition=annotated_condition_expression,
                if_clause=annotated_if_clause_expression,
                else_clause=annotated_else_clause_expression,
            ),
            type=type_derivation.type,
        )
    else:
        return AnnotatedExpression(expr, type_derivation.type)
