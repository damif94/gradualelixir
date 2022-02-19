import pytest

from .. import generators, utils
from ..definitions import (FunctionType, ListType, NoneType, TermType,
                           TupleType, is_static_type, is_subtype)

TEST_ITERATIONS = 1000


@pytest.mark.parametrize(
    "tau, sigma, expected_result, expected_flipped_result",
    (
        ("integer", "integer", True, True),
        ("integer", "term", True, False),
        ("integer", "none", False, True),
        ("integer", "float", False, False),
        ("integer", "number", True, False),
        ("float", "float", True, True),
        ("float", "term", True, False),
        ("integer", "none", False, True),
        ("float", "number", True, False),
        ("term", "term", True, True),
        ("none", "term", True, False),
        ("none", "none", True, True),
    ),
)
def test_base_types(tau, sigma, expected_result, expected_flipped_result):
    tau, sigma = utils.parse_type(tau), utils.parse_type(sigma)
    assert is_subtype(tau, sigma) == expected_result
    assert is_subtype(sigma, tau) == expected_flipped_result


def test_reflexivity():
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(TEST_ITERATIONS):
        tau = next(types_generator)
        assert is_subtype(tau, tau)


def test_term_and_none():
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(TEST_ITERATIONS):
        tau = next(types_generator)
        if is_static_type(tau):
            assert is_subtype(tau, TermType())
            assert is_subtype(NoneType(), tau)
        else:
            assert not is_subtype(tau, TermType())
            assert not is_subtype(NoneType(), tau)


def test_tuples_same_length():
    types_generator = generators.generate_types(base="gradual")()
    i = 0
    while i < TEST_ITERATIONS / 10:
        tau1, tau2 = next(types_generator), next(types_generator)
        sigma1, sigma2 = next(types_generator), next(types_generator)
        if is_subtype(tau1, sigma1) and is_subtype(tau2, sigma2):
            assert is_subtype(TupleType([tau1, tau2]), TupleType([sigma1, sigma2]))
            i += 1
    while i < TEST_ITERATIONS:
        tau1, tau2 = next(types_generator), next(types_generator)
        sigma1, sigma2 = next(types_generator), next(types_generator)
        if not (is_subtype(tau1, sigma1) and is_subtype(tau2, sigma2)):
            assert not is_subtype(TupleType([tau1, tau2]), TupleType([sigma1, sigma2]))
            i += 1


def test_tuples_different_lengths():
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(TEST_ITERATIONS):
        taus = [next(types_generator), next(types_generator)]
        sigmas = [next(types_generator), next(types_generator), next(types_generator)]
        assert not is_subtype(TupleType(taus), TupleType(sigmas))


def test_list():
    types_generator = generators.generate_types(base="gradual")()
    i = 0
    while i < TEST_ITERATIONS / 10:
        tau, sigma = next(types_generator), next(types_generator)
        if is_subtype(tau, sigma):
            assert is_subtype(ListType(tau), ListType(sigma))
            i += 1
    i = 0
    while i < TEST_ITERATIONS:
        tau, sigma = next(types_generator), next(types_generator)
        if is_subtype(tau, sigma):
            assert is_subtype(ListType(tau), ListType(sigma))
            i += 1


def test_functions_same_length():
    types_generator = generators.generate_types(base="gradual")()
    i = 0
    while i < TEST_ITERATIONS / 10:
        tau1, tau2 = next(types_generator), next(types_generator)
        sigma1, sigma2 = next(types_generator), next(types_generator)
        if is_subtype(sigma1, tau1) and is_subtype(tau2, sigma2):
            assert is_subtype(
                FunctionType([tau1], tau2), FunctionType([sigma1], sigma2)
            )
            i += 1
    i = 0
    while i < TEST_ITERATIONS:
        tau1, tau2 = next(types_generator), next(types_generator)
        sigma1, sigma2 = next(types_generator), next(types_generator)
        if not (is_subtype(sigma1, tau1) and is_subtype(tau2, sigma2)):
            assert not is_subtype(
                FunctionType([tau1], tau2), FunctionType([sigma1], sigma2)
            )
            i += 1
