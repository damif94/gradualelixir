import typing as t
from dataclasses import dataclass
from enum import Enum

from gradualelixir import types as gtypes, pattern
from gradualelixir.exception import SyntaxException


class UnaryOpEnum(Enum):
    negation = "!"
    negative = "-"
    absolute_value = "abs"

    @property
    def is_infix(self):
        return self not in [UnaryOpEnum.absolute_value]

    @property
    def types(self) -> t.List[t.Tuple[t.Type[gtypes.Type], t.Type[gtypes.Type]]]:
        if self in [UnaryOpEnum.negative, UnaryOpEnum.absolute_value]:
            return [
                (gtypes.IntegerType, gtypes.IntegerType),
                (gtypes.FloatType, gtypes.FloatType),
                (gtypes.NumberType, gtypes.NumberType)
            ]
        else:
            assert self is UnaryOpEnum.negation
            return [(gtypes.BooleanType, gtypes.BooleanType)]


class BinaryOpEnum(Enum):
    conjunction = "and"
    disjunction = "or"
    sum = "+"
    subtraction = "-"
    product = "*"
    division = "/"
    integer_division = "div"
    integer_reminder = "rem"
    maximum = "max"
    minimum = "min"
    concatenation = "++"
    unconcatenation = "--"
    equality = "=="

    @property
    def is_infix(self) -> bool:
        return self not in [
            BinaryOpEnum.integer_division,
            BinaryOpEnum.integer_reminder,
            BinaryOpEnum.maximum,
            BinaryOpEnum.minimum,
        ]

    @property
    def types(self) -> t.List[t.Tuple[t.Type[gtypes.Type], t.Type[gtypes.Type], t.Type[gtypes.Type]]]:
        if self in [BinaryOpEnum.conjunction, BinaryOpEnum.disjunction]:
            return [(gtypes.BooleanType, gtypes.BooleanType, gtypes.BooleanType)]
        elif self in [BinaryOpEnum.sum, BinaryOpEnum.product, BinaryOpEnum.subtraction]:
            return [
                (gtypes.IntegerType, gtypes.IntegerType, gtypes.IntegerType),
                (gtypes.FloatType, gtypes.FloatType, gtypes.FloatType),
                (gtypes.IntegerType, gtypes.FloatType, gtypes.FloatType),
                (gtypes.FloatType, gtypes.IntegerType, gtypes.FloatType),
                (gtypes.FloatType, gtypes.NumberType, gtypes.FloatType),
                (gtypes.NumberType, gtypes.FloatType, gtypes.FloatType),
                (gtypes.NumberType, gtypes.NumberType, gtypes.NumberType)
            ]
        elif self is BinaryOpEnum.division:
            return [(gtypes.NumberType, gtypes.NumberType, gtypes.FloatType)]
        elif self in [BinaryOpEnum.integer_reminder, BinaryOpEnum.integer_division]:
            return [(gtypes.IntegerType, gtypes.IntegerType, gtypes.IntegerType)]
        elif self in [BinaryOpEnum.maximum, BinaryOpEnum.minimum]:
            return [
                (gtypes.IntegerType, gtypes.IntegerType, gtypes.IntegerType),
                (gtypes.FloatType, gtypes.FloatType, gtypes.FloatType),
                (gtypes.NumberType, gtypes.NumberType, gtypes.NumberType)
            ]
        else:
            assert self is BinaryOpEnum.equality
            return [
                # TODO improve so that
                #  (gtypes.AtomLiteralType(value=x), gtypes.AtomLiteralType(value=x), gtypes.BooleanType)
                (gtypes.AtomType, gtypes.AtomType, gtypes.BooleanType),
                (gtypes.IntegerType, gtypes.IntegerType, gtypes.BooleanType),
                (gtypes.FloatType, gtypes.FloatType, gtypes.BooleanType),
                (gtypes.NumberType, gtypes.NumberType, gtypes.BooleanType)
            ]


