# heuristic

This directory contains the heuristic-based warning labeling approach.

Inputs: the processed 1,027-warning benchmark and cross-version warning pools.

Outputs: heuristic labels, match types, matched versions, and warning-evolution evidence in `results/`.

External warning pools can be supplied through environment variables when rerunning the heuristic scripts:

- `HEURISTIC_SOURCE_FUNCTION_POOL_PATH`: normalized cross-version warning pool with function/context data.
- `HEURISTIC_CPPCHECK_POOL_PATH`: Cppcheck cross-version warning pool.

Paper mapping: heuristic-based automatic warning labeling baseline using Exact, Location, Snippet, and Token-hash matching.
