import typing as t
from dataclasses import dataclass
from enum import Enum

from . import utils


class Type:
    pass


@dataclass
class IntegerType(Type):
    def __str__(self):
        return "integer"

    def __hash__(self):
        return 1


@dataclass
class FloatType(Type):
    def __str__(self):
        return "float"

    def __hash__(self):
        return 2


@dataclass
class NumberType(Type):
    def __str__(self):
        return "number"

    def __hash__(self):
        return 3


@dataclass
class TermType(Type):
    def __str__(self):
        return "term"

    def __hash__(self):
        return 4


@dataclass
class NoneType(Type):
    def __str__(self):
        return "none"


@dataclass
class AnyType(Type):
    def __str__(self):
        return "any"


@dataclass
class TupleType(Type):
    types: t.List[Type]

    def __str__(self):
        return "{" + ",".join([str(ty) for ty in self.types]) + "}"


@dataclass
class ListType(Type):
    type: Type

    def __str__(self):
        return "[" + str(self.type) + "]"


@dataclass
class MapType(Type):

    map_type: t.Dict[int, Type]

    def __str__(self):
        keys = self.map_type.keys()
        str_values = [str(v) for v in self.map_type.values()]
        return "%{" + ",".join([f"{k}: {v}" for (k, v) in zip(keys, str_values)]) + "}"


@dataclass
class FunctionType(Type):
    arg_types: t.List[Type]
    ret_type: Type

    def __str__(self):
        return (
            f'({",".join([str(ty) for ty in self.arg_types])}) -> {str(self.ret_type)}'
        )


class TypeExceptionEnum(Enum):
    supremum_does_not_exist_for_any_and_something_else = (
        "supremum_does_not_exist_for_any_and_something_else"
    )
    cannot_apply_grounding = "cannot_apply_grounding"
    type_is_not_base = "type_is_not_base"


class TypeException(Exception):
    reason: TypeExceptionEnum
    args: t.Any

    def __init__(self, reason: TypeExceptionEnum, *args: t.Any):
        self.reason = reason
        self.args = args


base_types: t.List[Type] = [
    IntegerType(),
    FloatType(),
    NumberType(),
    TermType(),
    NoneType(),
]


def grounding(tau: t.Union[AnyType, TermType, NoneType], sigma: Type) -> Type:
    if isinstance(sigma, ListType):
        return ListType(tau)
    elif isinstance(sigma, TupleType):
        return TupleType([tau for _ in sigma.types])
    elif isinstance(sigma, MapType):
        return MapType({k: tau for k in sigma.map_type})
    elif isinstance(sigma, FunctionType):
        tau1 = tau
        if isinstance(tau, TermType):
            tau1 = NoneType()
        elif isinstance(tau, NoneType):
            tau1 = TermType()
        return FunctionType([tau1 for _ in sigma.arg_types], tau)
    else:
        raise TypeException(reason=TypeExceptionEnum.cannot_apply_grounding)


def is_base_subtype(tau: Type, sigma: Type) -> bool:
    if tau not in base_types or sigma not in base_types:
        raise TypeException(reason=TypeExceptionEnum.type_is_not_base)
    if any(
        [
            tau == sigma,
            isinstance(tau, NoneType),
            isinstance(sigma, TermType),
            isinstance(tau, IntegerType) and isinstance(sigma, NumberType),
            isinstance(tau, FloatType) and isinstance(sigma, NumberType),
        ]
    ):
        return True
    return False


def base_supremum(tau: Type, sigma: Type) -> Type:
    if tau not in base_types or sigma not in base_types:
        raise TypeException(reason=TypeExceptionEnum.type_is_not_base)
    if is_base_subtype(tau, sigma):
        return sigma
    if is_base_subtype(sigma, tau):
        return tau
    if isinstance(tau, NoneType) or isinstance(sigma, NoneType):
        return tau if isinstance(sigma, NoneType) else sigma
    if isinstance(tau, IntegerType) and isinstance(sigma, FloatType):
        return NumberType()
    if isinstance(tau, FloatType) and isinstance(sigma, IntegerType):
        return NumberType()
    return TermType()


