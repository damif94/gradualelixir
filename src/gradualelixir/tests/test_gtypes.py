import typing

from gradualelixir import gtypes
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
    Type,
    is_materialization,
    is_subtype,
)

from . import TEST_ENV
from ..utils import long_line, Bcolors


def MapUnit(*args) -> MapType:
    return MapType({MapKey(arg): TupleType([]) for arg in args})


def assert_subtype(tau: Type, sigma: Type):
    assert is_subtype(tau, sigma)
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Relation:{Bcolors.ENDC} {tau} <={sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: True\n")


def assert_not_subtype(tau: Type, sigma: Type):
    assert not is_subtype(tau, sigma)
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Relation:{Bcolors.ENDC} {tau} <= {sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: False\n")


def assert_materialization(tau: Type, sigma: Type):
    assert is_materialization(tau, sigma)
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Relation:{Bcolors.ENDC} {tau} <<< {sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: True\n")


def assert_not_materialization(tau: Type, sigma: Type):
    assert not is_materialization(tau, sigma)
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Relation:{Bcolors.ENDC} {tau} <<< {sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: False\n")


def assert_merge_operator(input: typing.Tuple[Type, Type], output: Type):
    tau, sigma = input
    result = gtypes.merge_operator(tau, sigma)
    assert result == output
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Operation:{Bcolors.ENDC} {tau} <- {sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: {output}\n")


def assert_supremum_ok(input: typing.Tuple[Type, Type], output: Type):
    tau, sigma = input
    result = gtypes.supremum(tau, sigma)
    assert result == output
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Operation:{Bcolors.ENDC} {tau} \\/ {sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: {output}\n")


def assert_infimum_ok(input: typing.Tuple[Type, Type], output: Type):
    tau, sigma = input
    result = gtypes.infimum(tau, sigma)
    assert result == output
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Operation:{Bcolors.ENDC}: {tau} /\\ {sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: {output}\n")


def assert_supremum_error(tau: Type, sigma: Type, sup=True):
    result = gtypes.supremum(tau, sigma)
    assert isinstance(result, gtypes.SupremumError)
    assert result.args[0] == "supremum" if sup else "infimum"
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Operation:{Bcolors.ENDC}: {tau} \\/ {sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: Not defined\n")


def assert_infimum_error(tau: Type, sigma: Type, sup=False):
    result = gtypes.infimum(tau, sigma)
    assert isinstance(result, gtypes.SupremumError)
    assert result.args[0] == "supremum" if sup else "infimum"
    if TEST_ENV.get("display_results"):
        print(long_line)
        print()
        print(f"{Bcolors.OKBLUE}Operation:{Bcolors.ENDC}: {tau} /\\ {sigma}")
        print(f"{Bcolors.OKBLUE}Result:{Bcolors.ENDC}: Not defined\n")


def test_subtype_base():
    assert_subtype(IntegerType(), IntegerType())
    assert_subtype(IntegerType(), NumberType())
    assert_subtype(FloatType(), FloatType())
    assert_subtype(FloatType(), NumberType())
    assert_subtype(AtomLiteralType("a"), AtomType())
    assert_subtype(AtomLiteralType("true"), BooleanType())
    assert_subtype(AtomLiteralType("false"), BooleanType())
    assert_subtype(AtomLiteralType("true"), AtomType())
    assert_subtype(AtomLiteralType("false"), AtomType())
    assert_subtype(BooleanType(), AtomType())

    assert_not_subtype(NumberType(), IntegerType())
    assert_not_subtype(NumberType(), FloatType())
    assert_not_subtype(AtomType(), AtomLiteralType("a"))
    assert_not_subtype(BooleanType(), AtomLiteralType("true"))
    assert_not_subtype(BooleanType(), AtomLiteralType("false"))
    assert_not_subtype(AtomType(), AtomLiteralType("true"))
    assert_not_subtype(AtomType(), AtomLiteralType("false"))
    assert_not_subtype(AtomType(), BooleanType())

    assert_not_subtype(AtomType(), IntegerType())
    assert_not_subtype(IntegerType(), AtomType())
    assert_not_subtype(AtomType(), FloatType())
    assert_not_subtype(FloatType(), AtomType())
    assert_not_subtype(AtomType(), NumberType())
    assert_not_subtype(NumberType(), AtomType())
    assert_not_subtype(BooleanType(), IntegerType())
    assert_not_subtype(IntegerType(), BooleanType())
    assert_not_subtype(BooleanType(), FloatType())
    assert_not_subtype(FloatType(), BooleanType())
    assert_not_subtype(BooleanType(), NumberType())
    assert_not_subtype(NumberType(), BooleanType())


def test_subtype_list():
    assert_subtype(ElistType(), ElistType())
    assert_subtype(ElistType(), ListType(AtomLiteralType("true")))
    assert_subtype(ElistType(), ListType(IntegerType()))
    assert_subtype(ElistType(), ListType(AnyType()))
    assert_subtype(ElistType(), ListType(TupleType([AnyType()])))

    assert_not_subtype(ListType(AtomLiteralType("true")), ElistType())
    assert_not_subtype(TupleType([]), ElistType())
    assert_not_subtype(ListType(AnyType()), ElistType())
    assert_not_subtype(ListType(TupleType([AnyType()])), ElistType())

    assert_subtype(ListType(AtomLiteralType("true")), ListType(BooleanType()))
    assert_subtype(ListType(IntegerType()), ListType(IntegerType()))
    assert_subtype(ListType(IntegerType()), ListType(NumberType()))
    assert_subtype(ListType(IntegerType()), ListType(AnyType()))
    assert_subtype(ListType(AnyType()), ListType(IntegerType()))
    assert_subtype(ListType(TupleType([IntegerType(), IntegerType()])), ListType(TupleType([NumberType(), AnyType()])))

    assert_not_subtype(ListType(BooleanType()), ListType(AtomLiteralType("true")))
    assert_not_subtype(ListType(TupleType([BooleanType()])), ListType(BooleanType()))
    assert_not_subtype(
        ListType(TupleType([NumberType(), IntegerType()])), ListType(TupleType([IntegerType(), AnyType()]))
    )
    assert_not_subtype(
        ListType(TupleType([NumberType(), AnyType()])), ListType(TupleType([IntegerType(), IntegerType()]))
    )


def test_subtype_tuple():
    assert_subtype(TupleType([]), TupleType([]))
    assert_subtype(TupleType([IntegerType()]), TupleType([IntegerType()]))
    assert_subtype(TupleType([IntegerType(), FloatType()]), TupleType([IntegerType(), FloatType()]))

    assert_subtype(TupleType([AnyType()]), TupleType([ListType(IntegerType())]))
    assert_subtype(TupleType([IntegerType()]), TupleType([NumberType()]))
    assert_subtype(TupleType([IntegerType(), FloatType()]), TupleType([NumberType(), FloatType()]))
    assert_subtype(TupleType([IntegerType(), FloatType()]), TupleType([AnyType(), FloatType()]))
    assert_subtype(TupleType([IntegerType(), FloatType()]), TupleType([NumberType(), AnyType()]))
    assert_subtype(TupleType([AnyType(), FloatType()]), TupleType([NumberType(), AnyType()]))

    assert_not_subtype(TupleType([]), TupleType([IntegerType()]))
    assert_not_subtype(TupleType([IntegerType()]), TupleType([]))
    assert_not_subtype(TupleType([IntegerType()]), TupleType([IntegerType(), FloatType()]))
    assert_not_subtype(TupleType([IntegerType(), FloatType()]), TupleType([IntegerType()]))
    assert_not_subtype(TupleType([]), TupleType([IntegerType(), FloatType()]))
    assert_not_subtype(TupleType([IntegerType(), FloatType()]), TupleType([]))

    assert_not_subtype(TupleType([IntegerType()]), TupleType([FloatType()]))
    assert_not_subtype(TupleType([FloatType()]), TupleType([IntegerType()]))
    assert_not_subtype(TupleType([IntegerType(), AnyType()]), TupleType([FloatType(), AnyType()]))


def test_subtype_map():
    assert_subtype(MapType({}), MapType({}))
    assert_subtype(MapType({MapKey(1): IntegerType()}), MapType({MapKey(1): IntegerType()}))
    assert_subtype(
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
    )

    assert_subtype(MapType({MapKey(1): IntegerType()}), MapType({}))
    assert_subtype(MapType({MapKey(1): AnyType()}), MapType({}))
    assert_subtype(MapType({MapKey(1): TupleType([IntegerType(), AnyType()])}), MapType({}))
    assert_subtype(MapType({MapKey(1): IntegerType()}), MapType({MapKey(1): NumberType()}))
    assert_subtype(MapType({MapKey(1): IntegerType(), MapKey(2): TupleType([BooleanType(), AnyType()])}), MapType({}))
    assert_subtype(
        MapType({MapKey(1): IntegerType(), MapKey(2): TupleType([BooleanType(), AnyType()])}),
        MapType({MapKey(1): NumberType()}),
    )
    assert_subtype(
        MapType({MapKey(1): IntegerType(), MapKey(2): TupleType([BooleanType(), AnyType()])}),
        MapType({MapKey(2): TupleType([BooleanType(), NumberType()])}),
    )

    assert_not_subtype(MapType({MapKey(1): NumberType()}), MapType({MapKey(1): IntegerType()}))
    assert_not_subtype(MapType({MapKey(1): NumberType()}), MapType({MapKey(1): BooleanType()}))
    assert_not_subtype(
        MapType({MapKey(1): TupleType([NumberType(), AnyType()])}),
        MapType({MapKey(1): TupleType([IntegerType(), AnyType()])}),
    )

    assert_not_subtype(MapType({}), MapType({MapKey(1): IntegerType()}))
    assert_not_subtype(MapType({}), MapType({MapKey(1): AnyType()}))
    assert_not_subtype(MapType({MapKey(1): IntegerType()}), MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}))
    assert_not_subtype(MapType({MapKey(1): IntegerType()}), MapType({MapKey(1): AnyType(), MapKey(2): NumberType()}))
    assert_not_subtype(MapType({}), MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}))
    assert_not_subtype(MapType({}), MapType({MapKey(1): AnyType(), MapKey(2): NumberType()}))


def test_subtype_function():
    assert_subtype(FunctionType([], IntegerType()), FunctionType([], IntegerType()))
    assert_subtype(FunctionType([BooleanType()], IntegerType()), FunctionType([BooleanType()], IntegerType()))
    assert_subtype(
        FunctionType([BooleanType(), FloatType()], IntegerType()),
        FunctionType([BooleanType(), FloatType()], IntegerType()),
    )

    assert_subtype(IntegerType(), NumberType())
    assert_subtype(FunctionType([], AnyType()), FunctionType([], NumberType()))
    assert_subtype(FunctionType([], IntegerType()), FunctionType([], AnyType()))
    assert_subtype(FunctionType([BooleanType()], IntegerType()), FunctionType([BooleanType()], NumberType()))
    assert_subtype(FunctionType([AtomType()], IntegerType()), FunctionType([BooleanType()], IntegerType()))
    assert_subtype(FunctionType([AtomType()], IntegerType()), FunctionType([BooleanType()], NumberType()))
    assert_subtype(FunctionType([AtomType()], IntegerType()), FunctionType([BooleanType()], AnyType()))
    assert_subtype(FunctionType([AnyType()], IntegerType()), FunctionType([BooleanType()], NumberType()))
    assert_subtype(FunctionType([AnyType()], IntegerType()), FunctionType([BooleanType()], AnyType()))
    assert_subtype(
        FunctionType([AnyType(), IntegerType()], ListType(IntegerType())),
        FunctionType([BooleanType(), IntegerType()], ListType(AnyType())),
    )

    assert_not_subtype(IntegerType(), FunctionType([AnyType()], IntegerType()))
    assert_not_subtype(IntegerType(), FunctionType([BooleanType()], IntegerType()))
    assert_not_subtype(FunctionType([AnyType()], IntegerType()), IntegerType())
    assert_not_subtype(FunctionType([BooleanType()], IntegerType()), IntegerType())
    assert_not_subtype(
        FunctionType([AnyType()], IntegerType()), FunctionType([BooleanType(), IntegerType()], IntegerType())
    )
    assert_not_subtype(
        FunctionType([BooleanType(), IntegerType()], IntegerType()), FunctionType([AnyType()], IntegerType())
    )
    assert_not_subtype(
        FunctionType([BooleanType(), IntegerType()], IntegerType()), FunctionType([IntegerType()], IntegerType())
    )

    assert_not_subtype(NumberType(), IntegerType())
    assert_not_subtype(FunctionType([BooleanType()], IntegerType()), FunctionType([AtomType()], NumberType()))
    assert_not_subtype(
        FunctionType([BooleanType()], IntegerType()), FunctionType([ListType(BooleanType())], IntegerType())
    )
    assert_not_subtype(FunctionType([AtomType()], NumberType()), FunctionType([BooleanType()], IntegerType()))
    assert_not_subtype(FunctionType([AtomType()], NumberType()), FunctionType([BooleanType()], TupleType([AnyType()])))


def test_materialization_base():
    assert_materialization(IntegerType(), IntegerType())
    assert_materialization(FloatType(), FloatType())
    assert_materialization(NumberType(), NumberType())
    assert_materialization(AtomType(), AtomType())
    assert_materialization(AtomLiteralType("a"), AtomLiteralType("a"))
    assert_materialization(AnyType(), IntegerType())
    assert_materialization(AnyType(), FloatType())
    assert_materialization(AnyType(), NumberType())
    assert_materialization(AnyType(), AtomType())
    assert_materialization(AnyType(), AtomLiteralType("a"))

    assert_not_materialization(IntegerType(), NumberType())
    assert_not_materialization(NumberType(), IntegerType())
    assert_not_materialization(AtomLiteralType("a"), AtomLiteralType("b"))
    assert_not_materialization(IntegerType(), AnyType())
    assert_not_materialization(FloatType(), AnyType())
    assert_not_materialization(NumberType(), AnyType())
    assert_not_materialization(AtomType(), AnyType())
    assert_not_materialization(AtomLiteralType("a"), AnyType())


def test_materialization_list():
    assert_materialization(ElistType(), ElistType())
    assert_materialization(AnyType(), ElistType())

    assert_not_materialization(ElistType(), AnyType())

    assert_materialization(ListType(IntegerType()), ListType(IntegerType()))
    assert_materialization(ListType(AnyType()), ListType(IntegerType()))
    assert_materialization(AnyType(), ListType(IntegerType()))
    assert_materialization(AnyType(), ListType(AnyType()))

    assert_not_materialization(ListType(IntegerType()), AnyType())
    assert_not_materialization(ListType(AnyType()), AnyType())
    assert_not_materialization(ListType(IntegerType()), ListType(AnyType()))
    assert_not_materialization(ElistType(), ListType(AnyType()))


def test_materialization_tuple():
    assert_materialization(TupleType([IntegerType(), NumberType()]), TupleType([IntegerType(), NumberType()]))
    assert_materialization(TupleType([IntegerType(), AnyType()]), TupleType([IntegerType(), NumberType()]))
    assert_materialization(TupleType([AnyType(), AnyType()]), TupleType([IntegerType(), NumberType()]))
    assert_materialization(AnyType(), TupleType([IntegerType(), NumberType()]))
    assert_materialization(AnyType(), TupleType([AnyType(), AnyType()]))

    assert_not_materialization(TupleType([IntegerType(), NumberType()]), TupleType([NumberType(), NumberType()]))
    assert_not_materialization(TupleType([IntegerType(), AnyType()]), TupleType([AnyType(), NumberType()]))
    assert_not_materialization(TupleType([AnyType(), AnyType()]), IntegerType())
    assert_not_materialization(TupleType([AnyType(), AnyType()]), AnyType())
    assert_not_materialization(TupleType([AnyType(), AnyType()]), TupleType([AnyType()]))
    assert_not_materialization(TupleType([AnyType(), AnyType()]), TupleType([AnyType(), AnyType(), AnyType()]))


def test_materialization_map():
    assert_materialization(
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
    )
    assert_materialization(
        MapType({MapKey(1): IntegerType(), MapKey(2): AnyType()}),
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
    )
    assert_materialization(
        MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}),
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
    )
    assert_materialization(AnyType(), MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}))
    assert_materialization(AnyType(), MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}))

    assert_not_materialization(
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
        MapType({MapKey(1): NumberType(), MapKey(2): NumberType()}),
    )
    assert_not_materialization(
        MapType({MapKey(1): IntegerType(), MapKey(2): AnyType()}),
        MapType({MapKey(1): AnyType(), MapKey(2): NumberType()}),
    )
    assert_not_materialization(
        MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}), MapType({MapKey(1): IntegerType()})
    )
    assert_not_materialization(MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}), MapType({MapKey(1): AnyType()}))
    assert_not_materialization(
        MapType({MapKey(1): AnyType(), MapKey(2): AnyType()}),
        MapType({MapKey(1): AnyType(), MapKey(2): AnyType(), MapKey(3): AnyType()}),
    )


