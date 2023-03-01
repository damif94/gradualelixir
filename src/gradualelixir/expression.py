import typing as t
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum

from gradualelixir import gtypes, pattern
from gradualelixir.exception import SyntaxRestrictionError
from gradualelixir.utils import Bcolors, enumerate_list, ordinal


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
                (gtypes.NumberType(), gtypes.NumberType()),
                (gtypes.AnyType(), gtypes.AnyType()),
            ]
        else:
            assert self is UnaryOpEnum.negation
            return [
                (gtypes.AtomLiteralType("true"), gtypes.AtomLiteralType("false")),
                (gtypes.AtomLiteralType("false"), gtypes.AtomLiteralType("true")),
                (gtypes.BooleanType(), gtypes.BooleanType()),
                (gtypes.AnyType(), gtypes.AnyType()),
            ]

    @property
    def maximal_argument_type(self) -> gtypes.Type:
        acc: gtypes.Type = None  # type: ignore
        for arg_type, _ in self.types:
            if isinstance(arg_type, gtypes.AnyType):
                # this computation is at the static signatures
                continue
            new_acc = gtypes.supremum(acc, arg_type) if acc is not None else arg_type
            assert not isinstance(new_acc, gtypes.TypingError)
            acc = new_acc
        return acc

    def get_return_type(self, type: gtypes.Type) -> t.Optional[gtypes.Type]:
        for arg_type, ret_type in self.types:
            if gtypes.is_subtype(type, arg_type, consistent=False):
                return ret_type
        return None


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
    inequality = "!="
    lower = "<"
    lower_or_equal = "<="
    greater = ">"
    greater_or_equal = ">="
    identity = "==="
    inidentity = "!=="

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
        # TODO[improvements] adding term would unlock 'untyped' operators like
        #   ==, or !,&,||

        # TODO bug when any is provided - maybe on inverse order
        if self is BinaryOpEnum.conjunction:
            return [
                (
                    gtypes.AtomLiteralType("true"),
                    gtypes.AtomLiteralType("true"),
                    gtypes.AtomLiteralType("true"),
                ),
                (
                    gtypes.AtomLiteralType("false"),
                    gtypes.BooleanType(),
                    gtypes.AtomLiteralType("false"),
                ),
                (
                    gtypes.BooleanType(),
                    gtypes.AtomLiteralType("false"),
                    gtypes.AtomLiteralType("false"),
                ),
                (gtypes.BooleanType(), gtypes.BooleanType(), gtypes.BooleanType()),
                (
                    gtypes.AnyType(),
                    gtypes.AtomLiteralType("false"),
                    gtypes.AtomLiteralType("false"),
                ),
                (
                    gtypes.AtomLiteralType("false"),
                    gtypes.AnyType(),
                    gtypes.AtomLiteralType("false"),
                ),
                (
                    gtypes.BooleanType(),
                    gtypes.AnyType(),
                    gtypes.AnyType(),
                ),
                (
                    gtypes.AnyType(),
                    gtypes.BooleanType(),
                    gtypes.AnyType(),
                ),
                (
                    gtypes.AnyType(),
                    gtypes.AnyType(),
                    gtypes.AnyType(),
                ),
            ]
        if self is BinaryOpEnum.disjunction:
            return [
                (
                    gtypes.AtomLiteralType("false"),
                    gtypes.AtomLiteralType("false"),
                    gtypes.AtomLiteralType("false"),
                ),
                (
                    gtypes.AtomLiteralType("true"),
                    gtypes.BooleanType(),
                    gtypes.AtomLiteralType("true"),
                ),
                (
                    gtypes.BooleanType(),
                    gtypes.AtomLiteralType("true"),
                    gtypes.AtomLiteralType("true"),
                ),
                (gtypes.BooleanType(), gtypes.BooleanType(), gtypes.BooleanType()),
                (
                    gtypes.AnyType(),
                    gtypes.AtomLiteralType("true"),
                    gtypes.AtomLiteralType("true"),
                ),
                (
                    gtypes.AtomLiteralType("true"),
                    gtypes.AnyType(),
                    gtypes.AtomLiteralType("true"),
                ),
                (
                    gtypes.BooleanType(),
                    gtypes.AnyType(),
                    gtypes.AnyType(),
                ),
                (
                    gtypes.AnyType(),
                    gtypes.BooleanType(),
                    gtypes.AnyType(),
                ),
                (
                    gtypes.AnyType(),
                    gtypes.AnyType(),
                    gtypes.AnyType(),
                ),
            ]
        elif self in [BinaryOpEnum.sum, BinaryOpEnum.product, BinaryOpEnum.subtraction]:
            return [
                (gtypes.IntegerType(), gtypes.IntegerType(), gtypes.IntegerType()),
                (gtypes.FloatType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.IntegerType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.FloatType(), gtypes.IntegerType(), gtypes.FloatType()),
                (gtypes.FloatType(), gtypes.NumberType(), gtypes.FloatType()),
                (gtypes.NumberType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.NumberType(), gtypes.NumberType(), gtypes.NumberType()),
                (gtypes.AnyType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.FloatType(), gtypes.AnyType(), gtypes.FloatType()),
                (gtypes.AnyType(), gtypes.NumberType(), gtypes.AnyType()),
                (gtypes.NumberType(), gtypes.AnyType(), gtypes.AnyType()),
                (gtypes.AnyType(), gtypes.AnyType(), gtypes.AnyType()),
            ]
        elif self is BinaryOpEnum.division:
            return [
                (gtypes.NumberType(), gtypes.NumberType(), gtypes.FloatType()),
                (gtypes.AnyType(), gtypes.NumberType(), gtypes.FloatType()),
                (gtypes.NumberType(), gtypes.AnyType(), gtypes.FloatType()),
                (gtypes.AnyType(), gtypes.AnyType(), gtypes.FloatType()),
            ]
        elif self in [BinaryOpEnum.integer_reminder, BinaryOpEnum.integer_division]:
            return [
                (gtypes.IntegerType(), gtypes.IntegerType(), gtypes.IntegerType()),
                (gtypes.AnyType(), gtypes.IntegerType(), gtypes.IntegerType()),
                (gtypes.IntegerType(), gtypes.AnyType(), gtypes.IntegerType()),
                (gtypes.AnyType(), gtypes.AnyType(), gtypes.IntegerType()),
            ]
        elif self in [BinaryOpEnum.maximum, BinaryOpEnum.minimum]:
            return [
                (gtypes.IntegerType(), gtypes.IntegerType(), gtypes.IntegerType()),
                (gtypes.FloatType(), gtypes.FloatType(), gtypes.FloatType()),
                (gtypes.NumberType(), gtypes.NumberType(), gtypes.NumberType()),
                (gtypes.IntegerType(), gtypes.AnyType(), gtypes.AnyType()),
                (gtypes.AnyType(), gtypes.IntegerType(), gtypes.AnyType()),
                (gtypes.FloatType(), gtypes.AnyType(), gtypes.AnyType()),
                (gtypes.AnyType(), gtypes.FloatType(), gtypes.AnyType()),
                (gtypes.NumberType(), gtypes.AnyType(), gtypes.NumberType()),
                (gtypes.AnyType(), gtypes.NumberType(), gtypes.NumberType()),
                (gtypes.AnyType(), gtypes.AnyType(), gtypes.AnyType()),
            ]
        elif self in [
            BinaryOpEnum.identity,
            BinaryOpEnum.inidentity,
            BinaryOpEnum.lower,
            BinaryOpEnum.lower_or_equal,
            BinaryOpEnum.greater,
            BinaryOpEnum.greater_or_equal,
        ]:
            return [
                (gtypes.NumberType(), gtypes.NumberType(), gtypes.BooleanType()),
            ]
        else:
            assert self in [
                BinaryOpEnum.equality,
                BinaryOpEnum.inequality
            ]
            # TODO[improvements] improve so that if x!= y
            #  (gtypes.AtomLiteralType(value=x), gtypes.AtomLiteralType(value=y)) raises error
            return [
                (gtypes.AtomType(), gtypes.AtomType(), gtypes.BooleanType()),
                (gtypes.AtomType(), gtypes.AnyType(), gtypes.BooleanType()),
                (gtypes.AnyType(), gtypes.AtomType(), gtypes.BooleanType()),
                (gtypes.AnyType(), gtypes.AnyType(), gtypes.BooleanType()),
            ]

    @property
    def get_maximal_argument_types(self) -> t.Tuple[gtypes.Type, gtypes.Type]:
        acc: t.Tuple[gtypes.Type, gtypes.Type] = None  # type: ignore
        for left_arg_type, right_arg_type, _ in self.types:
            if isinstance(left_arg_type, gtypes.AnyType) or isinstance(right_arg_type, gtypes.AnyType):
                # this computation is at the static signatures
                continue
            if acc:
                new_acc = (gtypes.supremum(acc[0], left_arg_type), gtypes.supremum(acc[1], right_arg_type))
            else:
                new_acc = (left_arg_type, right_arg_type)
            new_acc_0, new_acc_1 = new_acc
            assert isinstance(new_acc_0, gtypes.Type)
            assert isinstance(new_acc_1, gtypes.Type)
            acc = new_acc  # type: ignore
        return acc

    def get_return_type(self, left_type: gtypes.Type, right_type: gtypes.Type) -> t.Optional[gtypes.Type]:
        for left_arg_type, right_arg_type, ret_type in self.types:
            if (
                gtypes.is_subtype(left_type, left_arg_type, consistent=False)
                and gtypes.is_subtype(right_type, right_arg_type, consistent=False)
            ):
                return ret_type
        return None


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
        if isinstance(self.value, int):
            return str(self.value) + ".0"
        return str(self.value)


