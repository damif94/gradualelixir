import typing as t
from dataclasses import dataclass
from enum import Enum


class Type:
    pass


@dataclass
class IntegerType(Type):
    def __str__(self):
        return 'integer'


@dataclass
class BooleanType(Type):
    def __str__(self):
        return 'boolean'


@dataclass
class AtomType(Type):
    def __str__(self):
        return 'atom'


@dataclass
class AtomLiteralType(Type):
    atom: str

    def __init__(self, atom):
        if atom == ':true':
            self.atom = 'true'
        elif atom == ':false':
            self.atom = 'false'
        else:
            self.atom = atom

    def __str__(self):
        if self.atom:
            if self.atom in ['true', 'false']:
                return self.atom
            return ':' + self.atom
        return 'atom'


@dataclass
class FloatType(Type):
    def __str__(self):
        return 'float'


@dataclass
class NumberType(Type):
    def __str__(self):
        return 'number'


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
class ElistType(Type):
    def __str__(self):
        return '[]'


@dataclass
class ListType(Type):
    type: Type

    def __str__(self):
        return '[' + str(self.type) + ']'


@dataclass
class MapType(Type):

    map_type: t.Dict[int, Type]

    def __str__(self):
        keys = self.map_type.keys()
        str_values = [str(v) for v in self.map_type.values()]
        return '%{' + ','.join([f'{k}: {v}' for (k, v) in zip(keys, str_values)]) + '}'


@dataclass
class FunctionType(Type):
    arg_types: t.List[Type]
    ret_type: Type

    def __str__(self):
        return (
            f'({",".join([str(ty) for ty in self.arg_types])}) -> {str(self.ret_type)}'
        )


class TypeErrorEnum(Enum):
    supremum_does_not_exist = '{} does not exist'


class TypingError:
    kind: TypeErrorEnum
    args: t.Any

    def __str__(self):
        return self.kind.value.format(self.args)


class SupremumError(TypingError):
    reason = TypeErrorEnum.supremum_does_not_exist

    def __init__(self, supremum: bool):
        self.args = ('supremum' if supremum else 'infimum',)


def is_base_type(tau: Type) -> bool:
    return any(
        [
            isinstance(tau, klass)
            for klass in [
                AtomLiteralType,
                AtomType,
                BooleanType,
                IntegerType,
                FloatType,
                NumberType,
            ]
        ]
    )


def grounding(tau: t.Union[ListType, TupleType, MapType, FunctionType]) -> Type:
    any = AnyType()
    if isinstance(tau, ListType):
        return ListType(any)
    elif isinstance(tau, TupleType):
        return TupleType([any for _ in tau.types])
    elif isinstance(tau, MapType):
        return MapType({k: any for k in tau.map_type})
    elif isinstance(tau, FunctionType):
        return FunctionType([any for _ in tau.arg_types], any)


