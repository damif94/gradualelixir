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
    type_check,
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


def assert_type_check_pattern_ok(
    pattern, type, env=None, external_env=None, expected_type=None, expected_env=None
):
    if TEST_ENV.get("errors_only"):
        return

    external_env = external_env or {}
    env = TypeEnv(env)
    expected_env = TypeEnv(expected_env or env.env)

    ret = type_check(pattern, type, env, external_env)
    assert isinstance(ret, PatternMatchSuccess)
    assert ret.refined_type == expected_type
    assert ret.exported_env == expected_env
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        print(f"\n{long_line}\n\n{ret}")


def assert_type_check_pattern_error(pattern, type, env=None, external_env=None, expected_context=None):
    if TEST_ENV.get("success_only"):
        return
    external_env = TypeEnv(external_env)
    env = TypeEnv(env)

    ret = type_check(pattern, type, env, external_env)
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


def test_type_check_lit():
    assert_type_check_pattern_ok(
        AtomLiteralPattern("true"),
        AtomType(),
        expected_type=AtomLiteralType("true"),
    )
    assert_type_check_pattern_error(
        AtomLiteralPattern("true"), IntegerType(), expected_context=PatternErrorEnum.incompatible_type_for_literal
    )


def test_type_check_pin():
    assert_type_check_pattern_ok(
        PinIdentPattern("x"),
        IntegerType(),
        external_env={"x": IntegerType()},
        expected_type=IntegerType(),
    )
    assert_type_check_pattern_ok(
        PinIdentPattern("x"),
        IntegerType(),
        external_env={"x": NumberType()},
        expected_type=IntegerType(),
    )

    assert_type_check_pattern_ok(
        PinIdentPattern("x"),
        MapType({MapKey(1, IntegerType()): TupleType([])}),
        external_env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
    )

    assert_type_check_pattern_ok(
        PinIdentPattern("x"),
        FunctionType([FloatType()], NumberType()),
        external_env={"x": FunctionType([NumberType()], IntegerType())},
        expected_type=FunctionType([NumberType()], IntegerType())
    )

    assert_type_check_pattern_error(
        PinIdentPattern("x"),
        IntegerType(),
        external_env={"y": IntegerType()},
        expected_context=PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )
    assert_type_check_pattern_error(
        PinIdentPattern("x"),
        IntegerType(),
        external_env={"x": FloatType()},
        expected_context=PatternErrorEnum.incompatible_type_for_pinned_variable,
    )

    assert_type_check_pattern_error(
        PinIdentPattern("x"),
        IntegerType(),
        external_env={"x": FloatType()},
        expected_context=PatternErrorEnum.incompatible_type_for_pinned_variable,
    )
    assert_type_check_pattern_error(
        PinIdentPattern("x"),
        IntegerType(),
        external_env={"y": IntegerType()},
        expected_context=PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )

    assert_type_check_pattern_error(
        PinIdentPattern("x"),
        IntegerType(),
        env={"x": IntegerType()},
        external_env={"y": IntegerType()},
        expected_context=PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )

    assert_type_check_pattern_error(
        PinIdentPattern("x"),
        IntegerType(),
        external_env={"x": FunctionType([IntegerType()], IntegerType())},
        expected_context=PatternErrorEnum.incompatible_type_for_pinned_variable,
    )


def test_type_check_wild():
    assert_type_check_pattern_ok(WildPattern(), IntegerType(), expected_type=IntegerType())

    assert_type_check_pattern_ok(
        WildPattern(),
        IntegerType(),
        env={"x": FloatType()},
        external_env={"y": NumberType()},
        expected_type=IntegerType(),
    )

    assert_type_check_pattern_ok(
        WildPattern(),
        ListType(FloatType()),
        env={"x": FloatType()},
        external_env={"y": NumberType()},
        expected_type=ListType(FloatType()),
    )


