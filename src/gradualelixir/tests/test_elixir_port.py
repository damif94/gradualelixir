from collections import OrderedDict

from dotenv import find_dotenv, get_key
from gradualelixir import elixir_port
from gradualelixir.expression import (
    AnonCallExpression,
    AnonymizedFunctionExpression,
    AtomLiteralExpression,
    BinaryOpEnum,
    BinaryOpExpression,
    CaseExpression,
    CondExpression,
    ElistExpression,
    Expression,
    FloatExpression,
    FunctionCallExpression,
    IdentExpression,
    IfElseExpression,
    IntegerExpression,
    ListExpression,
    MapExpression,
    PatternMatchExpression,
    SeqExpression,
    StringExpression,
    TupleExpression,
    UnaryOpEnum,
    UnaryOpExpression,
)
from gradualelixir.gtypes import (
    AtomLiteralType,
    AtomType,
    ElistType,
    FloatType,
    FunctionType,
    IntegerType,
    ListType,
    MapKey,
    MapType,
    NumberType,
    StringType,
    TupleType,
)
from gradualelixir.module import Spec
from gradualelixir.pattern import (
    AtomLiteralPattern,
    ElistPattern,
    FloatPattern,
    IdentPattern,
    IntegerPattern,
    ListPattern,
    MapPattern,
    PinIdentPattern,
    StringPattern,
    TuplePattern,
    WildPattern,
)

dotenv_path = find_dotenv()

project_path = get_key("PROJECT_PATH", dotenv_path)


def parse_expression(code):
    if isinstance(code, tuple):
        code = "\n".join(list(code))
    if isinstance(code, list):
        code = "\n".join(code)
    res, _ = elixir_port.ast_transform(code, elixir_port.SyntacticLevel.expression)
    assert isinstance(res, Expression)
    return res


def parse_pattern(code: str):
    code = code + " = {}"
    res, _ = elixir_port.ast_transform(code, elixir_port.SyntacticLevel.expression)
    assert isinstance(res, PatternMatchExpression)
    return res.pattern


def parse_type(code: str):
    code = f"@spec foo() :: {code}"
    res, _ = elixir_port.ast_transform(code, elixir_port.SyntacticLevel.spec)
    assert isinstance(res, Spec)
    return res.return_type


def test_parse_literal_expression():
    assert parse_expression("42") == IntegerExpression(42)
    assert parse_expression("42.0") == FloatExpression(42.0)
    assert parse_expression("true") == AtomLiteralExpression("true")
    assert parse_expression(":a") == AtomLiteralExpression("a")


def test_parse_data_expressions():
    assert parse_expression("{}") == TupleExpression([])
    assert parse_expression("{1}") == TupleExpression([IntegerExpression(1)])
    assert parse_expression("{1,2}") == TupleExpression([IntegerExpression(1), IntegerExpression(2)])
    assert parse_expression("{:a, \"a\"}") == TupleExpression([AtomLiteralExpression("a"), StringExpression("a")])
    assert parse_expression("{1,2,3}") == TupleExpression(
        [IntegerExpression(1), IntegerExpression(2), IntegerExpression(3)]
    )
    assert parse_expression("%{}") == MapExpression(OrderedDict([]))
    assert parse_expression("%{1 => :a}") == MapExpression(OrderedDict([(MapKey(1, IntegerType()), AtomLiteralExpression("a"))]))
    assert parse_expression("%{:a => 42.0}") == MapExpression(OrderedDict([(MapKey("a", AtomLiteralType("a")), FloatExpression(42))]))
    assert parse_expression("%{\"a\" => 42.0}") == MapExpression(OrderedDict([(MapKey("a", StringType()), FloatExpression(42))]))
    assert parse_expression("%{42.1 => true}") == MapExpression(
        OrderedDict([(MapKey(42.1, FloatType()), AtomLiteralExpression("true"))])
    )
    assert parse_expression("%{42.0 => {1,2}}") == MapExpression(
        OrderedDict(
            [
                (
                    MapKey(42.0, FloatType()),
                    TupleExpression([IntegerExpression(1), IntegerExpression(2)]),
                )
            ]
        )
    )
    assert parse_expression("%{42.0 => {1,2}}") == MapExpression(
        OrderedDict(
            [
                (
                    MapKey(42.0, FloatType()),
                    TupleExpression([IntegerExpression(1), IntegerExpression(2)]),
                )
            ]
        )
    )
    assert parse_expression("%{42.0 => %{1 => 2}}") == MapExpression(
        OrderedDict(
            [
                (
                    MapKey(42.0, FloatType()),
                    MapExpression(OrderedDict([(MapKey(1, IntegerType()), IntegerExpression(2))])),
                )
            ]
        )
    )
    assert parse_expression("%{42.0 => %{1 => :x}, :a => {}}") == MapExpression(
        OrderedDict(
            [
                (
                    MapKey(42.0, FloatType()),
                    MapExpression(OrderedDict([(MapKey(1, IntegerType()), AtomLiteralExpression("x"))])),
                ),
                (MapKey("a", AtomLiteralType("a")), TupleExpression([])),
            ]
        )
    )
    assert parse_expression("[]") == ElistExpression()
    assert parse_expression("[1]") == ListExpression(IntegerExpression(1), ElistExpression())
    assert parse_expression("[1, :a]") == (
        ListExpression(
            IntegerExpression(1),
            ListExpression(AtomLiteralExpression("a"), ElistExpression()),
        )
    )
    assert parse_expression("[{1, [2]}, :a, %{:x => 2.0}, []]") == (
        ListExpression(
            TupleExpression(
                [
                    IntegerExpression(1),
                    ListExpression(IntegerExpression(2), ElistExpression()),
                ]
            ),
            ListExpression(
                AtomLiteralExpression("a"),
                ListExpression(
                    MapExpression(OrderedDict([(MapKey("x", AtomLiteralType("x")), FloatExpression(2))])),
                    ListExpression(ElistExpression(), ElistExpression()),
                ),
            ),
        )
    )
    assert parse_expression("[{1, [2]}, :a, %{:x => 2.0}, []]") == (
        ListExpression(
            TupleExpression(
                [
                    IntegerExpression(1),
                    ListExpression(IntegerExpression(2), ElistExpression()),
                ]
            ),
            ListExpression(
                AtomLiteralExpression("a"),
                ListExpression(
                    MapExpression(OrderedDict([(MapKey("x", AtomLiteralType("x")), FloatExpression(2))])),
                    ListExpression(ElistExpression(), ElistExpression()),
                ),
            ),
        )
    )


