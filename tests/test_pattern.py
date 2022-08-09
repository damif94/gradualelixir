from collections import OrderedDict

from gradualelixir.gtypes import (
    AnyType,
    AtomLiteralType,
    AtomType,
    BooleanType,
    ElistType,
    FloatType,
    FunctionType,
    IntegerType,
    ListType,
    MapKey,
    MapType,
    NumberType,
    TupleType,
    TypeEnv,
)
from gradualelixir.pattern import (
    AtomLiteralPattern,
    BasePatternMatchError,
    ElistPattern,
    FloatPattern,
    IdentPattern,
    IntegerPattern,
    ListPattern,
    ListPatternContext,
    MapPattern,
    MapPatternContext,
    NestedPatternMatchError,
    PatternErrorEnum,
    PatternMatchError,
    PatternMatchSuccess,
    PinIdentPattern,
    TuplePattern,
    TuplePatternContext,
    WildPattern,
    pattern_match,
)
from gradualelixir.tests import TEST_ENV
from gradualelixir.utils import long_line

integer = "integer"
float = "float"
number = "number"
any = "any"
x = "x"
y = "y"
z = "z"
px = "^x"
py = "^y"
pz = "^z"


def assert_pattern_match_ok(
    pattern, type, hijacked_pattern_env=None, env=None, expected_type=None, expected_pattern_env=None
):
    if TEST_ENV.get("errors_only"):
        return

    env = env or {}
    hijacked_pattern_env = TypeEnv(hijacked_pattern_env)
    expected_pattern_env = TypeEnv(expected_pattern_env or hijacked_pattern_env.env)

    ret = pattern_match(pattern, type, hijacked_pattern_env, env)
    assert isinstance(ret, PatternMatchSuccess)
    assert ret.refined_type == expected_type
    assert ret.exported_env == expected_pattern_env
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        print(f"\n{long_line}\n\n{ret}")


def assert_pattern_match_error(pattern, type, hijacked_pattern_env=None, env=None, expected_context=None):
    if TEST_ENV.get("success_only"):
        return
    env = TypeEnv(env)
    hijacked_pattern_env = TypeEnv(hijacked_pattern_env)

    ret = pattern_match(pattern, type, hijacked_pattern_env, env)
    assert isinstance(ret, PatternMatchError)
    check_context_path(ret, expected_context)
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        print(f"\n{long_line}\n\n{ret.message(padding='')}")


def check_context_path(error_data: PatternMatchError, context_path):
    if isinstance(error_data, NestedPatternMatchError):
        assert isinstance(context_path, tuple)
        context_instance = context_path[0]
        assert error_data.context == context_instance
        check_context_path(error_data.bullet, context_path[1])
    else:
        assert isinstance(error_data, BasePatternMatchError)
        assert error_data.kind is context_path


def sett(*args):
    args = list(args)
    args.sort()
    aux = OrderedDict()
    for k in args:
        aux[k] = ()
    return aux


def test_tp_lit():
    assert_pattern_match_ok(
        AtomLiteralPattern("true"),
        AtomType(),
        expected_type=AtomLiteralType("true"),
    )
    assert_pattern_match_error(
        AtomLiteralPattern("true"), IntegerType(), expected_context=PatternErrorEnum.incompatible_type_for_literal
    )


def test_tp_pin():
    assert_pattern_match_ok(
        PinIdentPattern("x"),
        IntegerType(),
        env={"x": IntegerType()},
        expected_type=IntegerType(),
    )
    assert_pattern_match_ok(
        PinIdentPattern("x"),
        IntegerType(),
        env={"x": NumberType()},
        expected_type=IntegerType(),
    )

    assert_pattern_match_ok(
        PinIdentPattern("x"),
        MapType({MapKey(1): TupleType([])}),
        env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
    )

    assert_pattern_match_error(
        PinIdentPattern("x"),
        IntegerType(),
        env={"y": IntegerType()},
        expected_context=PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )
    assert_pattern_match_error(
        PinIdentPattern("x"),
        IntegerType(),
        env={"x": FloatType()},
        expected_context=PatternErrorEnum.incompatible_type_for_pinned_variable,
    )

    assert_pattern_match_error(
        PinIdentPattern("x"),
        IntegerType(),
        env={"x": FloatType()},
        expected_context=PatternErrorEnum.incompatible_type_for_pinned_variable,
    )
    assert_pattern_match_error(
        PinIdentPattern("x"),
        IntegerType(),
        env={"y": IntegerType()},
        expected_context=PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )

    assert_pattern_match_error(
        PinIdentPattern("x"),
        IntegerType(),
        hijacked_pattern_env={"x": IntegerType()},
        env={"y": IntegerType()},
        expected_context=PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )

    assert_pattern_match_error(
        PinIdentPattern("x"),
        IntegerType(),
        env={"x": FunctionType([IntegerType()], IntegerType())},
        expected_context=PatternErrorEnum.arrow_types_into_pinned_identifier,
    )


