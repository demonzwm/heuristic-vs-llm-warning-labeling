# Code-slice LLM baselines

DeepSeek-v4-flash predictions are in `deepseek/results/`. GPT-6 Luna predictions
are in `gpt/results/gpt_6_luna_baseline_predictions_1027.json`. The baseline
task template is `prompts/baseline_binary_prompt.py`. The DeepSeek runner loads
this template and supplies each warning's metadata and code slice as JSON.
Both released prediction sets use binary TP/FP labels; neither baseline uses
heuristic labels, evolution evidence, or GT as an inference input.

Run `python 03_llm/scripts/gpt/validate_gpt_baseline.py` to check the GPT
prediction IDs, labels, and model identity without contacting an API. RQ1/RQ2
metrics are rebuilt under `04_analysis/` from the released GT.
