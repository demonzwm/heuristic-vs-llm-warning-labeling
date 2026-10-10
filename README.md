# Static-Analysis Warning Validation: Paper Artifact

This directory contains the single paper release for 1,027 warnings. The three
methods are A (cross-version heuristic), B (code-slice LLM baseline), and C
(two-stage semantic and warning-evolution verification). C sends **every**
warning to Stage 2. TP is the positive class.

The selected ground truth contains 54 TP and 973 FP. A's archived predictions
are unchanged. DeepSeek-v4-flash and GPT-6 Luna each have their own B and C
predictions; comparisons use the same model within each pair. GPT-6 Luna used
low reasoning effort. No API call is needed to inspect or rebuild this release.

## Directory map

- `01_dataset/`: benchmark warnings and source warning data.
- `02_heuristic/`: A matching algorithm and its 1,027 predictions.
- `03_llm/`: B prompts, exact GPT prompt snapshots, and model predictions.
- `04_analysis/`: one GT, the A/B/C comparison dataset, RQ1/RQ2 tables, and rebuild script.
- `05_fusion/`: C's per-model Stage 1, all-warning Stage 2 inputs, verification outputs, and analysis.
- `ARTIFACT_MANIFEST.json`: model settings and hashes of released JSON artifacts.

## Offline validation and rebuild

```powershell
python 03_llm/scripts/gpt/validate_gpt_baseline.py
python 05_fusion/method/scripts/validate_fusion_release.py
python 04_analysis/scripts/build_final_paper_sync.py
```

The final command rebuilds the comparison dataset and all reported RQ1, RQ2,
and C summary tables from the one GT and frozen predictions. GT is read only
by the evaluation script, never by model input preparation.

Model prompts and predictions are preserved from the completed runs. This
release does not include API keys or upstream repository source checkouts.
