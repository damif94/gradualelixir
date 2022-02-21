import json
import subprocess
from collections import OrderedDict

from gradualelixir import jsonparser, types, PROJECT_PATH
from gradualelixir.expression import *
from gradualelixir.pattern import *


def parse_expression(code):
    if isinstance(code, tuple):
        code = '\n'.join(list(code))
    if isinstance(code, list):
        code = '\n'.join(code)

    ret = subprocess.run([f"{PROJECT_PATH}/elixir_port/elixir_port", code], capture_output=True)
    res = jsonparser.parse_expression(json.loads(ret.stdout))
    print(res)
    print(res.__repr__())
    return res


def parse_pattern(code: str):
    code = code + " = {}"
    res = parse_expression(code)
    assert isinstance(res, PatternMatchExpression)
    return res.pattern


def test_parse_literal_expression():
    assert parse_expression("42") == IntegerExpression(42)
    assert parse_expression("42.0") == FloatExpression(42.0)
    assert parse_expression("true") == AtomLiteralExpression("true")
    assert parse_expression(":a") == AtomLiteralExpression("a")


def test_parse_data_expressions():
    assert parse_expression("{}") == TupleExpression([])
    assert parse_expression("{1}") == TupleExpression([IntegerExpression(1)])
    assert parse_expression("{1,2}") == TupleExpression(
        [IntegerExpression(1), IntegerExpression(2)]
    )
    assert parse_expression("{1,2,3}") == TupleExpression(
        [IntegerExpression(1), IntegerExpression(2), IntegerExpression(3)]
    )
    assert parse_expression("%{}") == MapExpression(OrderedDict([]))
    assert parse_expression("%{1 => :a}") == MapExpression(OrderedDict([(1, AtomLiteralExpression("a"))]))
    assert parse_expression("%{:a => 42.0}") == MapExpression(OrderedDict([("a", FloatExpression(42))]))
    assert parse_expression("%{42.1 => true}") == MapExpression(OrderedDict([(42.1, AtomLiteralExpression("true"))]))
    # this one should be error...
    assert parse_expression("%{42.0 => {1,2}}") == MapExpression(
        OrderedDict([(42, TupleExpression([IntegerExpression(1), IntegerExpression(2)]))])
    )
    assert parse_expression("%{42.0 => {1,2}}") == MapExpression(
        OrderedDict([(42, TupleExpression([IntegerExpression(1), IntegerExpression(2)]))])
    )
    assert parse_expression("%{42.0 => %{1 => 2}}") == MapExpression(
        OrderedDict([
            (42, MapExpression(OrderedDict([(1, IntegerExpression(2))])))
        ])
    )
    assert parse_expression("%{42.0 => %{1 => :x}, :a => {}}") == MapExpression(
        OrderedDict([
            (42, MapExpression(OrderedDict([(1, AtomLiteralExpression("x"))]))),
            ("a", TupleExpression([]))
        ])
    )
    assert parse_expression("[]") == ElistExpression()
    assert parse_expression("[1]") == ListExpression(IntegerExpression(1), ElistExpression())
    assert parse_expression("[1, :a]") == (
        ListExpression(
            IntegerExpression(1),
            ListExpression(AtomLiteralExpression("a"), ElistExpression())
        )
    )
    assert parse_expression("[{1, [2]}, :a, %{:x => 2.0}, []]") == (
        ListExpression(
            TupleExpression([IntegerExpression(1), ListExpression(IntegerExpression(2), ElistExpression())]),
            ListExpression(
                AtomLiteralExpression("a"),
                ListExpression(
                    MapExpression(OrderedDict([("x", FloatExpression(2))])),
                    ListExpression(
                        ElistExpression(),
                        ElistExpression()
                    )
                )
            )
        )
    )
    assert parse_expression("[{1, [2]}, :a, %{:x => 2.0}, []]") == (
        ListExpression(
            TupleExpression([IntegerExpression(1), ListExpression(IntegerExpression(2), ElistExpression())]),
            ListExpression(
                AtomLiteralExpression("a"),
                ListExpression(
                    MapExpression(OrderedDict([("x", FloatExpression(2))])),
                    ListExpression(
                        ElistExpression(),
                        ElistExpression()
                    )
                )
            )
        )
    )


