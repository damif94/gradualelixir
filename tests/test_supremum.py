import pytest
import generators
import gtypes
from gtypes import *
import utils

TEST_ITERATIONS = 1


@pytest.mark.parametrize(
    'function_name, tau, sigma, mu_or_error',
    (
        ('supremum', 'integer', 'float', 'number'),
        ('infimum', 'integer', 'float', 'none'),
        ('supremum', 'integer', 'number', 'number'),
        ('infimum', 'integer', 'number', 'integer'),
        ('supremum', 'float', 'number', 'number'),
        ('infimum', 'float', 'number', 'float'),
    )
)
def test_base_types(function_name, tau, sigma, mu_or_error):
    function = getattr(gtypes, function_name)
    tau, sigma = utils.parse_type(tau), utils.parse_type(sigma)
    if isinstance(mu_or_error, TypeExceptionEnum):
        with pytest.raises(TypeException) as ex_info:
            function(tau, sigma)
        assert ex_info.value.reason is mu_or_error
    else:
        mu = utils.parse_type(mu_or_error)
        assert function(tau, sigma) == mu


@pytest.mark.parametrize(
    'function_name, tau, role',
    (
        ('infimum', 'none', 'top'),
        ('infimum', 'term', 'bottom'),
        ('supremum', 'term', 'top'),
        ('supremum', 'none', 'bottom'),
    )
)
def test_term_and_none(function_name, tau, role):
    tau = utils.parse_type(tau)
    function = getattr(gtypes, function_name)
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(TEST_ITERATIONS):
        sigma = next(types_generator)
        try:
            assert function(tau, sigma) == (tau if role == 'top' else sigma)
        except TypeException as e:
            assert e.reason is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else


@pytest.mark.parametrize(
    'function_name', ('infimum', 'supremum')
)
def test_tuples_same_length(function_name):
    function = getattr(gtypes, function_name)
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(TEST_ITERATIONS):
        tau1, tau2 = next(types_generator), next(types_generator)
        sigma1, sigma2 = next(types_generator), next(types_generator)
        try:
            mu = function(TupleType([tau1, tau2]), TupleType([sigma1, sigma2]))
        except TypeException as e:
            assert e.reason is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            with pytest.raises(TypeException) as ex_info:
                TupleType([function(tau1, sigma1), function(tau2, sigma2)])
            assert ex_info.value.reason is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            assert any([not is_static_type(x) for x in [tau1, sigma1, tau2, sigma2]])
        else:
            assert mu == TupleType([function(tau1, sigma1), function(tau2, sigma2)])


@pytest.mark.parametrize(
    'function_name', ('infimum', 'supremum')
)
def test_tuples_different_lengths(function_name):
    function = getattr(gtypes, function_name)
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(TEST_ITERATIONS):
        tau1, tau2 = next(types_generator), next(types_generator)
        sigma1, sigma2, sigma3 = next(types_generator), next(types_generator), next(types_generator)
        try:
            mu = function(TupleType([tau1, tau2]), TupleType([sigma1, sigma2, sigma3]))
        except TypeException as e:
            assert e.reason is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            assert any([not is_static_type(x) for x in [tau1, sigma1, tau2, sigma2, sigma3]])
        else:
            assert isinstance(mu, TermType if function_name == 'supremum' else NoneType)


@pytest.mark.parametrize(
    'function_name', ('infimum', 'supremum')
)
def test_list(function_name):
    function = getattr(gtypes, function_name)
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(TEST_ITERATIONS):
        tau, sigma = next(types_generator), next(types_generator)
        try:
            mu = function(ListType(tau), ListType(sigma))
        except TypeException as e:
            assert e.reason is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            assert any([not is_static_type(x) for x in [tau, sigma]])
        else:
            assert mu == ListType(function(tau, sigma))


@pytest.mark.parametrize(
    'function_name', ('infimum', 'supremum')
)
def test_functions_same_length(function_name):
    function = getattr(gtypes, function_name)
    dual_function = getattr(gtypes, 'supremum' if function_name == 'infimum' else 'infimum')
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(TEST_ITERATIONS):
        tau1, tau2, tau3 = next(types_generator), next(types_generator), next(types_generator)
        sigma1, sigma2, sigma3 = next(types_generator), next(types_generator), next(types_generator)
        try:
            mu = function(FunctionType([tau1, tau2], tau3), FunctionType([sigma1, sigma2], sigma3))
        except TypeException as e:
            assert e.reason is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            with pytest.raises(TypeException) as ex_info:
                FunctionType([dual_function(tau1, sigma1), dual_function(tau2, sigma2)], function(tau3, sigma3))
            assert ex_info.value.reason is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            assert any([not is_static_type(x) for x in [tau1, sigma1, tau2, sigma2, tau3, sigma3]])
        else:
            assert mu == FunctionType(
                [dual_function(tau1, sigma1), dual_function(tau2, sigma2)], function(tau3, sigma3)
            )


@pytest.mark.parametrize(
    'tau_keys, sigma_keys, mu_keys',
    (
            ([], [], []),
            ([1, 2], [], [1, 2]),
            ([1], [2], [1, 2]),
            ([1, 2], [2, 3], [1, 2, 3]),
    )
)
def test_map(tau_keys, sigma_keys, mu_keys):
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(1000):
        tau_map = dict([(k, next(types_generator)) for k in tau_keys])
        sigma_map = dict([(k, next(types_generator)) for k in sigma_keys])
        try:
            mu = infimum(MapType(tau_map), MapType(sigma_map))
        except TypeException as e:
            assert e.reason is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            assert any([not is_static_type(x) for x in list(tau_map.values()) + list(sigma_map.values())])
        else:
            assert isinstance(mu, MapType)
            assert mu_keys == list(mu.map_type.keys())
            for k in mu_keys:
                if k in tau_map and k in sigma_map:
                    assert mu.map_type[k] == infimum(tau_map[k], sigma_map[k])
                elif k in tau_map:
                    assert mu.map_type[k] == tau_map[k]
                else:
                    assert mu.map_type[k] == sigma_map[k]


