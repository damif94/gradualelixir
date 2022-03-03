from collections import OrderedDict

from gradualelixir import pattern, utils
from gradualelixir.pattern import (
    AtomLiteralPattern,
    ElistPattern,
    FloatPattern,
    IdentPattern,
    IntegerPattern,
    ListPattern,
    ListPatternContext,
    MapPattern,
    PinIdentPattern,
    TuplePattern,
    WildPattern,
)
from gradualelixir.tests import TEST_ENV
from gradualelixir.types import (
    AnyType,
    ElistType,
    FloatType,
    FunctionType,
    IntegerType,
    ListType,
    MapKey,
    MapType,
    NumberType,
    TupleType,
)
from gradualelixir.utils import long_line, parse_type

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


def pattern_match(pat, tau, gamma_env, sigma_env):
    gamma_env = {k: utils.parse_type(v) for k, v in gamma_env.items()}
    sigma_env = {k: utils.parse_type(v) for k, v in sigma_env.items()}
    return pattern.pattern_match(utils.parse_pattern(pat), utils.parse_type(tau), gamma_env, sigma_env)


def assert_pattern_match_ok(pattern_input, pattern_output):
    pattern_output_type = parse_type(pattern_output[0])
    pattern_output_env = {k: utils.parse_type(v) for k, v in pattern_output[1].items()}
    output = pattern_match(*pattern_input)
    assert (output.type, output.env) == (pattern_output_type, pattern_output_env)

    pattern_input = list(pattern_input)
    pattern_input[0] = utils.parse_pattern(pattern_input[0])
    pattern_input[1] = parse_type(pattern_input[1])
    pattern_input[2] = {k: utils.parse_type(v) for k, v in pattern_input[2].items()}
    pattern_input[3] = {k: utils.parse_type(v) for k, v in pattern_input[3].items()}
    to_print = OrderedDict(
        [
            ("hijacked_pattern_env", pattern_input[2].__repr__()),
            ("env", pattern_input[3].__repr__()),
            ("expected_type", pattern_output_type.__repr__()),
            ("expected_pattern_env", pattern_output_env.__repr__()),
        ]
    )

    if to_print["hijacked_pattern_env"] == {}:
        to_print.pop("hijacked_pattern_env")
    if to_print["env"] == {}:
        to_print.pop("env")
    if to_print["expected_pattern_env"] == to_print["hijacked_pattern_env"]:
        to_print.pop("expected_pattern_env")
    to_print_msg = ", ".join([f"{key}={value}" for key, value in to_print.items()])

    print()
    print(f"assert_pattern_match_okk({pattern_input[0].__repr__()}, {pattern_input[1].__repr__()}, {to_print_msg})")


def assert_pattern_match_okk(
    pat, type, hijacked_pattern_env=None, env=None, expected_type=None, expected_pattern_env=None
):
    env = env or {}
    hijacked_pattern_env = hijacked_pattern_env or {}
    expected_pattern_env = expected_pattern_env or hijacked_pattern_env

    ret = pattern.pattern_match(pat, type, hijacked_pattern_env, env)
    assert isinstance(ret, pattern.PatternMatchSuccess)
    assert ret.type == expected_type
    assert ret.env == expected_pattern_env
    if TEST_ENV.get("display_results"):
        print(f"\n{long_line}\n\n{ret.message(pat, type, env, expected_pattern_env)}")


def assert_pattern_match_errorr(pat, type, hijacked_pattern_env=None, env=None, expected_context=None):
    env = env or {}
    hijacked_pattern_env = hijacked_pattern_env or {}

    ret = pattern.pattern_match(pat, type, hijacked_pattern_env, env)
    assert isinstance(ret, pattern.PatternMatchError)
    check_context_path(ret, expected_context)
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        env_args = {"pattern": pat, "type": type, "env": env, "hijacked_pattern_env": hijacked_pattern_env}
        print(f"\n{long_line}\n\n{ret.message(padding='', **env_args)}")


def assert_pattern_match_error(pattern_match_input, context_path=None):
    pat, tau, gamma_env, sigma_env = pattern_match_input
    return_value = pattern_match(pat, tau, gamma_env, sigma_env)
    if len(context_path) == 1:
        assert isinstance(return_value, pattern.BasePatternMatchError)
        assert return_value.kind is context_path[-1]
    else:
        assert isinstance(return_value, pattern.NestedPatternMatchError)
        current_value = return_value
        for klass, arg in context_path[:-1]:
            current_context = current_value.context
            assert isinstance(current_context, pattern.PatternContext)
            if klass == pattern.ListPatternContext:
                assert isinstance(current_context, pattern.ListPatternContext)
                assert current_context.head == arg
            elif klass == pattern.TuplePatternContext:
                assert isinstance(current_context, pattern.TuplePatternContext)
                assert current_context.n == arg
            else:
                assert klass == pattern.MapPatternContext
                assert isinstance(current_context, pattern.MapPatternContext)
                assert current_context.key == arg
            current_value = current_value.error
        assert isinstance(current_value, pattern.BasePatternMatchError)
        assert current_value.kind is context_path[-1]

    pattern_input = list(pattern_match_input)
    pattern_input[0] = utils.parse_pattern(pattern_input[0])
    pattern_input[1] = parse_type(pattern_input[1])
    pattern_input[2] = {k: utils.parse_type(v) for k, v in pattern_input[2].items()}
    pattern_input[3] = {k: utils.parse_type(v) for k, v in pattern_input[3].items()}
    to_print = OrderedDict(
        [
            ("hijacked_pattern_env", pattern_input[2].__repr__()),
            ("env", pattern_input[3].__repr__()),
        ]
    )

    if to_print["hijacked_pattern_env"] == {}:
        to_print.pop("hijacked_pattern_env")
    if to_print["env"] == {}:
        to_print.pop("env")
    to_print_msg = ", ".join([f"{key}={value}" for key, value in to_print.items()])

    print()
    print(f"assert_pattern_match_errorr({pattern_input[0].__repr__()}, {pattern_input[1].__repr__()}, {to_print_msg})")


