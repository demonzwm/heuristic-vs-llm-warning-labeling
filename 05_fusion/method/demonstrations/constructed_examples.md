# Constructed demonstrations

These five examples are synthetic and do not come from the 1,027-warning evaluation set.

## Constructed case 1
Input JSON:
```json
{
  "warning": {
    "warning_id": "synthetic-1",
    "cwe": [
      "CWE-476"
    ],
    "message": "Possible null dereference of p",
    "sliced_code": "#include <stddef.h>\nstruct Item { int value; };\nint read_value(struct Item *p) {\n    if (p == NULL) return -1;\n    return p->value; // reported dereference\n}"
  },
  "stage1_output": {
    "initial_semantic_prediction": "TP",
    "semantic_confidence": "Medium",
    "supporting_reasoning": "p is a pointer parameter and may be NULL at the dereference.",
    "uncertainty": "Guard coverage was not established."
  },
  "structured_warning_evolution": {
    "observation": "matched",
    "matched": true,
    "matching_method": "location match",
    "matched_version": "later release",
    "matched_child_warning": "same rule near same location",
    "later_versions_checked": [
      "later release"
    ],
    "sca_reports_checked": [
      "later release report"
    ]
  },
  "cwe_reasoning_schema": {
    "name": "CWE-476",
    "schema": "Use the supplied schema for the actual warning."
  }
}
```
Output JSON:
```json
{
  "initial_semantic_prediction": "TP",
  "cwe_reasoning_schema": "CWE-476",
  "defect_hypothesis": "p is NULL when p->value is evaluated.",
  "defect_required_premises": [
    "p can be NULL",
    "the null path reaches p->value"
  ],
  "defect_structured_verification": "The first premise is possible, but the null branch returns before the use. No reassignment or alternate path is shown.",
  "defect_hypothesis_status": "REFUTED",
  "safety_hypothesis": "The return on p == NULL blocks every visible path to the dereference.",
  "safety_required_premises": [
    "the null check dominates the use",
    "p is not changed after the check"
  ],
  "safety_structured_verification": "Both conditions hold in the complete visible function.",
  "safety_hypothesis_status": "SUPPORTED",
  "evolution_evidence_reliability": "MEDIUM",
  "evolution_analysis": "A later release report and a same-rule nearby candidate are named, giving a traceable but only partly specified match (MEDIUM). Its exact file and location correspondence remains unverified. The historical match does not defeat the dominating guard.",
  "cross_evidence_resolution": "The reported null dereference is unreachable on the null path.",
  "final_reasoning": "The reported null dereference is unreachable on the null path.",
  "final_label": "FP"
}
```

## Constructed case 2
Input JSON:
```json
{
  "warning": {
    "warning_id": "synthetic-2",
    "cwe": [
      "CWE-787"
    ],
    "message": "Possible out-of-bounds write to buf",
    "sliced_code": "#include <stddef.h>\n#include <string.h>\nvoid consume(const char *s); // external observer\nvoid copy8(const char *src, size_t n) {\n    char buf[8]; // valid indices: 0..7\n    if (n > 8) return;\n    memcpy(buf, src, n);\n    buf[n] = '\\0'; // reported write; n == 8 reaches here\n    consume(buf);\n}"
  },
  "stage1_output": {
    "initial_semantic_prediction": "FP",
    "semantic_confidence": "Medium",
    "supporting_reasoning": "n is capped at 8, matching the destination capacity.",
    "uncertainty": "The terminator write was not checked separately."
  },
  "structured_warning_evolution": {
    "observation": "checked_no_match",
    "matched": false,
    "matching_method": "unavailable",
    "matched_version": "unavailable",
    "matched_child_warning": "unavailable",
    "later_versions_checked": [
      "later release"
    ],
    "sca_reports_checked": [
      "later release report"
    ]
  },
  "cwe_reasoning_schema": {
    "name": "CWE-787",
    "schema": "Use the supplied schema for the actual warning."
  }
}
```
Output JSON:
```json
{
  "initial_semantic_prediction": "FP",
  "cwe_reasoning_schema": "CWE-787",
  "defect_hypothesis": "n can equal 8, so buf[n] writes to buf[8], outside the eight-byte array.",
  "defect_required_premises": [
    "n == 8 reaches the write",
    "buf has only indices 0..7"
  ],
  "defect_structured_verification": "The guard rejects only n > 8. For n == 8, memcpy fills buf[0..7] and the terminator write targets buf[8].",
  "defect_hypothesis_status": "SUPPORTED",
  "safety_hypothesis": "The n <= 8 guard bounds all writes to buf.",
  "safety_required_premises": [
    "the guard also reserves one byte for the terminator"
  ],
  "safety_structured_verification": "The guard permits n == 8 and does not reserve a terminator byte.",
  "safety_hypothesis_status": "REFUTED",
  "evolution_evidence_reliability": "LOW",
  "evolution_analysis": "A later release report was checked, but its coverage and match search details are not given (LOW). No match therefore does not establish that the original defect was repaired or absent.",
  "cross_evidence_resolution": "A concrete reachable n == 8 path writes at invalid index 8.",
  "final_reasoning": "A concrete reachable n == 8 path writes at invalid index 8.",
  "final_label": "TP"
}
```

