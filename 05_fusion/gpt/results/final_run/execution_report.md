# GPT Fusion Full 1,027-Warning Run Report

1. actual GPT model
- `gpt-5.4-mini`
2. actual base_url
- `[redacted external endpoint]`
3. actual HTTP caller implementation
- `urllib.request` -> `POST /chat/completions` -> single merged user message
4. request parameters actually sent
- `model`, `messages`, `temperature`
5. retry/resume policy
- success never rerun; temporary failures bounded; terminal failures skipped on resume; per-warning lifetime cap enforced
6. raw persistence policy
- raw HTTP body and assistant content persisted before parsing for both Stage1 and Stage2
7. parser policy
- direct JSON -> fence stripping -> first balanced JSON-object extraction
8. reused Stage1 cache count
- `73`
9. new Stage1 API call count
- `977`
10. Stage2 candidate count
- `246`
11. Stage2 API call count
- `257`
12. retry count
- `34`
13. HTTP error counts
- `{"200": 1234}`
14. parse failure counts
- `37`
15. unresolved terminal failures
- `0`
16. total runtime
- `18227.352` seconds
17. total token usage if available
- input `7668380`, output `462750`, total `8131130`, usage_available=`True`
18. final metrics
- GPT baseline: `{"TP": 18, "FP": 216, "TN": 760, "FN": 33, "Precision": 0.076923, "Recall": 0.352941, "F1": 0.126316, "Accuracy": 0.757546}`
- GPT Fusion: `{"TP": 16, "FP": 81, "TN": 895, "FN": 35, "Precision": 0.164948, "Recall": 0.313725, "F1": 0.216216, "Accuracy": 0.88705}`
19. Branch A/B analysis
- Branch A: `{"candidate_count": 196, "correct_tp_to_fp_revisions": 115, "harmful_tp_to_fp_revisions": 3, "revision_precision": 0.974576, "tp_preservation": 0.785714}`
- Branch B: `{"candidate_count": 50, "correct_fp_to_tp_revisions": 0, "harmful_fp_to_tp_revisions": 0, "revision_precision": null, "fn_recovery": 0.0, "fp_preservation": 1.0}`
20. McNemar result
- `{"baseline_correct_fusion_wrong": 62, "baseline_wrong_fusion_correct": 195, "both_correct": 716, "both_wrong": 54, "changed_prediction_count": 257, "net_corrected_warnings": 133, "p": 0.0}`
21. Stage1 attempt distribution
- `{"min": 1, "median": 1.0, "p95": 1.0, "max": 3}`
22. Stage2 attempt distribution
- `{"min": 1, "median": 1.0, "p95": 1.0, "max": 3}`
23. observed API wall-clock span
- Stage1 `18227.352` seconds; Stage2 `5432.032` seconds