def test_base_pattern():
    assert parse_pattern("42") == IntegerPattern(42)
    assert parse_pattern("42.0") == FloatPattern(42.0)
    assert parse_pattern("true") == AtomLiteralPattern("true")
    assert parse_pattern(":a") == AtomLiteralPattern("a")
    assert parse_pattern("\":ab\"") == StringPattern(":ab")
    assert parse_pattern("x") == IdentPattern("x")
    assert parse_pattern("^x") == PinIdentPattern("x")
    assert parse_pattern("_") == WildPattern()


def test_parse_data_patterns():
    assert parse_pattern("{}") == TuplePattern([])
    assert parse_pattern("{1}") == TuplePattern([IntegerPattern(1)])
    assert parse_pattern("{1,2}") == TuplePattern([IntegerPattern(1), IntegerPattern(2)])
    assert parse_pattern("{1,2,3}") == TuplePattern([IntegerPattern(1), IntegerPattern(2), IntegerPattern(3)])
    assert parse_pattern("%{}") == MapPattern(OrderedDict([]))
    assert parse_pattern("%{1 => :a}") == MapPattern(OrderedDict([(MapKey(1, IntegerType()), AtomLiteralPattern("a"))]))
    assert parse_pattern("%{1 => :ab}") == MapPattern(OrderedDict([(MapKey(1, IntegerType()), AtomLiteralPattern("ab"))]))
    assert parse_pattern("%{:ab => 42.0}") == MapPattern(OrderedDict([(MapKey("ab", AtomLiteralType("ab")), FloatPattern(42))]))
    assert parse_pattern("%{1 => \":a\"}") == MapPattern(OrderedDict([(MapKey(1, IntegerType()), StringPattern(":a"))]))
    assert parse_pattern("%{\":a\" => 42.0}") == MapPattern(OrderedDict([(MapKey(":a", StringType()), FloatPattern(42))]))
    assert parse_pattern("%{42.1 => true}") == MapPattern(OrderedDict([(MapKey(42.1, FloatType()), AtomLiteralPattern("true"))]))
    assert parse_pattern("%{42.0 => {1,2}}") == MapPattern(
        OrderedDict([(MapKey(42.0, FloatType()), TuplePattern([IntegerPattern(1), IntegerPattern(2)]))])
    )
    assert parse_pattern("%{42.0 => %{1 => 2}}") == MapPattern(
        OrderedDict([(MapKey(42.0, FloatType()), MapPattern(OrderedDict([(MapKey(1, IntegerType()), IntegerPattern(2))])))])
    )
    assert parse_pattern("%{42.0 => %{1 => :x}, :a => {}}") == MapPattern(
        OrderedDict(
            [
                (
                    MapKey(42.0, FloatType()),
                    MapPattern(OrderedDict([(MapKey(1, IntegerType()), AtomLiteralPattern("x"))])),
                ),
                (MapKey("a", AtomLiteralType("a")), TuplePattern([])),
            ]
        )
    )
    assert parse_pattern("[]") == ElistPattern()
    assert parse_pattern("[1]") == ListPattern(IntegerPattern(1), ElistPattern())
    assert parse_pattern("[1, :a]") == (
        ListPattern(IntegerPattern(1), ListPattern(AtomLiteralPattern("a"), ElistPattern()))
    )
    assert parse_expression("[1|[]]") == ListExpression(IntegerExpression(1), ElistExpression())
    assert parse_pattern("[1|[]]") == ListPattern(IntegerPattern(1), ElistPattern())
    assert parse_pattern("[1|_]") == ListPattern(IntegerPattern(1), WildPattern())
    assert parse_pattern("[_|_]") == ListPattern(WildPattern(), WildPattern())
    assert parse_pattern("[{1, [2]}, :a, %{:x => 2.0}, []]") == (
        ListPattern(
            TuplePattern([IntegerPattern(1), ListPattern(IntegerPattern(2), ElistPattern())]),
            ListPattern(
                AtomLiteralPattern("a"),
                ListPattern(
                    MapPattern(OrderedDict([(MapKey("x", AtomLiteralType("x")), FloatPattern(2))])),
                    ListPattern(ElistPattern(), ElistPattern()),
                ),
            ),
        )
    )
    assert parse_pattern("[{1, [2]}, :a, %{:x => 2.0}, []]") == (
        ListPattern(
            TuplePattern([IntegerPattern(1), ListPattern(IntegerPattern(2), ElistPattern())]),
            ListPattern(
                AtomLiteralPattern("a"),
                ListPattern(
                    MapPattern(OrderedDict([(MapKey("x", AtomLiteralType("x")), FloatPattern(2))])),
                    ListPattern(ElistPattern(), ElistPattern()),
                ),
            ),
        )
    )
    assert parse_pattern("[{^x, [2]}, z, %{:x => _}, [1|_]]") == (
        ListPattern(
            TuplePattern([PinIdentPattern("x"), ListPattern(IntegerPattern(2), ElistPattern())]),
            ListPattern(
                IdentPattern("z"),
                ListPattern(
                    MapPattern(OrderedDict([(MapKey("x", AtomLiteralType("x")), WildPattern())])),
                    ListPattern(ListPattern(IntegerPattern(1), WildPattern()), ElistPattern()),
                ),
            ),
        )
    )


