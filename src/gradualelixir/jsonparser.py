from collections import OrderedDict

from gradualelixir import expression, pattern


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
                key, value_node = aux
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

    tail_pat = pattern.ElistPattern()
    for node in reversed(j):
        head_pat = parse_pattern(node)
        tail_pat = pattern.ListPattern(head_pat, tail_pat)
    return tail_pat


def parse_expression(j) -> expression.Expression:
    if isinstance(j, bool):
        return expression.AtomLiteralExpression(value="true" if j else "false")
    elif isinstance(j, str):
        return expression.AtomLiteralExpression(value=j)
    elif isinstance(j, int):
        return expression.IntegerExpression(j)
    elif isinstance(j, float):
        return expression.FloatExpression(j)
    elif isinstance(j, list):
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
                    key, value_node = aux
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
                return expression.IfExpression(cond_expr, if_expr, else_expr)
            elif op == "case":
                pattern_node, clause_nodes = children_nodes
                pat = parse_pattern(pattern_node)
                items = []
                for test_node, do_node in clause_nodes:
                    test_pat = parse_pattern(test_node)
                    do_expr = parse_expression(do_node)
                    items += (test_pat, do_expr)
                return expression.CaseExpression(pat, items)
            elif op == "cond":
                clause_nodes = children_nodes
                items = []
                for cond_node, do_node in clause_nodes:
                    cond_expr = parse_expression(cond_node)
                    do_expr = parse_expression(do_node)
                    items += (cond_expr, do_expr)
                return expression.CondExpression(items)
            elif op == "__block__":
                left_expression = parse_expression(children_nodes[0])
                if len(children_nodes) == 1:
                    return left_expression
                else:
                    right_expression = parse_expression([op, meta, children_nodes[1:]])
                    return expression.SeqExpression(left_expression, right_expression)
            elif children_nodes is None:
                return expression.IdentExpression(j[0])

        if len(j) == 1 and isinstance(j[0], list) and len(j[0]) > 0 and j[0][0] == "|":
            left_node, right_node = j[0][2]
            left_expression = parse_expression(left_node)
            right_expression = parse_expression(right_node)
            return expression.ListExpression(left_expression, right_expression)

        tail_expr = expression.ElistExpression()
        for node in reversed(j):
            head_expr = parse_expression(node)
            tail_expr = expression.ListExpression(head_expr, tail_expr)
        return tail_expr