def test_materialization_function():
    assert_materialization(FunctionType([IntegerType()], NumberType()), FunctionType([IntegerType()], NumberType()))
    assert_materialization(FunctionType([IntegerType()], AnyType()), FunctionType([IntegerType()], NumberType()))
    assert_materialization(FunctionType([AnyType()], AnyType()), FunctionType([IntegerType()], NumberType()))
    assert_materialization(AnyType(), FunctionType([IntegerType()], NumberType()))
    assert_materialization(AnyType(), FunctionType([AnyType()], AnyType()))

    assert_not_materialization(FunctionType([IntegerType()], NumberType()), FunctionType([NumberType()], NumberType()))
    assert_not_materialization(FunctionType([IntegerType()], AnyType()), FunctionType([AnyType()], NumberType()))
    assert_not_materialization(FunctionType([AnyType()], AnyType()), IntegerType())
    assert_not_materialization(FunctionType([AnyType()], AnyType()), AnyType())
    assert_not_materialization(FunctionType([AnyType()], AnyType()), FunctionType([], AnyType()))
    assert_not_materialization(FunctionType([AnyType()], AnyType()), FunctionType([AnyType(), AnyType()], AnyType()))


def test_merge_operator():
    assert_merge_operator((AnyType(), AnyType()), AnyType())
    assert_merge_operator((IntegerType(), IntegerType()), IntegerType())
    assert_merge_operator((AnyType(), IntegerType()), IntegerType())
    assert_merge_operator((IntegerType(), AnyType()), AnyType())
    assert_merge_operator((IntegerType(), NumberType()), IntegerType())

    assert_merge_operator((AnyType(), ListType(IntegerType())), ListType(IntegerType()))
    assert_merge_operator((ListType(IntegerType()), ListType(AnyType())), ListType(AnyType()))
    assert_merge_operator((ListType(IntegerType()), ListType(NumberType())), ListType(IntegerType()))

    assert_merge_operator((AnyType(), TupleType([])), TupleType([]))
    assert_merge_operator((AnyType(), TupleType([IntegerType()])), TupleType([IntegerType()]))
    assert_merge_operator((TupleType([AnyType()]), TupleType([IntegerType()])), TupleType([IntegerType()]))
    assert_merge_operator(
        (TupleType([AnyType(), IntegerType(), IntegerType()]), TupleType([NumberType(), NumberType(), AnyType()])),
        TupleType([NumberType(), IntegerType(), AnyType()]),
    )

    assert_merge_operator((AnyType(), MapType({})), MapType({}))
    assert_merge_operator((AnyType(), MapType({MapKey(1): IntegerType()})), MapType({MapKey(1): IntegerType()}))
    assert_merge_operator(
        (
            MapType({MapKey(1): AnyType(), MapKey(2): IntegerType()}),
            MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
        ),
        MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
    )
    assert_merge_operator(
        (
            MapType({MapKey(1): AnyType(), MapKey(2): IntegerType(), MapKey(3): AtomType()}),
            MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
        ),
        MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType(), MapKey(3): AtomType()}),
    )

    assert_merge_operator(
        (FunctionType([TupleType([])], MapUnit(1)), FunctionType([TupleType([])], MapUnit())),
        FunctionType([TupleType([])], MapUnit(1)),
    )

    assert_merge_operator(
        (FunctionType([MapUnit()], AnyType()), FunctionType([MapUnit(1)], AnyType())),
        FunctionType([MapUnit()], AnyType()),
    )

    assert_merge_operator(
        (
            FunctionType([AnyType(), NumberType()], TupleType([AnyType(), IntegerType()])),
            FunctionType([AtomType(), IntegerType()], TupleType([AtomType(), NumberType()])),
        ),
        FunctionType([AtomType(), NumberType()], TupleType([AtomType(), IntegerType()])),
    )

    assert_merge_operator(
        (
            MapType(
                {
                    MapKey(1): TupleType([IntegerType(), ListType(AnyType())]),
                    MapKey(2): IntegerType(),
                    MapKey(3): TupleType([IntegerType(), AnyType()]),
                }
            ),
            MapType({MapKey(1): TupleType([NumberType(), ListType(NumberType())]), MapKey(2): NumberType()}),
        ),
        MapType(
            {
                MapKey(1): TupleType([IntegerType(), ListType(NumberType())]),
                MapKey(2): IntegerType(),
                MapKey(3): TupleType([IntegerType(), AnyType()]),
            }
        ),
    )