class Expression:

    # should be implemented in any derived instance
    def __str__(self):
        pass


@dataclass
class IdentExpression(Expression):
    identifier: str

    def __str__(self):
        return self.identifier


@dataclass
class LiteralExpression(Expression):
    type: gtypes.Type
    value: t.Any


@dataclass
class IntegerExpression(LiteralExpression):
    value: int

    def __init__(self, value: int):
        self.type = gtypes.IntegerType()
        self.value = value

    def __str__(self):
        return str(self.value)


@dataclass
class FloatExpression(LiteralExpression):
    value: float

    def __init__(self, value: float):
        self.type = gtypes.FloatType()
        self.value = value

    def __str__(self):
        return str(self.value)


@dataclass
class AtomLiteralExpression(LiteralExpression):
    value: str

    def __init__(self, value: str):
        self.type = gtypes.AtomLiteralType(atom=value)
        self.value = value

    def __str__(self):
        return str(self.type)


@dataclass
class ElistExpression(Expression):
    def __str__(self):
        return "[]"


@dataclass
class ListExpression(Expression):
    head: Expression
    tail: t.Union["ListExpression", Expression]

    def __init__(self, head: Expression, tail: t.Union["ListExpression", Expression]):
        if not (isinstance(tail, ListExpression) or isinstance(tail, ElistExpression)):
            raise SyntaxException(
                "List pattern's tail should be either a List Expression or an Elist Expression"
            )
        self.head = head
        self.tail = tail

    def __str__(self):
        return f"[{str(self.head)} | {str(self.tail)}]"


@dataclass
class TupleExpression(Expression):
    items: t.List[Expression]

    def __str__(self):
        return "{" + ",".join([str(item) for item in self.items]) + "}"


@dataclass
class MapExpression(Expression):
    map: t.OrderedDict[t.Union[int, float, bool, str], Expression]

    def __str__(self):
        keys = self.map.keys()
        str_values = [str(v) for _, v in self.map.items()]
        return "%{" + ",".join([f"{k}: {v}" for (k, v) in zip(keys, str_values)]) + "}"


@dataclass
class UnaryOpExpression(Expression):
    op: UnaryOpEnum
    expression: Expression

    def __str__(self):
        if self.op.is_infix:
            return f"{self.op.value}{self.expression}"
        else:
            return f"{self.op.value}({self.expression})"


@dataclass
class BinaryOpExpression(Expression):
    op: BinaryOpEnum
    left_expression: Expression
    right_expression: Expression

    def __str__(self):
        if self.op.is_infix:
            return f"{self.left_expression} {self.op.value} {self.right_expression}"
        else:
            return f"{self.op.value}({self.left_expression}, {self.right_expression})"


@dataclass
class PatternMatchExpression(Expression):
    pattern: pattern.Pattern
    expression: Expression

    def __str__(self):
        return f"{self.pattern} = {self.expression}"


@dataclass
class IfExpression(Expression):
    condition: Expression
    if_expression: Expression
    else_expression: t.Optional[Expression]

    def __str__(self):
        res = f"if {self.condition} do\n"
        res += f"{self.if_expression}\n"
        if self.else_expression:
            res += "else\n"
            res += f"{self.else_expression}\n"
        res += "end"
        return res


@dataclass
class SeqExpression(Expression):
    left_expression: Expression
    right_expression: Expression

    def __str__(self):
        return f"{self.left_expression}; {self.right_expression}"


@dataclass
class CaseExpression(Expression):
    expression: Expression
    clauses: t.List[t.Tuple[pattern.Pattern, Expression]]

    def __init__(
        self,
        expression: Expression,
        clauses: t.List[t.Tuple[pattern.Pattern, Expression]],
    ):
        super(CaseExpression, self).__init__()
        if len(clauses) == 0:
            raise SyntaxException("case expression expects at least one clause")
        self.expression = expression
        self.clauses = clauses

    def __str__(self):
        res = f"case {self.expression} do\n"
        for clause in self.clauses:
            res += f"{clause[0]} -> {clause[1]}\n"
        res += "end"
        return res