def test_operations():
    assert parse_expression("-1") == UnaryOpExpression(UnaryOpEnum.negative, IntegerExpression(1))
    assert parse_expression("not x") == UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x"))
    assert parse_expression("not []") == UnaryOpExpression(UnaryOpEnum.negation, ElistExpression())
    assert parse_expression("1 + 2.0") == BinaryOpExpression(BinaryOpEnum.sum, IntegerExpression(1), FloatExpression(2))
    assert parse_expression("\"a\" <> \":abc\"") == BinaryOpExpression(
        BinaryOpEnum.concatenation, StringExpression("a"), StringExpression(":abc")
    )
    assert parse_expression("3 - 1 == 2.0") == (
        BinaryOpExpression(
            BinaryOpEnum.equality,
            BinaryOpExpression(BinaryOpEnum.subtraction, IntegerExpression(3), IntegerExpression(1)),
            FloatExpression(2),
        )
    )
    assert parse_expression("max(1, 2)") == BinaryOpExpression(
        BinaryOpEnum.maximum, IntegerExpression(1), IntegerExpression(2)
    )
    assert parse_expression("3 - 1 == 2.1") == (
        BinaryOpExpression(
            BinaryOpEnum.equality,
            BinaryOpExpression(BinaryOpEnum.subtraction, IntegerExpression(3), IntegerExpression(1)),
            FloatExpression(2.1),
        )
    )
    assert parse_expression("3 - abs(-1) === 2.0") == (
        BinaryOpExpression(
            BinaryOpEnum.identity,
            BinaryOpExpression(
                BinaryOpEnum.subtraction,
                IntegerExpression(3),
                UnaryOpExpression(
                    UnaryOpEnum.absolute_value,
                    UnaryOpExpression(UnaryOpEnum.negative, IntegerExpression(1)),
                ),
            ),
            FloatExpression(2.0),
        )
    )