def test_supremum_base():
    assert_supremum_ok((IntegerType(), IntegerType()), IntegerType())
    assert_supremum_ok((IntegerType(), NumberType()), NumberType())
    assert_supremum_ok((NumberType(), IntegerType()), NumberType())
    assert_supremum_ok((FloatType(), FloatType()), FloatType())
    assert_supremum_ok((FloatType(), NumberType()), NumberType())
    assert_supremum_ok((NumberType(), FloatType()), NumberType())
    assert_supremum_ok((IntegerType(), FloatType()), NumberType())
    assert_supremum_ok((BooleanType(), BooleanType()), BooleanType())
    assert_supremum_error(BooleanType(), IntegerType())
    assert_supremum_error(IntegerType(), BooleanType())
    assert_supremum_error(BooleanType(), FloatType())
    assert_supremum_error(FloatType(), BooleanType())
    assert_supremum_error(BooleanType(), NumberType())
    assert_supremum_error(NumberType(), BooleanType())

    assert_supremum_ok((AtomLiteralType("true"), AtomLiteralType("true")), AtomLiteralType("true"))
    assert_supremum_ok((AtomLiteralType("false"), AtomLiteralType("false")), AtomLiteralType("false"))
    assert_supremum_ok((AtomLiteralType("true"), AtomLiteralType("false")), BooleanType())
    assert_supremum_ok((AtomLiteralType("false"), AtomLiteralType("true")), BooleanType())
    assert_supremum_ok((AtomLiteralType("true"), BooleanType()), BooleanType())
    assert_supremum_ok((BooleanType(), AtomLiteralType("true")), BooleanType())
    assert_supremum_ok((AtomLiteralType("false"), BooleanType()), BooleanType())
    assert_supremum_ok((BooleanType(), AtomLiteralType("false")), BooleanType())

    assert_supremum_ok((AtomLiteralType("a"), AtomLiteralType("a")), AtomLiteralType("a"))
    assert_supremum_ok((AtomLiteralType("b"), AtomLiteralType("b")), AtomLiteralType("b"))
    assert_supremum_ok((AtomLiteralType("a"), AtomLiteralType("b")), AtomType())
    assert_supremum_ok((AtomLiteralType("b"), AtomLiteralType("a")), AtomType())

    assert_supremum_ok((AtomLiteralType("true"), AtomLiteralType("a")), AtomType())
    assert_supremum_ok((AtomLiteralType("false"), AtomLiteralType("a")), AtomType())
    assert_supremum_ok((AtomLiteralType("a"), AtomLiteralType("true")), AtomType())
    assert_supremum_ok((AtomLiteralType("a"), AtomLiteralType("false")), AtomType())

    assert_supremum_ok((AtomLiteralType("a"), BooleanType()), AtomType())
    assert_supremum_ok((BooleanType(), AtomLiteralType("a")), AtomType())


