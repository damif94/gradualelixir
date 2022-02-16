from gradualelixir.gtypes import generators
from gradualelixir.gtypes.definitions import (
    FunctionType,
    NoneType,
    TermType,
    TupleType,
    TypeException,
    TypeExceptionEnum,
    infimum,
    is_materialization,
    is_msubtype_plus,
    is_static_type,
    is_subtype,
    minfimum_minus,
    minfimum_plus,
    supremum,
)
from gradualelixir.gtypes.generators import generate_materializations


def test_subtype_is_msubtype_plus():
    subtypes_generator = generators.generate_subtypes(base="gradual")()
    for _ in range(1000):
        tau, sigma = next(subtypes_generator)
        try:
            assert is_msubtype_plus(tau, sigma)
        except AssertionError as e:
            is_subtype(tau, sigma)
            raise e


def test_lattice_relations():
    subtypes_generator = generators.generate_subtypes(base="gradual")()
    for _ in range(1000):
        tau1, tau2 = next(subtypes_generator)
        sigma1, sigma2 = next(subtypes_generator)
        try:
            assert is_subtype(supremum(tau1, sigma1), supremum(tau2, sigma2))
            assert is_subtype(infimum(tau1, sigma1), infimum(tau2, sigma2))
        except TypeException as e:
            assert (
                e.reason
                == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            )
        except AssertionError as e:
            print(tau1)
            print(sigma1)
            print(infimum(tau1, sigma1))
            print(tau2)
            print(sigma2)
            print(infimum(tau2, sigma2))
            raise e


def test_top_and_bottom_of_lattice():
    types_generator = generators.generate_types(base="gradual")()
    tau = next(types_generator)
    for _ in range(1000):
        if is_static_type(tau):
            assert is_subtype(tau, TermType())
            assert is_subtype(NoneType(), tau)
        else:
            try:
                is_subtype(tau, TermType())
            except TypeException as e:
                assert (
                    e.reason
                    == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
                )
            try:
                is_subtype(NoneType(), tau)
            except TypeException as e:
                assert (
                    e.reason
                    == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
                )


def test_supremum_is_defined_or_blame_any_and_something_else():
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(2500):
        tau1, tau2 = next(types_generator), next(types_generator)
        try:
            supremum(tau1, tau2)
        except TypeException as e:
            assert (
                e.reason
                == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            )


def test_infimum_is_defined_or_blame_any_and_something_else():
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(5000):
        tau1, tau2 = next(types_generator), next(types_generator)
        try:
            infimum(tau1, tau2)
        except TypeException as e:
            assert (
                e.reason
                is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            )


def test_supremum_is_diagonal_identity():
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(5000):
        tau = next(types_generator)
        assert tau == supremum(tau, tau)
        assert tau == infimum(tau, tau)


def test_supremum_is_commutative():
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(5000):
        tau, sigma = next(types_generator), next(types_generator)
        try:
            supremum(tau, sigma)
        except TypeException as e:
            assert (
                e.reason
                == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            )
        else:
            print(tau)
            print(sigma)
            try:
                assert supremum(tau, sigma) == supremum(sigma, tau)
            except Exception as e:
                supremum(tau, sigma)
                supremum(sigma, tau)
                raise e


def test_supremum_on_tuples():
    types_generator = generators.generate_types(base="gradual")()
    for _ in range(5000):
        tau1, sigma1 = next(types_generator), next(types_generator)
        tau2, sigma2 = next(types_generator), next(types_generator)
        try:
            s1 = supremum(tau1, sigma1)
            s2 = supremum(tau2, sigma2)
            assert TupleType([s1, s2]) == supremum(
                TupleType([tau1, tau2]), TupleType([sigma1, sigma2])
            )
        except TypeException as e:
            assert (
                e.reason
                == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            )


def test_supremum_on_functions():
    types_generator = generators.generate_types(base="gradual")(weights=[50, 50, 0])
    for _ in range(10000):
        tau1, sigma1 = next(types_generator), next(types_generator)
        tau2, sigma2 = next(types_generator), next(types_generator)
        tau3, sigma3 = next(types_generator), next(types_generator)
        try:
            s1 = infimum(tau1, sigma1)
            s2 = infimum(tau2, sigma2)
            s3 = supremum(tau3, sigma3)
            print(str(tau1) + " " + str(sigma1) + " " + str(s1))
            print(str(tau2) + " " + str(sigma2) + " " + str(s2))
            print("-------------------")
        except TypeException as e:
            assert (
                e.reason
                is TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            )
        else:
            assert FunctionType([s1, s2], s3) == supremum(
                FunctionType([tau1, tau2], tau3), FunctionType([sigma1, sigma2], sigma3)
            )


def test_materialization_and_msupremmum():
    materializations_generator = generate_materializations(remote=False)()
    for i in range(10000):
        (tau1, tau2), (sigma1, sigma2) = next(materializations_generator), next(
            materializations_generator
        )
        if isinstance(tau1, TupleType) and isinstance(sigma1, TupleType):
            print(
                str(tau1) + " " + str(sigma1) + " " + str(minfimum_minus(tau1, sigma1))
            )
            print(
                str(tau2) + " " + str(sigma2) + " " + str(minfimum_minus(tau2, sigma2))
            )
            print(
                str(tau1) + " " + str(sigma1) + " " + str(minfimum_plus(tau1, sigma1))
            )
            print(
                str(tau2) + " " + str(sigma2) + " " + str(minfimum_plus(tau2, sigma2))
            )
            print(i)
            print(
                "---------------------------------------------------------------------"
            )
        assert is_materialization(
            minfimum_plus(tau1, sigma1), minfimum_plus(tau2, sigma2)
        )
        assert is_materialization(
            minfimum_minus(tau1, sigma1), minfimum_minus(tau2, sigma2)
        )
