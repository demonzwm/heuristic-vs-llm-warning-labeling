# Scripts

This directory contains the final dataset-construction scripts for the formal
three-tool pipeline:

- CodeQL
- CSA
- Cppcheck

## Final Pipeline

CodeQL raw  
CSA raw  
Cppcheck raw

↓

Normalization / preprocessing

↓

Filtering

↓

Deduplication

↓

Benchmark construction

## Script List

| Script | Purpose |
| --- | --- |
| `normalize_warnings.py` | Normalize raw CodeQL, CSA, and Cppcheck reports into one unified warning schema |
| `supplement_cwe.py` | Fill missing CWE information from curated tool-specific mappings |
| `filter_cwe_top25.py` | Keep only warnings whose CWE intersects the final Top 25 list |
| `filter_warnings.py` | Remove irrelevant files, `#include` lines, and latest-version warnings |
| `deduplicate_warnings.py` | Reduce repeated warnings within the construction pool using the preserved deduplication key |
| `build_benchmark.py` | Assemble benchmark candidates from the non-Cppcheck and Cppcheck branches |

## Important Construction Note

CodeQL and CSA originated from the initial warning collection, while Cppcheck
was processed separately and integrated later.
