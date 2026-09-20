# Static-Analysis Warning Labeling Knowledge

This directory contains CWE-specific knowledge specifications for LLM-assisted validation of static-analysis warnings.

## Purpose

These files are designed to help an LLM decide whether a reported warning is a real defect path or a false positive in the given code context.

The knowledge is intentionally not a vulnerability encyclopedia. Each file focuses on:

- what code evidence supports a real defect path
- what code evidence weakens the warning or explains it away
- which reachability, data-flow, control-flow, API-contract, and project-context questions matter

## File Structure

- `CWE-119.md`
- `CWE-120.md`
- `CWE-121.md`
- `CWE-122.md`
- `CWE-125.md`
- `CWE-126.md`
- `CWE-131.md`
- `CWE-193.md`
- `CWE-251.md`
- `CWE-416.md`
- `CWE-476.md`
- `CWE-676.md`
- `CWE-787.md`
- `CWE-805.md`

Each file follows the same sections:

1. Weakness Characteristics
2. Expected Secure Behavior
3. Evidence Supporting TP
4. Evidence Supporting FP
5. Important Analysis Questions
6. Common Misleading Patterns
7. Required Context for Reliable Judgment

## Generation Basis

These knowledge files were generated for the CWEs that actually appear in `05_fusion/method/data/fusion_input_1027.json`.

Observed CWE set in the current dataset:

- `CWE-119`
- `CWE-120`
- `CWE-121`
- `CWE-122`
- `CWE-125`
- `CWE-126`
- `CWE-131`
- `CWE-193`
- `CWE-251`
- `CWE-416`
- `CWE-476`
- `CWE-676`
- `CWE-787`
- `CWE-805`

The content was written by combining:

- MITRE CWE official weakness descriptions and related explanatory material
- the warning-validation task definition used in this fusion experiment
- neutral code-analysis rules centered on path feasibility, data flow, control flow, API semantics, and project constraints

These files have also been refined to:

- emphasize evidence-based warning validation
- avoid CWE-based label bias
- provide security specifications rather than final labels

## How To Use In Prompts

Inject the relevant `CWE-XXX.md` content as auxiliary Stage 1 CWE knowledge when a warning includes that CWE.

Recommended usage pattern:

- provide the warning, sliced code, caller/callee context, and any evolution evidence
- attach the matching CWE knowledge file(s)
- instruct the model to use the knowledge as analysis criteria, not as a label prior

Suggested prompt role for this knowledge:

`Use the following CWE-specific warning labeling specification to determine what evidence must be checked before deciding TP or FP. Do not infer the final label from the CWE itself.`

## Scope Notes

- These files do not encode dataset statistics as label priors.
- They do not recommend TP or FP by CWE.
- They are intended to support reasoning, not replace manual validation.
- They are refined for warning-validation use rather than CWE explanation or final-label prediction.
- `CWE-251` is a category-level entry in MITRE; here it is treated as a warning-validation guide for string-management misuse patterns that appear in this dataset.
