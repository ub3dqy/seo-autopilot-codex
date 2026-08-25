# Local verification

## Authority

The project is released only through the reproducible local gate:

```bash
python scripts/verify_local.py
```

Windows:

```text
VERIFY_LOCAL_WINDOWS.cmd
```

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

Hosted workflow state is not evidence for this project. The final source tree must contain no active `.github/workflows/*.yml` or `.yaml` files.

## Preconditions

- clean checkout of the exact candidate commit;
- Python 3.10 or newer;
- Git available for transaction tests;
- no production credentials or private fixtures in the checkout;
- enough local disk space for two independent edition builds.

The deterministic gate must not require network access, an OpenAI API key or GitHub Actions.

## Mandatory phases

The runner performs and records:

1. environment and source commit discovery;
2. Python compilation and import checks;
3. complete `unittest` discovery;
4. transaction isolation, hook suppression and rollback tests;
5. A/B/C risk-floor and prompt-injection tests;
6. idempotency and budget enforcement;
7. report escaping, redaction and `run.json` schema checks;
8. tracked-source secret scan;
9. source/release-manifest verification;
10. clean User Edition installation test without modifying the checkout;
11. deterministic build A;
12. deterministic build B;
13. byte/hash comparison of both builds;
14. ZIP structure, CRC, traversal, duplicate-entry and link checks;
15. restoration of any split transport parts and SHA-256 comparison;
16. final machine-readable and human-readable evidence output.

A non-zero exit code blocks the release. Partial PASS results do not compensate for a failed phase.

## Evidence to preserve

Record at minimum:

- candidate commit and Git tree;
- platform and Python version;
- command line and exit code;
- discovered/passed/skipped test count;
- every gate status;
- User and Engineering artifact names, byte sizes and SHA-256;
- release manifest/build report SHA-256;
- live Codex canary status (`PASSED`, `FAILED` or `NOT_RUN`);
- confirmation that no active GitHub workflow files exist.

Sanitize the report before publication. Do not include credentials, private paths, customer content or complete production reports.

## Reproduction

From a clean checkout of the recorded commit:

```bash
python scripts/verify_local.py
```

The runner must produce the same artifact SHA-256 on repeated builds. A tree/commit change invalidates the previous verification and requires a full rerun.

## Release boundary

The local gate validates source and local artifacts. It does not prove post-deployment indexing, rankings, traffic, rich results, Core Web Vitals, Search Console state or production configuration. Those remain separately measured external evidence.
