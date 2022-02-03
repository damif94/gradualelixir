import pickle

from gtypes import *
import typing as t
import random
from utils import parse_type, flatten

seeds = {
    'static': ['integer', 'float', 'number', 'term', 'none'],
    'gradual': ['integer', 'float', 'number', 'term', 'none', 'any'],  # type: ignore
}


def type_builder(cls: t.Type[Type], arity, *args):
    if cls == ElistType:
        return ElistType()
    elif cls == ListType:
        return ListType(type=args[0])
    elif cls == TupleType:
        return TupleType(types=list(args)[:arity])
    elif cls == MapType:
        keys, args = list(args)[:arity], list(args)[arity:]
        return MapType(map_type=dict(zip(keys, args)))
    elif cls == FunctionType:
        return FunctionType(arg_types=list(args)[:arity - 1], ret_type=args[arity - 1])


def generate_types(base='static') -> t.List[t.List[Type]]:
    base_types = seeds[base]
    composite_types_1 = flatten([
        [()],
        [(x,) for x in base_types],
        [(x, y) for x in base_types for y in base_types],
        [
            dict([])
        ],
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
            for values in [[x, y, z] for x in base_types for y in base_types for z in base_types]
            if random.randint(0, 10) < 5
        ],
        [('->', x) for x in base_types],
        [(x, '->', y) for x in base_types for y in base_types],
        [(x, y, '->', z) for x in base_types for y in base_types for z in base_types],
    ])

    composite_types_2 = flatten([
        [()],
        [(x,) for x in composite_types_1],
        [(x, y) for x in base_types for y in composite_types_1],
        [(x, y) for x in composite_types_1 for y in base_types if random.randint(0, 10) == 2],
        [
            dict(list(zip(keys, values)))
            for keys in [[1], [2], [3]]
            for values in [[x] for x in composite_types_1]
            if random.randint(0, 10) == 2
        ],
        [
            dict(list(zip(keys, values)))
            for keys in [[1, 2], [1, 3], [2, 3]]
            for values in [[x, y] for x in base_types for y in composite_types_1]
            if random.randint(0, 10) == 1
        ],
        [
            dict(list(zip([1, 2, 3], values)))
            for values in [[x, y] for x in composite_types_1 for y in composite_types_1]
            if random.randint(0, 10) == 1
        ],
        [('->', x) for x in composite_types_1 if random.randint(0, 10) == 2],
        [(x, '->', y) for x in base_types for y in composite_types_1 if random.randint(0, 10) == 2],
        [(x, '->', y) for x in composite_types_1 for y in base_types if random.randint(0, 10) == 2],
        [(x, '->', y) for x in composite_types_1 for y in composite_types_1 if random.randint(0, 10) == 0],
        [(x, '->', y) for x in composite_types_1 for y in composite_types_1 if random.randint(0, 10) == 0],
        [(x, y, '->', z) for x in composite_types_1 for y in base_types for z in base_types if
         random.randint(0, 10) == 1],
        [(x, y, '->', z) for x in base_types for y in composite_types_1 for z in base_types if
         random.randint(0, 10) == 1],
        [(x, y, '->', z) for x in base_types for y in base_types for z in composite_types_1 if
         random.randint(0, 10) == 1],
        [(x, y, '->', z) for x in composite_types_1 for y in composite_types_1 for z in base_types if
         random.randint(0, 10) == 1],
        [(x, y, '->', z) for x in composite_types_1 for y in base_types for z in composite_types_1 if
         random.randint(0, 10) == 1],
        [(x, y, '->', z) for x in base_types for y in composite_types_1 for z in composite_types_1 if
         random.randint(0, 10) == 1],
    ])

    print(len(composite_types_2))
    return [
        [parse_type(x) for x in base_types],
        [parse_type(x) for x in composite_types_1],
        [parse_type(x) for x in composite_types_2]
    ]


def types_generator(base='static', force_recreate=False):
    if not force_recreate:
        try:
            f = open(f'types/{base}.pickle', 'rb')
            types_lists = pickle.load(f)
            f.close()
        except FileNotFoundError:
            return types_generator(base=base, force_recreate=False)
    else:
        types_lists = generate_types(base=base)
        f = open(f'types/{base}.pickle', 'wb')
        pickle.dump(types_lists, f)
        f.close()

    types_lengths = [len(types_list) for types_list in types_lists]

    def generator(weights=None):
        nonlocal types_lists, types_lengths
        while True:
            level = random.choices(population=[0, 1, 2], weights=weights or [10, 30, 60])[0]
            yield types_lists[level][random.randint(0, types_lengths[level] - 1)]

    return generator


def generate_subtypes(base='static', polarity='+'):

    def generator(weights=None):
        gen = types_generator(base=base)(weights)
        while True:
            tau, sigma = next(gen), next(gen)
            if (
                polarity == '+' and is_subtype(tau, sigma)
                or
                polarity == '-' and is_subtype(sigma, tau)
            ):
                yield tau, sigma

    return generator


def generate_msubtypes(base='static', polarity='+'):

    def generator(weights=None):
        gen = types_generator(base=base)(weights)
        while True:
            tau, sigma = next(gen), next(gen)
            if (
                polarity == '+' and is_msubtype_plus(tau, sigma)
                or
                polarity == '-' and is_msubtype_minus(tau, sigma)
            ):
                yield tau, sigma

    return generator


def generate_materializations(base='gradual'):

    def generator(weights=None):
        gen = types_generator(base=base)(weights)
        while True:
            tau, sigma = next(gen), next(gen)
            if is_materialization(tau, sigma):
                yield tau, sigma

    return generator
