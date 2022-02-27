import typing as t
from dataclasses import dataclass
from enum import Enum


class Type:
    pass


class BaseType(Type):
    pass


@dataclass
class BooleanType(BaseType):
    def __str__(self):
        return "boolean"


@dataclass
class AtomType(BaseType):
    def __str__(self):
        return "atom"


class LiteralType(BaseType):
    pass


@dataclass
class IntegerType(LiteralType):
    def __str__(self):
        return "integer"


@dataclass
class AtomLiteralType(LiteralType):
    atom: str

    def __init__(self, atom):
        self.atom = atom

    def __str__(self):
        if self.atom:
            if self.atom in ["true", "false"]:
                return self.atom
            return ":" + self.atom
        return "atom"


@dataclass
class FloatType(LiteralType):
    def __str__(self):
        return "float"


@dataclass
class NumberType(BaseType):
    def __str__(self):
        return "number"


@dataclass
class AnyType(Type):
    def __str__(self):
        return "any"


class CompositeType(Type):
    pass


@dataclass
class ElistType(CompositeType):
    def __str__(self):
        return "[]"


@dataclass
class ListType(CompositeType):
    type: Type

    def __str__(self):
        return "[" + str(self.type) + "]"


@dataclass
class TupleType(CompositeType):
    types: t.List[Type]

    def __str__(self):
        return "{" + ",".join([str(ty) for ty in self.types]) + "}"


@dataclass
class MapType(CompositeType):

    map_type: t.Dict[t.Union[int, float, str, bool], Type]

    def __str__(self):
        keys = self.map_type.keys()
        str_values = [str(v) for v in self.map_type.values()]
        return "%{" + ",".join([f"{k}: {v}" for (k, v) in zip(keys, str_values)]) + "}"


@dataclass
class FunctionType(CompositeType):
    arg_types: t.List[Type]
    ret_type: Type

    def __str__(self):
        return (
            f'({",".join([str(ty) for ty in self.arg_types])}) -> {str(self.ret_type)}'
        )


class TypeErrorEnum(Enum):
    supremum_does_not_exist = "{} does not exist"


class TypingError:
    kind: TypeErrorEnum
    args: t.Any

    def __str__(self):
        return self.kind.value.format(self.args)


class SupremumError(TypingError):
    reason = TypeErrorEnum.supremum_does_not_exist

    def __init__(self, is_supremum: bool):
        self.args = ("supremum" if is_supremum else "infimum",)


def is_maximal(tau: Type) -> bool:
    return any(
        [
            isinstance(tau, klass)
            for klass in [
                AtomType,
                NumberType,
            ]
        ]
    )


def is_minimal(tau: Type) -> bool:
    return any(
        [
            isinstance(tau, klass)
            for klass in [
                LiteralType
            ]
        ]
    )


def grounding(tau: CompositeType) -> Type:
    any = AnyType()
    if isinstance(tau, ListType):
        return ListType(any)
    elif isinstance(tau, TupleType):
        return TupleType([any for _ in tau.types])
    elif isinstance(tau, MapType):
        return MapType({k: any for k in tau.map_type})
    assert isinstance(tau, FunctionType)
    return FunctionType([any for _ in tau.arg_types], any)


def is_base_subtype(tau: BaseType, sigma: BaseType) -> bool:
    if any(
        [
            tau == sigma,
            isinstance(tau, AtomLiteralType)
            and tau.atom in ["true", "false"]
            and isinstance(sigma, BooleanType),
            isinstance(tau, BooleanType) and isinstance(sigma, AtomType),
            isinstance(tau, AtomLiteralType)
            and isinstance(sigma, AtomLiteralType)
            and tau.atom == sigma.atom,
            isinstance(tau, AtomLiteralType) and isinstance(sigma, AtomType),
            isinstance(tau, AtomType) and isinstance(sigma, AtomType),
            isinstance(tau, IntegerType) and isinstance(sigma, NumberType),
            isinstance(tau, FloatType) and isinstance(sigma, NumberType),
        ]
    ):
        return True
    return False


