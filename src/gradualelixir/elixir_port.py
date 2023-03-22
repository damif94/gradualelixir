import enum
import json
import os
import subprocess
from collections import OrderedDict
from typing import Any, Tuple

from dotenv import find_dotenv, get_key
from gradualelixir import expression, gtypes, module, pattern
from gradualelixir.exception import ElixirParseError, ElixirProcessError

dotenv_path = find_dotenv()

project_path = get_key(dotenv_path, "PROJECT_PATH")
elixir_path: str = get_key(dotenv_path, "ELIXIR_PATH") # type: ignore


def format_code(elixir_code: str) -> str:
    with open(file=f"{project_path}/swap.ex", mode="w") as swap:
        swap.write(elixir_code)

    mix_command = [elixir_path, "-S", "mix"]
    formatter_output = subprocess.run(mix_command + ["format", f"{project_path}/swap.ex"], capture_output=True)

    if error := formatter_output.stderr:
        raise Exception(f"Mix formatter failed for code {elixir_code}\n" + error.decode("ascii"))

    with open(file=f"{project_path}/swap.ex", mode="r") as swap:
        text = "".join(swap.readlines())
        text = text[:-1]

    os.remove(f"{project_path}/swap.ex")

    return text


def ast_transform(elixir_code: str, syntactic_level: "SyntacticLevel") -> Tuple[Any, bool]:
    elixir_ast_converter_output = subprocess.run(
        ["mix", "run", f"lib/ast_transformer.exs", elixir_code], capture_output=True, cwd=project_path + "/elixir_port"
    )

    if error := elixir_ast_converter_output.stderr:
        raise ElixirProcessError(f"Elixir ast transformer failed for code {elixir_code}\n" + error.decode("ascii"))

    out = str(elixir_ast_converter_output.stdout)[2:-5]
    try:
        return syntactic_level.parse(json.loads(out)), True
    except ElixirParseError:
        return "", False


def run(elixir_code: str) -> Tuple[str, bool]:
    elixir_runner_output = subprocess.run(
        ["mix", "run", f"lib/runner.exs", elixir_code], capture_output=True, cwd=project_path + "/elixir_port"
    )

    if error := elixir_runner_output.stderr:
        if "function Program.main/0 is undefined or private" in str(error):
            return "", False
        elif "** (" in str(error):
            return str(elixir_runner_output.stderr)[2:-3].replace("\\n", "\n").split("**")[1], True
        elif len(elixir_runner_output.stdout) > 0:
            return str(elixir_runner_output.stdout)[2:-3].replace("\\n", "\n"), True
        else:
            raise ElixirProcessError(f"Elixir runner failed to run module\n" + error.decode("ascii"))
    return str(elixir_runner_output.stdout)[2:-3], True


class SyntacticLevel(enum.Enum):
    key = "key"
    type = "type"
    pattern = "pattern"
    expression = "expression"
    definition = "definition"
    spec = "spec"
    module = "module"

    def parse(self, j) -> Any:
        try:
            if self is SyntacticLevel.key:
                return parse_key(j)
            elif self is SyntacticLevel.type:
                return parse_type(j)
            elif self is SyntacticLevel.pattern:
                return parse_pattern(j)
            elif self is SyntacticLevel.expression:
                return parse_expression(j)
            elif self is SyntacticLevel.definition:
                return parse_definition(j)
            elif self is SyntacticLevel.spec:
                return parse_spec(j)
            elif self is SyntacticLevel.module:
                return parse_module(j)
        except ElixirParseError as exc:
            raise exc
        except Exception as exc:
            raise ElixirParseError(
                f"Error when trying to parse the following elixir ast as a " f"mini elixir {self.value}:\n {j}"
            ) from exc


