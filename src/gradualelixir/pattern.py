import enum
import typing as t
from dataclasses import dataclass

from gradualelixir import gtypes
from gradualelixir.exception import SyntaxRestrictionError
from gradualelixir.gtypes import LiteralType
from gradualelixir.utils import Bcolors, ordinal


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
        return '{' + ', '.join([str(item) for item in self.items]) + '}'


@dataclass
class ElistPattern(Pattern):
    def __str__(self):
        return '[]'


@dataclass
class ListPattern(Pattern):
    head: Pattern
    tail: Pattern

    def __init__(self, head, tail):
        if not (isinstance(tail, ListPattern) or isinstance(tail, ElistPattern) or isinstance(tail, WildPattern)):
            raise SyntaxRestrictionError("List pattern's tail should be either a List Pattern or an Elist Pattern")
        self.head = head
        self.tail = tail

    def __str__(self):
        return f'[{str(self.head)} | {str(self.tail)}]'


@dataclass
class MapPattern(Pattern):

    map: t.OrderedDict[gtypes.MapKey, Pattern]

    def __str__(self):
        keys = self.map.keys()
        str_values = [str(v) for _, v in self.map.items()]
        return '%{' + ', '.join([f'{k} => {v}' for (k, v) in zip(keys, str_values)]) + '}'


def format_pattern_match(pattern: Pattern, type: gtypes.Type, padding='') -> str:
    code = f'{pattern} = {type}'
    needs_formatting = False
    if len(str(code)) > 50:  # pattern match is too long
        needs_formatting = True

    if needs_formatting:  # is multiline
        from gradualelixir.elixir_port import format_code

        msg = format_code(code)
        return '\n\n' + '\n'.join([padding + m for m in msg.split('\n')])
    else:
        return f' {code}'


class PatternErrorEnum(enum.Enum):
    incompatible_type_for_variable = "Couldn't match identifier {identifier}'s current type with this type"
    incompatible_type_for_literal = "Couldn't match literal {literal} with this type"
    arrow_types_into_nonlinear_identifier = (
        "Can't match {identifier}'s current type against this type. "
        'Arrow types can only be used for assignment in pattern matches'
    )
    incompatible_type_for_pinned_variable = (
        "Couldn't match pinned identifier {identifier}'s current type against this type"
    )
    pinned_identifier_not_found_in_environment = (
        "Couldn't find pinned variable ^{identifier} in the pattern environment"
    )
    arrow_types_into_pinned_identifier = (
        "Can't match ^{identifier}'s current type  in external environment.\n"
        'Arrow types can only be used for assignment in pattern matches'
    )
    incompatible_tuples_error = "Couldn't match tuples of different sizes ({n} and {m})"
    incompatible_maps_error = "Couldn't match map pattern because of missing {k} key is not present in this type"
    incompatible_constructors_error = "Couldn't match because of shape mismatch"
    incompatible_type_for_pattern = "Couldn't assign a type to the pattern match"


class PatternContext:
    pass


@dataclass
class ListPatternContext(PatternContext):
    head: bool

    def __str__(self):
        if self.head:
            return 'In the head pattern'
        return 'In the tail pattern'


@dataclass
class TuplePatternContext(PatternContext):
    n: int

    def __str__(self):
        return f'In the {ordinal(self.n)} pattern'


@dataclass
class MapPatternContext(PatternContext):
    key: gtypes.MapKey

    def __str__(self):
        return f'In the pattern for key {self.key}'


class PatternMatchError:
    pattern: Pattern
    type: gtypes.Type

    def _message(self, padding='', env: gtypes.TypeEnv = None, external_env: gtypes.TypeEnv = None):
        raise NotImplementedError()

    @staticmethod
    def env_message(padding='', env: gtypes.TypeEnv = None, external_env: gtypes.TypeEnv = None):
        env_msg = ''
        external_env_msg = ''
        eol = ''
        if env is not None:
            env_msg = f'{padding}{Bcolors.OKBLUE}External Variables:{Bcolors.ENDC} {env}\n'
            eol = '\n'
        if external_env is not None:
            external_env_msg = f'{padding}{Bcolors.OKBLUE}Pattern Variables:{Bcolors.ENDC} {external_env}\n'
            eol = '\n'
        return env_msg + external_env_msg + eol

    def message(self, padding='', env: gtypes.TypeEnv = None, external_env: gtypes.TypeEnv = None):
        pattern_msg = format_pattern_match(self.pattern, self.type, padding + '    ')
        env_msg = self.env_message(padding, env, external_env)
        return (
            f'{padding}{Bcolors.OKBLUE}Pattern match type check failed on pattern match{Bcolors.ENDC} '
            f'{pattern_msg}\n\n'
            f'{env_msg}'
            f'{self._message(padding, env, external_env)}\n'
        )


