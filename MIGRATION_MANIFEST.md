# Executed Migration Manifest

This manifest records the cleanup operations executed for the current artifact layout. Paths are repository-relative.

## Retained Layout

- `01_dataset/`
- `02_heuristic/`
- `03_llm/`
- `04_analysis/`
- `05_fusion/`

## Current Fusion State

- Fusion is self-contained under `05_fusion/`.
- Prediction-time inputs are in `05_fusion/method/data/`.
- The unified Stage 1 source is `05_fusion/method/stage1/stage1_results_1027.json`.
- Stage 1 and Stage 2 prompts, CWE knowledge, reasoning schemas, and executable runners are in `05_fusion/method/`.
- Completed DeepSeek/GPT predictions are in `05_fusion/deepseek/` and `05_fusion/gpt/`.
- Evaluation-only material is in `05_fusion/analysis/results/`.

## Operations

| Action | Current Path | Notes |
| --- | --- | --- |
| moved evaluation-only integrated labels | `05_fusion/analysis/results/integrated_warning_labels_1027_with_evaluation_fields.json` | Removed evaluation label fields from `method/data/`. |
| created unified Stage 1 output | `05_fusion/method/stage1/stage1_results_1027.json` | 1,027 records, 1,027 unique warning IDs, no evaluation fields. |
| retained Stage 1 evaluation copy | `05_fusion/analysis/results/stage1_results_with_evaluation.json` | Kept outside method runtime inputs. |
| retained GPT Stage 1 evaluation copy | `05_fusion/analysis/results/gpt_stage1_predictions_with_evaluation.json` | Kept outside model prediction artifacts. |
| rewrote Stage 1 provenance | `05_fusion/method/stage1/stage1_provenance.json` | Records only current artifact files, hashes, and validation results. |
| archived superseded DeepSeek run reports | `05_fusion/deepseek/results/final_run/final_report.md`, `05_fusion/deepseek/results/final_run/stage1_vs_final_comparison.csv` | Historical comparison files were moved out of the final result directory. |
| sanitized DeepSeek summary files | `05_fusion/deepseek/results/final_run/metrics_summary.json`, `05_fusion/deepseek/results/final_run/baseline_comparison.csv` | Metric values were preserved while obsolete comparison labels were removed. |
| moved GPT evaluation artifacts | `05_fusion/analysis/results/baseline_vs_final_fusion.csv`, `05_fusion/analysis/results/branch_analysis.json`, `05_fusion/analysis/results/mcnemar_result.json` | GPT comparison/evaluation files were moved out of the model final-run directory without content changes. |
| sanitized GPT final-run summaries | `05_fusion/gpt/results/final_run/execution_report.md`, `05_fusion/gpt/results/final_run/metrics_summary.json` | Obsolete method naming was replaced while preserving all reported values. |
| restored executable DeepSeek runner | `05_fusion/method/scripts/run_deepseek_fusion.py` | Supports `--preflight` and `--execute`; runtime outputs go to ignored local directory. |
| restored executable GPT runner | `05_fusion/method/scripts/run_gpt_fusion.py` | Supports `--preflight` and `--execute`; runtime outputs go to ignored local directory. |
| updated shared Fusion runner utilities | `05_fusion/method/scripts/fusion_common.py` | Uses repository-root-relative paths only. |
| updated Fusion docs | `README.md`, `05_fusion/README.md`, `05_fusion/method/data/README.md`, `05_fusion/method/stage1/README.md` | Documents self-contained Fusion boundary and API execution behavior. |

## Required Hashes

- `05_fusion/method/data/fusion_inference_input_1027.json`: `c5dc0bd628c59c12e2de5211ff523c3a55d0757be02af0544f5445543d95c7be`
- `05_fusion/method/stage1/stage1_results_1027.json`: `03de83231faaca6584b94deeda602ded53169983d20fa90579ad9ac85f8df5b5`
- `05_fusion/method/prompts/stage1_semantic_analysis_prompt.txt`: `14c774f4593b8174bcfe83a7a81dc39cc65f9217583300e24ee94420341b2b67`
- `05_fusion/method/prompts/stage2_disagreement_verification_prompt.txt`: `0959abdf86d7291bd4cd00502a9c45430e3306df6ed4dc3f53e7bebd91324a0b`
- `05_fusion/deepseek/results/final_run/final_predictions.json`: `fd66b39b5a7be45271d68070b1804693dfae230dfa2caa1a3b6c9dc236ce4944`
- `05_fusion/gpt/results/final_run/final_predictions.json`: `c2694e59e8ced4a9722b3e65f5afabfebc447db600c3dd522e4ab2ae41af313f`