# TODO make AtomLiteralSetExpression
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
        return "%{" + ",".join([f"{k} => {v}" for (k, v) in zip(keys, str_values)]) + "}"


@dataclass
class UnaryOpExpression(Expression):
    op: UnaryOpEnum
    argument: Expression

    def __str__(self):
        if self.op.is_infix:
            return f"{self.op.value} {self.argument}"
        else:
            return f"{self.op.value}({self.argument})"


@dataclass
class BinaryOpExpression(Expression):
    op: BinaryOpEnum
    left: Expression
    right: Expression

    def __str__(self):
        if self.op.is_infix:
            return f"{self.left} {self.op.value} {self.right}"
        else:
            return f"{self.op.value}({self.left}, {self.right})"


@dataclass
class PatternMatchExpression(Expression):
    pattern: pattern.Pattern
    expression: Expression

    def __str__(self):
        return f"{self.pattern} = {self.expression}"


@dataclass
class IfElseExpression(Expression):
    condition: Expression
    if_clause: Expression
    else_clause: Expression

    def __str__(self):
        return f"if {self.condition} do\n" f"  {self.if_clause}\n" f"else\n" f"{self.else_clause}\n" f"end"


@dataclass
class SeqExpression(Expression):
    left: Expression
    right: Expression

    def __str__(self):
        return f"{self.left}\n{self.right}"


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
class CaseExpression(Expression):
    test: Expression
    clauses: t.List[t.Tuple[pattern.Pattern, Expression]]

    def __str__(self):
        res = f"case {self.test} do\n"
        for clause in self.clauses:
            res += f"{clause[0]} -> {clause[1]}\n"
        res += "end"
        return res


