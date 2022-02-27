from collections import OrderedDict

from gradualelixir import types, utils

integer = "integer"
float = "float"
number = "number"
boolean = "boolean"
any = "any"
atom = "atom"
true = True
false = False


def supremum(sigma, tau):
    result = types.supremum(utils.parse_type(tau), utils.parse_type(sigma))
    if isinstance(result, types.SupremumError):
        return result
    return utils.unparse_type(result)


def infimum(sigma, tau):
    result = types.infimum(utils.parse_type(tau), utils.parse_type(sigma))
    if isinstance(result, types.SupremumError):
        return result
    return utils.unparse_type(result)


def is_subtype(tau, sigma):
    return types.is_subtype(utils.parse_type(tau), utils.parse_type(sigma))


def sett(*args):
    args = list(args)
    args.sort()
    aux = OrderedDict()
    for k in args:
        aux[k] = ()
    return aux


def assert_supremum_ok(input, output):
    sigma, tau = input
    assert supremum(sigma, tau) == output


def assert_infimum_ok(input, output):
    sigma, tau = input
    assert infimum(sigma, tau) == output


def assert_supremum_error(sigma, tau, sup=True):
    result = supremum(sigma, tau)
    assert isinstance(result, types.SupremumError)
    assert result.args[0] == "supremum" if sup else "infimum"


def assert_infimum_error(sigma, tau, sup=False):
    result = infimum(sigma, tau)
    assert isinstance(result, types.SupremumError)
    assert result.args[0] == "supremum" if sup else "infimum"


def test_subtype_base():
    assert is_subtype(integer, integer)
    assert is_subtype(integer, number)
    assert is_subtype(float, float)
    assert is_subtype(float, number)
    assert is_subtype(":a", atom)
    assert is_subtype(true, boolean)
    assert is_subtype(false, boolean)
    assert is_subtype(true, atom)
    assert is_subtype(false, atom)
    assert is_subtype(boolean, atom)

    assert not is_subtype(number, integer)
    assert not is_subtype(number, float)
    assert not is_subtype(atom, ":a")
    assert not is_subtype(boolean, true)
    assert not is_subtype(boolean, false)
    assert not is_subtype(atom, true)
    assert not is_subtype(atom, false)
    assert not is_subtype(atom, boolean)

    assert not is_subtype(atom, integer)
    assert not is_subtype(integer, atom)
    assert not is_subtype(atom, float)
    assert not is_subtype(float, atom)
    assert not is_subtype(atom, number)
    assert not is_subtype(number, atom)
    assert not is_subtype(boolean, integer)
    assert not is_subtype(integer, boolean)
    assert not is_subtype(boolean, float)
    assert not is_subtype(float, boolean)
    assert not is_subtype(boolean, number)
    assert not is_subtype(number, boolean)


def test_subtype_list():
    assert is_subtype([], [])
    assert is_subtype([], [true])
    assert is_subtype([], [(integer,)])
    assert is_subtype([], [any])
    assert is_subtype([], [(any,)])

    assert not is_subtype([true], [])
    assert not is_subtype([(integer,)], [])
    assert not is_subtype([any], [])
    assert not is_subtype([(any,)], [])

    assert is_subtype([true], [boolean])
    assert is_subtype([integer], [integer])
    assert is_subtype([integer], [number])
    assert is_subtype([integer], [any])
    assert is_subtype([any], [integer])
    assert is_subtype([(integer, integer)], [(number, any)])

    assert not is_subtype([boolean], [true])
    assert not is_subtype([(boolean,)], [boolean])
    assert not is_subtype([(number, integer)], [(integer, any)])
    assert not is_subtype([(number, any)], [(integer, integer)])


def test_subtype_tuple():
    assert is_subtype((), ())
    assert is_subtype((integer,), (integer,))
    assert is_subtype((integer, float), (integer, float))

    assert is_subtype((any,), (integer,))
    assert is_subtype((integer,), (number,))
    assert is_subtype((integer, float), (number, float))
    assert is_subtype((integer, float), (any, float))
    assert is_subtype((integer, float), (number, any))
    assert is_subtype((any, float), (number, any))

    assert not is_subtype((), (integer,))
    assert not is_subtype((integer,), ())
    assert not is_subtype((integer,), (integer, float))
    assert not is_subtype((integer, float), (integer,))
    assert not is_subtype((), (integer, float))
    assert not is_subtype((integer, float), ())

    assert not is_subtype((integer,), (float,))
    assert not is_subtype((float,), (integer,))
    assert not is_subtype((integer, any), (float, any))