def check_context_path(error_data: pattern.PatternMatchError, context_path):
    if isinstance(error_data, pattern.NestedPatternMatchError):
        assert isinstance(context_path, tuple)
        context_instance = context_path[0][0](pattern=error_data.context.pattern, **context_path[0][1])
        assert error_data.context == context_instance
        check_context_path(error_data.error, context_path[1])
    else:
        assert isinstance(error_data, pattern.BasePatternMatchError)
        assert error_data.kind is context_path


def sett(*args):
    args = list(args)
    args.sort()
    aux = OrderedDict()
    for k in args:
        aux[k] = ()
    return aux


def test_tp_pin():
    assert_pattern_match_okk(
        PinIdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={"x": IntegerType()},
        expected_type=IntegerType(),
    )
    assert_pattern_match_okk(
        PinIdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={"x": NumberType()},
        expected_type=IntegerType(),
    )

    assert_pattern_match_okk(
        PinIdentPattern(identifier="x"),
        MapType({MapKey(1): TupleType(types=[])}),
        hijacked_pattern_env={},
        env={"x": MapType({MapKey(2): TupleType(types=[])})},
        expected_type=MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
    )

    assert_pattern_match_errorr(
        PinIdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={"y": IntegerType()},
        expected_context=pattern.PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )
    assert_pattern_match_errorr(
        PinIdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={"x": FloatType()},
        expected_context=pattern.PatternErrorEnum.incompatible_type_for_pinned_variable,
    )

    assert_pattern_match_errorr(
        PinIdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={"x": FloatType()},
        expected_context=pattern.PatternErrorEnum.incompatible_type_for_pinned_variable,
    )
    assert_pattern_match_errorr(
        PinIdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={"y": IntegerType()},
        expected_context=pattern.PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )

    assert_pattern_match_errorr(
        PinIdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={"x": IntegerType()},
        env={"y": IntegerType()},
        expected_context=pattern.PatternErrorEnum.pinned_identifier_not_found_in_environment,
    )

    assert_pattern_match_errorr(
        PinIdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={"x": FunctionType(arg_types=[IntegerType()], ret_type=IntegerType())},
        expected_context=pattern.PatternErrorEnum.arrow_types_into_pinned_identifier,
    )


def test_tp_wild():
    assert_pattern_match_okk(WildPattern(), IntegerType(), hijacked_pattern_env={}, env={}, expected_type=IntegerType())

    assert_pattern_match_okk(
        WildPattern(),
        IntegerType(),
        hijacked_pattern_env={"x": FloatType()},
        env={"y": NumberType()},
        expected_type=IntegerType(),
    )

    assert_pattern_match_okk(
        WildPattern(),
        ListType(type=FloatType()),
        hijacked_pattern_env={"x": FloatType()},
        env={"y": NumberType()},
        expected_type=ListType(type=FloatType()),
    )


def test_tp_var():
    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={},
        expected_type=IntegerType(),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={},
        env={"x": FloatType()},
        expected_type=IntegerType(),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={"y": FloatType()},
        env={},
        expected_type=IntegerType(),
        expected_pattern_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        ListType(type=FloatType()),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=FloatType()),
        expected_pattern_env={"x": ListType(type=FloatType())},
    )


def test_tp_varn():
    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={"x": IntegerType()},
        env={},
        expected_type=IntegerType(),
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        MapType({MapKey(1): TupleType(types=[])}),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_type=MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})},
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        MapType({MapKey(1): TupleType(types=[])}),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={"x": MapType({MapKey(3): TupleType(types=[])})},
        expected_type=MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})},
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        MapType({MapKey(1): TupleType(types=[])}),
        hijacked_pattern_env={
            "x": MapType({MapKey(2): TupleType(types=[])}),
            "y": MapType({MapKey(3): TupleType(types=[])}),
        },
        env={},
        expected_type=MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
            "y": MapType({MapKey(3): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        MapType({MapKey(1): TupleType(types=[])}),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={"y": MapType({MapKey(3): TupleType(types=[])})},
        expected_type=MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})},
    )

    assert_pattern_match_errorr(
        IdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={"x": FloatType()},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_type_for_variable,
    )

    assert_pattern_match_errorr(
        IdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={"x": FunctionType(arg_types=[IntegerType()], ret_type=IntegerType())},
        env={},
        expected_context=pattern.PatternErrorEnum.arrow_types_into_nonlinear_identifier,
    )

    assert_pattern_match_errorr(
        IdentPattern(identifier="x"),
        FunctionType(arg_types=[IntegerType()], ret_type=IntegerType()),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_context=pattern.PatternErrorEnum.arrow_types_into_nonlinear_identifier,
    )


def test_tp_elist():
    assert_pattern_match_okk(ElistPattern(), ElistType(), hijacked_pattern_env={}, env={}, expected_type=ElistType())

    assert_pattern_match_okk(
        ElistPattern(), ListType(type=NumberType()), hijacked_pattern_env={}, env={}, expected_type=ElistType()
    )

    assert_pattern_match_errorr(
        ElistPattern(),
        IntegerType(),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_type_for_elist,
    )

    assert_pattern_match_errorr(
        ElistPattern(),
        TupleType(types=[IntegerType()]),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_type_for_elist,
    )