def parse_key(j) -> gtypes.MapKey:
    if isinstance(j, bool):
        return gtypes.MapKey("true" if j else "false", gtypes.AtomLiteralType("true" if j else "false"))
    if isinstance(j, list) and len(j) == 3 and j[0] == "atom" and len(j[2]) == 1 and isinstance(j[2][0], str):
        return gtypes.MapKey(j[2][0], gtypes.AtomLiteralType(j[2][0]))
    if isinstance(j, str):
        return gtypes.MapKey(j, gtypes.StringType())
    if isinstance(j, int):
        return gtypes.MapKey(j, gtypes.IntegerType())
    else:
        assert isinstance(j, float)
        return gtypes.MapKey(j, gtypes.FloatType())


def parse_type(j) -> gtypes.Type:
    if isinstance(j, bool):
        return gtypes.AtomLiteralType(atom="true" if j else "false")
    if isinstance(j, str):
        return gtypes.StringType(j)
    if isinstance(j, list) and len(j) == 0:
        return gtypes.ElistType()
    if isinstance(j, list) and len(j) == 1:
        node = j[0]
        if isinstance(node, list) and len(node) == 3 and node[0] == "->":
            return SyntacticLevel.type.parse(node)
        type = SyntacticLevel.type.parse(node)
        return gtypes.ListType(type)
    else:
        assert isinstance(j, list) and len(j) == 3
        op, meta, children_nodes = j
        if op == "atom" and isinstance(children_nodes, str):
            return gtypes.AtomLiteralType(children_nodes)
        if op == "{}":
            items = []
            for child_node in children_nodes:
                pat = SyntacticLevel.type.parse(child_node)
                items.append(pat)
            return gtypes.TupleType(items)
        elif op == "%{}":
            items_dict = OrderedDict()
            for child_node in children_nodes:
                _, _, aux = child_node
                key_node, value_node = aux
                key = SyntacticLevel.key.parse(key_node)
                pat = SyntacticLevel.type.parse(value_node)
                items_dict[key] = pat
            return gtypes.MapType(items_dict)
        elif op == "->":
            parameter_types_nodes = children_nodes[0]
            return_type_node = children_nodes[1]
            parameter_types = []
            for node in parameter_types_nodes or []:
                parameter_type = SyntacticLevel.type.parse(node)
                parameter_types.append(parameter_type)
            return_type = SyntacticLevel.type.parse(return_type_node)
            return gtypes.FunctionType(parameter_types, return_type)
        else:
            base_types = [
                gtypes.StringType(),
                gtypes.IntegerType(),
                gtypes.AtomType(),
                gtypes.FloatType(),
                gtypes.BooleanType(),
                gtypes.NumberType(),
                gtypes.AnyType(),
            ]
            for type in base_types:
                if op == str(type):
                    return type
            return gtypes.AtomLiteralType(op)


def parse_pattern(j) -> pattern.Pattern:
    if isinstance(j, bool):
        return pattern.AtomLiteralPattern(value="true" if j else "false")
    if isinstance(j, str):
        return pattern.StringPattern(j)
    if isinstance(j, int):
        return pattern.IntegerPattern(j)
    if isinstance(j, float):
        return pattern.FloatPattern(j)
    if len(j) == 3:
        op, meta, children_nodes = j
        if op == "atom" and len(children_nodes) == 1 and isinstance(children_nodes[0], str):
            return pattern.AtomLiteralPattern(children_nodes[0])
        if op == "{}":
            items = []
            for child_node in children_nodes:
                pat = SyntacticLevel.pattern.parse(child_node)
                items.append(pat)
            return pattern.TuplePattern(items)
        elif op == "%{}":
            items_dict = OrderedDict()
            for child_node in children_nodes:
                _, _, aux = child_node
                key_node, value_node = aux
                key = SyntacticLevel.key.parse(key_node)
                pat = SyntacticLevel.pattern.parse(value_node)
                items_dict[key] = pat
            return pattern.MapPattern(items_dict)
        elif op == "_":
            return pattern.WildPattern()
        elif op == "|":
            left_node, right_node = children_nodes[0]
            left_pattern = SyntacticLevel.pattern.parse(left_node)
            right_pattern = SyntacticLevel.pattern.parse(right_node)
            return pattern.ListPattern(left_pattern, right_pattern)
        elif op.startswith("^"):
            ident_pattern: pattern.IdentPattern = SyntacticLevel.pattern.parse(children_nodes[0])  # type: ignore
            return pattern.PinIdentPattern(ident_pattern.identifier)
        elif children_nodes is None:
            return pattern.IdentPattern(j[0])

    if len(j) == 1 and isinstance(j[0], list) and len(j[0]) > 0 and j[0][0] == "|":
        left_node, right_node = j[0][2]
        left_pattern = SyntacticLevel.pattern.parse(left_node)
        right_pattern = SyntacticLevel.pattern.parse(right_node)
        return pattern.ListPattern(left_pattern, right_pattern)

    tail_pattern: pattern.Pattern = pattern.ElistPattern()
    for node in reversed(j):
        head_pattern = SyntacticLevel.pattern.parse(node)
        tail_pattern = pattern.ListPattern(head_pattern, tail_pattern)
    return tail_pattern