@dataclass
class CondExpression(Expression):
    clauses: t.List[t.Tuple[Expression, Expression]]

    def __init__(self, clauses: t.List[t.Tuple[Expression, Expression]]):
        super(CondExpression, self).__init__()
        if len(clauses) == 0:
            raise SyntaxException("cond expression expects at least one clause")
        self.clauses = clauses

    def __str__(self):
        res = "cond do\n"
        for clause in self.clauses:
            res += f"{clause[0]} -> {clause[1]}\n"
        res += "end"
        return res


@dataclass
class AnonymizedFunctionExpression(Expression):
    name: str
    arity: int

    def __str__(self):
        return f"&{self.name}/{self.arity}"


@dataclass
class FunctionCallExpression(Expression):
    function_name: str
    arguments: t.List[Expression]

    def __str__(self):
        arguments_str = ",".join([str(arg) for arg in self.arguments])
        return f"{self.function_name}({arguments_str})"


@dataclass
class VarCallExpression(Expression):
    ident: str
    arguments: t.List[Expression]

    def __str__(self):
        arguments_str = ",".join([str(arg) for arg in self.arguments])
        return f"{self.ident}.({arguments_str})"


class ExpressionErrorEnum(Enum):
    incompatible_type_for_unary_operator = "The expression {expr} of type {tau} is not a valid argument for {op}/1"
    incompatible_types_for_binary_operator = (
        "The expressions {expr1} and {expr2} of type {tau1} and {tau2} are not together valid arguments for {op}/2"
    )
    pattern_match = (
        "Couldn't match the inferred type of the expression in the right, {tau}, with {pattern}\n"
        " > {pattern_match_error}"
    )
    incompatible_types_for_list = "The type for the head, {tau1}, and the type for the tail, {tau2} don't have supremum"
    incompatible_types_for_if_else = (
        "The type inferred for the if branch, {tau1}, and the type inferred for the else branch, "
        "{tau2} don't have supremum"
    )


class ExpressionContext:
    expression: Expression


@dataclass
class ListExpressionContext(ExpressionContext):
    expression: ListExpression
    head: bool

    def __str__(self):
        if self.head:
            return f"In the head expression"
        return f"In the tail expression"


@dataclass
class TupleExpressionContext(ExpressionContext):
    expression: TupleExpression
    n: int

    def __str__(self):
        return f"In {self.expression} {self.n}th position"


@dataclass
class MapExpressionContext(ExpressionContext):
    expression: MapExpression
    key: t.Union[int, float, bool, str]

    def __str__(self):
        return f"In the expression for key {self.key}"


@dataclass
class UnaryOpContext(ExpressionContext):
    expression: UnaryOpExpression

    def __str__(self):
        return "In the operator's argument"


@dataclass
class BinaryOpContext(ExpressionContext):
    expression: BinaryOpExpression
    is_left: bool

    def __str__(self):
        if self.is_left:
            return "In the operator's left argument"
        else:
            return "In the operator's right argument"


@dataclass
class PatternMatchContext(ExpressionContext):
    expression: Expression

    def __str__(self):
        return "In the expression"


@dataclass
class IfExpressionContext(ExpressionContext):
    expression: IfExpression
    branch: t.Optional[bool]

    def __str__(self):
        if self.branch is True:
            return f"In the condition"
        elif self.branch is False:
            return f"In the if branch"
        else:
            f"In the else branch"


@dataclass
class CondExpressionContext(ExpressionContext):
    expression: CondExpression
    cond: bool
    branch: int

    def __str__(self):
        if self.cond:
            return f"In the {self.branch}th condition inside\n{self.expression}"
        return f"In the {self.branch}th expression inside\n{self.expression}"


