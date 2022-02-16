import pickle
import random
import typing as t

import rpyc
from gradualelixir.gtypes.definitions import (
    FunctionType,
    ListType,
    MapType,
    TupleType,
    Type,
    is_subtype,
)
from gradualelixir.gtypes.utils import flatten, parse_type, unzip

T = t.TypeVar("T")


seeds = {
    "static": ["integer", "float", "number", "term", "none"],
    "gradual": ["integer", "float", "number", "term", "none", "any"],  # type: ignore
}


def type_builder(cls: t.Type[Type], arity: int, *args: t.Any) -> Type:
    if cls == ListType:
        return ListType(type=args[0])
    elif cls == TupleType:
        return TupleType(types=list(args)[:arity])
    elif cls == MapType:
        keys, args = list(args)[:arity], tuple(args)[arity:]
        return MapType(map_type=dict(zip(keys, args)))
    elif cls == FunctionType:
        return FunctionType(arg_types=list(args)[: arity - 1], ret_type=args[arity - 1])
    else:
        raise ValueError("cannot call type_builder without a type constructor")


def types_generator(base="static") -> t.List[t.List[Type]]:
    base_types = seeds[base]
    composite_types_1 = flatten(  # type: ignore
        [
            [()],  # type: ignore
            [(x,) for x in base_types],
            [(x, y) for x in base_types for y in base_types],
            [dict([])],
            [
                dict(list(zip(keys, values)))
                for keys in [[1], [2], [3]]
                for values in [[x] for x in base_types]
                if random.randint(0, 10) < 5
            ],
            [
                dict(list(zip(keys, values)))
                for keys in [[1, 2], [1, 3], [2, 3]]
                for values in [[x, y] for x in base_types for y in base_types]
                if random.randint(0, 10) < 5
            ],
            [
                dict(list(zip([1, 2, 3], values)))
                for values in [
                    [x, y, z]
                    for x in base_types
                    for y in base_types
                    for z in base_types
                ]
                if random.randint(0, 10) < 5
            ],
            [("->", x) for x in base_types],
            [(x, "->", y) for x in base_types for y in base_types],
            [
                (x, y, "->", z)
                for x in base_types
                for y in base_types
                for z in base_types
            ],
        ]
    )

    composite_types_2 = flatten(  # type: ignore
        [
            [()],  # type: ignore
            [(x,) for x in composite_types_1],
            [(x, y) for x in base_types for y in composite_types_1],
            [(x, y) for x in composite_types_1 for y in base_types],
            [
                dict(list(zip(keys, values)))
                for keys in [[1], [2], [3]]
                for values in [[x] for x in composite_types_1]
                if random.randint(0, 10) < 2
            ],
            [
                dict(list(zip(keys, values)))
                for keys in [[1, 2], [1, 3], [2, 3]]
                for values in [[x, y] for x in base_types for y in composite_types_1]
                if random.randint(0, 10) < 1
            ],
            [
                dict(list(zip(keys, values)))
                for keys in [[1, 2], [1, 3], [2, 3]]
                for values in [
                    [x, y] for x in composite_types_1 for y in composite_types_1
                ]
                if random.randint(0, 10) < 1
            ],
            [("->", x) for x in composite_types_1 if random.randint(0, 10) < 2],
            [
                (x, "->", y)
                for x in base_types
                for y in composite_types_1
                if random.randint(0, 10) < 2
            ],
            [
                (x, "->", y)
                for x in composite_types_1
                for y in base_types
                if random.randint(0, 10) < 2
            ],
            [
                (x, "->", y)
                for x in composite_types_1
                for y in composite_types_1
                if random.randint(0, 10) < 1
            ],
            [
                (x, y, "->", z)
                for x in composite_types_1
                for y in base_types
                for z in base_types
                if random.randint(0, 10) < 1
            ],
            [
                (x, y, "->", z)
                for x in base_types
                for y in composite_types_1
                for z in base_types
                if random.randint(0, 10) < 1
            ],
            [
                (x, y, "->", z)
                for x in base_types
                for y in base_types
                for z in composite_types_1
                if random.randint(0, 10) < 1
            ],
            [
                (x, y, "->", z)
                for x in composite_types_1
                for y in composite_types_1
                for z in base_types
                if random.randint(0, 10) < 1
            ],
            [
                (x, y, "->", z)
                for x in composite_types_1
                for y in base_types
                for z in composite_types_1
                if random.randint(0, 10) < 1
            ],
            [
                (x, y, "->", z)
                for x in base_types
                for y in composite_types_1
                for z in composite_types_1
                if random.randint(0, 10) < 1
            ],
        ]
    )

    return [
        [parse_type(x) for x in base_types],
        [parse_type(x) for x in composite_types_1],
        [parse_type(x) for x in composite_types_2],
    ]


