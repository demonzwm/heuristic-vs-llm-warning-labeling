"""Build paper tables from released GT and frozen heuristic, LLM, fusion predictions."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "04_analysis/results"
FUSION = ROOT / "05_fusion"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def table(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mapping(path, id_fn, label_fn):
    data = read(path)
    result = {int(id_fn(x)): label_fn(x) for x in data}
    assert len(data) == len(result) == 1027 and set(result.values()) <= {"TP", "FP"}, path
    return result


def score(rows, field):
    c = Counter((r["ground_truth_label"], r[field]) for r in rows)
    tp, fp, fn, tn = c["TP", "TP"], c["FP", "TP"], c["TP", "FP"], c["FP", "FP"]
    p = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * recall / (p + recall) if p + recall else 0
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "Precision": round(p, 6),
            "Recall": round(recall, 6), "F1": round(f1, 6),
            "Accuracy": round((tp + tn) / len(rows), 6)}


def cwes(raw):
    return [str(x) for x in raw] if isinstance(raw, list) else [
        x.strip() for x in str(raw or "").replace(",", ";").split(";") if x.strip()]


def transitions(rows, old_field, new_field):
    result = {}
    for old in ("TP", "FP"):
        for new in ("TP", "FP"):
            subset = [x for x in rows if x[old_field] == old and x[new_field] == new]
            result[f"{old}->{new}"] = {
                "count": len(subset),
                "warning_ids": [x["warning_id"] for x in subset],
                "ground_truth": dict(Counter(x["ground_truth_label"] for x in subset)),
            }
    return result


def build():
    gt = mapping(ROOT / "04_analysis/ground_truth/ground_truth_labels_1027.json",
                 lambda x: x["warning_id"], lambda x: x["ground_truth_label"])
    a = mapping(ROOT / "02_heuristic/results/heuristic_labels_1027.json",
                lambda x: x["warning_info"]["warning_id"], lambda x: x["heuristic_based_labeling"]["label"])
    db = mapping(ROOT / "03_llm/deepseek/results/deepseek_v4_flash_semantic_baseline_1027.json",
                 lambda x: x["warning_info"]["warning_id"], lambda x: x["llm_based_labeling"]["deepseek"]["label"])
    gb = mapping(ROOT / "03_llm/gpt/results/gpt_6_luna_baseline_predictions_1027.json",
                 lambda x: x["warning_id"], lambda x: x["label"])
    ds1 = mapping(FUSION / "method/stage1/deepseek_v4_flash/semantic_predictions_1027.json",
                  lambda x: x["warning_id"], lambda x: x["semantic_prediction"])
    gs1 = mapping(FUSION / "method/stage1/gpt_6_luna/semantic_predictions_1027.json",
                  lambda x: x["warning_id"], lambda x: x["semantic_prediction"])
    dcp = FUSION / "deepseek_v4_flash/results/fusion_predictions_1027.json"
    gcp = FUSION / "gpt_6_luna/results/fusion_predictions_1027.json"
    dc = mapping(dcp, lambda x: x["warning_id"], lambda x: x["final_label"])
    gc = mapping(gcp, lambda x: x["warning_id"], lambda x: x["final_label"])
    benchmark = read(ROOT / "01_dataset/processed/benchmark/benchmark_warnings_1027.json")
    ids = {int(x["warning_id"]) for x in benchmark}
    assert len(benchmark) == 1027 and all(set(m) == ids for m in (gt, a, db, gb, ds1, gs1, dc, gc))
    rows = [{**x, "ground_truth_label": gt[int(x["warning_id"])],
             "heuristic_label": a[int(x["warning_id"])],
             "deepseek_llm_label": db[int(x["warning_id"])],
             "gpt_6_luna_llm_label": gb[int(x["warning_id"])],
             "deepseek_stage1_label": ds1[int(x["warning_id"])],
             "gpt_6_luna_stage1_label": gs1[int(x["warning_id"])],
             "deepseek_fusion_label": dc[int(x["warning_id"])],
             "gpt_6_luna_fusion_label": gc[int(x["warning_id"])]} for x in benchmark]
    assert Counter(x["ground_truth_label"] for x in rows) == {"TP": 54, "FP": 973}
    save(RESULTS / "final_dataset/final_comparison_dataset_1027.json", rows)
    baseline = [("Heuristic", "heuristic_label"),
                ("LLM (DeepSeek-v4-flash)", "deepseek_llm_label"),
                ("LLM (GPT-6 Luna)", "gpt_6_luna_llm_label")]
    table(RESULTS / "rq1/overall_comparison.csv",
          [{"approach": name, **score(rows, field)} for name, field in baseline])
    table(RESULTS / "rq1/sca_level_comparison.csv",
          [{"tool": tool, "approach": name, "sample_count": len(subset), **score(subset, field)}
           for tool in sorted({x["tool_name"] for x in rows})
           for subset in [[x for x in rows if x["tool_name"] == tool]]
           for name, field in baseline])
    expanded = [{**x, "cwe_token": token} for x in rows for token in (cwes(x.get("cwe")) or ["<NO-CWE>"])]
    table(RESULTS / "rq1/cwe_level_comparison.csv",
          [{"cwe": cwe, "sample_count": len(subset),
            "gt_tp_count": sum(x["ground_truth_label"] == "TP" for x in subset),
            "gt_fp_count": sum(x["ground_truth_label"] == "FP" for x in subset),
            "approach": name, **score(subset, field)}
           for cwe in sorted({x["cwe_token"] for x in expanded})
           for subset in [[x for x in expanded if x["cwe_token"] == cwe]]
           for name, field in baseline])
    groups = Counter()
    cases = []
    for x in rows:
        correct = tuple(x[field] == x["ground_truth_label"] for _, field in baseline)
        category = {(1, 1, 1): "all correct", (0, 0, 0): "all incorrect",
                    (1, 0, 0): "only heuristic correct", (0, 1, 0): "only DeepSeek LLM correct",
                    (0, 0, 1): "only GPT LLM correct"}.get(correct, "mixed")
        groups[category] += 1
        cases.append({"warning_id": x["warning_id"], "tool_name": x["tool_name"],
                      "rule_id": x["rule_id"], "cwe": "; ".join(cwes(x.get("cwe"))),
                      "ground_truth_label": x["ground_truth_label"],
                      "heuristic_label": x["heuristic_label"],
                      "deepseek_llm_label": x["deepseek_llm_label"],
                      "gpt_6_luna_llm_label": x["gpt_6_luna_llm_label"], "category": category})
    table(RESULTS / "rq2/prediction_agreement.csv",
          [{"category": k, "count": groups[k]} for k in sorted(groups)])
    table(RESULTS / "rq2/warning_level_agreement.csv", cases)
    table(RESULTS / "rq2/disagreement_matrix.csv",
          [{"pair": name, **{f"heuristic_{left}_llm_{right}": sum(x["heuristic_label"] == left and x[field] == right for x in rows)
                             for left in ("TP", "FP") for right in ("TP", "FP")}}
           for name, field in (("Heuristic vs DeepSeek LLM", "deepseek_llm_label"),
                               ("Heuristic vs GPT LLM", "gpt_6_luna_llm_label"))])
    shared_llm = [x for x in rows if x["deepseek_llm_label"] == x["gpt_6_luna_llm_label"]]
    assert len(shared_llm) == 518
    shared_cases = [{"warning_id": x["warning_id"], "ground_truth_label": x["ground_truth_label"],
                     "heuristic_label": x["heuristic_label"], "shared_llm_label": x["deepseek_llm_label"],
                     "relation": "disagreement" if x["heuristic_label"] != x["deepseek_llm_label"] else "agreement"}
                    for x in shared_llm]
    table(RESULTS / "rq2/shared_llm_518_warning_level.csv", shared_cases)
    discordant = [x for x in shared_cases if x["relation"] == "disagreement"]
    save(RESULTS / "rq2/shared_llm_518_summary.json", {
        "selection_rule": "DeepSeek-v4-flash LLM label equals GPT-6 Luna LLM label",
        "selected_warnings": 518,
        "heuristic_vs_shared_llm": {"agreement": len(shared_cases)-len(discordant), "disagreement": len(discordant)},
        "disagreement_directions": {
            "heuristic_FP_shared_llm_TP": sum(x["heuristic_label"] == "FP" for x in discordant),
            "heuristic_TP_shared_llm_FP": sum(x["heuristic_label"] == "TP" for x in discordant),
        },
        "groups": [
            {"relation": relation, "heuristic_label": heuristic, "shared_llm_label": llm,
             "count": len(subset), "ground_truth": dict(Counter(x["ground_truth_label"] for x in subset)),
             "heuristic_correct": sum(x["heuristic_label"] == x["ground_truth_label"] for x in subset),
             "llm_correct": sum(x["shared_llm_label"] == x["ground_truth_label"] for x in subset)}
            for relation in ("agreement", "disagreement")
            for heuristic in ("TP", "FP") for llm in ("TP", "FP")
            for subset in [[x for x in shared_cases if x["relation"] == relation
                            and x["heuristic_label"] == heuristic and x["shared_llm_label"] == llm]]
            if subset
        ],
    })
    summary = []
    fusion_sca = []
    fusion_cwe = []
    revisions = {}
    label_transitions = {}
    for model, bfield, sfield, cfield, path in (
        ("DeepSeek-v4-flash", "deepseek_llm_label", "deepseek_stage1_label", "deepseek_fusion_label", dcp),
        ("GPT-6 Luna", "gpt_6_luna_llm_label", "gpt_6_luna_stage1_label", "gpt_6_luna_fusion_label", gcp),
    ):
        methods = (("LLM", bfield), ("Stage 1", sfield), ("Fusion", cfield))
        summary.extend(({"model": model, "method": method, **score(rows, field)}
                        for method, field in methods))
        fusion_sca.extend({"model": model, "method": method, "tool": tool,
                           "sample_count": len(subset), **score(subset, field)}
                          for tool in sorted({x["tool_name"] for x in rows})
                          for subset in [[x for x in rows if x["tool_name"] == tool]]
                          for method, field in methods)
        fusion_cwe.extend({"model": model, "method": method, "cwe": cwe,
                           "sample_count": len(subset), **score(subset, field)}
                          for cwe in sorted({x["cwe_token"] for x in expanded})
                          for subset in [[x for x in expanded if x["cwe_token"] == cwe]]
                          for method, field in methods)
        items = read(path)
        stage1 = {int(x["warning_id"]): x["stage1_label"] for x in items}
        outcomes = Counter()
        for x in rows:
            rid = int(x["warning_id"])
            outcomes[("correct" if x[cfield] == x["ground_truth_label"] else "incorrect") +
                     ("_retain" if stage1[rid] == x[cfield] else "_flip")] += 1
            if stage1[rid] != x[cfield]:
                outcomes[stage1[rid] + "_to_" + x[cfield]] += 1
        reliability = Counter(x["verification"]["evolution_evidence_reliability"] for x in items)
        assert sum(outcomes[k] for k in ("correct_retain", "incorrect_retain", "correct_flip", "incorrect_flip")) == 1027
        revisions[model] = {"stage2_coverage": 1027, "outcomes": dict(outcomes),
                            "evolution_evidence_reliability": dict(reliability)}
        label_transitions[model] = {
            "independent_llm_to_stage2": transitions(rows, bfield, cfield),
            "stage1_to_stage2": transitions(rows, sfield, cfield),
        }
    table(FUSION / "analysis/results/fusion_overall_metrics.csv", summary)
    table(FUSION / "analysis/results/fusion_sca_metrics.csv", fusion_sca)
    table(FUSION / "analysis/results/fusion_cwe_metrics.csv", fusion_cwe)
    table(FUSION / "analysis/results/fusion_vs_baseline_comparison.csv",
          [{"model": name, "llm_F1": b["F1"], "stage1_F1": s["F1"], "fusion_F1": c["F1"],
            "fusion_minus_llm_F1": round(c["F1"]-b["F1"], 6),
            "fusion_minus_stage1_F1": round(c["F1"]-s["F1"], 6),
            "llm_precision": b["Precision"], "stage1_precision": s["Precision"],
            "fusion_precision": c["Precision"],
            "llm_recall": b["Recall"], "stage1_recall": s["Recall"],
            "fusion_recall": c["Recall"]}
           for name in ("DeepSeek-v4-flash", "GPT-6 Luna")
           for b, s, c in [[x for x in summary if x["model"] == name]]])
    save(FUSION / "analysis/results/stage2_revision_analysis.json", revisions)
    save(FUSION / "analysis/results/label_transitions.json", label_transitions)
    print("Rebuilt GT, heuristic, LLM, fusion, RQ1, and RQ2 analyses.")


if __name__ == "__main__":
    build()
