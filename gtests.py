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
            assert is_subtype(supremum(tau1, sigma1, False), supremum(tau2, sigma2, False))
            assert is_subtype(infimum(tau2, sigma2, False), infimum(tau2, sigma2, False))
        except TypeException as e:
            assert e.reason in [
                TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility,
                TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            ]


def test_msupremum_plus_lattice_relations():
    msubtypes_generator = generators.generate_msubtypes(base='gradual', polarity='+')(weights=[30, 40, 30])
    for i in range(5000):
        tau1, tau2 = next(msubtypes_generator)
        sigma1, sigma2 = next(msubtypes_generator)
        assert is_msubtype_plus(msupremum(tau1, sigma1, '+'), msupremum(tau2, sigma2, '+'))


def test_msupremum_minus_lattice_relations():
    msubtypes_generator = generators.generate_msubtypes(base='gradual', polarity='-')(weights=[30, 40, 30])
    for i in range(5000):
        tau1, tau2 = next(msubtypes_generator)
        sigma1, sigma2 = next(msubtypes_generator)
        try:
            assert is_msubtype_minus(msupremum(tau1, sigma1, '-'), msupremum(tau2, sigma2, '-'))
        except TypeException as e:
            if e.reason != TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility:
                msupremum(tau1, sigma1, '-')
                msupremum(tau2, sigma2, '-')


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
    for i in range(5000):
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
        for m in [True, False]:
            tau = next(types_generator)
            assert tau == supremum(tau, tau, m)
            assert tau == infimum(tau, tau, m)


def test_supremum_is_commutative():
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(300):
        tau, sigma = next(types_generator), next(types_generator)
        for m in [True, False]:
            try:
                supremum(tau, sigma, m)
            except TypeException as e:
                assert e.reason == TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
                assert not m
            else:
                assert supremum(tau, sigma, m) == supremum(sigma, tau, m)

def test_supremum_on_tuples():
    types_generator = generators.types_generator(base='gradual')()
    for _ in range(300):
        tau1, sigma1 = next(types_generator), next(types_generator)
        tau2, sigma2 = next(types_generator), next(types_generator)
        for m in [True, False]:
            try:
                s1 = supremum(tau1, sigma1,  m)
                s2 = supremum(tau2, sigma2, m)
                assert TupleType([s1, s2]) == supremum(TupleType([tau1, tau2]), TupleType([sigma1, sigma2]), m)
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



#
# def test_lazy_equate():
#     gtypes.base_types += [gtypes.AnyType(), gtypes.AnyType(), gtypes.AnyType()]
#     types = generate_types(1)
#     print(len(types))
#     i = 0
#     while i < 50000:
#         t = [random.choice(types)[1] for _ in range(4)]
#         if is_msubtype(t[0], t[2], True) and is_msubtype(t[1], t[3], True):
#             i += 1
#             # u0, u1 = lazy_equate(t[0], t[1], True)
#             # u2, u3 = lazy_equate(t[2], t[3], True)
#             u0, u1 = lazy_equate(t[0], t[1], False)
#             u2, u3 = lazy_equate(t[2], t[3], False)
#             print(f"------------------------------------{i}--------------------------------------")
#             print(f'{str(t[0])},           {str(t[1])}  --->  ({str(u0)},          {str(u1)})')
#             print('          <=+                        <=+                                  ')
#             print(f'{str(t[2])},           {str(t[3])}  --->  ({str(u2)},          {str(u3)} ')
#             try:
#                 assert is_msubtype(l1 := supremum(u0, u1, True), l2 := supremum(u2, u3, True), True)
#                 print(f'{l1} <=+ {l2}')
#             except AssertionError as e:
#                 print(f'{l1} <=+nooo {l2}')
#                 raise e

# test_lattice_relations()
test_msupremum_minus_lattice_relations()
# test_supremum_is_defined_or_blame_any_and_something_else()
# test_infimum_is_defined_or_blame_incompatibility_or_blame_any_and_something_else()
# test_supremum_is_diagonal_identity()
# test_supremum_is_commutative()
# test_supremum_on_tuples()
# test_supremum_on_functions()
# test_lazy_equate()
#
#
# print(is_msubtype(FunctionType([NumberType()], IntegerType()), FunctionType([IntegerType()], IntegerType()), True))
