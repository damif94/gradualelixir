from collections import OrderedDict

from gradualelixir.cast import (
    AnnotatedModule,
    CastAnnotatedExpression,
    CastAnnotatedVarCallExpression,
    annotate_module,
    cast_annotate_expression,
)
from gradualelixir.expression import (
    AnonymizedFunctionExpression,
    AtomLiteralExpression,
    BinaryOpEnum,
    BinaryOpExpression,
    CaseExpression,
    CondExpression,
    ElistExpression,
    ExpressionErrorEnum,
    ExpressionTypeCheckSuccess,
    FloatExpression,
    FunctionCallExpression,
    IdentExpression,
    IfElseExpression,
    IntegerExpression,
    ListExpression,
    MapExpression,
    PatternMatchExpression,
    SeqExpression,
    TupleExpression,
    UnaryOpEnum,
    UnaryOpExpression,
    VarCallExpression,
    format_expression,
    type_check,
)
from gradualelixir.gtypes import (
    AnyType,
    AtomLiteralType,
    BooleanType,
    FloatType,
    FunctionType,
    IntegerType,
    ListType,
    MapKey,
    NumberType,
    SpecsEnv,
    TupleType,
    TypeEnv,
)
from gradualelixir.module import (
    Definition,
    Module,
    Spec,
    TypeCheckSuccess,
    format_module,
)
from gradualelixir.module import type_check as type_check_module
from gradualelixir.pattern import IdentPattern, WildPattern
from gradualelixir.utils import Bcolors, long_line

from . import TEST_ENV

identifier_not_found_in_environment = ExpressionErrorEnum.identifier_not_found_in_environment


def assert_cast_annotate_expression_ok(expr, env=None, expected_casted_expr=None, specs_env=None, comment: str = None):
    if TEST_ENV.get("errors_only"):
        return

    env = TypeEnv(env)
    specs_env = SpecsEnv(specs_env)
    assert expected_casted_expr is not None

    type_derivation = type_check(expr, env, specs_env)
    assert isinstance(type_derivation, ExpressionTypeCheckSuccess)
    ret = cast_annotate_expression(type_derivation)
    assert ret == expected_casted_expr
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        print(f"{Bcolors.OKBLUE}Variables:{Bcolors.ENDC} {env}\n")
        if specs_env is not None:
            print()
            print(f"{Bcolors.OKBLUE}Function Variables:{Bcolors.ENDC} {specs_env}\n")
        print(f"{Bcolors.OKBLUE}Original Expression:{Bcolors.ENDC} {format_expression(type_derivation.expression)}\n")
        print(f"{Bcolors.OKBLUE}Derived Type:{Bcolors.ENDC} {type_derivation.type}\n")
        print(f"{Bcolors.OKBLUE}Result Expression:{Bcolors.ENDC} {format_expression(ret)}\n")
        if comment:
            print(f"{Bcolors.OKBLUE}Comment:{Bcolors.ENDC} {comment}\n")
        print(f"\n{long_line}\n")


def assert_cast_annotate_module_ok(module: Module, expected_casted_module: AnnotatedModule, comment: str = None):
    if TEST_ENV.get("errors_only"):
        return

    type_derivation = type_check_module(module, static=False)
    assert isinstance(type_derivation, TypeCheckSuccess)
    ret = annotate_module(type_derivation, casts=True)
    assert isinstance(ret, AnnotatedModule)
    assert ret == expected_casted_module
    if TEST_ENV.get("display_results") or TEST_ENV.get("display_results_verbose"):
        print("\n")
        print(f"{Bcolors.OKBLUE}Original Module:{Bcolors.ENDC} {format_module(module)}\n")
        print(f"{Bcolors.OKBLUE}Result Module:{Bcolors.ENDC} {format_module(ret)}\n")  # type: ignore
        if comment:
            print(f"{Bcolors.OKBLUE}Comment:{Bcolors.ENDC} {comment}\n")
        print(f"\n{long_line}\n\n")