def test_type_check_var():
    assert_type_check_pattern_ok(
        IdentPattern("x"),
        IntegerType(),
        expected_type=IntegerType(),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        IntegerType(),
        external_env={"x": FloatType()},
        expected_type=IntegerType(),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        IntegerType(),
        env={"y": FloatType()},
        expected_type=IntegerType(),
        expected_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        ListType(FloatType()),
        expected_type=ListType(FloatType()),
        expected_env={"x": ListType(FloatType())},
    )


def test_type_check_varn():
    assert_type_check_pattern_ok(
        IdentPattern("x"),
        IntegerType(),
        env={"x": IntegerType()},
        expected_type=IntegerType(),
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        MapType({MapKey(1, IntegerType()): TupleType([])}),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        MapType({MapKey(1, IntegerType()): TupleType([])}),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        external_env={"x": MapType({MapKey(3, IntegerType()): TupleType([])})},
        expected_type=MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        MapType({MapKey(1, IntegerType()): TupleType([])}),
        env={
            "x": MapType({MapKey(2, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(3, IntegerType()): TupleType([])}),
        },
        expected_type=MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(3, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        MapType({MapKey(1, IntegerType()): TupleType([])}),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        external_env={"y": MapType({MapKey(3, IntegerType()): TupleType([])})},
        expected_type=MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        FunctionType([IntegerType()], FloatType()),
        env={"x": FunctionType([NumberType()], NumberType())},
        expected_type=FunctionType([NumberType()], FloatType()),
        expected_env={"x": FunctionType([NumberType()], FloatType())},
    )

    assert_type_check_pattern_error(
        IdentPattern("x"),
        IntegerType(),
        env={"x": FloatType()},
        expected_context=PatternErrorEnum.incompatible_type_for_variable,
    )

    assert_type_check_pattern_error(
        IdentPattern("x"),
        IntegerType(),
        env={"x": FunctionType([IntegerType()], IntegerType())},
        expected_context=PatternErrorEnum.incompatible_type_for_variable,
    )

    assert_type_check_pattern_error(
        IdentPattern("x"),
        FunctionType([IntegerType()], IntegerType()),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_context=PatternErrorEnum.incompatible_type_for_variable,
    )


def test_type_check_elist():
    assert_type_check_pattern_ok(ElistPattern(), ElistType(), expected_type=ElistType())

    assert_type_check_pattern_ok(ElistPattern(), ListType(NumberType()), expected_type=ElistType())

    assert_type_check_pattern_error(
        ElistPattern(),
        IntegerType(),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )

    assert_type_check_pattern_error(
        ElistPattern(),
        TupleType([IntegerType()]),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )


def test_type_check_list():
    assert_type_check_pattern_ok(
        ListPattern(IntegerPattern(1), ElistPattern()),
        ListType(IntegerType()),
        expected_type=ListType(IntegerType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        ListType(IntegerType()),
        expected_type=ListType(IntegerType()),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        ListPattern(IntegerPattern(1), ListPattern(FloatPattern(1.0), ElistPattern())),
        ListType(NumberType()),
        expected_type=ListType(NumberType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("x"), ElistPattern())),
        ListType(IntegerType()),
        expected_type=ListType(IntegerType()),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("x"), ElistPattern())),
        ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        env={"y": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(1, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        ListPattern(
            IdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        env={"y": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        ListPattern(
            IdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(1, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_error(
        ListPattern(IntegerPattern(1), ElistPattern()),
        IntegerType(),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )

    assert_type_check_pattern_error(
        ListPattern(PinIdentPattern("x"), ElistPattern()),
        ListType(IntegerType()),
        expected_context=(
            ListPatternContext(head=True),
            PatternErrorEnum.pinned_identifier_not_found_in_environment,
        ),
    )

    assert_type_check_pattern_error(
        ListPattern(IntegerPattern(1), ListPattern(PinIdentPattern("x"), ElistPattern())),
        ListType(IntegerType()),
        expected_context=(
            ListPatternContext(head=False),
            (ListPatternContext(head=True), PatternErrorEnum.pinned_identifier_not_found_in_environment),
        ),
    )


def test_type_check_tuple():
    assert_type_check_pattern_ok(TuplePattern([]), TupleType([]), expected_type=TupleType([]))

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x")]),
        TupleType([IntegerType()]),
        expected_type=TupleType([IntegerType()]),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x")]),
        TupleType([MapType({MapKey(1, IntegerType()): TupleType([])})]),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=TupleType([MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})]),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("y")]),
        TupleType([IntegerType(), FloatType()]),
        expected_type=TupleType([IntegerType(), FloatType()]),
        expected_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x")]),
        TupleType([IntegerType(), IntegerType()]),
        expected_type=TupleType([IntegerType(), IntegerType()]),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([])}),
                MapType({MapKey(2, IntegerType()): TupleType([])}),
            ]
        ),
        expected_type=TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
            ]
        ),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("y"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([])}),
                MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapType({MapKey(3, IntegerType()): TupleType([])}),
            ]
        ),
        expected_type=TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(3, IntegerType()): TupleType([])}),
                MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(3, IntegerType()): TupleType([])}),
            ]
        ),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(3, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(2, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        TuplePattern([PinIdentPattern("x"), IdentPattern("y"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([])}),
                MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapType({MapKey(3, IntegerType()): TupleType([])}),
            ]
        ),
        external_env={"x": MapType({MapKey(4, IntegerType()): TupleType([])})},
        expected_type=TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(4, IntegerType()): TupleType([])}),
                MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapType({MapKey(3, IntegerType()): TupleType([])}),
            ]
        ),
        expected_env={
            "x": MapType({MapKey(3, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(2, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_error(
        TuplePattern([IdentPattern("x")]),
        TupleType([FloatType(), IntegerType()]),
        expected_context=PatternErrorEnum.incompatible_tuples_error,
    )

    assert_type_check_pattern_error(
        TuplePattern([IntegerPattern(1), IdentPattern("x")]),
        TupleType([FloatType(), IntegerType()]),
        expected_context=(
            TuplePatternContext(n=1),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_type_check_pattern_error(
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

    assert_type_check_pattern_error(
        TuplePattern([IdentPattern("x")]),
        ListType(FloatType()),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )


def test_type_check_map():
    assert_type_check_pattern_ok(
        MapPattern(OrderedDict()),
        MapType({}),
        expected_type=MapType({}),
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x"))])),
        MapType({MapKey(1, IntegerType()): IntegerType()}),
        expected_type=MapType({MapKey(1, IntegerType()): IntegerType()}),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict()),
        MapType({MapKey(1, IntegerType()): IntegerType()}),
        expected_type=MapType({MapKey(1, IntegerType()): IntegerType()}),
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x")), (MapKey(2, IntegerType()), FloatPattern(2.0))])),
        MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): FloatType()}),
        expected_type=MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): FloatType()}),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(2, IntegerType()), FloatPattern(2.0)), (MapKey(1, IntegerType()), IdentPattern("x"))])),
        MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): FloatType()}),
        expected_type=MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): FloatType()}),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(2, IntegerType()), FloatPattern(2.0)), (MapKey(1, IntegerType()), IdentPattern("x"))])),
        MapType({MapKey(2, IntegerType()): FloatType(), MapKey(1, IntegerType()): IntegerType()}),
        expected_type=MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): FloatType()}),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x")), (MapKey(2, IntegerType()), FloatPattern(2.0))])),
        MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): FloatType()}),
        expected_type=MapType({MapKey(2, IntegerType()): FloatType(), MapKey(1, IntegerType()): IntegerType()}),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x"))])),
        MapType({MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([])})}),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=MapType({MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})}),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x")), (MapKey(2, IntegerType()), IdentPattern("y"))])),
        MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): FloatType()}),
        expected_type=MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): FloatType()}),
        expected_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x")), (MapKey(2, IntegerType()), IdentPattern("x"))])),
        MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): IntegerType()}),
        expected_type=MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): IntegerType()}),
        expected_env={"x": IntegerType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(2, IntegerType()), IntegerPattern(3))])),
        MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): NumberType()}),
        expected_type=MapType({MapKey(1, IntegerType()): IntegerType(), MapKey(2, IntegerType()): IntegerType()}),
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x")), (MapKey(2, IntegerType()), IdentPattern("x"))])),
        MapType(
            {
                MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([])}),
                MapKey(2, IntegerType()): MapType({MapKey(2, IntegerType()): TupleType([])}),
            }
        ),
        expected_type=MapType(
            {
                MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
                MapKey(2, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
            }
        ),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        MapPattern(
            OrderedDict(
                [
                    (MapKey(1, IntegerType()), IdentPattern("x")),
                    (MapKey(2, IntegerType()), IdentPattern("y")),
                    (MapKey(3, IntegerType()), IdentPattern("x")),
                ]
            )
        ),
        MapType(
            {
                MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([])}),
                MapKey(2, IntegerType()): MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapKey(3, IntegerType()): MapType({MapKey(3, IntegerType()): TupleType([])}),
            }
        ),
        expected_type=MapType(
            {
                MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(3, IntegerType()): TupleType([])}),
                MapKey(2, IntegerType()): MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapKey(3, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(3, IntegerType()): TupleType([])}),
            }
        ),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(3, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(2, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        MapPattern(
            OrderedDict(
                [
                    (MapKey(1, IntegerType()), PinIdentPattern("x")),
                    (MapKey(2, IntegerType()), IdentPattern("y")),
                    (MapKey(3, IntegerType()), IdentPattern("x")),
                ]
            )
        ),
        MapType(
            {
                MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([])}),
                MapKey(2, IntegerType()): MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapKey(3, IntegerType()): MapType({MapKey(3, IntegerType()): TupleType([])}),
            }
        ),
        external_env={"x": MapType({MapKey(4, IntegerType()): TupleType([])})},
        expected_type=MapType(
            {
                MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(4, IntegerType()): TupleType([])}),
                MapKey(2, IntegerType()): MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapKey(3, IntegerType()): MapType({MapKey(3, IntegerType()): TupleType([])}),
            }
        ),
        expected_env={
            "x": MapType({MapKey(3, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(2, IntegerType()): TupleType([])}),
        },
    )
    assert_type_check_pattern_error(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x"))])),
        MapType({MapKey(2, IntegerType()): FloatType(), MapKey(3, IntegerType()): IntegerType()}),
        expected_context=PatternErrorEnum.incompatible_maps_error,
    )

    assert_type_check_pattern_error(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IntegerPattern(1)), (MapKey(2, IntegerType()), IdentPattern("x"))])),
        MapType({MapKey(1, IntegerType()): FloatType(), MapKey(2, IntegerType()): IntegerType()}),
        expected_context=(
            MapPatternContext(key=MapKey(1, IntegerType())),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_type_check_pattern_error(
        MapPattern(OrderedDict([(MapKey(2, IntegerType()), IdentPattern("x")), (MapKey(1, IntegerType()), IntegerPattern(1))])),
        MapType({MapKey(1, IntegerType()): FloatType(), MapKey(2, IntegerType()): IntegerType()}),
        expected_context=(
            MapPatternContext(key=MapKey(1, IntegerType())),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_type_check_pattern_error(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IntegerPattern(1)), (MapKey(2, IntegerType()), IdentPattern("x"))])),
        MapType({MapKey(2, IntegerType()): IntegerType(), MapKey(1, IntegerType()): FloatType()}),
        expected_context=(
            MapPatternContext(key=MapKey(1, IntegerType())),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_type_check_pattern_error(
        MapPattern(OrderedDict([(MapKey(2, IntegerType()), IdentPattern("x")), (MapKey(1, IntegerType()), IntegerPattern(1))])),
        MapType({MapKey(1, IntegerType()): FloatType(), MapKey(2, IntegerType()): IntegerType()}),
        expected_context=(
            MapPatternContext(key=MapKey(1, IntegerType())),
            PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_type_check_pattern_error(
        MapPattern(
            OrderedDict(
                [
                    (MapKey(1, IntegerType()), WildPattern()),
                    (MapKey(2, IntegerType()), WildPattern()),
                    (
                        MapKey(3, IntegerType()),
                        MapPattern(
                            OrderedDict(
                                [
                                    (
                                        MapKey(1, IntegerType()),
                                        MapPattern(
                                            OrderedDict(
                                                [
                                                    (MapKey(1, IntegerType()), IntegerPattern(1)),
                                                    (MapKey(2, IntegerType()), IdentPattern("x")),
                                                ]
                                            )
                                        ),
                                    ),
                                    (MapKey(2, IntegerType()), IdentPattern("x")),
                                ]
                            )
                        ),
                    ),
                ]
            )
        ),
        MapType(
            {
                MapKey(1, IntegerType()): FloatType(),
                MapKey(2, IntegerType()): FloatType(),
                MapKey(3, IntegerType()): MapType(
                    {
                        MapKey(1, IntegerType()): MapType({MapKey(1, IntegerType()): FloatType(), MapKey(2, IntegerType()): IntegerType()}),
                        MapKey(2, IntegerType()): FloatType(),
                    }
                ),
            }
        ),
        expected_context=(
            MapPatternContext(key=MapKey(3, IntegerType())),
            (
                MapPatternContext(key=MapKey(1, IntegerType())),
                (
                    MapPatternContext(key=MapKey(1, IntegerType())),
                    PatternErrorEnum.incompatible_type_for_literal,
                ),
            ),
        ),
    )

    assert_type_check_pattern_error(
        MapPattern(
            OrderedDict(
                [
                    (MapKey(2, IntegerType()), WildPattern()),
                    (MapKey(3, IntegerType()), WildPattern()),
                    (
                        MapKey(1, IntegerType()),
                        MapPattern(
                            OrderedDict(
                                [
                                    (
                                        MapKey(1, IntegerType()),
                                        MapPattern(
                                            OrderedDict(
                                                [
                                                    (MapKey(2, IntegerType()), IntegerPattern(1)),
                                                    (MapKey(1, IntegerType()), IdentPattern("x")),
                                                ]
                                            )
                                        ),
                                    ),
                                    (MapKey(2, IntegerType()), IdentPattern("x")),
                                ]
                            )
                        ),
                    ),
                ]
            )
        ),
        MapType(
            {
                MapKey(2, IntegerType()): FloatType(),
                MapKey(3, IntegerType()): FloatType(),
                MapKey(1, IntegerType()): MapType(
                    {
                        MapKey(1, IntegerType()): MapType({MapKey(2, IntegerType()): FloatType(), MapKey(1, IntegerType()): IntegerType()}),
                        MapKey(2, IntegerType()): FloatType(),
                    }
                ),
            }
        ),
        expected_context=(
            MapPatternContext(key=MapKey(1, IntegerType())),
            (
                MapPatternContext(key=MapKey(1, IntegerType())),
                (
                    MapPatternContext(key=MapKey(2, IntegerType())),
                    PatternErrorEnum.incompatible_type_for_literal,
                ),
            ),
        ),
    )

    assert_type_check_pattern_error(
        MapPattern(OrderedDict([(MapKey(2, IntegerType()), IdentPattern("x"))])),
        ListType(FloatType()),
        expected_context=PatternErrorEnum.incompatible_constructors_error,
    )


def test_type_check_any():
    assert_type_check_pattern_ok(IntegerPattern(1), AnyType(), expected_type=IntegerType())

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        AnyType(),
        env={"x": IntegerType()},
        expected_type=IntegerType(),
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        IntegerType(),
        env={"x": IntegerType()},
        expected_type=IntegerType(),
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        AnyType(),
        env={"x": NumberType()},
        expected_type=AnyType(),
        expected_env={"x": AnyType()},
    )

    assert_type_check_pattern_ok(
        IdentPattern("x"),
        NumberType(),
        env={"x": AnyType()},
        expected_type=AnyType(),
    )

    assert_type_check_pattern_ok(
        PinIdentPattern("x"),
        AnyType(),
        external_env={"x": NumberType()},
        expected_type=AnyType(),
    )

    assert_type_check_pattern_ok(
        PinIdentPattern("x"),
        NumberType(),
        external_env={"x": AnyType()},
        expected_type=AnyType(),
    )

    assert_type_check_pattern_ok(ElistPattern(), AnyType(), expected_type=ElistType())

    assert_type_check_pattern_ok(
        ListPattern(WildPattern(), ElistPattern()),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(IntegerPattern(1), WildPattern()),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(IntegerPattern(1), ListPattern(IntegerPattern(2), ElistPattern())),
        AnyType(),
        expected_type=ListType(IntegerType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(WildPattern(), ListPattern(IntegerPattern(2), ElistPattern())),
        ListType(IntegerType()),
        expected_type=ListType(IntegerType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(WildPattern(), ListPattern(IntegerPattern(2), ElistPattern())),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(WildPattern(), WildPattern()),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(WildPattern(), ListPattern(WildPattern(), ElistPattern())),
        AnyType(),
        expected_type=ListType(AnyType()),
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        expected_type=ListType(AnyType()),
        expected_env={"x": AnyType()},
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        env={"x": NumberType()},
        expected_type=ListType(AnyType()),
        expected_env={"x": AnyType()},
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        env={"x": NumberType()},
        expected_type=ListType(AnyType()),
        expected_env={"x": AnyType(), "y": AnyType()},
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        env={"x": NumberType(), "y": NumberType()},
        expected_type=ListType(AnyType()),
        expected_env={"x": AnyType(), "y": AnyType()},
    )

    assert_type_check_pattern_ok(TuplePattern([]), AnyType(), expected_type=TupleType([]))

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x")]),
        AnyType(),
        expected_type=TupleType([AnyType()]),
        expected_env={"x": AnyType()},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("y")]),
        AnyType(),
        expected_type=TupleType([AnyType(), AnyType()]),
        expected_env={"x": AnyType(), "y": AnyType()},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x")]),
        AnyType(),
        expected_type=TupleType([AnyType(), AnyType()]),
        expected_env={"x": AnyType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(OrderedDict([(MapKey(1, IntegerType()), IdentPattern("x")), (MapKey(2, IntegerType()), IdentPattern("y"))])),
        AnyType(),
        expected_type=MapType({MapKey(1, IntegerType()): AnyType(), MapKey(2, IntegerType()): AnyType()}),
        expected_env={"x": AnyType(), "y": AnyType()},
    )

    assert_type_check_pattern_error(
        ListPattern(IntegerPattern(1), ListPattern(AtomLiteralPattern("true"), ElistPattern())),
        AnyType(),
        expected_context=PatternErrorEnum.incompatible_type_for_pattern,
    )

    assert_type_check_pattern_error(
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

    assert_type_check_pattern_error(
        ListPattern(
            MapPattern(OrderedDict([(MapKey(1, IntegerType()), TuplePattern([IntegerPattern(1), IntegerPattern(2)]))])),
            ListPattern(
                MapPattern(
                    OrderedDict(
                        [
                            (
                                MapKey(1, IntegerType()),
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

    assert_type_check_pattern_ok(
        ListPattern(
            MapPattern(OrderedDict([(MapKey(1, IntegerType()), TuplePattern([IntegerPattern(1), IntegerPattern(2)]))])),
            ListPattern(
                MapPattern(
                    OrderedDict(
                        [
                            (
                                MapKey(2, IntegerType()),
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


def test_type_check_ok_progressions():
    assert_type_check_pattern_ok(
        ListPattern(
            PinIdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        external_env={"x": MapType({MapKey(3, IntegerType()): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(1, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        ListPattern(
            PinIdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        env={"x": MapType({MapKey(2, IntegerType()): TupleType([]), MapKey(3, IntegerType()): TupleType([])})},
        external_env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        expected_env={
            "x": MapType(
                {
                    MapKey(1, IntegerType()): TupleType([]),
                    MapKey(2, IntegerType()): TupleType([]),
                    MapKey(3, IntegerType()): TupleType([]),
                }
            ),
            "y": MapType({MapKey(1, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        ListPattern(
            PinIdentPattern("x"),
            ListPattern(
                IdentPattern("x"),
                ListPattern(IdentPattern("y"), ElistPattern()),
            ),
        ),
        ListType(MapType({MapKey(1, IntegerType()): TupleType([])})),
        env={
            "x": MapType({MapKey(2, IntegerType()): TupleType([]), MapKey(3, IntegerType()): TupleType([])}),
            "y": MapType({MapKey(2, IntegerType()): TupleType([])}),
        },
        external_env={"x": MapType({MapKey(2, IntegerType()): TupleType([])})},
        expected_type=ListType(MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})),
        expected_env={
            "x": MapType(
                {
                    MapKey(1, IntegerType()): TupleType([]),
                    MapKey(2, IntegerType()): TupleType([]),
                    MapKey(3, IntegerType()): TupleType([]),
                }
            ),
            "y": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
        },
    )

    assert_type_check_pattern_ok(
        ListPattern(
            ListPattern(IntegerPattern(1), ElistPattern()),
            ListPattern(ListPattern(FloatPattern(1.0), ElistPattern()), ElistPattern()),
        ),
        ListType(ListType(NumberType())),
        expected_type=ListType(ListType(NumberType())),
    )

    assert_type_check_pattern_ok(
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

    assert_type_check_pattern_ok(
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

    assert_type_check_pattern_ok(
        ListPattern(
            TuplePattern([IntegerPattern(1), IntegerPattern(2)]),
            ListPattern(TuplePattern([IntegerPattern(1), FloatPattern(2.0)]), ElistPattern()),
        ),
        ListType(TupleType([IntegerType(), NumberType()])),
        expected_type=ListType(TupleType([IntegerType(), NumberType()])),
    )

    assert_type_check_pattern_ok(
        ListPattern(
            TuplePattern([IntegerPattern(1), IntegerPattern(2)]),
            ListPattern(TuplePattern([IntegerPattern(1), FloatPattern(2.0)]), ElistPattern()),
        ),
        ListType(TupleType([NumberType(), NumberType()])),
        expected_type=ListType(TupleType([IntegerType(), NumberType()])),
    )

    assert_type_check_pattern_ok(
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

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x")]),
        TupleType([MapType({MapKey(1, IntegerType()): TupleType([])})]),
        expected_type=TupleType([MapType({MapKey(1, IntegerType()): TupleType([])})]),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([])}),
                MapType({MapKey(2, IntegerType()): TupleType([])}),
            ]
        ),
        expected_type=TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}),
            ]
        ),
        expected_env={"x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])})},
    )

    assert_type_check_pattern_ok(
        TuplePattern([IdentPattern("x"), IdentPattern("x"), IdentPattern("x")]),
        TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([])}),
                MapType({MapKey(2, IntegerType()): TupleType([])}),
                MapType({MapKey(3, IntegerType()): TupleType([])}),
            ]
        ),
        expected_type=TupleType(
            [
                MapType(
                    {
                        MapKey(1, IntegerType()): TupleType([]),
                        MapKey(2, IntegerType()): TupleType([]),
                        MapKey(3, IntegerType()): TupleType([]),
                    }
                ),
                MapType(
                    {
                        MapKey(1, IntegerType()): TupleType([]),
                        MapKey(2, IntegerType()): TupleType([]),
                        MapKey(3, IntegerType()): TupleType([]),
                    }
                ),
                MapType(
                    {
                        MapKey(1, IntegerType()): TupleType([]),
                        MapKey(2, IntegerType()): TupleType([]),
                        MapKey(3, IntegerType()): TupleType([]),
                    }
                ),
            ]
        ),
        expected_env={
            "x": MapType(
                {
                    MapKey(1, IntegerType()): TupleType([]),
                    MapKey(2, IntegerType()): TupleType([]),
                    MapKey(3, IntegerType()): TupleType([]),
                }
            )
        },
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        env={"x": AtomLiteralType("true")},
        expected_type=ListType(AtomLiteralType("true")),
        expected_env={"x": AtomLiteralType("true")},
    )
    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        env={"x": BooleanType()},
        expected_type=ListType(AnyType()),
        expected_env={"x": AnyType()},
    )
    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ElistPattern()),
        AnyType(),
        env={"x": AtomType()},
        expected_type=ListType(AnyType()),
        expected_env={"x": AnyType()},
    )

    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        env={"x": AtomLiteralType("true")},
        expected_type=ListType(AnyType()),
        expected_env={"x": AtomLiteralType("true"), "y": AnyType()},
    )
    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        env={"x": BooleanType()},
        expected_type=ListType(AnyType()),
        expected_env={"x": AnyType(), "y": AnyType()},
    )
    assert_type_check_pattern_ok(
        ListPattern(IdentPattern("x"), ListPattern(IdentPattern("y"), ElistPattern())),
        AnyType(),
        env={"x": AtomType()},
        expected_type=ListType(AnyType()),
        expected_env={"x": AnyType(), "y": AnyType()},
    )

    assert_type_check_pattern_ok(
        TuplePattern(
            [
                ListPattern(IdentPattern("x"), ElistPattern()),
                TuplePattern([IdentPattern("x"), IdentPattern("x")]),
            ]
        ),
        AnyType(),
        env={"x": BooleanType()},
        expected_type=TupleType([ListType(AnyType()), TupleType([AnyType(), AnyType()])]),
        expected_env={"x": AnyType()},
    )

    assert_type_check_pattern_ok(
        MapPattern(
            OrderedDict(
                [
                    (
                        MapKey(1, IntegerType()),
                        TuplePattern(
                            [
                                ListPattern(IdentPattern("x"), ElistPattern()),
                                TuplePattern([IdentPattern("x"), IdentPattern("x")]),
                            ]
                        ),
                    ),
                    (MapKey(2, IntegerType()), IdentPattern("x")),
                ]
            )
        ),
        AnyType(),
        env={"x": NumberType()},
        expected_type=MapType(
            {
                MapKey(1, IntegerType()): TupleType([ListType(AnyType()), TupleType([AnyType(), AnyType()])]),
                MapKey(2, IntegerType()): AnyType(),
            }
        ),
        expected_env={"x": AnyType()},
    )


def test_type_check_errors():
    assert_type_check_pattern_error(
        ListPattern(
            TuplePattern(
                [
                    ListPattern(
                        MapPattern(OrderedDict([(MapKey(2, IntegerType()), TuplePattern([]))])),
                        ListPattern(
                            MapPattern(OrderedDict([(MapKey(2, IntegerType()), TuplePattern([]))])),
                            ListPattern(
                                MapPattern(OrderedDict([(MapKey(2, IntegerType()), ElistPattern())])),
                                ElistPattern(),
                            ),
                        ),
                    )
                ]
            ),
            ElistPattern(),
        ),
        ListType(TupleType([ListType(MapType({MapKey(2, IntegerType()): TupleType([])}))])),
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
                                MapPatternContext(key=MapKey(2, IntegerType())),
                                PatternErrorEnum.incompatible_constructors_error,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
