from dataclasses import dataclass
import typing as t
from gradualelixir.gtypes import definitions as types


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
    type: types.Type
    value: t.Any


@dataclass
class IntegerPattern(LiteralPattern):
    value: int

    def __init__(self, value: int):
        self.type = types.IntegerType()
        self.value = value

    def __str__(self):
        return str(self.value)


@dataclass
class FloatPattern(LiteralPattern):
    value: float

    def __init__(self, value: float):
        self.type = types.FloatType()
        self.value = value

    def __str__(self):
        return str(self.value)


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
                f"List pattern's tail should be either a List Pattern or an Elist Pattern"
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


@dataclass
class PatternError:
    msg: str
    bullet: t.Optional['PatternError'] = None


class SyntaxException(Exception):
    pass


@dataclass
class PatternMatchReturnType:
    type: types.Type
    env: t.Dict[str, types.Type]


def pattern_match(
    pattern: Pattern, tau: types.Type, gamma_env: t.Dict[str, types.Type], sigma_env: t.Dict[str, types.Type]
) -> t.Union[PatternMatchReturnType, PatternError]:
    if isinstance(pattern, LiteralPattern):
        # TP_LIT
        if types.is_msubtype_minus(tau, pattern.type):
            return PatternMatchReturnType(pattern.type, gamma_env)
        else:
            return PatternError(f"Couldn't match literal {pattern.value} with type {tau}")
    elif isinstance(pattern, IdentPattern):
        if sigma := gamma_env.get(pattern.identifier):
            # TP_VARN
            if types.is_higher_order(tau) or types.is_higher_order(sigma):
                return PatternError(
                    f"Can't match {pattern.identifier}'s current type {tau} against {sigma}. "
                    f"Arrow types can only be used for assignment in pattern matches"
                )
            if types.is_allowed(mu := types.minfimum_plus(tau, sigma)):
                gamma_env[pattern.identifier] = mu
                return PatternMatchReturnType(mu, gamma_env)
            return PatternError(
                f"Couldn't match identifier {pattern.identifier}'s current type {sigma} with {tau}"
            )
        else:
            # TP_VARE
            gamma_env[pattern.identifier] = tau
            return PatternMatchReturnType(tau, gamma_env)
    elif isinstance(pattern, PinIdentPattern):
        # TP_PIN
        if sigma := sigma_env.get(pattern.identifier):
            if types.is_higher_order(tau) or types.is_higher_order(sigma):
                return PatternError(
                   f"Can't match ^{pattern.identifier}'s current type {tau} with {sigma} in external environment. "
                   f"Arrow types can only be used for assignment in pattern matches"
                )
            elif types.is_allowed(mu := types.minfimum_plus(tau, sigma)):
                gamma_env[pattern.identifier] = mu
                return PatternMatchReturnType(mu, gamma_env)
            return PatternError(
                f"Couldn't match pinned identifier {pattern.identifier}'s current type {sigma} with {tau}"
            )
        else:
            return PatternError(
                f"Couldn't find pinned variable ^{pattern.identifier} in the environment"
            )
    elif isinstance(pattern, WildPattern):
        # TP_WILD
        return PatternMatchReturnType(tau, gamma_env)
    elif isinstance(pattern, ElistPattern) and isinstance(tau, types.ListType):
        # TP_ELIST
        return PatternMatchReturnType(types.ListType(types.NoneType()), gamma_env)
    elif isinstance(pattern, ListPattern) and isinstance(tau, types.ListType):
        # TP_LIST
        aux_head = pattern_match(pattern.head, tau.type, gamma_env, sigma_env)
        if isinstance(aux_head, PatternError):
            return PatternError(
                f"Errors matching list {pattern} against type {tau}",
                PatternError(f"In the head pattern: {aux_head.msg}", aux_head.bullet)
            )
        aux_tail = pattern_match(pattern.tail, tau, aux_head.env, sigma_env)
        if isinstance(aux_tail, PatternError):
            return PatternError(
                f"Errors matching list {pattern} against type {tau}",
                PatternError(f"In the tail pattern: {aux_tail.msg}", aux_tail.bullet)
            )
        assert isinstance(aux_tail.type, types.ListType)
        aux_head.type = refine_type(
            pattern.head, aux_head.type, aux_tail.env, sigma_env
        )
        return PatternMatchReturnType(
            types.minfimum_minus(types.ListType(aux_head.type), aux_tail.type), aux_tail.env
        )
    elif isinstance(pattern, TuplePattern) and isinstance(tau, types.TupleType):
        # TP_TUPLE
        if len(pattern.items) != len(tau.types):
            return PatternError(
                f"Couldn't match tuple {pattern} against type {tau} because they have different sizes"
            )
        types_acc: t.List[types.Type] = []
        gamma_env_aux = gamma_env
        for i in range(len(pattern.items)):
            aux = pattern_match(pattern.items[i], tau.types[i], gamma_env_aux, sigma_env)
            if isinstance(aux, PatternError):
                return PatternError(
                    f"Errors matching tuple {pattern} against type {tau}",
                    PatternError(f"In the {i + 1}'s pattern: {aux.msg}", aux.bullet)
                )
            types_acc.append(aux.type)
            gamma_env_aux = aux.env
        return PatternMatchReturnType(
            refine_type(pattern, types.TupleType(types_acc), gamma_env_aux, sigma_env),
            gamma_env_aux
        )
    elif isinstance(pattern, MapPattern) and isinstance(tau, types.MapType):
        # TP_MAP
        if not all([key in pattern.map for key in tau.map_type]):
            return PatternError(
                f"Couldn't match tuple {pattern} against type {tau} because they some of {tau} keys "
                f"are not present in {pattern}"
            )
        else:
            types_map_acc: t.Dict[int, types.Type] = {}
            gamma_env_aux = gamma_env
            for key in tau.map_type:
                aux = pattern_match(pattern.map[key], tau.map_type[key], gamma_env_aux, sigma_env)
                if isinstance(aux, PatternError):
                    return PatternError(
                        f"Errors matching tuple {str(pattern)} against type {str(tau)}",
                        PatternError(f"In the pattern for key {key}: {aux.msg}", aux.bullet)
                    )
                types_map_acc[key] = aux.type
                gamma_env_aux = aux.env
            return PatternMatchReturnType(
                refine_type(pattern, types.MapType(types_map_acc), gamma_env_aux, sigma_env),
                gamma_env_aux
            )
    elif isinstance(tau, types.AnyType):
        if isinstance(pattern, ElistPattern) or isinstance(pattern, ListPattern):
            ground_tau: types.Type = types.ListType(tau)
        elif isinstance(pattern, TuplePattern):
            ground_tau = types.TupleType([tau for _ in pattern.items])
        else:
            assert isinstance(pattern, MapPattern)
            ground_tau = types.MapType({k: tau for k in pattern.map})
        return pattern_match(pattern, ground_tau, gamma_env, sigma_env)
    else:
        assert any([
            isinstance(pattern, ElistPattern),
            isinstance(pattern, ListPattern),
            isinstance(pattern, TuplePattern),
            isinstance(pattern, MapPattern)
        ])
        assert any([
            isinstance(pattern, ElistPattern) and not isinstance(tau, types.ListType),
            isinstance(pattern, ListPattern) and not isinstance(tau, types.ListType),
            isinstance(pattern, TuplePattern) and not isinstance(tau, types.TupleType),
            isinstance(pattern, MapPattern) and not isinstance(tau, types.MapType),
            isinstance(tau, types.FunctionType)
        ])
        return PatternError(f"Error matching {pattern} with type {tau}: wrong shape")


