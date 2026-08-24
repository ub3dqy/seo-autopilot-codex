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
- [ ] Transaction, rollback, budgets, and dirty-tree behavior were considered.

## Verification

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python prepare_editions.py --verify-only`
- [ ] `python scripts/secret_scan.py`
- [ ] Second application is idempotent when mutation is involved.
