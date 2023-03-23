from collections import OrderedDict

from gradualelixir.expression import (
    AnonCallExpression,
    AnonCallExpressionContext,
    AnonymizedFunctionExpression,
    AtomLiteralExpression,
    BaseExpressionTypeCheckError,
    BinaryOpContext,
    BinaryOpEnum,
    BinaryOpExpression,
    CaseExpression,
    CaseExpressionContext,
    CondExpression,
    CondExpressionContext,
    ElistExpression,
    ExpressionErrorEnum,
    ExpressionTypeCheckError,
    ExpressionTypeCheckSuccess,
    FloatExpression,
    FunctionCallExpression,
    FunctionCallExpressionContext,
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
    PatternMatchExpressionContext,
    SeqExpression,
    SeqExpressionContext,
    StringExpression,
    TupleExpression,
    TupleExpressionContext,
    UnaryOpContext,
    UnaryOpEnum,
    UnaryOpExpression,
    type_check,
)
from gradualelixir.gtypes import (
    AnyType,
    AtomLiteralType,
    AtomType,
    BooleanType,
    ElistType,
    FloatType,
    FunctionType,
    IntegerType,
    ListType,
    MapKey,
    MapType,
    NumberType,
    SpecsEnv,
    StringType,
    TupleType,
    TypeEnv,
)
from gradualelixir.pattern import (
    AtomLiteralPattern,
    IdentPattern,
    IntegerPattern,
    PatternErrorEnum,
    PinIdentPattern,
    TuplePattern,
    WildPattern,
)
from gradualelixir.utils import long_line

from . import TEST_ENV
from .test_pattern import check_context_path as check_pattern_context_path

identifier_not_found_in_environment = ExpressionErrorEnum.identifier_not_found_in_environment


def assert_type_check_expression_ok(expr, env=None, expected_type=None, expected_env=None, specs_env=None):
    if TEST_ENV.get("errors_only"):
        return

    env = TypeEnv(env)
    expected_env = TypeEnv(expected_env)
    specs_env = SpecsEnv(specs_env)
    assert expected_type is not None

    ret = type_check(expr, env, specs_env)
    assert isinstance(ret, ExpressionTypeCheckSuccess)
    assert ret.type == expected_type
    assert ret.exported_env == expected_env
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        print(f"\n{long_line}\n{ret.message()}")


def check_context_path(error_data: ExpressionTypeCheckError, context_path):
    if isinstance(error_data, NestedExpressionTypeCheckError):
        assert isinstance(context_path, list)
        assert len(error_data.bullets) == len(context_path)
        for i in range(len(error_data.bullets)):
            context_instance = context_path[i][0]
            assert error_data.bullets[i].context == context_instance
            check_context_path(error_data.bullets[i].error, context_path[i][1])
    else:
        assert isinstance(error_data, BaseExpressionTypeCheckError)
        try:
            assert error_data.kind is context_path
        except AssertionError as e:
            if error_data.kind is ExpressionErrorEnum.pattern_match:
                check_pattern_context_path(error_data.args["pattern_match_error"], context_path)
            else:
                raise e


def assert_type_check_expression_error(expr, expected_context, env=None, specs_env=None):
    if TEST_ENV.get("success_only"):
        return

    original_env = TypeEnv(env)
    specs_env = SpecsEnv(specs_env)

    ret = type_check(expr, original_env, specs_env)
    assert isinstance(ret, ExpressionTypeCheckError)
    check_context_path(ret, expected_context)
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        env_args = {"env": original_env, "specs_env": specs_env} if TEST_ENV.get("display_results_verbose") else {}
        print(f"\n{long_line}\n{ret.message(padding='', **env_args)}")


def test_type_check_literal():
    assert_type_check_expression_ok(
        IntegerExpression(42),
        expected_type=IntegerType(),
    )
    assert_type_check_expression_ok(
        FloatExpression(42),
        expected_type=FloatType(),
    )
    assert_type_check_expression_ok(
        AtomLiteralExpression("true"),
        expected_type=AtomLiteralType("true"),
    )
    assert_type_check_expression_ok(
        AtomLiteralExpression("a"),
        expected_type=AtomLiteralType("a"),
    )
    assert_type_check_expression_ok(
        StringExpression(":a"),
        expected_type=StringType(),
    )