def test_tp_list():
    assert_pattern_match_okk(
        ListPattern(head=IntegerPattern(value=1), tail=ElistPattern()),
        ListType(type=IntegerType()),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=IntegerType()),
    )

    assert_pattern_match_okk(
        ListPattern(head=IdentPattern(identifier="x"), tail=ElistPattern()),
        ListType(type=IntegerType()),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=IntegerType()),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        ListPattern(head=IntegerPattern(value=1), tail=ListPattern(head=FloatPattern(value=1.0), tail=ElistPattern())),
        ListType(type=NumberType()),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=NumberType()),
    )

    assert_pattern_match_okk(
        ListPattern(
            head=IdentPattern(identifier="x"), tail=ListPattern(head=IdentPattern(identifier="x"), tail=ElistPattern())
        ),
        ListType(type=IntegerType()),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=IntegerType()),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        ListPattern(
            head=IdentPattern(identifier="x"), tail=ListPattern(head=IdentPattern(identifier="x"), tail=ElistPattern())
        ),
        ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_type=ListType(type=MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})},
    )

    assert_pattern_match_okk(
        ListPattern(
            head=IdentPattern(identifier="x"), tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern())
        ),
        ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        hijacked_pattern_env={"y": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_type=ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType(types=[])}),
            "y": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        ListPattern(
            head=IdentPattern(identifier="x"), tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern())
        ),
        ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_type=ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
            "y": MapType({MapKey(1): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        ListPattern(
            head=IdentPattern(identifier="x"),
            tail=ListPattern(
                head=IdentPattern(identifier="x"),
                tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern()),
            ),
        ),
        ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        hijacked_pattern_env={"y": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_type=ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType(types=[])}),
            "y": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        ListPattern(
            head=IdentPattern(identifier="x"),
            tail=ListPattern(
                head=IdentPattern(identifier="x"),
                tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern()),
            ),
        ),
        ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_type=ListType(type=MapType({MapKey(1): TupleType(types=[])})),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
            "y": MapType({MapKey(1): TupleType(types=[])}),
        },
    )

    assert_pattern_match_errorr(
        ListPattern(head=IntegerPattern(value=1), tail=ElistPattern()),
        IntegerType(),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_constructors_error,
    )

    assert_pattern_match_errorr(
        ListPattern(head=PinIdentPattern("x"), tail=ElistPattern()),
        ListType(IntegerType()),
        env={},
        expected_context=(
            (ListPatternContext, {"head": True}),
            pattern.PatternErrorEnum.pinned_identifier_not_found_in_environment,
        ),
    )

    assert_pattern_match_errorr(
        ListPattern(head=IntegerPattern(1), tail=ListPattern(head=PinIdentPattern("x"), tail=ElistPattern())),
        ListType(IntegerType()),
        env={},
        expected_context=(
            (ListPatternContext, {"head": False}),
            ((ListPatternContext, {"head": True}), pattern.PatternErrorEnum.pinned_identifier_not_found_in_environment),
        ),
    )


