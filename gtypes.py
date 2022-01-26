from dataclasses import dataclass

from enum import Enum
import typing as t


def concat(lists):
    res = ''
    for list in lists:
        res += list
    return res


class TypeExceptionEnum(Enum):
    supremum_does_not_exist_for_any_and_something_else = 'supremum_does_not_exist_for_any_and_something_else'
    supremum_does_not_exist_for_infimum_incompatibility = 'supremum_does_not_exist_for_infimum_incompatibility'
    cannot_apply_grounding = "cannot_apply_grounding"
    type_is_not_base = "type_is_not_base"


class TypeException(Exception):
    reason: TypeExceptionEnum
    args: t.Tuple[object]

    def __init__(self, reason: TypeExceptionEnum, *args):
        self.reason = reason
        self.args = args


class Type:
    pass


@dataclass
class IntegerType(Type):

    def __str__(self):
        return 'integer'

    def __hash__(self):
        return 1


@dataclass
class FloatType(Type):

    def __str__(self):
        return 'float'

    def __hash__(self):
        return 2


@dataclass
class NumberType(Type):

    def __str__(self):
        return 'number'

    def __hash__(self):
        return 3


@dataclass
class TermType(Type):

    def __str__(self):
        return 'term'

    def __hash__(self):
        return 4


@dataclass
class AnyType(Type):

    def __str__(self):
        return 'any'


@dataclass
class TupleType(Type):
    types: t.List[Type]

    def __str__(self):
        return '{' + ','.join([str(ty) for ty in self.types]) + '}'


@dataclass
class ListType(Type):
    type: Type

    def __str__(self):
        return '[' + str(self.type) + ']'


@dataclass
class ElistType(Type):

    def __str__(self):
        return '[]'


@dataclass
class FunctionType(Type):
    arg_types: t.List[Type]
    ret_type: Type

    def __str__(self):
        return f'({",".join([str(ty) for ty in self.arg_types])}) -> {str(self.ret_type)}'


@dataclass
class MapType(Type):
    map_type: t.Dict[int, Type]

    def __str__(self):
        keys = self.map_type.keys()
        str_values = [str(v) for v in self.map_type.values()]
        return '%{' + ','.join([f'{k}: {v}' for (k, v) in zip(keys, str_values)]) + '}'


def grounding(tau: t.Union[AnyType, TermType], sigma: Type) -> Type:
    if isinstance(sigma, ListType):
        return ListType(tau)
    elif isinstance(sigma, TupleType):
        return TupleType([tau for _ in sigma.types])
    elif isinstance(sigma, MapType):
        return MapType({k: tau for k in sigma.map_type})
    elif isinstance(sigma, FunctionType) and isinstance(tau, AnyType):
        return FunctionType([tau for _ in sigma.arg_types], tau)
    else:
        raise TypeException(reason=TypeExceptionEnum.cannot_apply_grounding)


def is_base_subtype(tau: Type, sigma: Type) -> bool:
    if tau not in base_types or sigma not in base_types:
        raise TypeException(reason=TypeExceptionEnum.type_is_not_base)
    if any(
            [
                tau == sigma,
                isinstance(sigma, TermType),
                isinstance(tau, IntegerType) and isinstance(sigma, NumberType),
                isinstance(tau, FloatType) and isinstance(sigma, NumberType)
            ]
    ):
        return True
    return False


def is_static_type(tau: Type) -> bool:
    if isinstance(tau, AnyType):
        return False
    elif tau in base_types:
        return True
    elif isinstance(tau, ElistType):
        return True
    elif isinstance(tau, ListType):
        return is_static_type(tau.type)
    elif isinstance(tau, TupleType):
        return all([
            is_static_type(sigma) for sigma in tau.types
        ])
    elif isinstance(tau, MapType):
        return all([
            is_static_type(sigma) for sigma in tau.map_type.values()
        ])
    elif isinstance(tau, FunctionType):
        return all([
            is_static_type(sigma) for sigma in tau.arg_types
        ]) and is_static_type(tau.ret_type)