def materializations_generator(**kwargs) -> t.List[t.List[t.Tuple[Type, Type]]]:
    base_relation = [("any", x) for x in seeds["static"]] + [
        (x, x) for x in seeds["gradual"]
    ]
    composite_relation_1 = flatten(  # type: ignore
        [
            [((), ())],  # type: ignore
            [((x[0],), (x[1],)) for x in base_relation],
            [
                ((x[0], y[0]), (x[1], y[1]))
                for x in base_relation
                for y in base_relation
                if random.randint(0, 100) < 5
            ],
            [(dict([]), dict([]))],
            [
                (
                    dict(list(zip(keys, unzip(values)[0]))),
                    dict(list(zip(keys, unzip(values)[1]))),
                )
                for keys in [[1], [2], [3]]
                for values in [[x] for x in base_relation]
                if random.randint(0, 100) < 5
            ],
            [
                (
                    dict(list(zip(keys, unzip(values)[0]))),
                    dict(list(zip(keys, unzip(values)[1]))),
                )
                for keys in [[1, 2], [1, 3], [2, 3]]
                for values in [[x, y] for x in base_relation for y in base_relation]
                if random.randint(0, 100) < 5
            ],
            [
                (
                    dict(list(zip([1, 2, 3], unzip(values)[0]))),
                    dict(list(zip([1, 2, 3], unzip(values)[1]))),
                )
                for values in [
                    [x, y, z]
                    for x in base_relation
                    for y in base_relation
                    for z in base_relation
                ]
                if random.randint(0, 100) < 5
            ],
            [(("->", x[0]), ("->", x[1])) for x in base_relation],
            [
                ((x[0], "->", y[0]), (x[1], "->", y[1]))
                for x in base_relation
                for y in base_relation
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in base_relation
                for y in base_relation
                for z in base_relation
                if random.randint(0, 100) < 5
            ],
        ]
    )
    composite_relation_types_1 = list(
        [x[0] for x in composite_relation_1 if random.randint(0, 4) < 1]
    )
    composite_relation_1 = composite_relation_1 + [("any", x) for x in composite_relation_types_1]  # type: ignore
    composite_relation_2 = flatten(  # type: ignore
        [
            [((), ())],  # type: ignore
            [((x[0],), (x[1],)) for x in composite_relation_1],
            [
                ((x[0], y[0]), (x[1], y[1]))
                for x in base_relation
                for y in composite_relation_1
            ],
            [
                ((x[0], y[0]), (x[1], y[1]))
                for x in composite_relation_1
                for y in base_relation
            ],
            [(dict([]), dict([]))],
            [
                (
                    dict(list(zip(keys, unzip(values)[0]))),
                    dict(list(zip(keys, unzip(values)[1]))),
                )
                for keys in [[1], [2], [3]]
                for values in [[x] for x in base_relation]
                if random.randint(0, 10) < 2
            ],
            [
                (
                    dict(list(zip(keys, unzip(values)[0]))),
                    dict(list(zip(keys, unzip(values)[1]))),
                )
                for keys in [[1, 2], [1, 3], [2, 3]]
                for values in [
                    [x, y] for x in base_relation for y in composite_relation_1
                ]
                if random.randint(0, 10) < 1
            ],
            [
                (
                    dict(list(zip(keys, unzip(values)[0]))),
                    dict(list(zip(keys, unzip(values)[1]))),
                )
                for keys in [[1, 2], [1, 3], [2, 3]]
                for values in [
                    [x, y] for x in composite_relation_1 for y in composite_relation_1
                ]
                if random.randint(0, 10) < 1
            ],
            [
                (("->", x[0]), ("->", x[1]))
                for x in composite_relation_1
                if random.randint(0, 10) < 2
            ],
            [
                ((x[0], "->", y[0]), (x[1], "->", y[1]))
                for x in base_relation
                for y in composite_relation_1
                if random.randint(0, 10) < 2
            ],
            [
                ((x[0], "->", y[0]), (x[1], "->", y[1]))
                for x in composite_relation_1
                for y in base_relation
                if random.randint(0, 10) < 2
            ],
            [
                ((x[0], "->", y[0]), (x[1], "->", y[1]))
                for x in composite_relation_1
                for y in composite_relation_1
                if random.randint(0, 10) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in composite_relation_1
                for y in base_relation
                for z in base_relation
                if random.randint(0, 50) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in base_relation
                for y in composite_relation_1
                for z in base_relation
                if random.randint(0, 50) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in base_relation
                for y in base_relation
                for z in composite_relation_1
                if random.randint(0, 50) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in composite_relation_1
                for y in composite_relation_1
                for z in base_relation
                if random.randint(0, 50) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in composite_relation_1
                for y in base_relation
                for z in composite_relation_1
                if random.randint(0, 50) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in base_relation
                for y in composite_relation_1
                for z in composite_relation_1
                if random.randint(0, 50) < 1
            ],
        ]
    )
    composite_relation_types_2 = list(
        [x[0] for x in composite_relation_2 if random.randint(0, 20) < 1]
    )
    composite_relation_2 = composite_relation_2 + [("any", x) for x in composite_relation_types_2]  # type: ignore

    return [
        [(parse_type(x[0]), parse_type(x[1])) for x in base_relation],
        [(parse_type(x[0]), parse_type(x[1])) for x in composite_relation_1],
        [(parse_type(x[0]), parse_type(x[1])) for x in composite_relation_2],
    ]