def test_tp_tuple():
    assert_pattern_match_okk(
        TuplePattern(items=[]), TupleType(types=[]), hijacked_pattern_env={}, env={}, expected_type=TupleType(types=[])
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x")]),
        TupleType(types=[IntegerType()]),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(types=[IntegerType()]),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x")]),
        TupleType(types=[MapType({MapKey(1): TupleType(types=[])})]),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_type=TupleType(types=[MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})]),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="y")]),
        TupleType(types=[IntegerType(), FloatType()]),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(types=[IntegerType(), FloatType()]),
        expected_pattern_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="x")]),
        TupleType(types=[IntegerType(), IntegerType()]),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(types=[IntegerType(), IntegerType()]),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="x")]),
        TupleType(
            types=[
                MapType({MapKey(1): TupleType(types=[])}),
                MapType({MapKey(2): TupleType(types=[])}),
            ]
        ),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(
            types=[
                MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
                MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
            ]
        ),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="y"), IdentPattern(identifier="x")]),
        TupleType(
            types=[
                MapType({MapKey(1): TupleType(types=[])}),
                MapType({MapKey(2): TupleType(types=[])}),
                MapType({MapKey(3): TupleType(types=[])}),
            ]
        ),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(
            types=[
                MapType({MapKey(1): TupleType(types=[]), MapKey(3): TupleType(types=[])}),
                MapType({MapKey(2): TupleType(types=[])}),
                MapType({MapKey(1): TupleType(types=[]), MapKey(3): TupleType(types=[])}),
            ]
        ),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType(types=[]), MapKey(3): TupleType(types=[])}),
            "y": MapType({MapKey(2): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        TuplePattern(
            items=[PinIdentPattern(identifier="x"), IdentPattern(identifier="y"), IdentPattern(identifier="x")]
        ),
        TupleType(
            types=[
                MapType({MapKey(1): TupleType(types=[])}),
                MapType({MapKey(2): TupleType(types=[])}),
                MapType({MapKey(3): TupleType(types=[])}),
            ]
        ),
        hijacked_pattern_env={},
        env={"x": MapType({MapKey(4): TupleType(types=[])})},
        expected_type=TupleType(
            types=[
                MapType({MapKey(1): TupleType(types=[]), MapKey(4): TupleType(types=[])}),
                MapType({MapKey(2): TupleType(types=[])}),
                MapType({MapKey(3): TupleType(types=[])}),
            ]
        ),
        expected_pattern_env={
            "x": MapType({MapKey(3): TupleType(types=[])}),
            "y": MapType({MapKey(2): TupleType(types=[])}),
        },
    )

    assert_pattern_match_errorr(
        TuplePattern(items=[IdentPattern(identifier="x")]),
        TupleType(types=[FloatType(), IntegerType()]),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_tuples_error,
    )

    assert_pattern_match_errorr(
        TuplePattern(items=[IntegerPattern(value=1), IdentPattern(identifier="x")]),
        TupleType(types=[FloatType(), IntegerType()]),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (pattern.TuplePatternContext, {"n": 1}),
            pattern.PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_errorr(
        TuplePattern(
            items=[
                WildPattern(),
                WildPattern(),
                TuplePattern(
                    items=[
                        TuplePattern(items=[IntegerPattern(value=1), IdentPattern(identifier="x")]),
                        IdentPattern(identifier="x"),
                    ]
                ),
            ]
        ),
        TupleType(
            types=[
                FloatType(),
                FloatType(),
                TupleType(types=[TupleType(types=[FloatType(), IntegerType()]), FloatType()]),
            ]
        ),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (pattern.TuplePatternContext, {"n": 3}),
            (
                (pattern.TuplePatternContext, {"n": 1}),
                ((pattern.TuplePatternContext, {"n": 1}), pattern.PatternErrorEnum.incompatible_type_for_literal),
            ),
        ),
    )

    assert_pattern_match_errorr(
        TuplePattern(items=[IdentPattern(identifier="x")]),
        ListType(type=FloatType()),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_constructors_error,
    )


def test_tp_map():
    assert_pattern_match_okk(
        MapPattern(OrderedDict()),
        MapType({}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({}),
    )

    assert_pattern_match_okk(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern(identifier="x"))])),
        MapType({MapKey(1): IntegerType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): IntegerType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        MapPattern(OrderedDict()),
        MapType({MapKey(1): IntegerType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): IntegerType()}),
    )

    assert_pattern_match_okk(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern(identifier="x")), (MapKey(2), FloatPattern(value=2.0))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        MapPattern(OrderedDict([(MapKey(2), FloatPattern(value=2.0)), (MapKey(1), IdentPattern(identifier="x"))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        MapPattern(OrderedDict([(MapKey(2), FloatPattern(value=2.0)), (MapKey(1), IdentPattern(identifier="x"))])),
        MapType({MapKey(2): FloatType(), MapKey(1): IntegerType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern(identifier="x")), (MapKey(2), FloatPattern(value=2.0))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(2): FloatType(), MapKey(1): IntegerType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern(identifier="x"))])),
        MapType({MapKey(1): MapType({MapKey(1): TupleType(types=[])})}),
        hijacked_pattern_env={"x": MapType({MapKey(2): TupleType(types=[])})},
        env={},
        expected_type=MapType(
            map_type={MapKey(1): MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})}
        ),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})},
    )

    assert_pattern_match_okk(
        MapPattern(
            map=OrderedDict([(MapKey(1), IdentPattern(identifier="x")), (MapKey(2), IdentPattern(identifier="y"))])
        ),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        expected_pattern_env={"x": IntegerType(), "y": FloatType()},
    )

    assert_pattern_match_okk(
        MapPattern(
            map=OrderedDict([(MapKey(1), IdentPattern(identifier="x")), (MapKey(2), IdentPattern(identifier="x"))])
        ),
        MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        expected_pattern_env={"x": IntegerType()},
    )

    assert_pattern_match_okk(
        MapPattern(OrderedDict([(MapKey(2), IntegerPattern(value=3))])),
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
    )

    assert_pattern_match_okk(
        MapPattern(
            map=OrderedDict([(MapKey(1), IdentPattern(identifier="x")), (MapKey(2), IdentPattern(identifier="x"))])
        ),
        MapType(
            map_type={
                MapKey(1): MapType({MapKey(1): TupleType(types=[])}),
                MapKey(2): MapType({MapKey(2): TupleType(types=[])}),
            }
        ),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType(
            map_type={
                MapKey(1): MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
                MapKey(2): MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])}),
            }
        ),
        expected_pattern_env={"x": MapType({MapKey(1): TupleType(types=[]), MapKey(2): TupleType(types=[])})},
    )

    assert_pattern_match_okk(
        MapPattern(
            map=OrderedDict(
                [
                    (MapKey(1), IdentPattern(identifier="x")),
                    (MapKey(2), IdentPattern(identifier="y")),
                    (MapKey(3), IdentPattern(identifier="x")),
                ]
            )
        ),
        MapType(
            map_type={
                MapKey(1): MapType({MapKey(1): TupleType(types=[])}),
                MapKey(2): MapType({MapKey(2): TupleType(types=[])}),
                MapKey(3): MapType({MapKey(3): TupleType(types=[])}),
            }
        ),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType(
            map_type={
                MapKey(1): MapType({MapKey(1): TupleType(types=[]), MapKey(3): TupleType(types=[])}),
                MapKey(2): MapType({MapKey(2): TupleType(types=[])}),
                MapKey(3): MapType({MapKey(1): TupleType(types=[]), MapKey(3): TupleType(types=[])}),
            }
        ),
        expected_pattern_env={
            "x": MapType({MapKey(1): TupleType(types=[]), MapKey(3): TupleType(types=[])}),
            "y": MapType({MapKey(2): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        MapPattern(
            map=OrderedDict(
                [
                    (MapKey(1), PinIdentPattern(identifier="x")),
                    (MapKey(2), IdentPattern(identifier="y")),
                    (MapKey(3), IdentPattern(identifier="x")),
                ]
            )
        ),
        MapType(
            map_type={
                MapKey(1): MapType({MapKey(1): TupleType(types=[])}),
                MapKey(2): MapType({MapKey(2): TupleType(types=[])}),
                MapKey(3): MapType({MapKey(3): TupleType(types=[])}),
            }
        ),
        hijacked_pattern_env={},
        env={"x": MapType({MapKey(4): TupleType(types=[])})},
        expected_type=MapType(
            map_type={
                MapKey(1): MapType({MapKey(1): TupleType(types=[]), MapKey(4): TupleType(types=[])}),
                MapKey(2): MapType({MapKey(2): TupleType(types=[])}),
                MapKey(3): MapType({MapKey(3): TupleType(types=[])}),
            }
        ),
        expected_pattern_env={
            "x": MapType({MapKey(3): TupleType(types=[])}),
            "y": MapType({MapKey(2): TupleType(types=[])}),
        },
    )
    assert_pattern_match_errorr(
        MapPattern(OrderedDict([(MapKey(1), IdentPattern(identifier="x"))])),
        MapType({MapKey(2): FloatType(), MapKey(3): IntegerType()}),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_maps_error,
    )

    assert_pattern_match_errorr(
        MapPattern(OrderedDict([(MapKey(1), IntegerPattern(value=1)), (MapKey(2), IdentPattern(identifier="x"))])),
        MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (pattern.MapPatternContext, {"key": MapKey(1)}),
            pattern.PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_errorr(
        MapPattern(OrderedDict([(MapKey(2), IdentPattern(identifier="x")), (MapKey(1), IntegerPattern(value=1))])),
        MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (pattern.MapPatternContext, {"key": MapKey(1)}),
            pattern.PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_errorr(
        MapPattern(OrderedDict([(MapKey(1), IntegerPattern(value=1)), (MapKey(2), IdentPattern(identifier="x"))])),
        MapType({MapKey(2): IntegerType(), MapKey(1): FloatType()}),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (pattern.MapPatternContext, {"key": MapKey(1)}),
            pattern.PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_errorr(
        MapPattern(OrderedDict([(MapKey(2), IdentPattern(identifier="x")), (MapKey(1), IntegerPattern(value=1))])),
        MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (pattern.MapPatternContext, {"key": MapKey(1)}),
            pattern.PatternErrorEnum.incompatible_type_for_literal,
        ),
    )

    assert_pattern_match_errorr(
        MapPattern(
            map=OrderedDict(
                [
                    (MapKey(1), WildPattern()),
                    (MapKey(2), WildPattern()),
                    (
                        MapKey(3),
                        MapPattern(
                            map=OrderedDict(
                                [
                                    (
                                        MapKey(1),
                                        MapPattern(
                                            map=OrderedDict(
                                                [
                                                    (MapKey(1), IntegerPattern(value=1)),
                                                    (MapKey(2), IdentPattern(identifier="x")),
                                                ]
                                            )
                                        ),
                                    ),
                                    (MapKey(2), IdentPattern(identifier="x")),
                                ]
                            )
                        ),
                    ),
                ]
            )
        ),
        MapType(
            map_type={
                MapKey(1): FloatType(),
                MapKey(2): FloatType(),
                MapKey(3): MapType(
                    map_type={
                        MapKey(1): MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
                        MapKey(2): FloatType(),
                    }
                ),
            }
        ),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (
                (pattern.MapPatternContext, {"key": MapKey(3)}),
                (
                    (pattern.MapPatternContext, {"key": MapKey(1)}),
                    (
                        (pattern.MapPatternContext, {"key": MapKey(1)}),
                        pattern.PatternErrorEnum.incompatible_type_for_literal,
                    ),
                ),
            )
        ),
    )

    assert_pattern_match_errorr(
        MapPattern(
            map=OrderedDict(
                [
                    (MapKey(2), WildPattern()),
                    (MapKey(3), WildPattern()),
                    (
                        MapKey(1),
                        MapPattern(
                            map=OrderedDict(
                                [
                                    (
                                        MapKey(1),
                                        MapPattern(
                                            map=OrderedDict(
                                                [
                                                    (MapKey(2), IntegerPattern(value=1)),
                                                    (MapKey(1), IdentPattern(identifier="x")),
                                                ]
                                            )
                                        ),
                                    ),
                                    (MapKey(2), IdentPattern(identifier="x")),
                                ]
                            )
                        ),
                    ),
                ]
            )
        ),
        MapType(
            map_type={
                MapKey(2): FloatType(),
                MapKey(3): FloatType(),
                MapKey(1): MapType(
                    map_type={
                        MapKey(1): MapType({MapKey(2): FloatType(), MapKey(1): IntegerType()}),
                        MapKey(2): FloatType(),
                    }
                ),
            }
        ),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (
                (pattern.MapPatternContext, {"key": MapKey(1)}),
                (
                    (pattern.MapPatternContext, {"key": MapKey(1)}),
                    (
                        (pattern.MapPatternContext, {"key": MapKey(2)}),
                        pattern.PatternErrorEnum.incompatible_type_for_literal,
                    ),
                ),
            )
        ),
    )

    assert_pattern_match_errorr(
        MapPattern(OrderedDict([(MapKey(2), IdentPattern(identifier="x"))])),
        ListType(type=FloatType()),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_constructors_error,
    )


def test_tp_any():
    assert_pattern_match_okk(
        IntegerPattern(value=1), AnyType(), hijacked_pattern_env={}, env={}, expected_type=IntegerType()
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        AnyType(),
        hijacked_pattern_env={"x": IntegerType()},
        env={},
        expected_type=IntegerType(),
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        IntegerType(),
        hijacked_pattern_env={"x": IntegerType()},
        env={},
        expected_type=IntegerType(),
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        env={},
        expected_type=AnyType(),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_okk(
        IdentPattern(identifier="x"),
        NumberType(),
        hijacked_pattern_env={"x": AnyType()},
        env={},
        expected_type=AnyType(),
    )

    assert_pattern_match_okk(
        PinIdentPattern(identifier="x"),
        AnyType(),
        hijacked_pattern_env={},
        env={"x": NumberType()},
        expected_type=AnyType(),
    )

    assert_pattern_match_okk(
        PinIdentPattern(identifier="x"),
        NumberType(),
        hijacked_pattern_env={},
        env={"x": AnyType()},
        expected_type=AnyType(),
    )

    assert_pattern_match_okk(ElistPattern(), AnyType(), hijacked_pattern_env={}, env={}, expected_type=ElistType())

    assert_pattern_match_okk(
        ListPattern(head=WildPattern(), tail=ElistPattern()),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=AnyType()),
    )

    assert_pattern_match_okk(
        ListPattern(head=IntegerPattern(value=1), tail=WildPattern()),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=AnyType()),
    )

    assert_pattern_match_okk(
        ListPattern(head=IntegerPattern(value=1), tail=ListPattern(head=IntegerPattern(value=2), tail=ElistPattern())),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=IntegerType()),
    )

    assert_pattern_match_okk(
        ListPattern(head=WildPattern(), tail=ListPattern(head=IntegerPattern(value=2), tail=ElistPattern())),
        ListType(type=IntegerType()),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=IntegerType()),
    )

    assert_pattern_match_okk(
        ListPattern(head=WildPattern(), tail=ListPattern(head=IntegerPattern(value=2), tail=ElistPattern())),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=AnyType()),
    )

    assert_pattern_match_okk(
        ListPattern(head=WildPattern(), tail=WildPattern()),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=AnyType()),
    )

    assert_pattern_match_okk(
        ListPattern(head=WildPattern(), tail=ListPattern(head=WildPattern(), tail=ElistPattern())),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=AnyType()),
    )

    assert_pattern_match_okk(
        ListPattern(head=IdentPattern(identifier="x"), tail=ElistPattern()),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=AnyType()),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_okk(
        ListPattern(head=IdentPattern(identifier="x"), tail=ElistPattern()),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        env={},
        expected_type=ListType(type=AnyType()),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_okk(
        ListPattern(
            head=IdentPattern(identifier="x"), tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern())
        ),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        env={},
        expected_type=ListType(type=AnyType()),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_okk(
        ListPattern(
            head=IdentPattern(identifier="x"), tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern())
        ),
        AnyType(),
        hijacked_pattern_env={"x": NumberType(), "y": NumberType()},
        env={},
        expected_type=ListType(type=AnyType()),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[]), AnyType(), hijacked_pattern_env={}, env={}, expected_type=TupleType(types=[])
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x")]),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(types=[AnyType()]),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="y")]),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(types=[AnyType(), AnyType()]),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="x")]),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(types=[AnyType(), AnyType()]),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_okk(
        MapPattern(
            map=OrderedDict([(MapKey(1), IdentPattern(identifier="x")), (MapKey(2), IdentPattern(identifier="y"))])
        ),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}),
        expected_pattern_env={"x": AnyType(), "y": AnyType()},
    )

    assert_pattern_match_errorr(
        ListPattern(
            head=IntegerPattern(value=1), tail=ListPattern(head=AtomLiteralPattern(value="true"), tail=ElistPattern())
        ),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_type_for_pattern,
    )

    assert_pattern_match_errorr(
        ListPattern(
            head=TuplePattern(items=[IntegerPattern(value=1), IntegerPattern(value=2)]),
            tail=ListPattern(
                head=TuplePattern(items=[AtomLiteralPattern(value="true"), IntegerPattern(value=2)]),
                tail=ElistPattern(),
            ),
        ),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_type_for_pattern,
    )

    assert_pattern_match_errorr(
        ListPattern(
            head=MapPattern(
                OrderedDict([(MapKey(1), TuplePattern(items=[IntegerPattern(value=1), IntegerPattern(value=2)]))])
            ),
            tail=ListPattern(
                head=MapPattern(
                    OrderedDict(
                        [
                            (
                                MapKey(1),
                                TuplePattern(
                                    items=[
                                        AtomLiteralPattern(value="true"),
                                        IntegerPattern(
                                            value=2,
                                        ),
                                    ]
                                ),
                            )
                        ]
                    )
                ),
                tail=ElistPattern(),
            ),
        ),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_context=pattern.PatternErrorEnum.incompatible_type_for_pattern,
    )

    assert_pattern_match_okk(
        ListPattern(
            head=MapPattern(
                map=OrderedDict([(MapKey(1), TuplePattern(items=[IntegerPattern(value=1), IntegerPattern(value=2)]))])
            ),
            tail=ListPattern(
                head=MapPattern(
                    map=OrderedDict(
                        [
                            (
                                MapKey(2),
                                TuplePattern(
                                    items=[
                                        AtomLiteralPattern(value="true"),
                                        IntegerPattern(
                                            value=2,
                                        ),
                                    ]
                                ),
                            )
                        ]
                    )
                ),
                tail=ElistPattern(),
            ),
        ),
        AnyType(),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=MapType({})),
    )


