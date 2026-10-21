# Comparison dataset

`final_comparison_dataset_1027.json` has one row per warning. It joins the
benchmark metadata and code slice with the released GT, Heuristic, each
independent LLM, each frozen Stage 1, and both final EvoVerify labels. It is generated solely by
`04_analysis/scripts/build_final_paper_sync.py`. Do not use it as model input.
