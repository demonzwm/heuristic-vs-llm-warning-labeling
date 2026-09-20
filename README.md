# Heuristic vs LLM Warning Validation Artifact

This repository is the paper artifact for comparing cross-version warning matching, LLM baselines, and the final two-stage fusion strategy. It contains artifact scripts, prompts, frozen inputs, predictions, and evaluation outputs. It does not contain the analyzed upstream project source trees.

## Directory Map

- `01_dataset/`: raw and processed warning datasets, including the original GitHub warning corpus and the 1,027-warning benchmark.
- `02_heuristic/`: cross-version warning matching scripts and heuristic labels.
- `03_llm/`: LLM baseline prompts, runners, and completed DeepSeek/GPT baseline predictions.
- `04_analysis/`: ground truth, paper analysis scripts, RQ1/RQ2 result tables, and figures directory.
- `05_fusion/`: self-contained final fusion method inputs, unified Stage 1 output, prompts, knowledge, schemas, runners, predictions, and fusion analysis.

## Reproduction Order

1. Build or inspect the benchmark data with `01_dataset/scripts/`.
2. Run cross-version matching with `02_heuristic/scripts/` to produce `02_heuristic/results/heuristic_labels_1027.json`.
3. Run LLM baselines from `03_llm/scripts/deepseek/` or `03_llm/scripts/gpt/run_gpt_baseline.py`.
4. Rebuild paper analysis tables with `python 04_analysis/scripts/build_final_paper_sync.py`.
5. Validate fusion material with `python 05_fusion/method/scripts/prepare_fusion_materials.py --preflight`.
6. Validate executable fusion runners with `python 05_fusion/method/scripts/run_deepseek_fusion.py --preflight` and `python 05_fusion/method/scripts/run_gpt_fusion.py --preflight`.
7. Summarize completed fusion runs with `python 05_fusion/analysis/scripts/summarize_fusion_results.py`.

The fusion runners are executable. `--preflight` performs local checks only. `--execute` calls the configured model API and writes local runtime byproducts under ignored runtime directories.

## Included Artifacts

- Included: cppcheck raw warning corpus, processed benchmark files, heuristic labels, LLM baseline predictions, fusion inference input, unified Stage 1 output, fusion prompts/knowledge/schemas, fusion runners, fusion prediction results, ground truth labels, and evaluation tables.
- Not included: upstream project source checkouts, CodeQL raw databases, Clang Static Analyzer raw project inputs, local API caches, logs, checkpoints, and virtual environments.

## Environment

Copy `.env.example` locally if API execution is needed. Do not commit real keys.

Non-Python tooling used by data construction includes Joern/PDG tooling and Tree-sitter style parsing utilities where referenced by context extraction scripts; exact local versions were not recoverable from the artifact and are therefore not pinned here.
