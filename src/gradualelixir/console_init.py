import gradualelixir.utils
from gradualelixir import pattern
from gradualelixir import types as gtypes
from gradualelixir import utils

term = "term"
none = "none"
integer = "integer"
number = "number"
float = "float"
any = "any"


def is_base_subtype(tau, sigma) -> bool:
    return gtypes.is_base_subtype(
        utils.parse_type(tau),
        utils.parse_type(sigma),
    )


def base_supremum(tau, sigma):
    return utils.unparse_type(
        gtypes.base_supremum(
            utils.parse_type(tau),
            utils.parse_type(sigma),
        )
    )


def base_infimum(tau, sigma):
    return utils.unparse_type(
        gtypes.base_infimum(utils.parse_type(tau), utils.parse_type(sigma))
    )


def is_static_type(tau) -> bool:
    return gtypes.is_static_type(utils.parse_type(tau))


def is_subtype(tau, sigma) -> bool:
    return gtypes.is_subtype(utils.parse_type(tau), utils.parse_type(sigma))


def is_materialization(tau, sigma) -> bool:
    return gtypes.is_materialization(utils.parse_type(tau), utils.parse_type(sigma))


def supremum(tau, sigma):
    return utils.unparse_type(
        gtypes.supremum(utils.parse_type(tau), utils.parse_type(sigma))
    )


def infimum(tau, sigma):
    return utils.unparse_type(
        gtypes.infimum(utils.parse_type(tau), utils.parse_type(sigma))
    )


def pattern_match(pat, tau, gamma_env, sigma_env):
    gamma_env = {k: utils.parse_type(v) for k, v in gamma_env.items()}
    sigma_env = {k: utils.parse_type(v) for k, v in sigma_env.items()}
    result = pattern.pattern_match(
        gradualelixir.utils.parse_pattern(pat),
        utils.parse_type(tau),
        gamma_env,
        sigma_env,
    )
    if isinstance(result, pattern.PatternMatchError):
        print(result)
        return
    return (
        utils.unparse_type(result[0]),
        {k: utils.unparse_type(v) for k, v in result[1].items()},
    )
