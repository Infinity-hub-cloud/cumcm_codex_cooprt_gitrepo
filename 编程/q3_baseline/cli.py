from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

from q1_baseline.solver_backend import HighsPyBackend

from .config import TRACKS, load_config
from .runner import run_q3_track, validate_input_only
from .runner import value_decomposition


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Q3 rolling PV/purchase implementation")
    parser.add_argument("--config", default="config/q3_baseline.json")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="show environment without invoking a solver")
    sub.add_parser("validate-input", help="run hash/schema/time checks without solving")
    run = sub.add_parser("run", help="HUMAN-RUN ONLY: run one formal Q3 track")
    run.add_argument("--track", choices=TRACKS, required=True)
    run.add_argument("--issue-set", choices=("0only", "0_12", "rolling4"))
    run.add_argument("--output-dir", required=True)
    compare = sub.add_parser("compare", help="compare completed human-run tracks without solving")
    compare.add_argument("--reference-metrics", required=True)
    compare.add_argument("--initial-metrics", required=True)
    compare.add_argument("--rolling-metrics", required=True)
    compare.add_argument("--no-storage-metrics")
    compare.add_argument("--output", required=True)
    revised = sub.add_parser("compare-revised", help="identity-gated revised Q3 value decomposition; no solve")
    revised.add_argument("--reference-metrics", required=True)
    for name in ("initial-zoh", "initial-interp", "rolling-zoh", "rolling-interp", "no-storage", "cost-a"):
        revised.add_argument(f"--{name}-run", required=True)
    revised.add_argument("--issue-frequency-run")
    revised.add_argument("--output", required=True)
    return parser


def _metrics(path: str, *, q2_frozen_reference: bool = False) -> dict[str, float]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if q2_frozen_reference:
        rows = [
            row
            for row in rows
            if row.get("model_id") == "M2-Q2-EXPERIMENT-weekday_buffer-v1.0"
            and row.get("baseline_id") == "B1_WEEKDAY_BUFFER_MILP_R0"
            and row.get("split") == "formal_output"
            and row.get("period") == "formal_output"
        ]
        aliases = {
            "total_cost_yuan": "total_cost",
            "planned_purchase_cost_yuan": "planned_purchase_cost",
            "emergency_purchase_cost_yuan": "emergency_purchase_cost",
            "emergency_kwh": "emergency_energy",
            "surplus_kwh": "spill_energy",
            "charge_kwh": "total_charge",
            "discharge_kwh": "total_discharge",
        }
    else:
        aliases = {}
    result: dict[str, float] = {}
    for row in rows:
        metric = aliases.get(str(row.get("metric")), str(row.get("metric")))
        if metric in result:
            raise ValueError(f"duplicate selected metric {metric}: {path}")
        result[metric] = float(row["value"])
    if "total_cost" not in result:
        raise ValueError(f"total cost metric not found for selected model/split: {path}")
    if q2_frozen_reference:
        result.update(
            {
                "downward_penalty": 0.0,
                "upward_adjustment_cost": 0.0,
                "adjust_down_energy": 0.0,
                "adjust_up_energy": 0.0,
            }
        )
    return result


def _component_savings(baseline: dict[str, float], candidate: dict[str, float]) -> dict[str, float]:
    def value(metrics: dict[str, float], key: str) -> float:
        return float(metrics.get(key, 0.0))

    return {
        "total_cost": value(baseline, "total_cost") - value(candidate, "total_cost"),
        "planned_purchase_cost": value(baseline, "planned_purchase_cost")
        - value(candidate, "planned_purchase_cost"),
        "regular_purchase_cost": value(baseline, "regular_purchase_cost")
        - value(candidate, "regular_purchase_cost"),
        "fulfilled_normal_purchase_cost": value(baseline, "fulfilled_normal_purchase_cost")
        - value(candidate, "fulfilled_normal_purchase_cost"),
        "cancelled_purchase_principal": value(baseline, "cancelled_purchase_principal")
        - value(candidate, "cancelled_purchase_principal"),
        "positive_downward_breach_penalty": value(baseline, "downward_penalty")
        - value(candidate, "downward_penalty"),
        "adjustment_cost": (
            value(baseline, "downward_penalty")
            + value(baseline, "upward_adjustment_cost")
            - value(candidate, "downward_penalty")
            - value(candidate, "upward_adjustment_cost")
        ),
        "emergency_purchase_cost": value(baseline, "emergency_purchase_cost")
        - value(candidate, "emergency_purchase_cost"),
        "emergency_energy": value(baseline, "emergency_energy")
        - value(candidate, "emergency_energy"),
        "spill_energy": value(baseline, "spill_energy") - value(candidate, "spill_energy"),
        "storage_throughput": (
            value(baseline, "total_charge")
            + value(baseline, "total_discharge")
            - value(candidate, "total_charge")
            - value(candidate, "total_discharge")
        ),
    }

def _bundle(directory: str) -> tuple[dict[str, object], dict[str, float]]:
    root=Path(directory);manifest=json.loads((root/"run_manifest.json").read_text(encoding="utf-8"))
    return manifest,_metrics(str(root/"metrics_summary.csv"))

