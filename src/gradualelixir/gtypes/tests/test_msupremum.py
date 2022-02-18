import pytest

from .. import definitions, generators, utils
from ..definitions import (
    AnyType,
    FunctionType,
    ListType,
    MapType,
    NoneType,
    TermType,
    TupleType,
    is_static_type,
)

TEST_ITERATIONS = 1000


def test_static_types():
    types_generator = generators.generate_types(base="static")(weights=[50, 50, 0])
    for function_name, mfunction_name in [
        ("supremum", "msupremum_plus"),
        ("infimum", "msupremum_minus"),
        ("supremum", "minfimum_minus"),
        ("infimum", "minfimum_plus"),
    ]:
        function = getattr(definitions, function_name)
        mfunction = getattr(definitions, mfunction_name)
        for _ in range(TEST_ITERATIONS):
            tau, sigma = next(types_generator), next(types_generator)
            try:
                assert function(tau, sigma) == mfunction(tau, sigma)
            except AssertionError as e:
                print(tau)
                print(sigma)
                print(function(tau, sigma))
                print(mfunction(tau, sigma))
                raise e


@pytest.mark.parametrize(
    "function_name, tau, role",
    (
        ("msupremum_minus", "none", "top"),
        ("msupremum_minus", "any", "bottom"),
        ("msupremum_plus", "term", "top"),
        ("msupremum_plus", "any", "bottom"),
        ("minfimum_plus", "any", "top"),
        ("minfimum_plus", "term", "bottom"),
        ("minfimum_minus", "any", "top"),
        ("minfimum_minus", "none", "bottom"),
    ),
)
def test_term_and_none(function_name, tau, role):
    tau = utils.parse_type(tau)
    function = getattr(definitions, function_name)
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(TEST_ITERATIONS):
        sigma = next(types_generator)
        assert function(tau, sigma) == (tau if role == "top" else sigma)


@pytest.mark.parametrize(
    "function_name",
    ("msupremum_plus", "msupremum_plus", "minfimum_plus", "minfimum_minus"),
)
def test_tuples_same_length(function_name):
    function = getattr(definitions, function_name)
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(TEST_ITERATIONS):
        tau1, tau2 = next(types_generator), next(types_generator)
        sigma1, sigma2 = next(types_generator), next(types_generator)
        mu = function(TupleType([tau1, tau2]), TupleType([sigma1, sigma2]))
        assert mu == TupleType([function(tau1, sigma1), function(tau2, sigma2)])


@pytest.mark.parametrize(
    "function_name, expected_result_if_both_static, expected_result_if_not_both_static",
    (
        ("msupremum_plus", "term", "term"),
        ("msupremum_minus", "none", "none"),
        ("minfimum_plus", "none", "any"),
        ("minfimum_minus", "term", "any"),
    ),
)
def test_tuples_different_lengths(
    function_name, expected_result_if_both_static, expected_result_if_not_both_static
):
    function = getattr(definitions, function_name)
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(TEST_ITERATIONS):
        taus = next(types_generator), next(types_generator)
        sigmas = next(types_generator), next(types_generator), next(types_generator)
        mu = function(TupleType(list(taus)), TupleType(list(sigmas)))
        if all([is_static_type(nu) for nu in list(taus) + list(sigmas)]):
            assert mu == utils.parse_type(expected_result_if_both_static)
        else:
            assert mu == utils.parse_type(expected_result_if_not_both_static)


@pytest.mark.parametrize(
    "function_name",
    ("msupremum_plus", "msupremum_plus", "minfimum_plus", "minfimum_minus"),
)
def test_list(function_name):
    function = getattr(definitions, function_name)
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(TEST_ITERATIONS):
        tau, sigma = next(types_generator), next(types_generator)
        mu = function(ListType(tau), ListType(sigma))
        assert mu == ListType(function(tau, sigma))


