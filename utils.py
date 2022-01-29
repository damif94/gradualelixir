import gtypes


def parse_type(x):
    if x == 'integer':
        return gtypes.IntegerType()
    if x == 'float':
        return gtypes.FloatType()
    if x == 'number':
        return gtypes.NumberType()
    if x == 'term':
        return gtypes.TermType()
    if x == 'none':
        return gtypes.NoneType()
    if x == 'any':
        return gtypes.AnyType()
    if type(x) == tuple:
        if len(x) >= 2 and x[-2] == '->':
            return gtypes.FunctionType([parse_type(y) for y in x[:-2]], parse_type(x[-1]))
        else:
            return gtypes.TupleType([parse_type(y) for y in x])
    if type(x) == dict:
        return gtypes.MapType({k: parse_type(x[k]) for k in x})
    if type(x) == list:
        if len(x) == 0:
            return gtypes.ElistType()
        if len(x) == 1:
            return gtypes.ListType(parse_type(x[0]))


def flatten(t):
    return [item for sublist in t for item in sublist]
