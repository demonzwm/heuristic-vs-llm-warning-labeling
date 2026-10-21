# RQ2 agreement subset

`shared_llm_518_warning_level.csv` contains the 518 warnings where the
independent DeepSeek-v4-flash and GPT-6 Luna LLM predictions agree. This
selection depends only on those two unchanged predictions; ground truth is
joined afterward for evaluation.

With the released Heuristic, 377 of the 518 share its label and 141 disagree:
109 Heuristic FP / shared LLM TP, and 32 Heuristic TP / shared LLM FP.
`shared_llm_518_summary.json` records IDs, GT counts, and correctness for the
groups. `warning_level_agreement.csv`, `prediction_agreement.csv`, and
`disagreement_matrix.csv` cover all 1,027 warnings.

All tables are rebuilt by `04_analysis/scripts/build_final_paper_sync.py`.