def test_subtype_map():
    assert is_subtype({}, {})
    assert is_subtype({1: integer}, {1: integer})
    assert is_subtype({1: integer, 2: float}, {1: integer, 2: float})

    assert is_subtype({1: integer}, {})
    assert is_subtype({1: any}, {})
    assert is_subtype({1: (integer, any)}, {})
    assert is_subtype({1: integer}, {1: number})
    assert is_subtype({1: integer, 2: (boolean, any)}, {})
    assert is_subtype({1: integer, 2: (boolean, any)}, {1: number})
    assert is_subtype({1: integer, 2: (boolean, any)}, {2: (boolean, number)})

    assert not is_subtype({1: number}, {1: integer})
    assert not is_subtype({1: number}, {1: boolean})
    assert not is_subtype({1: (number, any)}, {1: (integer, any)})

    assert not is_subtype({}, {1: integer})
    assert not is_subtype({}, {1: any})
    assert not is_subtype({1: integer}, {1: any, 2: any})
    assert not is_subtype({1: integer}, {1: any, 2: number})
    assert not is_subtype({}, {1: any, 2: any})
    assert not is_subtype({}, {1: any, 2: number})


def test_subtype_function():
    assert is_subtype(("->", integer), ("->", integer))
    assert is_subtype((boolean, "->", integer), (boolean, "->", integer))
    assert is_subtype((boolean, float, "->", integer), (boolean, float, "->", integer))

    assert is_subtype(("->", integer), ("->", number))
    assert is_subtype(("->", any), ("->", number))
    assert is_subtype(("->", integer), ("->", any))
    assert is_subtype((boolean, "->", integer), (boolean, "->", number))
    assert is_subtype((atom, "->", integer), (boolean, "->", integer))
    assert is_subtype((atom, "->", integer), (boolean, "->", number))
    assert is_subtype((atom, "->", integer), (boolean, "->", any))
    assert is_subtype((any, "->", integer), (boolean, "->", number))
    assert is_subtype((any, "->", integer), (boolean, "->", any))
    assert is_subtype(
        ((any, integer), "->", [integer]), ((boolean, integer), "->", [any])
    )

    assert not is_subtype(("->", integer), (any, "->", integer))
    assert not is_subtype(("->", integer), (boolean, "->", integer))
    assert not is_subtype((any, "->", integer), ("->", integer))
    assert not is_subtype((boolean, "->", integer), ("->", integer))
    assert not is_subtype((any, "->", integer), (boolean, integer, "->", integer))
    assert not is_subtype((boolean, integer, "->", integer), (any, "->", integer))
    assert not is_subtype((boolean, integer, "->", integer), (integer, "->", integer))

    assert not is_subtype(("->", number), ("->", integer))
    assert not is_subtype((boolean, "->", integer), (atom, "->", number))
    assert not is_subtype((boolean, "->", integer), ([boolean], "->", integer))
    assert not is_subtype((atom, "->", number), (boolean, "->", integer))
    assert not is_subtype((atom, "->", number), (boolean, "->", (any,)))


def test_supremum_base():
    assert_supremum_ok((integer, integer), integer)
    assert_supremum_ok((integer, number), number)
    assert_supremum_ok((number, integer), number)
    assert_supremum_ok((float, float), float)
    assert_supremum_ok((float, number), number)
    assert_supremum_ok((number, float), number)
    assert_supremum_ok((integer, float), number)
    assert_supremum_ok((boolean, boolean), boolean)
    assert_supremum_error(boolean, integer)
    assert_supremum_error(integer, boolean)
    assert_supremum_error(boolean, float)
    assert_supremum_error(float, boolean)
    assert_supremum_error(boolean, number)
    assert_supremum_error(number, boolean)

    assert_supremum_ok((true, true), true)
    assert_supremum_ok((false, false), false)
    assert_supremum_ok((true, false), boolean)
    assert_supremum_ok((false, true), boolean)
    assert_supremum_ok((true, boolean), boolean)
    assert_supremum_ok((boolean, true), boolean)
    assert_supremum_ok((false, boolean), boolean)
    assert_supremum_ok((boolean, false), boolean)

    assert_supremum_ok((":a", ":a"), ":a")
    assert_supremum_ok((":b", ":b"), ":b")
    assert_supremum_ok((":a", ":b"), atom)
    assert_supremum_ok((":b", ":a"), atom)

    assert_supremum_ok((true, ":a"), atom)
    assert_supremum_ok((false, ":a"), atom)
    assert_supremum_ok((":a", true), atom)
    assert_supremum_ok((":a", false), atom)

    assert_supremum_ok((":a", boolean), atom)
    assert_supremum_ok((boolean, ":a"), atom)