def test_list():
    assert_cast_annotate_expression_ok(
        ListExpression(IdentExpression("x"), ListExpression(IdentExpression("y"), ElistExpression())),
        {"x": AnyType(), "y": IntegerType()},
        expected_casted_expr=(
            ListExpression(
                IdentExpression("x"),
                CastAnnotatedExpression(
                    ListExpression(IdentExpression(identifier='y'), ElistExpression()),
                    ListType(type=IntegerType()),
                    ListType(type=AnyType())
                )
            )
        ),
        comment=(
            "Both the head and tail get casted; in this case the head get casted to any ~> any which is collapsed;\n"
            "the tail's cast doesn't push deeper; this will happen on runtime"
        )
    )
    assert_cast_annotate_expression_ok(
        ListExpression(IdentExpression("x"), ListExpression(IdentExpression("y"), ElistExpression())),
        {"x": AnyType(), "y": NumberType()},
        expected_casted_expr=(
            ListExpression(
                CastAnnotatedExpression(IdentExpression("x"), AnyType(), NumberType()),
                ListExpression(IdentExpression("y"), ElistExpression())
            )
        ),
        comment=(
            "Both the head and tail get casted; in this case the tail get casted to [number] ~> [number] "
            "which is collapsed"
        )
    )
    assert_cast_annotate_expression_ok(
        ListExpression(IdentExpression("x"), ListExpression(IdentExpression("y"), ElistExpression())),
        {"x": IntegerType(), "y": AnyType()},
        expected_casted_expr=(
            ListExpression(
                CastAnnotatedExpression(IdentExpression("x"), IntegerType(), AnyType()),
                ListExpression(IdentExpression("y"), ElistExpression())
            )
        ),
    )
    assert_cast_annotate_expression_ok(
        ListExpression(IdentExpression("x"), ListExpression(IdentExpression("y"), ElistExpression())),
        {"x": NumberType(), "y": AnyType()},
        expected_casted_expr=(
            ListExpression(
                IdentExpression("x"),
                CastAnnotatedExpression(
                    ListExpression(IdentExpression(identifier='y'), ElistExpression()),
                    ListType(type=AnyType()),
                    ListType(type=NumberType())
                )
            )
        ),
    )
    assert_cast_annotate_expression_ok(
        ListExpression(
            IdentExpression("x"),
            ListExpression(IdentExpression("y"), ListExpression(IdentExpression("z"), ElistExpression()))
        ),
        {"x": AnyType(), "y": IntegerType(), "z": NumberType()},
        expected_casted_expr=(
            ListExpression(
                CastAnnotatedExpression(IdentExpression("x"), AnyType(), NumberType()),
                ListExpression(IdentExpression("y"), ListExpression(IdentExpression("z"), ElistExpression()))
            )
        ),
        comment=(
            "Only the head cast remains; the two others suppress since after the merge operator\n"
            "they get transformed into identities"
        )
    )
    assert_cast_annotate_expression_ok(
        ListExpression(IdentExpression("x"), ListExpression(IdentExpression("y"), ElistExpression())),
        {"x": TupleType([IntegerType(), AnyType()]), "y": TupleType([NumberType(), NumberType()])},
        expected_casted_expr=(
            ListExpression(
                CastAnnotatedExpression(
                    IdentExpression("x"),
                    TupleType([IntegerType(), AnyType()]),
                    TupleType([IntegerType(), NumberType()])
                ),
                ListExpression(IdentExpression("y"), ElistExpression())
            )
        ),
        comment="The merge operator's effect can be noticed explicitly on the head"
    )
    assert_cast_annotate_expression_ok(
        ListExpression(IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": AnyType()},
        expected_casted_expr=(
            ListExpression(
                CastAnnotatedExpression(IdentExpression("x"), IntegerType(), AnyType()),
                CastAnnotatedExpression(IdentExpression("y"), AnyType(), ListType(AnyType()))
            )
        ),
        comment="As y is the list tail, it must be casted to [any]"
    )

    assert_cast_annotate_expression_ok(
        ListExpression(IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": ListType(AnyType())},
        expected_casted_expr=(
            ListExpression(
                CastAnnotatedExpression(IdentExpression("x"), IntegerType(), AnyType()),
                IdentExpression("y")
            )
        )
    )


def test_unary_op():
    assert_cast_annotate_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x")),
        {"x": IntegerType()},
        UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x")),
    )
    assert_cast_annotate_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x")),
        {"x": NumberType()},
        UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x"))
    )
    assert_cast_annotate_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negative, IdentExpression("x")),
        {"x": AnyType()},
        CastAnnotatedExpression(
            expression=UnaryOpExpression(
                UnaryOpEnum.negative, CastAnnotatedExpression(IdentExpression("x"), AnyType(), NumberType())
            ),
            left_type=NumberType(),
            right_type=AnyType()
        ),
        comment=(
            "A cast is added to protect the operator from a type error, by coercing it into the maximal argument type."
            "\nThe result is then casted from the result type for this maximal argument type into any"
        )
    )
    assert_cast_annotate_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AtomLiteralType("true")},
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x"))
    )
    assert_cast_annotate_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": BooleanType()},
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x"))
    )
    assert_cast_annotate_expression_ok(
        UnaryOpExpression(UnaryOpEnum.negation, IdentExpression("x")),
        {"x": AnyType()},
        CastAnnotatedExpression(
            expression=UnaryOpExpression(
                UnaryOpEnum.negation, CastAnnotatedExpression(IdentExpression("x"), AnyType(), BooleanType())
            ),
            left_type=BooleanType(),
            right_type=AnyType()
        )
    )


