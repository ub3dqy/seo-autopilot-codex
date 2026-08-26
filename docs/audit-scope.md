# Audit scope and privacy boundary

SEO Autopilot v1.5.2 uses `SOURCE_FIRST` scope. It does not recursively treat every HTML file inside a workspace as a production page.

## Default candidate model

In a Git repository, the audit evaluates relevant tracked source files. Untracked files are considered only when they are root-level website files or are inside known source roots such as `src/`, `app/`, `pages/`, `public/`, `static/`, `content/`, `components/`, `widgets/`, `scripts/`, `lib/`, `server/`, or `client/`.

Outside Git, the same known roots and root-level website files are used. Arbitrary workspace trees are not scanned.

## Generated and non-production exclusions

Generated, archived, temporary, report, snapshot, fixture, example, dependency, and build trees are excluded before file content is read. Typical examples include:

```text
artifacts/ tmp/ temp/ .cache/ .next/ .nuxt/ .output/
dist/ build/ coverage/ playwright-report/ test-results/
reports/ logs/ snapshots/ backups/ archives/ tests/ fixtures/ examples/
```

## Hard privacy exclusions

Directory metadata is inspected for browser-profile markers such as `Cookies`, `Login Data`, `Web Data`, `History`, `Local State`, `places.sqlite`, `key4.db`, and `logins.json`. Once a profile root is identified, its contents are excluded before audit reads. Reports record only the path, reason, marker names, and `files_not_read=true`.

Hard privacy exclusions cannot be disabled by project configuration.

## Project scope configuration

Optional roots and additional exclusions can be declared in `.seo-autopilot.json`:

```json
{
  "schema_version": 1,
  "scope": {
    "include_roots": ["website-src"],
    "exclude_directories": ["legacy-export"]
  },
  "checks": []
}
```

Paths must be relative and cannot contain `..`. Includes never override generated, non-production, symlink/junction, or sensitive-profile exclusions.

## Auto-fix boundary

An A-level candidate is eligible only when all of the following are true:

```text
source_class = CURRENT_SOURCE
scope_eligible = true
generated = false
sensitive = false
path resolves inside the target workspace
replacement is mechanically proven
```

Otherwise the engine emits review evidence or excludes the file. It never applies an A-level fix to artifacts, snapshots, temporary files, or browser profiles.

## Structured evidence

Every v1.5.2 `run.json` includes `audit_scope`, counts of scanned source files, generated/non-production exclusions, privacy exclusions, and evidence classes. `REVIEW_REQUIRED` means audit completed but human review or a clean mutation baseline is required; it is not equivalent to `FAILED`.
