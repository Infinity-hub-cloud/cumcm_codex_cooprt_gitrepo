from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .config import PREDICTORS, TRACKS
from .forecast import build_price_forecast_day
from .price import PriceHistory, read_price_records
from .runner import run_q4_2
from .config import load_config
from .integrity import verify_q4_inputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Q4-2 price-aware production code (Stage 5)")
    parser.add_argument("--config", default="config/q4_baseline.json")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-input")
    validate.set_defaults(command="validate-input")
    price = sub.add_parser("price-forecast")
    price.add_argument("--predictor", choices=PREDICTORS, required=True)
    price.add_argument("--date", required=True)
    run = sub.add_parser("run")
    run.add_argument("--track", choices=TRACKS, required=True)
    run.add_argument("--output-dir", required=True)
    run.add_argument("--allow-formal-human-run", action="store_true")
    run.add_argument("--predictor", choices=PREDICTORS)
    compare = sub.add_parser("compare")
    compare.add_argument("--costs-json", required=True, help="JSON mapping of track id to realized cost")
    compare.add_argument("--selected-predictor", required=True, choices=("Q4_2_PRICE_BASELINE_P0", "Q4_2_PRICE_CANDIDATE_P1", "Q4_2_PRICE_CANDIDATE_P2", "Q4_2_PRICE_CANDIDATE_P3"))
    compare.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(Path(args.config).resolve())
    if args.command == "validate-input":
        records = read_price_records(config.normalized_price_input)
        identity = verify_q4_inputs(config)
        print(json.dumps({"passed": True, "rows": len(records), "visibility_rule": config.parameters.visibility_rule, "solver_invoked": False, "sha256": identity["sha256"]}, ensure_ascii=False))
        return 0
    if args.command == "price-forecast":
        result = build_price_forecast_day(date.fromisoformat(args.date), args.predictor, PriceHistory(read_price_records(config.normalized_price_input), config.parameters))
        print(json.dumps({"passed": True, "date": args.date, "predictor": args.predictor, "rows": len(result.rows), "first": result.rows[0], "last": result.rows[-1]}, ensure_ascii=False, default=str))
        return 0
    if args.command == "compare":
        costs = json.loads(Path(args.costs_json).read_text(encoding="utf-8"))
        result = __import__("q4_baseline.runner", fromlist=["build_value_decomposition"]).build_value_decomposition(costs, args.selected_predictor)
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"passed": True, "output": args.output}, ensure_ascii=False))
        return 0
    run_q4_2(args.config, args.output_dir, args.track, allow_formal_run=args.allow_formal_human_run, predictor_override=args.predictor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
