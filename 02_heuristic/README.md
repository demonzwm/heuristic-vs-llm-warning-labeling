# Cross-version Heuristic

`scripts/tracker.py` is the released offline entry point. It evaluates the
unchanged 1,027-warning benchmark against the complete external cross-version
warning pools. Supply those pools and the corresponding project source tree:

```powershell
python 02_heuristic/scripts/tracker.py `
  --source-pool <normalized-warning-pool.json> `
  --cppcheck-pool <cppcheck-warning-pool.json> `
  --source-root <project-version-source-directory>
```

Use `--output-dir` to write an isolated verification run. The runner checks
benchmark IDs, required fields, source directories, files and line numbers
before matching. `input_manifest.json` records the required input hashes.

Candidates must have the same tool, project and nonempty exact `rule_id`, and
must come from a strictly later version. Versions are visited nearest first.
Within each version the full candidate list is searched by Exact, then
Location, Snippet and Hash, retaining original input order within a strategy.
Exact and Location require the complete normalized relative path. Snippet and
Hash allow cross-file matches; no function-name condition or global candidate
reservation is imposed.

Location retains the original nearest-equal-line calculation: in the same
path's line diff, it independently finds the nearest equal line on the old and
new side and accepts an offset difference of at most 3. Snippet retains two
context lines above and below, the original normalization and SequenceMatcher
similarity threshold 0.8. Hash retains the original single-line `\w+`
tokenization, first/last windows of up to 30 tokens, and rejects empty token
matches. The diff uses Python SequenceMatcher with `autojunk=True`. Any later
match predicts FP; otherwise the prediction is TP.

`results/heuristic_labels_1027.json` is the released prediction interface;
`results/heuristic_evolution_evidence_1027.json` and
`results/matching_audit.json` retain matching facts and checks. The prediction
fields use TP/FP as class codes (actionable/unactionable). Evaluation treats
actionable as positive; zero-denominator metrics are 0 and CWE categories may
overlap.
