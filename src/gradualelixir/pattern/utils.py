from collections import OrderedDict

from . import definitions


def parse_pattern(x):
    if isinstance(x, int):
        return definitions.IntegerPattern(value=x)
    elif isinstance(x, float):
        return definitions.FloatPattern(value=x)
    elif isinstance(x, bool):
        return definitions.AtomPattern(value="true" if x else "false")
    elif isinstance(x, str):
        if x.startswith(":"):
            return definitions.AtomPattern(value=x[1:])
        if x == "_":
            return definitions.WildPattern()
        elif x.startswith("^"):
            return definitions.PinIdentPattern(identifier=x[1:])
        else:
            return definitions.IdentPattern(identifier=x)
    elif isinstance(x, tuple):
        return definitions.TuplePattern([parse_pattern(y) for y in x])
    if isinstance(x, dict):
        map = OrderedDict()
        for k, v in x.items():
            map[k] = parse_pattern(v)
        return definitions.MapPattern(map)
    else:
        assert isinstance(x, list)
        if len(x) == 0:
            return definitions.ElistPattern()
        else:
            return definitions.ListPattern(parse_pattern(x[0]), parse_pattern(x[1:]))