@dataclass
class AnonymizedFunctionExpression(Expression):
    function_name: str
    arity: int

    def __str__(self):
        return f"(&{self.function_name}/{self.arity})"


@dataclass
class FunctionCallExpression(Expression):
    function_name: str
    arguments: t.List[Expression]

    def __str__(self):
        arguments_str = ", ".join([str(arg) for arg in self.arguments])
        return f"{self.function_name}({arguments_str})"


@dataclass
class AnonCallExpression(Expression):
    function: Expression
    arguments: t.List[Expression]

    def __str__(self):
        arguments_str = ", ".join([str(arg) for arg in self.arguments])
        return f"({self.function}).({arguments_str})"


def format_expression(expression: Expression, padding="") -> str:
    needs_formatting = False
    if len(str(expression).split("\n")) > 1 or len(str(expression)) > 120:  # is multiline or expression is too long
        needs_formatting = True

    if needs_formatting:  # is multiline
        from .elixir_port import format_code

        msg = format_code(str(expression))
        return "\n\n" + "\n".join([padding + m for m in msg.split("\n")])
    else:
        return f" {expression}"


class ExpressionErrorEnum(Enum):
    identifier_not_found_in_environment = "Couldn't find variable {identifier} in the environment"
    incompatible_type_for_unary_operator = "The argument of type {type} is not a valid argument for builtin {op}/1"
    incompatible_types_for_binary_operator = (
        "The arguments, of types {type1} and {type2}, are not together valid arguments for builtin {op}/2"
    )
    pattern_match = "Pattern match type errors\n\n" f"{Bcolors.ENDC}" "{pattern_match_error}"
    bad_type_for_list_tail = (
        "The type for the tail is {type} is not a list"
    )
    incompatible_types_for_list = (
        "The type for the head, {type1}, and the type for the tail, {type2} don't have supremum"
    )
    incompatible_types_for_if_else = (
        "The type inferred for the if branch, {type1}, and the type inferred for the else branch, "
        "{type2} don't have supremum"
    )
    inferred_type_is_not_as_expected = "The type inferred for the expression, {type1} is not a subtype of {type2}"
    incompatible_types_for_branches = "The types inferred for the branches, {types}, don't have a joint supremum"
    function_not_declared = "The function with signature {name}/{arity} was not declared"
    identifier_type_is_not_arrow_of_expected_arity = (
        "The type inferred for {identifier}, {type}, is not a function of {arity} arguments"
    )


class ExpressionContext:
    pass


@dataclass
class ListExpressionContext(ExpressionContext):
    head: bool

    def __str__(self):
        if self.head:
            return "In the head expression"
        return "In the tail expression"


@dataclass
class TupleExpressionContext(ExpressionContext):
    n: int

    def __str__(self):
        return f"In the {ordinal(self.n + 1)} position"


@dataclass
class MapExpressionContext(ExpressionContext):
    key: gtypes.MapKey

    def __str__(self):
        return f"In the expression for key {self.key}"


@dataclass
class UnaryOpContext(ExpressionContext):
    def __str__(self):
        return "In the operator's argument"


@dataclass
class BinaryOpContext(ExpressionContext):
    is_left: bool

    def __str__(self):
        if self.is_left:
            return "In the operator's left argument"
        else:
            return "In the operator's right argument"


@dataclass
class PatternMatchExpressionContext(ExpressionContext):
    def __str__(self):
        return "In the expression"


@dataclass
class IfElseExpressionContext(ExpressionContext):
    branch: t.Optional[bool]

    def __str__(self):
        if self.branch is True:
            return "In the condition"
        elif self.branch is False:
            return "In the if branch"
        else:
            return "In the else branch"


@dataclass
class SeqExpressionContext(ExpressionContext):
    is_left: bool

    def __str__(self):
        if self.is_left:
            return "In the left side"
        else:
            return "In the right side"


@dataclass
class CondExpressionContext(ExpressionContext):
    cond: bool
    branch: int

    def __str__(self):
        if self.cond:
            return f"In the {ordinal(self.branch + 1)} condition"
        return f"In the {ordinal(self.branch + 1)} expression"


@dataclass
class CaseExpressionContext(ExpressionContext):
    pattern: t.Optional[bool]
    branch: t.Optional[int]

    def __str__(self):
        if self.branch is None:
            return "In the case expression"
        if self.pattern is True:
            return f"In the {ordinal(self.branch + 1)} pattern"
        return f"In the {ordinal(self.branch + 1)} expression"


@dataclass
class FunctionCallExpressionContext(ExpressionContext):
    argument: int

    def __str__(self):
        return f"In the {ordinal(self.argument + 1)} argument"


@dataclass
class AnonCallExpressionContext(ExpressionContext):
    argument: t.Optional[int]

    def __str__(self):
        if self.argument is not None:
            return f"In the {ordinal(self.argument + 1)} argument"
        return "In the called expression"


