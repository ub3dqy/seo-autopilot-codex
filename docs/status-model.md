# Status model

- `READY` — all mandatory preconditions are satisfied.
- `READY_WITH_LIMITATIONS` — deterministic work can continue, but optional capability such as Codex CLI or a framework adapter is absent.
- `REVIEW_REQUIRED` — evidence exists that needs an owner decision, or fix mode is blocked by a dirty worktree.
- `BLOCKED` — a mandatory prerequisite is absent.
- `PASSED` — the requested deterministic scope completed and no open finding remains in that scope.
- `FAILED` — execution or validation failed.
- `NOT_RUN` — an explicitly separate live or external evidence check did not execute.

`NOT_RUN`, `READY_WITH_LIMITATIONS`, and `REVIEW_REQUIRED` must never be summarized as PASS.
