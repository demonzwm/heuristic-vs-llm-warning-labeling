from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = REPO_ROOT / "01_dataset" / "processed" / "benchmark" / "benchmark_warnings_1027.json"
GROUND_TRUTH_PATH = REPO_ROOT / "04_analysis" / "ground_truth" / "ground_truth_labels_1027.json"
HEURISTIC_PATH = REPO_ROOT / "02_heuristic" / "results" / "heuristic_labels_1027.json"
DEEPSEEK_PATH = REPO_ROOT / "03_llm" / "deepseek" / "results" / "deepseek_v4_flash_semantic_baseline_1027.json"
GPT_PATH = REPO_ROOT / "03_llm" / "gpt" / "results" / "gpt_ouol_1027.json"

RESULTS_DIR = REPO_ROOT / "04_analysis" / "results"
FINAL_DATASET_PATH = RESULTS_DIR / "final_dataset" / "final_comparison_dataset_1027.json"
RQ1_DIR = RESULTS_DIR / "rq1"
RQ2_DIR = RESULTS_DIR / "rq2"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"), strict=False)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def norm_label(value: Any) -> str:
    label = str(value or "").strip().upper()
    if label not in {"TP", "FP"}:
        raise ValueError(f"Invalid TP/FP label: {value!r}")
    return label


def norm_tool(value: Any) -> str:
    text = str(value or "").strip().lower()
    return {
        "codeql": "CodeQL",
        "cppcheck": "Cppcheck",
        "csa": "Clang Static Analyzer",
        "clang static analyzer": "Clang Static Analyzer",
    }.get(text, str(value or ""))


def cwe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    return [part.strip() for part in str(value).replace(",", ";").split(";") if part.strip()]


def confusion(rows: list[dict[str, Any]], pred_key: str) -> dict[str, Any]:
    tp = sum(1 for row in rows if row["ground_truth_label"] == "TP" and row[pred_key] == "TP")
    fp = sum(1 for row in rows if row["ground_truth_label"] == "FP" and row[pred_key] == "TP")
    tn = sum(1 for row in rows if row["ground_truth_label"] == "FP" and row[pred_key] == "FP")
    fn = sum(1 for row in rows if row["ground_truth_label"] == "TP" and row[pred_key] == "FP")
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(rows) if rows else 0.0
    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "Precision": round(precision, 6),
        "Recall": round(recall, 6),
        "F1": round(f1, 6),
        "Accuracy": round(accuracy, 6),
    }


def deepseek_label_map() -> dict[int, str]:
    text = DEEPSEEK_PATH.read_text(encoding="utf-8-sig", errors="replace")
    pattern = re.compile(r'"warning_id"\s*:\s*(\d+).*?"llm_based_labeling"\s*:\s*\{.*?"deepseek"\s*:\s*\{.*?"label"\s*:\s*"(TP|FP)"', re.S)
    labels = {int(match.group(1)): match.group(2) for match in pattern.finditer(text)}
    if len(labels) != 1027:
        raise RuntimeError(f"Expected 1027 DeepSeek labels, extracted {len(labels)}")
    return labels


def gpt_label_map() -> dict[int, str]:
    rows = load_json(GPT_PATH)
    labels: dict[int, str] = {}
    for row in rows:
        warning_id = int(row["warning_info"]["warning_id"])
        labels[warning_id] = norm_label(row["llm_based_labeling"]["gpt"]["label"])
    return labels


def build_final_rows() -> list[dict[str, Any]]:
    benchmark = load_json(BENCHMARK_PATH)
    gt = {int(row["warning_id"]): norm_label(row["ground_truth_label"]) for row in load_json(GROUND_TRUTH_PATH)}
    heuristic = {}
    for row in load_json(HEURISTIC_PATH):
        warning_id = int(row.get("warning_id", row.get("warning_info", {}).get("warning_id")))
        label = row.get("heuristic_label") or row.get("heuristic_based_labeling", {}).get("label")
        heuristic[warning_id] = norm_label(label)
    deepseek = deepseek_label_map()
    gpt = gpt_label_map()
    rows: list[dict[str, Any]] = []
    for row in benchmark:
        warning_id = int(row["warning_id"])
        rows.append(
            {
                **row,
                "ground_truth_label": gt[warning_id],
                "heuristic_label": heuristic[warning_id],
                "deepseek_label": deepseek[warning_id],
                "gpt_label": gpt[warning_id],
            }
        )
    if len(rows) != 1027:
        raise RuntimeError(f"Expected 1027 final rows, built {len(rows)}")
    return rows


