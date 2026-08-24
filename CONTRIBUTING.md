# Contributing

This repository is publicly readable but remains proprietary under `LICENSE.md`; it is not presented as an open-source project. Opening an issue or pull request does not grant redistribution, sublicensing, or commercial rights.

## Before proposing a change

Use a sanitized fixture and identify:

- the concrete user problem;
- the authoritative primary source;
- the expected risk level;
- deterministic evidence;
- failure and rollback behavior;
- the exact acceptance test.

Do not submit credentials, private site content, customer information, generated production reports, or copied proprietary datasets.

## Development gate

```bash
python -m pip install --no-deps -e .
python -m compileall -q src scripts tests prepare_editions.py
python -m unittest discover -s tests -v
python prepare_editions.py --verify-only
python scripts/secret_scan.py
```

Mutation-related changes must also prove:

- owner working tree remains untouched;
- Git hooks cannot run;
- no shell interpolation is used;
- budgets are enforced before writes;
- failed validation rolls back;
- the second run produces no repeat fix;
- B/C risks are never downgraded to A by model judgement.

## Policy changes

SEO policies are versioned. Do not silently rewrite an old policy pack. Add a new dated pack, record the primary source and verification date, update fixtures, and describe behavior changes in `CHANGELOG.md`.

## Pull requests

Keep each pull request coherent and reviewable. A maintainer may squash commits when merging. Passing automation is necessary but not sufficient; safety, evidence quality, licensing, and public claims remain owner decisions.
