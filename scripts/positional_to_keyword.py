#!/usr/bin/env python3
"""Convert positional call arguments to keyword arguments across the codebase.

Strategy:
  1. Walk all .py files with the stdlib ast module to build a map of
     function name -> ordered parameter names (skipping self/cls).
  2. Walk each file again with libcst, and for every Call node whose
     callee name is in the map, rewrite bare positional Arg nodes to
     keyword Arg nodes using the corresponding parameter name.

Limitations:
  - Name resolution is by function/method name only; if two different
    functions share a name the last one collected wins.
  - Starred arguments (*a, **kw) in a call are left untouched and abort
    conversion for that entire call to stay safe.
"""

import ast
import sys
from pathlib import Path

import libcst as cst

ROOT_DIR = Path(__file__).parent


def collect_params(source_files: list[Path]) -> dict[str, list[str]]:
    """Return {function_name: [param, ...]} for every def in source_files."""
    result: dict[str, list[str]] = {}
    for path in source_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
                result[node.name] = params
    return result


class PositionalToKeyword(cst.CSTTransformer):
    def __init__(self, params: dict[str, list[str]]) -> None:
        self.params = params

    @staticmethod
    def _callee_name(func: cst.BaseExpression) -> str | None:
        if isinstance(func, cst.Name):
            return func.value
        if isinstance(func, cst.Attribute):
            return func.attr.value
        return None

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        name = self._callee_name(func=updated_node.func)
        if name is None or name not in self.params:
            return updated_node

        # Bail out on any starred argument — can't safely convert.
        if any(arg.star for arg in updated_node.args):
            return updated_node

        param_names = self.params[name]
        new_args: list[cst.Arg] = []
        positional_idx = 0
        changed = False

        for arg in updated_node.args:
            if arg.keyword is not None:
                # Already a keyword arg; keep as-is.
                new_args.append(arg)
            elif positional_idx < len(param_names):
                new_args.append(
                    arg.with_changes(
                        keyword=cst.Name(param_names[positional_idx]),
                        equal=cst.AssignEqual(
                            whitespace_before=cst.SimpleWhitespace(""),
                            whitespace_after=cst.SimpleWhitespace(""),
                        ),
                    )
                )
                positional_idx += 1
                changed = True
            else:
                # More positional args than known params (e.g. *varargs in def).
                new_args.append(arg)
                positional_idx += 1

        if not changed:
            return updated_node

        return updated_node.with_changes(args=new_args)


def process_file(path: Path, params: dict[str, list[str]], dry_run: bool) -> bool:
    source = path.read_text(encoding="utf-8")
    try:
        tree = cst.parse_module(source)
    except cst.ParserSyntaxError as e:
        print(f"  SKIP (parse error): {path}: {e}")
        return False

    new_tree = tree.visit(PositionalToKeyword(params))
    if new_tree.code == source:
        return False

    if dry_run:
        print(f"  would update: {path}")
    else:
        path.write_text(new_tree.code, encoding="utf-8")
        print(f"  updated: {path}")
    return True


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    files = sorted(ROOT_DIR.rglob("*.py"))

    print(f"Collecting signatures from {len(files)} files...")
    params = collect_params(source_files=files)
    print(f"Found {len(params)} functions/methods.\n")

    changed = sum(process_file(path=f, params=params, dry_run=dry_run) for f in files)
    label = "would modify" if dry_run else "modified"
    print(f"\nDone — {label} {changed} file(s).")


if __name__ == "__main__":
    main()