@dataclass
class CaseExpressionContext(ExpressionContext):
    expression: CondExpression
    cond: t.Optional[bool]
    branch: t.Optional[int]

    def __str__(self):
        if self.branch is None:
            return f"In the case expression"
        if self.cond is True:
            return f"In the {self.branch}th pattern"
        return f"In the {self.branch}th expression"


@dataclass
class SeqExpressionContext(ExpressionContext):
    expression: SeqExpression
    is_left: bool

    def __str__(self):
        if self.is_left:
            return "In the left side"
        else:
            return "In the right side"


class ExpressionError:
    def message(self, padding):
        return ""


@dataclass
class BaseExpressionTypeCheckError(ExpressionError):
    expression: Expression
    kind: ExpressionErrorEnum
    args: t.Dict[str, t.Any]

    def __str__(self):
        return self.message()

    def message(self, padding=""):
        msg = f"Type error found inside expression\n{self.expression}\n\n"
        args = {k: str(arg) for k, arg in self.args.items()}
        msg += self.kind.value.format(**args)
        return "\n".join([padding + m for m in msg.split("\n")])


@dataclass
class NestedExpressionTypeCheckError(ExpressionError):
    expression: Expression
    errors: t.List[t.Tuple[ExpressionContext, ExpressionError]]

    def __str__(self):
        return self.message()

    def message(self, padding=""):
        msg = f"Type errors found inside expression\n{padding} {self.expression}\n\n"
        for context, error in self.errors:
            bullet_msg = error.message(padding + "  ")
            msg += f"> {context}:\n" + f"{bullet_msg}\n"
        return msg


TypeEnv = t.Dict[str, gtypes.Type]
SpecsEnv = t.Dict[t.Tuple[str, int], t.Tuple[t.List[gtypes.Type], gtypes.Type]]


@dataclass
class ExpressionTypeCheckReturnType:
    type: gtypes.Type
    env: TypeEnv


