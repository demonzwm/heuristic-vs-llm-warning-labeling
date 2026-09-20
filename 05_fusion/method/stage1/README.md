# Stage 1 Output

`stage1_results_1027.json` is the final unified Stage 1 output for the 1,027-warning fusion artifact.

Historical execution involved resumed runs, but the release artifact keeps only this consolidated 1,027-record result. Current Fusion scripts use this file as the only Stage 1 source.

## Fields

- `record_id` / `warning_id`: stable warning identifiers.
- `status`: model-call status from the completed Stage 1 run.
- `model`, `temperature`, `top_p`, `prompt_hash`: Stage 1 run configuration.
- `semantic_prediction`: independent Stage 1 TP/FP prediction.
- `semantic_confidence`: Stage 1 confidence statement.
- `supporting_reasoning`: Stage 1 reasoning based on the warning-related code slice and CWE knowledge.
- `uncertainty`: Stage 1 uncertainty statement.
- `tool_name`, `rule_id`, `project_name`: metadata retained for auditing.

## Method Boundary

Stage 1 uses warning metadata, the warning-related code slice, and Stage 1 CWE knowledge. Stage 1 does not receive heuristic labels or warning-evolution evidence.

Stage 2 receives the Stage 1 output together with the code slice, structured warning-evolution information, and the selected reasoning schema for disagreement cases.
