# Comparison dataset fields

The original benchmark warning fields are retained. Evaluation fields are:

| Field | Meaning |
|---|---|
| `ground_truth_label` | Released human TP/FP label |
| `heuristic_label` | A prediction |
| `deepseek_baseline_label` | DeepSeek B prediction |
| `gpt_baseline_label` | GPT-6 Luna B prediction |
| `deepseek_fusion_label` | DeepSeek C prediction |
| `gpt_fusion_label` | GPT-6 Luna C prediction |

All six labels are binary TP/FP. `warning_id` is unique across 1,027 rows.
