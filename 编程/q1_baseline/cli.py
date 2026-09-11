from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import run_q1, validate_input_only
from .solver_backend import HighsPyBackend


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage-5 Q1 B0/B1 implementation; solve only via explicit run command."
    )
    parser.add_argument(
        "--config", default="config/q1_baseline.json", help="Q1 JSON config path"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="check runtime capability without solving")
    commands.add_parser("validate-input", help="validate input and time mapping only")
    run = commands.add_parser("run", help="human-authorized B0/B1 solve and export")
    run.add_argument("--output-dir", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.config)
    if args.command == "doctor":
        print(
            json.dumps(
                {
                    "config_exists": config_path.is_file(),
                    "highspy_available": HighsPyBackend.available(),
                    "solve_executed": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "validate-input":
        print(json.dumps(validate_input_only(config_path), ensure_ascii=False, indent=2))
        return 0
    completed = run_q1(config_path, args.output_dir)
    print(f"Human-run unreviewed candidate written to: {completed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

