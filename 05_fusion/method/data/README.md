# Fusion Method Data

- `fusion_inference_input_1027.json`: inference-only input for final fusion. It contains warning metadata, `sliced_code`, Stage 1 semantic output, `heuristic_label_for_routing_only`, and structured warning-evolution information.
- `heuristic_label_for_routing_only` is used only to decide whether the LLM initial label and heuristic initial label disagree. It must not be inserted into the Stage 2 prompt.
- Evaluation labels and human annotation material are outside this directory and are loaded only after prediction.
- `benchmark_warnings_1027.json`, `heuristic_labels_1027.json`, and `heuristic_evolution_evidence_1027.jsonl` are frozen snapshots used to reconstruct or audit the inference input.