@dataclass
class BasePatternMatchError(PatternMatchError):
    pattern: Pattern
    type: gtypes.Type
    kind: PatternErrorEnum
    args: t.Dict[str, t.Any]

    def __init__(self, pattern: Pattern, type: gtypes.Type, kind: PatternErrorEnum, args: t.Dict[str, t.Any] = None):
        self.pattern = pattern
        self.type = type
        self.kind = kind
        self.args = args or {}

    def __str__(self):
        return self._message()

    def _message(self, padding='', _env: gtypes.TypeEnv = None, _external_env: gtypes.TypeEnv = None):
        args = {k: str(arg) for k, arg in self.args.items()}
        error_msg = self.kind.value.format(**args)
        return f'{padding}{Bcolors.FAIL}    {error_msg}{Bcolors.ENDC}\n'


@dataclass
class NestedPatternMatchError(PatternMatchError):
    pattern: Pattern
    type: gtypes.Type
    env: gtypes.TypeEnv
    context: PatternContext
    bullet: PatternMatchError

    def __str__(self):
        return self._message()

    def _message(self, padding='', env: gtypes.TypeEnv = None, external_env: gtypes.TypeEnv = None):
        env_msg = self.env_message(padding + '    ', env, external_env)
        bullet_expression_msg = format_pattern_match(
            pattern=self.bullet.pattern, type=self.bullet.type, padding=padding + '    '
        )
        bullet_msg = self.bullet._message(padding + '  ', env, external_env)
        return (
            f'\n{padding}{Bcolors.OKBLUE}  > {self.context}: {Bcolors.ENDC}'
            f'{bullet_expression_msg}\n\n'
            f'{env_msg}'
            f'{bullet_msg}\n'
        )


@dataclass
class PatternMatchAuxSuccess:
    env: gtypes.TypeEnv
    mapping: t.Callable[[gtypes.TypeEnv], t.Union[gtypes.Type, gtypes.TypingError]]


PatternMatchAuxResult = t.Union[PatternMatchAuxSuccess, PatternMatchError]


def pattern_match_aux(
    pattern: Pattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if isinstance(pattern, LiteralPattern):
        return pattern_match_aux_literal(pattern, type, env, external_env)
    if isinstance(pattern, IdentPattern):
        return pattern_match_aux_ident(pattern, type, env, external_env)
    if isinstance(pattern, PinIdentPattern):
        return pattern_match_aux_pin_ident(pattern, type, env, external_env)
    if isinstance(pattern, WildPattern):
        return pattern_match_aux_wild(pattern, type, env, external_env)
    if isinstance(type, gtypes.AnyType):
        return pattern_match_aux_any(pattern, type, env, external_env)
    if isinstance(pattern, ElistPattern):
        return pattern_match_aux_elist(pattern, type, env, external_env)
    if isinstance(pattern, ListPattern):
        return pattern_match_aux_list(pattern, type, env, external_env)
    if isinstance(pattern, TuplePattern):
        return pattern_match_aux_tuple(pattern, type, env, external_env)
    else:
        assert isinstance(pattern, MapPattern)
        return pattern_match_aux_map(pattern, type, env, external_env)


def pattern_match_aux_literal(
    pattern: LiteralPattern, type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if gtypes.is_subtype(pattern.type, type):
        return PatternMatchAuxSuccess(env, lambda domain: pattern.type)
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_literal,
            args={'literal': pattern.value},
        )


def pattern_match_aux_ident(
    pattern: IdentPattern, type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if sigma := env.get(pattern.identifier):
        if gtypes.is_higher_order(type) or gtypes.is_higher_order(sigma):
            return BasePatternMatchError(
                pattern=pattern,
                type=type,
                kind=PatternErrorEnum.arrow_types_into_nonlinear_identifier,
                args={'identifier': pattern.identifier},
            )
        if not isinstance(mu := gtypes.infimum(type, sigma), gtypes.TypingError):
            new_env = env.copy()
            new_env[pattern.identifier] = mu
            return PatternMatchAuxSuccess(new_env, lambda envv: envv[pattern.identifier])
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_variable,
            args={'identifier': pattern.identifier},
        )
    else:
        new_env = env.copy()
        new_env[pattern.identifier] = type
        return PatternMatchAuxSuccess(new_env, lambda envv: envv[pattern.identifier])


def pattern_match_aux_pin_ident(
    pattern: PinIdentPattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if sigma := external_env.get(pattern.identifier):
        if gtypes.is_higher_order(type) or gtypes.is_higher_order(sigma):
            return BasePatternMatchError(
                pattern=pattern,
                type=type,
                kind=PatternErrorEnum.arrow_types_into_pinned_identifier,
                args={'identifier': pattern.identifier},
            )
        elif not isinstance(mu := gtypes.infimum(type, sigma), gtypes.SupremumError):
            return PatternMatchAuxSuccess(env, lambda envv: mu)
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_pinned_variable,
            args={'identifier': pattern.identifier},
        )
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.pinned_identifier_not_found_in_environment,
            args={'identifier': pattern.identifier},
        )


