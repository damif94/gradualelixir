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
        return "{" + ", ".join([str(item) for item in self.items]) + "}"


@dataclass
class ElistPattern(Pattern):
    def __str__(self):
        return "[]"


@dataclass
class ListPattern(Pattern):
    head: Pattern
    tail: Pattern

    def __init__(self, head, tail):
        if not any(
            [
                isinstance(tail, ListPattern),
                isinstance(tail, ElistPattern),
                isinstance(tail, WildPattern),
                isinstance(tail, IdentPattern),
            ]
        ):
            raise SyntaxRestrictionError("List pattern's tail is not valid")
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
        return "%{" + ", ".join([f"{k} => {v}" for (k, v) in zip(keys, str_values)]) + "}"


def format_pattern_match(pattern: Pattern, type: gtypes.Type, padding="") -> str:
    code = f"{pattern} = {type}"
    needs_formatting = False
    if len(str(code)) > 50:  # pattern match is too long
        needs_formatting = True

    if needs_formatting:  # is multiline
        from gradualelixir.elixir_port import format_code

        msg = format_code(code)
        return "\n\n" + "\n".join([padding + m for m in msg.split("\n")])
    else:
        return f" {code}"


class PatternErrorEnum(enum.Enum):
    incompatible_type_for_variable = "Couldn't match identifier {identifier}'s current type with this type"
    incompatible_type_for_literal = "Couldn't match literal {literal} with this type"
    arrow_types_into_nonlinear_identifier = (
        "Can't match {identifier}'s current type against this type. "
        "Arrow types can only be used for assignment in pattern matches"
    )
    incompatible_type_for_pinned_variable = (
        "Couldn't match pinned identifier {identifier}'s current type against this type"
    )
    pinned_identifier_not_found_in_environment = (
        "Couldn't find pinned variable ^{identifier} in the pattern environment"
    )
    arrow_types_into_pinned_identifier = (
        "Can't match ^{identifier}'s current type  in external environment.\n"
        "Arrow types can only be used for assignment in pattern matches"
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
            return "In the head pattern"
        return "In the tail pattern"


@dataclass
class TuplePatternContext(PatternContext):
    n: int

    def __str__(self):
        return f"In the {ordinal(self.n)} pattern"


@dataclass
class MapPatternContext(PatternContext):
    key: gtypes.MapKey

    def __str__(self):
        return f"In the pattern for key {self.key}"


class PatternMatchError:
    pattern: Pattern
    type: gtypes.Type

    def _message(self, padding=""):
        raise NotImplementedError()

    @staticmethod
    def env_message(padding="", env: gtypes.TypeEnv = None, external_env: gtypes.TypeEnv = None):
        env_msg = ""
        external_env_msg = ""
        eol = ""
        if env is not None:
            env_msg = f"{padding}{Bcolors.OKBLUE}Current Pattern Variables:{Bcolors.ENDC} {env}\n"
            eol = "\n"
        if external_env is not None:
            external_env_msg = f"{padding}{Bcolors.OKBLUE}External Variables:{Bcolors.ENDC} {external_env}\n"
            eol = "\n"
        return env_msg + external_env_msg + eol

    def message(self, padding=""):
        pattern_msg = format_pattern_match(self.pattern, self.type, padding + "    ")
        return (
            f"{padding}{Bcolors.OKBLUE}Pattern match type check failed on pattern match{Bcolors.ENDC} "
            f"{pattern_msg}\n"
            f"{self._message(padding)}\n"
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

    def _message(self, padding=""):
        args = {k: str(arg) for k, arg in self.args.items()}
        error_msg = self.kind.value.format(**args)
        return f"{padding}{Bcolors.FAIL}    {error_msg}{Bcolors.ENDC}\n"


@dataclass
class NestedPatternMatchError(PatternMatchError):
    pattern: Pattern
    type: gtypes.Type
    env: gtypes.TypeEnv
    external_env: gtypes.TypeEnv
    context: PatternContext
    bullet: PatternMatchError

    def __str__(self):
        return self._message()

    def _message(self, padding=""):
        env_msg = self.env_message(padding + "    ", self.env, self.external_env)
        bullet_expression_msg = format_pattern_match(
            pattern=self.bullet.pattern, type=self.bullet.type, padding=padding + "    "
        )
        bullet_msg = self.bullet._message(padding + "  ")
        return (
            f"\n{padding}{Bcolors.OKBLUE}  > {self.context}: {Bcolors.ENDC}"
            f"{bullet_expression_msg}\n\n"
            f"{env_msg}"
            f"{bullet_msg}\n"
        )


@dataclass
class PatternMatchAuxSuccess:
    env: gtypes.TypeEnv
    mapping: t.Callable[[gtypes.TypeEnv], t.Union[gtypes.Type, gtypes.TypingError]]


CollectVarsResult = t.Union[gtypes.TypeEnv, PatternMatchError]
RefineTypeResult = t.Union[gtypes.Type, PatternMatchError]


def collect_vars(
    pattern: Pattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    if isinstance(pattern, LiteralPattern):
        return collect_vars_literal(pattern, type, env, external_env)
    if isinstance(pattern, IdentPattern):
        return collect_vars_ident(pattern, type, env, external_env)
    if isinstance(pattern, PinIdentPattern):
        return collect_vars_pin_ident(pattern, type, env, external_env)
    if isinstance(pattern, WildPattern):
        return collect_vars_wild(pattern, type, env, external_env)
    if isinstance(type, gtypes.AnyType):
        return collect_vars_any(pattern, type, env, external_env)
    if isinstance(pattern, ElistPattern):
        return collect_vars_elist(pattern, type, env, external_env)
    if isinstance(pattern, ListPattern):
        return collect_vars_list(pattern, type, env, external_env)
    if isinstance(pattern, TuplePattern):
        return collect_vars_tuple(pattern, type, env, external_env)
    else:
        assert isinstance(pattern, MapPattern)
        return collect_vars_map(pattern, type, env, external_env)


def collect_vars_literal(
    pattern: LiteralPattern, type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    if gtypes.is_subtype(pattern.type, type):
        return env
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_literal,
            args={"literal": gtypes.MapKey(pattern.value)},
        )


def collect_vars_ident(
    pattern: IdentPattern, type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    if sigma := env.get(pattern.identifier):
        if gtypes.is_higher_order(type) or gtypes.is_higher_order(sigma):
            return BasePatternMatchError(
                pattern=pattern,
                type=type,
                kind=PatternErrorEnum.arrow_types_into_nonlinear_identifier,
                args={"identifier": pattern.identifier},
            )
        if not isinstance(mu := gtypes.infimum(type, sigma), gtypes.TypingError):
            new_env = env.copy()
            new_env[pattern.identifier] = mu
            return new_env
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_variable,
            args={"identifier": pattern.identifier},
        )
    else:
        new_env = env.copy()
        new_env[pattern.identifier] = type
        return new_env


def collect_vars_pin_ident(
    pattern: PinIdentPattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    if sigma := external_env.get(pattern.identifier):
        if gtypes.is_higher_order(type) or gtypes.is_higher_order(sigma):
            return BasePatternMatchError(
                pattern=pattern,
                type=type,
                kind=PatternErrorEnum.arrow_types_into_pinned_identifier,
                args={"identifier": pattern.identifier},
            )
        elif not isinstance(gtypes.infimum(type, sigma), gtypes.SupremumError):
            return env
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_pinned_variable,
            args={"identifier": pattern.identifier},
        )
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.pinned_identifier_not_found_in_environment,
            args={"identifier": pattern.identifier},
        )


def collect_vars_wild(
    _pattern: WildPattern, _type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    return env


def collect_vars_elist(
    pattern: ElistPattern, type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    if gtypes.is_subtype(gtypes.ElistType(), type):
        return env
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
        )


def collect_vars_list(
    pattern: ListPattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    if not isinstance(type, gtypes.ListType):
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
        )
    head_pattern_match_result = collect_vars(pattern.head, type.type, env, external_env)
    if isinstance(head_pattern_match_result, PatternMatchError):
        return NestedPatternMatchError(
            pattern=pattern,
            type=type,
            env=env,
            external_env=external_env,
            context=ListPatternContext(head=True),
            bullet=head_pattern_match_result,
        )
    tail_pattern_match_result = collect_vars(pattern.tail, type, head_pattern_match_result, external_env)
    if isinstance(tail_pattern_match_result, PatternMatchError):
        return NestedPatternMatchError(
            pattern=pattern,
            type=type,
            env=head_pattern_match_result,
            external_env=external_env,
            context=ListPatternContext(head=False),
            bullet=tail_pattern_match_result,
        )

    return tail_pattern_match_result


def collect_vars_tuple(
    pattern: TuplePattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> CollectVarsResult:
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
            args={"n": len(pattern.items), "m": len(type.types)},
        )
    env_acc = env.copy()
    for i in range(len(pattern.items)):
        aux = collect_vars(pattern.items[i], type.types[i], env_acc, external_env)
        if isinstance(aux, PatternMatchError):
            return NestedPatternMatchError(
                pattern=pattern,
                type=type,
                env=env_acc,
                external_env=external_env,
                context=TuplePatternContext(n=i + 1),
                bullet=aux,
            )
        else:
            assert isinstance(aux, gtypes.TypeEnv)
            env_acc = aux
    return env_acc


def collect_vars_map(
    pattern: MapPattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    if not isinstance(type, gtypes.MapType):
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
            args={"type": type},
        )
    if len(missing_keys_on_type := [k for k in pattern.map.keys() if k not in type.map_type.keys()]) > 0:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_maps_error,
            args={"k": missing_keys_on_type[0]},
        )
    env_acc = env.copy()
    for key in type.map_type.keys():
        if key not in pattern.map.keys():
            continue
        aux = collect_vars(pattern.map[key], type.map_type[key], env_acc, external_env)
        if isinstance(aux, PatternMatchError):
            return NestedPatternMatchError(
                pattern=pattern,
                type=type,
                env=env_acc,
                context=MapPatternContext(key=key),
                external_env=external_env,
                bullet=aux,
            )
        else:
            assert isinstance(aux, gtypes.TypeEnv)
            env_acc = aux
    return env_acc


def collect_vars_any(
    pattern: Pattern, type: gtypes.AnyType, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> CollectVarsResult:
    if isinstance(pattern, ElistPattern):
        ground_type: gtypes.Type = gtypes.ElistType()
    elif isinstance(pattern, ListPattern):
        ground_type = gtypes.ListType(type)
    elif isinstance(pattern, TuplePattern):
        ground_type = gtypes.TupleType([type for _ in pattern.items])
    else:
        assert isinstance(pattern, MapPattern)
        ground_type = gtypes.MapType({k: type for k in pattern.map})
    return collect_vars(pattern, ground_type, env, external_env)


def refine_type(
    pattern: Pattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    if isinstance(pattern, LiteralPattern):
        return refine_type_literal(pattern, type, env, external_env)
    if isinstance(pattern, IdentPattern):
        return refine_type_ident(pattern, type, env, external_env)
    if isinstance(pattern, PinIdentPattern):
        return refine_type_pin_ident(pattern, type, env, external_env)
    if isinstance(pattern, WildPattern):
        return refine_type_wild(pattern, type, env, external_env)
    if isinstance(type, gtypes.AnyType):
        return refine_type_any(pattern, type, env, external_env)
    if isinstance(pattern, ElistPattern):
        return refine_type_elist(pattern, type, env, external_env)
    if isinstance(pattern, ListPattern):
        return refine_type_list(pattern, type, env, external_env)
    if isinstance(pattern, TuplePattern):
        return refine_type_tuple(pattern, type, env, external_env)
    else:
        assert isinstance(pattern, MapPattern)
        return refine_type_map(pattern, type, env, external_env)


def refine_type_literal(
    pattern: LiteralPattern, type: gtypes.Type, _env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    if gtypes.is_subtype(pattern.type, type):
        return pattern.type
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_literal,
            args={"literal": gtypes.MapKey(pattern.value)},
        )


def refine_type_ident(
    pattern: IdentPattern, type: gtypes.Type, env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    if sigma := env.get(pattern.identifier):
        if gtypes.is_higher_order(type) or gtypes.is_higher_order(sigma):
            return BasePatternMatchError(
                pattern=pattern,
                type=type,
                kind=PatternErrorEnum.arrow_types_into_nonlinear_identifier,
                args={"identifier": pattern.identifier},
            )
        if not isinstance(mu := gtypes.infimum(type, sigma), gtypes.TypingError):
            return mu
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_variable,
            args={"identifier": pattern.identifier},
        )
    else:
        return type


def refine_type_pin_ident(
    pattern: PinIdentPattern, type: gtypes.Type, _env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    if sigma := external_env.get(pattern.identifier):
        if gtypes.is_higher_order(type) or gtypes.is_higher_order(sigma):
            return BasePatternMatchError(
                pattern=pattern,
                type=type,
                kind=PatternErrorEnum.arrow_types_into_pinned_identifier,
                args={"identifier": pattern.identifier},
            )
        elif not isinstance(mu := gtypes.infimum(type, sigma), gtypes.SupremumError):
            return mu
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_type_for_pinned_variable,
            args={"identifier": pattern.identifier},
        )
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.pinned_identifier_not_found_in_environment,
            args={"identifier": pattern.identifier},
        )


def refine_type_wild(
    _pattern: WildPattern, type: gtypes.Type, _env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    return type


def refine_type_elist(
    pattern: ElistPattern, type: gtypes.Type, _env: gtypes.TypeEnv, _external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    if gtypes.is_subtype(gtypes.ElistType(), type):
        return gtypes.ElistType()
    else:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
        )


def refine_type_list(
    pattern: ListPattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    if not isinstance(type, gtypes.ListType):
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
        )
    head_pattern_match_result = refine_type(pattern.head, type.type, env, external_env)
    if isinstance(head_pattern_match_result, PatternMatchError):
        return NestedPatternMatchError(
            pattern=pattern,
            type=type,
            env=env,
            external_env=external_env,
            context=ListPatternContext(head=True),
            bullet=head_pattern_match_result,
        )
    tail_pattern_match_result = refine_type(pattern.tail, type, env, external_env)
    if isinstance(tail_pattern_match_result, PatternMatchError):
        return NestedPatternMatchError(
            pattern=pattern,
            type=type,
            env=env,
            external_env=external_env,
            context=ListPatternContext(head=False),
            bullet=tail_pattern_match_result,
        )

    assert isinstance(head_pattern_match_result, gtypes.Type)
    assert isinstance(tail_pattern_match_result, gtypes.Type)
    ret_type = gtypes.supremum(gtypes.ListType(head_pattern_match_result), tail_pattern_match_result)
    if isinstance(ret_type, gtypes.TypingError):
        return BasePatternMatchError(
            pattern=pattern, type=type, kind=PatternErrorEnum.incompatible_type_for_pattern, args={}
        )
    return ret_type


def refine_type_tuple(
    pattern: TuplePattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> RefineTypeResult:
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
            args={"n": len(pattern.items), "m": len(type.types)},
        )
    types: t.List[gtypes.Type] = []
    for i in range(len(pattern.items)):
        aux = refine_type(pattern.items[i], type.types[i], env, external_env)
        if isinstance(aux, PatternMatchError):
            return NestedPatternMatchError(
                pattern=pattern,
                type=type,
                env=env,
                external_env=external_env,
                context=TuplePatternContext(n=i + 1),
                bullet=aux,
            )
        else:
            assert isinstance(aux, gtypes.Type)
            types.append(aux)

    return gtypes.TupleType(types)


def refine_type_map(
    pattern: MapPattern, type: gtypes.Type, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    if not isinstance(type, gtypes.MapType):
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_constructors_error,
            args={"type": type},
        )
    if len(missing_keys_on_type := [k for k in pattern.map.keys() if k not in type.map_type.keys()]) > 0:
        return BasePatternMatchError(
            pattern=pattern,
            type=type,
            kind=PatternErrorEnum.incompatible_maps_error,
            args={"k": missing_keys_on_type[0]},
        )
    types_dict: t.Dict[gtypes.MapKey, gtypes.Type] = {}
    for key in type.map_type.keys():
        if key not in pattern.map.keys():
            types_dict[key] = type.map_type[key]
            continue
        aux = refine_type(pattern.map[key], type.map_type[key], env, external_env)
        if isinstance(aux, PatternMatchError):
            return NestedPatternMatchError(
                pattern=pattern,
                type=type,
                env=env,
                context=MapPatternContext(key=key),
                external_env=external_env,
                bullet=aux,
            )
        else:
            types_dict[key] = aux

    return gtypes.MapType(types_dict)


def refine_type_any(
    pattern: Pattern, type: gtypes.AnyType, env: gtypes.TypeEnv, external_env: gtypes.TypeEnv
) -> RefineTypeResult:
    if isinstance(pattern, ElistPattern):
        ground_type: gtypes.Type = gtypes.ElistType()
    elif isinstance(pattern, ListPattern):
        ground_type = gtypes.ListType(type)
    elif isinstance(pattern, TuplePattern):
        ground_type = gtypes.TupleType([type for _ in pattern.items])
    else:
        assert isinstance(pattern, MapPattern)
        ground_type = gtypes.MapType({k: type for k in pattern.map})
    return refine_type(pattern, ground_type, env, external_env)


@dataclass
class PatternMatchSuccess:
    pattern: Pattern
    type: gtypes.Type
    external_env: gtypes.TypeEnv
    hijacked_pattern_env: gtypes.TypeEnv
    refined_type: gtypes.Type
    exported_env: gtypes.TypeEnv

    def __str__(self):
        pattern_msg = format_pattern_match(self.pattern, self.type, padding="    ")
        hijacked_pattern_env_msg = (
            f"{Bcolors.OKBLUE}Hijacked Pattern Variables:{Bcolors.ENDC} {self.hijacked_pattern_env}\n"
            if self.hijacked_pattern_env.env != {}
            else ""
        )
        return (
            f"{Bcolors.OKBLUE}Type check success for{Bcolors.ENDC} {pattern_msg}\n\n"
            f"{Bcolors.OKBLUE}Variables:{Bcolors.ENDC} {self.external_env}\n"
            f"{hijacked_pattern_env_msg}"
            f"{Bcolors.OKBLUE}Refined Type:{Bcolors.ENDC} {self.refined_type}\n"
            f"{Bcolors.OKBLUE}Exported Variables:{Bcolors.ENDC} {self.exported_env}\n"
        )


PatternMatchResult = t.Union[PatternMatchSuccess, PatternMatchError]


def type_check(
    pattern: Pattern,
    type: gtypes.Type,
    env: gtypes.TypeEnv,
    external_env: gtypes.TypeEnv,
) -> PatternMatchResult:
    collect_vars_result = collect_vars(pattern, type, env, external_env)
    if isinstance(collect_vars_result, PatternMatchError):
        return collect_vars_result
    refine_types_result = refine_type(pattern, type, collect_vars_result, external_env)
    if isinstance(refine_types_result, PatternMatchError):
        return refine_types_result
    return PatternMatchSuccess(pattern, type, external_env, env, refine_types_result, collect_vars_result)