def base_supremum(tau: BaseType, sigma: BaseType) -> t.Union[Type, TypingError]:
    if is_base_subtype(tau, sigma):
        return sigma
    if is_base_subtype(sigma, tau):
        return tau
    if isinstance(tau, AtomLiteralType) and isinstance(sigma, AtomLiteralType):
        if tau.atom == "true" and sigma.atom == "false":
            return BooleanType()
        elif tau.atom == "false" and sigma.atom == "true":
            return BooleanType()
        else:
            return AtomType()
    if isinstance(tau, AtomLiteralType) and isinstance(sigma, BooleanType):
        return AtomType()
    if isinstance(tau, BooleanType) and isinstance(sigma, AtomLiteralType):
        return AtomType()
    if isinstance(tau, IntegerType) and isinstance(sigma, FloatType):
        return NumberType()
    if isinstance(tau, FloatType) and isinstance(sigma, IntegerType):
        return NumberType()
    return SupremumError(is_supremum=True)


def base_infimum(tau: Type, sigma: Type) -> t.Union[Type, TypingError]:
    assert isinstance(tau, BaseType) and isinstance(sigma, BaseType)
    if is_base_subtype(tau, sigma):
        return tau
    if is_base_subtype(sigma, tau):
        return sigma
    return SupremumError(is_supremum=False)


def is_static_type(tau: Type) -> bool:
    if isinstance(tau, BaseType):
        return True
    elif isinstance(tau, ElistType):
        return True
    elif isinstance(tau, ListType):
        return is_static_type(tau.type)
    elif isinstance(tau, TupleType):
        return all([is_static_type(sigma) for sigma in tau.types])
    elif isinstance(tau, MapType):
        return all([is_static_type(sigma) for sigma in tau.map_type.values()])
    elif isinstance(tau, FunctionType):
        return all(
            [is_static_type(sigma) for sigma in tau.arg_types]
        ) and is_static_type(tau.ret_type)
    else:
        assert isinstance(tau, AnyType)
        return False


def is_higher_order(tau: Type) -> bool:
    if isinstance(tau, BaseType):
        return False
    elif isinstance(tau, ElistType):
        return False
    elif isinstance(tau, ListType):
        return is_higher_order(tau.type)
    elif isinstance(tau, TupleType):
        return any([is_higher_order(sigma) for sigma in tau.types])
    elif isinstance(tau, MapType):
        return any([is_higher_order(sigma) for sigma in tau.map_type.values()])
    if isinstance(tau, FunctionType):
        return True
    else:
        assert isinstance(tau, AnyType)
        return False


def is_subtype(tau: Type, sigma: Type) -> bool:
    if isinstance(tau, BaseType) and isinstance(sigma, BaseType):
        return is_base_subtype(tau, sigma)
    elif isinstance(tau, AnyType) or isinstance(sigma, AnyType):
        return True
    elif isinstance(tau, ElistType) and isinstance(sigma, ElistType):
        return True
    elif isinstance(tau, ElistType) and isinstance(sigma, ListType):
        return True
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        return is_subtype(tau.type, sigma.type)
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        return len(tau.types) == len(sigma.types) and all(
            [is_subtype(tau.types[i], sigma.types[i]) for i in range(len(tau.types))]
        )
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        return all([(k in tau.map_type) for k in sigma.map_type]) and all(
            [is_subtype(tau.map_type[k], sigma.map_type[k]) for k in sigma.map_type.keys()]
        )
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        return is_subtype(
            TupleType(types=sigma.arg_types), TupleType(types=tau.arg_types)
        ) and is_subtype(tau.ret_type, sigma.ret_type)
    else:
        return False