def test_infimum_base():
    assert_infimum_ok((integer, integer), integer)
    assert_infimum_ok((integer, number), integer)
    assert_infimum_ok((number, integer), integer)
    assert_infimum_ok((float, float), float)
    assert_infimum_ok((float, number), float)
    assert_infimum_ok((number, float), float)
    assert_infimum_error(integer, float)
    assert_infimum_error(float, integer)
    assert_infimum_error(integer, boolean)
    assert_infimum_error(boolean, integer)
    assert_infimum_error(number, boolean)
    assert_infimum_error(boolean, number)

    assert_infimum_ok((true, true), true)
    assert_infimum_ok((false, false), false)
    assert_infimum_error(true, false)
    assert_infimum_error(false, true)
    assert_infimum_error((true, boolean), true)
    assert_infimum_error((boolean, true), true)
    assert_infimum_error((false, boolean), false)
    assert_infimum_error((boolean, false), false)

    assert_infimum_ok((":a", ":a"), ":a")
    assert_infimum_ok((":b", ":b"), ":b")
    assert_infimum_error(":a", ":b")
    assert_infimum_error(":b", ":a")

    assert_infimum_error(true, ":a")
    assert_infimum_error(false, ":a")
    assert_infimum_error(":a", true)
    assert_infimum_error(":a", false)

    assert_infimum_error(":a", boolean)
    assert_infimum_error(boolean, ":a")


def test_supremum_list():
    assert_supremum_ok(([], [integer]), [integer])
    assert_supremum_ok(([integer], []), [integer])
    assert_supremum_ok(([integer], [integer]), [integer])
    assert_supremum_ok(([integer], [float]), [number])

    assert_supremum_ok(([], [[float]]), [[float]])
    assert_supremum_ok(([[]], [[float]]), [[float]])
    assert_supremum_ok(([[integer]], [[float]]), [[number]])

    assert_supremum_error([integer], [boolean])


def test_infimum_list():
    assert_infimum_ok(([], [integer]), [])
    assert_infimum_ok(([integer], []), [])
    assert_infimum_ok(([integer], [integer]), [integer])
    assert_infimum_ok(([sett(1)], [sett(2)]), [sett(1, 2)])

    assert_infimum_ok(([], [[float]]), [])
    assert_infimum_ok(([[]], [[float]]), [[]])
    assert_infimum_ok(([[sett(1)]], [[sett(2)]]), [[sett(1, 2)]])
    assert_infimum_error([integer], [float])


def test_supremum_tuple():
    assert_supremum_ok(((), ()), ())
    assert_supremum_ok(((integer,), (float,)), (number,))

    assert_supremum_ok(((integer, integer), (float, integer)), (number, integer))
    assert_supremum_ok(((integer, integer), (integer, float)), (integer, number))
    assert_supremum_ok(((integer, float), (integer, integer)), (integer, number))
    assert_supremum_error((integer,), (boolean,))
    assert_supremum_error((integer, integer), (boolean, integer))
    assert_supremum_error((boolean, integer), (integer, integer))
    assert_supremum_error((boolean, boolean), (integer, integer))

    assert_supremum_error((), (integer,))
    assert_supremum_error((), (integer, float))
    assert_supremum_error((integer,), (integer, float))
    assert_supremum_error((float,), (integer, float))

    assert_supremum_ok(
        ((integer, ((float,), integer)), (float, ((integer,), float))),
        (number, ((number,), number)),
    )
    assert_supremum_error(
        (integer, ((float,), integer)),
        (float, (integer, float)),
    )


