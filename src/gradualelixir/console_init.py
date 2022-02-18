from gradualelixir.gtypes import definitions as type_definitions
from gradualelixir.gtypes import utils as type_utils
from gradualelixir.pattern import definitions as pattern_definitions
from gradualelixir.pattern import utils as pattern_utils

term = "term"
none = "none"
integer = "integer"
number = "number"
float = "float"
any = "any"


def is_base_subtype(tau, sigma) -> bool:
    return type_definitions.is_base_subtype(
        type_utils.parse_type(tau),
        type_utils.parse_type(sigma),
    )


def base_supremum(tau, sigma):
    return type_utils.unparse_type(
        type_definitions.base_supremum(
            type_utils.parse_type(tau),
            type_utils.parse_type(sigma),
        )
    )


def base_infimum(tau, sigma):
    return type_utils.unparse_type(
        type_definitions.base_infimum(
            type_utils.parse_type(tau), type_utils.parse_type(sigma)
        )
    )


def is_static_type(tau) -> bool:
    return type_definitions.is_static_type(type_utils.parse_type(tau))


def is_subtype(tau, sigma) -> bool:
    return type_definitions.is_subtype(
        type_utils.parse_type(tau), type_utils.parse_type(sigma)
    )


def is_materialization(tau, sigma) -> bool:
    return type_definitions.is_materialization(
        type_utils.parse_type(tau), type_utils.parse_type(sigma)
    )


def supremum(tau, sigma):
    return type_utils.unparse_type(
        type_definitions.supremum(
            type_utils.parse_type(tau), type_utils.parse_type(sigma)
        )
    )


def infimum(tau, sigma):
    return type_utils.unparse_type(
        type_definitions.infimum(
            type_utils.parse_type(tau), type_utils.parse_type(sigma)
        )
    )


def minfimum_plus(tau, sigma):
    return type_utils.unparse_type(
        type_definitions.infimum(
            type_utils.parse_type(tau), type_utils.parse_type(sigma)
        )
    )


def minfimum_minus(tau, sigma):
    return type_utils.unparse_type(
        type_definitions.supremum(
            type_utils.parse_type(tau), type_utils.parse_type(sigma)
        )
    )


def pattern_match(pattern, tau, gamma_env, sigma_env):
    gamma_env = {k: type_utils.parse_type(v) for k, v in gamma_env.items()}
    sigma_env = {k: type_utils.parse_type(v) for k, v in sigma_env.items()}
    result = pattern_definitions.pattern_match(
        pattern_utils.parse_pattern(pattern),
        type_utils.parse_type(tau),
        gamma_env,
        sigma_env,
    )
    if isinstance(result, pattern_definitions.PatternError):
        print(result)
        return
    return (
        type_utils.unparse_type(result[0]),
        {k: type_utils.unparse_type(v) for k, v in result[1].items()},
    )
