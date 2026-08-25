# Contributing

This repository is publicly readable but remains proprietary under `LICENSE.md`; it is not presented as an open-source project. Opening an issue or pull request does not grant redistribution, sublicensing or commercial rights.

## Before proposing a change

Use a sanitized fixture and identify:

- the concrete user problem;
- the authoritative primary source;
- the expected risk level;
- deterministic evidence;
- failure and rollback behavior;
- the exact acceptance test.

Do not submit credentials, private site content, customer information, generated production reports or copied proprietary datasets.

## Mandatory local gate

```bash
python scripts/verify_local.py
```

The detailed equivalent includes compilation, unit tests, source verification, secret scan, two deterministic package builds and release verification. The wrapper is the authoritative command and must remain reproducible from a clean checkout.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

Do not add required checks, badges, release steps or documentation that depend on GitHub Actions. A change is not accepted merely because a hosted status exists; its evidence must be produced by the local verification runner and committed or attached in sanitized form.

Mutation-related changes must also prove:

- the owner's working tree remains untouched;
- Git hooks cannot run;
- no shell interpolation is used;
- budgets are enforced before writes;
- failed validation rolls back;
- the second run produces no repeat fix;
- B/C risks are never downgraded to A by model judgement.

## Policy changes

SEO policies are versioned. Do not silently rewrite an old policy pack. Add a new dated pack, record the primary source and verification date, update fixtures and describe behavior changes in `CHANGELOG.md`.

## Pull requests

Keep each pull request coherent and reviewable. Include the exact local command, Python/platform versions, exit status, test count, artifact SHA-256 and any `NOT_RUN` external/live checks. Local verification is necessary but not sufficient; safety, evidence quality, licensing and public claims remain owner decisions.
