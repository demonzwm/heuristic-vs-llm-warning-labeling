# Final Comparison Dataset Schema

The formal comparison dataset contains one object per warning and integrates benchmark metadata with the final method outputs used for paper analysis.

## Top-level fields

- `warning_info`
  Benchmark-side warning metadata copied from the formal benchmark.

- `heuristic_based_labeling`
  Formal heuristic prediction object.

- `llm_based_labeling`
  Object containing:
  - `deepseek`
  - `gpt`

- `manual_annotation`
  Ground-truth annotation object.

## Usage

This file is intended for:

- RQ1 overall / SCA / rule / CWE comparison,
- RQ2 agreement / disagreement analysis,
- downstream paper tables that require aligned predictions from all formal approaches.
