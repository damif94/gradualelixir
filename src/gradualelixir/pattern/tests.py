from collections import OrderedDict

from .definitions import (
    ListPatternContext,
    MapPatternContext,
    PatternErrorEnum,
    TuplePatternContext,
)
from . import definitions, utils
from ..gtypes import utils as type_utils

integer = "integer"
float = "float"
number = "number"
none = "none"
any = "any"
x = "x"
y = "y"
z = "z"
px = "^x"
py = "^y"
pz = "^z"


def pattern_match(pattern, tau, gamma_env, sigma_env):
    gamma_env = {k: type_utils.parse_type(v) for k, v in gamma_env.items()}
    sigma_env = {k: type_utils.parse_type(v) for k, v in sigma_env.items()}
    result = definitions.pattern_match(
        utils.parse_pattern(pattern), type_utils.parse_type(tau), gamma_env, sigma_env
    )
    if isinstance(result, definitions.PatternError):
        return result
    return (
        type_utils.unparse_type(result[0]),
        {k: type_utils.unparse_type(v) for k, v in result[1].items()},
    )


def assert_pattern_match_ok(pattern_input, pattern_output):
    assert pattern_match(*pattern_input) == pattern_output


def assert_pattern_match_error(pattern_input, context_path=None):
    pattern, tau, gamma_env, sigma_env = pattern_input
    return_value = pattern_match(pattern, tau, gamma_env, sigma_env)
    if len(context_path) == 1:
        assert isinstance(return_value, definitions.BasePatternError)
        assert return_value.kind is context_path[-1]
    else:
        assert isinstance(return_value, definitions.NestedPatternError)
        current_value = return_value
        for klass, arg in context_path[:-1]:
            current_context = current_value.context
            assert isinstance(current_context, definitions.PatternContext)
            if klass == ListPatternContext:
                assert isinstance(current_context, ListPatternContext)
                assert current_context.head == arg
            elif klass == TuplePatternContext:
                assert isinstance(current_context, TuplePatternContext)
                assert current_context.n == arg
            else:
                assert klass == MapPatternContext
                assert isinstance(current_context, MapPatternContext)
                assert current_context.key == arg
            current_value = current_value.error
        assert isinstance(current_value, definitions.BasePatternError)
        assert current_value.kind is context_path[-1]


def sett(*args):
    args = list(args)
    args.sort()
    aux = OrderedDict()
    for k in args:
        aux[k] = ()
    return aux


def test_tp_pin():
    assert_pattern_match_ok((px, integer, {}, {x: integer}), (integer, {}))
    assert_pattern_match_ok((px, integer, {}, {x: number}), (integer, {}))
    assert_pattern_match_ok((px, sett(1), {}, {x: sett(2)}), (sett(1, 2), {}))
    assert_pattern_match_error(
        (px, integer, {}, {x: float}),
        context_path=[
            PatternErrorEnum.incompatible_type_for_pinned_variable,
        ],
    )
    assert_pattern_match_error(
        (px, integer, {}, {y: integer}),
        context_path=[
            PatternErrorEnum.pinned_identifier_not_found_in_environment,
        ],
    )
    assert_pattern_match_error(
        (px, integer, {x: integer}, {y: integer}),
        context_path=[
            PatternErrorEnum.pinned_identifier_not_found_in_environment,
        ],
    )
    assert_pattern_match_error(
        (px, integer, {}, {x: (integer, "->", integer)}),
        context_path=[
            PatternErrorEnum.arrow_types_into_pinned_identifier,
        ],
    )


def test_tp_wild():
    assert_pattern_match_ok(("_", integer, {}, {}), (integer, {}))
    assert_pattern_match_ok(
        ("_", integer, {x: float}, {y: number}), (integer, {x: float})
    )
    assert_pattern_match_ok(
        ("_", [float], {x: float}, {y: number}), ([float], {x: float})
    )


def test_tp_var():
    assert_pattern_match_ok((x, integer, {}, {}), (integer, {x: integer}))
    assert_pattern_match_ok((x, integer, {}, {x: float}), (integer, {x: integer}))
    assert_pattern_match_ok(
        (x, integer, {y: float}, {}), (integer, {x: integer, y: float})
    )
    assert_pattern_match_ok((x, [float], {}, {}), ([float], {x: [float]}))