def _revised_decomposition(args: argparse.Namespace) -> dict[str, object]:
    names=("initial_zoh","initial_interp","rolling_zoh","rolling_interp","no_storage","cost_a")
    bundles={name:_bundle(getattr(args,f"{name}_run")) for name in names}
    expected={"initial_zoh":"Q3_A3_0ONLY_ZOH","initial_interp":"Q3_A3_0ONLY_INTERP","rolling_zoh":"Q3_ROLLING_ZOH","rolling_interp":"Q3_ROLLING_INTERP","no_storage":"Q3_NOSTORAGE","cost_a":"Q3_COST_A_SENSITIVITY"}
    for name,(manifest,_) in bundles.items():
        if manifest.get("track") != expected[name] or manifest.get("formal_output_start") != "2025-02-01" or manifest.get("formal_output_end") != "2025-12-31":
            raise ValueError(f"run identity/date mismatch: {name}")
    baseline=bundles["rolling_interp"][0]
    common=("model_version","data_version","formal_output_start","formal_output_end")
    for name,(manifest,_) in bundles.items():
        if any(manifest.get(key)!=baseline.get(key) for key in common):
            raise ValueError(f"cross-run model/data/date mismatch: {name}")
        if manifest.get("code_identity",{}).get("core_python_sha256") != baseline.get("code_identity",{}).get("core_python_sha256"):
            raise ValueError(f"cross-run code hash mismatch: {name}")
        expected_cost="MODEL_A" if name=="cost_a" else "MODEL_B"
        if manifest.get("cost_semantics") != expected_cost:
            raise ValueError(f"cost semantics mismatch: {name}")
    reference=_metrics(args.reference_metrics,q2_frozen_reference=True)
    metric={name:value for name,(_,value) in bundles.items()}
    result={
        "Value_A3_initial":reference["total_cost"]-metric["initial_interp"]["total_cost"],
        "Value_intraday_update":metric["initial_interp"]["total_cost"]-metric["rolling_interp"]["total_cost"],
        "Value_interpolation":metric["rolling_zoh"]["total_cost"]-metric["rolling_interp"]["total_cost"],
        "Value_storage":metric["no_storage"]["total_cost"]-metric["rolling_interp"]["total_cost"],
        "Cost_semantics_sensitivity_A_minus_B":metric["cost_a"]["total_cost"]-metric["rolling_interp"]["total_cost"],
        "identity_gate":"PASS",
        "sign_convention":"positive means the named feature lowered formal_output total_cost",
        "note":"Q2 reference is a frozen external model; Q3 pairwise attributions passed same-core-code/data/date gates. A/B is sensitivity, not direct attribution.",
    }
    if args.issue_frequency_run:
        manifest,value=_bundle(args.issue_frequency_run)
        if manifest.get("code_identity",{}).get("core_python_sha256") != baseline.get("code_identity",{}).get("core_python_sha256") or manifest.get("cost_semantics")!="MODEL_B":
            raise ValueError("issue-frequency identity mismatch")
        result["Value_issue_frequency"] = value["total_cost"]-metric["rolling_interp"]["total_cost"]
    return result


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "doctor":
        config = load_config(Path(args.config))
        print(json.dumps({
            "python": sys.version,
            "platform": platform.platform(),
            "model_version": config.model_version,
            "solver_backend_available": HighsPyBackend.available(),
            "solve_executed": False,
        }, ensure_ascii=False, indent=2))
        return 0
    if args.command == "validate-input":
        print(json.dumps(validate_input_only(args.config), ensure_ascii=False, indent=2))
        return 0
    if args.command == "compare":
        reference = _metrics(args.reference_metrics, q2_frozen_reference=True)
        initial = _metrics(args.initial_metrics)
        rolling = _metrics(args.rolling_metrics)
        result = {
            **value_decomposition(
                reference["total_cost"], initial["total_cost"], rolling["total_cost"]
            ),
            "component_savings_baseline_minus_candidate": {
                "Attachment3_Initial_vs_REF_Q2_FROZEN": _component_savings(reference, initial),
                "Intraday_Rolling_vs_Attachment3_Initial": _component_savings(initial, rolling),
                "Q3_Rolling_vs_REF_Q2_FROZEN": _component_savings(reference, rolling),
            },
            "sign_convention": "positive means the candidate reduced the named cost/energy versus its baseline",
        }
        if args.no_storage_metrics:
            no_storage = _metrics(args.no_storage_metrics)
            result["Value_Storage_in_Q3_Rolling"] = (
                no_storage["total_cost"] - rolling["total_cost"]
            )
            result["component_savings_baseline_minus_candidate"][
                "Storage_Q3_Rolling_vs_Q3_NoStorage"
            ] = _component_savings(no_storage, rolling)
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "compare-revised":
        result=_revised_decomposition(args)
        Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    requested_destination = Path(args.output_dir).resolve()
    destination_existed_before_run = requested_destination.exists()
    try:
        output = run_q3_track(
            args.config,
            args.output_dir,
            args.track,
            issue_set_name=args.issue_set,
        )
        print(output)
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        destination = requested_destination
        evidence = destination
        if destination_existed_before_run:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            evidence = destination.parent / f"{destination.name}_launch_failure_{stamp}"
        evidence.mkdir(parents=True, exist_ok=not destination_existed_before_run)
        (evidence / "warnings_and_failures.log").write_text(
            traceback.format_exc(), encoding="utf-8"
        )
        (evidence / "run_manifest.failure.json").write_text(
            json.dumps(
                {
                    "question_id": "Q3",
                    "track": args.track,
                    "run_status": "FAILED",
                    "requested_output_dir": str(destination),
                    "failure_evidence_dir": str(evidence),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
