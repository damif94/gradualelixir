import enum
import typing as t
from dataclasses import dataclass

from gradualelixir import types as gtypes


class Pattern:
    pass


@dataclass
class WildPattern(Pattern):
    def __str__(self):
        return '_'


@dataclass
class IdentPattern(Pattern):
    identifier: str

    def __str__(self):
        return self.identifier


@dataclass
class PinIdentPattern(Pattern):
    identifier: str

    def __str__(self):
        return '^' + self.identifier


@dataclass
class LiteralPattern(Pattern):
    type: gtypes.Type
    value: t.Any


@dataclass
class IntegerPattern(LiteralPattern):
    value: int

    def __init__(self, value: int):
        self.type = gtypes.IntegerType()
        self.value = value

    def __str__(self):
        return str(self.value)


@dataclass
class FloatPattern(LiteralPattern):
    value: float

    def __init__(self, value: float):
        self.type = gtypes.FloatType()
        self.value = value

    def __str__(self):
        return str(self.value)


@dataclass
class AtomLiteralPattern(LiteralPattern):
    value: str

    def __init__(self, value: str):
        self.type = gtypes.AtomLiteralType(atom=value)
        self.value = value

    def __str__(self):
        return str(self.type)


@dataclass
class TuplePattern(Pattern):
    items: t.List[Pattern]

    def __str__(self):
        return '{' + ','.join([str(item) for item in self.items]) + '}'


@dataclass
class ElistPattern(Pattern):
    def __str__(self):
        return '[]'


@dataclass
class ListPattern(Pattern):
    head: Pattern
    tail: Pattern

    def __init__(self, head, tail):
        if not (isinstance(tail, ListPattern) or isinstance(tail, ElistPattern)):
            raise SyntaxException(
                "List pattern's tail should be either a List Pattern or an Elist Pattern"
            )
        self.head = head
        self.tail = tail

    def __str__(self):
        return f'[{str(self.head)} | {str(self.tail)}]'


@dataclass
class MapPattern(Pattern):

    map: t.OrderedDict[int, Pattern]

    def __str__(self):
        keys = self.map.keys()
        str_values = [str(v) for v in self.map.values()]
        return '%{' + ','.join([f'{k}: {v}' for (k, v) in zip(keys, str_values)]) + '}'


class PatternErrorEnum(enum.Enum):
    incompatible_type_for_variable = (
        "Couldn't match identifier {identifier}'s current type {sigma} with {tau}"
    )
    incompatible_type_for_literal = "Couldn't match literal {pattern} with type {tau}"
    arrow_types_into_nonlinear_identifier = (
        "Can't match {identifier}'s current type {tau} against {sigma}. "
        'Arrow types can only be used for assignment in pattern matches'
    )
    incompatible_type_for_pinned_variable = (
        "Couldn't match pinned identifier {identifier}'s current type {sigma} with {tau}"
    )
    pinned_identifier_not_found_in_environment = (
        "Couldn't find pinned variable ^{identifier} in the environment"
    )
    arrow_types_into_pinned_identifier = (
        "Can't match ^{identifier}'s current type {tau} with {sigma} in external environment. "
        f'Arrow types can only be used for assignment in pattern matches'
    )
    incompatible_tuples_error = "Couldn't match tuple {pattern} against type {tau} because they have different sizes"
    incompatible_maps_error = (
        "Couldn't match tuple {pattern} against type {tau} because they some of {tau} keys "
        'are not present in {pattern}'
    )
    incompatible_constructors_error = (
        'Error matching {pattern} with type {tau}: wrong shape'
    )


class PatternContext:
    pattern: Pattern


@dataclass
class ListPatternContext(PatternContext):
    pattern: ListPattern
    head: bool

    def __str__(self):
        if self.head:
            return f'In the head pattern inside {self.pattern}'
        return f'In the tail pattern inside {self.pattern}'


@dataclass
class TuplePatternContext(PatternContext):
    pattern: TuplePattern
    n: int

    def __str__(self):
        return f'In {self.pattern} {self.n}th position'


@dataclass
class MapPatternContext(PatternContext):
    pattern: MapPattern
    key: int

    def __str__(self):
        return f'In the pattern for key {self.key} inside {self.pattern}'


class PatternError:
    def message(self, padding):
        return ''