def test_tp_varn():
    assert_pattern_match_ok((x, integer, {x: integer}, {}), (integer, {x: integer}))
    assert_pattern_match_ok(
        (x, sett(1), {x: sett(2)}, {}), (sett(1, 2), {x: sett(1, 2)})
    )
    assert_pattern_match_ok(
        (x, sett(1), {x: sett(2)}, {x: sett(3)}), (sett(1, 2), {x: sett(1, 2)})
    )
    assert_pattern_match_ok(
        (x, sett(1), {x: sett(2), y: sett(3)}, {}),
        (sett(1, 2), {x: sett(1, 2), y: sett(3)}),
    )
    assert_pattern_match_ok(
        (x, sett(1), {x: sett(2)}, {y: sett(3)}), (sett(1, 2), {x: sett(1, 2)})
    )
    assert_pattern_match_error(
        (x, integer, {x: float}, {}),
        context_path=[PatternErrorEnum.incompatible_type_for_variable],
    )
    assert_pattern_match_error(
        (x, integer, {x: (integer, "->", integer)}, {}),
        context_path=[PatternErrorEnum.arrow_types_into_nonlinear_identifier],
    )
    assert_pattern_match_error(
        (x, (integer, "->", integer), {x: sett(2)}, {}),
        context_path=[PatternErrorEnum.arrow_types_into_nonlinear_identifier],
    )


def test_tp_elist():
    assert_pattern_match_ok(([], [none], {}, {}), ([none], {}))
    assert_pattern_match_ok(([], [number], {}, {}), ([none], {}))
    assert_pattern_match_error(
        ([], integer, {}, {}),
        context_path=[PatternErrorEnum.incompatible_constructors_error],
    )
    assert_pattern_match_error(
        ([], (integer,), {}, {}),
        context_path=[PatternErrorEnum.incompatible_constructors_error],
    )


def test_tp_list():
    assert_pattern_match_ok(([1], [integer], {}, {}), ([integer], {}))
    assert_pattern_match_ok(([x], [integer], {}, {}), ([integer], {x: integer}))
    assert_pattern_match_ok(([1, 1.0], [number], {}, {}), ([number], {}))
    assert_pattern_match_ok(([x, x], [integer], {}, {}), ([integer], {x: integer}))
    assert_pattern_match_ok(
        ([x, x], [sett(1)], {x: sett(2)}, {}), ([sett(1, 2)], {x: sett(1, 2)})
    )
    assert_pattern_match_ok(
        ([x, y], [sett(1)], {y: sett(2)}, {}), ([sett(1)], {x: sett(1), y: sett(1, 2)})
    )
    assert_pattern_match_ok(
        ([x, y], [sett(1)], {x: sett(2)}, {}), ([sett(1)], {x: sett(1, 2), y: sett(1)})
    )
    assert_pattern_match_ok(
        ([x, x, y], [sett(1)], {y: sett(2)}, {}),
        ([sett(1)], {x: sett(1), y: sett(1, 2)}),
    )
    assert_pattern_match_ok(
        ([x, x, y], [sett(1)], {x: sett(2)}, {}),
        ([sett(1)], {x: sett(1, 2), y: sett(1)}),
    )
    # assert_pattern_match_error(([x], [], {}, {}), ([integer], {x: integer}))
    assert_pattern_match_error(
        ([1], integer, {}, {}),
        context_path=[PatternErrorEnum.incompatible_constructors_error],
    )


def test_tp_tuple():
    assert_pattern_match_ok(((), (), {}, {}), ((), {}))
    assert_pattern_match_ok(((x,), (integer,), {}, {}), ((integer,), {x: integer}))
    assert_pattern_match_ok(
        ((x,), (sett(1),), {x: sett(2)}, {}),
        ((sett(1, 2),), {x: sett(1, 2)}),
    )
    assert_pattern_match_ok(
        ((x, y), (integer, float), {}, {}),
        ((integer, float), {x: integer, y: float}),
    )
    assert_pattern_match_ok(
        ((x, x), (integer, integer), {}, {}), ((integer, integer), {x: integer})
    )
    assert_pattern_match_ok(
        ((x, x), (sett(1), sett(2)), {}, {}),
        ((sett(1, 2), sett(1, 2)), {x: sett(1, 2)}),
    )
    assert_pattern_match_ok(
        ((x, y, x), (sett(1), sett(2), sett(3)), {}, {}),
        ((sett(1, 3), sett(2), sett(1, 3)), {x: sett(1, 3), y: sett(2)}),
    )
    assert_pattern_match_ok(
        ((px, y, x), (sett(1), sett(2), sett(3)), {}, {x: sett(4)}),
        ((sett(1, 4), sett(2), sett(3)), {x: sett(3), y: sett(2)}),
    )
    assert_pattern_match_error(
        ((x,), (float, integer), {}, {}),
        context_path=[
            PatternErrorEnum.incompatible_tuples_error,
        ],
    )
    assert_pattern_match_error(
        ((1, x), (float, integer), {}, {}),
        context_path=[
            (TuplePatternContext, 1),
            PatternErrorEnum.incompatible_type_for_literal,
        ],
    )
    assert_pattern_match_error(
        (("_", "_", ((1, x), x)), (float, float, ((float, integer), float)), {}, {}),
        context_path=[
            (TuplePatternContext, 3),
            (TuplePatternContext, 1),
            (TuplePatternContext, 1),
            PatternErrorEnum.incompatible_type_for_literal,
        ],
    )
    assert_pattern_match_error(
        ((x,), [float], {}, {}),
        context_path=[
            PatternErrorEnum.incompatible_constructors_error,
        ],
    )


