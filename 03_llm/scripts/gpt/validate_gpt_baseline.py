"""Validate the released GPT-6 Luna baseline predictions offline."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BENCHMARK = ROOT / "01_dataset/processed/benchmark/benchmark_warnings_1027.json"
OUTPUT = ROOT / "03_llm/gpt/results/gpt_6_luna_baseline_predictions_1027.json"


def main():
    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    outputs = json.loads(OUTPUT.read_text(encoding="utf-8"))
    labels = {int(x["warning_id"]): x for x in outputs}
    benchmark_ids = {int(x["warning_id"]) for x in benchmark}
    assert len(benchmark) == len(benchmark_ids) == len(outputs) == len(labels) == 1027
    assert set(labels) == benchmark_ids
    for item in outputs:
        assert item["label"] in {"TP", "FP"}
        assert item["model"] == "gpt-6-luna"
    print("Validated 1,027 GPT-6 Luna baseline predictions; no API call.")


if __name__ == "__main__":
    main()
