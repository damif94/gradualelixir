import json
import subprocess
from collections import OrderedDict

from gradualelixir import PROJECT_PATH, jsonparser, expression
from gradualelixir.expression import (
    ExpressionTypeCheckError,
    NestedExpressionTypeCheckError,
    BaseExpressionTypeCheckError,
    ExpressionErrorEnum,
    ListExpressionContext,
    TupleExpressionContext,
    MapExpressionContext,
    UnaryOpContext,
    BinaryOpContext,
    IfElseExpressionContext,
    BinaryOpExpression,
    IdentExpression,
    BinaryOpEnum,
    PatternMatchExpression,
    FloatExpression,
    IntegerExpression,
    Expression,
    IfElseExpression,
    AtomLiteralExpression,
    UnaryOpExpression,
    TupleExpression,
    MapExpression,
    ElistExpression,
    ListExpression,
)
from gradualelixir.pattern import LiteralPattern, IntegerPattern, IdentPattern
from gradualelixir.types import (
    IntegerType,
    AtomLiteralType,
    FloatType,
    MapType,
    AtomType,
    ElistType,
    ListType,
    NumberType,
    AnyType,
    MapKey,
    TupleType,
    BooleanType,
)

identifier_not_found_in_environment = ExpressionErrorEnum.identifier_not_found_in_environment


def assert_type_check_expression_ok(code, previous_env, type_klass, env):
    if not isinstance(code, Expression):
        if isinstance(code, tuple):
            code = "\n".join(list(code))
        if isinstance(code, list):
            code = "\n".join(code)

        ret = subprocess.run([f"{PROJECT_PATH}/elixir_port/elixir_port", code], capture_output=True)
        expr = jsonparser.parse_expression(json.loads(ret.stdout))
    else:
        expr = code
    ret = expression.type_check(expr, previous_env, {})
    assert isinstance(ret, expression.ExpressionTypeCheckSuccess)
    assert ret.type == type_klass
    assert ret.env == env


def check_context_path(error_data: ExpressionTypeCheckError, context_path):
    if isinstance(error_data, NestedExpressionTypeCheckError):
        assert isinstance(context_path, list)
        assert len(error_data.errors) == len(context_path)
        for i in range(len(error_data.errors)):
            error_instance = context_path[i][0][0](expression=error_data.expression, **context_path[i][0][1])
            assert error_data.errors[i][0] == error_instance
            check_context_path(error_data.errors[i][1], context_path[i][1])
    else:
        assert isinstance(error_data, BaseExpressionTypeCheckError)
        assert error_data.kind is context_path


def assert_type_check_expression_error(type_check_input, context_path):
    code, previous_env = type_check_input
    if not isinstance(code, Expression):
        code, previous_env = type_check_input
        if isinstance(code, tuple):
            code = "\n".join(list(code))
        if isinstance(code, list):
            code = "\n".join(code)

        elixir_ast = subprocess.run([f"{PROJECT_PATH}/elixir_port/elixir_port", code], capture_output=True)
        expr = jsonparser.parse_expression(json.loads(elixir_ast.stdout))
    else:
        expr = code
    ret = expression.type_check(expr, previous_env, {})
    assert isinstance(ret, ExpressionTypeCheckError)
    check_context_path(ret, context_path)


def test_literal():
    assert_type_check_expression_ok(
        # 42
        IntegerExpression(42),
        {},
        IntegerType(),
        {},
    )
    assert_type_check_expression_ok(
        # 42.0
        FloatExpression(42),
        {},
        FloatType(),
        {},
    )
    assert_type_check_expression_ok(AtomLiteralExpression("true"), {}, AtomLiteralType("true"), {})
    assert_type_check_expression_ok(
        # :a
        AtomLiteralExpression("a"),
        {},
        AtomLiteralType("a"),
        {},
    )


