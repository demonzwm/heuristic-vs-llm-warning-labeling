# Paper analysis

`ground_truth/ground_truth_labels_1027.json` is the sole released GT: 54 TP,
973 FP. The CSV beside it is the same data. The selected source review changed
warning IDs 150, 161, 596, and 983 to TP and 342 to FP; other labels are
unchanged. Warning 200's local annotation note is preserved.

`scripts/build_final_paper_sync.py` reads the frozen Heuristic, LLM, and Fusion results and
rebuilds one joined 1,027-row comparison dataset, RQ1 overall/SCA/CWE tables,
RQ2 agreement tables, the 518-warning shared-LLM subset, and Fusion summary metrics. It never changes predictions.

```powershell
python 04_analysis/scripts/build_final_paper_sync.py
```
