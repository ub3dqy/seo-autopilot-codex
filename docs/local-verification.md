# Local verification without GitHub Actions

GitHub Actions is intentionally not a dependency of this repository. Acceptance and release evidence is produced on the machine that actually executes the checks.

## One-command gates

Deterministic development gate:

```bash
python scripts/verify_local.py
```

Build both editions and verify release assets:

```bash
python scripts/verify_local.py --build
```

Official release gate from a clean Git checkout:

```bash
python scripts/verify_local.py --release
```

Optional real Codex canary:

```bash
python scripts/verify_local.py --live
```

Require a live PASS rather than accepting `NOT_RUN`:

```bash
python scripts/verify_local.py --live --require-live
```

## Evidence

Every invocation writes timestamped and stable aliases:

```text
local-verification/verification-<UTC>.json
local-verification/verification-<UTC>.log
local-verification/latest.json
local-verification/latest.log
```

The JSON report records:

- exact Git commit and branch when available;
- whether the working tree was dirty;
- operating system and Python runtime;
- exact argv for every subprocess;
- accepted and actual return codes;
- duration and status of every step;
- SHA-256 of redacted stdout and stderr;
- release artifact names, hashes and sizes in build/release mode.

The log contains redacted command output. Both directories are ignored by Git to avoid accidental publication of local evidence.

## Platform claims

A PASS proves only the environment recorded in that report. To claim support for several platforms, run the same commit separately on each platform and retain every report. Never infer Windows or macOS success from a Linux run.

## Failure handling

The harness stops official release work when the Git tree is dirty, but continues deterministic steps long enough to produce useful evidence where safe. A failed step makes the final status `FAIL`. Do not weaken the gate to turn a failure green; fix the cause and run the same command again.

## No remote mutation

The verification harness does not push, merge, create releases, deploy, or change repository settings. Publication remains a separate owner decision after reviewing local evidence.
