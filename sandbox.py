from dataclasses import dataclass

from enum import Enum
import typing as t

import utils
import gtypes

term = 'term'
none = 'none'
integer = 'integer'
number = 'number'
float = 'float'
any = 'any'


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
        gtypes.base_infimum(
            utils.parse_type(tau),
            utils.parse_type(sigma)
        )
    )


def is_static_type(tau) -> bool:
    return gtypes.is_static_type(
        utils.parse_type(tau)
    )


def is_subtype(tau, sigma) -> bool:
    return gtypes.is_subtype(
        utils.parse_type(tau),
        utils.parse_type(sigma)
    )


def is_materialization(tau, sigma) -> bool:
    return gtypes.is_materialization(
        utils.parse_type(tau),
        utils.parse_type(sigma)
    )


def is_msubtype_plus(tau, sigma) -> bool:
    return gtypes.is_msubtype_plus(
        utils.parse_type(tau),
        utils.parse_type(sigma),
    )


def is_msubtype_minus(tau, sigma) -> bool:
    return gtypes.is_msubtype_minus(
        utils.parse_type(tau),
        utils.parse_type(sigma),
    )


def supremum(tau, sigma):
    return utils.unparse_type(
        gtypes.supremum(
            utils.parse_type(tau),
            utils.parse_type(sigma)
        )
    )


def infimum(tau, sigma):
    return utils.unparse_type(
        gtypes.infimum(
            utils.parse_type(tau),
            utils.parse_type(sigma)
        )
    )


def msupremum_plus(tau, sigma):
    return utils.unparse_type(
        gtypes.msupremum_plus(
            utils.parse_type(tau),
            utils.parse_type(sigma)
        )
    )


def msupremum_minus(tau, sigma):
    return utils.unparse_type(
        gtypes.msupremum_minus(
            utils.parse_type(tau),
            utils.parse_type(sigma)
        )
    )
