from gtypes import *
import generators
import random


subtypes_generator = generators.generate_subtypes(base='static')


def test_lattice_relations():
    i = 0
    while i < 1000:
        tau1, tau2 = next(subtypes_generator)
        sigma1, sigma2 = next(subtypes_generator)
        try:
            assert is_subtype(tau1, tau2)
            assert is_subtype(sigma1, sigma2)
            assert is_subtype(infimum(tau1, sigma1), supremum(tau1, sigma1))
            # assert is_subtype(infimum(tau2, sigma2), supremum(tau2, sigma2))
            # assert is_subtype(infimum(tau1, sigma1), infimum(tau2, sigma2))
            # assert is_subtype(supremum(tau1, sigma2), supremum(tau2, sigma2))
            i += 1
            print(i)
            print(tau1)
            print(tau2)
        except TypeException as e:
            assert e.reason in [
                TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility,
                TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            ]
        except AssertionError as e:
            print(str(tau1) + '  ' + str(tau2) + '  ' + str(infimum(tau1, tau2)))
            print(str(sigma1) + '  ' + str(sigma2) + '  ' + str(infimum(sigma1, sigma2)))

test_lattice_relations()

# on static types
# def test_supremum_is_defined():
#     for _ in range(300):
#         t = [random.pickle.choice(types)[1] for i in range(2)]
#         supremum(t[0], t[1], True)
#
#
# # on static types
# def test_infimum_is_defined_or_blame_incompatibility():
#     for _ in range(300):
#         t = [random.pickle.choice(types)[1] for i in range(2)]
#         try:
#             supremum(t[0], t[1], False)
#         except TypeException as e:
#             assert e.reason == TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility
#
#
# def test_supremum_is_diagonal_identity():
#     for _, t in types:
#         assert (t == supremum(t, t, True))
#         assert (t == supremum(t, t, False))
#
#
# def test_supremum_is_commutative():
#     for _ in range(300):
#         t = [random.pickle.choice(types)[1] for i in range(2)]
#         assert supremum(t[0], t[1], True) == supremum(t[1], t[0], True)
#         try:
#             supremum(t[0], t[1], False)
#         except:
#             try:
#                 supremum(t[1], t[0], False)
#             except:
#                 continue
#             else:
#                 raise AssertionError(f"{t[1]} inf {t[0]} shouldn't be defined ")
#         else:
#             assert supremum(t[0], t[1], False) == supremum(t[1], t[0], False)
#
#
# def test_supremum_on_tuples():
#     for _ in range(300):
#         t = [random.pickle.choice(types)[1] for _ in range(4)]
#         s1 = supremum(TupleType([t[0], t[1]]), TupleType([t[2], t[3]]), True)
#         s2 = TupleType([supremum(t[0], t[2], True), supremum(t[1], t[3], True)])
#         assert s1 == s2
#
#
# def test_supremum_on_functions():
#     for _ in range(300):
#         ty = [random.pickle.choice(types)[1] for _ in range(6)]
#         try:
#             s1 = supremum(ty[0], ty[3], False)
#             s2 = supremum(ty[1], ty[4], False)
#         except TypeException as e:
#             assert e.reason == TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility
#             assert supremum(FunctionType([ty[0], ty[1]], ty[2]), FunctionType([ty[3], ty[4]], ty[5]), True) == TermType()
#         else:
#             s3 = FunctionType([s1, s2], supremum(ty[2], ty[5], True))
#             assert s3 == supremum(FunctionType([ty[0], ty[1]], ty[2]), FunctionType([ty[3], ty[4]], ty[5]), True)
#
#
# #
# # print("---------------------5---------------------")
# #
#
#
# test_supremum_is_defined()
# test_infimum_is_defined_or_blame_incompatibility()
# test_supremum_is_diagonal_identity()
# test_supremum_is_commutative()
# test_supremum_on_tuples()
# test_supremum_on_functions()