@pytest.mark.parametrize(
    "function_name",
    ("msupremum_plus", "msupremum_plus", "minfimum_plus", "minfimum_minus"),
)
def test_functions_same_length(function_name):
    dual_function_name = {
        "msupremum_plus": "msupremum_minus",
        "msupremum_minus": "msupremum_plus",
        "minfimum_plus": "minfimum_minus",
        "minfimum_minus": "minfimum_plus",
    }[function_name]
    function = getattr(definitions, function_name)
    dual_function = getattr(definitions, dual_function_name)
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(TEST_ITERATIONS):
        tau1, tau2, tau3 = (
            next(types_generator),
            next(types_generator),
            next(types_generator),
        )
        sigma1, sigma2, sigma3 = (
            next(types_generator),
            next(types_generator),
            next(types_generator),
        )
        mu = function(
            FunctionType([tau1, tau2], tau3), FunctionType([sigma1, sigma2], sigma3)
        )
        assert mu == FunctionType(
            [dual_function(tau1, sigma1), dual_function(tau2, sigma2)],
            function(tau3, sigma3),
        )


@pytest.mark.parametrize(
    "function_names, tau_keys, sigma_keys, mu_keys",
    (
        (["minfimum_plus", "msupremum_minus"], [], [], []),
        (["minfimum_plus", "msupremum_minus"], [1, 2], [], [1, 2]),
        (["minfimum_plus", "msupremum_minus"], [1], [2], [1, 2]),
        (["minfimum_plus", "msupremum_minus"], [1, 2], [2, 3], [1, 2, 3]),
        (["minfimum_minus", "msupremum_plus"], [], [], []),
        (["minfimum_minus", "msupremum_plus"], [1, 2], [], []),
        (["minfimum_minus", "msupremum_plus"], [1], [2], []),
        (["minfimum_minus", "msupremum_plus"], [1, 2], [2, 3], [2]),
        (["minfimum_minus", "msupremum_plus"], [1, 2], [1, 2, 3], [1, 2]),
    ),
)
def test_map(function_names, tau_keys, sigma_keys, mu_keys):
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(1000):
        tau_map = dict([(k, next(types_generator)) for k in tau_keys])
        sigma_map = dict([(k, next(types_generator)) for k in sigma_keys])
        for name in function_names:
            function = getattr(definitions, name)
            mu = function(MapType(tau_map), MapType(sigma_map))
            assert isinstance(mu, MapType)
            assert mu_keys == list(mu.map_type.keys())
            for k in mu_keys:
                if k in tau_map and k in sigma_map:
                    assert mu.map_type[k] == function(tau_map[k], sigma_map[k])
                elif name == "msupremum_plus":
                    assert k not in mu.map_type
                elif k in tau_map:
                    assert mu.map_type[k] == tau_map[k]
                else:
                    assert mu.map_type[k] == sigma_map[k]


@pytest.mark.parametrize(
    "cls1, meta1, cls2, meta2",
    (
        (TupleType, 2, TupleType, 3),
        (FunctionType, 2, FunctionType, 3),
        (ListType, 1, TupleType, 2),
        (ListType, 1, MapType, [1, 2]),
        (ListType, 1, FunctionType, 2),
        (TupleType, 1, MapType, [1, 2]),
        (TupleType, 1, FunctionType, 2),
        (MapType, [1, 2], FunctionType, 2),
    ),
)
def test_type_constructors_different_constructors(cls1, meta1, cls2, meta2):
    types_generator = generators.generate_types(base="gradual")()
    args1 = cls1, meta1
    if cls1 == MapType:
        args1 = cls1, *meta1
    args2 = cls2, meta2
    if cls2 == MapType:
        args2 = cls2, *meta2
    for _ in range(TEST_ITERATIONS):
        taus = next(types_generator), next(types_generator), next(types_generator)
        sigmas = next(types_generator), next(types_generator), next(types_generator)
        tau = generators.type_builder(*args1, *taus)
        sigma = generators.type_builder(*args2, *sigmas)
        assert isinstance(definitions.msupremum_plus(tau, sigma), TermType)
        assert isinstance(definitions.msupremum_minus(tau, sigma), NoneType)
        if is_static_type(tau) and is_static_type(sigma):
            assert isinstance(definitions.supremum(tau, sigma), TermType)
            assert isinstance(definitions.infimum(tau, sigma), NoneType)
        else:
            assert isinstance(definitions.supremum(tau, sigma), AnyType)
            assert isinstance(definitions.infimum(tau, sigma), AnyType)