def test_tp_wild():
    assert_pattern_match_ok(WildPattern(), IntegerType(), expected_type=IntegerType())

    assert_pattern_match_ok(
        WildPattern(),
        IntegerType(),
        hijacked_pattern_env={"x": FloatType()},
        env={"y": NumberType()},
        expected_type=IntegerType(),
    )

    assert_pattern_match_ok(
        WildPattern(),
        ListType(FloatType()),
        hijacked_pattern_env={"x": FloatType()},
        env={"y": NumberType()},
        expected_type=ListType(FloatType()),
    )


def test_tp_var():
    assert_pattern_match_ok(
        IdentPattern("x"),
        IntegerType(),
        expected_type=IntegerType(),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        IntegerType(),
        env={"x": FloatType()},
        expected_type=IntegerType(),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        IntegerType(),
        hijacked_pattern_env={"y": FloatType()},
        expected_type=IntegerType(),
        expected_pattern_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        ListType(FloatType()),
        expected_type=ListType(FloatType()),
        expected_pattern_env={"x": ListType(FloatType())},
    )


def test_tp_varn():
    assert_pattern_match_ok(
        IdentPattern("x"),
        IntegerType(),
        hijacked_pattern_env={"x": IntegerType()},
        expected_type=IntegerType(),
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        MapType({MapKey(1): TupleType([])}),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        MapType({MapKey(1): TupleType([])}),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        env={"x": MapType({MapKey(3): TupleType([])})},
        expected_type=MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        MapType({MapKey(1): TupleType([])}),
        hijacked_pattern_env={
            "x": MapType({MapKey(2): TupleType([])}),
            "y": MapType({MapKey(3): TupleType([])}),
        },
        expected_type=MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
            "y": MapType({MapKey(3): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        MapType({MapKey(1): TupleType([])}),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        env={"y": MapType({MapKey(3): TupleType([])})},
        expected_type=MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_error(
        IdentPattern("x"),
        IntegerType(),
        hijacked_pattern_env={"x": FloatType()},
        expected_context=PatternErrorEnum.incompatible_type_for_variable,
    )

    assert_pattern_match_error(
        IdentPattern("x"),
        IntegerType(),
        hijacked_pattern_env={"x": FunctionType([IntegerType()], IntegerType())},
        expected_context=PatternErrorEnum.arrow_types_into_nonlinear_identifier,
    )

    assert_pattern_match_error(
        IdentPattern("x"),
        FunctionType([IntegerType()], IntegerType()),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        expected_context=PatternErrorEnum.arrow_types_into_nonlinear_identifier,
    )


def test_tp_elist():
    assert_pattern_match_ok(ElistPattern(), ElistType(), expected_type=ElistType())

    assert_pattern_match_ok(ElistPattern(), ListType(NumberType()), expected_type=ElistType())

    assert_pattern_match_error(
        ElistPattern(),
        IntegerType(),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )

    assert_pattern_match_error(
        ElistPattern(),
        TupleType([IntegerType()]),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )


def test_tp_list():
    assert_pattern_match_ok(
        ListPattern(IntegerPattern(1), ElistPattern()),
        ListType(IntegerType()),
        expected_type=ListType(IntegerType()),
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        ListType(IntegerType()),
        expected_type=ListType(IntegerType()),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        ListPattern(IntegerPattern(1), ListPattern(FloatPattern(1.0), ElistPattern())),
        ListType(NumberType()),
        expected_type=ListType(NumberType()),
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("x"), ElistPattern())),
        ListType(IntegerType()),
        expected_type=ListType(IntegerType()),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("x"), ElistPattern())),
        ListType(MapType({MapKey(1): TupleType([])})),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        ListType(MapType({MapKey(1): TupleType([])})),
        hijacked_pattern_env={"y": MapType({MapKey(2): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1): TupleType([])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType([])}),
            "y": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        ListType(MapType({MapKey(1): TupleType([])})),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1): TupleType([])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
            "y": MapType({MapKey(1): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        ListPattern(
            IdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1): TupleType([])})),
        hijacked_pattern_env={"y": MapType({MapKey(2): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1): TupleType([])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType([])}),
            "y": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        ListPattern(
            IdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1): TupleType([])})),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1): TupleType([])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
            "y": MapType({MapKey(1): TupleType([])}),
        },
    )

    assert_pattern_match_error(
        ListPattern(IntegerPattern(1), ElistPattern()),
        IntegerType(),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )

    assert_pattern_match_error(
        ListPattern(PinIdentPattern("x"), ElistPattern()),
        ListType(IntegerType()),
        expected_context=(
            ListPatternContext(head=True),
            PatternErrorEnum.pinned_identifier_not_found_in_environment,
        ),
    )

    assert_pattern_match_error(
        ListPattern(IntegerPattern(1), ListPattern(PinIdentPattern("x"), ElistPattern())),
        ListType(IntegerType()),
        expected_context=(
            ListPatternContext(head=False),
            (ListPatternContext(head=True), PatternErrorEnum.pinned_identifier_not_found_in_environment),
        ),
    )