def test_infimum_base():
    assert_infimum_ok((IntegerType(), IntegerType()), IntegerType())
    assert_infimum_ok((IntegerType(), NumberType()), IntegerType())
    assert_infimum_ok((NumberType(), IntegerType()), IntegerType())
    assert_infimum_ok((FloatType(), FloatType()), FloatType())
    assert_infimum_ok((FloatType(), NumberType()), FloatType())
    assert_infimum_ok((NumberType(), FloatType()), FloatType())
    assert_infimum_error(IntegerType(), FloatType())
    assert_infimum_error(FloatType(), IntegerType())
    assert_infimum_error(IntegerType(), BooleanType())
    assert_infimum_error(BooleanType(), IntegerType())
    assert_infimum_error(NumberType(), BooleanType())
    assert_infimum_error(BooleanType(), NumberType())

    assert_infimum_ok((AtomLiteralType("true"), AtomLiteralType("true")), AtomLiteralType("true"))
    assert_infimum_ok((AtomLiteralType("false"), AtomLiteralType("false")), AtomLiteralType("false"))
    assert_infimum_ok((BooleanType(), AtomLiteralType("true")), AtomLiteralType("true"))
    assert_infimum_ok((AtomLiteralType("true"), BooleanType()), AtomLiteralType("true"))
    assert_infimum_ok((AtomLiteralType("false"), BooleanType()), AtomLiteralType("false"))
    assert_infimum_ok((BooleanType(), AtomLiteralType("false")), AtomLiteralType("false"))
    assert_infimum_error(AtomLiteralType("true"), AtomLiteralType("false"))
    assert_infimum_error(AtomLiteralType("false"), AtomLiteralType("true"))

    assert_infimum_ok((AtomLiteralType("a"), AtomLiteralType("a")), AtomLiteralType("a"))
    assert_infimum_ok((AtomLiteralType("b"), AtomLiteralType("b")), AtomLiteralType("b"))
    assert_infimum_error(AtomLiteralType("a"), AtomLiteralType("b"))
    assert_infimum_error(AtomLiteralType("b"), AtomLiteralType("a"))

    assert_infimum_error(AtomLiteralType("true"), AtomLiteralType("a"))
    assert_infimum_error(AtomLiteralType("false"), AtomLiteralType("a"))
    assert_infimum_error(AtomLiteralType("a"), AtomLiteralType("true"))
    assert_infimum_error(AtomLiteralType("a"), AtomLiteralType("false"))

    assert_infimum_error(AtomLiteralType("a"), BooleanType())
    assert_infimum_error(BooleanType(), AtomLiteralType("a"))


