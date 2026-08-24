# Changelog

All notable product, policy, safety, and release-process changes are recorded here.

## 1.5.0 — Trust, transparency, and transactional autopilot

### Added

- browsable canonical Python source, Codex skill, policies, schemas, tests, docs, and workflows;
- `doctor`, `audit`, `fix`, `rollback`, `verify`, `install-skill`, and `command-hash` commands;
- explicit A/B/C risk model with no model-controlled downgrade;
- isolated Git worktree transactions, disabled hooks, local branch commits, and rollback state;
- exact argv SHA-256 trust for optional project validators;
- structured `run.json`, Markdown report, and standalone HTML report;
- deterministic static HTML evidence and local image dimension auto-fix;
- prompt-injection fixture, idempotency test, budgets, dirty-tree gate, and rollback tests;
- versioned SEO policy pack and JSON Schema;
- cross-platform CI, CodeQL, dependency review, secret scanning, SBOM, provenance, release workflow, and manual live Codex canary.

### Changed

- release editions are now assembled directly from tracked source files;
- `VERSION` is the only version literal used by release tooling;
- generated directories are marked, verified, atomically replaced, and protected from accidental overwrite;
- User Edition installation is reduced to one platform launcher plus a natural-language Codex request.

### Removed

- opaque base64/xz source bundle from the canonical repository tree;
- stale source-embedded release checksums;
- temporary source-materialization workflow;
- claims that deterministic tests represent a live autonomous Codex pass.

### Security

- repository and web content is always untrusted data;
- shell interpolation and automatic execution of project scripts are prohibited;
- canonical, noindex, robots, redirects, routes, schema, content, deletion, push, merge, and deployment are not automatic.

## 1.4.0

- Initial User and Engineering editions.
- Deterministic package checks and static behavioral contracts.
- Live autonomous Codex suite recorded as `NOT_RUN`.