def subtypes_generator(base, **kwargs) -> t.List[t.List[t.Tuple[Type, Type]]]:
    base_relation = (
        [(x, x) for x in seeds[base]]
        + [(x, "term") for x in seeds["static"]]
        + [("none", x) for x in seeds["static"]]
    )
    base_relation_types = list(set([x[0] for x in base_relation]))
    composite_relation_1 = flatten(  # type: ignore
        [
            [((), ())],  # type: ignore
            [((x[0],), (x[1],)) for x in base_relation],
            [
                ((x[0], y[0]), (x[1], y[1]))
                for x in base_relation
                for y in base_relation
                if random.randint(0, 50) < 1
            ],
            [(dict([]), dict([]))],
            [
                (dict([]), dict([(key, x)]))
                for key in [1, 2]
                for x in base_relation_types
                if random.randint(0, 100) < 1
            ],
            [
                (dict([]), dict([(1, x), (2, y)]))
                for x, y in [
                    (x, y) for x in base_relation_types for y in base_relation_types
                ]
                if random.randint(0, 100) < 1
            ],
            [
                (dict([(key, x[0])]), dict([(key, x[1])]))
                for key in [1, 2]
                for x in base_relation
                if random.randint(0, 100) < 1
            ],
            [
                (dict([(key1, x[0])]), dict([(key1, x[1]), (key2, y)]))
                for key1, key2 in [(1, 2), (2, 1)]
                for x in base_relation
                for y in base_relation_types
                if random.randint(0, 100) < 1
            ],
            [
                (dict([(1, x[0]), (2, y[0])]), dict([(1, x[1]), (2, y[1])]))
                for x in base_relation
                for y in base_relation
                if random.randint(0, 100) < 1
            ],
            [(("->", x[0]), ("->", x[1])) for x in base_relation],
            [
                ((x[0], "->", y[0]), (x[1], "->", y[1]))
                for x in base_relation
                for y in base_relation
            ],
            [
                ((x[1], y[1], "->", z[0]), (x[0], y[0], "->", z[1]))
                for x in base_relation
                for y in base_relation
                for z in base_relation
                if random.randint(0, 100) < 1
            ],
        ]
    )

    composite_relation_types_1 = list(
        [x[0] for x in composite_relation_1 if random.randint(0, 4) < 1]
    )
    composite_relation_1 = composite_relation_1 + flatten([[(x, "term"), ("none", x)] for x in composite_relation_types_1])  # type: ignore

    composite_relation_2 = flatten(  # type: ignore
        [
            [((x[0],), (x[1],)) for x in composite_relation_1],  # type: ignore
            [
                ((x[0], y[0]), (x[1], y[1]))
                for x in base_relation
                for y in composite_relation_1
            ],
            [
                ((x[0], y[0]), (x[1], y[1]))
                for x in composite_relation_1
                for y in base_relation
            ],
            [
                ((x[0], y[0]), (x[1], y[1]))
                for x in composite_relation_1
                for y in composite_relation_1
                if random.randint(0, 50) < 1
            ],
            [
                (dict([]), dict([(key, x)]))
                for key in [1, 2]
                for x in composite_relation_types_1
                if random.randint(0, 100) < 1
            ],
            [
                (dict([]), dict([(1, x), (2, y)]))
                for x, y in (
                    [
                        (x, y)
                        for x in base_relation_types
                        for y in composite_relation_types_1
                    ]
                    + [
                        (x, y)
                        for x in composite_relation_types_1
                        for y in base_relation_types
                    ]
                    + [
                        (x, y)
                        for x in composite_relation_types_1
                        for y in composite_relation_types_1
                    ]
                )
                if random.randint(0, 100) < 1
            ],
            [
                (dict([(key, x[0])]), dict([(key, x[1])]))
                for key in [1, 2]
                for x in composite_relation_1
                if random.randint(0, 100) < 1
            ],
            [
                (dict([(key1, x[0])]), dict([(key1, x[1]), (key2, y)]))
                for key1, key2 in [(1, 2), (2, 1)]
                for x, y in (
                    [(x, y) for x in base_relation for y in composite_relation_types_1]
                    + [
                        (x, y)
                        for x in composite_relation_1
                        for y in base_relation_types
                    ]
                    + [
                        (x, y)
                        for x in composite_relation_1
                        for y in composite_relation_types_1
                    ]
                )
                if random.randint(0, 100) < 1
            ],
            [
                (dict([(1, x[0]), (2, y[0])]), dict([(1, x[1]), (2, y[1])]))
                for x, y in (
                    [(x, y) for x in base_relation for y in composite_relation_1]
                    + [(x, y) for x in composite_relation_1 for y in base_relation]
                    + [
                        (x, y)
                        for x in composite_relation_1
                        for y in composite_relation_1
                    ]
                )
                if random.randint(0, 100) < 1
            ],
            [
                (("->", x[0]), ("->", x[1]))
                for x in composite_relation_1
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], "->", y[0]), (x[1], "->", y[1]))
                for x in base_relation
                for y in composite_relation_1
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], "->", y[0]), (x[1], "->", y[1]))
                for x in composite_relation_1
                for y in base_relation
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], "->", y[0]), (x[1], "->", y[1]))
                for x in composite_relation_1
                for y in composite_relation_1
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in composite_relation_1
                for y in base_relation
                for z in base_relation
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in base_relation
                for y in composite_relation_1
                for z in base_relation
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in base_relation
                for y in base_relation
                for z in composite_relation_1
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in composite_relation_1
                for y in composite_relation_1
                for z in base_relation
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in composite_relation_1
                for y in base_relation
                for z in composite_relation_1
                if random.randint(0, 100) < 1
            ],
            [
                ((x[0], y[0], "->", z[0]), (x[1], y[1], "->", z[1]))
                for x in base_relation
                for y in composite_relation_1
                for z in composite_relation_1
                if random.randint(0, 100) < 1
            ],
        ]
    )

    composite_relation_types_2 = list(
        [x[0] for x in composite_relation_2 if random.randint(0, 20) < 1]
    )
    composite_relation_2 = composite_relation_2 + flatten([[(x, "term"), ("none", x)] for x in composite_relation_types_2])  # type: ignore

    return [
        [(parse_type(x[0]), parse_type(x[1])) for x in base_relation],
        [(parse_type(x[0]), parse_type(x[1])) for x in composite_relation_1],
        [(parse_type(x[0]), parse_type(x[1])) for x in composite_relation_2],
    ]