def test_supremum_list():
    assert_supremum_ok((ElistType(), ListType(IntegerType())), ListType(IntegerType()))
    assert_supremum_ok((ListType(IntegerType()), ElistType()), ListType(IntegerType()))
    assert_supremum_ok((ListType(IntegerType()), ListType(IntegerType())), ListType(IntegerType()))
    assert_supremum_ok((ListType(IntegerType()), ListType(FloatType())), ListType(NumberType()))

    assert_supremum_ok((ElistType(), ListType(ListType(FloatType()))), ListType(ListType(FloatType())))
    assert_supremum_ok((ListType(ElistType()), ListType(ListType(FloatType()))), ListType(ListType(FloatType())))
    assert_supremum_ok(
        (ListType(ListType(IntegerType())), ListType(ListType(FloatType()))), ListType(ListType(NumberType()))
    )

    assert_supremum_error(ListType(IntegerType()), ListType(BooleanType()))


def test_infimum_list():
    assert_infimum_ok((ElistType(), ListType(IntegerType())), ElistType())
    assert_infimum_ok((ListType(IntegerType()), ElistType()), ElistType())
    assert_infimum_ok((ListType(IntegerType()), ListType(IntegerType())), ListType(IntegerType()))
    assert_infimum_ok(
        (ListType(MapType({MapKey(1): TupleType([])})), ListType(MapType({MapKey(2): TupleType([])}))),
        ListType(MapUnit(1, 2)),
    )

    assert_infimum_ok((ElistType(), ListType(ListType(FloatType()))), ElistType())
    assert_infimum_ok((ListType(ElistType()), ListType(ListType(FloatType()))), ListType(ElistType()))
    assert_infimum_ok(
        (
            ListType(ListType(MapType({MapKey(1): TupleType([])}))),
            ListType(ListType(MapType({MapKey(2): TupleType([])}))),
        ),
        ListType(ListType(MapUnit(1, 2))),
    )
    assert_infimum_error(ListType(IntegerType()), ListType(FloatType()))


def test_supremum_tuple():
    assert_supremum_ok((TupleType([]), TupleType([])), TupleType([]))
    assert_supremum_ok((TupleType([IntegerType()]), TupleType([FloatType()])), TupleType([NumberType()]))

    assert_supremum_ok(
        (TupleType([IntegerType(), IntegerType()]), TupleType([FloatType(), IntegerType()])),
        TupleType([NumberType(), IntegerType()]),
    )
    assert_supremum_ok(
        (TupleType([IntegerType(), IntegerType()]), TupleType([IntegerType(), FloatType()])),
        TupleType([IntegerType(), NumberType()]),
    )
    assert_supremum_ok(
        (TupleType([IntegerType(), FloatType()]), TupleType([IntegerType(), IntegerType()])),
        TupleType([IntegerType(), NumberType()]),
    )
    assert_supremum_error(TupleType([IntegerType()]), TupleType([BooleanType()]))
    assert_supremum_error(TupleType([IntegerType(), IntegerType()]), TupleType([BooleanType(), IntegerType()]))
    assert_supremum_error(TupleType([BooleanType(), IntegerType()]), TupleType([IntegerType(), IntegerType()]))
    assert_supremum_error(TupleType([BooleanType(), BooleanType()]), TupleType([IntegerType(), IntegerType()]))

    assert_supremum_error(TupleType([]), TupleType([IntegerType()]))
    assert_supremum_error(TupleType([]), TupleType([IntegerType(), FloatType()]))
    assert_supremum_error(TupleType([IntegerType()]), TupleType([IntegerType(), FloatType()]))
    assert_supremum_error(TupleType([FloatType()]), TupleType([IntegerType(), FloatType()]))

    assert_supremum_ok(
        (
            TupleType([IntegerType(), TupleType([FloatType()]), IntegerType()]),
            TupleType([FloatType(), TupleType([IntegerType()]), FloatType()]),
        ),
        TupleType([NumberType(), TupleType([NumberType()]), NumberType()]),
    )
    assert_supremum_error(
        TupleType([IntegerType(), TupleType([FloatType()]), IntegerType()]),
        TupleType([FloatType(), TupleType([IntegerType(), FloatType()])]),
    )


