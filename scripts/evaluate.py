"""Run the small, reproducible Bug Trail evaluation set."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph import BugTrailGraph
from app.investigator import Investigator


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    cases = json.loads((root / "evaluation" / "cases.json").read_text(encoding="utf-8"))
    try:
        investigator = Investigator(BugTrailGraph())
    except Exception as exc:
        print("Could not connect to FalkorDB at localhost:6379.")
        print("Start FalkorDB with `docker compose up -d falkordb`, then run this script again.")
        print(f"Connection detail: {exc}")
        raise SystemExit(2) from exc
    passed = 0

    print("Bug Trail evaluation")
    print("=" * 72)
    for case in cases:
        result = investigator.investigate(case["description"])
        function_ok = result["suspected_function"] == case["expected_function"]
        commit_ok = result["evidence"]["commit"]["id"] == case["expected_commit"]
        case_ok = function_ok and commit_ok
        passed += int(case_ok)
        print(f"[{ 'PASS' if case_ok else 'FAIL' }] {case['name']}")
        print(f"  expected: {case['expected_function']} / {case['expected_commit']}")
        print(f"  actual:   {result['suspected_function']} / {result['evidence']['commit']['id']}")

    print("=" * 72)
    print(f"Result: {passed}/{len(cases)} cases passed")
    if passed != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