def is_materialization(tau: Type, sigma: Type) -> bool:
    if isinstance(tau, AnyType):
        return True
    elif isinstance(tau, BaseType):
        if isinstance(sigma, BaseType) and tau == sigma:
            return True
        return False
    elif isinstance(tau, ElistType):
        return isinstance(sigma, ElistType)
    elif isinstance(tau, ListType):
        return isinstance(sigma, ListType) and is_materialization(tau.type, sigma.type)
    elif isinstance(tau, TupleType):
        if isinstance(sigma, TupleType) and len(tau.types) == len(sigma.types):
            for i in range(len(tau.types)):
                if not is_materialization(tau.types[i], sigma.types[i]):
                    return False
            return True
        return False
    elif isinstance(tau, MapType):
        if isinstance(sigma, MapType) and len(tau.map_type.keys()) == len(sigma.map_type.keys()):
            for k in tau.map_type.keys():
                if not is_materialization(tau.map_type[k], sigma.map_type[k]):
                    return False
            return True
        return False
    else:
        assert isinstance(tau, FunctionType)
        if isinstance(sigma, FunctionType) and len(tau.arg_types) == len(sigma.arg_types):
            for i in range(len(tau.arg_types)):
                if not is_materialization(tau.arg_types[i], sigma.arg_types[i]):
                    return False
            return is_materialization(tau.ret_type, sigma.ret_type)
        return False


def supremum_infimum_aux(
    tau: Type, sigma: Type, is_supremum=True
) -> t.Union[Type, TypingError]:

    if isinstance(tau, AnyType) or isinstance(sigma, AnyType):
        tau, sigma = (tau, sigma) if isinstance(tau, AnyType) else (sigma, tau)
        if isinstance(sigma, AnyType):
            return tau
        elif isinstance(sigma, BaseType):
            if is_supremum and is_maximal(sigma):
                return sigma
            if not is_supremum and is_minimal(sigma):
                return sigma
            return tau
        else:
            assert isinstance(sigma, CompositeType)
            tau = grounding(sigma)

    if isinstance(tau, BaseType):
        return supremum_infimum_aux_base(tau, sigma, is_supremum)
    elif isinstance(sigma, BaseType):
        return supremum_infimum_aux_base(sigma, sigma, is_supremum)
    elif isinstance(tau, ElistType):
        return supremum_infimum_aux_elist(tau, sigma, is_supremum)
    elif isinstance(sigma, ElistType):
        return supremum_infimum_aux_elist(sigma, tau, is_supremum)
    elif isinstance(tau, ListType):
        return supremum_infimum_aux_list(tau, sigma, is_supremum)
    elif isinstance(sigma, ListType):
        return supremum_infimum_aux_list(sigma, tau, is_supremum)
    elif isinstance(tau, TupleType):
        return supremum_infimum_aux_tuple(tau, sigma, is_supremum)
    elif isinstance(sigma, TupleType):
        return supremum_infimum_aux_tuple(sigma, tau, is_supremum)
    elif isinstance(tau, MapType):
        return supremum_infimum_aux_map(tau, sigma, is_supremum)
    elif isinstance(sigma, MapType):
        return supremum_infimum_aux_map(sigma, tau, is_supremum)
    elif isinstance(tau, FunctionType):
        return supremum_infimum_aux_function(tau, sigma, is_supremum)
    else:
        assert isinstance(sigma, FunctionType)
        return supremum_infimum_aux_function(sigma, tau, is_supremum)


def supremum_infimum_aux_base(tau: BaseType, sigma: Type, is_supremum: bool) -> t.Union[Type, TypingError]:
    if isinstance(sigma, BaseType):
        return base_supremum(tau, sigma) if is_supremum else base_infimum(tau, sigma)
    return SupremumError(is_supremum=is_supremum)


