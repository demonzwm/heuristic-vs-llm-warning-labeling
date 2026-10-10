# Method C: full warning verification

C has two stages for each of the 1,027 warnings. Stage 1 judges code semantics
using the warning slice and CWE knowledge. Stage 2 receives that model's own
Stage 1 output, the slice, original cross-version matching facts, the CWE
checklist, and five constructed demonstrations. It verifies both a defect
hypothesis and a safety hypothesis before returning a binary TP/FP label.

Every warning received Stage 2 verification, independent of A or B's labels.
The matching algorithm and A prediction are unchanged. Stage 2 receives
matching facts, but not A's final TP/FP label or GT. The model-specific
prompt snapshots record the exact inputs used in the completed runs.

## Released files

- `method/prompts/`, `method/schemas/`, `method/knowledge/`, and
  `method/demonstrations/`: reasoning instructions and constructed examples.
- `method/stage1/{deepseek_v4_flash,gpt_6_luna}/`: each model's own 1,027 semantic outputs.
- `method/inputs/{deepseek_v4_flash,gpt_6_luna}/`: exact 1,027 Stage 2 prompts per model.
- `{deepseek_v4_flash,gpt_6_luna}/results/fusion_predictions_1027.json`: C label and full
  verification for every warning.
- `analysis/results/`: same-model B/C metrics and Stage 1 to C revision counts.

Run `python 05_fusion/method/scripts/validate_fusion_release.py` for offline
coverage, prompt-hash, label, and input-isolation checks. Rebuild evaluation
with `python 04_analysis/scripts/build_final_paper_sync.py`.
