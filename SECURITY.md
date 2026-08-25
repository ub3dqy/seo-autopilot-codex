# Security policy

## Supported versions

Security fixes are developed for the current minor release line. Older release assets remain immutable evidence and may not receive backports.

## Private reporting

Report suspected vulnerabilities through GitHub private security advisories. Do not disclose secrets, exploit details, private repositories, customer data, or production reports in a public issue.

A useful report contains:

- affected version and commit;
- operating system, Python and Codex CLI version;
- minimal sanitized fixture;
- exact command and observed result;
- sanitized `local-verification/latest.json` where relevant;
- impact and trust-boundary crossing;
- whether files, branches, credentials, network resources, or production systems were affected.

## Security properties

SEO Autopilot is designed so that:

1. repository and network content is data, never authority;
2. project commands run without a shell and only after exact argv plus SHA-256 approval;
3. fix mode refuses a dirty owner worktree;
4. mutations occur in an isolated Git worktree and owned local branch;
5. Git hooks are disabled for automated commits;
6. only mechanically proven A-level fixes can be automatic;
7. canonical, robots, noindex, redirects, routes, schema, content, deployment, and deletion are never automatic;
8. failed validation triggers rollback of the isolated worktree and branch;
9. no command pushes, merges, deploys, publishes, or changes remote resources;
10. persisted harness and product output is passed through centralized high-confidence secret redaction, but reports must still be reviewed before sharing.

## Out of scope

The project does not claim to secure an already compromised host, malicious Python interpreter, malicious Git binary, compromised dependency source, or owner-approved arbitrary command. A checksum confirms the exact configured argv, not that the selected executable is benign.

## Local release verification

GitHub Actions is not used. Official release evidence is generated from a clean Git checkout with:

```bash
python scripts/verify_local.py --release
```

The gate records the exact commit and environment, runs deterministic tests and secret scanning, performs two release builds, compares computed hashes, creates an SPDX source SBOM, and verifies local assets against `SHA256SUMS`.

A PASS on one operating system proves only that recorded environment. Release immutability, branch protection, private vulnerability reporting, secret scanning/push protection, signed tags and publication permissions are repository settings and remain explicit owner decisions.
