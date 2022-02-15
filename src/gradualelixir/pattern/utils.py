from . import definitions
from collections import OrderedDict


def format_error(error: definitions.PatternError, padding='') -> str:
    bullet = ''
    if error.bullet is not None:
        bullet = format_error(error.bullet, padding + '  ')
    return f'{error.msg}\n' + (f'{padding}> {bullet}' if bullet else '')


def parse_pattern(x):
    if isinstance(x, int):
        return definitions.IntegerPattern(value=x)
    elif isinstance(x, float):
        return definitions.FloatPattern(value=x)
    elif isinstance(x, str):
        if x == '_':
            return definitions.WildPattern()
        elif x.startswith('^'):
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