def test_binary_op():
    assert_cast_annotate_expression_ok(
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": NumberType()},
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y"))
    )
    assert_cast_annotate_expression_ok(
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": AnyType()},
        CastAnnotatedExpression(
            expression=BinaryOpExpression(
                BinaryOpEnum.sum,
                IdentExpression("x"),
                CastAnnotatedExpression(IdentExpression("y"), AnyType(), NumberType())
            ),
            left_type=NumberType(),
            right_type=AnyType()
        ),
        comment=(
            "Casts are added to protect the operator from a type error, by coercing it into the maximal argument types "
            "on each coordinate"
        )
    )
    assert_cast_annotate_expression_ok(
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"x": AnyType(), "y": IntegerType()},
        CastAnnotatedExpression(
            expression=BinaryOpExpression(
                BinaryOpEnum.sum,
                CastAnnotatedExpression(IdentExpression("x"), AnyType(), NumberType()),
                IdentExpression("y")
            ),
            left_type=NumberType(),
            right_type=AnyType()
        ),
    )
    assert_cast_annotate_expression_ok(
        BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y")),
        {"x": AnyType(), "y": AnyType()},
        CastAnnotatedExpression(
            BinaryOpExpression(
                BinaryOpEnum.sum,
                CastAnnotatedExpression(IdentExpression("x"), AnyType(), NumberType()),
                CastAnnotatedExpression(IdentExpression("y"), AnyType(), NumberType())
            ),
            left_type=NumberType(),
            right_type=AnyType()
        )
    )