def supremum_infimum_aux_elist(tau: ElistType, sigma: Type, is_supremum: bool) -> t.Union[Type, TypingError]:
    if isinstance(sigma, ElistType):
        return sigma
    elif isinstance(sigma, ListType):
        return sigma if is_supremum else tau
    return SupremumError(is_supremum=is_supremum)


def supremum_infimum_aux_list(tau: ListType, sigma: Type, is_supremum: bool) -> t.Union[Type, TypingError]:
    if isinstance(sigma, ElistType):
        return tau
    if isinstance(sigma, ListType):
        type_supremum = supremum_infimum_aux(tau.type, sigma.type, is_supremum)
        if isinstance(type_supremum, TypingError):
            return type_supremum
        return ListType(type_supremum)
    return SupremumError(is_supremum=is_supremum)


def supremum_infimum_aux_tuple(tau: TupleType, sigma: Type, is_supremum: bool) -> t.Union[Type, TypingError]:
    if isinstance(sigma, TupleType) and len(tau.types) == len(sigma.types):
        supremum_results = []
        for i in range(len(tau.types)):
            aux = supremum_infimum_aux(tau.types[i], sigma.types[i], is_supremum)
            if isinstance(aux, TypingError):
                return aux
            supremum_results.append(aux)
        return TupleType(supremum_results)
    else:
        return SupremumError(is_supremum=is_supremum)


def supremum_infimum_aux_map(tau: MapType, sigma: Type, is_supremum: bool) -> t.Union[Type, TypingError]:
    # TODO make supremum_infimum_aux_map(types: t.List[Type]) -> t.Union[Type, TypingError]
    #  to support arbitrary arity correctness with respect to gradual lifting
    if isinstance(sigma, MapType):
        keys = [k for k in tau.map_type.keys() if k in sigma.map_type.keys()]
        tau_map_type = tau.map_type.copy()
        sigma_map_type = sigma.map_type.copy()
        if not is_supremum:
            tau_keys_not_in_sigma = [k for k in tau.map_type.keys() if k not in sigma.map_type.keys()]
            sigma_keys_not_in_tau = [k for k in sigma.map_type.keys() if k not in tau.map_type.keys()]
            tau_map_type.update({k: sigma_map_type[k] for k in sigma_keys_not_in_tau})
            sigma_map_type.update({k: tau_map_type[k] for k in tau_keys_not_in_sigma})
            keys += tau_keys_not_in_sigma + sigma_keys_not_in_tau
        supremum_results_dict = {}
        for k in keys:
            aux = supremum_infimum_aux(tau_map_type[k], sigma_map_type[k], is_supremum)
            if isinstance(aux, TypingError):
                return aux
            supremum_results_dict[k] = aux
        return MapType(supremum_results_dict)
    return SupremumError(is_supremum=is_supremum)


def supremum_infimum_aux_function(tau: FunctionType, sigma: Type, is_supremum: bool) -> t.Union[Type, TypingError]:
    if isinstance(sigma, FunctionType) and len(tau.arg_types) == len(sigma.arg_types):
        args_supremum_results = []
        for i in range(len(tau.arg_types)):
            arg_supremum = supremum_infimum_aux(
                tau.arg_types[i], sigma.arg_types[i], not is_supremum
            )
            if isinstance(arg_supremum, TypingError):
                return arg_supremum
            args_supremum_results.append(arg_supremum)

        ret_type_supremum_result = supremum_infimum_aux(tau.ret_type, sigma.ret_type, is_supremum)
        if isinstance(ret_type_supremum_result, TypingError):
            return ret_type_supremum_result
        return FunctionType(args_supremum_results, ret_type_supremum_result)
    else:
        return SupremumError(is_supremum=is_supremum)


def supremum(tau: Type, sigma: Type) -> t.Union[Type, TypingError]:
    return supremum_infimum_aux(tau, sigma, True)


def infimum(tau: Type, sigma: Type) -> t.Union[Type, TypingError]:
    return supremum_infimum_aux(tau, sigma, False)

