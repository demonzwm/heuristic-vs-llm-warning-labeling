from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fusion_common import PATHS, load_json, write_preflight_report


def load_stage1_by_id() -> dict[int, dict[str, Any]]:
    rows = load_json(PATHS.stage1_results)
    by_id: dict[int, dict[str, Any]] = {}
    for row in rows:
        warning_id = int(row.get("warning_id", row.get("record_id")))
        by_id[warning_id] = {
            "semantic_prediction": row.get("semantic_prediction") or row.get("stage1_prediction"),
            "semantic_confidence": row.get("semantic_confidence") or row.get("stage1_confidence"),
            "supporting_reasoning": row.get("supporting_reasoning") or row.get("stage1_reasoning"),
            "uncertainty": row.get("uncertainty") or row.get("stage1_uncertainty", ""),
        }
    return by_id


def load_evolution_by_id() -> dict[int, dict[str, Any]]:
    rows = load_json(PATHS.heuristic_evolution)
    by_id: dict[int, dict[str, Any]] = {}
    for row in rows:
        warning_id = int(row.get("warning_id", row.get("record_id", row.get("id"))))
        by_id[warning_id] = row
    return by_id


def build_inference_input() -> list[dict[str, Any]]:
    heuristic_rows = load_json(PATHS.heuristic_labels)
    stage1_by_id = load_stage1_by_id()
    evolution_by_id = load_evolution_by_id()
    output: list[dict[str, Any]] = []
    for row in heuristic_rows:
        warning_id = int(row.get("warning_id", row.get("warning_info", {}).get("warning_id")))
        info = row.get("warning_info", row)
        output.append(
            {
                "warning_id": warning_id,
                "tool_name": info.get("tool_name"),
                "project_name": info.get("project_name"),
                "project_name_with_version": info.get("project_name_with_version"),
                "project_version": info.get("project_version"),
                "file_path": info.get("file_path"),
                "line_number": info.get("line_number"),
                "function_name": info.get("function_name"),
                "cwe": info.get("cwe"),
                "rule_id": info.get("rule_id"),
                "message": info.get("message"),
                "severity": info.get("severity"),
                "sliced_code": info.get("sliced_code"),
                "stage1": stage1_by_id.get(warning_id, {}),
                "heuristic_label_for_routing_only": row.get("heuristic_label")
                or row.get("heuristic_based_labeling", {}).get("label"),
                "structured_warning_evolution": evolution_by_id.get(warning_id, {}),
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare fusion inference-only material without evaluation label fields.")
    parser.add_argument("--write", action="store_true", help="Write fusion_inference_input_1027.json.")
    parser.add_argument("--preflight", action="store_true", help="Run fusion preflight after preparation.")
    args = parser.parse_args()

    if args.write:
        rows = build_inference_input()
        PATHS.inference_input.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {PATHS.inference_input}")
    if args.preflight or not args.write:
        ok = write_preflight_report()
        print(f"Preflight report: {PATHS.preflight_report} ({'PASS' if ok else 'FAIL'})")
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
