# Fusion Analysis

This directory separates evaluation artifacts from model prediction artifacts.

## Contents

- `results/fusion_overall_metrics.csv`: DeepSeek/GPT baseline and fusion metrics.
- `results/fusion_vs_baseline_comparison.csv`: baseline-to-fusion comparison summary.
- `results/stage2_revision_analysis.json`: Stage 2 branch and revision summary.
- `results/baseline_vs_final_fusion.csv`, `results/branch_analysis.json`, `results/mcnemar_result.json`: GPT Fusion evaluation and comparison artifacts moved out of the model final-run directory.
- `results/stage1_results_with_evaluation.json`: Stage 1 output copy with evaluation label fields, kept as an evaluation artifact.
- `results/gpt_stage1_predictions_with_evaluation.json`: GPT Stage 1 output copy with evaluation label fields, kept as an evaluation artifact.
- `results/deepseek_final_predictions_with_evaluation.json`: DeepSeek prediction file with evaluation correctness fields, kept as an evaluation artifact.
- `results/integrated_warning_labels_1027_with_evaluation_fields.json`: historical integrated labels with evaluation fields, kept only for audit.
- `scripts/summarize_fusion_results.py`: regenerates aggregate fusion analysis files from completed result summaries.
- `figures/`: reserved for fusion figures.

The model result directories keep prediction artifacts. Files with evaluation labels or correctness fields belong here.
