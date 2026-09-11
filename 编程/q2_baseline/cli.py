from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import run_q2, validate_input_only
from .candidate_forecast import EXPERIMENTS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Q2 causal forecast + daily MILP + R0 baseline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-input", help="read/validate only; never invokes solver")
    validate.add_argument("--config", required=True, type=Path)
    run = subparsers.add_parser("run", help="HUMAN ONLY: full Jan warmup and Feb-Dec candidate run")
    run.add_argument("--config", required=True, type=Path)
    run.add_argument("--output-dir", required=True, type=Path)
    run.add_argument("--experiment", choices=EXPERIMENTS, default="baseline")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate-input":
        print(json.dumps(validate_input_only(args.config), ensure_ascii=False, indent=2))
        return 0
    destination = run_q2(args.config, args.output_dir, experiment=args.experiment)
    print(f"Q2 human-run candidate created at: {destination}")
    print("Status: HUMAN_RUN_UNREVIEWED_CANDIDATE; not a final competition result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