def test_ident():
    assert_type_check_expression_ok(
        # x
        IdentExpression("x"),
        {"x": IntegerType()},
        IntegerType(),
        {"x": IntegerType()},
    )
    assert_type_check_expression_ok(
        # x
        IdentExpression("x"),
        {"x": TupleType([AtomLiteralType("a")])},
        TupleType([AtomLiteralType("a")]),
        {"x": TupleType([AtomLiteralType("a")])},
    )
    assert_type_check_expression_error(
        # x
        (IdentExpression("x"), {}),
        ExpressionErrorEnum.identifier_not_found_in_environment,
    )
    assert_type_check_expression_error(
        # x
        (IdentExpression("x"), {"y": AtomType()}),
        ExpressionErrorEnum.identifier_not_found_in_environment,
    )


def test_elist():
    assert_type_check_expression_ok(
        # []
        ElistExpression(),
        {},
        ElistType(),
        {},
    )


def test_list():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        # [1]
        ListExpression(IntegerExpression(1), ElistExpression()),
        {},
        ListType(IntegerType()),
        {},
    )
    assert_type_check_expression_ok(
        # [x]
        ListExpression(IdentExpression("x"), ElistExpression()),
        {"x": FloatType()},
        ListType(FloatType()),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # [x, 1]
        ListExpression(IdentExpression("x"), ListExpression(IntegerExpression(1), ElistExpression())),
        {"x": FloatType()},
        ListType(NumberType()),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # [1, x]
        ListExpression(IntegerExpression(1), ListExpression(IdentExpression("x"), ElistExpression())),
        {"x": FloatType()},
        ListType(NumberType()),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # [1.0, x]
        ListExpression(FloatExpression(1.0), ListExpression(IdentExpression("x"), ElistExpression())),
        {"x": FloatType()},
        ListType(FloatType()),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # [1, x]
        ListExpression(IntegerExpression(1), ListExpression(IdentExpression("x"), ElistExpression())),
        {"z": IntegerType(), "x": AnyType()},
        ListType(AnyType()),
        {"z": IntegerType(), "x": AnyType()},
    )
    assert_type_check_expression_ok(
        # [z, x]
        ListExpression(IdentExpression("z"), ListExpression(IdentExpression("x"), ElistExpression())),
        {"z": NumberType(), "x": AnyType()},
        ListType(NumberType()),
        {"z": NumberType(), "x": AnyType()},
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # [x=1, x=2.0]
        ListExpression(
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            ListExpression(PatternMatchExpression(IdentPattern("x"), FloatExpression(2.0)), ElistExpression()),
        ),
        {},
        ListType(NumberType()),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # [[x=1], [x=2.0]]
        ListExpression(
            ListExpression(PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)), ElistExpression()),
            ListExpression(
                ListExpression(PatternMatchExpression(IdentPattern("x"), FloatExpression(2.0)), ElistExpression()),
                ElistExpression(),
            ),
        ),
        {},
        ListType(ListType(NumberType())),
        {"x": FloatType()},
    )

    # BASE ERRORS behavior
    assert_type_check_expression_error(
        # [1, true]
        (ListExpression(IntegerExpression(1), ListExpression(AtomLiteralExpression("true"), ElistExpression())), {}),
        ExpressionErrorEnum.incompatible_types_for_list,
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # [x]
        (ListExpression(IdentExpression("x"), ElistExpression()), {}),
        [
            (
                (ListExpressionContext, {"head": True}),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        # [1, x]
        (ListExpression(IntegerExpression(1), ListExpression(IdentExpression("x"), ElistExpression())), {}),
        [
            (
                (ListExpressionContext, {"head": False}),
                [
                    (
                        (ListExpressionContext, {"head": True}),
                        identifier_not_found_in_environment,
                    )
                ],
            )
        ],
    )


def test_tuple():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        # {}
        TupleExpression([]),
        {},
        TupleType([]),
        {},
    )
    assert_type_check_expression_ok(
        # {1}
        TupleExpression([IntegerExpression(1)]),
        {},
        TupleType([IntegerType()]),
        {},
    )
    assert_type_check_expression_ok(
        # {x}
        TupleExpression([IdentExpression("x")]),
        {"x": FloatType()},
        TupleType([FloatType()]),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # {x, 1}
        TupleExpression([IdentExpression("x"), IntegerExpression(1)]),
        {"x": FloatType()},
        TupleType([FloatType(), IntegerType()]),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # {1, x}
        TupleExpression([IntegerExpression(1), IdentExpression("x")]),
        {"x": FloatType()},
        TupleType([IntegerType(), FloatType()]),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # {1.0, :a, true}
        TupleExpression([FloatExpression(1.0), AtomLiteralExpression("a"), AtomLiteralExpression("true")]),
        {},
        TupleType([FloatType(), AtomLiteralType("a"), AtomLiteralType("true")]),
        {},
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # {x = 1, x = 2.0}
        TupleExpression(
            [
                PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                PatternMatchExpression(IdentPattern("x"), FloatExpression(2.0)),
            ]
        ),
        {},
        TupleType([IntegerType(), FloatType()]),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # {x = 1, x = 2.0, y = true}
        TupleExpression(
            [
                PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                PatternMatchExpression(IdentPattern("x"), FloatExpression(2.0)),
                PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("true")),
            ]
        ),
        {},
        TupleType([IntegerType(), FloatType(), AtomLiteralType("true")]),
        {"x": FloatType(), "y": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        # {x = 1, x = 2.0}
        TupleExpression(
            [
                TupleExpression([PatternMatchExpression(IdentPattern("x"), IntegerExpression(1))]),
                TupleExpression([PatternMatchExpression(IdentPattern("x"), FloatExpression(2.0))]),
            ]
        ),
        {},
        TupleType([TupleType([IntegerType()]), TupleType([FloatType()])]),
        {"x": FloatType()},
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # {x}
        (TupleExpression([IdentExpression("x")]), {}),
        [
            (
                (TupleExpressionContext, {"n": 1}),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        # {1, x, 4}
        (TupleExpression([IntegerExpression(1), IdentExpression("x"), IntegerExpression(4)]), {}),
        [
            (
                (TupleExpressionContext, {"n": 2}),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        # {1, {x, 2}, 4}
        (
            TupleExpression(
                [
                    IntegerExpression(1),
                    TupleExpression([IdentExpression("x"), IntegerExpression(2)]),
                    IntegerExpression(4),
                ]
            ),
            {},
        ),
        [
            (
                (TupleExpressionContext, {"n": 2}),
                [
                    (
                        (TupleExpressionContext, {"n": 1}),
                        identifier_not_found_in_environment,
                    )
                ],
            )
        ],
    )


def test_map():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        # %{}
        MapExpression(OrderedDict([])),
        {},
        MapType({}),
        {},
    )
    assert_type_check_expression_ok(
        # %{:a => 1}
        MapExpression(OrderedDict([(MapKey("a"), IntegerExpression(1))])),
        {},
        MapType(OrderedDict([(MapKey("a"), IntegerType())])),
        {},
    )
    # TODO[thesis] add comment in the thesis text about how using python's dicts for types gives us
    #  the map's type equivalence for free
    assert_type_check_expression_ok(
        # %{:a => 1, 1 => :a, 1.0 => true, false => 2.1}
        MapExpression(
            OrderedDict(
                [
                    (MapKey("a"), IntegerExpression(1)),
                    (MapKey(1), AtomLiteralExpression("a")),
                    (MapKey(1.0), AtomLiteralExpression("true")),
                    (MapKey("false"), FloatExpression(2.1)),
                ]
            )
        ),
        {},
        MapType(
            {
                MapKey("a"): IntegerType(),
                MapKey(1): AtomLiteralType("a"),
                MapKey(1.0): AtomLiteralType("true"),
                MapKey("false"): FloatType(),
            }
        ),
        {},
    )
    assert_type_check_expression_ok(
        # %{1.0 => true, 1 => :a, :a => 1, false => 2.1}
        MapExpression(
            OrderedDict(
                [
                    (MapKey(1.0), AtomLiteralExpression("true")),
                    (MapKey(1), AtomLiteralExpression("a")),
                    (MapKey("a"), IntegerExpression(1)),
                    (MapKey("false"), FloatExpression(2.1)),
                ]
            )
        ),
        {},
        MapType(
            {
                MapKey("a"): IntegerType(),
                MapKey(1): AtomLiteralType("a"),
                MapKey(1.0): AtomLiteralType("true"),
                MapKey("false"): FloatType(),
            }
        ),
        {},
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # %{:a => x = 1.0, :b => 1}
        MapExpression(
            OrderedDict(
                [
                    (MapKey("a"), PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0))),
                    (MapKey("b"), IntegerExpression(1)),
                ]
            )
        ),
        {},
        MapType({MapKey("a"): FloatType(), MapKey("b"): IntegerType()}),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # %{:a => x = 1.0, :b => x = 1}
        MapExpression(
            OrderedDict(
                [
                    (MapKey("a"), PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0))),
                    (MapKey("b"), PatternMatchExpression(IdentPattern("x"), IntegerExpression(1))),
                ]
            )
        ),
        {},
        MapType({MapKey("a"): FloatType(), MapKey("b"): IntegerType()}),
        {"x": IntegerType()},
    )
    assert_type_check_expression_ok(
        # %{:a => x = 1.0, :c => y = :d, :b => x = 1}
        MapExpression(
            OrderedDict(
                [
                    (MapKey("a"), PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0))),
                    (MapKey("c"), PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("d"))),
                    (MapKey("b"), PatternMatchExpression(IdentPattern("x"), IntegerExpression(1))),
                ]
            )
        ),
        {},
        MapType(
            {
                MapKey("a"): FloatType(),
                MapKey("b"): IntegerType(),
                MapKey("c"): AtomLiteralType("d"),
            }
        ),
        {"x": IntegerType(), "y": AtomLiteralType("d")},
    )
    assert_type_check_expression_ok(
        # %{:a => %{1 => x = 1.0}, :c => %{:a => y = :x}, :b => x = 1}
        MapExpression(
            OrderedDict(
                [
                    (
                        MapKey("a"),
                        MapExpression(
                            OrderedDict([(MapKey(1), PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)))])
                        ),
                    ),
                    (
                        MapKey("c"),
                        MapExpression(
                            OrderedDict(
                                [(MapKey("a"), PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("x")))]
                            )
                        ),
                    ),
                    (MapKey("b"), PatternMatchExpression(IdentPattern("x"), IntegerExpression(1))),
                ]
            )
        ),
        {},
        MapType(
            {
                MapKey("a"): MapType({MapKey(1): FloatType()}),
                MapKey("b"): IntegerType(),
                MapKey("c"): MapType({MapKey("a"): AtomLiteralType("x")}),
            }
        ),
        {"x": IntegerType(), "y": AtomLiteralType("x")},
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        (
            # %{:a => 1, :b => x, :c => 4}
            MapExpression(
                OrderedDict(
                    [
                        (MapKey("a"), IntegerExpression(1)),
                        (MapKey("b"), IdentExpression("x")),
                        (MapKey("c"), IntegerExpression(4)),
                    ]
                )
            ),
            {},
        ),
        [
            (
                (MapExpressionContext, {"key": MapKey("b")}),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        (
            # %{:a => 1, :b => %{:a => x, :b => 2}, :c => 4}
            MapExpression(
                OrderedDict(
                    [
                        (MapKey("a"), IntegerExpression(1)),
                        (
                            MapKey("b"),
                            MapExpression(
                                OrderedDict([(MapKey("a"), IdentExpression("x")), (MapKey("b"), IntegerExpression(2))])
                            ),
                        ),
                        (MapKey("c"), IntegerExpression(4)),
                    ]
                )
            ),
            {},
        ),
        [
            (
                (MapExpressionContext, {"key": MapKey("b")}),
                [
                    (
                        (MapExpressionContext, {"key": MapKey("a")}),
                        identifier_not_found_in_environment,
                    )
                ],
            )
        ],
    )


def test_unary_op():
    # RESULT TYPE behavior
    for t in [IntegerType(), FloatType(), NumberType()]:
        assert_type_check_expression_ok(
            UnaryOpExpression(expression.UnaryOpEnum.negative, IdentExpression("x")), {"x": t}, t, {"x": t}
        )
        assert_type_check_expression_ok(
            UnaryOpExpression(expression.UnaryOpEnum.absolute_value, IdentExpression("x")), {"x": t}, t, {"x": t}
        )
    assert_type_check_expression_ok(
        # not x
        UnaryOpExpression(expression.UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AtomLiteralType("true")},
        AtomLiteralType("false"),
        {"x": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        # not x
        UnaryOpExpression(expression.UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AtomLiteralType("false")},
        AtomLiteralType("true"),
        {"x": AtomLiteralType("false")},
    )
    assert_type_check_expression_ok(
        # not x
        UnaryOpExpression(expression.UnaryOpEnum.negation, IdentExpression("x")),
        {"x": BooleanType()},
        BooleanType(),
        {"x": BooleanType()},
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # -(x = 1)
        UnaryOpExpression(
            expression.UnaryOpEnum.negative, PatternMatchExpression(IdentPattern("x"), IntegerExpression(1))
        ),
        {},
        IntegerType(),
        {"x": IntegerType()},
    )

    # BASE ERRORS behavior
    for t in [
        BooleanType(),
        AtomType(),
        AtomLiteralType("a"),
        TupleType([IntegerType(), IntegerType()]),
    ]:
        assert_type_check_expression_error(
            # -x
            (UnaryOpExpression(expression.UnaryOpEnum.negative, IdentExpression("x")), {"x": t}),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
        )
        assert_type_check_expression_error(
            # abs(x)
            (UnaryOpExpression(expression.UnaryOpEnum.absolute_value, IdentExpression("x")), {"x": t}),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
        )
    for t in [IntegerType(), FloatType(), NumberType(), AtomType(), AtomLiteralType("a")]:
        assert_type_check_expression_error(
            # not x
            (UnaryOpExpression(expression.UnaryOpEnum.negation, IdentExpression("x")), {"x": t}),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
        )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # not x
        (UnaryOpExpression(expression.UnaryOpEnum.negation, IdentExpression("x")), {}),
        [((UnaryOpContext, {}), identifier_not_found_in_environment)],
    )


def test_binary_op():
    # RESULT TYPE behavior
    for t in [IntegerType(), FloatType(), NumberType()]:
        assert_type_check_expression_ok(
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
            {"x": t, "y": t},
            t,
            {"x": t, "y": t},
        )
    for t in [IntegerType(), NumberType()]:
        assert_type_check_expression_ok(
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
            {"x": FloatType(), "y": t},
            FloatType(),
            {"x": FloatType(), "y": t},
        )
        assert_type_check_expression_ok(
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
            {"y": FloatType(), "x": t},
            FloatType(),
            {"y": FloatType(), "x": t},
        )
    assert_type_check_expression_ok(
        # x + y
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": NumberType()},
        NumberType(),
        {"x": IntegerType(), "y": NumberType()},
    )
    assert_type_check_expression_ok(
        # x + y
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"y": IntegerType(), "x": NumberType()},
        NumberType(),
        {"y": IntegerType(), "x": NumberType()},
    )

    for t1 in [IntegerType(), FloatType(), NumberType()]:
        for t2 in [IntegerType(), FloatType(), NumberType()]:
            # x / y
            assert_type_check_expression_ok(
                BinaryOpExpression(BinaryOpEnum.division, IdentExpression("x"), IdentExpression("y")),
                {"x": t1, "y": t2},
                FloatType(),
                {"x": t1, "y": t2},
            )

    for b1 in [True, False]:
        for b2 in [True, False]:
            t1, t2 = AtomLiteralType("true" if b1 else "false"), AtomLiteralType("true" if b2 else "false")
            t3 = AtomLiteralType("true" if b1 and b2 else "false")
            assert_type_check_expression_ok(
                # x and y
                BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
                {"x": t1, "y": t2},
                t3,
                {"x": t1, "y": t2},
            )
            t4 = AtomLiteralType("true" if b1 or b2 else "false")
            assert_type_check_expression_ok(
                # x or y
                BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
                {"x": t1, "y": t2},
                t4,
                {"x": t1, "y": t2},
            )

    assert_type_check_expression_ok(
        # x or y
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("false")},
        BooleanType(),
        {"x": BooleanType(), "y": AtomLiteralType("false")},
    )
    assert_type_check_expression_ok(
        # x or y
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("true")},
        AtomLiteralType("true"),
        {"x": BooleanType(), "y": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        # x and y
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("false")},
        AtomLiteralType("false"),
        {"x": BooleanType(), "y": AtomLiteralType("false")},
    )
    assert_type_check_expression_ok(
        # x and y
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("true")},
        BooleanType(),
        {"x": BooleanType(), "y": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        # x or y
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": BooleanType()},
        BooleanType(),
        {"x": BooleanType(), "y": BooleanType()},
    )
    assert_type_check_expression_ok(
        # x and y
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": BooleanType()},
        BooleanType(),
        {"x": BooleanType(), "y": BooleanType()},
    )

    assert_type_check_expression_ok(
        # div(x, y)
        BinaryOpExpression(BinaryOpEnum.integer_division, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
        {"x": IntegerType(), "y": IntegerType()},
    )
    assert_type_check_expression_ok(
        # rem(x, y)
        BinaryOpExpression(BinaryOpEnum.integer_reminder, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
        {"x": IntegerType(), "y": IntegerType()},
    )

    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
        {"x": IntegerType(), "y": IntegerType()},
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": FloatType(), "y": FloatType()},
        FloatType(),
        {"x": FloatType(), "y": FloatType()},
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": NumberType()},
        NumberType(),
        {"x": NumberType(), "y": NumberType()},
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": FloatType()},
        NumberType(),
        {"x": IntegerType(), "y": FloatType()},
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": FloatType(), "y": IntegerType()},
        NumberType(),
        {"x": FloatType(), "y": IntegerType()},
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": NumberType()},
        NumberType(),
        {"x": IntegerType(), "y": NumberType()},
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": FloatType()},
        NumberType(),
        {"x": NumberType(), "y": FloatType()},
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # (x = 1) + (y = 1.0)
        BinaryOpExpression(
            BinaryOpEnum.sum,
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("y"), FloatExpression(1.0)),
        ),
        {},
        FloatType(),
        {"x": IntegerType(), "y": FloatType()},
    )
    assert_type_check_expression_ok(
        # (x = 1) + (x = 1.0)
        BinaryOpExpression(
            BinaryOpEnum.sum,
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
        ),
        {},
        FloatType(),
        {"x": FloatType()},
    )

    # BASE ERRORS behavior
    incompatible_type_for_binary_operator = ExpressionErrorEnum.incompatible_types_for_binary_operator
    for t in [
        BooleanType(),
        AtomType(),
        AtomLiteralType("a"),
        TupleType([IntegerType(), IntegerType()]),
    ]:
        assert_type_check_expression_error(
            # x + y
            (
                BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
                {"x": t, "y": IntegerType()},
            ),
            incompatible_type_for_binary_operator,
        )
        assert_type_check_expression_error(
            # max(x, y)
            (
                BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
                {"x": IntegerType(), "y": t},
            ),
            incompatible_type_for_binary_operator,
        )
        assert_type_check_expression_error(
            # div(x, y)
            (
                BinaryOpExpression(BinaryOpEnum.integer_division, IdentExpression("x"), IdentExpression("y")),
                {"x": t, "y": IntegerType()},
            ),
            incompatible_type_for_binary_operator,
        )
    for t in [FloatType(), NumberType()]:
        assert_type_check_expression_error(
            # rem(x, y)
            (
                BinaryOpExpression(BinaryOpEnum.integer_reminder, IdentExpression("x"), IdentExpression("y")),
                {"x": t, "y": IntegerType()},
            ),
            incompatible_type_for_binary_operator,
        )
        assert_type_check_expression_error(
            # div(x, y)
            (
                BinaryOpExpression(BinaryOpEnum.integer_division, IdentExpression("x"), IdentExpression("y")),
                {"x": t, "y": IntegerType()},
            ),
            incompatible_type_for_binary_operator,
        )
    for t in [IntegerType(), FloatType(), NumberType(), AtomLiteralType("a"), AtomType()]:
        assert_type_check_expression_error(
            # x and y
            (
                BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
                {"x": t, "y": BooleanType()},
            ),
            incompatible_type_for_binary_operator,
        )
        assert_type_check_expression_error(
            # x or y
            (
                BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
                {"x": t, "y": BooleanType()},
            ),
            incompatible_type_for_binary_operator,
        )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # x + 1
        (BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IntegerExpression(1)), {}),
        [((BinaryOpContext, {"is_left": True}), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        # 1 + x
        (BinaryOpExpression(BinaryOpEnum.sum, IntegerExpression(1), IdentExpression("x")), {}),
        [((BinaryOpContext, {"is_left": False}), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        # x + (1 + y)
        (
            BinaryOpExpression(
                BinaryOpEnum.sum,
                IdentExpression("x"),
                (BinaryOpExpression(BinaryOpEnum.sum, IntegerExpression(1), IdentExpression("y"))),
            ),
            {},
        ),
        [
            ((BinaryOpContext, {"is_left": True}), identifier_not_found_in_environment),
            (
                (BinaryOpContext, {"is_left": False}),
                [((BinaryOpContext, {"is_left": False}), identifier_not_found_in_environment)],
            ),
        ],
    )


def test_if_else():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        # if true do
        #   x
        # end
        IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), None),
        {"x": IntegerType()},
        IntegerType(),
        {"x": IntegerType()},
    )
    assert_type_check_expression_ok(
        # if true do
        #   x
        # else
        #   y
        # end
        IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": FloatType()},
        NumberType(),
        {"x": IntegerType(), "y": FloatType()},
    )
    assert_type_check_expression_ok(
        # if true do
        #   x
        # else
        #   y
        # end
        IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": AnyType()},
        AnyType(),
        {"x": IntegerType(), "y": AnyType()},
    )
    assert_type_check_expression_ok(
        # if true do
        #   x
        # else
        #   y
        # end
        IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": AnyType()},
        NumberType(),
        {"x": NumberType(), "y": AnyType()},
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # if true do
        #   x = 1
        # else
        #   y = 1.0
        # end
        IfElseExpression(
            AtomLiteralExpression("true"),
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("y"), FloatExpression(1.0)),
        ),
        {},
        NumberType(),
        {"x": IntegerType(), "y": FloatType()},
    )
    assert_type_check_expression_ok(
        # if true do
        #   x = 1
        # else
        #   x = 1.0
        # end
        IfElseExpression(
            AtomLiteralExpression("true"),
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
        ),
        {},
        NumberType(),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # if true do
        #   x = 1
        # else
        #   if false do
        #     x = 2.0
        #   else
        #     y = 2
        #   end
        # end
        IfElseExpression(
            AtomLiteralExpression("true"),
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            (
                IfElseExpression(
                    AtomLiteralExpression("false"),
                    PatternMatchExpression(IdentPattern("x"), FloatExpression(2.0)),
                    PatternMatchExpression(IdentPattern("y"), IntegerExpression(2)),
                )
            ),
        ),
        {},
        NumberType(),
        {"x": FloatType(), "y": IntegerType()},
    )

    # BASE ERRORS behavior
    assert_type_check_expression_error(
        # if 1 do
        #   1
        # else
        #   :a
        # end
        (IfElseExpression(IntegerExpression(1), IntegerExpression(1), AtomLiteralExpression("a")), {}),
        [((IfElseExpressionContext, {"branch": None}), ExpressionErrorEnum.type_is_not_boolean)],
    )
    assert_type_check_expression_error(
        # if true do
        #   1
        # else
        #   :a
        # end
        (IfElseExpression(AtomLiteralExpression("true"), IntegerExpression(1), AtomLiteralExpression("a")), {}),
        ExpressionErrorEnum.incompatible_types_for_if_else,
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # if x do
        #   1
        # else
        #   :a
        # end
        (IfElseExpression(IdentExpression("x"), IntegerExpression(1), AtomLiteralExpression("a")), {}),
        [((IfElseExpressionContext, {"branch": None}), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        # if true do
        #   x
        # else
        #   :a
        # end
        (IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), AtomLiteralExpression("a")), {}),
        [((IfElseExpressionContext, {"branch": True}), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        # if true do
        #   x
        # else
        #   x
        # end
        (IfElseExpression(AtomLiteralExpression("true"), IntegerExpression(1), IdentExpression("x")), {}),
        [((IfElseExpressionContext, {"branch": False}), identifier_not_found_in_environment)],
    )