def write_final_dataset(rows: list[dict[str, Any]]) -> None:
    FINAL_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINAL_DATASET_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_rq1(rows: list[dict[str, Any]]) -> None:
    approaches = [
        ("Heuristic", "heuristic_label"),
        ("DeepSeek-v4-flash", "deepseek_label"),
        ("GPT", "gpt_label"),
    ]
    metric_fields = ["TP", "FP", "TN", "FN", "Precision", "Recall", "F1", "Accuracy"]

    overall_rows = [{"approach": name, **confusion(rows, key)} for name, key in approaches]
    write_csv(RQ1_DIR / "overall_comparison.csv", overall_rows, ["approach", *metric_fields])

    sca_rows: list[dict[str, Any]] = []
    for tool in sorted({norm_tool(row["tool_name"]) for row in rows}):
        subset = [row for row in rows if norm_tool(row["tool_name"]) == tool]
        for name, key in approaches:
            sca_rows.append({"tool": tool, "approach": name, **confusion(subset, key)})
    write_csv(RQ1_DIR / "sca_level_comparison.csv", sca_rows, ["tool", "approach", *metric_fields])

    expanded: list[dict[str, Any]] = []
    for row in rows:
        cwes = cwe_list(row.get("cwe")) or ["<NO-CWE>"]
        for cwe in cwes:
            expanded.append({**row, "cwe_token": cwe})
    cwe_rows: list[dict[str, Any]] = []
    for cwe in sorted({row["cwe_token"] for row in expanded}):
        subset = [row for row in expanded if row["cwe_token"] == cwe]
        gt_tp = sum(1 for row in subset if row["ground_truth_label"] == "TP")
        gt_fp = sum(1 for row in subset if row["ground_truth_label"] == "FP")
        for name, key in approaches:
            cwe_rows.append(
                {
                    "cwe": cwe,
                    "sample_count": len(subset),
                    "gt_tp_count": gt_tp,
                    "gt_fp_count": gt_fp,
                    "approach": name,
                    **confusion(subset, key),
                }
            )
    write_csv(RQ1_DIR / "cwe_level_comparison.csv", cwe_rows, ["cwe", "sample_count", "gt_tp_count", "gt_fp_count", "approach", *metric_fields])


def build_rq2(rows: list[dict[str, Any]]) -> None:
    categories: Counter[str] = Counter()
    representatives: list[dict[str, Any]] = []
    for row in rows:
        states = {
            "heuristic": row["heuristic_label"] == row["ground_truth_label"],
            "deepseek": row["deepseek_label"] == row["ground_truth_label"],
            "gpt": row["gpt_label"] == row["ground_truth_label"],
        }
        if all(states.values()):
            category = "all three correct"
        elif not any(states.values()):
            category = "all three incorrect"
        elif states["heuristic"] and not states["deepseek"] and not states["gpt"]:
            category = "only heuristic correct"
        elif states["deepseek"] and not states["heuristic"] and not states["gpt"]:
            category = "only DeepSeek correct"
        elif states["gpt"] and not states["heuristic"] and not states["deepseek"]:
            category = "only GPT correct"
        else:
            category = "mixed partial agreement"
        categories[category] += 1
        if category != "mixed partial agreement":
            representatives.append(
                {
                    "warning_id": row["warning_id"],
                    "tool_name": norm_tool(row["tool_name"]),
                    "rule_id": row["rule_id"],
                    "cwe": "; ".join(cwe_list(row.get("cwe"))),
                    "ground_truth_label": row["ground_truth_label"],
                    "heuristic_label": row["heuristic_label"],
                    "deepseek_label": row["deepseek_label"],
                    "gpt_label": row["gpt_label"],
                    "category": category,
                }
            )
    write_csv(RQ2_DIR / "prediction_agreement.csv", [{"category": key, "count": categories[key]} for key in sorted(categories)], ["category", "count"])
    matrix_rows = [
        {
            "pair": "Heuristic vs DeepSeek",
            "heuristic_TP_deepseek_TP": sum(1 for row in rows if row["heuristic_label"] == "TP" and row["deepseek_label"] == "TP"),
            "heuristic_TP_deepseek_FP": sum(1 for row in rows if row["heuristic_label"] == "TP" and row["deepseek_label"] == "FP"),
            "heuristic_FP_deepseek_TP": sum(1 for row in rows if row["heuristic_label"] == "FP" and row["deepseek_label"] == "TP"),
            "heuristic_FP_deepseek_FP": sum(1 for row in rows if row["heuristic_label"] == "FP" and row["deepseek_label"] == "FP"),
        },
        {
            "pair": "Heuristic vs GPT",
            "heuristic_TP_gpt_TP": sum(1 for row in rows if row["heuristic_label"] == "TP" and row["gpt_label"] == "TP"),
            "heuristic_TP_gpt_FP": sum(1 for row in rows if row["heuristic_label"] == "TP" and row["gpt_label"] == "FP"),
            "heuristic_FP_gpt_TP": sum(1 for row in rows if row["heuristic_label"] == "FP" and row["gpt_label"] == "TP"),
            "heuristic_FP_gpt_FP": sum(1 for row in rows if row["heuristic_label"] == "FP" and row["gpt_label"] == "FP"),
        },
    ]
    write_csv(RQ2_DIR / "disagreement_matrix.csv", matrix_rows, sorted({key for row in matrix_rows for key in row}))
    write_csv(RQ2_DIR / "representative_cases.csv", representatives, ["warning_id", "tool_name", "rule_id", "cwe", "ground_truth_label", "heuristic_label", "deepseek_label", "gpt_label", "category"])


def main() -> None:
    rows = build_final_rows()
    write_final_dataset(rows)
    build_rq1(rows)
    build_rq2(rows)
    print("Rebuilt final dataset, RQ1 overall/SCA/CWE tables, and RQ2 disagreement tables.")


if __name__ == "__main__":
    main()