def test_tp_ok_progressions():
    assert_pattern_match_okk(
        ListPattern(
            head=PinIdentPattern(identifier="x"),
            tail=ListPattern(
                head=IdentPattern(identifier="x"),
                tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern()),
            ),
        ),
        ListType(type=MapType(map_type={MapKey(value=1): TupleType(types=[])})),
        hijacked_pattern_env={"x": MapType(map_type={MapKey(value=2): TupleType(types=[])})},
        env={"x": MapType(map_type={MapKey(value=3): TupleType(types=[])})},
        expected_type=ListType(type=MapType(map_type={MapKey(value=1): TupleType(types=[])})),
        expected_pattern_env={
            "x": MapType(map_type={MapKey(value=1): TupleType(types=[]), MapKey(value=2): TupleType(types=[])}),
            "y": MapType(map_type={MapKey(value=1): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        ListPattern(
            head=PinIdentPattern(identifier="x"),
            tail=ListPattern(
                head=IdentPattern(identifier="x"),
                tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern()),
            ),
        ),
        ListType(type=MapType(map_type={MapKey(value=1): TupleType(types=[])})),
        hijacked_pattern_env={
            "x": MapType(map_type={MapKey(value=2): TupleType(types=[]), MapKey(value=3): TupleType(types=[])})
        },
        env={"x": MapType(map_type={MapKey(value=2): TupleType(types=[])})},
        expected_type=ListType(type=MapType(map_type={MapKey(value=1): TupleType(types=[])})),
        expected_pattern_env={
            "x": MapType(
                map_type={
                    MapKey(value=1): TupleType(types=[]),
                    MapKey(value=2): TupleType(types=[]),
                    MapKey(value=3): TupleType(types=[]),
                }
            ),
            "y": MapType(map_type={MapKey(value=1): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        ListPattern(
            head=PinIdentPattern(identifier="x"),
            tail=ListPattern(
                head=IdentPattern(identifier="x"),
                tail=ListPattern(head=IdentPattern(identifier="y"), tail=ElistPattern()),
            ),
        ),
        ListType(type=MapType(map_type={MapKey(value=1): TupleType(types=[])})),
        hijacked_pattern_env={
            "x": MapType(map_type={MapKey(value=2): TupleType(types=[]), MapKey(value=3): TupleType(types=[])}),
            "y": MapType(map_type={MapKey(value=2): TupleType(types=[])}),
        },
        env={"x": MapType(map_type={MapKey(value=2): TupleType(types=[])})},
        expected_type=ListType(
            type=MapType(map_type={MapKey(value=1): TupleType(types=[]), MapKey(value=2): TupleType(types=[])})
        ),
        expected_pattern_env={
            "x": MapType(
                map_type={
                    MapKey(value=1): TupleType(types=[]),
                    MapKey(value=2): TupleType(types=[]),
                    MapKey(value=3): TupleType(types=[]),
                }
            ),
            "y": MapType(map_type={MapKey(value=1): TupleType(types=[]), MapKey(value=2): TupleType(types=[])}),
        },
    )

    assert_pattern_match_okk(
        ListPattern(
            head=ListPattern(head=IntegerPattern(value=1), tail=ElistPattern()),
            tail=ListPattern(head=ListPattern(head=FloatPattern(value=1.0), tail=ElistPattern()), tail=ElistPattern()),
        ),
        ListType(type=ListType(type=NumberType())),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=ListType(type=NumberType())),
    )

    assert_pattern_match_okk(
        ListPattern(
            head=ListPattern(head=ListPattern(head=IntegerPattern(value=1), tail=ElistPattern()), tail=ElistPattern()),
            tail=ListPattern(
                head=ListPattern(
                    head=ListPattern(head=FloatPattern(value=1.0), tail=ElistPattern()), tail=ElistPattern()
                ),
                tail=ElistPattern(),
            ),
        ),
        ListType(type=ListType(type=ListType(type=NumberType()))),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=ListType(type=ListType(type=NumberType()))),
    )

    assert_pattern_match_okk(
        ListPattern(
            head=ListPattern(head=ListPattern(head=IntegerPattern(value=1), tail=ElistPattern()), tail=ElistPattern()),
            tail=ListPattern(
                head=ListPattern(
                    head=ListPattern(head=FloatPattern(value=1.0), tail=ElistPattern()), tail=ElistPattern()
                ),
                tail=ListPattern(
                    head=ListPattern(
                        head=ListPattern(
                            head=IntegerPattern(value=1),
                            tail=ListPattern(head=FloatPattern(value=1.0), tail=ElistPattern()),
                        ),
                        tail=ElistPattern(),
                    ),
                    tail=ElistPattern(),
                ),
            ),
        ),
        ListType(type=ListType(type=ListType(type=NumberType()))),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=ListType(type=ListType(type=NumberType()))),
    )

    assert_pattern_match_okk(
        ListPattern(
            head=TuplePattern(items=[IntegerPattern(value=1), IntegerPattern(value=2)]),
            tail=ListPattern(
                head=TuplePattern(items=[IntegerPattern(value=1), FloatPattern(value=2.0)]), tail=ElistPattern()
            ),
        ),
        ListType(type=TupleType(types=[IntegerType(), NumberType()])),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=TupleType(types=[IntegerType(), NumberType()])),
    )

    assert_pattern_match_okk(
        ListPattern(
            head=TuplePattern(items=[IntegerPattern(value=1), IntegerPattern(value=2)]),
            tail=ListPattern(
                head=TuplePattern(items=[IntegerPattern(value=1), FloatPattern(value=2.0)]), tail=ElistPattern()
            ),
        ),
        ListType(type=TupleType(types=[NumberType(), NumberType()])),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=TupleType(types=[IntegerType(), NumberType()])),
    )

    assert_pattern_match_okk(
        ListPattern(
            head=TuplePattern(items=[IntegerPattern(value=1), IntegerPattern(value=2)]),
            tail=ListPattern(
                head=TuplePattern(items=[IntegerPattern(value=1), FloatPattern(value=2.0)]),
                tail=ListPattern(
                    head=TuplePattern(items=[FloatPattern(value=3.0), IntegerPattern(value=1)]), tail=ElistPattern()
                ),
            ),
        ),
        ListType(type=TupleType(types=[NumberType(), NumberType()])),
        hijacked_pattern_env={},
        env={},
        expected_type=ListType(type=TupleType(types=[NumberType(), NumberType()])),
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x")]),
        TupleType(types=[MapType(map_type={MapKey(value=1): TupleType(types=[])})]),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(types=[MapType(map_type={MapKey(value=1): TupleType(types=[])})]),
        expected_pattern_env={"x": MapType(map_type={MapKey(value=1): TupleType(types=[])})},
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="x")]),
        TupleType(
            types=[
                MapType(map_type={MapKey(value=1): TupleType(types=[])}),
                MapType(map_type={MapKey(value=2): TupleType(types=[])}),
            ]
        ),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(
            types=[
                MapType(map_type={MapKey(value=1): TupleType(types=[]), MapKey(value=2): TupleType(types=[])}),
                MapType(map_type={MapKey(value=1): TupleType(types=[]), MapKey(value=2): TupleType(types=[])}),
            ]
        ),
        expected_pattern_env={
            "x": MapType(map_type={MapKey(value=1): TupleType(types=[]), MapKey(value=2): TupleType(types=[])})
        },
    )

    assert_pattern_match_okk(
        TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="x"), IdentPattern(identifier="x")]),
        TupleType(
            types=[
                MapType(map_type={MapKey(value=1): TupleType(types=[])}),
                MapType(map_type={MapKey(value=2): TupleType(types=[])}),
                MapType(map_type={MapKey(value=3): TupleType(types=[])}),
            ]
        ),
        hijacked_pattern_env={},
        env={},
        expected_type=TupleType(
            types=[
                MapType(
                    map_type={
                        MapKey(value=1): TupleType(types=[]),
                        MapKey(value=2): TupleType(types=[]),
                        MapKey(value=3): TupleType(types=[]),
                    }
                ),
                MapType(
                    map_type={
                        MapKey(value=1): TupleType(types=[]),
                        MapKey(value=2): TupleType(types=[]),
                        MapKey(value=3): TupleType(types=[]),
                    }
                ),
                MapType(
                    map_type={
                        MapKey(value=1): TupleType(types=[]),
                        MapKey(value=2): TupleType(types=[]),
                        MapKey(value=3): TupleType(types=[]),
                    }
                ),
            ]
        ),
        expected_pattern_env={
            "x": MapType(
                map_type={
                    MapKey(value=1): TupleType(types=[]),
                    MapKey(value=2): TupleType(types=[]),
                    MapKey(value=3): TupleType(types=[]),
                }
            )
        },
    )

    assert_pattern_match_okk(
        ListPattern(head=IdentPattern(identifier="x"), tail=ElistPattern()),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        env={},
        expected_type=ListType(type=AnyType()),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_okk(
        TuplePattern(
            items=[
                ListPattern(head=IdentPattern(identifier="x"), tail=ElistPattern()),
                TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="x")]),
            ]
        ),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        env={},
        expected_type=TupleType(types=[ListType(type=AnyType()), TupleType(types=[AnyType(), AnyType()])]),
        expected_pattern_env={"x": AnyType()},
    )

    assert_pattern_match_okk(
        MapPattern(
            map=OrderedDict(
                [
                    (
                        MapKey(value=1),
                        TuplePattern(
                            items=[
                                ListPattern(head=IdentPattern(identifier="x"), tail=ElistPattern()),
                                TuplePattern(items=[IdentPattern(identifier="x"), IdentPattern(identifier="x")]),
                            ]
                        ),
                    ),
                    (MapKey(value=2), IdentPattern(identifier="x")),
                ]
            )
        ),
        AnyType(),
        hijacked_pattern_env={"x": NumberType()},
        env={},
        expected_type=MapType(
            map_type={
                MapKey(value=1): TupleType(types=[ListType(type=AnyType()), TupleType(types=[AnyType(), AnyType()])]),
                MapKey(value=2): AnyType(),
            }
        ),
        expected_pattern_env={"x": AnyType()},
    )


