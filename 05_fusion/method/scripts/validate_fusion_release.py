"""Validate that every warning received full Stage 2 verification."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FUSION = ROOT / "05_fusion"
METHOD = FUSION / "method"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ids = {int(x["warning_id"]) for x in read(ROOT / "01_dataset/processed/benchmark/benchmark_warnings_1027.json")}
    assert len(ids) == 1027
    for model in ("deepseek_v4_flash", "gpt_6_luna"):
        prompts = read(METHOD / "inputs" / model / "stage2_prompts_1027.json")
        stage1 = read(METHOD / "stage1" / model / "semantic_predictions_1027.json")
        predictions = read(FUSION / model / "results/fusion_predictions_1027.json")
        pmap = {int(x["warning_id"]): x for x in prompts}
        smap = {int(x["warning_id"]): x for x in stage1}
        cmap = {int(x["warning_id"]): x for x in predictions}
        assert all(len(x) == 1027 for x in (prompts, stage1, predictions, pmap, smap, cmap))
        assert set(pmap) == set(smap) == set(cmap) == ids
        for rid in ids:
            prompt = pmap[rid]["prompt"]
            assert hashlib.sha256(prompt.encode("utf-8")).hexdigest() == pmap[rid]["prompt_sha256"]
            assert cmap[rid]["prompt_sha256"] == pmap[rid]["prompt_sha256"]
            assert cmap[rid]["stage1_label"] == smap[rid]["semantic_prediction"]
            assert cmap[rid]["final_label"] == cmap[rid]["verification"]["final_label"]
            assert cmap[rid]["final_label"] in {"TP", "FP"}
            assert "ground_truth_label" not in prompt and "manual_annotation" not in prompt
        print(f"{model}: 1,027 full Stage 2 inputs and verified outputs")


if __name__ == "__main__":
    main()
