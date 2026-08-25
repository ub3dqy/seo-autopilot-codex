## Scope

Describe one coherent change and the user-visible outcome.

## Evidence

- [ ] Primary source or policy rule is linked where applicable.
- [ ] Findings and fixtures identify exact paths and expected behavior.
- [ ] No secrets or private site data are included.

## Safety

- [ ] Risk level is unchanged or explicitly justified.
- [ ] No B/C change was converted to automatic application by model judgement.
- [ ] Commands use argv arrays and no shell interpolation.
- [ ] Transaction, rollback, budgets and dirty-tree behavior were considered.

## Local verification

- [ ] `python scripts/verify_local.py` completed successfully.
- [ ] Candidate commit/tree and platform/Python versions are recorded.
- [ ] Test count, artifact names and SHA-256 are recorded.
- [ ] Second application is idempotent when mutation is involved.
- [ ] `.github/workflows/` contains no active `.yml` or `.yaml` files.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```