def test_infimum_tuple():
    assert_infimum_ok((TupleType([]), TupleType([])), TupleType([]))
    assert_infimum_ok((TupleType([MapUnit(1)]), TupleType([MapUnit(2)])), TupleType([MapUnit(1, 2)]))

    assert_infimum_ok(
        (TupleType([MapUnit(1), MapUnit(1)]), TupleType([MapUnit(2), MapUnit(1)])),
        TupleType([MapUnit(1, 2), MapUnit(1)]),
    )
    assert_infimum_ok(
        (TupleType([MapUnit(1), MapUnit(1)]), TupleType([MapUnit(1), MapUnit(2)])),
        TupleType([MapUnit(1), MapUnit(1, 2)]),
    )
    assert_infimum_ok(
        (TupleType([MapUnit(1), MapUnit(2)]), TupleType([MapUnit(1), MapUnit(1)])),
        TupleType([MapUnit(1), MapUnit(1, 2)]),
    )

    assert_infimum_error(TupleType([IntegerType()]), TupleType([FloatType()]))
    assert_infimum_error(TupleType([IntegerType(), IntegerType()]), TupleType([FloatType(), IntegerType()]))
    assert_infimum_error(TupleType([FloatType(), IntegerType()]), TupleType([IntegerType(), IntegerType()]))
    assert_infimum_error(TupleType([FloatType(), FloatType()]), TupleType([IntegerType(), IntegerType()]))

    assert_infimum_error(TupleType([]), TupleType([IntegerType()]))
    assert_infimum_error(TupleType([]), TupleType([IntegerType(), FloatType()]))
    assert_infimum_error(TupleType([IntegerType()]), TupleType([IntegerType(), FloatType()]))
    assert_infimum_error(TupleType([FloatType()]), TupleType([IntegerType(), FloatType()]))

    assert_infimum_ok(
        (
            TupleType([MapUnit(1), TupleType([MapUnit(2)]), MapUnit(1)]),
            TupleType([MapUnit(2), TupleType([MapUnit(1)]), MapUnit(2)]),
        ),
        TupleType([MapUnit(1, 2), TupleType([MapUnit(1, 2)]), MapUnit(1, 2)]),
    )

    assert_infimum_error(
        TupleType([MapUnit(1), TupleType([MapUnit(2)]), MapUnit(1)]),
        TupleType([MapUnit(1, 2), TupleType([MapUnit(1, 2), MapUnit(1, 2)])]),
    )


def test_supremum_map():
    assert_supremum_ok((MapType({}), MapType({})), MapType({}))
    assert_supremum_ok((MapUnit(1), MapType({})), MapType({}))
    assert_supremum_ok((MapType({}), MapUnit(1)), MapType({}))
    assert_supremum_ok(
        (
            MapUnit(1, 3),
            MapUnit(2, 3),
        ),
        MapUnit(3),
    )

    assert_supremum_ok((MapType({MapKey(1): IntegerType()}), MapType({MapKey(2): FloatType()})), MapType({}))
    assert_supremum_ok(
        (MapType({MapKey(1): IntegerType()}), MapType({MapKey(1): FloatType()})), MapType({MapKey(1): NumberType()})
    )
    assert_supremum_ok(
        (
            MapType({MapKey(1): MapType({MapKey(1): IntegerType()})}),
            MapType({MapKey(1): MapType({MapKey(1): FloatType()})}),
        ),
        MapType({MapKey(1): MapType({MapKey(1): NumberType()})}),
    )
    assert_supremum_ok(
        (
            MapType({MapKey(1): MapType({MapKey(2): IntegerType()})}),
            MapType({MapKey(1): MapType({MapKey(2): FloatType()})}),
        ),
        MapType({MapKey(1): MapType({MapKey(2): NumberType()})}),
    )

    assert_supremum_ok(
        (
            MapType({MapKey(1): MapUnit(3)}),
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
        ),
        MapType({MapKey(1): MapType({})}),
    )
    assert_supremum_ok(
        (
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
            MapType({MapKey(1): MapUnit(3)}),
        ),
        MapType({MapKey(1): MapType({})}),
    )
    assert_supremum_ok(
        (
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
            MapType({MapKey(1): MapUnit(3), MapKey(2): MapUnit(2)}),
        ),
        MapType({MapKey(1): MapType({}), MapKey(2): MapUnit(2)}),
    )

    assert_supremum_ok(
        (
            MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
            MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        ),
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
    )
    assert_supremum_ok(
        (
            MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
            MapType({MapKey(2): IntegerType(), MapKey(1): IntegerType()}),
        ),
        MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()}),
    )

    assert_supremum_error(MapType({MapKey(1): IntegerType()}), MapType({MapKey(1): BooleanType()}))
    assert_supremum_error(
        MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        MapType({MapKey(1): BooleanType(), MapKey(2): IntegerType()}),
    )
    assert_supremum_error(
        MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        MapType({MapKey(1): IntegerType(), MapKey(2): BooleanType()}),
    )


