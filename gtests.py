import gtypes
from gtypes import *
import generators

gtypes.base_types += [gtypes.AnyType()]

base_types = ['integer', 'float', 'number', 'term', 'any']


def test_lattice_relations():
    subtypes_generator = generators.generate_subtypes(base='gradual')()
    for _ in range(1000):
        tau1, tau2 = next(subtypes_generator)
        sigma1, sigma2 = next(subtypes_generator)
        try:
            assert is_subtype(supremum(tau1, sigma1), supremum(tau2, sigma2))
            assert is_subtype(infimum(tau2, sigma2,), infimum(tau2, sigma2))
        except TypeException as e:
            assert e.reason in [
                TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility,
                TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            ]


def test_supremum_is_defined_or_blame_any_and_something_else():
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(2500):
        tau1, tau2 = next(types_generator), next(types_generator)
        try:
            supremum(tau1, tau2)
        except TypeException as e:
            assert e.reason == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else


def test_infimum_is_defined_or_blame_incompatibility_or_blame_any_and_something_else():
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(5000):
        tau1, tau2 = next(types_generator), next(types_generator)
        try:
            infimum(tau1, tau2)
        except TypeException as e:
            assert e.reason in [
                TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility,
                TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            ]


def test_supremum_is_diagonal_identity():
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(5000):
        tau = next(types_generator)
        assert tau == supremum(tau, tau)
        assert tau == infimum(tau, tau)


def test_supremum_is_commutative():
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(300):
        tau, sigma = next(types_generator), next(types_generator)
        for m in [True, False]:
            try:
                supremum(tau, sigma)
            except TypeException as e:
                assert e.reason == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
                assert not m
            else:
                assert supremum(tau, sigma) == supremum(sigma, tau)


def test_supremum_on_tuples():
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(300):
        tau1, sigma1 = next(types_generator), next(types_generator)
        tau2, sigma2 = next(types_generator), next(types_generator)
        for m in [True, False]:
            try:
                s1 = supremum(tau1, sigma1)
                s2 = supremum(tau2, sigma2)
                assert TupleType([s1, s2]) == supremum(TupleType([tau1, tau2]), TupleType([sigma1, sigma2]))
            except TypeException as e:
                assert e.reason == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
                assert not m


def test_supremum_on_functions():
    types_generator = generators.types_generator(base='gradual', force_recreate=True)(weights=[50, 50, 0])
    for _ in range(10000):
        tau1, sigma1 = next(types_generator), next(types_generator)
        tau2, sigma2 = next(types_generator), next(types_generator)
        tau3, sigma3 = next(types_generator), next(types_generator)
        try:
            s1 = infimum(tau1, sigma1)
            s2 = infimum(tau2, sigma2)
            print(str(tau1) + ' ' + str(sigma1) + ' ' + str(s1))
            print(str(tau2) + ' ' + str(sigma2) + ' ' + str(s2))
            print("-------------------")
        except TypeException as e:
            if e.reason == TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility:
                assert supremum(FunctionType([tau1, tau2], tau3), FunctionType([sigma1, sigma2], sigma3)) == TermType()
            else:
                assert e.reason == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
        else:
            try:
                s3 = supremum(tau3, sigma3)
            except TypeException as e:
                assert e.reason == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            else:
                assert FunctionType([s1, s2], s3) == supremum(FunctionType([tau1, tau2], tau3), FunctionType([sigma1, sigma2], sigma3))


def test_lazy_equate_identity_on_static_types():
    types_generator = generators.types_generator(base='static', force_recreate=True)(weights=[30, 30, 40])
    for _ in range(5000):
        tau, sigma = next(types_generator), next(types_generator)
        assert lazy_equate(tau, sigma, True) == (tau, sigma)
        assert lazy_equate(tau, sigma, False) == (tau, sigma)


def test_lazy_equate_materializes():
    types_generator = generators.types_generator(base='gradual', force_recreate=True)(weights=[40, 40, 20])
    for _ in range(5000):
        tau, sigma = next(types_generator), next(types_generator)

        tau1, sigma1 = lazy_equate(tau, sigma, True)
        assert is_materialization(tau, tau1)
        assert is_materialization(sigma, sigma1)
        assert is_subtype(tau1, supremum(tau1, sigma1))
        assert is_subtype(sigma1, supremum(tau1, sigma1))
        # print(f'({str(tau)}, {str(sigma)}) -> ({str(tau1), str(sigma1)})')

        tau2, sigma2 = lazy_equate(tau, sigma, False)
        assert is_materialization(tau2, tau)
        assert is_materialization(sigma2, sigma)
        assert is_subtype(tau2, supremum(tau2, sigma2))
        assert is_subtype(sigma2, supremum(tau2, sigma2))

        try:
            assert is_subtype(infimum(tau1, sigma1), tau1)
            assert is_subtype(infimum(tau1, sigma1), sigma1)

            assert is_subtype(infimum(tau2, sigma2), tau2)
            assert is_subtype(infimum(tau2, sigma2), sigma2)

        except TypeException as e:
            if not e.reason == TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility:
                raise e


def test_lazy_equate_materialization_invariant_lemma():
    materializations_generator = generators.generate_materializations(base='gradual')(weights=[40, 40, 20])
    types_generator = generators.types_generator(base='gradual', force_recreate=True)(weights=[40, 40, 20])
    for _ in range(10000):
        tau1, tau2 = next(materializations_generator)
        mu = next(types_generator)

        tau3, mu1 = lazy_equate(tau1, mu, False)
        tau4, mu2 = lazy_equate(tau2, mu, False)

        assert is_materialization(tau3, tau4)
        assert is_materialization(mu1, mu2)

        print(f'({str(tau1)}, {str(mu)}) -> ({str(tau3), str(mu1)})')
        print(f'({str(tau2)}, {str(mu)}) -> ({str(tau4), str(mu1)})')
        print("----------------------------------------------------")


def test_lazy_equate_materialization_invariant():
    materializations_generator = generators.generate_materializations(base='gradual')(weights=[40, 40, 20])
    for _ in range(10000):
        tau1, tau2 = next(materializations_generator)
        sigma1, sigma2 = next(materializations_generator)

        tau3, sigma3 = lazy_equate(tau1, sigma1, False)
        tau4, sigma4 = lazy_equate(tau2, sigma2, False)

        assert is_materialization(tau3, tau4)
        assert is_materialization(sigma3, sigma4)


# test_lattice_relations()
# test_supremum_is_defined_or_blame_any_and_something_else()
# test_infimum_is_defined_or_blame_incompatibility_or_blame_any_and_something_else()
# test_supremum_is_diagonal_identity()
# test_supremum_is_commutative()
# test_supremum_on_tuples()
# test_supremum_on_functions()
# test_lazy_equate_identity_on_static_types()
# test_lazy_equate_materializes()
# test_lazy_equate_materialization_invariant_lemma()