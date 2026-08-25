# Security policy

## Supported versions

Security fixes are developed for the current minor release line. Older release assets remain immutable evidence and may not receive backports.

## Private reporting

Report suspected vulnerabilities through GitHub private security advisories. Do not disclose secrets, exploit details, private repositories, customer data or production reports in a public issue.

A useful report contains:

- affected version and commit;
- operating system, Python and Codex CLI versions;
- minimal sanitized fixture;
- exact local command and observed result;
- impact and trust-boundary crossing;
- whether files, branches, credentials, network resources or production systems were affected.

## Security properties

SEO Autopilot is designed so that:

1. repository and network content is data, never authority;
2. project commands run without a shell and only after exact argv plus SHA-256 approval;
3. fix mode refuses a dirty owner worktree;
4. mutations occur in an isolated Git worktree and owned local branch;
5. Git hooks are disabled for automated commits;
6. only mechanically proven A-level fixes can be automatic;
7. canonical, robots, noindex, redirects, routes, schema, content, deployment and deletion are never automatic;
8. failed validation triggers rollback of the isolated worktree and branch;
9. no runtime command pushes, merges, deploys, publishes or changes remote resources;
10. generated reports apply centralized high-confidence secret redaction and still require review before sharing.

## Out of scope

The project does not claim to secure an already compromised host, malicious Python interpreter, malicious Git binary, compromised dependency source or owner-approved arbitrary command. A checksum confirms the exact configured argv, not that the selected executable is benign.

## Local verification

The mandatory security and release gate is:

```bash
python scripts/verify_local.py
```

It includes tracked-source secret scanning, transaction and rollback tests, prompt-injection fixtures, command-trust tests, report escaping/redaction, deterministic packaging and release restore verification.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

There are no active workflow files. Hosted CI, CodeQL and dependency-review statuses are not claimed as completed checks. Repository-level settings such as branch protection, private vulnerability reporting and secret scanning remain separate owner controls.