def test_infimum_map():
    assert_infimum_ok((MapType({}), MapType({})), MapType({}))
    assert_infimum_ok((MapUnit(1), MapType({})), MapUnit(1))
    assert_infimum_ok((MapType({}), MapUnit(1)), MapUnit(1))
    assert_infimum_ok(
        (
            MapUnit(1, 3),
            MapUnit(2, 3),
        ),
        MapType({MapKey(1): TupleType([]), MapKey(2): TupleType([]), MapKey(3): TupleType([])}),
    )

    assert_infimum_ok(
        (MapType({MapKey(1): MapUnit(1)}), MapType({MapKey(2): MapUnit(2)})),
        MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
    )
    assert_infimum_ok(
        (MapType({MapKey(1): MapUnit(1)}), MapType({MapKey(1): MapUnit(2)})),
        MapType({MapKey(1): MapUnit(1, 2)}),
    )
    assert_infimum_ok(
        (
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(1)}),
        ),
        MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(1, 2)}),
    )
    assert_infimum_ok(
        (
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
            MapType({MapKey(2): MapUnit(1), MapKey(1): MapUnit(1)}),
        ),
        MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(1, 2)}),
    )

    assert_infimum_ok(
        (
            MapType({MapKey(1): MapUnit(3)}),
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
        ),
        MapType({MapKey(1): MapUnit(1, 3), MapKey(2): MapUnit(2)}),
    )
    assert_infimum_ok(
        (
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
            MapType({MapKey(1): MapUnit(3)}),
        ),
        MapType({MapKey(1): MapUnit(1, 3), MapKey(2): MapUnit(2)}),
    )
    assert_infimum_ok(
        (
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
            MapType({MapKey(1): MapUnit(3), MapKey(2): MapUnit(2)}),
        ),
        MapType({MapKey(1): MapUnit(1, 3), MapKey(2): MapUnit(2)}),
    )

    assert_infimum_ok(
        (
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(1)}),
        ),
        MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(1, 2)}),
    )
    assert_infimum_ok(
        (
            MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(2)}),
            MapType({MapKey(2): MapUnit(1), MapKey(1): MapUnit(1)}),
        ),
        MapType({MapKey(1): MapUnit(1), MapKey(2): MapUnit(1, 2)}),
    )

    assert_infimum_error(MapType({MapKey(1): IntegerType()}), MapType({MapKey(1): FloatType()}))
    assert_infimum_error(
        MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        MapType({MapKey(1): FloatType(), MapKey(2): IntegerType()}),
    )
    assert_infimum_error(
        MapType({MapKey(1): IntegerType(), MapKey(2): IntegerType()}),
        MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()}),
    )


def test_supremum_function():
    assert_supremum_ok(
        (FunctionType([], IntegerType()), FunctionType([], IntegerType())), FunctionType([], IntegerType())
    )
    assert_supremum_ok((FunctionType([], IntegerType()), FunctionType([], FloatType())), FunctionType([], NumberType()))
    assert_supremum_ok((FunctionType([], FloatType()), FunctionType([], IntegerType())), FunctionType([], NumberType()))
    assert_supremum_ok(
        (
            FunctionType([MapUnit(1)], TupleType([])),
            FunctionType([MapUnit(2)], TupleType([])),
        ),
        FunctionType([MapUnit(1, 2)], TupleType([])),
    )
    assert_supremum_ok(
        (
            FunctionType([MapUnit(1)], MapUnit(1)),
            FunctionType([MapUnit(2)], MapUnit(2)),
        ),
        FunctionType([MapUnit(1, 2)], MapType({})),
    )
    assert_supremum_ok(
        (
            FunctionType(
                [MapUnit(1), MapUnit(3)],
                MapUnit(1),
            ),
            FunctionType(
                [MapUnit(2), MapUnit(4)],
                MapUnit(2),
            ),
        ),
        FunctionType(
            [
                MapUnit(1, 2),
                MapType({MapKey(3): TupleType([]), MapKey(4): TupleType([])}),
            ],
            MapType({}),
        ),
    )
    assert_supremum_error(FunctionType([], TupleType([])), FunctionType([FloatType()], TupleType([])))
    assert_infimum_error(
        FunctionType([IntegerType()], TupleType([])), FunctionType([BooleanType()], TupleType([])), sup=True
    )
    assert_infimum_error(FunctionType([IntegerType()], IntegerType()), FunctionType([IntegerType()], BooleanType()))
    assert_supremum_error(IntegerType(), FunctionType([IntegerType()], IntegerType()))
    assert_supremum_error(IntegerType(), FunctionType([IntegerType(), IntegerType()], IntegerType()))
    assert_supremum_error(
        FunctionType([IntegerType()], IntegerType()), FunctionType([IntegerType(), IntegerType()], IntegerType())
    )


def test_infimum_function():
    assert_infimum_ok((FunctionType([], MapUnit(1)), FunctionType([], MapUnit(1))), FunctionType([], MapUnit(1)))
    assert_infimum_ok((FunctionType([], MapUnit(1)), FunctionType([], MapUnit(2))), FunctionType([], MapUnit(1, 2)))
    assert_infimum_ok((FunctionType([], MapUnit(2)), FunctionType([], MapUnit(1))), FunctionType([], MapUnit(1, 2)))
    assert_infimum_ok(
        (
            FunctionType([MapUnit(1)], TupleType([])),
            FunctionType([MapUnit(2)], TupleType([])),
        ),
        FunctionType([MapType({})], TupleType([])),
    )
    assert_infimum_ok(
        (
            FunctionType([MapUnit(1)], MapUnit(1)),
            FunctionType([MapUnit(2)], MapUnit(2)),
        ),
        FunctionType([MapType({})], MapUnit(1, 2)),
    )
    assert_infimum_ok(
        (
            FunctionType(
                [MapUnit(1), MapUnit(3)],
                MapUnit(1),
            ),
            FunctionType(
                [MapUnit(2), MapUnit(4)],
                MapUnit(2),
            ),
        ),
        FunctionType([MapType({}), MapType({})], MapUnit(1, 2)),
    )
    assert_supremum_error(
        FunctionType([IntegerType()], TupleType([])), FunctionType([FloatType()], TupleType([])), sup=False
    )
    assert_supremum_error(FunctionType([IntegerType()], IntegerType()), FunctionType([IntegerType()], BooleanType()))
    assert_infimum_error(IntegerType(), FunctionType([IntegerType()], IntegerType()))
    assert_infimum_error(IntegerType(), FunctionType([IntegerType(), IntegerType()], IntegerType()))
    assert_infimum_error(
        FunctionType([IntegerType()], IntegerType()), FunctionType([IntegerType(), IntegerType()], IntegerType())
    )


