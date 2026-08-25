# Support

## Start with local evidence

Run:

```bash
python scripts/verify_local.py
seo-autopilot doctor . --json
seo-autopilot audit .
```

Attach only sanitized output. The most useful evidence is the product version, source commit, local verification exit status, test count, artifact SHA-256, `run.json`, validator statuses, detected stack and a minimal fixture without private data.

## Hosted CI status

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

Do not report a red Actions badge as a product test failure and do not rerun hosted workflows. Reproduce the issue through `scripts/verify_local.py` or the relevant local command.

## Public issues

Use a public issue for reproducible bugs and feature requests that contain no secrets, vulnerabilities, private repositories, customer content or production identifiers.

## Security reports

Use a private GitHub security advisory for prompt-injection escapes, command execution, path traversal, sandbox or transaction bypass, secret exposure, unsafe rollback or release-integrity issues.

## Unsupported expectations

SEO Autopilot does not provide a ranking guarantee, indexing guarantee, rich-result guarantee, production deployment service, Search Console account access, backlink database, keyword database or legal/compliance review. External evidence remains unavailable until the owner separately configures and authorizes the relevant provider.
