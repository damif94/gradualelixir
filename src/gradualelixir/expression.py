import typing as t
from dataclasses import dataclass
from enum import Enum

from gradualelixir import types as gtypes, pattern
from gradualelixir.exception import SyntaxRestrictionException
from gradualelixir.formatter import format_elixir_code
from gradualelixir.utils import Bcolors


class UnaryOpEnum(Enum):
    negation = "not"
    negative = "-"
    absolute_value = "abs"

    @property
    def is_infix(self):
        return self not in [UnaryOpEnum.absolute_value]

    @property
    def types(self) -> t.List[t.Tuple[gtypes.Type, gtypes.Type]]:
        if self in [UnaryOpEnum.negative, UnaryOpEnum.absolute_value]:
            return [
                (gtypes.IntegerType(), gtypes.IntegerType()),
                (gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.NumberType(), gtypes.NumberType())
            ]
        else:
            assert self is UnaryOpEnum.negation
            return [
                (gtypes.AtomLiteralType("true"), gtypes.AtomLiteralType("false")),
                (gtypes.AtomLiteralType("false"), gtypes.AtomLiteralType("true")),
                (gtypes.BooleanType(), gtypes.BooleanType())
            ]


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
    def types(self) -> t.List[t.Tuple[gtypes.Type, gtypes.Type, gtypes.Type]]:
        if self is BinaryOpEnum.conjunction:
            return [
                (gtypes.AtomLiteralType("true"), gtypes.AtomLiteralType("true"), gtypes.AtomLiteralType("true")),
                (gtypes.AtomLiteralType("false"), gtypes.BooleanType(), gtypes.AtomLiteralType("false")),
                (gtypes.BooleanType(), gtypes.AtomLiteralType("false"), gtypes.AtomLiteralType("false")),
                (gtypes.BooleanType(), gtypes.BooleanType(), gtypes.BooleanType())
            ]
        if self is BinaryOpEnum.disjunction:
            return [
                (gtypes.AtomLiteralType("false"), gtypes.AtomLiteralType("false"), gtypes.AtomLiteralType("false")),
                (gtypes.AtomLiteralType("true"), gtypes.BooleanType(), gtypes.AtomLiteralType("true")),
                (gtypes.BooleanType(), gtypes.AtomLiteralType("true"), gtypes.AtomLiteralType("true")),
                (gtypes.BooleanType(), gtypes.BooleanType(), gtypes.BooleanType())
            ]
        elif self in [BinaryOpEnum.sum, BinaryOpEnum.product, BinaryOpEnum.subtraction]:
            return [
                (gtypes.IntegerType(), gtypes.IntegerType(), gtypes.IntegerType()),
                (gtypes.FloatType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.IntegerType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.FloatType(), gtypes.IntegerType(), gtypes.FloatType()),
                (gtypes.FloatType(), gtypes.NumberType(), gtypes.FloatType()),
                (gtypes.NumberType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.NumberType(), gtypes.NumberType(), gtypes.NumberType())
            ]
        elif self is BinaryOpEnum.division:
            return [(gtypes.NumberType(), gtypes.NumberType(), gtypes.FloatType())]
        elif self in [BinaryOpEnum.integer_reminder, BinaryOpEnum.integer_division]:
            return [(gtypes.IntegerType(), gtypes.IntegerType(), gtypes.IntegerType())]
        elif self in [BinaryOpEnum.maximum, BinaryOpEnum.minimum]:
            return [
                (gtypes.IntegerType(), gtypes.IntegerType(), gtypes.IntegerType()),
                (gtypes.FloatType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.NumberType(), gtypes.NumberType(), gtypes.NumberType())
            ]
        else:
            assert self is BinaryOpEnum.equality
            return [
                # TODO improve so that
                #  (gtypes.AtomLiteralType(value=x), gtypes.AtomLiteralType(value=x), gtypes.BooleanType)
                (gtypes.AtomType(), gtypes.AtomType(), gtypes.BooleanType()),
                (gtypes.IntegerType(), gtypes.IntegerType(), gtypes.BooleanType()),
                (gtypes.FloatType(), gtypes.FloatType(), gtypes.BooleanType()),
                (gtypes.NumberType(), gtypes.NumberType(), gtypes.BooleanType())
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
            raise SyntaxRestrictionException(
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
    map: t.OrderedDict[gtypes.MapKey, Expression]

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
            return f"{self.op.value} {self.expression}"
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
class IfElseExpression(Expression):
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

    def __str__(self):
        res = f"case {self.expression} do\n"
        for clause in self.clauses:
            res += f"{clause[0]} -> {clause[1]}\n"
        res += "end"
        return res


@dataclass
class CondExpression(Expression):
    clauses: t.List[t.Tuple[Expression, Expression]]

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
    identifier_not_found_in_environment = "Couldn't find variable {identifier} in the environment"
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
    type_is_not_boolean = "The type inferred for {tau} is not a subtype of boolean"
    incompatible_types_for_cond = "C"


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
        return f"In {self.expression} {self.n + 1}th position"


@dataclass
class MapExpressionContext(ExpressionContext):
    expression: MapExpression
    key: gtypes.MapKey

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
class PatternMatchExpressionContext(ExpressionContext):
    expression: Expression

    def __str__(self):
        return "In the expression"


@dataclass
class IfElseExpressionContext(ExpressionContext):
    expression: IfElseExpression
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
            return f"In the {self.branch + 1}th condition inside"
        return f"In the {self.branch + 1}th expression inside"


@dataclass
class CaseExpressionContext(ExpressionContext):
    expression: CaseExpression
    pattern: t.Optional[bool]
    branch: t.Optional[int]

    def __str__(self):
        if self.branch is None:
            return f"In the case expression"
        if self.pattern is True:
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


class ExpressionTypeCheckError:
    def message(self, padding):
        pass


@dataclass
class BaseExpressionTypeCheckError(ExpressionTypeCheckError):
    expression: Expression
    kind: ExpressionErrorEnum
    args: t.Dict[str, t.Any]

    def __str__(self):
        return self.message()

    def message(self, padding=""):
        expression_msg = format_elixir_code(str(self.expression))
        expression_msg = "\n".join([padding + "    " + m for m in str(expression_msg).split("\n")])
        msg = f"{padding}{Bcolors.OKBLUE}Type error found inside expression{Bcolors.ENDC}\n\n{expression_msg}{Bcolors.ENDC}\n\n"
        args = {k: str(arg) for k, arg in self.args.items()}
        msg += f"{padding}{Bcolors.FAIL}    Error: {self.kind.value.format(**args)}{Bcolors.ENDC}"
        return msg


@dataclass
class NestedExpressionTypeCheckError(ExpressionTypeCheckError):
    expression: Expression
    errors: t.List[t.Tuple[ExpressionContext, ExpressionTypeCheckError]]

    def __str__(self):
        return self.message()

    def message(self, padding=""):
        expression_msg = format_elixir_code(str(self.expression))
        expression_msg = "\n".join([padding + "    " + m for m in str(expression_msg).split("\n")])
        msg = f"{padding}{Bcolors.OKBLUE}Type errors found inside expression{Bcolors.ENDC}\n\n{expression_msg}\n\n"
        for context, error in self.errors:
            bullet_msg = error.message(padding + "    ")
            msg += f"{padding}{Bcolors.OKBLUE}> {context}:{Bcolors.ENDC}\n" + f"{bullet_msg}\n"
        return msg


TypeEnv = t.Dict[str, gtypes.Type]
SpecsEnv = t.Dict[t.Tuple[str, int], t.Tuple[t.List[gtypes.Type], gtypes.Type]]


@dataclass
class ExpressionTypeCheckSuccess:
    type: gtypes.Type
    env: TypeEnv


ExpressionTypeCheckResult = t.Union[ExpressionTypeCheckSuccess, ExpressionTypeCheckError]


def type_check(expr: Expression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    if isinstance(expr, LiteralExpression):
        return type_check_literal(expr, gamma_env, delta_env)
    if isinstance(expr, IdentExpression):
        return type_check_ident(expr, gamma_env, delta_env)
    if isinstance(expr, ElistExpression):
        return type_check_elist(expr, gamma_env, delta_env)
    if isinstance(expr, ListExpression):
        return type_check_list(expr, gamma_env, delta_env)
    if isinstance(expr, TupleExpression):
        return type_check_tuple(expr, gamma_env, delta_env)
    if isinstance(expr, MapExpression):
        return type_check_map(expr, gamma_env, delta_env)
    if isinstance(expr, UnaryOpExpression):
        return type_check_unary_op(expr, gamma_env, delta_env)
    if isinstance(expr, BinaryOpExpression):
        return type_check_binary_op(expr, gamma_env, delta_env)
    if isinstance(expr, PatternMatchExpression):
        return type_check_pattern_match(expr, gamma_env, delta_env)
    if isinstance(expr, IfElseExpression):
        return type_check_if_else(expr, gamma_env, delta_env)
    if isinstance(expr, SeqExpression):
        return type_check_seq(expr, gamma_env, delta_env)
    if isinstance(expr, CondExpression):
        return type_check_cond(expr, gamma_env, delta_env)
    if isinstance(expr, CaseExpression):
        return type_check_case(expr, gamma_env, delta_env)
    else:
        pass


def type_check_literal(expr: LiteralExpression, gamma_env: TypeEnv, _delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    return ExpressionTypeCheckSuccess(expr.type, gamma_env)


def type_check_ident(expr: IdentExpression, gamma_env: TypeEnv, _delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    if (sigma := gamma_env.get(expr.identifier)) is not None:
        return ExpressionTypeCheckSuccess(sigma, gamma_env)
    else:
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.identifier_not_found_in_environment,
            args={"identifier": expr.identifier},
        )


def type_check_elist(_expr: ElistExpression, gamma_env: TypeEnv, _delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    return ExpressionTypeCheckSuccess(gtypes.ElistType(), gamma_env)


def type_check_list(expr: ListExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    head_type_check_result = type_check(expr.head, gamma_env, delta_env)
    tail_type_check_result = type_check(expr.tail, gamma_env, delta_env)
    if isinstance(head_type_check_result, ExpressionTypeCheckError) and isinstance(tail_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            errors=[
                (ListExpressionContext(expr, head=True), head_type_check_result),
                (ListExpressionContext(expr, head=False), tail_type_check_result)
            ]
        )
    if isinstance(head_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            errors=[(ListExpressionContext(expr, head=True), head_type_check_result)]
        )
    if isinstance(tail_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            errors=[(ListExpressionContext(expr, head=False), tail_type_check_result)]
        )
    result_type = gtypes.supremum(
        gtypes.ListType(head_type_check_result.type), tail_type_check_result.type
    )
    if not isinstance(result_type, gtypes.TypingError):
        return ExpressionTypeCheckSuccess(
            type=result_type,
            env={**head_type_check_result.env, **tail_type_check_result.env}
        )
    else:
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.incompatible_types_for_list,
            args={"tau1": head_type_check_result.type, "tau2": tail_type_check_result.type.type}  # type: ignore
        )


def type_check_tuple(expr: TupleExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    type_check_results = []
    errors: t.List[t.Tuple[ExpressionContext, ExpressionTypeCheckError]] = []
    for i in range(len(expr.items)):
        item_type_check_result = type_check(expr.items[i], gamma_env, delta_env)
        if isinstance(item_type_check_result, ExpressionTypeCheckError):
            errors.append((TupleExpressionContext(expr, n=i), item_type_check_result))
        else:
            type_check_results.append(item_type_check_result)
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, errors=errors)
    else:
        gamma_env = {}
        for item in type_check_results:
            gamma_env = {**gamma_env, **item.env}
        return ExpressionTypeCheckSuccess(
            type=gtypes.TupleType([e.type for e in type_check_results]), env=gamma_env
        )


def type_check_map(expr: MapExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    type_check_results_dict = {}
    errors: t.List[t.Tuple[ExpressionContext, ExpressionTypeCheckError]] = []
    for k in expr.map:
        item_type_check_result = type_check(expr.map[k], gamma_env, delta_env)
        if isinstance(item_type_check_result, ExpressionTypeCheckError):
            errors.append((MapExpressionContext(expr, key=k), item_type_check_result))
        else:
            type_check_results_dict[k] = item_type_check_result
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, errors=errors)
    else:
        gamma_env = {}
        for k in type_check_results_dict:
            gamma_env = {**gamma_env, **type_check_results_dict[k].env}
        return ExpressionTypeCheckSuccess(
            type=gtypes.MapType({k: tau.type for k, tau in type_check_results_dict.items()}), env=gamma_env
        )


def type_check_unary_op(expr: UnaryOpExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    expression_type_check_result = type_check(expr.expression, gamma_env, delta_env)
    if isinstance(expression_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr, errors=[(UnaryOpContext(expression=expr), expression_type_check_result)]
        )
    if valid_result_types := [
        ret_type for arg_type, ret_type in expr.op.types
        if gtypes.is_subtype(expression_type_check_result.type, arg_type)
    ]:
        return ExpressionTypeCheckSuccess(valid_result_types[0], expression_type_check_result.env)
    return BaseExpressionTypeCheckError(
        expression=expr,
        kind=ExpressionErrorEnum.incompatible_type_for_unary_operator,
        args={"expr": expr.expression, "tau": expression_type_check_result.type, "op": expr.op.value}
    )


def type_check_binary_op(expr: BinaryOpExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    left_type_check_result = type_check(expr.left_expression, gamma_env, delta_env)
    right_type_check_result = type_check(expr.right_expression, gamma_env, delta_env)
    if isinstance(left_type_check_result, ExpressionTypeCheckError) and isinstance(right_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            errors=[
                (BinaryOpContext(expression=expr, is_left=True), left_type_check_result),
                (BinaryOpContext(expression=expr, is_left=False), right_type_check_result)
            ]
        )
    if isinstance(left_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            errors=[(BinaryOpContext(expression=expr, is_left=True), left_type_check_result)]
        )
    if isinstance(right_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            errors=[(BinaryOpContext(expression=expr, is_left=False), right_type_check_result)]
        )
    if valid_result_types := [
        ret_type for left_arg_type, right_arg_type, ret_type in expr.op.types
        if (
            gtypes.is_subtype(left_type_check_result.type, left_arg_type)
            and
            gtypes.is_subtype(right_type_check_result.type, right_arg_type)
        )
    ]:
        return ExpressionTypeCheckSuccess(
            type=valid_result_types[0],
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


def type_check_pattern_match(expr: PatternMatchExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    expression_type_check_result = type_check(expr.expression, gamma_env, delta_env)
    if isinstance(expression_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr, errors=[(PatternMatchExpressionContext(expr.expression), expression_type_check_result)]
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
        return ExpressionTypeCheckSuccess(
            pattern_match_result.type, {**expression_type_check_result.env, **pattern_match_result.env}
        )


def type_check_if_else(expr: IfElseExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    cond_type_check_result = type_check(expr.condition, gamma_env, delta_env)
    if isinstance(cond_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr, errors=[(IfElseExpressionContext(expression=expr, branch=None), cond_type_check_result)]
        )
    if not gtypes.is_subtype(cond_type_check_result.type, gtypes.BooleanType()):
        return NestedExpressionTypeCheckError(
            expression=expr, errors=[(
                IfElseExpressionContext(expression=expr, branch=None),
                BaseExpressionTypeCheckError(
                    expression=expr,
                    kind=ExpressionErrorEnum.type_is_not_boolean,
                    args={"tau": cond_type_check_result.type}
                )
            )]
        )
    errors: t.List[t.Tuple[ExpressionContext, ExpressionTypeCheckError]] = []
    if_type_check_result = type_check(expr.if_expression, cond_type_check_result.env, delta_env)
    if isinstance(if_type_check_result, ExpressionTypeCheckError):
        errors.append((IfElseExpressionContext(expression=expr, branch=True), if_type_check_result))
    if expr.else_expression is not None:
        else_type_check_result = type_check(expr.else_expression, cond_type_check_result.env, delta_env)
        if isinstance(else_type_check_result, ExpressionTypeCheckError):
            errors.append((IfElseExpressionContext(expression=expr, branch=False), else_type_check_result))
    else:
        else_type_check_result = if_type_check_result
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, errors=errors)

    assert isinstance(if_type_check_result, ExpressionTypeCheckSuccess)
    assert isinstance(else_type_check_result, ExpressionTypeCheckSuccess)
    ret_type, ret_env = if_type_check_result.type, if_type_check_result.env
    if expr.else_expression:
        aux = gtypes.supremum(if_type_check_result.type, else_type_check_result.type)
        if isinstance(aux, gtypes.TypingError):
            return BaseExpressionTypeCheckError(
                expression=expr,
                kind=ExpressionErrorEnum.incompatible_types_for_if_else,
                args={"tau1": if_type_check_result.type, "tau2": else_type_check_result.type}
            )
        ret_type = aux
    return ExpressionTypeCheckSuccess(ret_type, cond_type_check_result.env)


def type_check_seq(expr: SeqExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    left_type_check_expression = type_check(expr.left_expression, gamma_env, delta_env)
    if isinstance(left_type_check_expression, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr, errors=[(SeqExpressionContext(expr, is_left=True), left_type_check_expression)]
        )
    else:
        right_type_check_expression = type_check(
            expr.right_expression, left_type_check_expression.env, delta_env
        )
        if isinstance(right_type_check_expression, ExpressionTypeCheckError):
            return NestedExpressionTypeCheckError(
                expression=expr, errors=[(SeqExpressionContext(expr, is_left=False), right_type_check_expression)]
            )
        return ExpressionTypeCheckSuccess(
            right_type_check_expression.type,
            {**left_type_check_expression.env, **right_type_check_expression.env}
        )


def type_check_cond(expr: CondExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    errors: t.List[t.Tuple[ExpressionContext, ExpressionTypeCheckError]] = []
    branches_type_check_results = []
    for i in range(len(expr.clauses)):
        cond_type_check_expression = type_check(expr.clauses[i][0], gamma_env, delta_env)
        if isinstance(cond_type_check_expression, ExpressionTypeCheckError):
            errors.append((CondExpressionContext(expr, branch=i, cond=True), cond_type_check_expression))
            continue
        if not gtypes.is_subtype(cond_type_check_expression.type, gtypes.BooleanType()):
            errors.append(
                (
                    CondExpressionContext(expr, branch=i, cond=True),
                    BaseExpressionTypeCheckError(
                        expression=expr.clauses[i][0],
                        kind=ExpressionErrorEnum.type_is_not_boolean,
                        args={"tau": cond_type_check_expression.type}
                    )
                )
            )
            continue

        do_type_check_expression = type_check(expr.clauses[i][1], cond_type_check_expression.env, delta_env)
        if isinstance(do_type_check_expression, ExpressionTypeCheckError):
            errors.append((CondExpressionContext(expr, branch=i, cond=False), do_type_check_expression))
            continue
        branches_type_check_results.append(do_type_check_expression)
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, errors=errors)
    ret_type = branches_type_check_results[0].type
    for i in range(len(branches_type_check_results) - 1):
        aux = gtypes.supremum(ret_type, branches_type_check_results[i + 1].type)
        if isinstance(aux, gtypes.TypingError):
            return BaseExpressionTypeCheckError(
                expression=expr,
                kind=ExpressionErrorEnum.incompatible_types_for_cond,
                args={"tau1": ret_type, "tau2": branches_type_check_results[i + 1]}
            )
        ret_type = aux
    return ExpressionTypeCheckSuccess(ret_type, gamma_env)


def type_check_case(expr: CaseExpression, gamma_env: TypeEnv, delta_env: TypeEnv) -> ExpressionTypeCheckResult:
    case_input_type_check_result = type_check(expr.expression, gamma_env, delta_env)
    if isinstance(case_input_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            errors=[(CaseExpressionContext(expr, branch=None, pattern=False), case_input_type_check_result)]
        )
    errors: t.List[t.Tuple[ExpressionContext, ExpressionTypeCheckError]] = []
    case_type_check_results = []
    for i in range(len(expr.clauses)):
        pattern_match_result = pattern.pattern_match(
            expr.clauses[i][0], case_input_type_check_result.type, gamma_env, delta_env
        )
        if isinstance(pattern_match_result, pattern.PatternMatchError):
            errors.append(
                (
                    CaseExpressionContext(expr, branch=i, pattern=True),
                    BaseExpressionTypeCheckError(
                        expression=PatternMatchExpression(expr.clauses[i][0], expr.expression),
                        kind=ExpressionErrorEnum.pattern_match,
                        args={
                            "tau": case_input_type_check_result.type,
                            "pattern": expr.clauses[i][0],
                            "pattern_match_error": pattern_match_result
                        }
                    )
                )
            )
            continue

        assert isinstance(pattern_match_result, pattern.PatternMatchSuccess)
        do_type_check_expression = type_check(expr.clauses[i][1], pattern_match_result.env, delta_env)
        if isinstance(do_type_check_expression, ExpressionTypeCheckError):
            errors.append((CaseExpressionContext(expr, branch=i, pattern=False), do_type_check_expression))
            continue
        case_type_check_results.append(do_type_check_expression)
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, errors=errors)
    ret_type = case_type_check_results[0].type
    for i in range(len(case_type_check_results) - 1):
        aux = gtypes.supremum(ret_type, case_type_check_results[i + 1].type)
        if isinstance(aux, gtypes.TypingError):
            return BaseExpressionTypeCheckError(
                expression=expr,
                kind=ExpressionErrorEnum.incompatible_types_for_cond,
                args={"tau1": ret_type, "tau2": case_type_check_results[i + 1]}
            )
        ret_type = aux
    return ExpressionTypeCheckSuccess(ret_type, case_input_type_check_result.env)