class ExpressionTypeCheckError:
    expression: Expression

    def _message(self, padding="", env: gtypes.TypeEnv = None, specs_env: gtypes.SpecsEnv = None):
        raise NotImplementedError()

    @staticmethod
    def env_message(padding="", env: gtypes.TypeEnv = None, specs_env: gtypes.SpecsEnv = None):
        env_msg = ""
        specs_msg = ""
        eol = ""
        if env is not None:
            env_msg = f"{padding}{Bcolors.OKBLUE}Variables:{Bcolors.ENDC} {env}\n"
            eol = "\n"
        if specs_env is not None:
            specs_msg = f"{padding}{Bcolors.OKBLUE}Specs:{Bcolors.ENDC} {specs_env}\n"
            eol = "\n"
        return env_msg + specs_msg + eol

    def message(self, padding="", env: gtypes.TypeEnv = None, specs_env: gtypes.SpecsEnv = None):
        expression_msg = format_expression(expression=self.expression, padding=padding + "    ")
        env_msg = self.env_message(padding, env, specs_env)
        return (
            f"{padding}{Bcolors.OKBLUE}Type errors found inside expression{Bcolors.ENDC} "
            f"{expression_msg}\n\n"
            f"{env_msg}"
            f"{self._message(padding, env, specs_env)}\n"
        )


@dataclass
class BaseExpressionTypeCheckError(ExpressionTypeCheckError):
    expression: Expression
    kind: ExpressionErrorEnum
    args: t.Dict[str, t.Any]

    def __str__(self):
        return self.message()

    def _message(self, padding="", _env: gtypes.TypeEnv = None, _specs_env: gtypes.SpecsEnv = None):
        error_msg = self.kind.value.format(**{k: str(arg) for k, arg in self.args.items()})
        error_msg = "\n".join([padding + "    " + line for line in error_msg.split("\n")])
        return f"{Bcolors.FAIL}{error_msg}{Bcolors.ENDC}\n"


@dataclass
class ContextExpressionTypeCheckError:
    context: ExpressionContext
    env: gtypes.TypeEnv
    error: ExpressionTypeCheckError


@dataclass
class NestedExpressionTypeCheckError(ExpressionTypeCheckError):
    expression: Expression
    bullets: t.List[ContextExpressionTypeCheckError]

    def __str__(self):
        return self.message()

    def _message(self, padding="", env: gtypes.TypeEnv = None, specs_env: gtypes.SpecsEnv = None):
        env_msg = self.env_message(padding + "    ", env, specs_env)
        item_msgs = []
        for bullet in self.bullets:
            bullet_expression_msg = format_expression(expression=bullet.error.expression, padding=padding + "    ")
            bullet_msg = bullet.error._message(padding + "    ", bullet.env, specs_env)
            item_msgs.append(
                f"{padding}{Bcolors.OKBLUE}  > {bullet.context}{Bcolors.ENDC}"
                f"{bullet_expression_msg}\n\n"
                f"{env_msg}"
                f"{bullet_msg}\n"
            )
        return "".join(item_msgs)


@dataclass
class ExpressionTypeCheckSuccess:
    expression: Expression
    type: gtypes.Type
    env: gtypes.TypeEnv
    specs_env: gtypes.SpecsEnv
    exported_env: gtypes.TypeEnv
    children: t.Dict[str, t.Any]

    def message(self, padding=""):
        expression_msg = format_expression(self.expression, padding=padding + "    ")
        return (
            f"{padding}{Bcolors.OKBLUE}Type check success for{Bcolors.ENDC} {expression_msg}\n\n"
            f"{padding}{Bcolors.OKBLUE}Variables:{Bcolors.ENDC} {self.env}\n"
            f"{padding}{Bcolors.OKBLUE}Specs:{Bcolors.ENDC} {self.specs_env}\n"
            f"{padding}{Bcolors.OKBLUE}Assigned Type:{Bcolors.ENDC} {self.type}\n"
            f"{padding}{Bcolors.OKBLUE}Exported Variables:{Bcolors.ENDC} {self.exported_env}\n"
        )


ExpressionTypeCheckResult = t.Union[ExpressionTypeCheckSuccess, ExpressionTypeCheckError]


def type_check(expr: Expression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv) -> ExpressionTypeCheckResult:
    if isinstance(expr, IdentExpression):
        return type_check_var(expr, env, specs_env)
    if isinstance(expr, LiteralExpression):
        return type_check_literal(expr, env, specs_env)
    if isinstance(expr, ElistExpression):
        return type_check_elist(expr, env, specs_env)
    if isinstance(expr, ListExpression):
        return type_check_list(expr, env, specs_env)
    if isinstance(expr, TupleExpression):
        return type_check_tuple(expr, env, specs_env)
    if isinstance(expr, MapExpression):
        return type_check_map(expr, env, specs_env)
    if isinstance(expr, UnaryOpExpression):
        return type_check_unary_op(expr, env, specs_env)
    if isinstance(expr, BinaryOpExpression):
        return type_check_binary_op(expr, env, specs_env)
    if isinstance(expr, PatternMatchExpression):
        return type_check_pattern_match(expr, env, specs_env)
    if isinstance(expr, IfElseExpression):
        return type_check_if_else(expr, env, specs_env)
    if isinstance(expr, SeqExpression):
        return type_check_seq(expr, env, specs_env)
    if isinstance(expr, CondExpression):
        return type_check_cond(expr, env, specs_env)
    if isinstance(expr, CaseExpression):
        return type_check_case(expr, env, specs_env)
    if isinstance(expr, AnonymizedFunctionExpression):
        return type_check_anon(expr, env, specs_env)
    if isinstance(expr, FunctionCallExpression):
        return type_check_function_call(expr, env, specs_env)
    else:
        assert isinstance(expr, AnonCallExpression)
        return type_check_anonymous_call(expr, env, specs_env)


