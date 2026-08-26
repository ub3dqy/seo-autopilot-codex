# Changelog

All notable product, policy, safety and release-process changes are recorded here.

## 1.5.3 — Route-safe privacy marker detection

### Fixed

- Next.js route and content directories named `cookies`, `history`, `preferences`, `bookmarks`, or other browser-like marker names are no longer treated as browser profile databases;
- active source below route groups such as `src/app/(site)/(legacy)/cookies/` remains in `SOURCE_FIRST` scope;
- a single ambiguous marker file inside a known source root no longer excludes the surrounding source subtree.

### Changed

- browser-profile markers must be regular files rather than directories or symlinks;
- ambiguous marker names now require browser-shaped context or multiple independent markers;
- distinctive browser database filenames remain fail-closed outside known source roots;
- custom source roots receive the same false-positive protection as built-in source roots.

### Added

- regression coverage for `cookies`, `history`, `preferences`, and `bookmarks` Next.js routes alongside a real Chrome profile;
- deterministic repeat-audit assertions proving that source inclusion and sensitive exclusions remain stable.

### Security

- actual browser profiles remain `EXCLUDED_SENSITIVE` with `files_not_read=true`;
- the fix changes metadata classification only and does not open, excerpt, or hash browser database contents.

## 1.5.2 — Audit Scope & Privacy Hardening

### Added

- source-first audit scope based on tracked files plus untracked files only inside known source roots;
- structured `audit_scope` evidence with generated, non-production, and sensitive exclusions;
- hard browser-profile detection that excludes Chrome/Chromium/Edge/Firefox/Playwright profile trees before content reads;
- deterministic Next.js source findings for deferred hash navigation, mobile-menu accessibility, sitemap `lastModified`, WebSite identity, and dynamic metadata ownership;
- AIRSYS-shaped regression coverage with noisy `artifacts/**`, `tmp/**`, and browser profile markers.

### Changed

- A-level fixes are emitted only for `CURRENT_SOURCE` files admitted by the source-first scope;
- generated output, archives, snapshots, reports, fixtures, examples, and temporary trees are excluded by default;
- v1.5.2 reports extend schema version 1 with `audit_scope` and evidence classes while preserving compatibility;
- `REVIEW_REQUIRED` is presented as a review state, not a technical failure.

### Security

- privacy exclusions are immutable and cannot be overridden by project scope configuration;
- browser profile file contents are never opened, excerpted, or hashed by the audit engine;
- custom scope includes cannot re-enable generated or sensitive trees.

## 1.5.1 — Direct-from-release version hotfix

### Fixed

- direct execution from an unpacked User or Engineering Edition now resolves the version from the trusted root `VERSION` file when installed package metadata is unavailable;
- `python -S -m seo_autopilot --version` no longer returns `0+unknown` in the pinned bootstrap runtime;
- User Edition now carries `release-manifest.json`, allowing direct temporary execution to locate the bundled policy pack and schemas.

### Added

- a regression test that reproduces the exact `PYTHONPATH=<edition>/src` bootstrap path without site-packages;
- an explicit release note that v1.5.0 must not be used for direct-from-archive bootstrap.

### Security

- the version gate remains fail-closed;
- fallback version text is accepted only from the expected `src/seo_autopilot` layout and only when it matches the release version syntax.

## 1.5.0 — Trust, transparency and transactional autopilot

### Added

- browsable canonical Python source, Codex skill, policies, schemas, tests and docs;
- `doctor`, `audit`, `fix`, `rollback`, `verify`, `install-skill` and `command-hash` commands;
- explicit A/B/C risk model with no model-controlled downgrade;
- isolated Git worktree transactions, disabled hooks, local branch commits and rollback state;
- exact argv SHA-256 trust for optional project validators;
- structured `run.json`, Markdown report and standalone HTML report;
- deterministic static HTML evidence and local image-dimension auto-fix;
- prompt-injection fixture, idempotency, budgets, dirty-tree gate and rollback tests;
- versioned SEO policy pack and JSON Schema;
- cross-platform local verification runner, deterministic packaging, release restore tests and tracked-source secret scan.

### Changed

- release editions are assembled directly from tracked source files;
- `VERSION` is the single version source used by release tooling;
- generated directories are marked, verified, atomically replaced and protected from accidental overwrite;
- User Edition installation is reduced to one platform launcher plus a natural-language Codex request;
- GitHub Actions is explicitly classified as `BLOCKED_EXTERNAL / WAIVED_BY_OWNER`;
- the sole mandatory release gate is `python scripts/verify_local.py`.

### Removed

- opaque base64/xz source bundle from the canonical repository tree;
- stale source-embedded release checksums;
- active `.github/workflows/*` files and all release dependence on hosted Actions;
- claims that deterministic tests represent a live autonomous Codex pass.

### Security

- repository and web content is always untrusted data;
- shell interpolation and automatic execution of project scripts are prohibited;
- canonical, noindex, robots, redirects, routes, schema, content, deletion, push, merge and deployment are not automatic;
- generated evidence is locally reproducible and includes high-confidence secret redaction.

## 1.4.0

- Initial User and Engineering editions.
- Deterministic package checks and static behavioral contracts.
- Live autonomous Codex suite recorded as `NOT_RUN`.