def test_infimum_tuple():
    assert_infimum_ok(((), ()), ())
    assert_infimum_ok(((sett(1),), (sett(2),)), (sett(1, 2),))

    assert_infimum_ok(((sett(1), sett(1)), (sett(2), sett(1))), (sett(1, 2), sett(1)))
    assert_infimum_ok(((sett(1), sett(1)), (sett(1), sett(2))), (sett(1), sett(1, 2)))
    assert_infimum_ok(((sett(1), sett(2)), (sett(1), sett(1))), (sett(1), sett(1, 2)))
    assert_infimum_error((integer,), (float,))
    assert_infimum_error((integer, integer), (float, integer))
    assert_infimum_error((float, integer), (integer, integer))
    assert_infimum_error((float, float), (integer, integer))

    assert_infimum_error((), (integer,))
    assert_infimum_error((), (integer, float))
    assert_infimum_error((integer,), (integer, float))
    assert_infimum_error((float,), (integer, float))

    assert_infimum_ok(
        ((sett(1), ((sett(2),), sett(1))), (sett(2), ((sett(1),), sett(2)))),
        (sett(1, 2), ((sett(1, 2),), sett(1, 2))),
    )
    assert_infimum_error(
        (sett(1), ((sett(2),), sett(1))),
        (sett(2), (sett(1), sett(2))),
    )


def test_supremum_map():
    assert_supremum_ok((sett(), sett()), sett())
    assert_supremum_ok((sett(1), sett()), sett())
    assert_supremum_ok((sett(), sett(1)), sett())
    assert_supremum_ok((sett(1, 3), sett(2, 3)), sett(3))

    assert_supremum_ok(({1: integer}, {2: float}), {})
    assert_supremum_ok(({1: integer}, {1: float}), {1: number})
    assert_supremum_ok(({1: {1: integer}}, {1: {1: float}}), {1: {1: number}})
    assert_supremum_ok(({1: {2: integer}}, {1: {2: float}}), {1: {2: number}})

    assert_supremum_ok(({1: sett(3)}, {1: sett(1), 2: sett(2)}), {1: sett()})
    assert_supremum_ok(({1: sett(1), 2: sett(2)}, {1: sett(3)}), {1: sett()})
    assert_supremum_ok(
        ({1: sett(1), 2: sett(2)}, {1: sett(3), 2: sett(2)}), {1: sett(), 2: sett(2)}
    )

    assert_supremum_ok(
        ({1: integer, 2: float}, {1: integer, 2: integer}), {1: integer, 2: number}
    )
    assert_supremum_ok(
        ({1: integer, 2: float}, {2: integer, 1: integer}), {1: integer, 2: number}
    )

    assert_supremum_error({1: integer}, {1: boolean})
    assert_supremum_error({1: integer, 2: integer}, {1: boolean, 2: integer})
    assert_supremum_error({1: integer, 2: integer}, {1: integer, 2: boolean})


def test_infimum_map():
    assert_infimum_ok((sett(), sett()), sett())
    assert_infimum_ok((sett(1), sett()), sett(1))
    assert_infimum_ok((sett(), sett(1)), sett(1))
    assert_infimum_ok((sett(1, 3), sett(2, 3)), sett(1, 2, 3))

    assert_infimum_ok(({1: sett(1)}, {2: sett(2)}), {1: sett(1), 2: sett(2)})
    assert_infimum_ok(({1: sett(1)}, {1: sett(2)}), {1: sett(1, 2)})
    assert_infimum_ok(({1: {1: sett(1)}}, {1: {1: sett(2)}}), {1: {1: sett(1, 2)}})
    assert_infimum_ok(({1: {2: sett(1)}}, {1: {2: sett(2)}}), {1: {2: sett(1, 2)}})

    assert_infimum_ok(
        ({1: sett(3)}, {1: sett(1), 2: sett(2)}), {1: sett(1, 3), 2: sett(2)}
    )
    assert_infimum_ok(
        ({1: sett(1), 2: sett(2)}, {1: sett(3)}), {1: sett(1, 3), 2: sett(2)}
    )
    assert_infimum_ok(
        ({1: sett(1), 2: sett(2)}, {1: sett(3), 2: sett(2)}),
        {1: sett(1, 3), 2: sett(2)},
    )

    assert_infimum_ok(
        ({1: sett(1), 2: sett(2)}, {1: sett(1), 2: sett(1)}),
        {1: sett(1), 2: sett(1, 2)},
    )
    assert_infimum_ok(
        ({1: sett(1), 2: sett(2)}, {2: sett(1), 1: sett(1)}),
        {1: sett(1), 2: sett(1, 2)},
    )

    assert_infimum_error({1: integer}, {1: float})
    assert_infimum_error({1: integer, 2: integer}, {1: float, 2: integer})
    assert_infimum_error({1: integer, 2: integer}, {1: integer, 2: float})