def type_check_var(
    expr: IdentExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    if (ret_type := env.get(expr.identifier)) is not None:
        return ExpressionTypeCheckSuccess(
            expression=expr, env=env, specs_env=specs_env, type=ret_type, exported_env=gtypes.TypeEnv(), children={}
        )
    else:
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.identifier_not_found_in_environment,
            args={"identifier": expr.identifier},
        )


def type_check_literal(
    expr: LiteralExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    return ExpressionTypeCheckSuccess(
        expression=expr, env=env, specs_env=specs_env, type=expr.type, exported_env=gtypes.TypeEnv(), children={}
    )


def type_check_elist(
    expr: ElistExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    return ExpressionTypeCheckSuccess(
        expression=expr, env=env, specs_env=specs_env, type=gtypes.ElistType(), exported_env=gtypes.TypeEnv(), children={}
    )


def type_check_list(expr: ListExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv) -> ExpressionTypeCheckResult:
    head_type_check_result = type_check(expr.head, env, specs_env)
    tail_type_check_result = type_check(expr.tail, env, specs_env)
    if isinstance(head_type_check_result, ExpressionTypeCheckError) and isinstance(
        tail_type_check_result, ExpressionTypeCheckError
    ):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[
                ContextExpressionTypeCheckError(ListExpressionContext(head=True), env, head_type_check_result),
                ContextExpressionTypeCheckError(ListExpressionContext(head=False), env, tail_type_check_result),
            ],
        )
    if isinstance(head_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[ContextExpressionTypeCheckError(ListExpressionContext(head=True), env, head_type_check_result)],
        )
    if isinstance(tail_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[ContextExpressionTypeCheckError(ListExpressionContext(head=False), env, tail_type_check_result)],
        )
    result_type = gtypes.supremum(gtypes.ListType(head_type_check_result.type), tail_type_check_result.type)
    if not isinstance(result_type, gtypes.TypingError):
        return ExpressionTypeCheckSuccess(
            env=env,
            specs_env=specs_env,
            expression=expr,
            type=result_type,
            exported_env=gtypes.TypeEnv.merge(head_type_check_result.exported_env, tail_type_check_result.exported_env),
            children={"head": head_type_check_result, "tail": tail_type_check_result},
        )
    elif not isinstance(tail_type_check_result.type, gtypes.ListType):
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.bad_type_for_list_tail,
            args={"type": tail_type_check_result.type},
        )
    else:
        assert isinstance(tail_type_check_result.type, gtypes.ListType)
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.incompatible_types_for_list,
            args={"type1": head_type_check_result.type, "type2": tail_type_check_result.type.type}
        )


def type_check_tuple(
    expr: TupleExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    items_type_check_results = []
    errors: t.List[ContextExpressionTypeCheckError] = []
    for i in range(len(expr.items)):
        item_type_check_result = type_check(expr.items[i], env, specs_env)
        if isinstance(item_type_check_result, ExpressionTypeCheckError):
            errors.append(ContextExpressionTypeCheckError(TupleExpressionContext(n=i), env, item_type_check_result))
        else:
            items_type_check_results.append(item_type_check_result)
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, bullets=errors)
    else:
        exported_env = gtypes.TypeEnv()
        for item in items_type_check_results:
            exported_env = gtypes.TypeEnv.merge(exported_env, item.exported_env)
        return ExpressionTypeCheckSuccess(
            env=env,
            specs_env=specs_env,
            expression=expr,
            type=gtypes.TupleType([e.type for e in items_type_check_results]),
            exported_env=exported_env,
            children={"items": items_type_check_results},
        )


def type_check_map(expr: MapExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv) -> ExpressionTypeCheckResult:
    type_check_results_dict = OrderedDict()
    errors: t.List[ContextExpressionTypeCheckError] = []
    for k in expr.map:
        item_type_check_result = type_check(expr.map[k], env, specs_env)
        if isinstance(item_type_check_result, ExpressionTypeCheckError):
            errors.append(ContextExpressionTypeCheckError(MapExpressionContext(key=k), env, item_type_check_result))
        else:
            type_check_results_dict[k] = item_type_check_result
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, bullets=errors)
    else:
        exported_env = gtypes.TypeEnv()
        for k in type_check_results_dict:
            exported_env = gtypes.TypeEnv.merge(exported_env, type_check_results_dict[k].exported_env)
        return ExpressionTypeCheckSuccess(
            env=env,
            specs_env=specs_env,
            expression=expr,
            type=gtypes.MapType({k: type.type for k, type in type_check_results_dict.items()}),
            exported_env=exported_env,
            children={"map": list(type_check_results_dict.values())},
        )


