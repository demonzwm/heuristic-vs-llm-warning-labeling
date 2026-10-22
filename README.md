# Static-Analysis Warning Validation: Paper Artifact

This repository contains the final reproducibility package for 1,027 warnings:
cross-version Heuristic matching, independent code-slice LLM judgments, and
EvoVerify. Every warning enters EvoVerify Stage 2. Its DeepSeek-v4-flash and
GPT-6 Luna variants reuse their own frozen Stage 1 outputs and receive the
released Heuristic's evolution facts.

The paper calls the classes **actionable** and **unactionable**. Stored class
labels remain `TP` (actionable) and `FP` (unactionable); actionable is the
positive class. These class codes differ from the TP/FP/FN/TN entries of a
confusion matrix. The naming map changes neither labels nor metrics.

The released ground truth has 54 TP and 973 FP. The selected Heuristic requires
identical tool, project, and nonempty rule IDs and a strictly later version.
Exact and Location use the complete normalized relative path; Snippet and Hash
can match across files. Each later version is searched by strategy in the order
Exact, Location, Snippet, Hash. Location uses the original matcher's nearest
equal-line offsets with threshold 3. Snippet uses two lines of context on each
side and threshold 0.8; Hash uses the original single-line tokenization and up
to 30 tokens at each end. A later match predicts FP; no match predicts TP.
The executable and full parameters are in `02_heuristic/`.

## Directory map

- `01_dataset/`: 1,027-warning benchmark and preprocessing materials.
- `02_heuristic/`: released matching code, configuration, predictions, and audit.
- `03_llm/`: unchanged independent DeepSeek and GPT predictions.
- `04_analysis/`: unchanged GT and generated Overall, SCA, CWE, and RQ2 tables.
- `05_fusion/`: frozen model-specific Stage 1, complete Stage 2 prompt snapshots,
  matching facts, final EvoVerify predictions, and evaluation.
- `ARTIFACT_MANIFEST.json`: hashes of released data and prompt files.

The independent LLM baseline task template is in
`03_llm/prompts/baseline_binary_prompt.py`; released binary predictions and
their offline checks are described in `03_llm/README.md`. The frozen GPT
request texts are retained under `03_llm/gpt/inputs/`.

## Offline validation and rebuild

```powershell
python 03_llm/scripts/gpt/validate_gpt_baseline.py
python 05_fusion/method/scripts/validate_fusion_release.py
python 04_analysis/scripts/build_final_paper_sync.py
python 04_analysis/scripts/build_artifact_manifest.py
python 04_analysis/scripts/verify_artifact_manifest.py
```

The Heuristic can be rerun without an API by passing the complete external
warning pools and project source checkout to `02_heuristic/scripts/tracker.py`;
see `02_heuristic/README.md`. The analysis rebuild reads the one GT and frozen
predictions. Zero-denominator metrics are reported as 0. A warning can belong
to multiple CWE groups, so CWE counts do not sum to Overall.

Structural EvoVerify validation checks 1,027 IDs, prompt hashes, Stage 1
correspondence, and frozen labels. The separate hypothesis-status audit records
14 DeepSeek and 13 GPT status/label conflicts without changing any label.
Independent LLMs agree on 518 warnings; the released Heuristic disagrees with
their shared label on 141. RQ2 IDs and GT breakdown are in `04_analysis/results/rq2/`.

The final Heuristic and EvoVerify outputs were selected from validated isolated
runs and copied into these stable paths. Original GT, independent LLM results,
and each model's Stage 1 file remain unchanged. The external migration record
contains the prior repository backup, source hashes, and detailed mapping.
No API call is needed to inspect or rebuild this release.
