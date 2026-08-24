# Security policy

## Supported versions

Security fixes are developed for the current minor release line. Older release assets remain immutable evidence and may not receive backports.

## Private reporting

Report suspected vulnerabilities through GitHub private security advisories. Do not disclose secrets, exploit details, private repositories, customer data, or production reports in a public issue.

A useful report contains:

- affected version and commit;
- operating system and Codex CLI version;
- minimal sanitized fixture;
- exact command and observed result;
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
10. generated reports redact no secrets automatically and therefore must be reviewed before sharing.

## Out of scope

The project does not claim to secure an already compromised host, malicious Python interpreter, malicious Git binary, compromised dependency source, or owner-approved arbitrary command. A checksum confirms the exact configured argv, not that the selected executable is benign.

## Release verification

Tagged releases are intended to be built by `.github/workflows/release.yml`, accompanied by SHA-256 checksums, an SPDX source SBOM, and GitHub artifact provenance. Release immutability and branch protection are repository settings and must also be enabled by the owner.
