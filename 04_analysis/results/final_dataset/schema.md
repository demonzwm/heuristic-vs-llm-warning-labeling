# Comparison dataset fields

The original benchmark warning fields are retained. Evaluation fields are:

| Field | Meaning |
|---|---|
| `ground_truth_label` | Released human TP/FP label |
| `heuristic_label` | Heuristic prediction |
| `deepseek_llm_label` | DeepSeek-v4-flash LLM prediction |
| `gpt_6_luna_llm_label` | GPT-6 Luna LLM prediction |
| `deepseek_fusion_label` | DeepSeek-v4-flash Fusion prediction |
| `gpt_6_luna_fusion_label` | GPT-6 Luna Fusion prediction |

All six labels are binary TP/FP. `warning_id` is unique across 1,027 rows.
