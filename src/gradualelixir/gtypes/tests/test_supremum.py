from collections import OrderedDict

from .. import definitions, utils

integer = "integer"
float = "float"
number = "number"
boolean = "boolean"
any = "any"

def supremum(sigma, tau):
    result = definitions.supremum(
        utils.parse_type(tau), utils.parse_type(sigma)
    )
    if isinstance(result, definitions.SupremumError):
        return result
    return utils.unparse_type(result)


def infimum(sigma, tau):
    result = definitions.infimum(
        utils.parse_type(tau), utils.parse_type(sigma)
    )
    if isinstance(result, definitions.SupremumError):
        return result
    return utils.unparse_type(result)


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
    assert isinstance(result, definitions.SupremumError)
    assert result.args[0] == 'supremum' if sup else 'infimum'


def assert_infimum_error(sigma, tau, sup=False):
    result = infimum(sigma, tau)
    assert isinstance(result, definitions.SupremumError)
    assert result.args[0] == 'supremum' if sup else 'infimum'


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
        (number, ((number,), number))
    )
    assert_supremum_error(
        (integer, ((float,), integer)), (float, (integer, float)),
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
        (sett(1, 2), ((sett(1, 2),), sett(1, 2)))
    )
    assert_infimum_error(
        (sett(1), ((sett(2),), sett(1))), (sett(2), (sett(1), sett(2))),
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
    assert_supremum_ok(({1: sett(1), 2: sett(2)}, {1: sett(3), 2: sett(2)}), {1: sett(), 2: sett(2)})

    assert_supremum_ok(({1: integer, 2: float}, {1: integer, 2: integer}), {1: integer, 2: number})
    assert_supremum_ok(({1: integer, 2: float}, {2: integer, 1: integer}), {1: integer, 2: number})

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

    assert_infimum_ok(({1: sett(3)}, {1: sett(1), 2: sett(2)}), {1: sett(1, 3), 2: sett(2)})
    assert_infimum_ok(({1: sett(1), 2: sett(2)}, {1: sett(3)}), {1: sett(1, 3), 2: sett(2)})
    assert_infimum_ok(({1: sett(1), 2: sett(2)}, {1: sett(3), 2: sett(2)}), {1: sett(1, 3), 2: sett(2)})

    assert_infimum_ok(({1: sett(1), 2: sett(2)}, {1: sett(1), 2: sett(1)}), {1: sett(1), 2: sett(1, 2)})
    assert_infimum_ok(({1: sett(1), 2: sett(2)}, {2: sett(1), 1: sett(1)}), {1: sett(1), 2: sett(1, 2)})

    assert_infimum_error({1: integer}, {1: float})
    assert_infimum_error({1: integer, 2: integer}, {1: float, 2: integer})
    assert_infimum_error({1: integer, 2: integer}, {1: integer, 2: float})


def test_supremum_function():
    assert_supremum_ok((('->', integer), ('->', integer)), ('->', integer))
    assert_supremum_ok((('->', integer), ('->', float)), ('->', number))
    assert_supremum_ok((('->', float), ('->', integer)), ('->', number))
    assert_supremum_ok(((sett(1), '->', ()), (sett(2), '->', ())), (sett(1, 2), '->', ()))
    assert_supremum_ok(((sett(1), '->', sett(1)), (sett(2), '->', sett(2))), (sett(1, 2), '->', sett()))
    assert_supremum_ok(
        ((sett(1), sett(3), '->', sett(1)), (sett(2), sett(4), '->', sett(2))), 
        (sett(1, 2), sett(3, 4), '->', sett())
    )
    assert_supremum_error(('->', ()), (float, '->', ()))
    assert_infimum_error((integer, '->', ()), (boolean, '->', ()), sup=True)
    assert_infimum_error((integer, '->', integer), (integer, '->', boolean))
    assert_supremum_error(('->', integer), (integer, '->', integer))
    assert_supremum_error(('->', integer), (integer, integer, '->', integer))
    assert_supremum_error((integer, '->', integer), (integer, integer, '->', integer))


def test_infimum_function():
    assert_infimum_ok((('->', integer), ('->', integer)), ('->', integer))
    assert_infimum_ok((('->', sett(1)), ('->', sett(2))), ('->', sett(1, 2)))
    assert_infimum_ok((('->', sett(2)), ('->', sett(1))), ('->', sett(1, 2)))
    assert_infimum_ok(((sett(1), '->', ()), (sett(2), '->', ())), (sett(), '->', ()))
    assert_infimum_ok(((sett(1), '->', sett(1)), (sett(2), '->', sett(2))), (sett(), '->', sett(1, 2)))
    assert_infimum_ok(
        ((sett(1), sett(3), '->', sett(1)), (sett(2), sett(4), '->', sett(2))), 
        (sett(), sett(), '->', sett(1, 2))
    )
    assert_supremum_error((integer, '->', ()), (float, '->', ()), sup=False)
    assert_supremum_error((integer, '->', integer), (integer, '->', boolean))
    assert_infimum_error(('->', integer), (integer, '->', integer))
    assert_infimum_error(('->', integer), (integer, integer, '->', integer))
    assert_infimum_error((integer, '->', integer), (integer, integer, '->', integer))


def test_supremum_any():
    assert_supremum_ok((any, any), any)
    assert_supremum_ok((integer, any), any)
    assert_supremum_ok((any, integer), any)
    assert_supremum_ok(((any, integer), (float, any)), (any, any))
    assert_supremum_ok(({1: any}, {1: integer, 2: float}), {1: any})
    assert_supremum_ok(
        ((sett(1), any, '->', integer), (sett(2), any, '->', integer)),
        (sett(1, 2), any, '->', integer)
    )
    assert_supremum_ok(
        ((any, sett(1), '->', integer), (sett(2), any, '->', integer)),
        (any, any, '->', integer)
    )


def test_infimum_any():
    assert_infimum_ok((any, any), any)
    assert_infimum_ok((integer, any), any)
    assert_infimum_ok((any, integer), any)
    assert_infimum_ok(((any, integer), (float, any)), (any, any))
    assert_infimum_ok(({1: any}, {1: integer, 2: float}), {1: any, 2: float})
    assert_infimum_ok(({1: any}, {1: any, 2: float}), {1: any, 2: float})
    assert_infimum_ok(
        ((sett(1), any, '->', integer), (sett(2), any, '->', integer)),
        (sett(), any, '->', integer)
    )
    assert_infimum_ok(
        ((any, sett(1), '->', integer), (sett(2), any, '->', integer)),
        (any, any, '->', integer)
    )
