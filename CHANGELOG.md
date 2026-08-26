# Changelog

All notable product, policy, safety and release-process changes are recorded here.

## 1.5.2 — Audit scope and privacy hotfix

### Fixed

- generated snapshots and temporary trees such as `artifacts/`, `tmp/`, Playwright reports and caches are excluded from the default HTML audit scope;
- Git-ignored files no longer become SEO findings unless they are already tracked;
- browser-profile and credential-bearing directory names are excluded before page parsing;
- audits no longer propose A-level fixes for archived HTML copies outside the current website source.

### Added

- automatic `.seo-autopilotignore` support with ordered glob rules and `!` re-inclusion;
- `python -m seo_autopilot.scope <workspace> --json` read-only scope preflight;
- scope evidence for selected HTML, pruned directories, Git-ignore use and browser-profile-like paths;
- regression coverage reproducing the AIRSYS `artifacts/**`, `tmp/**` and Chrome-profile noise scenario.

### Privacy

- browser profile detection uses path and directory-entry names only;
- Cookies, History, Login Data and other profile file contents are not opened by the scope preflight or HTML scanner;
- sensitive paths produce `REVIEW_REQUIRED` in scope evidence and remain excluded from SEO findings.

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