def parse_expression(j) -> expression.Expression:
    if isinstance(j, bool):
        return expression.AtomLiteralExpression(value="true" if j else "false")
    if isinstance(j, str):
        return expression.StringExpression(j)
    elif isinstance(j, int):
        return expression.IntegerExpression(j)
    elif isinstance(j, float):
        return expression.FloatExpression(j)
    else:
        assert isinstance(j, list)
        if len(j) == 3:
            op, meta, children_nodes = j
            if op == "atom" and len(children_nodes) == 1 and isinstance(children_nodes[0], str):
                return expression.AtomLiteralExpression(children_nodes[0])
            if op == "{}":
                items = []
                for child_node in children_nodes:
                    expr = SyntacticLevel.expression.parse(child_node)
                    items.append(expr)
                return expression.TupleExpression(items)
            elif op == "%{}":
                items_dict = OrderedDict()
                for child_node in children_nodes:
                    _, _, aux = child_node
                    key_node, value_node = aux
                    key = SyntacticLevel.key.parse(key_node)
                    expr = SyntacticLevel.expression.parse(value_node)
                    items_dict[key] = expr
                return expression.MapExpression(items_dict)
            elif op == "=":
                left_node, right_node = children_nodes
                pat = SyntacticLevel.pattern.parse(left_node)
                expr = SyntacticLevel.expression.parse(right_node)
                return expression.PatternMatchExpression(pat, expr)
            elif op == "if":
                cond_node, do_node = children_nodes
                cond_expr = SyntacticLevel.expression.parse(cond_node)
                if_expr = SyntacticLevel.expression.parse(do_node["do"])
                else_expr = SyntacticLevel.expression.parse(do_node["else"])
                return expression.IfElseExpression(cond_expr, if_expr, else_expr)
            elif op == "case":
                case_node, clause_nodes = children_nodes
                case_expression = SyntacticLevel.expression.parse(case_node)
                branches = []
                for _, _, node in clause_nodes["do"]:
                    test_pattern = SyntacticLevel.pattern.parse(node[0][0])
                    do_expression = SyntacticLevel.expression.parse(node[1])
                    branches.append((test_pattern, do_expression))
                return expression.CaseExpression(case_expression, branches)
            elif op == "cond":
                clause_nodes = children_nodes
                branches = []
                for _, _, node in clause_nodes[0]["do"]:
                    cond_node = node[0][0]
                    do_node = node[1]
                    cond_expression = SyntacticLevel.expression.parse(cond_node)
                    do_expression = SyntacticLevel.expression.parse(do_node)
                    branches.append((cond_expression, do_expression))  # type: ignore
                return expression.CondExpression(branches)  # type: ignore
            elif op == "&":
                function_name = children_nodes[0][2][0][0]
                arity = children_nodes[0][2][1]
                return expression.AnonymizedFunctionExpression(function_name, arity)
            elif op == "__block__":
                left_expression = SyntacticLevel.expression.parse(children_nodes[0])
                if len(children_nodes) == 1:
                    return left_expression
                else:
                    right_expression = SyntacticLevel.expression.parse([op, meta, children_nodes[1:]])
                    return expression.SeqExpression(left_expression, right_expression)
            elif aux := [
                symbol for symbol in list(expression.UnaryOpEnum) + list(expression.BinaryOpEnum) if symbol.value == op
            ]:
                if len(children_nodes) == 1:
                    symbol = aux[0]
                    assert symbol in expression.UnaryOpEnum
                    arg_expression = SyntacticLevel.expression.parse(children_nodes[0])
                    return expression.UnaryOpExpression(symbol, arg_expression)
                else:
                    symbol = aux[0] if aux[0] in expression.BinaryOpEnum else aux[1]
                    assert symbol in expression.BinaryOpEnum
                    left_expression = SyntacticLevel.expression.parse(children_nodes[0])
                    right_expression = SyntacticLevel.expression.parse(children_nodes[1])
                    return expression.BinaryOpExpression(symbol, left_expression, right_expression)  # type: ignore
            elif isinstance(op, list) and len(op) == 3 and op[0][0] == ".":
                function_name = SyntacticLevel.expression.parse(op[2][0])
                args = []
                for node in children_nodes:
                    arg_expression = SyntacticLevel.expression.parse(node)
                    args.append(arg_expression)
                return expression.AnonCallExpression(function_name, args)
            elif children_nodes is not None and isinstance(meta, dict) and "line" in meta:
                # isinstance(meta, dict) and 'line' in meta -> patch to "escape" three
                # element lists from entering this clause.
                args = []
                for node in children_nodes:
                    arg_expression = SyntacticLevel.expression.parse(node)
                    args.append(arg_expression)
                return expression.FunctionCallExpression(op, args)
            elif children_nodes is None:
                return expression.IdentExpression(j[0])

        if len(j) == 1 and isinstance(j[0], list) and len(j[0]) > 0 and j[0][0] == "|":
            left_node, right_node = j[0][2]
            left_expression = SyntacticLevel.expression.parse(left_node)
            right_expression = SyntacticLevel.expression.parse(right_node)
            return expression.ListExpression(left_expression, right_expression)

        tail_expression: expression.Expression = expression.ElistExpression()
        for node in reversed(j):
            head_expression = SyntacticLevel.expression.parse(node)
            tail_expression = expression.ListExpression(head_expression, tail_expression)
        return tail_expression