def test_if_else():
    assert_cast_annotate_expression_ok(
        IfElseExpression(IdentExpression("b"), IdentExpression("x"), IdentExpression("y")),
        {"x": IntegerType(), "y": AnyType(), "b": AnyType()},
        expected_casted_expr=(
            IfElseExpression(
                CastAnnotatedExpression(IdentExpression("b"), AnyType(), BooleanType()),
                CastAnnotatedExpression(IdentExpression("x"), IntegerType(), AnyType()),
                IdentExpression("y")
            )
        ),
        comment=(
            "The derived type gets passed as right cast to both branches;\n"
            "in this case the else cast is the identity any ~> any, which is unnecessary and is therefore collapsed.\n"
            "The condition must be casted to boolean"
        )
    )
    assert_cast_annotate_expression_ok(
        IfElseExpression(IdentExpression("b"), IdentExpression("x"), IdentExpression("y")),
        {"x": TupleType([IntegerType(), AnyType()]), "y": TupleType([FloatType(), AnyType()]), "b": BooleanType()},
        expected_casted_expr=IfElseExpression(IdentExpression("b"), IdentExpression("x"), IdentExpression("y")),
        comment=(
            "Nothing to do; since the merge operator forces the identity cast on both branches"
        )
    )
    assert_cast_annotate_expression_ok(
        IfElseExpression(IdentExpression("b"), IdentExpression("x"), IdentExpression("y")),
        {
            "x": TupleType([IntegerType(), AnyType(), IntegerType()]),
            "y": TupleType([AnyType(), FloatType(), FloatType()]),
            "b": BooleanType()
        },
        expected_casted_expr=(
            IfElseExpression(
                IdentExpression("b"),
                CastAnnotatedExpression(
                    IdentExpression("x"),
                    TupleType([IntegerType(), AnyType(), IntegerType()]),
                    TupleType([AnyType(), AnyType(), IntegerType()])
                ),
                CastAnnotatedExpression(
                    IdentExpression("y"),
                    TupleType([AnyType(), FloatType(), FloatType()]),
                    TupleType([AnyType(), AnyType(), FloatType()])
                )
            )
        )
    )
    assert_cast_annotate_expression_ok(
        IfElseExpression(
            IdentExpression("b"),
            TupleExpression([IntegerExpression(1), IdentExpression("x"), IntegerExpression(1)]),
            TupleExpression([IdentExpression("x"), FloatExpression(1.0), FloatExpression(1.0)])
        ),
        {"x": AnyType(), "b": BooleanType()},
        expected_casted_expr=(
            IfElseExpression(
                IdentExpression("b"),
                CastAnnotatedExpression(
                    TupleExpression([IntegerExpression(1), IdentExpression("x"), IntegerExpression(1)]),
                    TupleType([IntegerType(), AnyType(), IntegerType()]),
                    TupleType([AnyType(), AnyType(), IntegerType()])
                ),
                CastAnnotatedExpression(
                    TupleExpression([IdentExpression("x"), FloatExpression(1.0), FloatExpression(1.0)]),
                    TupleType([AnyType(), FloatType(), FloatType()]),
                    TupleType([AnyType(), AnyType(), FloatType()])
                )
            )
        ),
        comment="The cast doesn't get pushed to the tuple's components; that rewriting happens in runtime"
    )


def test_case():
    assert_cast_annotate_expression_ok(
        CaseExpression(
            test=IdentExpression("test"),
            clauses=[
                (IdentPattern("a"), IdentExpression("x")),
                (IdentPattern("b"), IdentExpression("y")),
                (IdentPattern("^x"), IdentExpression("z")),
                (WildPattern(), IdentExpression("w"))
            ]
        ),
        {"x": FloatType(), "y": NumberType(), "z": AnyType(), "w": IntegerType(), "test": AnyType()},
        expected_casted_expr=(
            CaseExpression(
                test=IdentExpression("test"),
                clauses=[
                    (IdentPattern("a"), IdentExpression("x")),
                    (IdentPattern("b"), IdentExpression("y")),
                    (IdentPattern("^x"), CastAnnotatedExpression(IdentExpression("z"), AnyType(), NumberType())),
                    (WildPattern(), IdentExpression("w"))
                ]
            )
        ),
        comment=(
            "A cast is inserted into every clause expression from the case derived type into \n"
            "the expression derived type"
        )
    )
    assert_cast_annotate_expression_ok(
        CaseExpression(
            test=IdentExpression("test"),
            clauses=[
                (IdentPattern("a"), IdentExpression("x")),
                (IdentPattern("b"), IdentExpression("y")),
            ]
        ),
        {"x": TupleType([NumberType(),  AnyType()]), "y": TupleType([AnyType(), NumberType()]), "test": AnyType()},
        expected_casted_expr=(
            CaseExpression(
                test=IdentExpression("test"),
                clauses=[
                    (
                        IdentPattern("a"),
                        CastAnnotatedExpression(
                            expression=IdentExpression("x"),
                            left_type=TupleType([NumberType(), AnyType()]),
                            right_type=TupleType([NumberType(), NumberType()])
                        )
                    ),
                    (
                        IdentPattern("b"),
                        CastAnnotatedExpression(
                            expression=IdentExpression("y"),
                            left_type=TupleType([AnyType(), NumberType()]),
                            right_type=TupleType([NumberType(), NumberType()])
                        )
                    )
                ]
            )
        ),
        comment=(
            "A cast is inserted into every clause expression from the case derived type into the "
            "expression derived type"
        )
    )