def pattern_match_aux_wild(
    _pattern: WildPattern, type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    return PatternMatchAuxSuccess(env, lambda envv: type)


def pattern_match_aux_elist(
    pattern: ElistPattern, type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if gtypes.is_subtype(gtypes.ElistType(), type):
        return PatternMatchAuxSuccess(env, lambda envv: gtypes.ElistType())
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
        )


def pattern_match_aux_list(
    pattern: ListPattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if not isinstance(type, gtypes.ListType):
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
        )
    head_pattern_match_result = pattern_match_aux(pattern.head, type.type, env, external_env)
    if isinstance(head_pattern_match_result, PatternMatchError):
        return NestedPatternMatchError(
            pattern=pattern,
            type=type,
            env=env,
            context=ListPatternContext(head=True),
            bullet=head_pattern_match_result,
        )
    tail_pattern_match_result = pattern_match_aux(pattern.tail, type, head_pattern_match_result.env, external_env)
    if isinstance(tail_pattern_match_result, PatternMatchError):
        return NestedPatternMatchError(
            pattern=pattern,
            type=type,
            env=head_pattern_match_result.env,
            context=ListPatternContext(head=False),
            bullet=tail_pattern_match_result,
        )

    def ret_mapping(envv: gtypes.TypeEnv):
        nonlocal head_pattern_match_result, tail_pattern_match_result
        assert isinstance(head_pattern_match_result, PatternMatchAuxSuccess)
        assert isinstance(tail_pattern_match_result, PatternMatchAuxSuccess)
        if isinstance(head_type := head_pattern_match_result.mapping(envv), gtypes.TypingError):
            return head_pattern_match_result
        elif isinstance(tail_type := tail_pattern_match_result.mapping(envv), gtypes.TypingError):
            return tail_pattern_match_result
        else:
            return gtypes.supremum(gtypes.ListType(head_type), tail_type)

    return PatternMatchAuxSuccess(env=tail_pattern_match_result.env, mapping=ret_mapping)


def pattern_match_aux_tuple(
    pattern: TuplePattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if not isinstance(type, gtypes.TupleType):
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
        )
    if len(pattern.items) != len(type.types):
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_tuples_error,
            args={'n': len(pattern.items), 'm': len(type.types)},
        )
    pattern_match_mapping_results = []
    env_aux = env.copy()
    for i in range(len(pattern.items)):
        aux = pattern_match_aux(pattern.items[i], type.types[i], env_aux, external_env)
        if isinstance(aux, PatternMatchError):
            return NestedPatternMatchError(
                pattern=pattern,
                type=type,
                env=env_aux,
                context=TuplePatternContext(n=i + 1),
                bullet=aux,
            )
        else:
            assert isinstance(aux, PatternMatchAuxSuccess)
            pattern_match_mapping_results.append(aux.mapping)
            env_aux = aux.env

    def ret_mapping(envv: gtypes.TypeEnv):
        nonlocal pattern_match_mapping_results
        items = []
        for mapping in pattern_match_mapping_results:
            aux_type = mapping(envv)
            if isinstance(aux_type, gtypes.TypingError):
                return aux_type
            items.append(aux_type)
        return gtypes.TupleType(items)

    return PatternMatchAuxSuccess(env=env_aux, mapping=ret_mapping)