def test_control_flow_expressions():
    assert parse_expression("if true do\n" "  {1, 1}\n" "else\n" "  {2, 2}\n" "end\n") == (
        IfElseExpression(
            condition=AtomLiteralExpression("true"),
            if_clause=TupleExpression([IntegerExpression(1), IntegerExpression(1)]),
            else_clause=TupleExpression([IntegerExpression(2), IntegerExpression(2)]),
        )
    )
    assert parse_expression("cond do\n" "  1 == x -> 2\n" "end\n") == (
        CondExpression(
            clauses=[
                (
                    BinaryOpExpression(
                        BinaryOpEnum.equality,
                        IntegerExpression(1),
                        IdentExpression("x"),
                    ),
                    IntegerExpression(2),
                )
            ]
        )
    )
    assert parse_expression("cond do\n" "  1 === x -> 2\n" "  x and y -> 3\n" "end\n") == (
        CondExpression(
            clauses=[
                (
                    BinaryOpExpression(
                        BinaryOpEnum.identity,
                        IntegerExpression(1),
                        IdentExpression("x"),
                    ),
                    IntegerExpression(2),
                ),
                (
                    BinaryOpExpression(
                        BinaryOpEnum.conjunction,
                        IdentExpression("x"),
                        IdentExpression("y"),
                    ),
                    IntegerExpression(3),
                ),
            ]
        )
    )
    assert parse_expression("case {x,y} do\n" "  {^x,\"1\"} -> 2\n" "  _ -> \"a\"\n" "end\n") == (
        CaseExpression(
            test=TupleExpression([IdentExpression("x"), IdentExpression("y")]),
            clauses=[
                (
                    TuplePattern([PinIdentPattern("x"), StringPattern("1")]),
                    IntegerExpression(2),
                ),
                (WildPattern(), StringExpression("a")),
            ],
        )
    )
    assert parse_expression("x; y") == SeqExpression(IdentExpression("x"), IdentExpression("y"))
    assert parse_expression(
        "h = case {x,y} do\n"
        "  {^x,1} -> {u, 2} = x; u\n"
        "  _ -> 3\n"
        "end\n"
        "if h === 1 do\n"
        "  res = true\n"
        "else\n"
        "  res = false\n"
        "end"
    ) == SeqExpression(
        PatternMatchExpression(
            IdentPattern("h"),
            CaseExpression(
                test=TupleExpression([IdentExpression("x"), IdentExpression("y")]),
                clauses=[
                    (
                        TuplePattern([PinIdentPattern("x"), IntegerPattern(1)]),
                        SeqExpression(
                            PatternMatchExpression(
                                TuplePattern([IdentPattern("u"), IntegerPattern(2)]),
                                IdentExpression("x"),
                            ),
                            IdentExpression("u"),
                        ),
                    ),
                    (WildPattern(), IntegerExpression(3)),
                ],
            ),
        ),
        IfElseExpression(
            BinaryOpExpression(BinaryOpEnum.identity, IdentExpression("h"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("res"), AtomLiteralExpression("true")),
            PatternMatchExpression(IdentPattern("res"), AtomLiteralExpression("false")),
        ),
    )


def test_function():
    assert parse_expression("f(2,{})") == FunctionCallExpression("f", [IntegerExpression(2), TupleExpression([])])
    assert parse_expression("f.(2,{})") == AnonCallExpression(IdentExpression("f"), [IntegerExpression(2), TupleExpression([])])
    assert parse_expression("&(foo/0)") == AnonymizedFunctionExpression("foo", 0)
    assert parse_expression("&(foo/1)") == AnonymizedFunctionExpression("foo", 1)
    assert parse_expression("&(foo/2)") == AnonymizedFunctionExpression("foo", 2)


def test_types():
    assert parse_type("float") == FloatType()
    assert parse_type("number") == NumberType()
    assert parse_type("atom") == AtomType()
    assert parse_type(":a") == AtomLiteralType("a")
    assert parse_type(":b") == AtomLiteralType("b")
    assert parse_type("true") == AtomLiteralType("true")
    assert parse_type("integer") == IntegerType()
    assert parse_type("string") == StringType()
    assert parse_type("[]") == ElistType()
    assert parse_type("[:a]") == ListType(AtomLiteralType("a"))
    assert parse_type("{:a}") == TupleType([AtomLiteralType("a")])
    assert parse_type("{}") == TupleType([])
    assert parse_type("{:a, :bc}") == TupleType([AtomLiteralType("a"), AtomLiteralType("bc")])
    assert parse_type("%{}") == MapType({})
    assert parse_type("%{1 => :a}") == MapType({MapKey(1, IntegerType()): AtomLiteralType("a")})
    assert parse_type("%{1 => :a, true => float, 2.0 => atom}") == MapType(
        {MapKey(1, IntegerType()): AtomLiteralType("a"), MapKey("true", AtomLiteralType("true")): FloatType(), MapKey(2.0, FloatType()): AtomType()}
    )
    assert parse_type("(() -> :a)") == FunctionType([], AtomLiteralType("a"))
    assert parse_type("(integer -> :a)") == FunctionType([IntegerType()], AtomLiteralType("a"))
    assert parse_type("(integer, :b -> :a)") == FunctionType([IntegerType(), AtomLiteralType("b")], AtomLiteralType("a"))
    assert parse_type("{(() -> :ac)}") == TupleType([FunctionType([], AtomLiteralType("ac"))])
