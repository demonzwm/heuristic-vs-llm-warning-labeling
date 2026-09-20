# 05_fusion

This directory contains the self-contained final fusion strategy. All final inputs, Stage 1 output, prompts, CWE knowledge, schemas, runners, completed predictions, and analysis summaries needed by the Fusion artifact are inside this repository.

## Method Boundary

- Heuristic and LLM independently produce initial labels.
- Agreement cases keep the initial label.
- Disagreement cases enter Stage 2.
- Stage 1 uses warning-related code slices and CWE knowledge.
- Stage 2 uses the code slice, Stage 1 output, structured warning-evolution information, and a CWE-specific reasoning schema.
- Stage 2 constructs a defect hypothesis and a safety hypothesis before producing a final TP/FP label.
- `heuristic_label_for_routing_only` is retained only to decide whether Stage 2 is needed. It is not passed to the Stage 2 prompt.

## Contents

- `method/prompts/`: final Stage 1 and Stage 2 prompts.
- `method/knowledge/`: CWE knowledge used by Stage 1.
- `method/schemas/`: CWE-specific and generic Stage 2 reasoning schemas.
- `method/data/fusion_inference_input_1027.json`: inference-only input without evaluation label fields.
- `method/stage1/stage1_results_1027.json`: final unified 1,027-warning Stage 1 output.
- `method/scripts/`: preparation, preflight, and executable Fusion runners.
- `deepseek/results/final_run/`: completed DeepSeek fusion predictions and run summaries.
- `gpt/results/final_run/`: completed GPT fusion predictions and run summaries.
- `analysis/results/`: fusion evaluation artifacts and aggregate summaries.
- `analysis/scripts/`: scripts for summarizing completed fusion runs.

## Validation

Run:

```powershell
python 05_fusion/method/scripts/prepare_fusion_materials.py --preflight
python 05_fusion/method/scripts/run_deepseek_fusion.py --preflight
python 05_fusion/method/scripts/run_gpt_fusion.py --preflight
python 05_fusion/analysis/scripts/summarize_fusion_results.py
```

These commands perform local checks or aggregate completed results. They do not call model APIs.

## Execution

`run_deepseek_fusion.py --execute` and `run_gpt_fusion.py --execute` run the final Fusion method and call the configured API endpoint. API keys, model names, and base URLs must be supplied through environment variables or command-line arguments. Local checkpoint and raw-response files are written under `05_fusion/runtime/`, which is ignored by `.gitignore`.

This cleanup did not execute either runner.