def generator_from_cache(function, base=None, force_recreate=False):
    cache_dir = "/Users/damian/PycharmProjects/gradual-elixir/.cache/"
    suffix = f"__{base}" if base else ""
    if not force_recreate:
        try:
            f = open(f"{cache_dir}{function.__name__}{suffix}.pickle", "rb")
            types_lists = pickle.load(f)
            f.close()
        except FileNotFoundError:
            return generator_from_cache(function, base=base, force_recreate=True)
    else:
        types_lists = function(base=base)
        f = open(f"{cache_dir}{function.__name__}{suffix}.pickle", "wb")
        pickle.dump(types_lists, f)
        f.close()

    types_lengths = [len(types_list) for types_list in types_lists]

    def generator(weights=None):
        nonlocal types_lists, types_lengths
        while True:
            level = random.choices(
                population=[0, 1, 2], weights=weights or [10, 30, 60]
            )[0]
            yield types_lists[level][random.randint(0, types_lengths[level] - 1)]

    return generator


def generate_types(base="static"):
    return generator_from_cache(
        function=types_generator, base=base, force_recreate=False
    )


def generate_subtypes(base="static", polarity="+"):
    def generator(weights=None):
        gen = generate_types(base=base)(weights)
        while True:
            tau, sigma = next(gen), next(gen)
            if (
                polarity == "+"
                and is_subtype(tau, sigma)
                or polarity == "-"
                and is_subtype(sigma, tau)
            ):
                yield tau, sigma

    return generator


def generate_materializations():
    return generator_from_cache(
        function=materializations_generator, force_recreate=False
    )


#
# def generate_subtypes(base='static', remote=False):
#     if remote:
#         return generator_from_remote(base=base, function=subtypes_generator, relation_arity=2)
#     return generator_from_cache(base=base, function=subtypes_generator, force_recreate=False)
#