def test_tp_map():
    assert_pattern_match_ok(({}, {}, {}, {}), ({}, {}))
    assert_pattern_match_ok(
        ({1: x}, {1: integer}, {}, {}), ({1: integer}, {x: integer})
    )
    assert_pattern_match_ok(
        ({1: x, 2: 2.0}, {1: integer, 2: float}, {}, {}),
        ({1: integer, 2: float}, {x: integer}),
    )
    assert_pattern_match_ok(
        ({2: 2.0, 1: x}, {1: integer, 2: float}, {}, {}),
        ({1: integer, 2: float}, {x: integer}),
    )
    assert_pattern_match_ok(
        ({2: 2.0, 1: x}, {2: float, 1: integer}, {}, {}),
        ({1: integer, 2: float}, {x: integer}),
    )
    assert_pattern_match_ok(
        ({1: x, 2: 2.0}, {1: integer, 2: float}, {}, {}),
        ({2: float, 1: integer}, {x: integer}),
    )
    assert_pattern_match_ok(
        ({1: x}, {1: sett(1)}, {x: sett(2)}, {}),
        ({1: sett(1, 2)}, {x: sett(1, 2)}),
    )
    assert_pattern_match_ok(
        ({1: x, 2: y}, {1: integer, 2: float}, {}, {}),
        ({1: integer, 2: float}, {x: integer, y: float}),
    )
    assert_pattern_match_ok(
        ({1: x, 2: x}, {1: integer, 2: integer}, {}, {}),
        ({1: integer, 2: integer}, {x: integer}),
    )
    assert_pattern_match_ok(
        ({1: x, 2: x}, {1: sett(1), 2: sett(2)}, {}, {}),
        ({1: sett(1, 2), 2: sett(1, 2)}, {x: sett(1, 2)}),
    )
    assert_pattern_match_ok(
        ({1: x, 2: y, 3: x}, {1: sett(1), 2: sett(2), 3: sett(3)}, {}, {}),
        ({1: sett(1, 3), 2: sett(2), 3: sett(1, 3)}, {x: sett(1, 3), y: sett(2)}),
    )
    assert_pattern_match_ok(
        ({1: px, 2: y, 3: x}, {1: sett(1), 2: sett(2), 3: sett(3)}, {}, {x: sett(4)}),
        ({1: sett(1, 4), 2: sett(2), 3: sett(3)}, {x: sett(3), y: sett(2)}),
    )
    assert_pattern_match_error(
        ({1: x}, {2: float, 3: integer}, {}, {}),
        context_path=[
            PatternErrorEnum.incompatible_maps_error,
        ],
    )
    assert_pattern_match_error(
        ({1: 1, 2: x}, {1: float, 2: integer}, {}, {}),
        context_path=[
            (MapPatternContext, 1),
            PatternErrorEnum.incompatible_type_for_literal,
        ],
    )
    assert_pattern_match_error(
        ({2: x, 1: 1}, {1: float, 2: integer}, {}, {}),
        context_path=[
            (MapPatternContext, 1),
            PatternErrorEnum.incompatible_type_for_literal,
        ],
    )
    assert_pattern_match_error(
        ({1: 1, 2: x}, {2: integer, 1: float}, {}, {}),
        context_path=[
            (MapPatternContext, 1),
            PatternErrorEnum.incompatible_type_for_literal,
        ],
    )
    assert_pattern_match_error(
        ({2: x, 1: 1}, {1: float, 2: integer}, {}, {}),
        context_path=[
            (MapPatternContext, 1),
            PatternErrorEnum.incompatible_type_for_literal,
        ],
    )
    assert_pattern_match_error(
        (
            {1: "_", 2: "_", 3: {1: {1: 1, 2: x}, 2: x}},
            {1: float, 2: float, 3: {1: {1: float, 2: integer}, 2: float}},
            {},
            {},
        ),
        context_path=[
            (MapPatternContext, 3),
            (MapPatternContext, 1),
            (MapPatternContext, 1),
            PatternErrorEnum.incompatible_type_for_literal,
        ],
    )
    assert_pattern_match_error(
        (
            {2: "_", 3: "_", 1: {1: {2: 1, 1: x}, 2: x}},
            {2: float, 3: float, 1: {1: {2: float, 1: integer}, 2: float}},
            {},
            {},
        ),
        context_path=[
            (MapPatternContext, 1),
            (MapPatternContext, 1),
            (MapPatternContext, 2),
            PatternErrorEnum.incompatible_type_for_literal,
        ],
    )
    assert_pattern_match_error(
        ({2: x}, [float], {}, {}),
        context_path=[
            PatternErrorEnum.incompatible_constructors_error,
        ],
    )