def is_subtype(tau: Type, sigma: Type) -> bool:
    if isinstance(tau, AnyType) or isinstance(sigma, AnyType):
        return isinstance(tau, AnyType) and isinstance(sigma, AnyType)
    if isinstance(tau, TermType):
        return isinstance(sigma, TermType)
    if isinstance(sigma, TermType):
        return is_static_type(tau)
    if tau in base_types and sigma in base_types:
        return is_base_subtype(tau, sigma)
    if isinstance(tau, ElistType) and isinstance(sigma, ElistType):
        return True
    if isinstance(tau, ElistType) and isinstance(sigma, ListType):
        return True
    if isinstance(tau, ListType) and isinstance(sigma, ElistType):
        return False
    if isinstance(tau, ListType) and isinstance(sigma, ListType):
        return is_subtype(tau.type, sigma.type)
    if isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        return len(tau.types) == len(sigma.types) and all([
            is_subtype(tau.types[i], sigma.types[i]) for i in range(len(tau.types))
        ])
    if isinstance(tau, MapType) and isinstance(sigma, MapType):
        return all([(k in tau.map_type) for k in sigma.map_type]) and all([
            is_subtype(tau.map_type[k], sigma.map_type[k]) for k in sigma.map_type
        ])
    if isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        return is_subtype(
            TupleType(types=sigma.arg_types), TupleType(types=tau.arg_types)
        ) and is_subtype(tau.ret_type, sigma.ret_type)
    return False


def is_materialization(tau: Type, sigma: Type) -> bool:
    if isinstance(tau, AnyType):
        return True
    elif tau in base_types:
        return sigma == tau
    elif isinstance(tau, ListType):
        return isinstance(sigma, ListType) and is_materialization(tau.type, sigma.type)
    elif isinstance(tau, TupleType):
        return isinstance(sigma, TupleType) and len(tau.types) == len(sigma.types) and all([
            is_materialization(tau.types[i], sigma.types[i]) for i in range(len(tau.types))
        ])
    elif isinstance(tau, MapType):
        return isinstance(sigma, MapType) and set(tau.map_type.keys()) == set(sigma.map_type.keys()) and all([
            is_materialization(tau.map_type[k], sigma.map_type[k]) for k in tau.map_type.keys()
        ])
    elif isinstance(tau, FunctionType):
        return isinstance(sigma, FunctionType) and len(tau.arg_types) == len(sigma.arg_types) and all([
            is_materialization(tau.arg_types[i], sigma.arg_types[i]) for i in range(len(tau.arg_types))
        ]) and is_materialization(tau.ret_type, sigma.ret_type)


def supremum(tau: Type, sigma: Type) -> Type:
    if tau == sigma:
        return tau
    if AnyType() in [tau, sigma]:
        raise TypeException(reason=TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else)
    elif TermType() in [tau, sigma]:
        return TermType()
    elif (tau, sigma) in [
        (IntegerType(), FloatType()), (IntegerType(), NumberType()), (FloatType(), NumberType()),
        (FloatType(), IntegerType()), (NumberType(), IntegerType()), (NumberType(), FloatType()),
    ]:
        return NumberType()
    elif ElistType() in [tau, sigma]:
        if isinstance(tau, ListType):
            return tau
        elif isinstance(sigma, ListType):
            return sigma
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return ListType(supremum(tau.type, sigma.type))
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            return TupleType([
                supremum(tau.types[i], sigma.types[i]) for i in range(len(tau.types))
            ])
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        inter_keys = [k for k in tau.map_type if k in sigma.map_type]
        return MapType({k: supremum(tau.map_type[k], sigma.map_type[k]) for k in inter_keys})
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            try:
                return FunctionType([
                        infimum(tau.arg_types[i], sigma.arg_types[i]) for i in range(len(tau.arg_types))
                    ], supremum(tau.ret_type, sigma.ret_type))
            except TypeException as e:
                if e.reason == TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility:
                    return TermType()
                raise e
    return TermType()