def type_check(
    expr: Expression, gamma_env: TypeEnv, delta_env: TypeEnv
) -> t.Union[ExpressionTypeCheckReturnType, ExpressionError]:
    if isinstance(expr, LiteralExpression):
        return ExpressionTypeCheckReturnType(expr.type, gamma_env)
    elif isinstance(expr, IdentExpression):
        return ExpressionTypeCheckReturnType(gamma_env[expr.identifier], gamma_env)
    elif isinstance(expr, ElistExpression):
        return ExpressionTypeCheckReturnType(gtypes.ElistType(), gamma_env)
    elif isinstance(expr, ListExpression):
        head_type_check_result = type_check(expr.head, gamma_env, delta_env)
        tail_type_check_result = type_check(expr.tail, gamma_env, delta_env)
        list_errors = []
        if isinstance(head_type_check_result, ExpressionError):
            list_errors.append((ListExpressionContext(expr, head=False), head_type_check_result))
        if isinstance(tail_type_check_result, ExpressionError):
            list_errors.append((ListExpressionContext(expr, head=False), tail_type_check_result))
        if list_errors:
            return NestedExpressionTypeCheckError(expression=expr, errors=list_errors)  # type: ignore
        else:
            result_type = gtypes.supremum(
                gtypes.ListType(head_type_check_result.type), tail_type_check_result.type  # type: ignore
            )
            if not isinstance(result_type, gtypes.TypingError):
                return ExpressionTypeCheckReturnType(
                    type=result_type,
                    env={**head_type_check_result.env, **tail_type_check_result.env}  # type: ignore
                )
            else:
                return BaseExpressionTypeCheckError(
                    expression=expr,
                    kind=ExpressionErrorEnum.incompatible_types_for_list,
                    args={"tau1": head_type_check_result.type, "tau2": tail_type_check_result.type.type}  # type: ignore
                )
    elif isinstance(expr, TupleExpression):
        type_check_results = []
        tuple_errors = []
        for i in range(len(expr.items)):
            aux = type_check(expr.items[i], gamma_env, delta_env)
            if isinstance(aux, ExpressionError):
                tuple_errors.append((TupleExpressionContext(expr, n=i), aux))
            else:
                type_check_results.append(aux)
        if tuple_errors:
            return NestedExpressionTypeCheckError(expression=expr, errors=tuple_errors)  # type: ignore
        else:
            gamma_env = {}
            for item in type_check_results:
                gamma_env = {**gamma_env, **item.env}
            return ExpressionTypeCheckReturnType(
                type=gtypes.TupleType([e.type for e in type_check_results]), env=gamma_env
            )
    elif isinstance(expr, MapExpression):
        type_check_results_dict = {}
        map_errors = {}
        for k in expr.map:
            aux = type_check(expr.map[k], gamma_env, delta_env)
            if isinstance(aux, ExpressionError):
                map_errors[k] = (MapExpressionContext(expr, key=k), aux)
            else:
                type_check_results_dict[k] = aux
        if map_errors:
            return NestedExpressionTypeCheckError(expression=expr, errors=map_errors)  # type: ignore
        else:
            gamma_env = {}
            for k in type_check_results_dict:
                gamma_env = {**gamma_env, **type_check_results_dict[k].env}
            return ExpressionTypeCheckReturnType(
                type=gtypes.MapType({k: tau.type for k, tau in type_check_results_dict.items()}), env=gamma_env
            )
    elif isinstance(expr, UnaryOpExpression):
        expression_type_check_result = type_check(expr.expression, gamma_env, delta_env)
        if isinstance(expression_type_check_result, ExpressionError):
            return NestedExpressionTypeCheckError(
                expression=expr, errors=[(UnaryOpContext(expression=expr), expression_type_check_result)]
            )
        if valid_result_types := [
            ret_type for arg_type, ret_type in expr.op.types
            if gtypes.is_subtype(expression_type_check_result.type, arg_type())
        ]:
            return ExpressionTypeCheckReturnType(valid_result_types[0](), expression_type_check_result.env)
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.incompatible_type_for_unary_operator,
            args={"expr": expr.expression, "tau": expression_type_check_result.type, "op": expr.op.value}
        )
    elif isinstance(expr, BinaryOpExpression):
        left_type_check_result = type_check(expr.left_expression, gamma_env, delta_env)
        if isinstance(left_type_check_result, ExpressionError):
            return NestedExpressionTypeCheckError(
                expression=expr,
                errors=[(BinaryOpContext(expression=expr, is_left=True), left_type_check_result)]
            )
        right_type_check_result = type_check(expr.right_expression, gamma_env, delta_env)
        if isinstance(right_type_check_result, ExpressionError):
            return NestedExpressionTypeCheckError(
                expression=expr,
                errors=[(BinaryOpContext(expression=expr, is_left=False), right_type_check_result)]
            )
        if valid_result_types := [
            ret_type for left_arg_type, right_arg_type, ret_type in expr.op.types  # type: ignore
            if (
                gtypes.is_subtype(right_type_check_result.type, left_arg_type())
                and
                gtypes.is_subtype(right_type_check_result.type, right_arg_type())
            )
        ]:
            return ExpressionTypeCheckReturnType(
                type=valid_result_types[0](),
                env={**left_type_check_result.env, **right_type_check_result.env}
            )
        else:
            return BaseExpressionTypeCheckError(
                expression=expr,
                kind=ExpressionErrorEnum.incompatible_types_for_binary_operator,
                args={
                    "expr1": expr.left_expression,
                    "expr2": expr.right_expression,
                    "tau1": left_type_check_result.type,
                    "tau2": right_type_check_result.type,
                    "op": expr.op.value
                }
            )
    elif isinstance(expr, PatternMatchExpression):
        expression_type_check_result = type_check(expr.expression, gamma_env, delta_env)
        if isinstance(expression_type_check_result, ExpressionError):
            return NestedExpressionTypeCheckError(
                expression=expr, errors=[(PatternMatchContext(expr.expression), expression_type_check_result)]
            )
        else:
            pattern_match_result = pattern.pattern_match(
                expr.pattern, expression_type_check_result.type, {}, expression_type_check_result.env
            )
            if isinstance(pattern_match_result, pattern.PatternMatchError):
                return BaseExpressionTypeCheckError(
                    expression=expr,
                    kind=ExpressionErrorEnum.pattern_match,
                    args={
                        "tau": expression_type_check_result.type,
                        "pattern": expr.pattern,
                        "pattern_match_error": pattern_match_result
                    }
                )
            return ExpressionTypeCheckReturnType(
                pattern_match_result[0], {**expression_type_check_result.env, **pattern_match_result[1]}
            )
    elif isinstance(expr, IfExpression):
        cond_type_check_result = type_check(expr.condition, gamma_env, delta_env)
        if isinstance(cond_type_check_result, ExpressionError):
            return NestedExpressionTypeCheckError(
                expression=expr, errors=[(IfExpressionContext(expression=expr, branch=None), cond_type_check_result)]
            )
        else:
            errors = []
            if_type_check_result = type_check(expr.if_expression, gamma_env, delta_env)
            if isinstance(if_type_check_result, ExpressionError):
                errors.append((IfExpressionContext(expression=expr, branch=True), if_type_check_result))
            else_type_check_result = None
            if expr.else_expression is not None:
                else_type_check_result = type_check(expr.if_expression, gamma_env, delta_env)
                if isinstance(else_type_check_result, ExpressionError):
                    errors.append((IfExpressionContext(expression=expr, branch=False), else_type_check_result))
            if errors:
                return NestedExpressionTypeCheckError(expression=expr, errors=errors)  # type: ignore
            assert isinstance(if_type_check_result, ExpressionTypeCheckReturnType)
            assert isinstance(else_type_check_result, ExpressionTypeCheckReturnType)
            ret_type, ret_env = if_type_check_result.type, if_type_check_result.env
            if else_type_check_result:
                ret_type = gtypes.supremum(if_type_check_result.type, else_type_check_result.type)  # type: ignore
                if isinstance(ret_type, gtypes.TypingError):
                    return BaseExpressionTypeCheckError(
                        expression=expr,
                        kind=ExpressionErrorEnum.incompatible_types_for_if_else,
                        args={"tau1": if_type_check_result.type, "tau2": else_type_check_result.type}
                    )
                ret_env = {**if_type_check_result.env, **else_type_check_result.env}
            return ExpressionTypeCheckReturnType(ret_type, ret_env)
    elif isinstance(expr, SeqExpression):
        left_type_check_expression = type_check(expr.left_expression, gamma_env, delta_env)
        if isinstance(left_type_check_expression, ExpressionError):
            return NestedExpressionTypeCheckError(
                expression=expr, errors=[(SeqExpressionContext(expr, is_left=True), left_type_check_expression)]
            )
        else:
            right_type_check_expression = type_check(
                expr.right_expression, left_type_check_expression.env, delta_env
            )
            if isinstance(right_type_check_expression, ExpressionError):
                return NestedExpressionTypeCheckError(
                    expression=expr, errors=[(SeqExpressionContext(expr, is_left=False), right_type_check_expression)]
                )
            return ExpressionTypeCheckReturnType(
                right_type_check_expression.type,
                {**left_type_check_expression.env, **right_type_check_expression.env}
            )
    # elif isinstance(expr, CondExpression):
    #     errors = []
    #     for i in range(len(expr.clauses)):
    #         cond_type_check_expression = type_check(branch[0], gamma_env, delta_env)
    #         if isinstance(cond_type_check_expression, ExpressionError):
    #             errors.append((CondExpressionContext(expr, branch=i, cond=True), cond_type_check_expression))
    #             continue
    #         do_type_check_expression = type_check(expr[1], gamma_env, delta_env)