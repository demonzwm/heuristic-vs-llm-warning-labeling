# Final Artifact Audit

## Scope

This audit covers the self-contained Fusion artifact under `05_fusion/` and repository-level documentation needed to publish it. No model API was called and no completed prediction labels or metric values were regenerated.

## Validation Results

| Check | Result | Detail |
| --- | --- | --- |
| Python files parse | PASS | checked in this cleanup run |
| DeepSeek runner `--help` | PASS | local CLI only |
| GPT runner `--help` | PASS | local CLI only |
| DeepSeek runner `--preflight` | PASS | no API call |
| GPT runner `--preflight` | PASS | no API call |
| Stage 1 record count | PASS | 1027 |
| Stage 1 unique warning IDs | PASS | 1027 |
| Stage 1 evaluation fields absent | PASS | 0 |
| Stage 1 aligns with DeepSeek final Fusion output | PASS | mismatched fields: 0; id sets match: True |
| method/data evaluation fields absent | PASS | all checked JSON/JSONL files clean |
| method code avoids evaluation dependencies | PASS | no method references to evaluation label paths or human annotation material |
| DeepSeek baseline JSON integrity | PASS | restored from the validated original copy; standard JSON parse succeeds with 1027 records and 1027 unique warning IDs |
| retained docs/scripts/provenance avoid external legacy paths and retired terms | PASS | not found in the requested scan scope |
| preflight report avoids machine-specific absolute root paths | PASS | reports repository layout validation and repository-relative hashes |
| checkpoint/cache/log files absent from retained artifact scope | PASS | not found |

## Stage 1 Consolidation

- Source selected: complete 1,027-record historical Stage 1 output, consolidated into `05_fusion/method/stage1/stage1_results_1027.json`.
- Evaluation fields were removed from the method copy and retained under `05_fusion/analysis/results/`.
- The unified Stage 1 output has 1,027 records and 1,027 unique warning IDs.
- Stage 1 prediction, confidence, reasoning, and uncertainty have zero mismatches against the saved DeepSeek final Fusion output.
- Historical execution-only fields `source` and `from_cache` were removed from the canonical method copy without changing record order or prediction fields.

## DeepSeek Final Run Cleanup

- Superseded report/comparison files were moved out of `05_fusion/deepseek/results/final_run/`.
- `metrics_summary.json` and `baseline_comparison.csv` were sanitized to remove obsolete comparison labels while preserving metric values.
- Current final-run retained files no longer reference retired method labels, old local experiment paths, private endpoints, or human annotation material.

## GPT Final Run Cleanup

- GPT evaluation/comparison files were moved from `05_fusion/gpt/results/final_run/` to `05_fusion/analysis/results/`.
- `experiment_run_report.md` was renamed to `execution_report.md`.
- GPT summary keys were renamed to `gpt_stage1`, `gpt_fusion`, and `deepseek_fusion` without changing metric values.
- Current GPT final-run retained files no longer contain obsolete method labels, pilot wording, or evaluation label text.

## Executable Runners

- `05_fusion/method/scripts/run_deepseek_fusion.py` supports `--preflight` and `--execute`.
- `05_fusion/method/scripts/run_gpt_fusion.py` supports `--preflight` and `--execute`.
- `--execute` calls the configured API and writes ignored local runtime files under `05_fusion/runtime/`.
- This cleanup did not execute either runner.

## Required Hashes
- `05_fusion/method/data/fusion_inference_input_1027.json`: `c5dc0bd628c59c12e2de5211ff523c3a55d0757be02af0544f5445543d95c7be`
- `05_fusion/method/stage1/stage1_results_1027.json`: `03de83231faaca6584b94deeda602ded53169983d20fa90579ad9ac85f8df5b5`
- `05_fusion/method/prompts/stage1_semantic_analysis_prompt.txt`: `14c774f4593b8174bcfe83a7a81dc39cc65f9217583300e24ee94420341b2b67`
- `05_fusion/method/prompts/stage2_disagreement_verification_prompt.txt`: `0959abdf86d7291bd4cd00502a9c45430e3306df6ed4dc3f53e7bebd91324a0b`
- `05_fusion/deepseek/results/final_run/final_predictions.json`: `fd66b39b5a7be45271d68070b1804693dfae230dfa2caa1a3b6c9dc236ce4944`
- `05_fusion/gpt/results/final_run/final_predictions.json`: `c2694e59e8ced4a9722b3e65f5afabfebc447db600c3dd522e4ab2ae41af313f`
