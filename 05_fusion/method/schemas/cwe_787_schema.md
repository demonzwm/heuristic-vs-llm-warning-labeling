# CWE-787 Reasoning Schema

This schema is used for disagreement-triggered verification of out-of-bounds / unbounded-write warnings.

Core predicates:
1. `WRITE_OPERATION`
   Identify the warning-critical write or bounds-sensitive use.

2. `DESTINATION_CAPACITY`
   Determine the real destination bound from visible allocation or object size information.
   If the capacity cannot be determined, mark that premise `UNRESOLVED`.

3. `LENGTH_OR_INDEX_RELATION`
   Determine how the copied length / index / offset is produced and whether it remains bounded.

4. `BOUNDS_GUARD`
   Check for:
   - range checks
   - truncation
   - loop bounds
   - validation helpers
   - size constraints

5. `CONTROL_FLOW / PATH_FEASIBILITY`
   Check whether the dangerous length or index can actually reach the write.

6. `ARITHMETIC_RELATION`
   When relevant, examine:
   - off-by-one behavior
   - addition / multiplication
   - terminator handling
   - signed / unsigned relations

7. `WARNING_BOUNDS_CONDITION`
   Decide whether the visible evidence supports a real condition such as:
   - index > valid bound
   - copy length > destination capacity
   - terminator / extra write exceeds the valid extent

Defect Hypothesis structure:
`WRITE_OPERATION -> DESTINATION_CAPACITY -> LENGTH_OR_INDEX_RELATION -> BOUND_VIOLATION -> REACHABILITY`

Safety Hypothesis structure:
`Bounds guard -> Capacity constraint -> Truncation / validation -> Safe reachability`