def test_base_pattern():
    assert parse_pattern("42") == IntegerPattern(42)
    assert parse_pattern("42.0") == FloatPattern(42.0)
    assert parse_pattern("true") == AtomLiteralPattern("true")
    assert parse_pattern(":a") == AtomLiteralPattern("a")
    assert parse_pattern("x") == IdentPattern("x")
    assert parse_pattern("^x") == PinIdentPattern("x")
    assert parse_pattern("_") == WildPattern()


def test_parse_data_patterns():
    assert parse_pattern("{}") == TuplePattern([])
    assert parse_pattern("{1}") == TuplePattern([IntegerPattern(1)])
    assert parse_pattern("{1,2}") == TuplePattern(
        [IntegerPattern(1), IntegerPattern(2)]
    )
    assert parse_pattern("{1,2,3}") == TuplePattern(
        [IntegerPattern(1), IntegerPattern(2), IntegerPattern(3)]
    )
    assert parse_pattern("%{}") == MapPattern(OrderedDict([]))
    assert parse_pattern("%{1 => :a}") == MapPattern(OrderedDict([(1, AtomLiteralPattern("a"))]))
    assert parse_pattern("%{:a => 42.0}") == MapPattern(OrderedDict([("a", FloatPattern(42))]))
    assert parse_pattern("%{42.1 => true}") == MapPattern(OrderedDict([(42.1, AtomLiteralPattern("true"))]))
    # this one should be error...
    assert parse_pattern("%{42.0 => {1,2}}") == MapPattern(
        OrderedDict([(42, TuplePattern([IntegerPattern(1), IntegerPattern(2)]))])
    )
    assert parse_pattern("%{42.0 => {1,2}}") == MapPattern(
        OrderedDict([(42, TuplePattern([IntegerPattern(1), IntegerPattern(2)]))])
    )
    assert parse_pattern("%{42.0 => %{1 => 2}}") == MapPattern(
        OrderedDict([
            (42, MapPattern(OrderedDict([(1, IntegerPattern(2))])))
        ])
    )
    assert parse_pattern("%{42.0 => %{1 => :x}, :a => {}}") == MapPattern(
        OrderedDict([
            (42, MapPattern(OrderedDict([(1, AtomLiteralPattern("x"))]))),
            ("a", TuplePattern([]))
        ])
    )
    assert parse_pattern("[]") == ElistPattern()
    assert parse_pattern("[1]") == ListPattern(IntegerPattern(1), ElistPattern())
    assert parse_pattern("[1, :a]") == (
        ListPattern(
            IntegerPattern(1),
            ListPattern(AtomLiteralPattern("a"), ElistPattern())
        )
    )
    assert parse_pattern("[{1, [2]}, :a, %{:x => 2.0}, []]") == (
        ListPattern(
            TuplePattern([IntegerPattern(1), ListPattern(IntegerPattern(2), ElistPattern())]),
            ListPattern(
                AtomLiteralPattern("a"),
                ListPattern(
                    MapPattern(OrderedDict([("x", FloatPattern(2))])),
                    ListPattern(
                        ElistPattern(),
                        ElistPattern()
                    )
                )
            )
        )
    )
    assert parse_pattern("[{1, [2]}, :a, %{:x => 2.0}, []]") == (
        ListPattern(
            TuplePattern([IntegerPattern(1), ListPattern(IntegerPattern(2), ElistPattern())]),
            ListPattern(
                AtomLiteralPattern("a"),
                ListPattern(
                    MapPattern(OrderedDict([("x", FloatPattern(2))])),
                    ListPattern(
                        ElistPattern(),
                        ElistPattern()
                    )
                )
            )
        )
    )


def test_working():
    assert parse_expression("[1|[]]") == ListExpression(IntegerExpression(1), ElistExpression())
    # assert parse_pattern("[1|_]") == ListPattern(IntegerPattern(1), WildPattern())
    # assert parse_pattern("[{^x, [2]}, z, %{:x => _}, [1|_]]") == (
    #     ListPattern(
    #         TuplePattern([PinIdentPattern("x"), ListPattern(IntegerPattern(2), ElistPattern())]),
    #         ListPattern(
    #             IdentPattern("z"),
    #             ListPattern(
    #                 MapPattern(OrderedDict([("x", WildPattern())])),
    #                 ListPattern(
    #                     ElistPattern(),
    #                     WildPattern()
    #                 )
    #             )
    #         )
    #     )
    # )
    #