def type_check_unary_op(
    expr: UnaryOpExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    argument_type_check_result = type_check(expr.argument, env, specs_env)
    if isinstance(argument_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[ContextExpressionTypeCheckError(UnaryOpContext(), env, argument_type_check_result)],
        )

    result_type = expr.op.get_return_type(argument_type_check_result.type)

    if result_type is not None:
        return ExpressionTypeCheckSuccess(
            env=env,
            expression=expr,
            specs_env=specs_env,
            type=result_type,
            exported_env=argument_type_check_result.exported_env,
            children={"argument": argument_type_check_result},
        )
    return BaseExpressionTypeCheckError(
        expression=expr,
        kind=ExpressionErrorEnum.incompatible_type_for_unary_operator,
        args={"type": argument_type_check_result.type, "op": expr.op.value},
    )


def type_check_binary_op(
    expr: BinaryOpExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    left_type_check_result = type_check(expr.left, env, specs_env)
    right_type_check_result = type_check(expr.right, env, specs_env)
    if isinstance(left_type_check_result, ExpressionTypeCheckError) and isinstance(
        right_type_check_result, ExpressionTypeCheckError
    ):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[
                ContextExpressionTypeCheckError(BinaryOpContext(is_left=True), env, left_type_check_result),
                ContextExpressionTypeCheckError(BinaryOpContext(is_left=False), env, right_type_check_result),
            ],
        )
    if isinstance(left_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[ContextExpressionTypeCheckError(BinaryOpContext(is_left=True), env, left_type_check_result)],
        )
    if isinstance(right_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[ContextExpressionTypeCheckError(BinaryOpContext(is_left=False), env, right_type_check_result)],
        )

    result_type = expr.op.get_return_type(left_type_check_result.type, right_type_check_result.type)

    if result_type is not None:
        return ExpressionTypeCheckSuccess(
            expression=expr,
            env=env,
            specs_env=specs_env,
            type=result_type,
            exported_env=gtypes.TypeEnv.merge(
                left_type_check_result.exported_env, right_type_check_result.exported_env
            ),
            children={"left": left_type_check_result, "right": right_type_check_result},
        )
    else:
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.incompatible_types_for_binary_operator,
            args={
                "type1": left_type_check_result.type,
                "type2": right_type_check_result.type,
                "op": expr.op.value,
            },
        )


def type_check_pattern_match(
    expr: PatternMatchExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    expression_type_check_result = type_check(expr.expression, env, specs_env)
    if isinstance(expression_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[
                ContextExpressionTypeCheckError(
                    PatternMatchExpressionContext(),
                    env,
                    expression_type_check_result,
                )
            ],
        )
    else:
        pattern_match_result = pattern.type_check(
            expr.pattern,
            expression_type_check_result.type,
            gtypes.TypeEnv(),
            expression_type_check_result.exported_env,
        )
        if isinstance(pattern_match_result, pattern.PatternMatchError):
            return BaseExpressionTypeCheckError(
                expression=expr,
                kind=ExpressionErrorEnum.pattern_match,
                args={
                    "type": expression_type_check_result.type,
                    "pattern": expr.pattern,
                    "pattern_match_error": pattern_match_result.message("    "),
                },
            )
        return ExpressionTypeCheckSuccess(
            env=env,
            specs_env=specs_env,
            expression=expr,
            type=pattern_match_result.refined_type,
            exported_env=gtypes.TypeEnv.merge(
                expression_type_check_result.exported_env, pattern_match_result.exported_env
            ),
            children={"expression": expression_type_check_result},
        )


def type_check_if_else(
    expr: IfElseExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    condition_type_check_result = type_check(expr.condition, env, specs_env)
    if isinstance(condition_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[
                ContextExpressionTypeCheckError(
                    IfElseExpressionContext(branch=None),
                    env,
                    condition_type_check_result,
                )
            ],
        )
    if not gtypes.is_subtype(condition_type_check_result.type, gtypes.BooleanType()):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[
                ContextExpressionTypeCheckError(
                    IfElseExpressionContext(branch=None),
                    env,
                    BaseExpressionTypeCheckError(
                        expression=expr,
                        kind=ExpressionErrorEnum.inferred_type_is_not_as_expected,
                        args={"type1": condition_type_check_result.type, "type2": gtypes.BooleanType()},
                    ),
                )
            ],
        )
    errors: t.List[ContextExpressionTypeCheckError] = []
    new_env = gtypes.TypeEnv.merge(env, condition_type_check_result.exported_env)
    if_clause_type_check_result = type_check(expr.if_clause, new_env, specs_env)
    if isinstance(if_clause_type_check_result, ExpressionTypeCheckError):
        errors.append(
            ContextExpressionTypeCheckError(
                IfElseExpressionContext(branch=True),
                new_env,
                if_clause_type_check_result,
            )
        )
    if expr.else_clause is not None:
        else_clause_type_check_result = type_check(expr.else_clause, new_env, specs_env)
        if isinstance(else_clause_type_check_result, ExpressionTypeCheckError):
            errors.append(
                ContextExpressionTypeCheckError(
                    IfElseExpressionContext(branch=False),
                    new_env,
                    else_clause_type_check_result,
                )
            )
    else:
        else_clause_type_check_result = if_clause_type_check_result
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, bullets=errors)

    assert isinstance(if_clause_type_check_result, ExpressionTypeCheckSuccess)
    assert isinstance(else_clause_type_check_result, ExpressionTypeCheckSuccess)
    ret_type = if_clause_type_check_result.type
    if expr.else_clause:
        aux = gtypes.supremum(if_clause_type_check_result.type, else_clause_type_check_result.type)
        if isinstance(aux, gtypes.TypingError):
            return BaseExpressionTypeCheckError(
                expression=expr,
                kind=ExpressionErrorEnum.incompatible_types_for_if_else,
                args={
                    "type1": if_clause_type_check_result.type,
                    "type2": else_clause_type_check_result.type,
                },
            )
        ret_type = aux
    return ExpressionTypeCheckSuccess(
        env=env,
        specs_env=specs_env,
        expression=expr,
        type=ret_type,
        exported_env=condition_type_check_result.exported_env,
        children={
            "condition": condition_type_check_result,
            "if_clause": if_clause_type_check_result,
            "else_clause": else_clause_type_check_result,
        },
    )