def test_type_check_var():
    assert_type_check_expression_ok(
        IdentExpression("x"),
        {"x": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        IdentExpression("x"),
        {"x": TupleType([AtomLiteralType("a")])},
        TupleType([AtomLiteralType("a")]),
    )
    assert_type_check_expression_error(
        IdentExpression("x"),
        ExpressionErrorEnum.identifier_not_found_in_environment,
    )
    assert_type_check_expression_error(
        IdentExpression("x"), ExpressionErrorEnum.identifier_not_found_in_environment, {"y": AtomType()}
    )


def test_type_check_elist():
    assert_type_check_expression_ok(
        ElistExpression(),
        expected_type=ElistType(),
    )


def test_type_check_list():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        ListExpression(StringExpression("1"), ElistExpression()),
        expected_type=ListType(StringType()),
    )
    assert_type_check_expression_ok(
        ListExpression(IdentExpression("x"), ElistExpression()),
        {"x": FloatType()},
        ListType(FloatType()),
    )
    assert_type_check_expression_ok(
        ListExpression(
            IdentExpression("x"),
            ListExpression(IntegerExpression(1), ElistExpression()),
        ),
        {"x": FloatType()},
        ListType(NumberType()),
    )
    assert_type_check_expression_ok(
        ListExpression(
            IntegerExpression(1),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        {"x": FloatType()},
        ListType(NumberType()),
    )
    assert_type_check_expression_ok(
        ListExpression(
            FloatExpression(1.0),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        {"x": FloatType()},
        ListType(FloatType()),
    )
    assert_type_check_expression_ok(
        ListExpression(
            IntegerExpression(1),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        {"z": IntegerType(), "x": AnyType()},
        ListType(AnyType()),
    )
    assert_type_check_expression_ok(
        ListExpression(
            IdentExpression("z"),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        {"z": NumberType(), "x": AnyType()},
        ListType(NumberType()),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
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
        ListExpression(
            IntegerExpression(1),
            ListExpression(AtomLiteralExpression("true"), ElistExpression()),
        ),
        ExpressionErrorEnum.incompatible_types_for_list,
    )
    assert_type_check_expression_error(
        ListExpression(IntegerExpression(1), AtomLiteralExpression("true")),
        ExpressionErrorEnum.bad_type_for_list_tail,
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        ListExpression(IdentExpression("x"), ElistExpression()),
        [
            (
                ListExpressionContext(head=True),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        ListExpression(
            IntegerExpression(1),
            ListExpression(IdentExpression("x"), ElistExpression()),
        ),
        [
            (
                ListExpressionContext(head=False),
                [
                    (
                        ListExpressionContext(head=True),
                        identifier_not_found_in_environment,
                    )
                ],
            )
        ],
    )


def test_type_check_tuple():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        TupleExpression([]),
        expected_type=TupleType([]),
    )
    assert_type_check_expression_ok(
        expr=TupleExpression([IntegerExpression(1)]),
        expected_type=TupleType([IntegerType()]),
    )
    assert_type_check_expression_ok(
        TupleExpression([IdentExpression("x")]),
        {"x": FloatType()},
        TupleType([FloatType()]),
    )
    assert_type_check_expression_ok(
        TupleExpression([IdentExpression("x"), IntegerExpression(1)]),
        {"x": FloatType()},
        TupleType([FloatType(), IntegerType()]),
    )
    assert_type_check_expression_ok(
        TupleExpression([IntegerExpression(1), IdentExpression("x")]),
        {"x": FloatType()},
        TupleType([IntegerType(), FloatType()]),
    )
    assert_type_check_expression_ok(
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
        env={"x": IntegerType()},
        expr=TupleExpression(
            [
                PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                IdentExpression("x"),
                PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("true")),
            ]
        ),
        expected_type=TupleType([FloatType(), IntegerType(), AtomLiteralType("true")]),
        expected_env={"x": FloatType(), "y": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        env={"x": IntegerType()},
        expr=TupleExpression(
            [
                IdentExpression("x"),
                PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("true")),
            ]
        ),
        expected_type=TupleType([IntegerType(), FloatType(), AtomLiteralType("true")]),
        expected_env={"x": FloatType(), "y": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
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
        TupleExpression([IdentExpression("x")]),
        [
            (
                TupleExpressionContext(n=0),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        TupleExpression([IntegerExpression(1), IdentExpression("x"), IntegerExpression(4)]),
        [
            (
                TupleExpressionContext(n=1),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        TupleExpression(
            [
                IntegerExpression(1),
                TupleExpression([IdentExpression("x"), IntegerExpression(2)]),
                IntegerExpression(4),
            ]
        ),
        [
            (
                TupleExpressionContext(n=1),
                [
                    (
                        TupleExpressionContext(n=0),
                        identifier_not_found_in_environment,
                    )
                ],
            )
        ],
    )


def test_type_check_map():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        MapExpression(OrderedDict([])),
        expected_type=MapType({}),
    )
    assert_type_check_expression_ok(
        MapExpression(OrderedDict([(MapKey("a", AtomLiteralType("a")), IntegerExpression(1))])),
        expected_type=MapType(OrderedDict([(MapKey("a", AtomLiteralType("a")), IntegerType())])),
    )
    assert_type_check_expression_ok(
        MapExpression(
            OrderedDict(
                [
                    (MapKey("a", AtomLiteralType("a")), IntegerExpression(1)),
                    (MapKey(1, IntegerType()), AtomLiteralExpression("a")),
                    (MapKey(1.0, FloatType()), AtomLiteralExpression("true")),
                    (MapKey("false", AtomLiteralType("false")), FloatExpression(2.1)),
                ]
            )
        ),
        {},
        MapType(
            {
                MapKey("a", AtomLiteralType("a")): IntegerType(),
                MapKey(1, IntegerType()): AtomLiteralType("a"),
                MapKey(1.0, FloatType()): AtomLiteralType("true"),
                MapKey("false", AtomLiteralType("false")): FloatType(),
            }
        ),
        {},
    )
    assert_type_check_expression_ok(
        MapExpression(
            OrderedDict(
                [
                    (MapKey(1.0, FloatType()), AtomLiteralExpression("true")),
                    (MapKey(1, IntegerType()), AtomLiteralExpression("a")),
                    (MapKey("a", AtomLiteralType("a")), IntegerExpression(1)),
                    (MapKey("false", AtomLiteralType("false")), FloatExpression(2.1)),
                    (MapKey("false", StringType()), StringExpression("true")),
                ]
            )
        ),
        {},
        MapType(
            {
                MapKey("a", AtomLiteralType("a")): IntegerType(),
                MapKey(1, IntegerType()): AtomLiteralType("a"),
                MapKey(1.0, FloatType()): AtomLiteralType("true"),
                MapKey("false", AtomLiteralType("false")): FloatType(),
                MapKey("false", StringType()): StringType(),
            }
        ),
        {},
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        MapExpression(
            OrderedDict(
                [
                    (
                        MapKey("a", AtomLiteralType("a")),
                        PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                    ),
                    (MapKey("b", AtomLiteralType("b")), IntegerExpression(1)),
                ]
            )
        ),
        {},
        MapType({MapKey("a", AtomLiteralType("a")): FloatType(), MapKey("b", AtomLiteralType("b")): IntegerType()}),
        {"x": FloatType()},
    )
    assert_type_check_expression_ok(
        MapExpression(
            OrderedDict(
                [
                    (
                        MapKey("a", AtomLiteralType("a")),
                        PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                    ),
                    (
                        MapKey("b", AtomLiteralType("b")),
                        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                    ),
                ]
            )
        ),
        {},
        MapType({MapKey("a", AtomLiteralType("a")): FloatType(), MapKey("b", AtomLiteralType("b")): IntegerType()}),
        {"x": IntegerType()},
    )
    assert_type_check_expression_ok(
        MapExpression(
            OrderedDict(
                [
                    (
                        MapKey("a", AtomLiteralType("a")),
                        PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                    ),
                    (
                        MapKey("c", AtomLiteralType("c")),
                        PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("d")),
                    ),
                    (
                        MapKey("b", AtomLiteralType("b")),
                        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                    ),
                ]
            )
        ),
        {},
        MapType(
            {
                MapKey("a", AtomLiteralType("a")): FloatType(),
                MapKey("b", AtomLiteralType("b")): IntegerType(),
                MapKey("c", AtomLiteralType("c")): AtomLiteralType("d"),
            }
        ),
        {"x": IntegerType(), "y": AtomLiteralType("d")},
    )
    assert_type_check_expression_ok(
        MapExpression(
            OrderedDict(
                [
                    (
                        MapKey("a", AtomLiteralType("a")),
                        MapExpression(
                            OrderedDict(
                                [
                                    (
                                        MapKey(1, IntegerType()),
                                        PatternMatchExpression(IdentPattern("x"), FloatExpression(1.0)),
                                    )
                                ]
                            )
                        ),
                    ),
                    (
                        MapKey("c", AtomLiteralType("c")),
                        MapExpression(
                            OrderedDict(
                                [
                                    (
                                        MapKey("a", AtomLiteralType("a")),
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
                        MapKey("b", AtomLiteralType("b")),
                        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                    ),
                ]
            )
        ),
        {},
        MapType(
            {
                MapKey("a", AtomLiteralType("a")): MapType({MapKey(1, IntegerType()): FloatType()}),
                MapKey("b", AtomLiteralType("b")): IntegerType(),
                MapKey("c", AtomLiteralType("c")): MapType({MapKey("a", AtomLiteralType("a")): AtomLiteralType("x")}),
            }
        ),
        {"x": IntegerType(), "y": AtomLiteralType("x")},
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        MapExpression(
            OrderedDict(
                [
                    (MapKey("a", AtomLiteralType("a")), IntegerExpression(1)),
                    (MapKey("b", AtomLiteralType("b")), IdentExpression("x")),
                    (MapKey("c", AtomLiteralType("c")), IntegerExpression(4)),
                ]
            )
        ),
        [
            (
                MapExpressionContext(key=MapKey("b", AtomLiteralType("b"))),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        MapExpression(
            OrderedDict(
                [
                    (MapKey("a", AtomLiteralType("a")), IntegerExpression(1)),
                    (
                        MapKey("b", AtomLiteralType("b")),
                        MapExpression(
                            OrderedDict(
                                [
                                    (MapKey("a", AtomLiteralType("a")), IdentExpression("x")),
                                    (MapKey("b", AtomLiteralType("b")), IntegerExpression(2)),
                                ]
                            )
                        ),
                    ),
                    (MapKey("c", AtomLiteralType("c")), IntegerExpression(4)),
                ]
            )
        ),
        [
            (
                MapExpressionContext(key=MapKey("b", AtomLiteralType("b"))),
                [
                    (
                        MapExpressionContext(key=MapKey("a", AtomLiteralType("a"))),
                        identifier_not_found_in_environment,
                    )
                ],
            )
        ],
    )


def test_type_check_unary_op():
    # RESULT TYPE behavior
    for t in [IntegerType(), FloatType(), NumberType()]:
        assert_type_check_expression_ok(
            UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x")),
            {"x": t},
            t,
        )
        assert_type_check_expression_ok(
            UnaryOpExpression(UnaryOpEnum.absolute_value, IdentExpression("x")),
            {"x": t},
            t,
        )
    assert_type_check_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AtomLiteralType("true")},
        AtomLiteralType("false"),
    )
    assert_type_check_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AtomLiteralType("false")},
        AtomLiteralType("true"),
    )
    assert_type_check_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": BooleanType()},
        BooleanType(),
    )
    assert_type_check_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AnyType()},
        AnyType(),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
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
            UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x")),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
            {"x": t},
        )
        assert_type_check_expression_error(
            UnaryOpExpression(UnaryOpEnum.absolute_value, IdentExpression("x")),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
            {"x": t},
        )
    for t in [
        IntegerType(),
        FloatType(),
        NumberType(),
        AtomType(),
        AtomLiteralType("a"),
    ]:
        assert_type_check_expression_error(
            UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
            ExpressionErrorEnum.incompatible_type_for_unary_operator,
            {"x": t},
        )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        [(UnaryOpContext(), identifier_not_found_in_environment)],
    )


def test_type_check_binary_op():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.concatenation, IdentExpression("x"), StringExpression("y")),
        {"x": StringType()},
        StringType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.concatenation, IdentExpression("x"), StringExpression("y")),
        {"x": AnyType()},
        StringType(),
    )
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
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": NumberType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"y": IntegerType(), "x": NumberType()},
        NumberType(),
    )

    for t1 in [IntegerType(), FloatType(), NumberType()]:
        for t2 in [IntegerType(), FloatType(), NumberType()]:
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
                BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
                {"x": t1, "y": t2},
                t3,
            )
            t4 = AtomLiteralType("true" if b1 or b2 else "false")
            assert_type_check_expression_ok(
                BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
                {"x": t1, "y": t2},
                t4,
            )

    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("false")},
        BooleanType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("true")},
        AtomLiteralType("true"),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("false")},
        AtomLiteralType("false"),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AtomLiteralType("true")},
        BooleanType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": BooleanType()},
        BooleanType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": AnyType()},
        AnyType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
        {"x": BooleanType(), "y": BooleanType()},
        BooleanType(),
    )

    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.integer_division, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.integer_reminder, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
    )

    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": FloatType(), "y": FloatType()},
        FloatType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": NumberType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": FloatType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
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
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": FloatType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": AnyType()},
        AnyType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": AnyType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": AnyType(), "y": NumberType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
        {"x": AnyType(), "y": AnyType()},
        AnyType(),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        BinaryOpExpression(
            BinaryOpEnum.sum,
            PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("y"), FloatExpression(1.0)),
        ),
        expected_type=FloatType(),
        expected_env={"x": IntegerType(), "y": FloatType()},
    )
    assert_type_check_expression_ok(
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
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
            incompatible_type_for_binary_operator,
            {"x": t, "y": IntegerType()},
        )
        assert_type_check_expression_error(
            BinaryOpExpression(BinaryOpEnum.maximum, IdentExpression("x"), IdentExpression("y")),
            incompatible_type_for_binary_operator,
            {"x": IntegerType(), "y": t},
        )
        assert_type_check_expression_error(
            BinaryOpExpression(
                BinaryOpEnum.integer_division,
                IdentExpression("x"),
                IdentExpression("y"),
            ),
            incompatible_type_for_binary_operator,
            {"x": t, "y": IntegerType()},
        )
    for t in [FloatType(), NumberType()]:
        assert_type_check_expression_error(
            BinaryOpExpression(
                BinaryOpEnum.integer_reminder,
                IdentExpression("x"),
                IdentExpression("y"),
            ),
            incompatible_type_for_binary_operator,
            {"x": t, "y": IntegerType()},
        )
        assert_type_check_expression_error(
            BinaryOpExpression(
                BinaryOpEnum.integer_division,
                IdentExpression("x"),
                IdentExpression("y"),
            ),
            incompatible_type_for_binary_operator,
            {"x": t, "y": IntegerType()},
        )
    for t in [
        IntegerType(),
        FloatType(),
        NumberType(),
        AtomLiteralType("a"),
        AtomType(),
    ]:
        assert_type_check_expression_error(
            BinaryOpExpression(BinaryOpEnum.conjunction, IdentExpression("x"), IdentExpression("y")),
            incompatible_type_for_binary_operator,
            {"x": t, "y": BooleanType()},
        )
        assert_type_check_expression_error(
            BinaryOpExpression(BinaryOpEnum.disjunction, IdentExpression("x"), IdentExpression("y")),
            incompatible_type_for_binary_operator,
            {"x": t, "y": BooleanType()},
        )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        # x + 1
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IntegerExpression(1)),
        [(BinaryOpContext(is_left=True), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        BinaryOpExpression(BinaryOpEnum.sum, IntegerExpression(1), IdentExpression("x")),
        [(BinaryOpContext(is_left=False), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        BinaryOpExpression(
            BinaryOpEnum.sum,
            IdentExpression("x"),
            (BinaryOpExpression(BinaryOpEnum.sum, IntegerExpression(1), IdentExpression("y"))),
        ),
        [
            (BinaryOpContext(is_left=True), identifier_not_found_in_environment),
            (
                BinaryOpContext(is_left=False),
                [
                    (
                        BinaryOpContext(is_left=False),
                        identifier_not_found_in_environment,
                    )
                ],
            ),
        ],
    )


def test_type_check_pattern_match():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
        expected_type=IntegerType(),
        expected_env={"x": IntegerType()},
    )
    assert_type_check_expression_ok(
        PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
        {"x": AtomType()},
        expected_type=IntegerType(),
        expected_env={"x": IntegerType()},
    )
    assert_type_check_expression_ok(
        PatternMatchExpression(PinIdentPattern("x"), PatternMatchExpression(IdentPattern("x"), IntegerExpression(1))),
        {"x": NumberType()},
        expected_type=IntegerType(),
        expected_env={"x": IntegerType()},
    )
    assert_type_check_expression_ok(
        PatternMatchExpression(
            TuplePattern([IdentPattern("x"), IdentPattern("x")]),
            TupleExpression(
                [
                    MapExpression(OrderedDict([(MapKey(1, IntegerType()), TupleExpression([])), (MapKey(2, IntegerType()), IntegerExpression(1))])),
                    IdentExpression("y"),
                ]
            ),
        ),
        {"y": MapType({MapKey(2, IntegerType()): NumberType()})},
        expected_type=TupleType(
            [
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): IntegerType()}),
                MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): IntegerType()}),
            ]
        ),
        expected_env={
            "x": MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): IntegerType()}),
        },
    )

    # BASE ERRORS behavior
    assert_type_check_expression_error(
        PatternMatchExpression(IntegerPattern(1), IdentExpression("x")),
        ExpressionErrorEnum.pattern_match,
        {"x": BooleanType()},
    )

    assert_type_check_expression_error(
        PatternMatchExpression(
            TuplePattern([IdentPattern("x"), IdentPattern("x")]),
            TupleExpression(
                [
                    MapExpression(OrderedDict([(MapKey(1, IntegerType()), TupleExpression([])), (MapKey(2, IntegerType()), IntegerExpression(1))])),
                    IdentExpression("y"),
                ]
            ),
        ),
        ExpressionErrorEnum.pattern_match,
        {"y": MapType({MapKey(2, IntegerType()): AtomType()})},
    )
    assert_type_check_expression_error(
        PatternMatchExpression(PinIdentPattern("x"), PatternMatchExpression(IdentPattern("x"), IntegerExpression(1))),
        ExpressionErrorEnum.pattern_match,
        {"x": FloatType()},
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        PatternMatchExpression(IdentPattern("x"), IdentExpression("y")),
        [(PatternMatchExpressionContext(), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        PatternMatchExpression(IdentPattern("x"), IdentExpression("x")),
        [(PatternMatchExpressionContext(), identifier_not_found_in_environment)],
    )
    assert_type_check_expression_error(
        PatternMatchExpression(TuplePattern([]), TupleExpression([IdentExpression("x")])),
        [(PatternMatchExpressionContext(), [(TupleExpressionContext(n=0), identifier_not_found_in_environment)])],
    )


def test_type_check_if_else():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), IdentExpression("x")),
        {"x": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        IfElseExpression(IdentExpression("b"), IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": FloatType(), "b": BooleanType()},
        NumberType(),
    )
    assert_type_check_expression_ok(
        IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": AnyType()},
        AnyType(),
    )
    assert_type_check_expression_ok(
        IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), IdentExpression("y")),
        {"x": NumberType(), "y": AnyType()},
        NumberType(),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        IfElseExpression(
            PatternMatchExpression(IdentPattern("b"), AtomLiteralExpression("true")),
            SeqExpression(IdentExpression("b"), IntegerExpression(1)),
            SeqExpression(IdentExpression("b"), FloatExpression(1.0)),
        ),
        expected_type=NumberType(),
        expected_env={"b": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        IfElseExpression(
            AtomLiteralExpression("true"),
            PatternMatchExpression(IdentPattern("b"), IntegerExpression(1)),
            PatternMatchExpression(IdentPattern("b"), FloatExpression(1.0)),
        ),
        expected_type=NumberType(),
    )
    assert_type_check_expression_ok(
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
        IfElseExpression(IntegerExpression(1), IntegerExpression(1), AtomLiteralExpression("a")),
        [
            (
                IfElseExpressionContext(branch=None),
                ExpressionErrorEnum.inferred_type_is_not_as_expected,
            )
        ],
    )
    assert_type_check_expression_error(
        IfElseExpression(
            AtomLiteralExpression("true"),
            IntegerExpression(1),
            AtomLiteralExpression("a"),
        ),
        ExpressionErrorEnum.incompatible_types_for_if_else,
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        IfElseExpression(IdentExpression("x"), IntegerExpression(1), AtomLiteralExpression("a")),
        [
            (
                IfElseExpressionContext(branch=None),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        IfElseExpression(
            AtomLiteralExpression("true"),
            IdentExpression("x"),
            AtomLiteralExpression("a"),
        ),
        [
            (
                IfElseExpressionContext(branch=True),
                identifier_not_found_in_environment,
            )
        ],
    )
    assert_type_check_expression_error(
        IfElseExpression(
            AtomLiteralExpression("true"),
            IntegerExpression(1),
            IdentExpression("x"),
        ),
        [
            (
                IfElseExpressionContext(branch=False),
                identifier_not_found_in_environment,
            )
        ],
    )


def test_type_check_seq():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        SeqExpression(IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": AtomLiteralType("a")},
        AtomLiteralType("a"),
    )
    assert_type_check_expression_ok(
        SeqExpression(IdentExpression("x"), TupleExpression([IntegerExpression(1), AtomLiteralExpression("true")])),
        {"x": IntegerType(), "y": AtomLiteralType("a")},
        TupleType([IntegerType(), AtomLiteralType("true")]),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        SeqExpression(PatternMatchExpression(IdentPattern("x"), IdentExpression("y")), IntegerExpression(1)),
        {"y": AtomLiteralType("a")},
        IntegerType(),
        {"x": AtomLiteralType("a")},
    )
    assert_type_check_expression_ok(
        SeqExpression(
            PatternMatchExpression(IdentPattern("x"), IdentExpression("y")),
            IfElseExpression(AtomLiteralExpression("true"), IdentExpression("x"), AtomLiteralExpression("c")),
        ),
        {"y": AtomLiteralType("a")},
        AtomType(),
        {"x": AtomLiteralType("a")},
    )
    assert_type_check_expression_ok(
        SeqExpression(
            PatternMatchExpression(
                TuplePattern([IdentPattern("x"), IdentPattern("y")]),
                TupleExpression([IdentExpression("u"), IdentExpression("u")]),
            ),
            PatternMatchExpression(IdentPattern("y"), AtomLiteralExpression("true")),
        ),
        {"u": NumberType()},
        AtomLiteralType("true"),
        {"x": NumberType(), "y": AtomLiteralType("true")},
    )
    assert_type_check_expression_ok(
        SeqExpression(
            PatternMatchExpression(IdentPattern("y"), IntegerExpression(1)),
            SeqExpression(
                PatternMatchExpression(IdentPattern("z"), IdentExpression("y")),
                PatternMatchExpression(IdentPattern("y"), FloatExpression(1)),
            ),
        ),
        expected_type=FloatType(),
        expected_env={"y": FloatType(), "z": IntegerType()},
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        SeqExpression(IdentExpression("x"), IdentExpression("x")),
        [(SeqExpressionContext(is_left=True), identifier_not_found_in_environment)],
    )

    assert_type_check_expression_error(
        SeqExpression(IdentExpression("x"), IdentExpression("y")),
        [(SeqExpressionContext(is_left=True), identifier_not_found_in_environment)],
    )

    assert_type_check_expression_error(
        SeqExpression(IdentExpression("x"), IdentExpression("y")),
        [(SeqExpressionContext(is_left=False), identifier_not_found_in_environment)],
        {"x": IntegerType()},
    )


def test_type_check_cond():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        CondExpression([(AtomLiteralExpression("true"), IdentExpression("x"))]),
        {"x": IntegerType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
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
        CondExpression(
            [
                (IntegerExpression(1), IdentExpression("x")),
                (AtomLiteralExpression("false"), IntegerExpression(4)),
            ]
        ),
        [
            (
                CondExpressionContext(branch=0, cond=True),
                ExpressionErrorEnum.inferred_type_is_not_as_expected,
            )
        ],
    )
    assert_type_check_expression_error(
        CondExpression(
            [
                (IntegerExpression(1), IdentExpression("x")),
                (AtomLiteralExpression("a"), IdentExpression("y")),
            ]
        ),
        [
            (
                CondExpressionContext(branch=0, cond=True),
                ExpressionErrorEnum.inferred_type_is_not_as_expected,
            ),
            (
                CondExpressionContext(branch=1, cond=True),
                ExpressionErrorEnum.inferred_type_is_not_as_expected,
            ),
        ],
    )
    assert_type_check_expression_error(
        CondExpression(
            [
                (AtomLiteralExpression("true"), IntegerExpression(1)),
                (AtomLiteralExpression("false"), AtomLiteralExpression("a")),
            ]
        ),
        ExpressionErrorEnum.incompatible_types_for_branches,
    )

    # NESTED ERRORS behavior
    assert_type_check_expression_error(
        CondExpression(
            [
                (IdentExpression("x"), IntegerExpression(1)),
                (AtomLiteralExpression("a"), IdentExpression("w")),
                (AtomLiteralExpression("true"), IdentExpression("w")),
            ]
        ),
        [
            (
                CondExpressionContext(branch=0, cond=True),
                identifier_not_found_in_environment,
            ),
            (
                CondExpressionContext(branch=1, cond=True),
                ExpressionErrorEnum.inferred_type_is_not_as_expected,
            ),
            (
                CondExpressionContext(branch=2, cond=False),
                identifier_not_found_in_environment,
            ),
        ],
    )

    assert_type_check_expression_error(
        CondExpression(
            [
                (
                    AtomLiteralExpression("false"),
                    UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("b")),
                ),
                (AtomLiteralExpression("a"), IdentExpression("b")),
            ]
        ),
        [
            (
                CondExpressionContext(branch=1, cond=True),
                ExpressionErrorEnum.inferred_type_is_not_as_expected,
            )
        ],
        {"b": BooleanType()},
    )

    assert_type_check_expression_error(
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
        [
            (
                CondExpressionContext(branch=0, cond=False),
                [
                    (
                        CondExpressionContext(branch=1, cond=True),
                        ExpressionErrorEnum.inferred_type_is_not_as_expected,
                    )
                ],
            ),
            (
                CondExpressionContext(branch=1, cond=False),
                ExpressionErrorEnum.incompatible_types_for_branches,
            ),
        ],
        {"b": BooleanType()},
    )


def test_type_check_case():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        CaseExpression(IdentExpression("x"), [(AtomLiteralPattern("true"), IntegerExpression(1))]),
        {"x": BooleanType()},
        IntegerType(),
    )
    assert_type_check_expression_ok(
        CaseExpression(IdentExpression("x"), [(AtomLiteralPattern("true"), IdentExpression("x"))]),
        {"x": BooleanType()},
        BooleanType(),
    )
    assert_type_check_expression_ok(
        CaseExpression(
            TupleExpression([IdentExpression("x"), IdentExpression("y")]),
            [
                (
                    TuplePattern([IdentPattern("z"), IdentPattern("z")]),
                    TupleExpression([IdentExpression("z"), IntegerExpression(1)]),
                )
            ],
        ),
        {"x": MapType({MapKey(1, IntegerType()): TupleType([])}), "y": MapType({MapKey(2, IntegerType()): TupleType([])})},
        TupleType([MapType({MapKey(1, IntegerType()): TupleType([]), MapKey(2, IntegerType()): TupleType([])}), IntegerType()]),
    )
    assert_type_check_expression_ok(
        CaseExpression(
            IdentExpression("c"),
            [(AtomLiteralPattern("true"), IdentExpression("x")), (AtomLiteralPattern("a"), IdentExpression("y"))],
        ),
        {"c": AtomType(), "x": IntegerType(), "y": FloatType()},
        NumberType(),
    )

    # VARIABLE EXPORT behavior
    assert_type_check_expression_ok(
        CaseExpression(
            PatternMatchExpression(IdentPattern("n"), IntegerExpression(1)),
            [
                (
                    IntegerPattern(1),
                    PatternMatchExpression(IdentPattern("x"), IntegerExpression(1)),
                ),
                (
                    WildPattern(),
                    SeqExpression(
                        PatternMatchExpression(IdentPattern("n"), FloatExpression(1.0)),
                        IdentExpression("n"),
                    ),
                ),
            ],
        ),
        {},
        NumberType(),
        {"n": IntegerType()},
    )

    # ERRORS behavior
    assert_type_check_expression_error(
        CaseExpression(
            IdentExpression("x"), [(WildPattern(), IntegerExpression(1)), (WildPattern(), AtomLiteralExpression("a"))]
        ),
        ExpressionErrorEnum.incompatible_types_for_branches,
        {"x": BooleanType()},
    )
    assert_type_check_expression_error(
        CaseExpression(IdentExpression("x"), [(PinIdentPattern("y"), IntegerExpression(1))]),
        [(CaseExpressionContext(pattern=True, branch=0), PatternErrorEnum.incompatible_type_for_pinned_variable)],
        {"x": BooleanType(), "y": IntegerType()},
    )
    assert_type_check_expression_error(
        CaseExpression(
            IdentExpression("x"),
            [
                (PinIdentPattern("y"), IdentExpression("w")),
                (AtomLiteralPattern("true"), IdentExpression("w")),
                (WildPattern(), IdentExpression("x")),
            ],
        ),
        [
            (CaseExpressionContext(pattern=True, branch=0), PatternErrorEnum.incompatible_type_for_pinned_variable),
            (CaseExpressionContext(pattern=False, branch=1), identifier_not_found_in_environment),
        ],
        {"x": BooleanType(), "y": IntegerType()},
    )
    assert_type_check_expression_error(
        CaseExpression(
            IdentExpression("x"),
            [
                (PinIdentPattern("y"), IdentExpression("w")),
                (AtomLiteralPattern("true"), IdentExpression("w")),
            ],
        ),
        [
            (
                CaseExpressionContext(pattern=True, branch=0),
                PatternErrorEnum.pinned_identifier_not_found_in_environment,
            ),
            (CaseExpressionContext(pattern=False, branch=1), identifier_not_found_in_environment),
        ],
        {"x": BooleanType()},
    )
    assert_type_check_expression_error(
        CaseExpression(
            IdentExpression("x"),
            [(IdentExpression("y"), IntegerExpression(1)), (WildPattern(), AtomLiteralExpression("a"))],
        ),
        [(CaseExpressionContext(pattern=None, branch=None), identifier_not_found_in_environment)],
    )


