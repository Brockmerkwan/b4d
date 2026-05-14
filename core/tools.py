#!/usr/bin/env python3
import sys, json, ast, operator

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

def eval_expr(node):
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](eval_expr(node.left), eval_expr(node.right))
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    raise ValueError("unsupported expression")

def tool_math(payload):
    expr = payload.get("expr")
    tree = ast.parse(expr, mode="eval")
    return eval_expr(tree.body)

def main():
    if len(sys.argv) < 3:
        sys.exit(1)
    tool = sys.argv[1]
    payload = json.loads(sys.argv[2])

    if tool == "math":
        print(tool_math(payload))
        return

    raise SystemExit(1)

if __name__ == "__main__":
    main()