def test_supremum_any():
    assert_supremum_ok((AnyType(), AnyType()), AnyType())
    assert_supremum_ok((IntegerType(), AnyType()), AnyType())
    assert_supremum_ok((AnyType(), IntegerType()), AnyType())
    assert_supremum_ok((FloatType(), AnyType()), AnyType())
    assert_supremum_ok((AnyType(), FloatType()), AnyType())
    assert_supremum_ok((NumberType(), AnyType()), NumberType())
    assert_supremum_ok((AnyType(), NumberType()), NumberType())
    assert_supremum_ok((BooleanType(), AnyType()), AnyType())
    assert_supremum_ok((AnyType(), BooleanType()), AnyType())
    assert_supremum_ok((AtomType(), AnyType()), AtomType())
    assert_supremum_ok((AnyType(), AtomType()), AtomType())
    assert_supremum_ok((AtomLiteralType("a"), AnyType()), AnyType())
    assert_supremum_ok((AnyType(), AtomLiteralType("a")), AnyType())

    assert_supremum_ok((AnyType(), ElistType()), AnyType())
    assert_supremum_ok((ListType(AnyType()), ElistType()), ListType(AnyType()))
    assert_supremum_ok((AnyType(), ListType(IntegerType())), ListType(AnyType()))
    assert_supremum_ok((AnyType(), TupleType([])), TupleType([]))
    assert_supremum_ok((AnyType(), TupleType([IntegerType(), FloatType()])), TupleType([AnyType(), AnyType()]))
    assert_supremum_ok((AnyType(), TupleType([IntegerType(), NumberType()])), TupleType([AnyType(), NumberType()]))
    assert_supremum_ok((AnyType(), MapType({})), MapType({}))
    assert_supremum_ok((AnyType(), MapType({MapKey(1): IntegerType(), MapKey(2): NumberType()})), MapType({}))
    assert_supremum_ok((AnyType(), TupleType([IntegerType(), NumberType()])), TupleType([AnyType(), NumberType()]))
    assert_supremum_ok(
        (AnyType(), FunctionType([IntegerType()], IntegerType())), FunctionType([IntegerType()], AnyType())
    )
    assert_supremum_ok(
        (AnyType(), FunctionType([IntegerType()], NumberType())), FunctionType([IntegerType()], NumberType())
    )
    assert_supremum_ok((AnyType(), FunctionType([NumberType()], IntegerType())), FunctionType([AnyType()], AnyType()))

    assert_supremum_ok((ListType(AnyType()), ElistType()), ListType(AnyType()))
    assert_supremum_ok((ListType(AnyType()), ListType(IntegerType())), ListType(AnyType()))
    assert_supremum_ok(
        (TupleType([AnyType(), IntegerType()]), TupleType([FloatType(), AnyType()])), TupleType([AnyType(), AnyType()])
    )
    assert_supremum_ok(
        (MapType({MapKey(1): AnyType()}), MapType({MapKey(1): IntegerType(), MapKey(2): FloatType()})),
        MapType({MapKey(1): AnyType()}),
    )
    assert_supremum_ok(
        (FunctionType([MapUnit(1), AnyType()], IntegerType()), FunctionType([MapUnit(2), AnyType()], IntegerType())),
        FunctionType([MapUnit(1, 2), AnyType()], IntegerType()),
    )
    assert_supremum_ok(
        (FunctionType([MapUnit(1), AnyType()], IntegerType()), FunctionType([AnyType(), MapUnit(2)], IntegerType())),
        FunctionType([AnyType(), AnyType()], IntegerType()),
    )


def test_infimum_any():
    assert_infimum_ok((AnyType(), AnyType()), AnyType())
    assert_infimum_ok((IntegerType(), AnyType()), IntegerType())
    assert_infimum_ok((AnyType(), IntegerType()), IntegerType())
    assert_infimum_ok((FloatType(), AnyType()), FloatType())
    assert_infimum_ok((AnyType(), FloatType()), FloatType())
    assert_infimum_ok((NumberType(), AnyType()), AnyType())
    assert_infimum_ok((AnyType(), NumberType()), AnyType())
    assert_infimum_ok((BooleanType(), AnyType()), AnyType())
    assert_infimum_ok((AnyType(), BooleanType()), AnyType())
    assert_infimum_ok((AtomType(), AnyType()), AnyType())
    assert_infimum_ok((AnyType(), AtomType()), AnyType())
    assert_infimum_ok((AtomLiteralType("a"), AnyType()), AtomLiteralType("a"))
    assert_infimum_ok((AnyType(), AtomLiteralType("a")), AtomLiteralType("a"))

    assert_infimum_ok((AnyType(), ElistType()), ElistType())
    assert_infimum_ok((ListType(AnyType()), ElistType()), ElistType())
    assert_infimum_ok((AnyType(), ListType(NumberType())), AnyType())
    assert_infimum_ok((AnyType(), TupleType([])), TupleType([]))
    assert_infimum_ok((AnyType(), TupleType([IntegerType(), NumberType()])), TupleType([IntegerType(), AnyType()]))
    assert_infimum_ok((AnyType(), MapType({})), AnyType())
    assert_infimum_ok((AnyType(), FunctionType([], NumberType())), FunctionType([], AnyType()))
    assert_infimum_ok(
        (AnyType(), FunctionType([IntegerType(), NumberType()], NumberType())),
        FunctionType([AnyType(), NumberType()], AnyType()),
    )

    assert_infimum_ok((ListType(AnyType()), ElistType()), ElistType())
    assert_infimum_ok((ListType(AnyType()), ListType(NumberType())), ListType(AnyType()))
    assert_infimum_ok(
        (TupleType([AnyType(), IntegerType()]), TupleType([NumberType(), AnyType()])),
        TupleType([AnyType(), IntegerType()]),
    )
    assert_infimum_ok(
        (MapType({MapKey(1): AnyType()}), MapType({MapKey(1): NumberType(), MapKey(2): FloatType()})),
        MapType({MapKey(1): AnyType(), MapKey(2): FloatType()}),
    )
    assert_infimum_ok(
        (MapType({MapKey(1): AnyType()}), MapType({MapKey(1): AnyType(), MapKey(2): FloatType()})),
        MapType({MapKey(1): AnyType(), MapKey(2): FloatType()}),
    )
    assert_infimum_ok(
        (AnyType(), FunctionType([AnyType(), NumberType()], NumberType())),
        FunctionType([AnyType(), NumberType()], AnyType()),
    )
    assert_infimum_ok(
        (
            FunctionType([IntegerType(), AnyType()], IntegerType()),
            FunctionType([FloatType(), AnyType()], IntegerType()),
        ),
        FunctionType([NumberType(), AnyType()], IntegerType()),
    )
    assert_infimum_ok(
        (
            FunctionType([IntegerType(), AnyType()], IntegerType()),
            FunctionType([AnyType(), FloatType()], IntegerType()),
        ),
        FunctionType([AnyType(), AnyType()], IntegerType()),
    )