## Constructed case 3
Input JSON:
```json
{
  "warning": {
    "warning_id": "synthetic-3",
    "cwe": [
      "CWE-476"
    ],
    "message": "Possible null dereference after allocation",
    "sliced_code": "#include <stdlib.h>\nstruct Item { int value; };\nint make_value(void) {\n    struct Item *p = malloc(sizeof *p);\n    p->value = 1; // reported dereference\n    return p->value;\n}"
  },
  "stage1_output": {
    "initial_semantic_prediction": "TP",
    "semantic_confidence": "Medium",
    "supporting_reasoning": "malloc may return NULL and p is dereferenced without a check.",
    "uncertainty": "No allocation guarantee is visible."
  },
  "structured_warning_evolution": {
    "observation": "no_match_with_incomplete_check_record",
    "matched": false,
    "matching_method": "unavailable",
    "matched_version": "unavailable",
    "matched_child_warning": "unavailable",
    "later_versions_checked": "unavailable",
    "sca_reports_checked": "unavailable"
  },
  "cwe_reasoning_schema": {
    "name": "CWE-476",
    "schema": "Use the supplied schema for the actual warning."
  }
}
```
Output JSON:
```json
{
  "initial_semantic_prediction": "TP",
  "cwe_reasoning_schema": "CWE-476",
  "defect_hypothesis": "Allocation can fail and the null result reaches p->value.",
  "defect_required_premises": [
    "malloc can return NULL",
    "there is no intervening guard or fallback"
  ],
  "defect_structured_verification": "Both premises hold in the visible function; the assignment dereferences p immediately.",
  "defect_hypothesis_status": "SUPPORTED",
  "safety_hypothesis": "A visible check or fallback prevents use of a null allocation result.",
  "safety_required_premises": [
    "a check or replacement occurs before p->value"
  ],
  "safety_structured_verification": "No such check or replacement is present.",
  "safety_hypothesis_status": "REFUTED",
  "evolution_evidence_reliability": "UNAVAILABLE",
  "evolution_analysis": "No usable later report or check trace is provided (UNAVAILABLE). The bare no-match flag cannot resolve the current code path.",
  "cross_evidence_resolution": "The initial TP remains supported by a concrete allocation-failure path.",
  "final_reasoning": "The initial TP remains supported by a concrete allocation-failure path.",
  "final_label": "TP"
}
```