def parse_definition(j) -> module.Definition:
    assert isinstance(j, list) and len(j) == 3
    op, meta, children_nodes = j
    assert op in ["def", "defp"]
    assert len(children_nodes) == 2
    assert len(children_nodes[0]) == 3

    function_name = children_nodes[0][0]
    function_parameters = []
    for node in children_nodes[0][2] or []:
        parameter_pattern = SyntacticLevel.pattern.parse(node)
        function_parameters.append(parameter_pattern)

    body_expression = SyntacticLevel.expression.parse(children_nodes[1]["do"])
    return module.Definition(function_name, function_parameters, body_expression)


def parse_spec(j) -> module.Spec:
    assert j[0] == "@"
    assert j[2][0][0] == "spec"
    assert j[2][0][2][0][0] == "::"
    left_node, right_node = j[2][0][2][0][2]
    definition_name = left_node[0]
    parameter_type_nodes = left_node[2]
    return_type_node = right_node

    parameter_types = []
    for node in parameter_type_nodes:
        parameter_type = SyntacticLevel.type.parse(node)
        parameter_types.append(parameter_type)
    return_type = SyntacticLevel.type.parse(return_type_node)
    return module.Spec(name=definition_name, parameter_types=parameter_types, return_type=return_type)


def parse_module(j) -> module.Module:
    op, meta, children = j
    assert op == "defmodule"
    name = children[0][2][0][2]
    body = children[1]["do"]
    if body[0] == "__block__":
        body = body[2]
    else:
        body = [body]
    specs = []
    definitions = []
    for node in body:
        if node[0].startswith("@"):
            spec = SyntacticLevel.spec.parse(node)
            specs.append(spec)
        else:
            definition = SyntacticLevel.definition.parse(node)
            definitions.append(definition)
    return module.Module(name=name, definitions=definitions, specs=specs)
