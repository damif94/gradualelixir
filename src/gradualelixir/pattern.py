import enum
import typing as t
from dataclasses import dataclass

from gradualelixir import types as gtypes
from gradualelixir.exception import SyntaxRestrictionException
from gradualelixir.types import LiteralType


class Pattern:
    pass


@dataclass
class WildPattern(Pattern):
    def __str__(self):
        return "_"


@dataclass
class IdentPattern(Pattern):
    identifier: str

    def __str__(self):
        return self.identifier


@dataclass
class PinIdentPattern(Pattern):
    identifier: str

    def __str__(self):
        return "^" + self.identifier


@dataclass
class LiteralPattern(Pattern):
    value: t.Any
    type: LiteralType


@dataclass
class IntegerPattern(LiteralPattern):
    value: int

    def __init__(self, value: int):
        self.value = value
        self.type = gtypes.IntegerType()

    def __str__(self):
        return str(self.value)


@dataclass
class FloatPattern(LiteralPattern):
    value: float

    def __init__(self, value: float):
        self.value = value
        self.type = gtypes.FloatType()

    def __str__(self):
        return str(self.value)


@dataclass
class AtomLiteralPattern(LiteralPattern):
    value: str

    def __init__(self, value: str):
        self.value = value
        self.type = gtypes.AtomLiteralType(value)

    def __str__(self):
        return str(gtypes.MapKey(self.value))


@dataclass
class TuplePattern(Pattern):
    items: t.List[Pattern]

    def __str__(self):
        return "{" + ",".join([str(item) for item in self.items]) + "}"


@dataclass
class ElistPattern(Pattern):
    def __str__(self):
        return "[]"


@dataclass
class ListPattern(Pattern):
    head: Pattern
    tail: Pattern

    def __init__(self, head, tail):
        if not (
            isinstance(tail, ListPattern)
            or isinstance(tail, ElistPattern)
            or isinstance(tail, WildPattern)
        ):
            raise SyntaxRestrictionException(
                "List pattern's tail should be either a List Pattern or an Elist Pattern"
            )
        self.head = head
        self.tail = tail

    def __str__(self):
        return f"[{str(self.head)} | {str(self.tail)}]"


@dataclass
class MapPattern(Pattern):

    map: t.OrderedDict[gtypes.MapKey, Pattern]

    def __str__(self):
        keys = self.map.keys()
        str_values = [str(v) for _, v in self.map.items()]
        return "%{" + ",".join([f"{k}: {v}" for (k, v) in zip(keys, str_values)]) + "}"


class PatternErrorEnum(enum.Enum):
    incompatible_type_for_variable = (
        "Couldn't match identifier {identifier}'s current type {sigma} with {tau}"
    )
    incompatible_type_for_literal = "Couldn't match literal {pattern} with type {tau}"
    arrow_types_into_nonlinear_identifier = (
        "Can't match {identifier}'s current type {tau} against {sigma}. "
        "Arrow types can only be used for assignment in pattern matches"
    )
    incompatible_type_for_pinned_variable = (
        "Couldn't match pinned identifier {identifier}'s current type {sigma} with {tau}"
    )
    pinned_identifier_not_found_in_environment = (
        "Couldn't find pinned variable ^{identifier} in the environment"
    )
    incompatible_type_for_elist = "Couldn't match pattern [] with type {tau}"
    arrow_types_into_pinned_identifier = (
        "Can't match ^{identifier}'s current type {tau} with {sigma} in external environment. "
        f"Arrow types can only be used for assignment in pattern matches"
    )
    incompatible_tuples_error = "Couldn't match tuple {pattern} against type {tau} because they have different sizes"
    incompatible_maps_error = (
        "Couldn't match tuple {pattern} against type {tau} because they some of {tau} keys "
        "are not present in {pattern}"
    )
    incompatible_constructors_error = "Error matching {pattern} with type {tau}: wrong shape"
    incompatible_type_for_pattern = "Couldn't assign a type to the pattern match"


class PatternContext:
    pattern: Pattern


