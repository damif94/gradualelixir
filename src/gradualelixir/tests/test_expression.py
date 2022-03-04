from collections import OrderedDict

from gradualelixir.expression import (
    AtomLiteralExpression,
    BaseExpressionTypeCheckError,
    BinaryOpContext,
    BinaryOpEnum,
    BinaryOpExpression,
    CondExpression,
    CondExpressionContext,
    ElistExpression,
    ExpressionErrorEnum,
    ExpressionTypeCheckError,
    FloatExpression,
    IdentExpression,
    IfElseExpression,
    IfElseExpressionContext,
    IntegerExpression,
    ListExpression,
    ListExpressionContext,
    MapExpression,
    MapExpressionContext,
    NestedExpressionTypeCheckError,
    PatternMatchExpression,
    SeqExpression,
    TupleExpression,
    TupleExpressionContext,
    UnaryOpContext,
    UnaryOpEnum,
    UnaryOpExpression,
    type_check,
    ExpressionTypeCheckSuccess, ContextExpressionTypeCheckError,
)
from gradualelixir.pattern import IdentPattern, TuplePattern
from gradualelixir.types import (
    AnyType,
    AtomLiteralType,
    AtomType,
    BooleanType,
    ElistType,
    FloatType,
    IntegerType,
    ListType,
    MapKey,
    MapType,
    NumberType,
    TupleType,
)
from gradualelixir.utils import long_line
from . import TEST_ENV

identifier_not_found_in_environment = ExpressionErrorEnum.identifier_not_found_in_environment


def assert_type_check_expression_ok(expr, env=None, expected_type=None, expected_env=None, specs_env=None):
    env = env or {}
    expected_env = expected_env or env
    specs_env = specs_env or {}
    assert expected_type is not None

    ret = type_check(expr, env, {})
    assert isinstance(ret, ExpressionTypeCheckSuccess)
    assert ret.type == expected_type
    assert ret.env == expected_env
    if TEST_ENV.get("display_results"):
        print(f"\n{long_line}\n{ret.message(expr, env, specs_env)}")


def check_context_path(error_data: ExpressionTypeCheckError, context_path):
    if isinstance(error_data, NestedExpressionTypeCheckError):
        assert isinstance(context_path, list)
        assert len(error_data.bullets) == len(context_path)
        for i in range(len(error_data.bullets)):
            context_instance = context_path[i][0][0](expression=error_data.expression, **context_path[i][0][1])
            assert error_data.bullets[i].context == context_instance
            check_context_path(error_data.bullets[i].error, context_path[i][1])
    else:
        assert isinstance(error_data, BaseExpressionTypeCheckError)
        assert error_data.kind is context_path


def assert_type_check_expression_error(type_check_input, expected_context):
    expr, original_env, specs_env = type_check_input, {}, {}
    if isinstance(type_check_input, tuple) and len(type_check_input) == 2:
        expr, original_env = type_check_input
    if isinstance(type_check_input, tuple) and len(type_check_input) == 3:
        expr, original_env, specs_env = type_check_input

    ret = type_check(expr, original_env, {})
    assert isinstance(ret, ExpressionTypeCheckError)
    check_context_path(ret, expected_context)
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        env_args = (
            {"original_env": original_env, "specs_env": specs_env} if TEST_ENV.get("display_results_verbose") else {}
        )
        print(f"\n{long_line}\n{ret.message(padding='', **env_args)}")


def test_literal():
    assert_type_check_expression_ok(
        # 42
        IntegerExpression(42),
        expected_type=IntegerType(),
    )
    assert_type_check_expression_ok(
        # 42.0
        FloatExpression(42),
        expected_type=FloatType(),
    )
    assert_type_check_expression_ok(
        AtomLiteralExpression("true"),
        expected_type=AtomLiteralType("true"),
    )
    assert_type_check_expression_ok(
        # :a
        AtomLiteralExpression("a"),
        expected_type=AtomLiteralType("a"),
    )


