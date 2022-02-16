import random
import typing as t

from gradualelixir.gtypes import definitions as types
from gradualelixir.gtypes.generators import generator_from_cache
from gradualelixir.gtypes.utils import flatten
from gradualelixir.pattern.utils import parse_pattern


def patterns_generator(**kwargs) -> t.List[t.List[types.Type]]:
    identifiers = ["x", "y", "z"]

    base_patterns = flatten(
        [
            ["_"],
            identifiers,
            [f"^{x}" for x in identifiers],
        ]
    )

    composite_patterns_1 = flatten(
        [
            [()],  # type: ignore
            [(x,) for x in base_patterns],
            [(x, y) for x in base_patterns for y in base_patterns],
            [[]],  # type: ignore
            [[x] for x in base_patterns],
            [[x, y] for x in base_patterns for y in base_patterns],
            [
                [x, y, z]
                for x in base_patterns
                for y in base_patterns
                for z in base_patterns
                if random.randint(0, 10) < 2
            ],
            [dict([])],
            [
                dict(list(zip(keys, values)))
                for keys in [[1], [2], [3]]
                for values in [[x] for x in base_patterns]
                if random.randint(0, 10) < 3
            ],
            [
                dict(list(zip(keys, values)))
                for keys in [[1, 2], [1, 3], [2, 3]]
                for values in [[x, y] for x in base_patterns for y in base_patterns]
                if random.randint(0, 10) < 3
            ],
            [
                dict(list(zip([1, 2, 3], values)))
                for values in [
                    [x, y, z]
                    for x in base_patterns
                    for y in base_patterns
                    for z in base_patterns
                ]
                if random.randint(0, 10) < 2
            ],
        ]
    )
    composite_patterns_2 = flatten(
        [
            [(x,) for x in composite_patterns_1],
            [[x] for x in composite_patterns_1],
            [
                [x, y]
                for x in base_patterns + composite_patterns_1
                for y in base_patterns + composite_patterns_1
            ],
            [
                dict(list(zip(keys, values)))
                for keys in [[1], [2], [3]]
                for values in [[x] for x in composite_patterns_1]
                if random.randint(0, 10) < 2
            ],
            [
                dict(list(zip(keys, values)))
                for keys in [[1, 2], [1, 3], [2, 3]]
                for values in [
                    [x, y]
                    for x in base_patterns + composite_patterns_1
                    for y in base_patterns + composite_patterns_1
                ]
                if random.randint(0, 10) < 2
            ],
        ]
    )

    return [
        [parse_pattern(x) for x in base_patterns],
        [parse_pattern(x) for x in composite_patterns_1],
        [parse_pattern(x) for x in composite_patterns_2],
    ]


def generate_patterns():
    return generator_from_cache(function=patterns_generator, force_recreate=False)
