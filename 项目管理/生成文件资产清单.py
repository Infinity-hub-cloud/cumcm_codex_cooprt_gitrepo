from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "项目管理" / "文件资产清单_20260912.csv"
SUMMARY = ROOT / "项目管理" / "资产状态摘要_20260912.json"
SELF_PATHS = {INVENTORY.resolve(), SUMMARY.resolve()}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def classify(relative: str) -> tuple[str, str, str, str]:
    posix = relative.replace("\\", "/")
    lower = posix.lower()

    if "/__pycache__/" in f"/{lower}" or lower.endswith(".pyc"):
        return "generated_cache", "GENERATED_CACHE", "NO", "解释器缓存，不是成果"
    if posix.startswith("C题/"):
        return "official_c_problem_material", "OFFICIAL_READ_ONLY", "SOURCE", "题面、附件或官方结果模板"
    if posix.startswith("B题/"):
        return "retained_other_problem", "OUT_OF_SCOPE", "NO", "保留但不作为C题输入"
    if posix.startswith("论文/cumcm-paper-agent-skills/"):
        return "third_party_paper_tooling", "VENDOR_READ_ONLY", "TOOL_ONLY", "供应方工具包，不写入项目状态"
    if posix.startswith("论文/"):
        return "paper_workspace", "CURRENT", "NAVIGATION", "论文手入口或工作区"
    if posix.startswith("建模/"):
        return "model_specification", "CURRENT_WITH_HISTORICAL_STATUS", "METHOD", "模型规格；状态以总导航校正"
    if posix.startswith("项目管理/"):
        return "project_management", "CURRENT", "NAVIGATION", "资产清单与维护记录"
    if posix.startswith("编程/归档/"):
        return "archive", "HISTORICAL", "AUDIT_ONLY", "归档证据或历史快照"
    if posix.startswith("编程/runs/q3_20260912_"):
        return "q3_old_run_evidence", "OBSOLETE_Q3_SEMANTICS", "AUDIT_ONLY", "旧时间/费用语义，不作当前Q3结果"
    if posix.startswith("编程/runs/q2_low_complexity_20260912_002010/weekday_buffer/"):
        return "q2_frozen_run_evidence", "ACCEPTED_FROZEN", "RESULT_EVIDENCE", "Q2冻结主模型运行证据"
    if posix.startswith("编程/runs/q2_low_complexity_20260912_002010/"):
        return "q2_ablation_run_evidence", "PASSED_EVIDENCE", "COMPARISON_EVIDENCE", "Q2保留公平对照"
    if posix.startswith("编程/runs/q1_human_run_"):
        return "q1_run_evidence", "PASSED_EVIDENCE", "RESULT_EVIDENCE", "Q1人工通过运行包"
    if posix.startswith("编程/runs/"):
        return "historical_run_evidence", "HISTORICAL", "AUDIT_ONLY", "旧运行、失败或非冻结结果"
    if posix.startswith("编程/human_run_logs/"):
        return "human_console_log", "HISTORICAL_EVIDENCE", "AUDIT_ONLY", "人工运行控制台留痕"
    if posix.startswith("编程/交付候选/Q2_20260912_weekday_buffer/"):
        return "q2_delivery_candidate", "ACCEPTED_FROZEN_PENDING_SUBMISSION", "RESULT_OR_TABLE", "主模型已冻结，提交批准另行确认"
    if posix.startswith("编程/交付候选/"):
        return "delivery_candidate", "PENDING_HUMAN_APPROVAL", "CANDIDATE_ONLY", "候选交付层"
    if posix.startswith("编程/审计/") or posix.startswith("编程/audit_q3_") or posix == "编程/test_q3_audit_contracts.py":
        return "audit_evidence_or_tool", "CURRENT_AUDIT", "AUDIT_ONLY", "独立审计输出或工具"
    if posix.startswith("编程/预处理审计输出_Q3修订版_点值语义/"):
        return "q3_revised_mapping", "CURRENT", "INPUT_EVIDENCE", "Q3当前point/ZOH/INTERP映射"
    if posix.startswith("编程/预处理审计输出_时间口径修订版/"):
        return "q1_q2_normalized_input", "CURRENT", "INPUT_EVIDENCE", "Q1/Q2当前正式预处理"
    if posix.startswith("编程/预处理审计输出/"):
        return "old_normalized_input", "HISTORICAL", "AUDIT_ONLY", "首版口径，不作当前输入"
    if posix.startswith("编程/q3_baseline/") or posix == "编程/config/q3_baseline.json" or posix == "编程/requirements-q3.txt":
        return "q3_source_or_config", "PENDING_HUMAN_RUN", "METHOD", "Q3修订版生产实现"
    if posix.startswith("编程/q2_baseline/") or posix == "编程/config/q2_baseline.json" or posix == "编程/requirements-q2.txt":
        return "q2_source_or_config", "ACCEPTED_FROZEN", "METHOD", "Q2冻结主模型实现"
    if posix.startswith("编程/q1_baseline/") or posix == "编程/config/q1_baseline.json" or posix == "编程/requirements-q1.txt":
        return "q1_source_or_config", "PASSED", "METHOD", "Q1已通过实现"
    if posix.startswith("编程/tests/"):
        return "test_suite", "CURRENT", "VALIDATION", "共享测试；部分Solver测试需人工运行"
    if posix.startswith("编程/"):
        return "programming_document_or_tool", "CURRENT", "METHOD_OR_NAVIGATION", "编程说明、工具或导航"
    if posix == "format2026.doc":
        return "official_format_template", "OFFICIAL_READ_ONLY", "TEMPLATE", "比赛论文格式模板"
    if posix.endswith(".md"):
        return "shared_specification_or_protocol", "CURRENT_WITH_HISTORY", "METHOD_OR_NAVIGATION", "共享协议、规划或基线文档"
    return "shared_root_asset", "RETAINED", "CHECK_CONTEXT", "共享区根文件"


def main() -> None:
    files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
    ]
    files.extend(path for path in SELF_PATHS if path not in files)
    rows: list[dict[str, object]] = []
    for path in sorted(set(files), key=lambda item: item.relative_to(ROOT).as_posix().casefold()):
        relative = path.relative_to(ROOT).as_posix()
        asset_class, status, paper_use, notes = classify(relative)
        if path.resolve() in SELF_PATHS:
            size = path.stat().st_size if path.exists() else ""
            modified = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds") if path.exists() else ""
            digest = "SELF_NOT_HASHED"
        else:
            stat = path.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
            digest = sha256(path)
        rows.append(
            {
                "relative_path": relative,
                "top_area": relative.split("/", 1)[0],
                "asset_class": asset_class,
                "lifecycle_status": status,
                "size_bytes": size,
                "modified_local": modified,
                "sha256": digest,
                "paper_use": paper_use,
                "notes": notes,
            }
        )

    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    with INVENTORY.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    status_counts = Counter(str(row["lifecycle_status"]) for row in rows)
    class_counts = Counter(str(row["asset_class"]) for row in rows)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "workspace": str(ROOT),
        "file_count_including_inventory_records": len(rows),
        "total_bytes_excluding_self_records": sum(int(row["size_bytes"]) for row in rows if isinstance(row["size_bytes"], int)),
        "excluded": [".git directory and all Git internal objects"],
        "self_hash_policy": "inventory and summary rows use SELF_NOT_HASHED to avoid recursive self-reference",
        "lifecycle_status_counts": dict(sorted(status_counts.items())),
        "asset_class_counts": dict(sorted(class_counts.items())),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