def pattern_match_aux_map(
    pattern: MapPattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if not isinstance(type, gtypes.MapType):
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
            args={'type': type},
        )
    if len(missing_keys_on_type := [k for k in pattern.map.keys() if k not in type.map_type.keys()]) > 0:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_maps_error,
            args={'k': missing_keys_on_type[0]},
        )
    pattern_match_mapping_results_dict: t.Dict[
        gtypes.MapKey, t.Callable[[gtypes.TypeEnv], t.Union[gtypes.Type, gtypes.TypingError]]
    ] = {}
    env_aux = env.copy()
    for key in type.map_type.keys():
        if key not in pattern.map.keys():
            value = type.map_type[key]
            pattern_match_mapping_results_dict[key] = lambda d: value
            continue
        aux = pattern_match_aux(pattern.map[key], type.map_type[key], env_aux, external_env)
        if isinstance(aux, PatternMatchError):
            return NestedPatternMatchError(
                pattern=pattern, type=type, env=env_aux, context=MapPatternContext(key=key), bullet=aux
            )
        else:
            pattern_match_mapping_results_dict[key] = aux.mapping
            env_aux = aux.env

    def ret_mapping(envv: gtypes.TypeEnv):
        nonlocal pattern_match_mapping_results_dict
        items: t.Dict[gtypes.MapKey, gtypes.Type] = {}
        for k in pattern_match_mapping_results_dict.keys():
            aux_type = pattern_match_mapping_results_dict[k](envv)
            if isinstance(aux_type, gtypes.TypingError):
                return aux_type
            items[k] = aux_type
        return gtypes.MapType(items)

    return PatternMatchAuxSuccess(env=env_aux, mapping=ret_mapping)


def pattern_match_aux_any(
    pattern: Pattern, type: gtypes.AnyType, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> PatternMatchAuxResult:
    if isinstance(pattern, ElistPattern):
        ground_type: gtypes.Type = gtypes.ElistType()
    elif isinstance(pattern, ListPattern):
        ground_type = gtypes.ListType(type)
    elif isinstance(pattern, TuplePattern):
        ground_type = gtypes.TupleType([type for _ in pattern.items])
    else:
        assert isinstance(pattern, MapPattern)
        ground_type = gtypes.MapType({k: type for k in pattern.map})
    return pattern_match_aux(pattern, ground_type, env, external_env)


@dataclass
class PatternMatchSuccess:
    type: gtypes.Type
    env: gtypes.TypeEnv

    def message(
        self, pattern: Pattern, type: gtypes.Type, external_env: gtypes.TypeEnv, hijacked_pattern_env: gtypes.TypeEnv
    ):
        pattern_msg = format_pattern_match(pattern, type, padding='    ')
        hijacked_pattern_env_msg = (
            f'{Bcolors.OKBLUE}Hijacked Pattern Variables:{Bcolors.ENDC} {hijacked_pattern_env}\n'
            if hijacked_pattern_env.env != {}
            else ''
        )
        return (
            f'{Bcolors.OKBLUE}Type check success for{Bcolors.ENDC} {pattern_msg}\n\n'
            f'{Bcolors.OKBLUE}Variables:{Bcolors.ENDC} {external_env}\n'
            f'{hijacked_pattern_env_msg}'
            f'{Bcolors.OKBLUE}Refined Type:{Bcolors.ENDC} {self.type}\n'
            f'{Bcolors.OKBLUE}Exported Variables:{Bcolors.ENDC} {self.env}\n'
        )


PatternMatchResult = t.Union[PatternMatchSuccess, PatternMatchError]


def pattern_match(
    pattern: Pattern,
    type: gtypes.Type,
    env: gtypes.TypeEnv,
    external_env: gtypes.TypeEnv,
) -> PatternMatchResult:
    pattern_match_result = pattern_match_aux(pattern, type, env, external_env)
    if isinstance(pattern_match_result, PatternMatchError):
        return pattern_match_result
    ret_type = pattern_match_result.mapping(pattern_match_result.env)
    if isinstance(ret_type, gtypes.TypingError):
        return BasePatternMatchError(
            pattern=pattern, type=type, kind=PatternErrorEnum.incompatible_type_for_pattern, args={}
        )
    return PatternMatchSuccess(type=ret_type, env=pattern_match_result.env)