def base_infimum(tau: Type, sigma: Type) -> Type:
    if tau not in base_types or sigma not in base_types:
        raise TypeException(reason=TypeExceptionEnum.type_is_not_base)
    if is_base_subtype(tau, sigma):
        return tau
    if is_base_subtype(sigma, tau):
        return sigma
    if isinstance(tau, TermType) or isinstance(sigma, TermType):
        return tau if isinstance(sigma, TermType) else sigma
    return NoneType()


def is_static_type(tau: Type) -> bool:
    if isinstance(tau, AnyType):
        return False
    elif tau in base_types:
        return True
    elif isinstance(tau, ListType):
        return is_static_type(tau.type)
    elif isinstance(tau, TupleType):
        return all([is_static_type(sigma) for sigma in tau.types])
    elif isinstance(tau, MapType):
        return all([is_static_type(sigma) for sigma in tau.map_type.values()])
    else:
        assert isinstance(tau, FunctionType)
        return all(
            [is_static_type(sigma) for sigma in tau.arg_types]
        ) and is_static_type(tau.ret_type)


def is_higher_order(tau: Type) -> bool:
    if tau in base_types + [AnyType()]:
        return False
    elif isinstance(tau, ListType):
        return is_higher_order(tau.type)
    elif isinstance(tau, TupleType):
        return any([is_higher_order(sigma) for sigma in tau.types])
    elif isinstance(tau, MapType):
        return any([is_higher_order(sigma) for sigma in tau.map_type.values()])
    else:
        assert isinstance(tau, FunctionType)
        return True


def is_allowed(tau: Type) -> bool:
    if isinstance(tau, NoneType):
        return False
    elif tau in base_types + [AnyType()]:
        return True
    elif isinstance(tau, ListType):
        return True
    elif isinstance(tau, TupleType):
        return all([is_allowed(sigma) for sigma in tau.types])
    elif isinstance(tau, MapType):
        return all([is_allowed(sigma) for sigma in tau.map_type.values()])
    else:
        assert isinstance(tau, FunctionType)
        return is_allowed(tau.ret_type)


