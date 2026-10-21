# Fusion inference materials

Stage 1 uses `prompts/stage1_semantic_analysis_prompt.txt`, the warning slice,
and relevant CWE knowledge. The DeepSeek and GPT-6 Luna Stage 1 outputs are
stored separately under `stage1/`. GPT's exact Stage 1 prompts are also kept
in `inputs/gpt_6_luna/stage1_prompts_1027.json`.

Stage 2 uses `prompts/stage2_full_verification_prompt.txt`, a CWE-476,
CWE-787, or generic checklist from `schemas/`, and the five synthetic cases
in `demonstrations/constructed_examples.md`. `inputs/{deepseek_v4_flash,gpt_6_luna}/` contains
the exact per-warning prompts supplied during each complete run. These input
files include warning metadata, code slices, Stage 1 outputs, and evolution
facts. They contain neither ground truth nor the Heuristic final label.

`data/` contains the benchmark warning input and released Heuristic matching facts.
The method copy of matching facts excludes the Heuristic TP/FP decision. Its published
prediction remains under `02_heuristic/results/` for evaluation only.

`run_config.json` records each model's actual Stage 2 request configuration,
frozen Stage 1 hash, and final prompt/prediction hashes. Both models reused
their own frozen Stage 1 and received the same released evolution facts. The
1,027 final predictions for each model are self-contained; no experiment cache
directory is needed to inspect or evaluate them. Stage 2 requests exclude GT,
annotation reasons, and the Heuristic final class label.

The exact prompt snapshots and responses are the authoritative run record.
`scripts/validate_fusion_release.py` checks full coverage and their hashes
offline. No API request is performed by this release validation script.