def test_cond():
    assert_cast_annotate_expression_ok(
        CondExpression(
            clauses=[
                (IdentExpression("a"), IdentExpression("x")),
                (IdentExpression("b"), IdentExpression("y")),
            ]
        ),
        {
            "a": AtomLiteralType("true"),
            "b": AnyType(),
            "x": TupleType([NumberType(),  AnyType()]),
            "y": TupleType([AnyType(), NumberType()])
        },
        expected_casted_expr=(
            CondExpression(
                clauses=[
                    (
                        IdentExpression("a"),
                        CastAnnotatedExpression(
                            expression=IdentExpression("x"),
                            left_type=TupleType([NumberType(), AnyType()]),
                            right_type=TupleType([NumberType(), NumberType()])
                        )
                    ),
                    (
                        CastAnnotatedExpression(
                            IdentExpression("b"), AnyType(), BooleanType()
                        ),
                        CastAnnotatedExpression(
                            expression=IdentExpression("y"),
                            left_type=TupleType([AnyType(), NumberType()]),
                            right_type=TupleType([NumberType(), NumberType()])
                        )
                    )
                ]
            )
        ),
        comment=(
            "A cast is inserted from every cond expression into boolean and from every clause expression into \n"
            "the expression derived type"
        )
    )


def test_function_call():
    assert_cast_annotate_expression_ok(
        FunctionCallExpression("foo", [IdentExpression("x"), IdentExpression("y"), IdentExpression("z")]),
        env={"x": IntegerType(), "y": IntegerType(), "z": AnyType()},
        specs_env={("foo", 3): ([IntegerType(), AnyType(), NumberType()], IntegerType())},
        expected_casted_expr=(
            FunctionCallExpression(
                "foo",
                [
                    IdentExpression("x"),
                    CastAnnotatedExpression(IdentExpression("y"), IntegerType(), AnyType()),
                    CastAnnotatedExpression(IdentExpression("z"), AnyType(), NumberType())
                ]
            )
        ),
        comment=(
            "Each argument gets casted from its derived type into the respective parameter type for the function's\n"
            "spec in question"
        )
    )


def test_var_call():
    assert_cast_annotate_expression_ok(
        VarCallExpression("foo", [IdentExpression("x"), IdentExpression("y"), IdentExpression("z")]),
        env={
            "foo": FunctionType([IntegerType(), AnyType(), NumberType()], IntegerType()),
            "x": IntegerType(),
            "y": IntegerType(),
            "z": AnyType()
        },
        expected_casted_expr=(
            VarCallExpression(
                "foo",
                [
                    IdentExpression("x"),
                    CastAnnotatedExpression(IdentExpression("y"), IntegerType(), AnyType()),
                    CastAnnotatedExpression(IdentExpression("z"), AnyType(), NumberType())
                ]
            )
        ),
        comment=(
            "Each argument gets casted from its derived type into the respective parameter type for the function's\n"
            "spec in question"
        )
    )
    assert_cast_annotate_expression_ok(
        VarCallExpression("foo", [IdentExpression("x"), IdentExpression("y"), IdentExpression("z")]),
        env={
            "foo": AnyType(), "x": IntegerType(), "y": IntegerType(), "z": AnyType()
        },
        expected_casted_expr=(
            CastAnnotatedVarCallExpression(
                VarCallExpression(
                    "foo",
                    [
                        CastAnnotatedExpression(IdentExpression("x"), IntegerType(), AnyType()),
                        CastAnnotatedExpression(IdentExpression("y"), IntegerType(), AnyType()),
                        IdentExpression("z")
                    ]
                ),
                ident_left_type=AnyType(),
                ident_right_type=FunctionType([AnyType(), AnyType(), AnyType()], AnyType())
            )
        ),
        comment=(
            "The called variable has type any, so it will be casted to the "
            "Each argument gets casted from its derived type into the respective parameter type for the function's\n"
            "spec in question"
        )
    )


