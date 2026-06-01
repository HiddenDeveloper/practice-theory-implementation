"""Run golden-situation evals.

    uv run python -m evals.run                      # all cases, scripted driver
    uv run python -m evals.run --provider codex     # all cases, live codex pass
    uv run python -m evals.run --provider claude    # all cases, live Claude pass
    uv run python -m evals.run judge_unevaluated_proposal --provider scripted

The scripted driver validates the harness + grading mechanics without a model
call. The codex (OpenAI) and claude (Anthropic) drivers run a real practitioner
and are the actual test of the apprenticeship. Exit code is non-zero if any
selected case fails.
"""

from __future__ import annotations

import argparse
import sys

from evals.cases import CASES
from evals.harness import run_case_sync


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run golden-situation evals.")
    parser.add_argument(
        "cases",
        nargs="*",
        help="case ids to run (default: all)",
    )
    parser.add_argument(
        "--provider",
        default="scripted",
        choices=["scripted", "codex", "claude"],
        help=(
            "who plays the practitioner: scripted (no model), codex (OpenAI "
            "Codex CLI), or claude (Anthropic Claude CLI). Default: scripted"
        ),
    )
    args = parser.parse_args(argv)

    selected = args.cases or list(CASES)
    unknown = [c for c in selected if c not in CASES]
    if unknown:
        parser.error(f"unknown case(s): {', '.join(unknown)}")

    failures = 0
    for case_id in selected:
        case = CASES[case_id]
        try:
            result = run_case_sync(case, provider=args.provider)
        except Exception as exc:  # noqa: BLE001 - surface any harness/adapter error per-case
            failures += 1
            print(f"ERROR {case_id} [{args.provider}]: {type(exc).__name__}: {exc}")
            continue
        status = "PASS" if result["passed"] else "FAIL"
        if not result["passed"]:
            failures += 1
        print(f"{status} {case_id} [{args.provider}]")
        for f in result["evidence"]:
            print(f"    friction: kind={f.get('kind')!r} content={f.get('content')!r}")
        if not result["evidence"]:
            print("    (no friction emitted on the target enactment)")

    print(f"\n{len(selected) - failures}/{len(selected)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