@dataclass
class ListPatternContext(PatternContext):
    pattern: ListPattern
    head: bool

    def __str__(self):
        if self.head:
            return f"In the head pattern inside {self.pattern}"
        return f"In the tail pattern inside {self.pattern}"


@dataclass
class TuplePatternContext(PatternContext):
    pattern: TuplePattern
    n: int

    def __str__(self):
        return f"In {self.pattern} {self.n}th position"


@dataclass
class MapPatternContext(PatternContext):
    pattern: MapPattern
    key: gtypes.MapKey

    def __str__(self):
        return f"In the pattern for key {self.key} inside {self.pattern}"


class PatternMatchError:
    def message(self, padding):
        return ""


@dataclass
class BasePatternMatchError(PatternMatchError):
    kind: PatternErrorEnum
    args: t.Dict[str, t.Any]

    def __str__(self):
        return self.message()

    def message(self, padding=""):
        args = {k: str(arg) for k, arg in self.args.items()}
        return self.kind.value.format(**args)


@dataclass
class NestedPatternMatchError(PatternMatchError):
    context: PatternContext
    error: PatternMatchError

    def __str__(self):
        return self.message()

    def message(self, padding=""):
        bullet_msg = self.error.message(padding + "  ")
        return f"{self.context}:\n" + f"{padding}  > {bullet_msg}"


TypeEnv = t.Dict[str, gtypes.Type]


@dataclass
class PatternMatchAuxSuccess:
    env: TypeEnv
    mapping: t.Callable[[TypeEnv], t.Union[gtypes.Type, gtypes.TypingError]]


PatternMatchAuxResult = t.Union[PatternMatchAuxSuccess, PatternMatchError]


