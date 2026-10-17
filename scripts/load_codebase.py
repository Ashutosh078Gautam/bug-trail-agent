"""Extract the synthetic application's functions and call graph into FalkorDB."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph import BugTrailGraph


ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = ROOT / "sample_app"


def extract_functions(path: Path) -> list[dict]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.add(child.func.attr)
        functions.append({
            "name": node.name,
            "file": path.relative_to(ROOT).as_posix(),
            "module": path.stem,
            "line": node.lineno,
            "calls": sorted(calls),
        })
    return functions


def main() -> None:
    graph = BugTrailGraph()
    functions = []
    for path in sorted(SOURCE_ROOT.glob("*.py")):
        functions.extend(extract_functions(path))

    for item in functions:
        graph.query(
            """
            MERGE (m:Module {name: $module})
            MERGE (f:Function {name: $name})
            SET f.file = $file, f.source_line = $line, f.source_module = $module
            MERGE (f)-[:BELONGS_TO]->(m)
            """,
            item,
        )

    names = {item["name"] for item in functions}
    for item in functions:
        for callee in item["calls"]:
            if callee not in names:
                continue
            graph.query(
                """
                MATCH (caller:Function {name: $caller}), (callee:Function {name: $callee})
                MERGE (caller)-[:CALLS]->(callee)
                """,
                {"caller": item["name"], "callee": callee},
            )

    print(f"Loaded {len(functions)} functions and their local call relationships into FalkorDB.")


if __name__ == "__main__":
    main()

