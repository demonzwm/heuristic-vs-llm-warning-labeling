# 04_analysis

This directory contains paper-facing analysis material.

## Contents

- `ground_truth/`: the only authoritative ground-truth TP/FP labels.
- `scripts/build_final_paper_sync.py`: rebuilds the final comparison dataset and paper tables.
- `results/rq1/`: overall, SCA-level, and CWE-level comparison tables.
- `results/rq2/`: disagreement and complementarity analysis tables.
- `results/final_dataset/`: final comparison dataset joining metadata, GT, heuristic labels, and baseline labels for evaluation.
- `figures/`: reserved for paper figures.

## Rebuild

Run:

```powershell
python 04_analysis/scripts/build_final_paper_sync.py
```

The script loads ground truth only at evaluation time. Prediction runners do not load `04_analysis/ground_truth/`.
