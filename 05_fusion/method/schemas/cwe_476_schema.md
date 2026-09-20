# CWE-476 Reasoning Schema

This schema is used for disagreement-triggered verification of null-dereference style warnings.

Core predicates:
1. `NULL_SOURCE`
   Check whether the warning-relevant object can truly become NULL through:
   - function return
   - initialization
   - allocation result
   - assignment
   - parameter flow
   - visible global state

2. `NULL_PROPAGATION`
   Check whether the nullable state can propagate to the warning-related use:
   - assignment
   - aliasing
   - reassignment
   - fallback replacement

3. `NULL_GUARD`
   Check whether a visible guard really constrains the warning-reaching path:
   - null check
   - early return
   - helper validation
   - fallback assignment

4. `CONTROL_FLOW / PATH_FEASIBILITY`
   Check:
   - branch ordering
   - dominance
   - mutually exclusive paths
   - loop behavior
   - early exits

5. `CALLER_CALLEE_CONSTRAINT`
   If the conclusion depends on caller or callee semantics not visible in the current context, mark that premise `UNRESOLVED`.

6. `DEREFERENCE_REACHABILITY`
   Decide whether there is a concrete reachable path from nullable state to the dereference.

Defect Hypothesis structure:
`NULL_SOURCE -> NULL_PROPAGATION -> NULL_GUARD analysis -> PATH_FEASIBILITY -> DEREFERENCE_REACHABILITY`

Safety Hypothesis structure:
`Safety constraint -> Guard dominance -> Reassignment / fallback -> Caller / callee constraint -> Path blocking`