def test_uninteresting_cases():
    subexpression = ListExpression(IdentExpression("x"), ListExpression(IdentExpression("y"), ElistExpression()))
    casted_subexpression = ListExpression(
        IdentExpression("x"),
        CastAnnotatedExpression(
            ListExpression(IdentExpression(identifier='y'), ElistExpression()),
            ListType(type=IntegerType()),
            ListType(type=AnyType())
        )
    )

    assert_cast_annotate_expression_ok(
        TupleExpression([subexpression, subexpression]),
        {"x": AnyType(), "y": IntegerType()},
        expected_casted_expr=(
            TupleExpression([casted_subexpression, casted_subexpression])
        ),
        comment=(
            "The casts push recursively into the tuple's components"
        )
    )
    assert_cast_annotate_expression_ok(
        MapExpression(OrderedDict([(MapKey(1), subexpression)])),
        {"x": AnyType(), "y": IntegerType()},
        expected_casted_expr=(
            MapExpression(OrderedDict([(MapKey(1), casted_subexpression)]))
        ),
        comment=(
            "The casts push recursively into the map's value components"
        )
    )

    assert_cast_annotate_expression_ok(
        PatternMatchExpression(IdentPattern("x"), subexpression),
        {"x": AnyType(), "y": IntegerType()},
        PatternMatchExpression(IdentPattern("x"), casted_subexpression)
    )

    assert_cast_annotate_expression_ok(
        SeqExpression(subexpression, subexpression),
        {"x": AnyType(), "y": IntegerType()},
        SeqExpression(casted_subexpression, casted_subexpression)
    )

    assert_cast_annotate_expression_ok(
        AnonymizedFunctionExpression("foo", 2),
        specs_env={("foo", 2): ([IntegerType(), AnyType()], AnyType())},
        expected_casted_expr=AnonymizedFunctionExpression("foo", 2)
    )
    assert_cast_annotate_expression_ok(
        AnonymizedFunctionExpression("foo", 2),
        specs_env={("foo", 2): ([IntegerType(), AnyType()], IntegerType())},
        expected_casted_expr=AnonymizedFunctionExpression("foo", 2)
    )


