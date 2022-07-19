import typing as t

from gradualelixir import gtypes

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


def ordinal(n: int):
    return str(n) + {1: "st", 2: "nd", 3: "rd"}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")


def enumerate_list(items: t.List[str]) -> str:
    if len(items) == 0:
        return ""
    if len(items) == 1:
        return str(items[0])
    else:
        return ",".join([str(item) for item in items[:-1]]) + " and " + str(items[-1])


long_line = "".join(["-" for _ in range(200)])