def is_base_subtype(tau: Type, sigma: Type) -> bool:
    assert is_base_type(tau) and is_base_type(sigma)
    if any(
        [
            tau == sigma,
            isinstance(tau, AtomLiteralType)
            and tau.atom in ['true', 'false']
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


def base_supremum(tau: Type, sigma: Type) -> t.Union[Type, TypingError]:
    assert is_base_type(tau) and is_base_type(sigma)
    if is_base_subtype(tau, sigma):
        return sigma
    if is_base_subtype(sigma, tau):
        return tau
    if isinstance(tau, AtomLiteralType) and isinstance(sigma, AtomLiteralType):
        if tau.atom == 'true' and sigma.atom == 'false':
            return BooleanType()
        elif tau.atom == 'false' and sigma.atom == 'true':
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
    return SupremumError(supremum=True)


def base_infimum(tau: Type, sigma: Type) -> t.Union[Type, TypingError]:
    assert is_base_type(tau) and is_base_type(sigma)
    if is_base_subtype(tau, sigma):
        return tau
    if is_base_subtype(sigma, tau):
        return sigma
    return SupremumError(supremum=False)


def is_static_type(tau: Type) -> bool:
    if isinstance(tau, AnyType):
        return False
    elif is_base_type(tau):
        return True
    elif isinstance(tau, ElistType):
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
    if is_base_type(tau):
        return False
    elif isinstance(tau, AnyType):
        return False
    elif isinstance(tau, ElistType):
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


def is_subtype(tau: Type, sigma: Type) -> bool:
    if is_base_type(tau) and is_base_type(sigma):
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
            [is_subtype(tau.map_type[k], sigma.map_type[k]) for k in sigma.map_type]
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
    elif is_base_type(tau) and is_base_type(sigma) and tau == sigma:
        return True
    elif isinstance(tau, ElistType) or isinstance(sigma, ElistType):
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
        return False


def supremum_infimum_aux(
    tau: Type, sigma: Type, supremum=True
) -> t.Union[Type, TypingError]:
    if AnyType() in [tau, sigma]:
        return AnyType()
    elif is_base_type(tau) and is_base_type(sigma):
        return base_supremum(tau, sigma) if supremum else base_infimum(tau, sigma)
    elif isinstance(tau, ElistType):
        if isinstance(sigma, ElistType):
            return sigma
        elif isinstance(sigma, ListType):
            return sigma if supremum else tau
        return SupremumError(supremum=supremum)
    elif isinstance(sigma, ElistType):
        return supremum_infimum_aux(sigma, tau, supremum)
    elif isinstance(tau, ListType) and isinstance(sigma, ListType):
        type = supremum_infimum_aux(tau.type, sigma.type, supremum)
        if isinstance(error := type, TypingError):
            return error
        return ListType(type)  # type: ignore
    elif isinstance(tau, TupleType) and isinstance(sigma, TupleType):
        if len(tau.types) == len(sigma.types):
            types_acc = []
            for i in range(len(tau.types)):
                aux = supremum_infimum_aux(tau.types[i], sigma.types[i], supremum)
                if isinstance(aux, TypingError):
                    return aux
                types_acc.append(aux)
            return TupleType(types_acc)
        else:
            return SupremumError(supremum=supremum)
    elif isinstance(tau, MapType) and isinstance(sigma, MapType):
        keys = [k for k in tau.map_type if k in sigma.map_type]
        tau_map_type = tau.map_type.copy()
        sigma_map_type = sigma.map_type.copy()
        if not supremum:
            tau_keys_not_in_sigma = [k for k in tau.map_type if k not in sigma.map_type]
            sigma_keys_not_in_tau = [k for k in sigma.map_type if k not in tau.map_type]
            tau_map_type.update({k: sigma_map_type[k] for k in sigma_keys_not_in_tau})
            sigma_map_type.update({k: tau_map_type[k] for k in tau_keys_not_in_sigma})
            keys += tau_keys_not_in_sigma + sigma_keys_not_in_tau
        types_map_acc = {}
        for k in keys:
            aux = supremum_infimum_aux(tau_map_type[k], sigma_map_type[k], supremum)
            if isinstance(aux, TypingError):
                return aux
            types_map_acc[k] = aux
        return MapType(types_map_acc)
    elif isinstance(tau, FunctionType) and isinstance(sigma, FunctionType):
        if len(tau.arg_types) == len(sigma.arg_types):
            types_acc = []
            for i in range(len(tau.arg_types)):
                aux = supremum_infimum_aux(
                    tau.arg_types[i], sigma.arg_types[i], not supremum
                )
                if isinstance(aux, TypingError):
                    return aux
                types_acc.append(aux)
        else:
            return SupremumError(supremum=supremum)
        arg_types = types_acc
        ret_type = supremum_infimum_aux(tau.ret_type, sigma.ret_type, supremum)
        if isinstance(error := ret_type, TypingError):
            return error
        return FunctionType(arg_types, ret_type)  # type: ignore
    else:
        return SupremumError(supremum=supremum)


def supremum(tau: Type, sigma: Type) -> t.Union[Type, TypingError]:
    return supremum_infimum_aux(tau, sigma, True)


def infimum(tau: Type, sigma: Type) -> t.Union[Type, TypingError]:
    return supremum_infimum_aux(tau, sigma, False)
