# Status model

SEO Autopilot uses explicit states rather than a single ambiguous PASS/FAIL label.

| Status | Meaning |
|---|---|
| `READY` | Preconditions for the requested operation are satisfied. |
| `READY_WITH_LIMITATIONS` | Work can continue, but declared evidence or adapter coverage is unavailable. |
| `REVIEW_REQUIRED` | Read-only audit completed or the project is usable, but human review or a clean mutation baseline is required. This is **not** a technical failure. |
| `BLOCKED` | A mandatory safety or integrity precondition prevents the requested operation. |
| `PASSED` | The requested deterministic operation and its validators completed successfully. |
| `FAILED` | An attempted operation or validator failed. |
| `NOT_RUN` | The operation was not attempted. |

Scope exclusions are recorded separately:

| Scope status | Meaning |
|---|---|
| `EXCLUDED_BY_SCOPE` | Generated, temporary, archive, report, fixture, example, dependency, build, or owner-excluded tree was not audited as production source. |
| `EXCLUDED_SENSITIVE` | Browser-profile or credential-adjacent tree was identified from metadata and excluded before content reads. |

Missing external evidence should be described as `DEFERRED` or `NOT_RUN`, not estimated. A dirty Git tree normally produces `REVIEW_REQUIRED`: audit remains available, while `fix` stays blocked.