def test_tp_errors():
    assert_pattern_match_errorr(
        ListPattern(
            head=TuplePattern(
                items=[
                    ListPattern(
                        head=MapPattern(map=OrderedDict([(MapKey(value=2), TuplePattern(items=[]))])),
                        tail=ListPattern(
                            head=MapPattern(map=OrderedDict([(MapKey(value=2), TuplePattern(items=[]))])),
                            tail=ListPattern(
                                head=MapPattern(map=OrderedDict([(MapKey(value=2), ElistPattern())])),
                                tail=ElistPattern(),
                            ),
                        ),
                    )
                ]
            ),
            tail=ElistPattern(),
        ),
        ListType(type=TupleType(types=[ListType(type=MapType(map_type={MapKey(value=2): TupleType(types=[])}))])),
        hijacked_pattern_env={},
        env={},
        expected_context=(
            (pattern.ListPatternContext, {"head": True}),
            (
                (pattern.TuplePatternContext, {"n": 1}),
                (
                    (pattern.ListPatternContext, {"head": False}),
                    (
                        (pattern.ListPatternContext, {"head": False}),
                        (
                            (pattern.ListPatternContext, {"head": True}),
                            (
                                (pattern.MapPatternContext, {"key": MapKey(2)}),
                                pattern.PatternErrorEnum.incompatible_type_for_elist,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