def test_supremum_function():
    assert_supremum_ok((("->", integer), ("->", integer)), ("->", integer))
    assert_supremum_ok((("->", integer), ("->", float)), ("->", number))
    assert_supremum_ok((("->", float), ("->", integer)), ("->", number))
    assert_supremum_ok(
        ((sett(1), "->", ()), (sett(2), "->", ())), (sett(1, 2), "->", ())
    )
    assert_supremum_ok(
        ((sett(1), "->", sett(1)), (sett(2), "->", sett(2))), (sett(1, 2), "->", sett())
    )
    assert_supremum_ok(
        ((sett(1), sett(3), "->", sett(1)), (sett(2), sett(4), "->", sett(2))),
        (sett(1, 2), sett(3, 4), "->", sett()),
    )
    assert_supremum_error(("->", ()), (float, "->", ()))
    assert_infimum_error((integer, "->", ()), (boolean, "->", ()), sup=True)
    assert_infimum_error((integer, "->", integer), (integer, "->", boolean))
    assert_supremum_error(("->", integer), (integer, "->", integer))
    assert_supremum_error(("->", integer), (integer, integer, "->", integer))
    assert_supremum_error((integer, "->", integer), (integer, integer, "->", integer))


def test_infimum_function():
    assert_infimum_ok((("->", integer), ("->", integer)), ("->", integer))
    assert_infimum_ok((("->", sett(1)), ("->", sett(2))), ("->", sett(1, 2)))
    assert_infimum_ok((("->", sett(2)), ("->", sett(1))), ("->", sett(1, 2)))
    assert_infimum_ok(((sett(1), "->", ()), (sett(2), "->", ())), (sett(), "->", ()))
    assert_infimum_ok(
        ((sett(1), "->", sett(1)), (sett(2), "->", sett(2))), (sett(), "->", sett(1, 2))
    )
    assert_infimum_ok(
        ((sett(1), sett(3), "->", sett(1)), (sett(2), sett(4), "->", sett(2))),
        (sett(), sett(), "->", sett(1, 2)),
    )
    assert_supremum_error((integer, "->", ()), (float, "->", ()), sup=False)
    assert_supremum_error((integer, "->", integer), (integer, "->", boolean))
    assert_infimum_error(("->", integer), (integer, "->", integer))
    assert_infimum_error(("->", integer), (integer, integer, "->", integer))
    assert_infimum_error((integer, "->", integer), (integer, integer, "->", integer))


def test_supremum_any():
    assert_supremum_ok((any, any), any)
    assert_supremum_ok((integer, any), any)
    assert_supremum_ok((any, integer), any)
    assert_supremum_ok((float, any), any)
    assert_supremum_ok((any, float), any)
    assert_supremum_ok((number, any), number)
    assert_supremum_ok((any, number), number)
    assert_supremum_ok((boolean, any), any)
    assert_supremum_ok((any, boolean), any)
    assert_supremum_ok((atom, any), atom)
    assert_supremum_ok((any, atom), atom)
    assert_supremum_ok((":a", any), any)
    assert_supremum_ok((any, ":a"), any)

    assert_supremum_ok(((any, integer), (float, any)), (any, any))
    assert_supremum_ok(({1: any}, {1: integer, 2: float}), {1: any})
    assert_supremum_ok(
        ((sett(1), any, "->", integer), (sett(2), any, "->", integer)),
        (sett(1, 2), any, "->", integer),
    )
    assert_supremum_ok(
        ((any, {1: integer}, "->", integer), ({2: any}, any, "->", integer)),
        ({2: any}, {1: integer}, "->", integer),
    )


def test_infimum_any():
    assert_infimum_ok((any, any), any)
    assert_infimum_ok((integer, any), any)
    assert_infimum_ok((any, integer), any)
    assert_infimum_ok(((any, integer), (float, any)), (any, any))
    assert_infimum_ok(({1: any}, {1: integer, 2: float}), {1: any, 2: float})
    assert_infimum_ok(({1: any}, {1: any, 2: float}), {1: any, 2: float})
    assert_infimum_ok(
        ((sett(1), any, "->", integer), (sett(2), any, "->", integer)),
        (sett(), any, "->", integer),
    )
    assert_infimum_ok(
        ((any, sett(1), "->", integer), (sett(2), any, "->", integer)),
        (any, any, "->", integer),
    )
