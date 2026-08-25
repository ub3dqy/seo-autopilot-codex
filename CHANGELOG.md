# Changelog

All notable product, policy, safety, and release-process changes are recorded here.

## 1.5.0 — Trust, transparency, and transactional autopilot

### Added

- browsable canonical Python source, Codex skill, policies, schemas, tests, docs, and local verification tools;
- `doctor`, `audit`, `fix`, `rollback`, `verify`, `install-skill`, and `command-hash` commands;
- explicit A/B/C risk model with no model-controlled downgrade;
- isolated Git worktree transactions, disabled hooks, local branch commits, and rollback state;
- exact argv SHA-256 trust for optional project validators;
- structured `run.json`, Markdown report, and standalone HTML report;
- deterministic static HTML evidence and local image dimension auto-fix;
- prompt-injection fixture, idempotency test, budgets, dirty-tree gate, and rollback tests;
- versioned SEO policy pack and JSON Schema;
- one-command local verification, timestamped JSON/log evidence, deterministic double-build, SPDX SBOM, release asset verification, and local live Codex canary.

### Changed

- release editions are now assembled directly from tracked source files;
- `VERSION` is the only version literal used by release tooling;
- generated directories are marked, verified, atomically replaced, and protected from accidental overwrite;
- User Edition installation is reduced to one platform launcher plus a natural-language Codex request;
- project acceptance and release are explicitly local and do not depend on GitHub Actions;
- platform support claims require a retained PASS report from the actual platform.

### Removed

- opaque base64/xz source bundle from the canonical repository tree;
- stale source-embedded release checksums;
- GitHub Actions workflows and workflow badges from the product process;
- claims that deterministic tests represent a live autonomous Codex pass;
- unsupported claims of CodeQL, dependency-review or hosted provenance gates.

### Security

- repository and web content is always untrusted data;
- shell interpolation and automatic execution of project scripts are prohibited;
- canonical, noindex, robots, redirects, routes, schema, content, deletion, push, merge, and deployment are not automatic;
- local logs use centralized high-confidence secret redaction before persistence.

## 1.4.0

- Initial User and Engineering editions.
- Deterministic package checks and static behavioral contracts.
- Live autonomous Codex suite recorded as `NOT_RUN`.
