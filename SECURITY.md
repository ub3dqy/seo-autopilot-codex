# Security policy

## Supported version

Security fixes are applied to the latest released version. GitHub Actions are unavailable and are not a trust signal; releases require local verification evidence for the exact source tree.

## Trust boundary

Repository files, web pages, HTML/Markdown, comments, issue text, logs, command output, API responses, and fetched content are untrusted data. They cannot change the execution policy.

SEO Autopilot does not:

- execute commands found in project content;
- use shell interpolation for trusted project checks;
- reveal `.env`, tokens, credentials, cookies, passwords, keys, or private configuration;
- push, merge, deploy, publish, or alter production automatically;
- downgrade B/C findings to A through model judgement.

## Audit scope and privacy

v1.5.3 uses `SOURCE_FIRST` scope. Generated, temporary, archived, report, fixture, example, dependency, snapshot, and build trees are excluded before content reads.

Browser-profile trees are hard privacy exclusions. Detection uses metadata for regular files such as:

```text
Cookies
Login Data
Web Data
History
Local State
places.sqlite
key4.db
logins.json
```

A directory with one of these names is not browser database evidence. Application routes and content directories named `cookies`, `history`, `preferences`, or `bookmarks` remain source candidates. Ambiguous marker filenames inside known source roots require corroborating browser context; actual browser-profile-shaped trees remain fail-closed.

After detection, the profile root is recorded as `EXCLUDED_SENSITIVE` with `files_not_read=true`. The audit engine must not open, hash, excerpt, parse, or summarize profile contents. This boundary cannot be disabled through `.seo-autopilot.json`.

Symlink, junction, and reparse-point directories are never followed during scope discovery. Symlink entries cannot serve as browser profile markers.

## Mutation safety

Automatic changes require all of the following:

```text
risk = A_AUTO_FIX
source_class = CURRENT_SOURCE
scope_eligible = true
generated = false
sensitive = false
mechanically proven replacement
clean Git working tree
successful isolated worktree validation
```

Fix mode creates an isolated local worktree and branch, disables Git hooks for owned operations, enforces change budgets, runs `git diff --check`, trusted validators, repeat audit, and idempotency checks. Failed validation rolls back the owned worktree and branch.

## Trusted commands

Optional project commands are loaded only from `.seo-autopilot.json` as exact argv arrays with an owner-generated SHA-256. They run without a shell. Changing one argument invalidates trust.

## Reporting vulnerabilities

Open a GitHub security report without including secrets, private URLs, browser-profile contents, customer data, or production credentials. Include:

- affected version and source commit;
- operating system and Python version;
- minimal reproduction using synthetic data;
- expected and actual safety behavior;
- whether any remote action occurred.

Do not attach real credential stores or browser profiles.