def type_check_seq(expr: SeqExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv) -> ExpressionTypeCheckResult:
    left_type_check_result = type_check(expr.left, env, specs_env)
    if isinstance(left_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[ContextExpressionTypeCheckError(SeqExpressionContext(is_left=True), env, left_type_check_result)],
        )
    else:
        new_env = gtypes.TypeEnv.merge(env, left_type_check_result.exported_env)
        right_type_check_result = type_check(expr.right, new_env, specs_env)
        if isinstance(right_type_check_result, ExpressionTypeCheckError):
            return NestedExpressionTypeCheckError(
                expression=expr,
                bullets=[
                    ContextExpressionTypeCheckError(
                        SeqExpressionContext(is_left=False), new_env, right_type_check_result
                    )
                ],
            )
        return ExpressionTypeCheckSuccess(
            env=env,
            specs_env=specs_env,
            expression=expr,
            type=right_type_check_result.type,
            exported_env=gtypes.TypeEnv.merge(
                left_type_check_result.exported_env, right_type_check_result.exported_env
            ),
            children={"left": left_type_check_result, "right": right_type_check_result},
        )


def type_check_cond(expr: CondExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv) -> ExpressionTypeCheckResult:
    errors: t.List[ContextExpressionTypeCheckError] = []
    clauses_type_check_results = []
    for i in range(len(expr.clauses)):
        cond_type_check_result = type_check(expr.clauses[i][0], env, specs_env)
        if isinstance(cond_type_check_result, ExpressionTypeCheckError):
            errors.append(
                ContextExpressionTypeCheckError(
                    CondExpressionContext(branch=i, cond=True),
                    env,
                    cond_type_check_result,
                )
            )
            continue
        if not gtypes.is_subtype(cond_type_check_result.type, gtypes.BooleanType()):
            errors.append(
                ContextExpressionTypeCheckError(
                    CondExpressionContext(branch=i, cond=True),
                    env,
                    BaseExpressionTypeCheckError(
                        expression=expr.clauses[i][0],
                        kind=ExpressionErrorEnum.inferred_type_is_not_as_expected,
                        args={"type1": cond_type_check_result.type, "type2": gtypes.BooleanType()},
                    ),
                )
            )
            continue

        new_env = gtypes.TypeEnv.merge(env, cond_type_check_result.exported_env)
        do_type_check_result = type_check(expr.clauses[i][1], new_env, specs_env)
        if isinstance(do_type_check_result, ExpressionTypeCheckError):
            errors.append(
                ContextExpressionTypeCheckError(
                    CondExpressionContext(branch=i, cond=False), new_env, do_type_check_result,
                )
            )
            continue
        clauses_type_check_results.append((cond_type_check_result, do_type_check_result))
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, bullets=errors)
    ret_type = clauses_type_check_results[0][1].type
    for i in range(len(clauses_type_check_results) - 1):
        aux = gtypes.supremum(ret_type, clauses_type_check_results[i + 1][1].type)
        if isinstance(aux, gtypes.TypingError):
            return BaseExpressionTypeCheckError(
                expression=expr,
                kind=ExpressionErrorEnum.incompatible_types_for_branches,
                args={"types": enumerate_list([str(clause[1].type) for clause in clauses_type_check_results])},
            )
        ret_type = aux
    return ExpressionTypeCheckSuccess(
        env=env,
        specs_env=specs_env,
        expression=expr,
        type=ret_type,
        exported_env=gtypes.TypeEnv(),
        children={"clauses": clauses_type_check_results},
    )


def type_check_case(expr: CaseExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv) -> ExpressionTypeCheckResult:
    test_type_check_result = type_check(expr.test, env, specs_env)
    if isinstance(test_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[
                ContextExpressionTypeCheckError(
                    CaseExpressionContext(branch=None, pattern=None),
                    env,
                    test_type_check_result,
                )
            ],
        )
    errors: t.List[ContextExpressionTypeCheckError] = []
    clauses_type_check_results = []
    for i in range(len(expr.clauses)):
        new_env = gtypes.TypeEnv.merge(env, test_type_check_result.exported_env)
        pattern_match_result = pattern.type_check(
            expr.clauses[i][0], test_type_check_result.type, gtypes.TypeEnv(), new_env
        )
        if isinstance(pattern_match_result, pattern.PatternMatchError):
            errors.append(
                ContextExpressionTypeCheckError(
                    CaseExpressionContext(branch=i, pattern=True),
                    new_env,
                    BaseExpressionTypeCheckError(
                        expression=PatternMatchExpression(expr.clauses[i][0], expr.test),
                        kind=ExpressionErrorEnum.pattern_match,
                        args={
                            "type": test_type_check_result.type,
                            "pattern": expr.clauses[i][0],
                            "pattern_match_error": pattern_match_result,
                        },
                    ),
                )
            )
            continue

        assert isinstance(pattern_match_result, pattern.PatternMatchSuccess)
        new_env = gtypes.TypeEnv.merge(new_env, pattern_match_result.exported_env)
        do_type_check_result = type_check(expr.clauses[i][1], new_env, specs_env)
        if isinstance(do_type_check_result, ExpressionTypeCheckError):
            errors.append(
                ContextExpressionTypeCheckError(
                    CaseExpressionContext(branch=i, pattern=False), new_env, do_type_check_result
                )
            )
            continue
        clauses_type_check_results.append((pattern_match_result, do_type_check_result))
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, bullets=errors)
    ret_type = clauses_type_check_results[0][1].type
    for i in range(len(clauses_type_check_results) - 1):
        aux = gtypes.supremum(ret_type, clauses_type_check_results[i + 1][1].type)
        if isinstance(aux, gtypes.TypingError):
            return BaseExpressionTypeCheckError(
                expression=expr,
                kind=ExpressionErrorEnum.incompatible_types_for_branches,
                args={"types": enumerate_list([str(clause[1].type) for clause in clauses_type_check_results])},
            )
        ret_type = aux
    return ExpressionTypeCheckSuccess(
        env=env,
        specs_env=specs_env,
        expression=expr,
        type=ret_type,
        exported_env=test_type_check_result.exported_env,
        children={"test": test_type_check_result, "clauses": clauses_type_check_results},
    )


