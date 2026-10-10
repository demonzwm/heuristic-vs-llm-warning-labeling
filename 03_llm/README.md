# Code-slice LLM baselines

DeepSeek-v4-flash predictions are in `deepseek/results/`. GPT-6 Luna predictions are in
`gpt/results/gpt_6_luna_baseline_predictions_1027.json`; its exact 1,027
prompts are in `gpt/inputs/baseline_prompts_1027.json`. The GPT run used low
reasoning effort. Each record has one binary TP/FP label. No heuristic label,
evolution evidence, or GT was supplied to either LLM baseline.

Run `python 03_llm/scripts/gpt/validate_gpt_baseline.py` to check IDs,
prompt hashes, labels, and model identity without contacting an API. RQ1/RQ2
metrics are rebuilt under `04_analysis/` from the released GT.