def test_type_check_call():
    # RESULT TYPE behavior
    assert_type_check_expression_ok(
        FunctionCallExpression("foo", []), specs_env={("foo", 0): ([], IntegerType())}, expected_type=IntegerType()
    )
    assert_type_check_expression_ok(
        FunctionCallExpression("foo", [IntegerExpression(1)]),
        specs_env={("foo", 1): ([IntegerType()], FloatType())},
        expected_type=FloatType(),
    )
    assert_type_check_expression_ok(
        FunctionCallExpression("foo", [TupleExpression([FloatExpression(1), IdentExpression("x")])]),
        env={"x": AnyType()},
        specs_env={("foo", 1): ([TupleType([AnyType(), IntegerType()])], FloatType())},
        expected_type=FloatType(),
    )
    assert_type_check_expression_ok(
        FunctionCallExpression("baz", [FunctionCallExpression("foo", [IntegerExpression(1)]), IdentExpression("x")]),
        env={"x": AtomLiteralType("a")},
        specs_env={("foo", 1): ([IntegerType()], FloatType()), ("baz", 2): ([FloatType(), AtomType()], NumberType())},
        expected_type=NumberType(),
    )
    assert_type_check_expression_ok(
        AnonCallExpression(IdentExpression("z"), [FunctionCallExpression("foo", [IntegerExpression(1)]), IdentExpression("x")]),
        env={"x": AtomLiteralType("a"), "z": FunctionType([FloatType(), AtomType()], NumberType())},
        specs_env={("foo", 1): ([IntegerType()], FloatType())},
        expected_type=NumberType(),
    )
    assert_type_check_expression_ok(
        AnonCallExpression(FunctionCallExpression("foo", []), [IntegerExpression(1)]),
        specs_env={("foo", 0): ([], FunctionType([IntegerType()], FloatType()))},
        expected_type=FloatType(),
    )
    assert_type_check_expression_ok(
        AnonCallExpression(IdentExpression("x"), [IntegerExpression(1)]), env={"x": AnyType()}, expected_type=AnyType()
    )

    # ERRORS behavior
    assert_type_check_expression_error(
        AnonCallExpression(IdentExpression("x"), [IntegerExpression(1)]),
        ExpressionErrorEnum.identifier_type_is_not_arrow_of_expected_arity,
        env={"x": FunctionType([], IntegerType())},
    )
    assert_type_check_expression_error(
        FunctionCallExpression("foo", [IntegerExpression(1)]),
        ExpressionErrorEnum.function_not_declared,
        specs_env={("foo", 0): ([], IntegerType())},
    )
    assert_type_check_expression_error(
        FunctionCallExpression("foo", [IntegerExpression(1)]),
        [(FunctionCallExpressionContext(argument=0), ExpressionErrorEnum.inferred_type_is_not_as_expected)],
        specs_env={("foo", 1): ([FloatType()], IntegerType())},
    )
    assert_type_check_expression_error(
        FunctionCallExpression("foo", [AtomLiteralExpression("true"), IntegerExpression(1)]),
        [(FunctionCallExpressionContext(argument=1), ExpressionErrorEnum.inferred_type_is_not_as_expected)],
        specs_env={("foo", 2): ([AtomType(), FloatType()], IntegerType())},
    )
    assert_type_check_expression_error(
        FunctionCallExpression("foo", [TupleExpression([FloatExpression(1), IntegerExpression(1)])]),
        [(FunctionCallExpressionContext(argument=0), ExpressionErrorEnum.inferred_type_is_not_as_expected)],
        specs_env={("foo", 1): ([TupleType([IntegerType(), AnyType()])], FloatType())},
    )
    assert_type_check_expression_error(
        FunctionCallExpression("foo", [IdentExpression("x"), IntegerExpression(1)]),
        [
            (FunctionCallExpressionContext(argument=0), ExpressionErrorEnum.identifier_not_found_in_environment),
            (FunctionCallExpressionContext(argument=1), ExpressionErrorEnum.inferred_type_is_not_as_expected),
        ],
        specs_env={("foo", 2): ([AtomType(), FloatType()], IntegerType())},
    )
    assert_type_check_expression_error(
        AnonCallExpression(IdentExpression("x"), [IntegerExpression(1)]),
        ExpressionErrorEnum.identifier_type_is_not_arrow_of_expected_arity,
        env={"x": FunctionType([], IntegerType())},
    )
    assert_type_check_expression_error(
        AnonCallExpression(
            BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IntegerExpression(2)), [IntegerExpression(1)]
        ),
        [(AnonCallExpressionContext(None), ExpressionErrorEnum.incompatible_types_for_binary_operator)],
        env={"x": FunctionType([], IntegerType())},
    )


def test_type_check_anon():
    assert_type_check_expression_ok(
        AnonymizedFunctionExpression("foo", 0),
        specs_env={("foo", 0): ([], AnyType())},
        expected_type=FunctionType([], AnyType()),
    )
    assert_type_check_expression_ok(
        AnonymizedFunctionExpression("foo", 2),
        specs_env={("foo", 0): ([], AnyType()), ("foo", 2): ([AtomType(), FloatType()], AnyType())},
        expected_type=FunctionType([AtomType(), FloatType()], AnyType()),
    )
    assert_type_check_expression_error(
        AnonymizedFunctionExpression("foo", 1),
        specs_env={("foo", 0): ([], AnyType()), ("foo", 2): ([AtomType(), FloatType()], AnyType())},
        expected_context=ExpressionErrorEnum.function_not_declared,
    )
