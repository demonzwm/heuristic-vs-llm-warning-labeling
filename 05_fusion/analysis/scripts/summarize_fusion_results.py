from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
FUSION_DIR = REPO_ROOT / "05_fusion"
ANALYSIS_RESULTS = FUSION_DIR / "analysis" / "results"

DEEPSEEK_METRICS = FUSION_DIR / "deepseek" / "results" / "final_run" / "metrics_summary.json"
GPT_METRICS = FUSION_DIR / "gpt" / "results" / "final_run" / "metrics_summary.json"
GPT_BRANCH = ANALYSIS_RESULTS / "branch_analysis.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def metric_row(model: str, approach: str, metrics: dict[str, Any]) -> dict[str, Any]:
    fields = ["TP", "FP", "TN", "FN", "Precision", "Recall", "F1", "Accuracy"]
    return {"model": model, "approach": approach, **{field: metrics[field] for field in fields}}


def main() -> None:
    deepseek = load_json(DEEPSEEK_METRICS)
    gpt = load_json(GPT_METRICS)
    gpt_branch = load_json(GPT_BRANCH)
    deepseek_fusion = deepseek["fusion"]

    overall_rows = [
        metric_row("DeepSeek-v4-flash", "LLM baseline", deepseek["deepseek"]),
        metric_row("DeepSeek-v4-flash", "Fusion", deepseek_fusion),
        metric_row("GPT", "LLM baseline", gpt["gpt_baseline"]),
        metric_row("GPT", "Fusion", gpt["gpt_fusion"]),
    ]
    write_csv(
        ANALYSIS_RESULTS / "fusion_overall_metrics.csv",
        overall_rows,
        ["model", "approach", "TP", "FP", "TN", "FN", "Precision", "Recall", "F1", "Accuracy"],
    )

    comparison_rows = [
        {
            "model": "DeepSeek-v4-flash",
            "baseline_accuracy": deepseek["deepseek"]["Accuracy"],
            "fusion_accuracy": deepseek_fusion["Accuracy"],
            "baseline_f1": deepseek["deepseek"]["F1"],
            "fusion_f1": deepseek_fusion["F1"],
            "baseline_fp": deepseek["deepseek"]["FP"],
            "fusion_fp": deepseek_fusion["FP"],
        },
        {
            "model": "GPT",
            "baseline_accuracy": gpt["gpt_baseline"]["Accuracy"],
            "fusion_accuracy": gpt["gpt_fusion"]["Accuracy"],
            "baseline_f1": gpt["gpt_baseline"]["F1"],
            "fusion_f1": gpt["gpt_fusion"]["F1"],
            "baseline_fp": gpt["gpt_baseline"]["FP"],
            "fusion_fp": gpt["gpt_fusion"]["FP"],
        },
    ]
    write_csv(
        ANALYSIS_RESULTS / "fusion_vs_baseline_comparison.csv",
        comparison_rows,
        ["model", "baseline_accuracy", "fusion_accuracy", "baseline_f1", "fusion_f1", "baseline_fp", "fusion_fp"],
    )

    revision_summary = {
        "DeepSeek-v4-flash": {
            "routing": deepseek["routing"],
            "branch_a": deepseek["branch_a"],
            "branch_b": deepseek["branch_b"],
            "evolution_contribution": deepseek.get("evolution_contribution", {}),
            "cross_evidence": deepseek.get("cross_evidence", {}),
        },
        "GPT": {
            "routing": gpt_branch["routing"],
            "branch_a": gpt_branch["branch_a"],
            "branch_b": gpt_branch["branch_b"],
            "agreement_accuracy": gpt_branch.get("agreement_accuracy"),
            "disagreement_accuracy": gpt_branch.get("disagreement_accuracy"),
        },
    }
    (ANALYSIS_RESULTS / "stage2_revision_analysis.json").write_text(
        json.dumps(revision_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Wrote fusion analysis summaries.")


if __name__ == "__main__":
    main()
