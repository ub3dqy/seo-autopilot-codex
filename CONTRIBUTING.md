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

GitHub Actions is not used. Run the tracked local gate:

### Windows

```text
VERIFY_LOCAL_WINDOWS.cmd
```

### macOS / Linux

```bash
./verify_local.sh
```

Direct equivalent:

```bash
python scripts/verify_local.py
```

Attach or retain `local-verification/latest.json` for the exact commit under review. Never claim another operating system passed unless the same commit was actually checked there.

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

Keep each pull request coherent and reviewable. A maintainer may squash commits when merging. A local PASS is necessary but not sufficient; safety, evidence quality, licensing, and public claims remain owner decisions.
