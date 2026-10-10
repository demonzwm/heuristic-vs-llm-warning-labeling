# Static-Analysis Warning Validation: Paper Artifact

This directory contains the single paper release for 1,027 warnings. The
approaches are **Heuristic** (cross-version warning matching), **LLM**
(code-slice judgment), and **Fusion** (semantic and warning-evolution
verification). Fusion sends **every** warning to Stage 2. TP is the positive class.

The selected ground truth contains 54 TP and 973 FP. Heuristic predictions
are unchanged. DeepSeek-v4-flash and GPT-6 Luna each have their own LLM and Fusion
predictions; comparisons use the same model within each pair. GPT-6 Luna used
low reasoning effort. No API call is needed to inspect or rebuild this release.

## Directory map

- `01_dataset/`: benchmark warnings and source warning data.
- `02_heuristic/`: matching algorithm and its 1,027 predictions.
- `03_llm/`: LLM prompts, exact GPT prompt snapshots, and model predictions.
- `04_analysis/`: one GT, the comparison dataset, RQ1/RQ2 tables, and rebuild script.
- `05_fusion/`: per-model Stage 1, all-warning Stage 2 inputs, verification outputs, and analysis.
- `ARTIFACT_MANIFEST.json`: model settings and hashes of released data and prompt files.

## Offline validation and rebuild

```powershell
python 03_llm/scripts/gpt/validate_gpt_baseline.py
python 05_fusion/method/scripts/validate_fusion_release.py
python 04_analysis/scripts/build_final_paper_sync.py
python 04_analysis/scripts/build_artifact_manifest.py
python 04_analysis/scripts/verify_artifact_manifest.py
```

The analysis command rebuilds the comparison dataset and all reported RQ1, RQ2,
and Fusion summary tables from the one GT and frozen predictions. GT is read only
by the evaluation script, never by model input preparation.

Fusion validation has two separate outcomes: structural checks verify 1,027
inputs, IDs, prompt hashes, and frozen outputs; semantic auditing records cases
where a hypothesis status conflicts with the final binary label. Structural
checks pass, while `05_fusion/analysis/results/verification_consistency_audit.json`
records 12 DeepSeek and 79 GPT-6 Luna status/label conflicts. No frozen label
is corrected by this audit.

The RQ2 shared-LLM subset selects the 518 warnings where DeepSeek and GPT-6 Luna
LLM labels agree. The heuristic disagrees with their shared label on 136 of
these; IDs and subgroup counts are in `04_analysis/results/rq2/`.

Manifest hashes use the repository's LF byte form. The verifier normalizes
CRLF worktree files to LF before hashing, so the same manifest works on GitHub
and Windows checkouts.

Model prompts and predictions are preserved from the completed runs. This
release does not include API keys or upstream repository source checkouts.