def test_ident():
    assert_type_check_expression_ok(
        # x
        IdentExpression("x"),
        {"x": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        # x
        IdentExpression("x"),
        {"x": TupleType([AtomLiteralType("a")])},
        TupleType([AtomLiteralType("a")]),
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
        expected_type=ElistType(),
    )


def test_list():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        # [1]
        ListExpression(IntegerExpression(1), ElistExpression()),
        expected_type=ListType(IntegerType()),
    )
    assert_type_check_expression_ok(
        # [x]
        ListExpression(IdentExpression("x"), ElistExpression()),
        {"x": FloatType()},
        ListType(FloatType()),
    )
    assert_type_check_expression_ok(
        # [x, 1]
        ListExpression(
            IdentExpression("x"),
            ListExpression(IntegerExpression(1), ElistExpression()),
        ),
        {"x": FloatType()},
        ListType(NumberType()),
    )
    assert_type_check_expression_ok(
        # [1, x]
        ListExpression(
            IntegerExpression(1),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        {"x": FloatType()},
        ListType(NumberType()),
    )
    assert_type_check_expression_ok(
        # [1.0, x]
        ListExpression(
            FloatExpression(1.0),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        {"x": FloatType()},
        ListType(FloatType()),
    )
    assert_type_check_expression_ok(
        # [1, x]
        ListExpression(
            IntegerExpression(1),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        {"z": IntegerType(), "x": AnyType()},
        ListType(AnyType()),
    )
    assert_type_check_expression_ok(
        # [z, x]
        ListExpression(
            IdentExpression("z"),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        {"z": NumberType(), "x": AnyType()},
        ListType(NumberType()),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # [x=1, x=2.0]
        ListExpression(
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            ListExpression(
                PatternMatchExpression(IdentPattern("x"), FloatExpression(2.0)),
                ElistExpression(),
            ),
        ),
        expected_type=ListType(NumberType()),
        expected_env={"x": FloatType()},
    )
    assert_type_check_expression_ok(
        # [[x=1], [x=2.0]]
        ListExpression(
            ListExpression(
                PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                ElistExpression(),
            ),
            ListExpression(
                ListExpression(
                    PatternMatchExpression(IdentPattern("x"), FloatExpression(2.0)),
                    ElistExpression(),
                ),
                ElistExpression(),
            ),
        ),
        expected_type=ListType(ListType(NumberType())),
        expected_env={"x": FloatType()},
    )

    # BASE ERRORS behavior
    assert_type_check_expression_error(
        # [1, true]
        (
            ListExpression(
                IntegerExpression(1),
                ListExpression(AtomLiteralExpression("true"), ElistExpression()),
            ),
            {},
        ),
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
        (
            ListExpression(
                IntegerExpression(1),
                ListExpression(IdentExpression("x"), ElistExpression()),
            ),
            {},
        ),
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
        expected_type=TupleType([]),
    )
    assert_type_check_expression_ok(
        # {1}
        expr=TupleExpression([IntegerExpression(1)]),
        expected_type=TupleType([IntegerType()]),
    )
    assert_type_check_expression_ok(
        # {x}
        TupleExpression([IdentExpression("x")]),
        {"x": FloatType()},
        TupleType([FloatType()]),
    )
    assert_type_check_expression_ok(
        # {x, 1}
        TupleExpression([IdentExpression("x"), IntegerExpression(1)]),
        {"x": FloatType()},
        TupleType([FloatType(), IntegerType()]),
    )
    assert_type_check_expression_ok(
        # {1, x}
        TupleExpression([IntegerExpression(1), IdentExpression("x")]),
        {"x": FloatType()},
        TupleType([IntegerType(), FloatType()]),
    )
    assert_type_check_expression_ok(
        # {1.0, :a, true}
        TupleExpression(
            [
                FloatExpression(1.0),
                AtomLiteralExpression("a"),
                AtomLiteralExpression("true"),
            ]
        ),
        expected_type=TupleType([FloatType(), AtomLiteralType("a"), AtomLiteralType("true")]),
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
        expected_type=TupleType([IntegerType(), FloatType()]),
        expected_env={"x": FloatType()},
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
        expected_type=TupleType([IntegerType(), FloatType(), AtomLiteralType("true")]),
        expected_env={"x": FloatType(), "y": AtomLiteralType("true")},
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
        expected_type=TupleType([TupleType([IntegerType()]), TupleType([FloatType()])]),
        expected_env={"x": FloatType()},
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # {x}
        (TupleExpression([IdentExpression("x")]), {}),
        [
            (
                (TupleExpressionContext, {"n": 0}),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        # {1, x, 4}
        (
            TupleExpression([IntegerExpression(1), IdentExpression("x"), IntegerExpression(4)]),
            {},
        ),
        [
            (
                (TupleExpressionContext, {"n": 1}),
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
                (TupleExpressionContext, {"n": 1}),
                [
                    (
                        (TupleExpressionContext, {"n": 0}),
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
        expected_type=MapType({}),
    )
    assert_type_check_expression_ok(
        # %{:a => 1}
        MapExpression(OrderedDict([(MapKey("a"), IntegerExpression(1))])),
        expected_type=MapType(OrderedDict([(MapKey("a"), IntegerType())])),
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
                    (
                        MapKey("a"),
                        PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                    ),
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
                    (
                        MapKey("a"),
                        PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                    ),
                    (
                        MapKey("b"),
                        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                    ),
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
                    (
                        MapKey("a"),
                        PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                    ),
                    (
                        MapKey("c"),
                        PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("d")),
                    ),
                    (
                        MapKey("b"),
                        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                    ),
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
                            OrderedDict(
                                [
                                    (
                                        MapKey(1),
                                        PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                                    )
                                ]
                            )
                        ),
                    ),
                    (
                        MapKey("c"),
                        MapExpression(
                            OrderedDict(
                                [
                                    (
                                        MapKey("a"),
                                        PatternMatchExpression(
                                            IdentPattern("y"),
                                            AtomLiteralExpression("x"),
                                        ),
                                    )
                                ]
                            )
                        ),
                    ),
                    (
                        MapKey("b"),
                        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                    ),
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
                                OrderedDict(
                                    [
                                        (MapKey("a"), IdentExpression("x")),
                                        (MapKey("b"), IntegerExpression(2)),
                                    ]
                                )
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
            UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x")),
            {"x": t},
            t,
            {"x": t},
        )
        assert_type_check_expression_ok(
            UnaryOpExpression(UnaryOpEnum.absolute_value, IdentExpression("x")),
            {"x": t},
            t,
            {"x": t},
        )
    assert_type_check_expression_ok(
        # not x
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AtomLiteralType("true")},
        AtomLiteralType("false"),
    )
    assert_type_check_expression_ok(
        # not x
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AtomLiteralType("false")},
        AtomLiteralType("true"),
    )
    assert_type_check_expression_ok(
        # not x
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": BooleanType()},
        BooleanType(),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # -(x = 1)
        UnaryOpExpression(
            UnaryOpEnum.negative,
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
        ),
        expected_type=IntegerType(),
        expected_env={"x": IntegerType()},
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
            (
                UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x")),
                {"x": t},
            ),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
        )
        assert_type_check_expression_error(
            # abs(x)
            (
                UnaryOpExpression(UnaryOpEnum.absolute_value, IdentExpression("x")),
                {"x": t},
            ),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
        )
    for t in [
        IntegerType(),
        FloatType(),
        NumberType(),
        AtomType(),
        AtomLiteralType("a"),
    ]:
        assert_type_check_expression_error(
            # not x
            (
                UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
                {"x": t},
            ),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
        )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # not x
        (UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")), {}),
        [((UnaryOpContext, {}), identifier_not_found_in_environment)],
    )


def test_binary_op():
    # RESULT TYPE behavior
    for t in [IntegerType(), FloatType(), NumberType()]:
        assert_type_check_expression_ok(
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
            {"x": t, "y": t},
            t,
        )
    for t in [IntegerType(), NumberType()]:
        assert_type_check_expression_ok(
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
            {"x": FloatType(), "y": t},
            FloatType(),
        )
        assert_type_check_expression_ok(
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
            {"y": FloatType(), "x": t},
            FloatType(),
        )
    assert_type_check_expression_ok(
        # x + y
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": NumberType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        # x + y
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"y": IntegerType(), "x": NumberType()},
        NumberType(),
    )

    for t1 in [IntegerType(), FloatType(), NumberType()]:
        for t2 in [IntegerType(), FloatType(), NumberType()]:
            # x / y
            assert_type_check_expression_ok(
                BinaryOpExpression(BinaryOpEnum.division, IdentExpression("x"), IdentExpression("y")),
                {"x": t1, "y": t2},
                FloatType(),
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
            )
            t4 = AtomLiteralType("true" if b1 or b2 else "false")
            assert_type_check_expression_ok(
                # x or y
                BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
                {"x": t1, "y": t2},
                t4,
            )

    assert_type_check_expression_ok(
        # x or y
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("false")},
        BooleanType(),
    )
    assert_type_check_expression_ok(
        # x or y
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("true")},
        AtomLiteralType("true"),
    )
    assert_type_check_expression_ok(
        # x and y
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("false")},
        AtomLiteralType("false"),
    )
    assert_type_check_expression_ok(
        # x and y
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("true")},
        BooleanType(),
    )
    assert_type_check_expression_ok(
        # x or y
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": BooleanType()},
        BooleanType(),
    )
    assert_type_check_expression_ok(
        # x and y
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": BooleanType()},
        BooleanType(),
    )

    assert_type_check_expression_ok(
        # div(x, y)
        BinaryOpExpression(BinaryOpEnum.integer_division, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        # rem(x, y)
        BinaryOpExpression(BinaryOpEnum.integer_reminder, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
    )

    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": FloatType(), "y": FloatType()},
        FloatType(),
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": NumberType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": FloatType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": FloatType(), "y": IntegerType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": NumberType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        # max(x, y)
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": FloatType()},
        NumberType(),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # (x = 1) + (y = 1.0)
        BinaryOpExpression(
            BinaryOpEnum.sum,
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("y"), FloatExpression(1.0)),
        ),
        expected_type=FloatType(),
        expected_env={"x": IntegerType(), "y": FloatType()},
    )
    assert_type_check_expression_ok(
        # (x = 1) + (x = 1.0)
        BinaryOpExpression(
            BinaryOpEnum.sum,
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
        ),
        expected_type=FloatType(),
        expected_env={"x": FloatType()},
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
                BinaryOpExpression(
                    BinaryOpEnum.integer_division,
                    IdentExpression("x"),
                    IdentExpression("y"),
                ),
                {"x": t, "y": IntegerType()},
            ),
            incompatible_type_for_binary_operator,
        )
    for t in [FloatType(), NumberType()]:
        assert_type_check_expression_error(
            # rem(x, y)
            (
                BinaryOpExpression(
                    BinaryOpEnum.integer_reminder,
                    IdentExpression("x"),
                    IdentExpression("y"),
                ),
                {"x": t, "y": IntegerType()},
            ),
            incompatible_type_for_binary_operator,
        )
        assert_type_check_expression_error(
            # div(x, y)
            (
                BinaryOpExpression(
                    BinaryOpEnum.integer_division,
                    IdentExpression("x"),
                    IdentExpression("y"),
                ),
                {"x": t, "y": IntegerType()},
            ),
            incompatible_type_for_binary_operator,
        )
    for t in [
        IntegerType(),
        FloatType(),
        NumberType(),
        AtomLiteralType("a"),
        AtomType(),
    ]:
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
        (
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IntegerExpression(1)),
            {},
        ),
        [((BinaryOpContext, {"is_left": True}), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        # 1 + x
        (
            BinaryOpExpression(BinaryOpEnum.sum, IntegerExpression(1), IdentExpression("x")),
            {},
        ),
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
                [
                    (
                        (BinaryOpContext, {"is_left": False}),
                        identifier_not_found_in_environment,
                    )
                ],
            ),
        ],
    )


