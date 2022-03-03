import typing as t
from collections import OrderedDict

from gradualelixir import pattern
from gradualelixir import types as gtypes

T = t.TypeVar("T")


class Bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def parse_key(x):
    if isinstance(x, bool):
        return gtypes.MapKey("true" if x else "false")
    return gtypes.MapKey(x)


def parse_type(x):
    if isinstance(x, bool):
        return gtypes.AtomLiteralType(atom="true" if x else "false")
    if isinstance(x, str):
        if x.startswith(":"):
            return gtypes.AtomLiteralType(atom=x[1:])
        if x == "boolean":
            return gtypes.BooleanType()
        if x == "atom":
            return gtypes.AtomType()
        if x == "integer":
            return gtypes.IntegerType()
        if x == "float":
            return gtypes.FloatType()
        if x == "number":
            return gtypes.NumberType()
        if x == "any":
            return gtypes.AnyType()
    if isinstance(x, tuple):
        if len(x) >= 2 and x[-2] == "->":
            return gtypes.FunctionType([parse_type(y) for y in x[:-2]], parse_type(x[-1]))
        else:
            return gtypes.TupleType([parse_type(y) for y in x])
    if isinstance(x, dict):
        return gtypes.MapType({parse_key(k): parse_type(x[k]) for k in x})
    if isinstance(x, list):
        if len(x) == 0:
            return gtypes.ElistType()
        assert len(x) == 1
        return gtypes.ListType(parse_type(x[0]))


def unparse_type(x):
    if isinstance(x, gtypes.BooleanType):
        return "boolean"
    if isinstance(x, gtypes.AtomLiteralType):
        if x.atom in ["true", "false"]:
            return x.atom == "true"
        return str(x)
    if isinstance(x, gtypes.AtomType):
        return "atom"
    if isinstance(x, gtypes.IntegerType):
        return "integer"
    if isinstance(x, gtypes.FloatType):
        return "float"
    if isinstance(x, gtypes.NumberType):
        return "number"
    if isinstance(x, gtypes.AnyType):
        return "any"
    if isinstance(x, gtypes.ElistType):
        return []
    elif isinstance(x, gtypes.ListType):
        return [unparse_type(x.type)]
    if isinstance(x, gtypes.TupleType):
        return tuple([unparse_type(y) for y in x.types])
    if isinstance(x, gtypes.FunctionType):
        return tuple([unparse_type(y) for y in x.arg_types] + ["->"] + [unparse_type(x.ret_type)])
    else:
        assert isinstance(x, gtypes.MapType)
        return {k: unparse_type(x.map_type[k]) for k in x.map_type}


def parse_pattern(x):
    if isinstance(x, bool):
        return pattern.AtomLiteralPattern(value="true" if x else "false")
    elif isinstance(x, int):
        return pattern.IntegerPattern(value=x)
    elif isinstance(x, float):
        return pattern.FloatPattern(value=x)
    elif isinstance(x, str):
        if x.startswith(":"):
            return pattern.AtomLiteralPattern(value=x[1:])
        if x == "_":
            return pattern.WildPattern()
        elif x.startswith("^"):
            return pattern.PinIdentPattern(identifier=x[1:])
        else:
            return pattern.IdentPattern(identifier=x)
    elif isinstance(x, tuple):
        return pattern.TuplePattern([parse_pattern(y) for y in x])
    if isinstance(x, dict):
        return pattern.MapPattern(OrderedDict([(parse_key(k), parse_pattern(v)) for k, v in x.items()]))
    else:
        assert isinstance(x, list)
        if len(x) == 0:
            return pattern.ElistPattern()
        else:
            if len(x) == 3 and x[1] == "|":
                return pattern.ListPattern(parse_pattern(x[0]), parse_pattern(x[2]))
            return pattern.ListPattern(parse_pattern(x[0]), parse_pattern(x[1:]))


def flatten(x: t.List[t.List[T]]) -> t.List[T]:
    return [item for sublist in x for item in sublist]


def ordinal(n: int):
    return str(n) + {1: "st", 2: "nd", 3: "rd"}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")


def enumerate_list(items: t.List[str]) -> str:
    if len(items) == 0:
        return ""
    if len(items) == 1:
        return str(items[0])
    else:
        return ",".join([str(item) for item in items[:-1]]) + " and " + str(items[-1])


long_line = "--------------------------------------------------------------------------------------------"
