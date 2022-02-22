import typing as t
from dataclasses import dataclass
from enum import Enum

from . import pattern
from . import types as gtypes
from .exception import SyntaxException


class UnaryOpEnum(Enum):
    negation = "!"
    negative = "-"
    absolute_value = "abs"

    @property
    def is_infix(self):
        return self not in [UnaryOpEnum.absolute_value]


class BinaryOpEnum(Enum):
    conjunction = "and"
    disjunction = "or"
    sum = "+"
    subtraction = "-"
    multiplication = "*"
    division = "/"
    integer_division = "div"
    integer_reminder = "rem"
    maximum = "max"
    minimum = "min"
    concatenation = "++"
    unconcatenation = "--"
    equality = "=="

    @property
    def is_infix(self):
        return self not in [
            BinaryOpEnum.integer_division,
            BinaryOpEnum.integer_reminder,
            BinaryOpEnum.maximum,
            BinaryOpEnum.minimum,
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
class TupleExpression(Expression):
    items: t.List[Expression]

    def __str__(self):
        return "{" + ",".join([str(item) for item in self.items]) + "}"


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
class MapExpression(Expression):
    map: t.OrderedDict[t.Union[int, float, bool, str], Expression]

    def __str__(self):
        keys = self.map.keys()
        str_values = [str(v) for _, v in self.map.items()]
        return "%{" + ",".join([f"{k}: {v}" for (k, v) in zip(keys, str_values)]) + "}"


@dataclass
class PatternMatchExpression(Expression):
    pattern: pattern.Pattern
    expression: Expression

    def __str__(self):
        return f"{self.pattern} = {self.expression}"


@dataclass
class SeqExpression(Expression):
    left_expression: Expression
    right_expression: Expression

    def __str__(self):
        return f"{self.left_expression}; {self.right_expression}"


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