def test_seq():
    # RESULT TYPE behavior
    # assert_type_check_expression_ok(
    #     # x ; y
    #     SeqExpression(IdentExpression("x"), IdentExpression("y")),
    #     {"x": IntegerType(), "y": AtomLiteralType("a")},
    #     AtomLiteralType("a"),
    # )
    # assert_type_check_expression_ok(
    #     # x ; {1,true}
    #     SeqExpression(IdentExpression("x"), TupleExpression([IntegerExpression(1), AtomLiteralExpression("true")])),
    #     {"x": IntegerType(), "y": AtomLiteralType("a")},
    #     TupleType([IntegerType(), AtomLiteralType("true")]),
    # )
    #
    # # VARIABLE EXPORT behavior
    # assert_type_check_expression_ok(
    #     # x ; y
    #     SeqExpression(PatternMatchExpression(IdentPattern("x"), IdentExpression("y")), IntegerExpression(1)),
    #     {"y": AtomLiteralType("a")},
    #     IntegerType(),
    #     {"x": AtomLiteralType("a"), "y": AtomLiteralType("a")},
    # )
    # assert_type_check_expression_ok(
    #     # x ; y
    #     SeqExpression(
    #         PatternMatchExpression(IdentPattern("x"), IdentExpression("y")),
    #         IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), AtomLiteralExpression("c"))
    #     ),
    #     {"y": AtomLiteralType("a")},
    #     AtomType(),
    #     {"x": AtomLiteralType("a"), "y": AtomLiteralType("a")},
    # )
    assert_type_check_expression_ok(
        # x ; y
        SeqExpression(
            PatternMatchExpression(
                TuplePattern([IdentPattern("x"), IdentPattern("y")]),
                TupleExpression([IdentExpression("u"), IdentExpression("u")])
            ),
            PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("true"))
        ),
        {"u": NumberType()},
        AtomLiteralType("true"),
        {"u": NumberType(), "x": NumberType(), "y": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        # x ; y
        SeqExpression(
            PatternMatchExpression(
                IdentPattern("y"), IntegerExpression(1)
            ),
            SeqExpression(
                PatternMatchExpression(
                    IdentPattern("z"), IdentExpression("y")
                ),
                PatternMatchExpression(
                    IdentPattern("y"), FloatExpression(1)
                )
            )
        ),
        expected_type=FloatType(),
        expected_env={"y": FloatType(),"z": IntegerType()}
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
    )
    assert_type_check_expression_ok(
        # if true do
        #   x
        # else
        #   y
        # end
        IfElseExpression(IdentExpression("b"), IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": FloatType(), "b": BooleanType()},
        NumberType(),
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
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # if b = true do
        #   b; 1
        # else
        #   b; 1.0
        # end
        IfElseExpression(
            PatternMatchExpression(IdentPattern("b"), AtomLiteralExpression("true")),
            SeqExpression(IdentExpression("b"), IntegerExpression(1)),
            SeqExpression(IdentExpression("b"), FloatExpression(1.0)),
        ),
        expected_type=NumberType(),
        expected_env={"b": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        # if true do
        #   b = 1
        # else
        #   b = 1.0
        # end
        IfElseExpression(
            AtomLiteralExpression("true"),
            PatternMatchExpression(IdentPattern("b"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("b"), FloatExpression(1.0)),
        ),
        expected_type=NumberType(),
    )
    assert_type_check_expression_ok(
        # if x = true do
        #   y = 1
        # else
        #   z = 1.0
        # end
        IfElseExpression(
            PatternMatchExpression(IdentPattern("x"), AtomLiteralExpression("true")),
            PatternMatchExpression(IdentPattern("y"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("z"), FloatExpression(1.0)),
        ),
        expected_type=NumberType(),
        expected_env={"x": AtomLiteralType("true")},
    )

    # BASE ERRORS behavior
    assert_type_check_expression_error(
        # if 1 do
        #   1
        # else
        #   :a
        # end
        (
            IfElseExpression(IntegerExpression(1), IntegerExpression(1), AtomLiteralExpression("a")),
            {},
        ),
        [
            (
                (IfElseExpressionContext, {"branch": None}),
                ExpressionErrorEnum.type_is_not_boolean,
            )
        ],
    )
    assert_type_check_expression_error(
        # if true do
        #   1
        # else
        #   :a
        # end
        (
            IfElseExpression(
                AtomLiteralExpression("true"),
                IntegerExpression(1),
                AtomLiteralExpression("a"),
            ),
            {},
        ),
        ExpressionErrorEnum.incompatible_types_for_if_else,
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # if x do
        #   1
        # else
        #   :a
        # end
        (
            IfElseExpression(IdentExpression("x"), IntegerExpression(1), AtomLiteralExpression("a")),
            {},
        ),
        [
            (
                (IfElseExpressionContext, {"branch": None}),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        # if true do
        #   x
        # else
        #   :a
        # end
        (
            IfElseExpression(
                AtomLiteralExpression("true"),
                IdentExpression("x"),
                AtomLiteralExpression("a"),
            ),
            {},
        ),
        [
            (
                (IfElseExpressionContext, {"branch": True}),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        # if true do
        #   x
        # else
        #   x
        # end
        (
            IfElseExpression(
                AtomLiteralExpression("true"),
                IntegerExpression(1),
                IdentExpression("x"),
            ),
            {},
        ),
        [
            (
                (IfElseExpressionContext, {"branch": False}),
                identifier_not_found_in_environment,
            )
        ],
    )


def test_cond():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        # cond do
        #   true -> x
        # end
        CondExpression([(AtomLiteralExpression("true"), IdentExpression("x"))]),
        {"x": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        # cond do
        #   true -> x
        #   false -> y
        # end
        CondExpression(
            [
                (AtomLiteralExpression("true"), IdentExpression("x")),
                (AtomLiteralExpression("false"), IdentExpression("y")),
            ]
        ),
        {"x": IntegerType(), "y": FloatType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        # cond do
        #   b -> x
        #   false -> y
        # end
        CondExpression(
            [
                (IdentExpression("b"), IdentExpression("x")),
                (AtomLiteralExpression("false"), IdentExpression("y")),
            ]
        ),
        {"x": IntegerType(), "y": FloatType(), "b": BooleanType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        # cond do
        #   true -> x
        #   false -> y
        # end
        CondExpression(
            [
                (AtomLiteralExpression("true"), IdentExpression("x")),
                (AtomLiteralExpression("false"), IdentExpression("y")),
            ]
        ),
        {"x": IntegerType(), "y": FloatType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        # cond do
        #   true -> x
        #   false -> y
        # end
        CondExpression(
            [
                (AtomLiteralExpression("true"), IdentExpression("x")),
                (AtomLiteralExpression("false"), IdentExpression("y")),
            ]
        ),
        {"x": NumberType(), "y": AnyType()},
        NumberType(),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        # cond do
        #   b = true -> b; x = 1
        #   c = false -> c; y = 1.0
        # end
        CondExpression(
            [
                (
                    PatternMatchExpression(IdentPattern("b"), AtomLiteralExpression("true")),
                    SeqExpression(
                        IdentExpression("b"),
                        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                    ),
                ),
                (
                    PatternMatchExpression(IdentPattern("c"), AtomLiteralExpression("false")),
                    SeqExpression(
                        IdentExpression("c"),
                        PatternMatchExpression(IdentPattern("y"), FloatExpression(1.0)),
                    ),
                ),
            ]
        ),
        {},
        NumberType(),
        {},
    )

    # BASE ERRORS behavior
    assert_type_check_expression_error(
        # cond do
        #   1 -> x
        #   false -> 4
        # end
        (
            CondExpression(
                [
                    (IntegerExpression(1), IdentExpression("x")),
                    (AtomLiteralExpression("false"), IntegerExpression(4)),
                ]
            ),
            {},
        ),
        [
            (
                (CondExpressionContext, {"branch": 0, "cond": True}),
                ExpressionErrorEnum.type_is_not_boolean,
            )
        ],
    )
    assert_type_check_expression_error(
        # cond do
        #   1 -> x
        #   :a -> y
        # end
        (
            CondExpression(
                [
                    (IntegerExpression(1), IdentExpression("x")),
                    (AtomLiteralExpression("a"), IdentExpression("y")),
                ]
            ),
            {},
        ),
        [
            (
                (CondExpressionContext, {"branch": 0, "cond": True}),
                ExpressionErrorEnum.type_is_not_boolean,
            ),
            (
                (CondExpressionContext, {"branch": 1, "cond": True}),
                ExpressionErrorEnum.type_is_not_boolean,
            ),
        ],
    )
    assert_type_check_expression_error(
        # cond do
        #   true -> 1
        #   false -> :a
        # end
        (
            CondExpression(
                [
                    (AtomLiteralExpression("true"), IntegerExpression(1)),
                    (AtomLiteralExpression("false"), AtomLiteralExpression("a")),
                ]
            ),
            {},
        ),
        ExpressionErrorEnum.incompatible_types_for_cond,
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # cond do
        #    x -> 1
        #    :a -> w
        #    true -> w
        # end
        (
            CondExpression(
                [
                    (IdentExpression("x"), IntegerExpression(1)),
                    (AtomLiteralExpression("a"), IdentExpression("w")),
                    (AtomLiteralExpression("true"), IdentExpression("w")),
                ]
            ),
            {},
        ),
        [
            (
                (CondExpressionContext, {"branch": 0, "cond": True}),
                identifier_not_found_in_environment,
            ),
            (
                (CondExpressionContext, {"branch": 1, "cond": True}),
                ExpressionErrorEnum.type_is_not_boolean,
            ),
            (
                (CondExpressionContext, {"branch": 2, "cond": False}),
                identifier_not_found_in_environment,
            ),
        ],
    )

    assert_type_check_expression_error(
        # cond do
        #    false -> not b
        #    :a -> b
        # end
        (
            CondExpression(
                [
                    (
                        AtomLiteralExpression("false"),
                        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("b")),
                    ),
                    (AtomLiteralExpression("a"), IdentExpression("b")),
                ]
            ),
            {"b": BooleanType()},
        ),
        [
            (
                (CondExpressionContext, {"branch": 1, "cond": True}),
                ExpressionErrorEnum.type_is_not_boolean,
            )
        ],
    )

    assert_type_check_expression_error(
        # cond do
        #   c = b ->
        #     cond do
        #       false -> not c
        #       :a -> c
        #    end
        #  true ->
        #    cond do
        #      true -> :a
        #      b -> 1.0
        #     end
        # end
        (
            CondExpression(
                [
                    (
                        PatternMatchExpression(IdentPattern("c"), IdentExpression("b")),
                        CondExpression(
                            [
                                (
                                    AtomLiteralExpression("false"),
                                    UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("b")),
                                ),
                                (AtomLiteralExpression("a"), IdentExpression("b")),
                            ]
                        ),
                    ),
                    (
                        AtomLiteralExpression("true"),
                        CondExpression(
                            [
                                (
                                    AtomLiteralExpression("true"),
                                    AtomLiteralExpression("a"),
                                ),
                                (IdentExpression("b"), IntegerExpression(1)),
                            ]
                        ),
                    ),
                ]
            ),
            {"b": BooleanType()},
        ),
        [
            (
                (CondExpressionContext, {"branch": 0, "cond": False}),
                [
                    (
                        (CondExpressionContext, {"branch": 1, "cond": True}),
                        ExpressionErrorEnum.type_is_not_boolean,
                    )
                ],
            ),
            (
                (CondExpressionContext, {"branch": 1, "cond": False}),
                ExpressionErrorEnum.incompatible_types_for_cond,
            ),
        ],
    )


def test_wip():
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
                (TupleExpressionContext, {"n": 1}),
                [
                    (
                        (TupleExpressionContext, {"n": 0}),
                        identifier_not_found_in_environment,
                    )
                ],
            )
        ],
    )
