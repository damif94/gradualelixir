from collections import OrderedDict

from gradualelixir import expression, pattern
from gradualelixir import types as gtypes


def parse_key(j) -> gtypes.MapKey:
    if isinstance(j, bool):
        return gtypes.MapKey("true" if j else "false")
    else:
        return gtypes.MapKey(j)


def parse_pattern(j) -> pattern.Pattern:
    if isinstance(j, bool):
        return pattern.AtomLiteralPattern(value="true" if j else "false")
    elif isinstance(j, str):
        return pattern.AtomLiteralPattern(value=j)
    if isinstance(j, int):
        return pattern.IntegerPattern(j)
    if isinstance(j, float):
        return pattern.FloatPattern(j)
    if len(j) == 3:
        op, meta, children_nodes = j
        if op == "{}":
            items = []
            for child_node in children_nodes:
                pat = parse_pattern(child_node)
                items.append(pat)
            return pattern.TuplePattern(items)
        elif op == "%{}":
            items_dict = OrderedDict()
            for child_node in children_nodes:
                _, _, aux = child_node
                key_node, value_node = aux
                key = parse_key(key_node)
                pat = parse_pattern(value_node)
                items_dict[key] = pat
            return pattern.MapPattern(items_dict)
        elif op == "_":
            return pattern.WildPattern()
        elif op == "|":
            left_node, right_node = children_nodes[0]
            left_pattern = parse_pattern(left_node)
            right_pattern = parse_pattern(right_node)
            return pattern.ListPattern(left_pattern, right_pattern)
        elif op.startswith("^"):
            ident_pattern: pattern.IdentPattern = parse_pattern(children_nodes[0])  # type: ignore
            return pattern.PinIdentPattern(ident_pattern.identifier)
        elif children_nodes is None:
            return pattern.IdentPattern(j[0])

    if len(j) == 1 and isinstance(j[0], list) and len(j[0]) > 0 and j[0][0] == "|":
        left_node, right_node = j[0][2]
        left_pattern = parse_pattern(left_node)
        right_pattern = parse_pattern(right_node)
        return pattern.ListPattern(left_pattern, right_pattern)

    tail_pattern: pattern.Pattern = pattern.ElistPattern()
    for node in reversed(j):
        head_pattern = parse_pattern(node)
        tail_pattern = pattern.ListPattern(head_pattern, tail_pattern)
    return tail_pattern


def parse_expression(j) -> expression.Expression:
    if isinstance(j, bool):
        return expression.AtomLiteralExpression(value="true" if j else "false")
    elif isinstance(j, str):
        return expression.AtomLiteralExpression(value=j)
    elif isinstance(j, int):
        return expression.IntegerExpression(j)
    elif isinstance(j, float):
        return expression.FloatExpression(j)
    else:
        assert isinstance(j, list)
        if len(j) == 3:
            op, meta, children_nodes = j
            if op == "{}":
                items = []
                for child_node in children_nodes:
                    expr = parse_expression(child_node)
                    items.append(expr)
                return expression.TupleExpression(items)
            elif op == "%{}":
                items_dict = OrderedDict()
                for child_node in children_nodes:
                    _, _, aux = child_node
                    key_node, value_node = aux
                    key = parse_key(key_node)
                    expr = parse_expression(value_node)
                    items_dict[key] = expr
                return expression.MapExpression(items_dict)
            elif op == "=":
                left_node, right_node = children_nodes
                pat = parse_pattern(left_node)
                expr = parse_expression(right_node)
                return expression.PatternMatchExpression(pat, expr)
            elif op == "if":
                cond_node, do_node = children_nodes
                cond_expr = parse_expression(cond_node)
                if_expr = parse_expression(do_node["do"])
                else_expr = None
                if "else" in do_node:
                    else_expr = parse_expression(do_node["else"])
                return expression.IfElseExpression(cond_expr, if_expr, else_expr)
            elif op == "case":
                case_node, clause_nodes = children_nodes
                case_expression = parse_expression(case_node)
                branches = []
                for _, _, node in clause_nodes["do"]:
                    test_pattern = parse_pattern(node[0][0])
                    do_expression = parse_expression(node[1])
                    branches.append((test_pattern, do_expression))
                return expression.CaseExpression(case_expression, branches)
            elif op == "cond":
                clause_nodes = children_nodes
                branches = []
                for _, _, node in clause_nodes[0]["do"]:
                    cond_node = node[0][0]
                    do_node = node[1]
                    cond_expression = parse_expression(cond_node)
                    do_expression = parse_expression(do_node)
                    branches.append((cond_expression, do_expression))  # type: ignore
                return expression.CondExpression(branches)  # type: ignore
            elif op == "__block__":
                left_expression = parse_expression(children_nodes[0])
                if len(children_nodes) == 1:
                    return left_expression
                else:
                    right_expression = parse_expression([op, meta, children_nodes[1:]])
                    return expression.SeqExpression(left_expression, right_expression)
            elif aux := [
                symbol
                for symbol in list(expression.UnaryOpEnum) + list(expression.BinaryOpEnum)
                if symbol.value == op
            ]:
                if len(children_nodes) == 1:
                    symbol = aux[0]
                    assert symbol in expression.UnaryOpEnum
                    arg_expression = parse_expression(children_nodes[0])
                    return expression.UnaryOpExpression(symbol, arg_expression)
                else:
                    symbol = aux[0] if aux[0] in expression.BinaryOpEnum else aux[1]
                    assert symbol in expression.BinaryOpEnum
                    left_expression = parse_expression(children_nodes[0])
                    right_expression = parse_expression(children_nodes[1])
                    return expression.BinaryOpExpression(symbol, left_expression, right_expression)  # type: ignore
            elif isinstance(op, list) and len(op) == 3 and op[0][0] == ".":
                function_name = op[2][0][0]
                args = []
                for node in children_nodes:
                    arg_expression = parse_expression(node)
                    args.append(arg_expression)
                return expression.VarCallExpression(function_name, args)
            elif children_nodes is not None:
                args = []
                for node in children_nodes:
                    arg_expression = parse_expression(node)
                    args.append(arg_expression)
                return expression.FunctionCallExpression(op, args)
            elif children_nodes is None:
                return expression.IdentExpression(j[0])

        if len(j) == 1 and isinstance(j[0], list) and len(j[0]) > 0 and j[0][0] == "|":
            left_node, right_node = j[0][2]
            left_expression = parse_expression(left_node)
            right_expression = parse_expression(right_node)
            return expression.ListExpression(left_expression, right_expression)

        tail_expression: expression.Expression = expression.ElistExpression()
        for node in reversed(j):
            head_expression = parse_expression(node)
            tail_expression = expression.ListExpression(head_expression, tail_expression)
        return tail_expression