def test_tp_tuple():
    assert_pattern_match_ok(TuplePattern([]), TupleType([]), expected_type=TupleType([]))

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x")]),
        TupleType([IntegerType()]),
        expected_type=TupleType([IntegerType()]),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x")]),
        TupleType([MapType({MapKey(1): TupleType([])})]),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=TupleType([MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})]),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("y")]),
        TupleType([IntegerType(), FloatType()]),
        expected_type=TupleType([IntegerType(), FloatType()]),
        expected_pattern_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x")]),
        TupleType([IntegerType(), IntegerType()]),
        expected_type=TupleType([IntegerType(), IntegerType()]),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1): TupleType([])}),
                MapType({MapKey(2): TupleType([])}),
            ]
        ),
        expected_type=TupleType(
            [
                MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
                MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
            ]
        ),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("y"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1): TupleType([])}),
                MapType({MapKey(2): TupleType([])}),
                MapType({MapKey(3): TupleType([])}),
            ]
        ),
        expected_type=TupleType(
            [
                MapType({MapKey(1): TupleType([]), MapKey(3): TupleType([])}),
                MapType({MapKey(2): TupleType([])}),
                MapType({MapKey(1): TupleType([]), MapKey(3): TupleType([])}),
            ]
        ),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType([]), MapKey(3): TupleType([])}),
            "y": MapType({MapKey(2): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        TuplePattern([PinIdentPattern("x"), IdentPattern("y"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1): TupleType([])}),
                MapType({MapKey(2): TupleType([])}),
                MapType({MapKey(3): TupleType([])}),
            ]
        ),
        env={"x": MapType({MapKey(4): TupleType([])})},
        expected_type=TupleType(
            [
                MapType({MapKey(1): TupleType([]), MapKey(4): TupleType([])}),
                MapType({MapKey(2): TupleType([])}),
                MapType({MapKey(3): TupleType([])}),
            ]
        ),
        expected_pattern_env={
            "x": MapType({MapKey(3): TupleType([])}),
            "y": MapType({MapKey(2): TupleType([])}),
        },
    )

    assert_pattern_match_error(
        TuplePattern([IdentPattern("x")]),
        TupleType([FloatType(), IntegerType()]),
        expected_context=PatternErrorEnum.incompatible_tuples_error,
    )

    assert_pattern_match_error(
        TuplePattern([IntegerPattern(1), IdentPattern("x")]),
        TupleType([FloatType(), IntegerType()]),
        expected_context=(
            TuplePatternContext(n=1),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_error(
        TuplePattern(
            [
                WildPattern(),
                WildPattern(),
                TuplePattern(
                    [
                        TuplePattern([IntegerPattern(1), IdentPattern("x")]),
                        IdentPattern("x"),
                    ]
                ),
            ]
        ),
        TupleType(
            [
                FloatType(),
                FloatType(),
                TupleType([TupleType([FloatType(), IntegerType()]), FloatType()]),
            ]
        ),
        expected_context=(
            TuplePatternContext(n=3),
            (
                TuplePatternContext(n=1),
                (TuplePatternContext(n=1), PatternErrorEnum.incompatible_type_for_literal),
            ),
        ),
    )

    assert_pattern_match_error(
        TuplePattern([IdentPattern("x")]),
        ListType(FloatType()),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )


def test_tp_map():
    assert_pattern_match_ok(
        MapPattern(OrderedDict()),
        MapType({}),
        expected_type=MapType({}),
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x"))])),
        MapType({MapKey(1): IntegerType()}),
        expected_type=MapType({MapKey(1): IntegerType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict()),
        MapType({MapKey(1): IntegerType()}),
        expected_type=MapType({MapKey(1): IntegerType()}),
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x")), (MapKey(2), FloatPattern(2.0))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(2), FloatPattern(2.0)), (MapKey(1), IdentPattern("x"))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(2), FloatPattern(2.0)), (MapKey(1), IdentPattern("x"))])),
        MapType({MapKey(2): FloatType(), MapKey(1): IntegerType()}),
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x")), (MapKey(2), FloatPattern(2.0))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_type=MapType({MapKey(2): FloatType(), MapKey(1): IntegerType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x"))])),
        MapType({MapKey(1): MapType({MapKey(1): TupleType([])})}),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=MapType({MapKey(1): MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})}),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x")), (MapKey(2), IdentPattern("y"))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_pattern_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x")), (MapKey(2), IdentPattern("x"))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(2), IntegerPattern(3))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x")), (MapKey(2), IdentPattern("x"))])),
        MapType(
            {
                MapKey(1): MapType({MapKey(1): TupleType([])}),
                MapKey(2): MapType({MapKey(2): TupleType([])}),
            }
        ),
        expected_type=MapType(
            {
                MapKey(1): MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
                MapKey(2): MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
            }
        ),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_ok(
        MapPattern(
            OrderedDict(
                [
                    (MapKey(1), IdentPattern("x")),
                    (MapKey(2), IdentPattern("y")),
                    (MapKey(3), IdentPattern("x")),
                ]
            )
        ),
        MapType(
            {
                MapKey(1): MapType({MapKey(1): TupleType([])}),
                MapKey(2): MapType({MapKey(2): TupleType([])}),
                MapKey(3): MapType({MapKey(3): TupleType([])}),
            }
        ),
        expected_type=MapType(
            {
                MapKey(1): MapType({MapKey(1): TupleType([]), MapKey(3): TupleType([])}),
                MapKey(2): MapType({MapKey(2): TupleType([])}),
                MapKey(3): MapType({MapKey(1): TupleType([]), MapKey(3): TupleType([])}),
            }
        ),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType([]), MapKey(3): TupleType([])}),
            "y": MapType({MapKey(2): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        MapPattern(
            OrderedDict(
                [
                    (MapKey(1), PinIdentPattern("x")),
                    (MapKey(2), IdentPattern("y")),
                    (MapKey(3), IdentPattern("x")),
                ]
            )
        ),
        MapType(
            {
                MapKey(1): MapType({MapKey(1): TupleType([])}),
                MapKey(2): MapType({MapKey(2): TupleType([])}),
                MapKey(3): MapType({MapKey(3): TupleType([])}),
            }
        ),
        env={"x": MapType({MapKey(4): TupleType([])})},
        expected_type=MapType(
            {
                MapKey(1): MapType({MapKey(1): TupleType([]), MapKey(4): TupleType([])}),
                MapKey(2): MapType({MapKey(2): TupleType([])}),
                MapKey(3): MapType({MapKey(3): TupleType([])}),
            }
        ),
        expected_pattern_env={
            "x": MapType({MapKey(3): TupleType([])}),
            "y": MapType({MapKey(2): TupleType([])}),
        },
    )
    assert_pattern_match_error(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x"))])),
        MapType({MapKey(2): FloatType(), MapKey(3): IntegerType()}),
        expected_context=PatternErrorEnum.incompatible_maps_error,
    )

    assert_pattern_match_error(
        MapPattern(OrderedDict([(MapKey(1), IntegerPattern(1)), (MapKey(2), IdentPattern("x"))])),
        MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
        expected_context=(
            MapPatternContext(key=MapKey(1)),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_error(
        MapPattern(OrderedDict([(MapKey(2), IdentPattern("x")), (MapKey(1), IntegerPattern(1))])),
        MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
        expected_context=(
            MapPatternContext(key=MapKey(1)),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_error(
        MapPattern(OrderedDict([(MapKey(1), IntegerPattern(1)), (MapKey(2), IdentPattern("x"))])),
        MapType({MapKey(2): IntegerType(), MapKey(1): FloatType()}),
        expected_context=(
            MapPatternContext(key=MapKey(1)),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_error(
        MapPattern(OrderedDict([(MapKey(2), IdentPattern("x")), (MapKey(1), IntegerPattern(1))])),
        MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
        expected_context=(
            MapPatternContext(key=MapKey(1)),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_error(
        MapPattern(
            OrderedDict(
                [
                    (MapKey(1), WildPattern()),
                    (MapKey(2), WildPattern()),
                    (
                        MapKey(3),
                        MapPattern(
                            OrderedDict(
                                [
                                    (
                                        MapKey(1),
                                        MapPattern(
                                            OrderedDict(
                                                [
                                                    (MapKey(1), IntegerPattern(1)),
                                                    (MapKey(2), IdentPattern("x")),
                                                ]
                                            )
                                        ),
                                    ),
                                    (MapKey(2), IdentPattern("x")),
                                ]
                            )
                        ),
                    ),
                ]
            )
        ),
        MapType(
            {
                MapKey(1): FloatType(),
                MapKey(2): FloatType(),
                MapKey(3): MapType(
                    {
                        MapKey(1): MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
                        MapKey(2): FloatType(),
                    }
                ),
            }
        ),
        expected_context=(
            MapPatternContext(key=MapKey(3)),
            (
                MapPatternContext(key=MapKey(1)),
                (
                    MapPatternContext(key=MapKey(1)),
                    PatternErrorEnum.incompatible_type_for_literal,
                ),
            ),
        ),
    )

    assert_pattern_match_error(
        MapPattern(
            OrderedDict(
                [
                    (MapKey(2), WildPattern()),
                    (MapKey(3), WildPattern()),
                    (
                        MapKey(1),
                        MapPattern(
                            OrderedDict(
                                [
                                    (
                                        MapKey(1),
                                        MapPattern(
                                            OrderedDict(
                                                [
                                                    (MapKey(2), IntegerPattern(1)),
                                                    (MapKey(1), IdentPattern("x")),
                                                ]
                                            )
                                        ),
                                    ),
                                    (MapKey(2), IdentPattern("x")),
                                ]
                            )
                        ),
                    ),
                ]
            )
        ),
        MapType(
            {
                MapKey(2): FloatType(),
                MapKey(3): FloatType(),
                MapKey(1): MapType(
                    {
                        MapKey(1): MapType({MapKey(2): FloatType(), MapKey(1): IntegerType()}),
                        MapKey(2): FloatType(),
                    }
                ),
            }
        ),
        expected_context=(
            MapPatternContext(key=MapKey(1)),
            (
                MapPatternContext(key=MapKey(1)),
                (
                    MapPatternContext(key=MapKey(2)),
                    PatternErrorEnum.incompatible_type_for_literal,
                ),
            ),
        ),
    )

    assert_pattern_match_error(
        MapPattern(OrderedDict([(MapKey(2), IdentPattern("x"))])),
        ListType(FloatType()),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )


def test_tp_any():
    assert_pattern_match_ok(IntegerPattern(1), AnyType(), expected_type=IntegerType())

    assert_pattern_match_ok(
        IdentPattern("x"),
        AnyType(),
        hijacked_pattern_env={"x": IntegerType()},
        expected_type=IntegerType(),
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        IntegerType(),
        hijacked_pattern_env={"x": IntegerType()},
        expected_type=IntegerType(),
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        expected_type=AnyType(),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_ok(
        IdentPattern("x"),
        NumberType(),
        hijacked_pattern_env={"x": AnyType()},
        expected_type=AnyType(),
    )

    assert_pattern_match_ok(
        PinIdentPattern("x"),
        AnyType(),
        env={"x": NumberType()},
        expected_type=AnyType(),
    )

    assert_pattern_match_ok(
        PinIdentPattern("x"),
        NumberType(),
        env={"x": AnyType()},
        expected_type=AnyType(),
    )

    assert_pattern_match_ok(ElistPattern(), AnyType(), expected_type=ElistType())

    assert_pattern_match_ok(
        ListPattern(WildPattern(), ElistPattern()),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_pattern_match_ok(
        ListPattern(IntegerPattern(1), WildPattern()),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_pattern_match_ok(
        ListPattern(IntegerPattern(1), ListPattern(IntegerPattern(2), ElistPattern())),
        AnyType(),
        expected_type=ListType(IntegerType()),
    )

    assert_pattern_match_ok(
        ListPattern(WildPattern(), ListPattern(IntegerPattern(2), ElistPattern())),
        ListType(IntegerType()),
        expected_type=ListType(IntegerType()),
    )

    assert_pattern_match_ok(
        ListPattern(WildPattern(), ListPattern(IntegerPattern(2), ElistPattern())),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_pattern_match_ok(
        ListPattern(WildPattern(), WildPattern()),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_pattern_match_ok(
        ListPattern(WildPattern(), ListPattern(WildPattern(), ElistPattern())),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        hijacked_pattern_env={"x": NumberType(), "y": NumberType()},
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_ok(TuplePattern([]), AnyType(), expected_type=TupleType([]))

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x")]),
        AnyType(),
        expected_type=TupleType([AnyType()]),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("y")]),
        AnyType(),
        expected_type=TupleType([AnyType(), AnyType()]),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x")]),
        AnyType(),
        expected_type=TupleType([AnyType(), AnyType()]),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_ok(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern("x")), (MapKey(2), IdentPattern("y"))])),
        AnyType(),
        expected_type=MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_error(
        ListPattern(IntegerPattern(1), ListPattern(AtomLiteralPattern("true"), ElistPattern())),
        AnyType(),
        expected_context=PatternErrorEnum.incompatible_type_for_pattern,
    )

    assert_pattern_match_error(
        ListPattern(
            TuplePattern([IntegerPattern(1), IntegerPattern(2)]),
            ListPattern(
                TuplePattern([AtomLiteralPattern("true"), IntegerPattern(2)]),
                ElistPattern(),
            ),
        ),
        AnyType(),
        expected_context=PatternErrorEnum.incompatible_type_for_pattern,
    )

    assert_pattern_match_error(
        ListPattern(
            MapPattern(OrderedDict([(MapKey(1), TuplePattern([IntegerPattern(1), IntegerPattern(2)]))])),
            ListPattern(
                MapPattern(
                    OrderedDict(
                        [
                            (
                                MapKey(1),
                                TuplePattern(
                                    [
                                        AtomLiteralPattern("true"),
                                        IntegerPattern(
                                            2,
                                        ),
                                    ]
                                ),
                            )
                        ]
                    )
                ),
                ElistPattern(),
            ),
        ),
        AnyType(),
        expected_context=PatternErrorEnum.incompatible_type_for_pattern,
    )

    assert_pattern_match_ok(
        ListPattern(
            MapPattern(OrderedDict([(MapKey(1), TuplePattern([IntegerPattern(1), IntegerPattern(2)]))])),
            ListPattern(
                MapPattern(
                    OrderedDict(
                        [
                            (
                                MapKey(2),
                                TuplePattern(
                                    [
                                        AtomLiteralPattern("true"),
                                        IntegerPattern(
                                            2,
                                        ),
                                    ]
                                ),
                            )
                        ]
                    )
                ),
                ElistPattern(),
            ),
        ),
        AnyType(),
        expected_type=ListType(MapType({})),
    )


def test_tp_ok_progressions():
    assert_pattern_match_ok(
        ListPattern(
            PinIdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1): TupleType([])})),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([])})},
        env={"x": MapType({MapKey(3): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1): TupleType([])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
            "y": MapType({MapKey(1): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        ListPattern(
            PinIdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1): TupleType([])})),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType([]), MapKey(3): TupleType([])})},
        env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1): TupleType([])})),
        expected_pattern_env={
            "x": MapType(
                {
                    MapKey(1): TupleType([]),
                    MapKey(2): TupleType([]),
                    MapKey(3): TupleType([]),
                }
            ),
            "y": MapType({MapKey(1): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        ListPattern(
            PinIdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1): TupleType([])})),
        hijacked_pattern_env={
            "x": MapType({MapKey(2): TupleType([]), MapKey(3): TupleType([])}),
            "y": MapType({MapKey(2): TupleType([])}),
        },
        env={"x": MapType({MapKey(2): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})),
        expected_pattern_env={
            "x": MapType(
                {
                    MapKey(1): TupleType([]),
                    MapKey(2): TupleType([]),
                    MapKey(3): TupleType([]),
                }
            ),
            "y": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
        },
    )

    assert_pattern_match_ok(
        ListPattern(
            ListPattern(IntegerPattern(1), ElistPattern()),
            ListPattern(ListPattern(FloatPattern(1.0), ElistPattern()), ElistPattern()),
        ),
        ListType(ListType(NumberType())),
        expected_type=ListType(ListType(NumberType())),
    )

    assert_pattern_match_ok(
        ListPattern(
            ListPattern(ListPattern(IntegerPattern(1), ElistPattern()), ElistPattern()),
            ListPattern(
                ListPattern(ListPattern(FloatPattern(1.0), ElistPattern()), ElistPattern()),
                ElistPattern(),
            ),
        ),
        ListType(ListType(ListType(NumberType()))),
        expected_type=ListType(ListType(ListType(NumberType()))),
    )

    assert_pattern_match_ok(
        ListPattern(
            ListPattern(ListPattern(IntegerPattern(1), ElistPattern()), ElistPattern()),
            ListPattern(
                ListPattern(ListPattern(FloatPattern(1.0), ElistPattern()), ElistPattern()),
                ListPattern(
                    ListPattern(
                        ListPattern(
                            IntegerPattern(1),
                            ListPattern(FloatPattern(1.0), ElistPattern()),
                        ),
                        ElistPattern(),
                    ),
                    ElistPattern(),
                ),
            ),
        ),
        ListType(ListType(ListType(NumberType()))),
        expected_type=ListType(ListType(ListType(NumberType()))),
    )

    assert_pattern_match_ok(
        ListPattern(
            TuplePattern([IntegerPattern(1), IntegerPattern(2)]),
            ListPattern(TuplePattern([IntegerPattern(1), FloatPattern(2.0)]), ElistPattern()),
        ),
        ListType(TupleType([IntegerType(), NumberType()])),
        expected_type=ListType(TupleType([IntegerType(), NumberType()])),
    )

    assert_pattern_match_ok(
        ListPattern(
            TuplePattern([IntegerPattern(1), IntegerPattern(2)]),
            ListPattern(TuplePattern([IntegerPattern(1), FloatPattern(2.0)]), ElistPattern()),
        ),
        ListType(TupleType([NumberType(), NumberType()])),
        expected_type=ListType(TupleType([IntegerType(), NumberType()])),
    )

    assert_pattern_match_ok(
        ListPattern(
            TuplePattern([IntegerPattern(1), IntegerPattern(2)]),
            ListPattern(
                TuplePattern([IntegerPattern(1), FloatPattern(2.0)]),
                ListPattern(TuplePattern([FloatPattern(3.0), IntegerPattern(1)]), ElistPattern()),
            ),
        ),
        ListType(TupleType([NumberType(), NumberType()])),
        expected_type=ListType(TupleType([NumberType(), NumberType()])),
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x")]),
        TupleType([MapType({MapKey(1): TupleType([])})]),
        expected_type=TupleType([MapType({MapKey(1): TupleType([])})]),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([])})},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1): TupleType([])}),
                MapType({MapKey(2): TupleType([])}),
            ]
        ),
        expected_type=TupleType(
            [
                MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
                MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])}),
            ]
        ),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([])})},
    )

    assert_pattern_match_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1): TupleType([])}),
                MapType({MapKey(2): TupleType([])}),
                MapType({MapKey(3): TupleType([])}),
            ]
        ),
        expected_type=TupleType(
            [
                MapType(
                    {
                        MapKey(1): TupleType([]),
                        MapKey(2): TupleType([]),
                        MapKey(3): TupleType([]),
                    }
                ),
                MapType(
                    {
                        MapKey(1): TupleType([]),
                        MapKey(2): TupleType([]),
                        MapKey(3): TupleType([]),
                    }
                ),
                MapType(
                    {
                        MapKey(1): TupleType([]),
                        MapKey(2): TupleType([]),
                        MapKey(3): TupleType([]),
                    }
                ),
            ]
        ),
        expected_pattern_env={
            "x": MapType(
                {
                    MapKey(1): TupleType([]),
                    MapKey(2): TupleType([]),
                    MapKey(3): TupleType([]),
                }
            )
        },
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        hijacked_pattern_env={"x": AtomLiteralType("true")},
        expected_type=ListType(AtomLiteralType("true")),
        expected_pattern_env={"x": AtomLiteralType("true")},
    )
    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        hijacked_pattern_env={"x": BooleanType()},
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AnyType()},
    )
    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        hijacked_pattern_env={"x": AtomType()},
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        hijacked_pattern_env={"x": AtomLiteralType("true")},
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AtomLiteralType("true"), "y": AnyType()},
    )
    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        hijacked_pattern_env={"x": BooleanType()},
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )
    assert_pattern_match_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        hijacked_pattern_env={"x": AtomType()},
        expected_type=ListType(AnyType()),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_ok(
        TuplePattern(
            [
                ListPattern(IdentPattern("x"), ElistPattern()),
                TuplePattern([IdentPattern("x"), IdentPattern("x")]),
            ]
        ),
        AnyType(),
        hijacked_pattern_env={"x": BooleanType()},
        expected_type=TupleType([ListType(AnyType()), TupleType([AnyType(), AnyType()])]),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_ok(
        MapPattern(
            OrderedDict(
                [
                    (
                        MapKey(1),
                        TuplePattern(
                            [
                                ListPattern(IdentPattern("x"), ElistPattern()),
                                TuplePattern([IdentPattern("x"), IdentPattern("x")]),
                            ]
                        ),
                    ),
                    (MapKey(2), IdentPattern("x")),
                ]
            )
        ),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        expected_type=MapType(
            {
                MapKey(1): TupleType([ListType(AnyType()), TupleType([AnyType(), AnyType()])]),
                MapKey(2): AnyType(),
            }
        ),
        expected_pattern_env={"x": AnyType()},
    )


def test_tp_errors():
    assert_pattern_match_error(
        ListPattern(
            TuplePattern(
                [
                    ListPattern(
                        MapPattern(OrderedDict([(MapKey(2), TuplePattern([]))])),
                        ListPattern(
                            MapPattern(OrderedDict([(MapKey(2), TuplePattern([]))])),
                            ListPattern(
                                MapPattern(OrderedDict([(MapKey(2), ElistPattern())])),
                                ElistPattern(),
                            ),
                        ),
                    )
                ]
            ),
            ElistPattern(),
        ),
        ListType(TupleType([ListType(MapType({MapKey(2): TupleType([])}))])),
        expected_context=(
            ListPatternContext(head=True),
            (
                TuplePatternContext(n=1),
                (
                    ListPatternContext(head=False),
                    (
                        ListPatternContext(head=False),
                        (
                            ListPatternContext(head=True),
                            (
                                MapPatternContext(key=MapKey(2)),
                                PatternErrorEnum.incompatible_constructors_error,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
