# C analysis

`results/fusion_overall_metrics.csv` compares B and C separately for
DeepSeek-v4-flash and GPT-6 Luna. `fusion_vs_baseline_comparison.csv` gives the
same-model metric differences. `stage2_revision_analysis.json` counts correct
and incorrect Stage 1 to C flips and retentions, plus the reported evolution
evidence reliability categories. All files are rebuilt from the one released
GT and frozen predictions by `04_analysis/scripts/build_final_paper_sync.py`.