def pattern_match_aux(
    pattern: Pattern, tau: gtypes.Type, gamma_env: TypeEnv, sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if isinstance(pattern, LiteralPattern):
        return pattern_match_aux_literal(pattern, tau, gamma_env, sigma_env)
    if isinstance(pattern, IdentPattern):
        return pattern_match_aux_ident(pattern, tau, gamma_env, sigma_env)
    if isinstance(pattern, PinIdentPattern):
        return pattern_match_aux_pin_ident(pattern, tau, gamma_env, sigma_env)
    if isinstance(pattern, WildPattern):
        return pattern_match_aux_wild(pattern, tau, gamma_env, sigma_env)
    if isinstance(tau, gtypes.AnyType):
        return pattern_match_aux_any(pattern, tau, gamma_env, sigma_env)
    if isinstance(pattern, ElistPattern):
        return pattern_match_aux_elist(pattern, tau, gamma_env, sigma_env)
    if isinstance(pattern, ListPattern):
        return pattern_match_aux_list(pattern, tau, gamma_env, sigma_env)
    if isinstance(pattern, TuplePattern):
        return pattern_match_aux_tuple(pattern, tau, gamma_env, sigma_env)
    else:
        assert isinstance(pattern, MapPattern)
        return pattern_match_aux_map(pattern, tau, gamma_env, sigma_env)


def pattern_match_aux_literal(
        pattern: LiteralPattern, tau: gtypes.Type, gamma_env: TypeEnv, _sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if gtypes.is_subtype(pattern.type, tau):
        return PatternMatchAuxSuccess(gamma_env, lambda domain: pattern.type)
    else:
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_type_for_literal,
            args={"pattern": pattern, "tau": tau},
        )


def pattern_match_aux_ident(
        pattern: IdentPattern, tau: gtypes.Type, gamma_env: TypeEnv, _sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if sigma := gamma_env.get(pattern.identifier):
        if gtypes.is_higher_order(tau) or gtypes.is_higher_order(sigma):
            return BasePatternMatchError(
                kind=PatternErrorEnum.arrow_types_into_nonlinear_identifier,
                args={"identifier": pattern.identifier, "tau": tau, "sigma": sigma},
            )
        if not isinstance(mu := gtypes.infimum(tau, sigma), gtypes.TypingError):
            gamma_env[pattern.identifier] = mu
            return PatternMatchAuxSuccess(gamma_env, lambda env: env[pattern.identifier])
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_type_for_variable,
            args={"identifier": pattern.identifier, "tau": tau, "sigma": sigma},
        )
    else:
        gamma_env[pattern.identifier] = tau
        return PatternMatchAuxSuccess(gamma_env, lambda env: env[pattern.identifier])


def pattern_match_aux_pin_ident(
        pattern: PinIdentPattern, tau: gtypes.Type, gamma_env: TypeEnv, sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if sigma := sigma_env.get(pattern.identifier):
        if gtypes.is_higher_order(tau) or gtypes.is_higher_order(sigma):
            return BasePatternMatchError(
                kind=PatternErrorEnum.arrow_types_into_pinned_identifier,
                args={"identifier": pattern.identifier, "tau": tau, "sigma": sigma},
            )
        elif not isinstance(mu := gtypes.infimum(tau, sigma), gtypes.SupremumError):
            return PatternMatchAuxSuccess(gamma_env, lambda env: mu)
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_type_for_pinned_variable,
            args={"identifier": pattern.identifier, "tau": tau, "sigma": sigma},
        )
    else:
        return BasePatternMatchError(
            kind=PatternErrorEnum.pinned_identifier_not_found_in_environment,
            args={"identifier": pattern.identifier},
        )


def pattern_match_aux_wild(
    _pattern: WildPattern, tau: gtypes.Type, gamma_env: TypeEnv, _sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    return PatternMatchAuxSuccess(gamma_env, lambda env: tau)


def pattern_match_aux_elist(
    _pattern: ElistPattern, tau: gtypes.Type, gamma_env: TypeEnv, _sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if gtypes.is_subtype(gtypes.ElistType(), tau):
        return PatternMatchAuxSuccess(gamma_env, lambda env: gtypes.ElistType())
    else:
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_type_for_elist, args={"tau": tau},
        )


def pattern_match_aux_list(
        pattern: ListPattern, tau: gtypes.Type, gamma_env: TypeEnv, sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if not isinstance(tau, gtypes.ListType):
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_constructors_error,
            args={"pattern": pattern, "tau": tau},
        )
    head_pattern_match_result = pattern_match_aux(pattern.head, tau.type, gamma_env, sigma_env)
    if isinstance(head_pattern_match_result, PatternMatchError):
        return NestedPatternMatchError(
            error=head_pattern_match_result, context=ListPatternContext(head=True, pattern=pattern)
        )
    tail_pattern_match_result = pattern_match_aux(pattern.tail, tau, head_pattern_match_result.env, sigma_env)
    if isinstance(tail_pattern_match_result, PatternMatchError):
        return NestedPatternMatchError(
            error=tail_pattern_match_result, context=ListPatternContext(head=False, pattern=pattern)
        )

    def ret_mapping(env: TypeEnv):
        nonlocal head_pattern_match_result, tail_pattern_match_result
        assert isinstance(head_pattern_match_result, PatternMatchAuxSuccess)
        assert isinstance(tail_pattern_match_result, PatternMatchAuxSuccess)
        if isinstance(head_type := head_pattern_match_result.mapping(env), gtypes.TypingError):
            return head_pattern_match_result
        elif isinstance(tail_type := tail_pattern_match_result.mapping(env), gtypes.TypingError):
            return tail_pattern_match_result
        else:
            return gtypes.supremum(gtypes.ListType(head_type), tail_type)

    return PatternMatchAuxSuccess(env=tail_pattern_match_result.env, mapping=ret_mapping)


def pattern_match_aux_tuple(
        pattern: TuplePattern, tau: gtypes.Type, gamma_env: TypeEnv, sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if not isinstance(tau, gtypes.TupleType):
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_constructors_error,
            args={"pattern": pattern, "tau": tau},
        )
    if len(pattern.items) != len(tau.types):
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_tuples_error,
            args={"pattern": pattern, "tau": tau},
        )
    pattern_match_mapping_results = []
    gamma_env_aux = gamma_env.copy()
    for i in range(len(pattern.items)):
        aux = pattern_match_aux(pattern.items[i], tau.types[i], gamma_env_aux, sigma_env)
        if isinstance(aux, PatternMatchError):
            return NestedPatternMatchError(
                error=aux, context=TuplePatternContext(n=i + 1, pattern=pattern)
            )
        else:
            assert isinstance(aux, PatternMatchAuxSuccess)
            pattern_match_mapping_results.append(aux.mapping)
            gamma_env_aux = aux.env

    def ret_mapping(env: TypeEnv):
        nonlocal pattern_match_mapping_results
        items = []
        for mapping in pattern_match_mapping_results:
            aux_type = mapping(env)
            if isinstance(aux_type, gtypes.TypingError):
                return aux_type
            items.append(aux_type)
        return gtypes.TupleType(items)

    return PatternMatchAuxSuccess(env=gamma_env_aux, mapping=ret_mapping)


def pattern_match_aux_map(
    pattern: MapPattern, tau: gtypes.Type, gamma_env: TypeEnv, sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if not isinstance(tau, gtypes.MapType):
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_constructors_error,
            args={"pattern": pattern, "tau": tau},
        )
    if not all([k in tau.map_type.keys() for k in pattern.map.keys()]):
        return BasePatternMatchError(
            kind=PatternErrorEnum.incompatible_maps_error,
            args={"pattern": pattern, "tau": tau},
        )
    pattern_match_mapping_results_dict: t.Dict[
        gtypes.MapKey, t.Callable[[TypeEnv], t.Union[gtypes.Type, gtypes.TypingError]]
    ] = {}
    gamma_env_aux = gamma_env
    for key in tau.map_type.keys():
        if key not in pattern.map.keys():
            value = tau.map_type[key]
            pattern_match_mapping_results_dict[key] = lambda d: value
            continue
        aux = pattern_match_aux(
            pattern.map[key], tau.map_type[key], gamma_env_aux, sigma_env
        )
        if isinstance(aux, PatternMatchError):
            return NestedPatternMatchError(
                error=aux, context=MapPatternContext(key=key, pattern=pattern)
            )
        else:
            pattern_match_mapping_results_dict[key] = aux.mapping
            gamma_env_aux = aux.env

    def ret_mapping(env: TypeEnv):
        nonlocal pattern_match_mapping_results_dict
        items: t.Dict[gtypes.MapKey, gtypes.Type] = {}
        for k in pattern_match_mapping_results_dict.keys():
            aux_type = pattern_match_mapping_results_dict[k](env)
            if isinstance(aux_type, gtypes.TypingError):
                return aux_type
            items[k] = aux_type
        return gtypes.MapType(items)

    return PatternMatchAuxSuccess(env=gamma_env_aux, mapping=ret_mapping)


def pattern_match_aux_any(
    pattern: Pattern, tau: gtypes.AnyType, gamma_env: TypeEnv, sigma_env: TypeEnv
) -> PatternMatchAuxResult:
    if isinstance(pattern, ElistPattern):
        ground_tau: gtypes.Type = gtypes.ElistType()
    elif isinstance(pattern, ListPattern):
        ground_tau = gtypes.ListType(tau)
    elif isinstance(pattern, TuplePattern):
        ground_tau = gtypes.TupleType([tau for _ in pattern.items])
    else:
        assert isinstance(pattern, MapPattern)
        ground_tau = gtypes.MapType({k: tau for k in pattern.map})
    return pattern_match_aux(pattern, ground_tau, gamma_env, sigma_env)


@dataclass
class PatternMatchSuccess:
    type: gtypes.Type
    env: TypeEnv


PatternMatchResult = t.Union[PatternMatchSuccess, PatternMatchError]


def pattern_match(
    pattern: Pattern, tau: gtypes.Type, gamma_env: TypeEnv, sigma_env: TypeEnv,
) -> PatternMatchResult:
    pattern_match_result = pattern_match_aux(pattern, tau, gamma_env, sigma_env)
    if isinstance(pattern_match_result, PatternMatchError):
        return pattern_match_result
    ret_type = pattern_match_result.mapping(pattern_match_result.env)
    if isinstance(ret_type, gtypes.TypingError):
        return BasePatternMatchError(kind=PatternErrorEnum.incompatible_type_for_pattern, args={})
    return PatternMatchSuccess(type=ret_type, env=pattern_match_result.env)
