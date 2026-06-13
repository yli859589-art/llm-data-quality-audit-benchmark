# Level 3 Readiness Gates

The Level 3 gates are implemented in `src/readiness_v2/gates.py`.

## Gate Summary

| Gate | Current Expected Status | Meaning |
|---|---|---|
| DataGate | `not_ready` | No verified 500M-token Level 3 data matrix exists. |
| TokenizerGate | `partial` | Smoke BPE exists, but mainline GPT-2/BPE32k evidence is not completed. |
| FilterGate | `partial` | Filter interfaces and smoke artifacts exist, but the full heavy matrix is not completed. |
| ModelScaleGate | `partial` | Tiny smoke training exists; medium and selected large-lite runs are not completed. |
| EvaluationGate | `partial` | Evaluation framework exists; official downstream/full matrix evidence is not completed. |
| MechanismGate | `partial` | Mechanism framework exists; full-scale mechanism evidence is not completed. |
| ClaimGate | `pass` | Current promotional claims are blocked or bounded. |

Gate failures for heavy evidence are expected in Step 9. They are not Step 9
failures. Step 9 fails only if the gate system cannot detect the missing heavy
evidence or if unsafe claims pass.

Step 10A-hotfix adds reproducibility checks around the gate artifacts. The
artifact scanner must classify paths relative to the repository root, so a
parent directory name containing `step1` or `step10a` cannot change gate or
registry classification.

## State Boundary

`LEVEL3_PIPELINE_READY` is the maximum current state.  
`LEVEL3_COMPLETED_ARTIFACT` is forbidden until Step 10B/10C real heavy execution
is complete.

Registry finalization must occur after report generation. If the final registry
hash check fails, the readiness report must not be treated as a clean completed
protocol-freeze state.