## Constructed case 4
Input JSON:
```json
{
  "warning": {
    "warning_id": "synthetic-4",
    "cwe": [
      "CWE-787"
    ],
    "message": "Possible write beyond dst",
    "sliced_code": "void put(char *dst, size_t dst_size, size_t n) {\n    if (n >= dst_size) return;\n    dst[n] = 'X'; // reported write\n}"
  },
  "stage1_output": {
    "initial_semantic_prediction": "FP",
    "semantic_confidence": "Low",
    "supporting_reasoning": "The index is checked against dst_size before writing.",
    "uncertainty": "The slice does not show whether dst_size reflects the actual allocation."
  },
  "structured_warning_evolution": {
    "observation": "match_unavailable",
    "matched": "unavailable",
    "matching_method": "unavailable",
    "matched_version": "unavailable",
    "matched_child_warning": "unavailable",
    "later_versions_checked": "unavailable",
    "sca_reports_checked": "unavailable"
  },
  "cwe_reasoning_schema": {
    "name": "CWE-787",
    "schema": "Use the supplied schema for the actual warning."
  }
}
```
Output JSON:
```json
{
  "initial_semantic_prediction": "FP",
  "cwe_reasoning_schema": "CWE-787",
  "defect_hypothesis": "dst_size may exceed the actual allocation, allowing n inside the stated bound but outside dst.",
  "defect_required_premises": [
    "a caller can pass an overstated dst_size",
    "such an n reaches the write"
  ],
  "defect_structured_verification": "The slice omits callers and allocation size, so the overstated-size premise cannot be established or excluded.",
  "defect_hypothesis_status": "UNRESOLVED",
  "safety_hypothesis": "dst_size equals the actual writable capacity, so n < dst_size protects dst[n].",
  "safety_required_premises": [
    "caller supplies the actual capacity",
    "dst points to that writable object"
  ],
  "safety_structured_verification": "The local comparison is visible, but the capacity and caller contract are not.",
  "safety_hypothesis_status": "UNRESOLVED",
  "evolution_evidence_reliability": "UNAVAILABLE",
  "evolution_analysis": "Matching and later-report data are unavailable (UNAVAILABLE); no historical conclusion follows.",
  "cross_evidence_resolution": "Neither a concrete violation nor an affirmed safety guarantee is established. Retain the initial FP as a binary fallback, not as proof of safety.",
  "final_reasoning": "Neither a concrete violation nor an affirmed safety guarantee is established. Retain the initial FP as a binary fallback, not as proof of safety.",
  "final_label": "FP"
}
```

## Constructed case 5
Input JSON:
```json
{
  "warning": {
    "warning_id": "synthetic-5",
    "cwe": [
      "CWE-787"
    ],
    "message": "Possible out-of-bounds write to buf",
    "sliced_code": "#include <stddef.h>\nvoid consume(const char *p, size_t n); // external observer\nvoid write_char(size_t n) {\n    char buf[8]; // valid indices: 0..7\n    if (n >= sizeof buf) return;\n    buf[n] = 'X'; // reported write\n    consume(buf, sizeof buf);\n}"
  },
  "stage1_output": {
    "initial_semantic_prediction": "FP",
    "semantic_confidence": "High",
    "supporting_reasoning": "The return excludes n >= 8 before the indexed write.",
    "uncertainty": "None in the visible path."
  },
  "structured_warning_evolution": {
    "observation": "matched",
    "matched": true,
    "matching_method": "location match",
    "matched_version": "later release",
    "matched_child_warning": "same rule near same location",
    "later_versions_checked": [
      "later release"
    ],
    "sca_reports_checked": [
      "later release report"
    ]
  },
  "cwe_reasoning_schema": {
    "name": "CWE-787",
    "schema": "Use the supplied schema for the actual warning."
  }
}
```
Output JSON:
```json
{
  "initial_semantic_prediction": "FP",
  "cwe_reasoning_schema": "CWE-787",
  "defect_hypothesis": "n reaches buf[n] with a value outside 0..7.",
  "defect_required_premises": [
    "n >= 8 reaches the write"
  ],
  "defect_structured_verification": "n >= sizeof buf returns, and sizeof buf is 8. Values reaching the write are 0..7.",
  "defect_hypothesis_status": "REFUTED",
  "safety_hypothesis": "The guard uses the actual local array size and dominates the only reported write.",
  "safety_required_premises": [
    "buf is an eight-byte local array",
    "the guard dominates buf[n]"
  ],
  "safety_structured_verification": "Both conditions are explicit in the visible function.",
  "safety_hypothesis_status": "SUPPORTED",
  "evolution_evidence_reliability": "MEDIUM",
  "evolution_analysis": "A later release report and a same-rule nearby candidate are named, giving a traceable but only partly specified match (MEDIUM). Exact correspondence remains unverified, and the match does not overturn the code-level bound proof.",
  "cross_evidence_resolution": "The initial FP is retained because the visible guard excludes every invalid index at the reported write.",
  "final_reasoning": "The initial FP is retained because the visible guard excludes every invalid index at the reported write.",
  "final_label": "FP"
}
```