def test_tp_any():
    assert_pattern_match_ok((1, any, {}, {}), (integer, {}))

    assert_pattern_match_ok((x, any, {x: integer}, {}), (any, {x: any}))
    assert_pattern_match_ok((x, integer, {x: any}, {}), (any, {x: any}))

    assert_pattern_match_ok((px, any, {}, {x: integer}), (any, {}))
    assert_pattern_match_ok((px, integer, {}, {x: any}), (any, {}))

    assert_pattern_match_ok(([], any, {}, {}), ([none], {}))

    assert_pattern_match_ok(([x], any, {}, {}), ([any], {x: any}))
    assert_pattern_match_ok(([x], any, {x: integer}, {}), ([any], {x: any}))
    assert_pattern_match_ok(([x, y], any, {x: integer}, {}), ([any], {x: any, y: any}))
    assert_pattern_match_ok(
        ([x, y], any, {x: integer, y: integer}, {}), ([any], {x: any, y: any})
    )

    assert_pattern_match_ok(((), any, {}, {}), ((), ({})))
    assert_pattern_match_ok(((x,), any, {}, {}), ((any,), ({x: any})))
    assert_pattern_match_ok(((x, y), any, {}, {}), ((any, any), ({x: any, y: any})))
    assert_pattern_match_ok(((x, x), any, {}, {}), ((any, any), ({x: any})))

    assert_pattern_match_ok(
        ({1: x, 2: y}, any, {}, {}), ({1: any, 2: any}, {x: any, y: any})
    )


def test_tp_ok_progressions():

    assert_pattern_match_ok(
        ([px, x, y], [sett(1)], {x: sett(2)}, {x: sett(3)}),
        ([sett(1)], {x: sett(1, 2), y: sett(1)}),
    )
    assert_pattern_match_ok(
        ([px, x, y], [sett(1)], {x: sett(2, 3)}, {x: sett(2)}),
        ([sett(1)], {x: sett(1, 2, 3), y: sett(1)}),
    )
    assert_pattern_match_ok(
        ([px, x, y], [sett(1)], {x: sett(2, 3), y: sett(2)}, {x: sett(2)}),
        ([sett(1, 2)], {x: sett(1, 2, 3), y: sett(1, 2)}),
    )

    assert_pattern_match_ok(([[1], [1.0]], [[number]], {}, {}), ([[number]], {}))
    assert_pattern_match_ok(
        ([[[1]], [[1.0]]], [[[number]]], {}, {}), ([[[number]]], {})
    )
    assert_pattern_match_ok(
        ([[[1]], [[1.0]], [[1, 1.0]]], [[[number]]], {}, {}), ([[[number]]], {})
    )

    assert_pattern_match_ok(
        ([(1, 2), (1, 2.0)], [(integer, number)], {}, {}), ([(integer, number)], {})
    )
    assert_pattern_match_ok(
        ([(1, 2), (1, 2.0)], [(number, number)], {}, {}), ([(integer, number)], {})
    )
    assert_pattern_match_ok(
        ([(1, 2), (1, 2.0), (3.0, 1)], [(number, number)], {}, {}),
        ([(number, number)], {}),
    )

    assert_pattern_match_ok(((x,), (sett(1),), {}, {}), ((sett(1),), {x: sett(1)}))
    assert_pattern_match_ok(
        ((x, x), (sett(1), sett(2)), {}, {}),
        ((sett(1, 2), sett(1, 2)), {x: sett(1, 2)}),
    )
    assert_pattern_match_ok(
        ((x, x, x), (sett(1), sett(2), sett(3)), {}, {}),
        ((sett(1, 2, 3), sett(1, 2, 3), sett(1, 2, 3)), {x: sett(1, 2, 3)}),
    )

    assert_pattern_match_ok(([x], any, {x: integer}, {}), ([any], {x: any}))
    assert_pattern_match_ok(
        (([x], (x, x)), any, {x: integer}, {}), (([any], (any, any)), {x: any})
    )
    assert_pattern_match_ok(
        ({1: ([x], (x, x)), 2: x}, any, {x: integer}, {}),
        ({1: ([any], (any, any)), 2: any}, {x: any}),
    )


def test_tp_errors():
    assert_pattern_match_error(
        ([([{2: ()}, {2: ()}, {2: []}],)], [([{2: ()}],)], {}, {}),
        context_path=[
            (ListPatternContext, True),
            (TuplePatternContext, 1),
            (ListPatternContext, False),
            (ListPatternContext, False),
            (ListPatternContext, True),
            (MapPatternContext, 2),
            PatternErrorEnum.incompatible_constructors_error,
        ],
    )
