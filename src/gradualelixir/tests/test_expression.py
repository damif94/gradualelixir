import json
import subprocess

from gradualelixir import PROJECT_PATH, jsonparser, expression
from gradualelixir.expression import (
    ExpressionTypeCheckError,
    NestedExpressionTypeCheckError,
    BaseExpressionTypeCheckError,
    ExpressionErrorEnum, ListExpressionContext, TupleExpressionContext
)
from gradualelixir.types import IntegerType, AtomLiteralType, FloatType, TupleType, AtomType, ElistType, ListType, \
    NumberType, AnyType


def assert_type_check_expression_ok(code, previous_env, type_klass, env):
    if isinstance(code, tuple):
        code = "\n".join(list(code))
    if isinstance(code, list):
        code = "\n".join(code)

    ret = subprocess.run(
        [f"{PROJECT_PATH}/elixir_port/elixir_port", code], capture_output=True
    )
    expr = jsonparser.parse_expression(json.loads(ret.stdout))
    ret = expression.type_check(expr, previous_env, {})
    assert isinstance(ret, expression.ExpressionTypeCheckSuccess)
    assert ret.type == type_klass
    assert ret.env == env


def check_context_path(error_data: ExpressionTypeCheckError, context_path):
    if isinstance(error_data, NestedExpressionTypeCheckError):
        assert isinstance(context_path, list)
        assert len(error_data.errors) == len(context_path)
        for i in range(len(error_data.errors)):
            error_instance = context_path[i][0][0](
                expression=error_data.expression, **context_path[i][0][1]
            )
            assert error_data.errors[i][0] == error_instance
            check_context_path(error_data.errors[i][1], context_path[i][1])
    else:
        assert isinstance(error_data, BaseExpressionTypeCheckError)
        assert error_data.kind is context_path


def assert_type_check_expression_error(type_check_input, context_path):
    code, previous_env = type_check_input
    if isinstance(code, tuple):
        code = "\n".join(list(code))
    if isinstance(code, list):
        code = "\n".join(code)

    elixir_ast = subprocess.run(
        [f"{PROJECT_PATH}/elixir_port/elixir_port", code], capture_output=True
    )
    expr = jsonparser.parse_expression(json.loads(elixir_ast.stdout))
    ret = expression.type_check(expr, previous_env, {})
    assert isinstance(ret, ExpressionTypeCheckError)
    check_context_path(ret, context_path)


def test_literal():
    assert_type_check_expression_ok("42", {}, IntegerType(), {})
    assert_type_check_expression_ok("42.0", {}, FloatType(), {})
    assert_type_check_expression_ok("true", {}, AtomLiteralType("true"), {})
    assert_type_check_expression_ok(":a", {}, AtomLiteralType("a"), {})


def test_ident():
    assert_type_check_expression_ok(
        "x", {"x": IntegerType()}, IntegerType(), {"x": IntegerType()}
    )
    assert_type_check_expression_ok(
        "x", 
        {"x": TupleType([AtomLiteralType("a")])}, 
        TupleType([AtomLiteralType("a")]), 
        {"x": TupleType([AtomLiteralType("a")])}
    )
    assert_type_check_expression_error(
        ("x", {}), ExpressionErrorEnum.identifier_not_found_in_environment
    )
    assert_type_check_expression_error(
        ("x", {"y": AtomType()}), ExpressionErrorEnum.identifier_not_found_in_environment
    )


def test_elist():
    assert_type_check_expression_ok("[]", {}, ElistType(), {})


def test_list():
    # RESULT TYPE behavior
    assert_type_check_expression_ok("[1]", {}, ListType(IntegerType()), {})
    assert_type_check_expression_ok("[x]", {"x": FloatType()}, ListType(FloatType()), {"x": FloatType()})
    assert_type_check_expression_ok("[x, 1]", {"x": FloatType()}, ListType(NumberType()), {"x": FloatType()})
    assert_type_check_expression_ok("[1, x]", {"x": FloatType()}, ListType(NumberType()), {"x": FloatType()})
    assert_type_check_expression_ok("[1.0, x]", {"x": FloatType()}, ListType(FloatType()), {"x": FloatType()})
    assert_type_check_expression_ok(
        "[1, x]", {"z": IntegerType(), "x": AnyType()}, ListType(AnyType()), {"z": IntegerType(), "x": AnyType()}
    )
    assert_type_check_expression_ok(
        "[z, x]", {"z": NumberType(), "x": AnyType()}, ListType(NumberType()), {"z": NumberType(), "x": AnyType()}
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok("[x=1, x=2.0]", {}, ListType(NumberType()), {"x": FloatType()})
    assert_type_check_expression_ok("[[x=1], [x=2.0]]", {}, ListType(ListType(NumberType())), {"x": FloatType()})

    # BASE ERRORS behavior
    assert_type_check_expression_error(("[1, true]", {}), ExpressionErrorEnum.incompatible_types_for_list)

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        ("[x]", {}),
        [((ListExpressionContext, {"head": True}), ExpressionErrorEnum.identifier_not_found_in_environment)]
    )
    assert_type_check_expression_error(
        ("[1, x]", {}),
        [(
            (ListExpressionContext, {"head": False}), [
                ((ListExpressionContext, {"head": True}), ExpressionErrorEnum.identifier_not_found_in_environment)
            ]
        )]
    )


def test_tuple():
    # RESULT TYPE behavior
    assert_type_check_expression_ok("{}", {}, TupleType([]), {})
    assert_type_check_expression_ok("{1}", {}, TupleType([IntegerType()]), {})
    assert_type_check_expression_ok("{x}", {"x": FloatType()}, TupleType([FloatType()]), {"x": FloatType()})
    assert_type_check_expression_ok(
        "{x, 1}", {"x": FloatType()}, TupleType([FloatType(), IntegerType()]), {"x": FloatType()}
    )
    assert_type_check_expression_ok(
        "{1, x}", {"x": FloatType()}, TupleType([IntegerType(), FloatType()]), {"x": FloatType()}
    )
    assert_type_check_expression_ok(
        "{1.0, :a, true}", {}, TupleType([FloatType(), AtomLiteralType("a"), AtomLiteralType("true")]), {}
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok("{x=1, x=2.0}", {}, TupleType([IntegerType(), FloatType()]), {"x": FloatType()})
    assert_type_check_expression_ok(
        "{x=1, x=2.0, y=true}",
        {},
        TupleType([IntegerType(), FloatType(), AtomLiteralType("true")]),
        {"x": FloatType(), "y": AtomLiteralType("true")}
    )
    assert_type_check_expression_ok(
        "{{x=1}, {x=2.0}}",
        {},
        TupleType([TupleType([IntegerType()]), TupleType([FloatType()])]),
        {"x": FloatType()})

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        ("{x}", {}),
        [((TupleExpressionContext, {"n": 1}), ExpressionErrorEnum.identifier_not_found_in_environment)]
    )
    assert_type_check_expression_error(
        ("{1, x, 4}", {}),
        [((TupleExpressionContext, {"n": 2}), ExpressionErrorEnum.identifier_not_found_in_environment)]
    )
    assert_type_check_expression_error(
        ("{1, {x, 2}, 4}", {}),
        [(
            (TupleExpressionContext, {"n": 2}), [
                ((TupleExpressionContext, {"n": 1}), ExpressionErrorEnum.identifier_not_found_in_environment)
            ]
        )]
    )

