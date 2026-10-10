"""Validate the frozen GPT-6 Luna B run without contacting an API."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUTS = ROOT / "03_llm/gpt/inputs/baseline_prompts_1027.json"
OUTPUT = ROOT / "03_llm/gpt/results/gpt_6_luna_baseline_predictions_1027.json"


def main():
    inputs = json.loads(INPUTS.read_text(encoding="utf-8"))
    outputs = json.loads(OUTPUT.read_text(encoding="utf-8"))
    prompts = {int(x["warning_id"]): x for x in inputs}
    labels = {int(x["warning_id"]): x for x in outputs}
    assert len(inputs) == len(outputs) == len(prompts) == len(labels) == 1027
    for rid, item in prompts.items():
        assert hashlib.sha256(item["prompt"].encode("utf-8")).hexdigest() == item["prompt_sha256"]
        assert labels[rid]["prompt_sha256"] == item["prompt_sha256"]
        assert labels[rid]["label"] in {"TP", "FP"}
        assert labels[rid]["model"] == "gpt-6-luna"
    print("Validated 1,027 GPT-6 Luna B prompts and predictions; no API call.")


if __name__ == "__main__":
    main()
