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
    audit = {"scope": "frozen predictions; no labels are changed",
             "structural_validation_passed": True,
             "semantic_consistency_rule": (
                 "TP requires defect_hypothesis_status=SUPPORTED; "
                 "FP must not have defect_hypothesis_status=SUPPORTED. "
                 "UNRESOLVED/UNRESOLVED with FP is not counted because the binary policy "
                 "can choose FP after explaining insufficient defect evidence."
             ), "models": {}}
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
        conflicts = []
        for rid in sorted(ids):
            verification = cmap[rid]["verification"]
            defect = verification["defect_hypothesis_status"]
            safety = verification["safety_hypothesis_status"]
            label = cmap[rid]["final_label"]
            if label == "TP" and defect != "SUPPORTED":
                kind = "TP_WITHOUT_SUPPORTED_DEFECT"
            elif label == "FP" and defect == "SUPPORTED":
                kind = "FP_DESPITE_SUPPORTED_DEFECT"
            else:
                continue
            conflicts.append({"warning_id": rid, "issue": kind, "final_label": label,
                              "defect_hypothesis_status": defect,
                              "safety_hypothesis_status": safety})
        audit["models"][model] = {"structural_validation_passed": True,
                                   "stage2_coverage": 1027,
                                   "semantic_consistency_passed": not conflicts,
                                   "status_label_conflict_count": len(conflicts),
                                   "status_label_conflicts": conflicts}
        print(f"{model}: structural checks passed for 1,027 warnings; "
              f"{len(conflicts)} status/label conflicts recorded")
    assert [audit["models"][m]["status_label_conflict_count"]
            for m in ("deepseek_v4_flash", "gpt_6_luna")] == [12, 79]
    output = FUSION / "analysis/results/verification_consistency_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
