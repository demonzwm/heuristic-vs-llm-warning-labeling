# 03_llm

This directory contains the RQ1/RQ2 LLM baselines.

## Scope

The baseline uses warning metadata and the warning-related code slice only. It does not use CWE knowledge, heuristic labels, fusion routing information, or manual ground truth during prediction.

## Contents

- `prompts/baseline_binary_prompt.py`: final binary TP/FP baseline prompt.
- `scripts/deepseek/`: retained DeepSeek baseline scripts.
- `scripts/gpt/run_gpt_baseline.py`: GPT baseline runner/preflight entry point.
- `deepseek/results/`: completed DeepSeek baseline predictions and evaluation reports.
- `gpt/results/`: completed GPT baseline predictions.

## GPT Configuration

The GPT runner reads:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `GPT_MODEL`

Running `python 03_llm/scripts/gpt/run_gpt_baseline.py --preflight` performs only local validation and does not call an API.