@dataclass
class BasePatternError(PatternError):
    kind: PatternErrorEnum
    args: t.Dict[str, t.Any]

    def __str__(self):
        return self.message()

    def message(self, padding=''):
        args = {k: str(arg) for k, arg in self.args.items()}
        return self.kind.value.format(**args)


@dataclass
class NestedPatternError(PatternError):
    context: PatternContext
    error: PatternError

    def __str__(self):
        return self.message()

    def message(self, padding=''):
        context_msg = str(self.context)
        bullet_msg = self.error.message(padding + '  ')
        return f'{context_msg}:\n' + f'{padding}  > {bullet_msg}'


class SyntaxException(Exception):
    pass


@dataclass
class PatternMatchReturnType:
    env: t.Dict[str, gtypes.Type]
    mapping: t.Callable[[t.Dict[str, gtypes.Type]], gtypes.Type]


def pattern_match_aux(
    pattern: Pattern,
    tau: gtypes.Type,
    gamma_env: t.Dict[str, gtypes.Type],
    sigma_env: t.Dict[str, gtypes.Type],
) -> t.Union[PatternMatchReturnType, PatternError]:
    if isinstance(pattern, LiteralPattern):
        # TP_LIT
        if gtypes.is_subtype(pattern.type, tau):
            return PatternMatchReturnType(gamma_env, lambda domain: pattern.type)  # type: ignore
        else:
            return BasePatternError(
                kind=PatternErrorEnum.incompatible_type_for_literal,
                args={'pattern': pattern, 'tau': tau},
            )
    elif isinstance(pattern, IdentPattern):
        if sigma := gamma_env.get(pattern.identifier):
            # TP_VARN
            if gtypes.is_higher_order(tau) or gtypes.is_higher_order(sigma):
                return BasePatternError(
                    kind=PatternErrorEnum.arrow_types_into_nonlinear_identifier,
                    args={'identifier': pattern.identifier, 'tau': tau, 'sigma': sigma},
                )
            if not isinstance(mu := gtypes.infimum(tau, sigma), gtypes.SupremumError):
                gamma_env[pattern.identifier] = mu  # type: ignore
                return PatternMatchReturnType(gamma_env, lambda env: env[pattern.identifier])  # type: ignore
            return BasePatternError(
                kind=PatternErrorEnum.incompatible_type_for_variable,
                args={'identifier': pattern.identifier, 'tau': tau, 'sigma': sigma},
            )
        else:
            # TP_VARE
            gamma_env[pattern.identifier] = tau
            return PatternMatchReturnType(gamma_env, lambda env: env[pattern.identifier])  # type: ignore
    elif isinstance(pattern, PinIdentPattern):
        # TP_PIN
        if (sigma := sigma_env.get(pattern.identifier)) is not None:
            if gtypes.is_higher_order(tau) or gtypes.is_higher_order(sigma):
                return BasePatternError(
                    kind=PatternErrorEnum.arrow_types_into_pinned_identifier,
                    args={'identifier': pattern.identifier, 'tau': tau, 'sigma': sigma},
                )
            elif not isinstance(mu := gtypes.infimum(tau, sigma), gtypes.SupremumError):
                return PatternMatchReturnType(gamma_env, lambda env: mu)  # type: ignore
            return BasePatternError(
                kind=PatternErrorEnum.incompatible_type_for_pinned_variable,
                args={'identifier': pattern.identifier, 'tau': tau, 'sigma': sigma},
            )
        else:
            return BasePatternError(
                kind=PatternErrorEnum.pinned_identifier_not_found_in_environment,
                args={'identifier': pattern.identifier},
            )
    elif isinstance(pattern, WildPattern):
        # TP_WILD
        return PatternMatchReturnType(gamma_env, lambda env: tau)
    elif isinstance(pattern, ElistPattern) and gtypes.is_subtype(
        gtypes.ElistType(), tau
    ):
        # TP_ELIST
        return PatternMatchReturnType(gamma_env, lambda env: gtypes.ElistType())
    elif isinstance(pattern, ListPattern) and isinstance(tau, gtypes.ListType):
        # TP_LIST
        aux_head = pattern_match_aux(pattern.head, tau.type, gamma_env, sigma_env)
        if isinstance(aux_head, PatternError):
            return NestedPatternError(
                error=aux_head, context=ListPatternContext(head=True, pattern=pattern)
            )
        aux_tail = pattern_match_aux(pattern.tail, tau, aux_head.env, sigma_env)
        if isinstance(aux_tail, PatternError):
            return NestedPatternError(
                error=aux_tail, context=ListPatternContext(head=False, pattern=pattern)
            )
        return PatternMatchReturnType(
            gamma_env, lambda env: gtypes.supremum(gtypes.ListType(aux_head.mapping(env)), aux_tail.mapping(env))  # type: ignore
        )
    elif isinstance(pattern, TuplePattern) and isinstance(tau, gtypes.TupleType):
        # TP_TUPLE
        if len(pattern.items) != len(tau.types):
            return BasePatternError(
                kind=PatternErrorEnum.incompatible_tuples_error,
                args={'pattern': pattern, 'tau': tau},
            )
        mappings_acc: t.List[t.Callable[[t.Dict[str, gtypes.Type]], gtypes.Type]] = []
        gamma_env_aux = gamma_env
        for i in range(len(pattern.items)):
            aux = pattern_match_aux(
                pattern.items[i], tau.types[i], gamma_env_aux, sigma_env
            )
            if isinstance(aux, PatternError):
                return NestedPatternError(
                    error=aux, context=TuplePatternContext(n=i + 1, pattern=pattern)
                )
            mappings_acc.append(aux.mapping)
            gamma_env_aux = aux.env
        return PatternMatchReturnType(
            gamma_env_aux,
            lambda env: gtypes.TupleType([mapping(env) for mapping in mappings_acc]),
        )
    elif isinstance(pattern, MapPattern) and isinstance(tau, gtypes.MapType):
        # TP_MAP
        if pattern.map.keys() != tau.map_type.keys():
            return BasePatternError(
                kind=PatternErrorEnum.incompatible_maps_error,
                args={'pattern': pattern, 'tau': tau},
            )
        else:
            mappings_map_acc: t.Dict[
                int, t.Callable[[t.Dict[str, gtypes.Type]], gtypes.Type]
            ] = {}
            gamma_env_aux = gamma_env
            for key in tau.map_type:
                aux = pattern_match_aux(
                    pattern.map[key], tau.map_type[key], gamma_env_aux, sigma_env
                )
                if isinstance(aux, PatternError):
                    return NestedPatternError(
                        error=aux, context=MapPatternContext(key=key, pattern=pattern)
                    )
                mappings_map_acc[key] = aux.mapping
                gamma_env_aux = aux.env
            return PatternMatchReturnType(
                gamma_env_aux,
                lambda env: gtypes.MapType(dict([(k, mapping(env)) for k, mapping in mappings_map_acc.items()])),  # type: ignore
            )
    elif isinstance(tau, gtypes.AnyType):
        if isinstance(pattern, ElistPattern) or isinstance(pattern, ListPattern):
            ground_tau: gtypes.Type = gtypes.ListType(tau)
        elif isinstance(pattern, TuplePattern):
            ground_tau = gtypes.TupleType([tau for _ in pattern.items])
        else:
            assert isinstance(pattern, MapPattern)
            ground_tau = gtypes.MapType({k: tau for k in pattern.map})
        return pattern_match_aux(pattern, ground_tau, gamma_env, sigma_env)
    else:
        assert any(
            [
                isinstance(pattern, ElistPattern),
                isinstance(pattern, ListPattern),
                isinstance(pattern, TuplePattern),
                isinstance(pattern, MapPattern),
            ]
        )
        assert any(
            [
                isinstance(pattern, ElistPattern)
                and not isinstance(tau, gtypes.ListType),
                isinstance(pattern, ListPattern)
                and not isinstance(tau, gtypes.ListType),
                isinstance(pattern, TuplePattern)
                and not isinstance(tau, gtypes.TupleType),
                isinstance(pattern, MapPattern) and not isinstance(tau, gtypes.MapType),
                isinstance(tau, gtypes.FunctionType),
            ]
        )
        return BasePatternError(
            kind=PatternErrorEnum.incompatible_constructors_error,
            args={'pattern': pattern, 'tau': tau},
        )


def pattern_match(
    pattern: Pattern,
    tau: gtypes.Type,
    gamma_env: t.Dict[str, gtypes.Type],
    sigma_env: t.Dict[str, gtypes.Type],
) -> t.Union[t.Tuple[gtypes.Type, t.Dict[str, gtypes.Type]], PatternError]:
    aux = pattern_match_aux(pattern, tau, gamma_env, sigma_env)
    if isinstance(aux, PatternError):
        return aux
    else:
        return aux.mapping(aux.env), aux.env