def type_check_anon(
    expr: AnonymizedFunctionExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    if not (value := specs_env.get((expr.function_name, expr.arity))):
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.function_not_declared,
            args={"name": expr.function_name, "arity": expr.arity},
        )
    else:
        return ExpressionTypeCheckSuccess(
            env=env,
            specs_env=specs_env,
            expression=expr,
            type=gtypes.FunctionType(value[0], value[1]),
            exported_env=env,
            children={},
        )


def type_check_function_call(
    expr: FunctionCallExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    context_class: t.Type[FunctionCallExpressionContext] = FunctionCallExpressionContext
    function_type: gtypes.FunctionType
    if not (value := specs_env.get((expr.function_name, len(expr.arguments)))):
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.function_not_declared,
            args={"name": expr.function_name, "arity": len(expr.arguments)},
        )

    function_type = gtypes.FunctionType(value[0], value[1])

    errors: t.List[ContextExpressionTypeCheckError] = []
    arguments_type_check_results = []
    for i in range(len(expr.arguments)):
        argument_type_check_result = type_check(expr.arguments[i], env, specs_env)
        if isinstance(argument_type_check_result, ExpressionTypeCheckError):
            errors.append(
                ContextExpressionTypeCheckError(
                    context_class(argument=i),
                    env,
                    argument_type_check_result,
                )
            )
            continue
        if not gtypes.is_subtype(argument_type_check_result.type, function_type.arg_types[i]):
            errors.append(
                ContextExpressionTypeCheckError(
                    context_class(argument=i),
                    env,
                    BaseExpressionTypeCheckError(
                        expression=expr.arguments[i],
                        kind=ExpressionErrorEnum.inferred_type_is_not_as_expected,
                        args={"type1": argument_type_check_result.type, "type2": function_type.arg_types[i]},
                    ),
                )
            )
            continue
        arguments_type_check_results.append(argument_type_check_result)
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, bullets=errors)

    exported_env = gtypes.TypeEnv()
    for item in arguments_type_check_results:
        exported_env = gtypes.TypeEnv.merge(exported_env, item.exported_env)
    return ExpressionTypeCheckSuccess(
        env=env,
        specs_env=specs_env,
        expression=expr,
        type=function_type.ret_type,
        exported_env=exported_env,
        children={"arguments": arguments_type_check_results},
    )


def type_check_anonymous_call(
    expr: AnonCallExpression, env: gtypes.TypeEnv, specs_env: gtypes.SpecsEnv
) -> ExpressionTypeCheckResult:
    context_class: t.Type[AnonCallExpressionContext] = AnonCallExpressionContext
    function_type_check_result = type_check(expr.function, env, specs_env)
    if isinstance(function_type_check_result, ExpressionTypeCheckError):
        return NestedExpressionTypeCheckError(
            expression=expr,
            bullets=[
                ContextExpressionTypeCheckError(AnonCallExpressionContext(None), env, function_type_check_result)],
        )
    function_type = function_type_check_result.type
    if isinstance(function_type, gtypes.AnyType):
        # if env[x] = any, we will refine x: (any,...,any)n -> any for the
        # sake of typing x.(e1,..en)
        function_type = gtypes.FunctionType([gtypes.AnyType() for _ in expr.arguments], gtypes.AnyType())

    elif not isinstance(function_type, gtypes.FunctionType) or len(function_type.arg_types) != len(expr.arguments):
        return BaseExpressionTypeCheckError(
            expression=expr,
            kind=ExpressionErrorEnum.identifier_type_is_not_arrow_of_expected_arity,
            args={"identifier": expr.function, "type": function_type, "arity": len(expr.arguments)},
        )

    assert isinstance(function_type, gtypes.FunctionType)

    errors: t.List[ContextExpressionTypeCheckError] = []
    arguments_type_check_results = []
    for i in range(len(expr.arguments)):
        argument_type_check_result = type_check(expr.arguments[i], env, specs_env)
        if isinstance(argument_type_check_result, ExpressionTypeCheckError):
            errors.append(
                ContextExpressionTypeCheckError(
                    context_class(argument=i),
                    env,
                    argument_type_check_result,
                )
            )
            continue
        if not gtypes.is_subtype(argument_type_check_result.type, function_type.arg_types[i]):
            errors.append(
                ContextExpressionTypeCheckError(
                    context_class(argument=i),
                    env,
                    BaseExpressionTypeCheckError(
                        expression=expr.arguments[i],
                        kind=ExpressionErrorEnum.inferred_type_is_not_as_expected,
                        args={"type1": argument_type_check_result.type, "type2": function_type.arg_types[i]},
                    ),
                )
            )
            continue
        arguments_type_check_results.append(argument_type_check_result)
    if errors:
        return NestedExpressionTypeCheckError(expression=expr, bullets=errors)

    exported_env = function_type_check_result.exported_env
    for item in arguments_type_check_results:
        exported_env = gtypes.TypeEnv.merge(exported_env, item.exported_env)
    return ExpressionTypeCheckSuccess(
        env=env,
        specs_env=specs_env,
        expression=expr,
        type=function_type.ret_type,
        exported_env=exported_env,
        children={"function": function_type_check_result, "arguments": arguments_type_check_results},
    )
