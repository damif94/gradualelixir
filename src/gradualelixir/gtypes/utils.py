import typing as t

from . import definitions

S = t.TypeVar("S")
T = t.TypeVar("T")


def parse_type(x):
    if isinstance(x, bool):
        return definitions.AtomLiteralType(atom="true" if x else "false")
    if isinstance(x, str):
        if x.startswith(":"):
            return definitions.AtomLiteralType(atom=x[1:])
        if x == "boolean":
            return definitions.BooleanType()
        if x == "atom":
            return definitions.AtomType()
        if x == "integer":
            return definitions.IntegerType()
        if x == "float":
            return definitions.FloatType()
        if x == "number":
            return definitions.NumberType()
        if x == "any":
            return definitions.AnyType()
    if isinstance(x, tuple):
        if len(x) >= 2 and x[-2] == "->":
            return definitions.FunctionType(
                [parse_type(y) for y in x[:-2]], parse_type(x[-1])
            )
        else:
            return definitions.TupleType([parse_type(y) for y in x])
    if isinstance(x, dict):
        return definitions.MapType({k: parse_type(x[k]) for k in x})
    if isinstance(x, list):
        if len(x) == 0:
            return definitions.ElistType()
        assert len(x) == 1
        return definitions.ListType(parse_type(x[0]))


def unparse_type(x):
    if isinstance(x, definitions.BooleanType):
        return "boolean"
    if isinstance(x, definitions.AtomLiteralType):
        if x.atom in ["true", "false"]:
            return x.atom == "true"
        return str(x)
    if isinstance(x, definitions.AtomType):
        return "atom"
    if isinstance(x, definitions.IntegerType):
        return "integer"
    if isinstance(x, definitions.FloatType):
        return "float"
    if isinstance(x, definitions.NumberType):
        return "number"
    if isinstance(x, definitions.AnyType):
        return "any"
    if isinstance(x, definitions.ElistType):
        return []
    elif isinstance(x, definitions.ListType):
        return [unparse_type(x.type)]
    if isinstance(x, definitions.TupleType):
        return tuple([unparse_type(y) for y in x.types])
    if isinstance(x, definitions.FunctionType):
        return tuple(
            [unparse_type(y) for y in x.arg_types] + ["->"] + [unparse_type(x.ret_type)]
        )
    else:
        assert isinstance(x, definitions.MapType)
        return {k: unparse_type(x.map_type[k]) for k in x.map_type}


def flatten(x: t.List[t.List[T]]) -> t.List[T]:
    return [item for sublist in x for item in sublist]


def merge_dicts(
    d1: t.Dict[S, T], d2: t.Dict[S, T], f: t.Callable[[T, T], T]
) -> t.Dict[S, T]:
    result = d1.copy()
    for k, v in d2.items():
        result[k] = v if k not in d1 else f(d1[k], v)
    return result


def unzip(x: t.List[t.Tuple[S, T]]) -> t.Tuple[t.List[S], t.List[T]]:
    result: t.Tuple[t.List[S], t.List[T]] = ([], [])
    for pair in x:
        result[0].append(pair[0])
        result[1].append(pair[1])
    return result