def infimum(tau: Type, sigma: Type) -> Type:
    if tau == sigma:
        return tau
    elif AnyType() in [tau, sigma]:
        raise TypeException(reason=TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else)
    elif TermType() in [tau, sigma]:
        return tau if isinstance(sigma, TermType) else sigma
    elif tau in [IntegerType(), FloatType()] and sigma in [IntegerType(), FloatType()]:
        raise TypeException(reason=TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility)
    elif tau in [IntegerType(), NumberType()] and sigma in [IntegerType(), NumberType()]:
        return IntegerType()
    elif tau in [FloatType(), NumberType()] and sigma in [FloatType(), NumberType()]:
        return FloatType()
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return ListType(infimum(tau.type, sigma.type))
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            return TupleType([
                infimum(tau.types[i], sigma.types[i]) for i in range(len(tau.types))
            ])
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        union_keys = [k for k in tau.map_type if k not in sigma.map_type] + list(sigma.map_type)
        map_type = {
            k:  (
                    tau.map_type[k] if (k not in sigma.map_type) else
                    sigma.map_type[k] if (k not in tau.map_type) else
                    infimum(tau.map_type[k], sigma.map_type[k])
            )
            for k in union_keys
        }
        return MapType(map_type)
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            return FunctionType([
                    supremum(tau.arg_types[i], sigma.arg_types[i]) for i in range(len(tau.arg_types))
            ], infimum(tau.ret_type, sigma.ret_type))
    raise TypeException(reason=TypeExceptionEnum.supremum_does_not_exist_for_infimum_incompatibility)


def lazy_equate(tau: Type, sigma: Type, modality: bool) -> t.Tuple[Type, Type]:
    if AnyType() in [tau, sigma]:
        if modality:
            return (tau, tau) if sigma == AnyType() else (sigma, sigma)
        else:
            return AnyType(), AnyType()
    if isinstance(tau, ListType) and isinstance(sigma, ListType):
        if ListType(type=AnyType()) in [tau, sigma] and ElistType() in [tau, sigma]:
            if modality:
                return ElistType(), ElistType()
            else:
                return ListType(type=AnyType()), ListType(type=AnyType())
        else:
            tau_1, sigma_1 = lazy_equate(tau.type, sigma.type, modality)
            return ListType(type=tau_1), ListType(type=sigma_1)
    if isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            aux = [lazy_equate(tau.types[i], sigma.types[i], modality) for i in range(len(tau.types))]
            return (
                TupleType(types=[p[0] for p in aux]),
                TupleType(types=[p[1] for p in aux])
            )
    if isinstance(tau, MapType) and isinstance(sigma, MapType):
        keys = [k for k in sigma.map_type if k in tau.map_type]
        aux = {k: lazy_equate(tau.map_type[k], sigma.map_type[k], modality) for k in keys}
        return (
            MapType(map_type={
                k: aux[k][0] if k in keys else tau.map_type[k] for k in tau.map_type
            }),
            MapType(map_type={
                k: aux[k][1] if k in keys else sigma.map_type[k] for k in sigma.map_type
            })
        )

    if isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        taus, sigmas = lazy_equate(TupleType(types=tau.arg_types), TupleType(types=sigma.arg_types), modality)
        tau_0, sigma_0 = lazy_equate(tau.ret_type, sigma.ret_type, modality)
        return (
            FunctionType(arg_types=taus.types, ret_type=tau_0),  # type: ignore
            FunctionType(arg_types=sigmas.types, ret_type=sigma_0)  # type: ignore
        )
    return tau, sigma


base_types: t.List[t.Type[Type]] = [IntegerType(), FloatType(), NumberType(), TermType()]  # type: ignore
