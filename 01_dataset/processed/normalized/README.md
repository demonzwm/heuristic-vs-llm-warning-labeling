# Normalized

This directory stores normalized references and processed intermediate artifacts
used by the final three-tool dataset pipeline.

## Final Pipeline View

CodeQL and CSA originated from the initial warning collection, while Cppcheck
was processed separately and integrated later.

## Files

- `merged_codeql_C_report.xlsx`
  CodeQL CWE-reference workbook used during supplementation.

- `csa_merged_cwe.xlsx`
  CSA CWE-reference workbook used during supplementation.

- `merged_cppcheck_report.xlsx`
  Cppcheck CWE-reference workbook used during supplementation.

- `cppcheck/`
  Processed Cppcheck intermediate artifacts retained as part of the final
  construction lineage.

No cross-tool merged normalized file is forced here, because the three-tool
field alignment was not promoted to a single final normalized artifact.