def is_subtype(tau: Type, sigma: Type) -> bool:
    if tau in base_types and sigma in base_types:
        return is_base_subtype(tau, sigma)
    elif isinstance(tau, AnyType) or isinstance(sigma, AnyType):
        return isinstance(tau, AnyType) and isinstance(sigma, AnyType)
    elif isinstance(tau, NoneType):
        return is_subtype(grounding(tau, sigma), sigma)
    elif isinstance(sigma, TermType):
        return is_subtype(tau, grounding(sigma, tau))
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return is_subtype(tau.type, sigma.type)
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        return len(tau.types) == len(sigma.types) and all(
            [is_subtype(tau.types[i], sigma.types[i]) for i in range(len(tau.types))]
        )
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        return all([(k in tau.map_type) for k in sigma.map_type]) and all(
            [is_subtype(tau.map_type[k], sigma.map_type[k]) for k in sigma.map_type]
        )
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        return is_subtype(
            TupleType(types=sigma.arg_types), TupleType(types=tau.arg_types)
        ) and is_subtype(tau.ret_type, sigma.ret_type)
    else:
        assert any(
            [
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        return False


def is_materialization(tau: Type, sigma: Type) -> bool:
    if isinstance(tau, AnyType):
        return True
    elif tau in base_types and sigma in base_types and tau == sigma:
        return True
    elif isinstance(tau, ListType):
        return isinstance(sigma, ListType) and is_materialization(tau.type, sigma.type)
    elif isinstance(tau, TupleType):
        return (
            isinstance(sigma, TupleType)
            and len(tau.types) == len(sigma.types)
            and all(
                [
                    is_materialization(tau.types[i], sigma.types[i])
                    for i in range(len(tau.types))
                ]
            )
        )
    elif isinstance(tau, MapType):
        return (
            isinstance(sigma, MapType)
            and set(tau.map_type.keys()) == set(sigma.map_type.keys())
            and all(
                [
                    is_materialization(tau.map_type[k], sigma.map_type[k])
                    for k in tau.map_type.keys()
                ]
            )
        )
    elif isinstance(tau, FunctionType):
        if isinstance(sigma, FunctionType):
            return (
                len(tau.arg_types) == len(sigma.arg_types)
                and all(
                    [
                        is_materialization(tau.arg_types[i], sigma.arg_types[i])
                        for i in range(len(tau.arg_types))
                    ]
                )
                and is_materialization(tau.ret_type, sigma.ret_type)
            )
        return False
    else:
        assert any(
            [
                tau in base_types and sigma in base_types and tau != sigma,
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        return False


def is_msubtype_plus(tau: Type, sigma: Type) -> bool:
    if tau in base_types and sigma in base_types:
        return is_base_subtype(tau, sigma)
    elif isinstance(tau, AnyType) or isinstance(sigma, AnyType):
        return isinstance(tau, AnyType)
    elif isinstance(tau, NoneType):
        return is_static_type(sigma)
    elif isinstance(sigma, TermType):
        return True
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return is_msubtype_plus(tau.type, sigma.type)
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        return len(tau.types) == len(sigma.types) and all(
            [
                is_msubtype_plus(tau.types[i], sigma.types[i])
                for i in range(len(tau.types))
            ]
        )
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        return all([(k in tau.map_type) for k in sigma.map_type]) and all(
            [
                is_msubtype_plus(tau.map_type[k], sigma.map_type[k])
                for k in sigma.map_type
            ]
        )
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        return is_msubtype_minus(
            TupleType(types=tau.arg_types), TupleType(types=sigma.arg_types)
        ) and is_msubtype_plus(tau.ret_type, sigma.ret_type)
    return False


def is_msubtype_minus(tau: Type, sigma: Type) -> bool:
    if tau in base_types and sigma in base_types:
        return is_base_subtype(sigma, tau)
    elif isinstance(tau, AnyType) or isinstance(sigma, AnyType):
        return isinstance(tau, AnyType)
    elif isinstance(tau, TermType):
        return is_static_type(sigma)
    elif isinstance(sigma, NoneType):
        return True
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return is_msubtype_minus(tau.type, sigma.type)
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        return len(tau.types) == len(sigma.types) and all(
            [
                is_msubtype_minus(tau.types[i], sigma.types[i])
                for i in range(len(tau.types))
            ]
        )
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        return all([(k in sigma.map_type) for k in tau.map_type]) and all(
            [
                is_msubtype_minus(tau.map_type[k], sigma.map_type[k])
                for k in tau.map_type
            ]
        )
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        return is_msubtype_plus(
            TupleType(types=tau.arg_types), TupleType(types=sigma.arg_types)
        ) and is_msubtype_minus(tau.ret_type, sigma.ret_type)
    else:
        assert any(
            [
                tau in base_types and sigma in base_types and tau != sigma,
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        return False


def supremum(tau: Type, sigma: Type) -> Type:
    if tau in base_types and sigma in base_types:
        return base_supremum(tau, sigma)
    elif AnyType() in [tau, sigma]:
        if isinstance(tau, AnyType) and isinstance(sigma, AnyType):
            return AnyType()
        else:
            raise TypeException(
                reason=TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            )
    elif TermType() in [tau, sigma]:
        if is_subtype(tau if isinstance(sigma, TermType) else sigma, TermType()):
            return TermType()
        raise TypeException(
            reason=TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
        )
    elif NoneType() in [tau, sigma]:
        if is_subtype(NoneType(), mu := tau if isinstance(sigma, NoneType) else sigma):
            return mu
        raise TypeException(
            reason=TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
        )
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return ListType(supremum(tau.type, sigma.type))
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            return TupleType(
                [supremum(tau.types[i], sigma.types[i]) for i in range(len(tau.types))]
            )
        else:
            assert isinstance(supremum(TermType(), tau), TermType)
            assert isinstance(supremum(TermType(), sigma), TermType)
            return TermType()
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        inter_keys = [k for k in tau.map_type if k in sigma.map_type]
        return MapType(
            {k: supremum(tau.map_type[k], sigma.map_type[k]) for k in inter_keys}
        )
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            return FunctionType(
                [
                    infimum(tau.arg_types[i], sigma.arg_types[i])
                    for i in range(len(tau.arg_types))
                ],
                supremum(tau.ret_type, sigma.ret_type),
            )
        else:
            assert isinstance(supremum(TermType(), tau), TermType)
            assert isinstance(supremum(TermType(), sigma), TermType)
            return TermType()
    else:
        assert any(
            [
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        return TermType()


def infimum(tau: Type, sigma: Type) -> Type:
    if tau in base_types and sigma in base_types:
        return base_infimum(tau, sigma)
    elif AnyType() in [tau, sigma]:
        if isinstance(tau, AnyType) and isinstance(sigma, AnyType):
            return AnyType()
        else:
            raise TypeException(
                reason=TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
            )
    elif NoneType() in [tau, sigma]:
        if is_subtype(NoneType(), tau if isinstance(sigma, NoneType) else sigma):
            return NoneType()
        raise TypeException(
            reason=TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
        )
    elif TermType() in [tau, sigma]:
        if is_subtype(mu := tau if isinstance(sigma, TermType) else sigma, TermType()):
            return mu
        raise TypeException(
            reason=TypeExceptionEnum.supremum_does_not_exist_for_any_and_something_else
        )
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return ListType(infimum(tau.type, sigma.type))
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            return TupleType(
                [infimum(tau.types[i], sigma.types[i]) for i in range(len(tau.types))]
            )
        else:
            assert isinstance(infimum(NoneType(), tau), NoneType)
            assert isinstance(infimum(NoneType(), sigma), NoneType)
            return NoneType()
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        return MapType(utils.merge_dicts(tau.map_type, sigma.map_type, infimum))
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            return FunctionType(
                [
                    supremum(tau.arg_types[i], sigma.arg_types[i])
                    for i in range(len(tau.arg_types))
                ],
                infimum(tau.ret_type, sigma.ret_type),
            )
        else:
            assert isinstance(infimum(NoneType(), tau), NoneType)
            assert isinstance(infimum(NoneType(), sigma), NoneType)
            return NoneType()
    else:
        assert any(
            [
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        return NoneType()


def msupremum_plus(tau: Type, sigma: Type) -> Type:
    if tau in base_types and sigma in base_types:
        return base_supremum(tau, sigma)
    if AnyType() in [tau, sigma]:
        return tau if isinstance(sigma, AnyType) else sigma
    elif NoneType() in [tau, sigma]:
        tau, sigma = (tau, sigma) if isinstance(tau, NoneType) else (sigma, tau)
        assert isinstance(tau, NoneType)
        return msupremum_plus(grounding(tau, sigma), sigma)
    elif TermType() in [tau, sigma]:
        return TermType()
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return ListType(msupremum_plus(tau.type, sigma.type))
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            return TupleType(
                [
                    msupremum_plus(tau.types[i], sigma.types[i])
                    for i in range(len(tau.types))
                ]
            )
        else:
            return TermType()
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        inter_keys = [k for k in tau.map_type if k in sigma.map_type]
        return MapType(
            {k: msupremum_plus(tau.map_type[k], sigma.map_type[k]) for k in inter_keys}
        )
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            return FunctionType(
                [
                    msupremum_minus(tau.arg_types[i], sigma.arg_types[i])
                    for i in range(len(tau.arg_types))
                ],
                msupremum_plus(tau.ret_type, sigma.ret_type),
            )
        else:
            return TermType()
    else:
        assert any(
            [
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        return TermType()


def msupremum_minus(tau: Type, sigma: Type) -> Type:
    if tau in base_types and sigma in base_types:
        return base_infimum(tau, sigma)
    if AnyType() in [tau, sigma]:
        return tau if isinstance(sigma, AnyType) else sigma
    elif TermType() in [tau, sigma]:
        tau, sigma = (tau, sigma) if isinstance(tau, TermType) else (sigma, tau)
        assert isinstance(tau, TermType)
        return msupremum_minus(grounding(tau, sigma), sigma)
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return ListType(msupremum_minus(tau.type, sigma.type))
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            return TupleType(
                [
                    msupremum_minus(tau.types[i], sigma.types[i])
                    for i in range(len(tau.types))
                ]
            )
        else:
            return NoneType()
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        return MapType(utils.merge_dicts(tau.map_type, sigma.map_type, msupremum_minus))
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            return FunctionType(
                [
                    msupremum_plus(tau.arg_types[i], sigma.arg_types[i])
                    for i in range(len(tau.arg_types))
                ],
                msupremum_minus(tau.ret_type, sigma.ret_type),
            )
        else:
            return NoneType()
    else:
        assert any(
            [
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        return NoneType()


def minfimum_plus(tau: Type, sigma: Type) -> Type:
    if tau in base_types and sigma in base_types:
        return base_infimum(tau, sigma)
    if AnyType() in [tau, sigma]:
        return AnyType()
    elif TermType() in [tau, sigma]:
        return tau if isinstance(sigma, TermType) else sigma
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return ListType(minfimum_plus(tau.type, sigma.type))
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            return TupleType(
                [
                    minfimum_plus(tau.types[i], sigma.types[i])
                    for i in range(len(tau.types))
                ]
            )
        else:
            if is_static_type(tau) and is_static_type(sigma):
                return NoneType()
            return AnyType()
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        return MapType(utils.merge_dicts(tau.map_type, sigma.map_type, minfimum_plus))
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            return FunctionType(
                [
                    minfimum_minus(tau.arg_types[i], sigma.arg_types[i])
                    for i in range(len(tau.arg_types))
                ],
                minfimum_plus(tau.ret_type, sigma.ret_type),
            )
        else:
            if is_static_type(tau) and is_static_type(sigma):
                return NoneType()
            return AnyType()
    else:
        assert any(
            [
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        if is_static_type(tau) and is_static_type(sigma):
            return NoneType()
        else:
            return AnyType()


def minfimum_minus(tau: Type, sigma: Type) -> Type:
    if tau in base_types and sigma in base_types:
        return base_supremum(tau, sigma)
    if AnyType() in [tau, sigma]:
        return AnyType()
    elif NoneType() in [tau, sigma]:
        return tau if isinstance(sigma, NoneType) else sigma
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return ListType(minfimum_minus(tau.type, sigma.type))
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            return TupleType(
                [
                    minfimum_minus(tau.types[i], sigma.types[i])
                    for i in range(len(tau.types))
                ]
            )
        else:
            if is_static_type(tau) and is_static_type(sigma):
                return TermType()
            else:
                return AnyType()
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        inter_keys = [k for k in tau.map_type if k in sigma.map_type]
        return MapType(
            {k: minfimum_minus(tau.map_type[k], sigma.map_type[k]) for k in inter_keys}
        )
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            return FunctionType(
                [
                    minfimum_plus(tau.arg_types[i], sigma.arg_types[i])
                    for i in range(len(tau.arg_types))
                ],
                minfimum_minus(tau.ret_type, sigma.ret_type),
            )
        else:
            if is_static_type(tau) and is_static_type(sigma):
                return TermType()
            else:
                return AnyType()
    else:
        assert any(
            [
                tau in base_types and sigma not in base_types,
                sigma in base_types and tau not in base_types,
            ]
        ) or all(
            [tau not in base_types, sigma not in base_types, type(tau) != type(sigma)]
        )
        if is_static_type(tau) and is_static_type(sigma):
            return TermType()
        else:
            return AnyType()
