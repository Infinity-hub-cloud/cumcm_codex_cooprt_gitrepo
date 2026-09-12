from __future__ import annotations

import argparse
import json

from .config import TRACKS
from .runner import compare_tracks, run_q4_3, validate_input_only


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Q4-3 causal rolling price-aware runner")
    root.add_argument("--config", default="config/q4_3_baseline.json")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-input")
    run = commands.add_parser("run")
    run.add_argument("--track", required=True, choices=TRACKS)
    run.add_argument("--output-dir", required=True)
    run.add_argument("--allow-formal-run", action="store_true", help="use only after explicit human authorization")
    compare = commands.add_parser("compare")
    compare.add_argument("--run-root", required=True)
    compare.add_argument("--output", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "validate-input":
        print(json.dumps(validate_input_only(args.config), ensure_ascii=False, indent=2, default=str)); return 0
    if args.command == "compare":
        print(compare_tracks(args.run_root, args.output)); return 0
    output = run_q4_3(args.config, args.output_dir, args.track, allow_formal_run=args.allow_formal_run)
    print(output); return 0


if __name__ == "__main__":
    raise SystemExit(main())