def test_cast_annotate_module__untyped_sum():
    module = Module(
        name="Demo",
        specs=[],
        definitions=[
            Definition(
                name="untyped_sum",
                parameters=[IdentPattern("x"), IdentPattern("y")],
                body=BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y"))
            ),
            Definition(
                name="main",
                parameters=[],
                body=SeqExpression(
                    left=PatternMatchExpression(IdentPattern("x"), AnonymizedFunctionExpression("untyped_sum", 2)),
                    right=VarCallExpression("x", [IntegerExpression(1), AtomLiteralExpression("a")])
                )
            )
        ]
    )
    cast_annotated_module = AnnotatedModule(
        name="Demo",
        annotated_definitions=[
            (
                Spec("untyped_sum", [AnyType(), AnyType()], AnyType()),
                Definition(
                    name="untyped_sum",
                    parameters=[IdentPattern("x"), IdentPattern("y")],
                    body=CastAnnotatedExpression(
                        BinaryOpExpression(
                            BinaryOpEnum.sum,
                            CastAnnotatedExpression(IdentExpression("x"), AnyType(), NumberType()),
                            CastAnnotatedExpression(IdentExpression("y"), AnyType(), NumberType())
                        ),
                        NumberType(),
                        AnyType()
                    )
                )
            ),
            (
                Spec("main", [], AnyType()),
                Definition(
                    name="main",
                    parameters=[],
                    body=SeqExpression(
                        left=PatternMatchExpression(IdentPattern("x"), AnonymizedFunctionExpression("untyped_sum", 2)),
                        right=VarCallExpression(
                            "x",
                            [
                                CastAnnotatedExpression(IntegerExpression(1), IntegerType(), AnyType()),
                                CastAnnotatedExpression(AtomLiteralExpression("a"), AtomLiteralType("a"), AnyType()),
                            ]
                        )
                    )
                )
            )
        ]
    )
    assert_cast_annotate_module_ok(module, cast_annotated_module)


def test_cast_annotate_module__untyped_sum_untyped():
    module = Module(
        name="Demo",
        specs=[],
        definitions=[
            Definition(
                name="untyped_sum",
                parameters=[IdentPattern("x"), IdentPattern("y")],
                body=BinaryOpExpression(BinaryOpEnum.sum, IdentExpression("x"), IdentExpression("y"))
            ),
            Definition(
                name="untyped",
                parameters=[IdentPattern("x")],
                body=IdentExpression("x")
            ),
            Definition(
                name="main",
                parameters=[],
                body=SeqExpression(
                    left=SeqExpression(
                        left=PatternMatchExpression(IdentPattern("x"), AnonymizedFunctionExpression("untyped_sum", 2)),
                        right=PatternMatchExpression(IdentPattern("x"), FunctionCallExpression("untyped", [IdentExpression("x")]))
                    ),
                    right=VarCallExpression("x", [IntegerExpression(1)])
                )
            )
        ]
    )
    cast_annotated_module = AnnotatedModule(
        name="Demo",
        annotated_definitions=[
            (
                Spec("untyped_sum", [AnyType(), AnyType()], AnyType()),
                Definition(
                    name="untyped_sum",
                    parameters=[IdentPattern("x"), IdentPattern("y")],
                    body=CastAnnotatedExpression(
                        BinaryOpExpression(
                            BinaryOpEnum.sum,
                            CastAnnotatedExpression(IdentExpression("x"), AnyType(), NumberType()),
                            CastAnnotatedExpression(IdentExpression("y"), AnyType(), NumberType())
                        ),
                        NumberType(),
                        AnyType()
                    )
                )
            ),
            (
                Spec("untyped", [AnyType()], AnyType()),
                Definition(
                    name="untyped",
                    parameters=[IdentPattern("x")],
                    body=IdentExpression("x")
                )
            ),
            (
                Spec("main", [], AnyType()),
                Definition(
                    name="main",
                    parameters=[],
                    body=SeqExpression(
                        left=SeqExpression(
                            left=PatternMatchExpression(IdentPattern("x"), AnonymizedFunctionExpression("untyped_sum", 2)),
                            right=PatternMatchExpression(
                                IdentPattern("x"),
                                FunctionCallExpression(
                                    "untyped",
                                    [
                                        CastAnnotatedExpression(
                                            IdentExpression("x"), FunctionType([AnyType(), AnyType()], AnyType()), AnyType()
                                        )
                                    ]
                                )
                            )
                        ),
                        right=CastAnnotatedVarCallExpression(
                            VarCallExpression(
                                "x",
                                [CastAnnotatedExpression(IntegerExpression(1), IntegerType(), AnyType())]
                            ),
                            ident_left_type=AnyType(),
                            ident_right_type=FunctionType([AnyType()], AnyType())
                        )
                    )
                )
            )
        ]
    )
    assert_cast_annotate_module_ok(module, cast_annotated_module)