def refine_type(
    pattern: Pattern, candidate_type: types.Type, gamma_env: t.Dict[str, types.Type], sigma_env: t.Dict[str, types.Type]
) -> types.Type:
    if isinstance(pattern, LiteralPattern):
        return candidate_type
    elif isinstance(pattern, IdentPattern):
        return gamma_env[pattern.identifier]
    elif isinstance(pattern, PinIdentPattern):
        return sigma_env[pattern.identifier]
    elif isinstance(pattern, WildPattern):
        return candidate_type
    elif isinstance(pattern, ElistPattern):
        return candidate_type
    elif isinstance(pattern, ListPattern):
        assert isinstance(candidate_type, types.ListType)
        aux_head = refine_type(pattern.head, candidate_type.type, gamma_env, sigma_env)
        aux_tail = refine_type(pattern.tail, candidate_type, gamma_env, sigma_env)
        return types.minfimum_minus(types.ListType(aux_head), aux_tail)
    elif isinstance(pattern, TuplePattern):
        assert isinstance(candidate_type, types.TupleType)
        assert len(pattern.items) == len(candidate_type.types)
        return types.TupleType([
            refine_type(pattern.items[i], candidate_type.types[i], gamma_env, sigma_env)
            for i in range(len(pattern.items))
        ])
    else:
        assert isinstance(pattern, MapPattern)
        assert isinstance(candidate_type, types.MapType)
        assert all([key in pattern.map for key in candidate_type.map_type])
        return types.MapType({
            k: refine_type(pattern.map[k], candidate_type.map_type[k], gamma_env, sigma_env)
            for k in candidate_type.map_type
        })
