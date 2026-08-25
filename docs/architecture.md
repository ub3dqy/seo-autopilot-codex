# Architecture

## Components

```text
natural-language Codex request
        │
        ▼
skills/seo-autopilot/SKILL.md
        │  trust boundary and workflow
        ▼
seo-autopilot CLI
   ├── doctor.py            Git/Codex/stack readiness
   ├── policy.py            versioned rules and risk floor
   ├── engine.py            deterministic evidence and A-level fixes
   ├── trusted_commands.py  exact argv + SHA-256 validators
   ├── transaction.py       isolated worktree, branch, commit, rollback
   └── reporting.py         run.json, Markdown, standalone HTML
        │
        ▼
local seo-autopilot/<run-id> branch
```

The Codex skill is an orchestration policy. The Python engine is the deterministic enforcement layer. The skill cannot promote a change into automatic application; only engine-produced `SafeFix` records with `A_AUTO_FIX` are eligible.

## Run lifecycle

```text
INITIALIZED
  → DISCOVERY_COMPLETE
  → EVIDENCE_COMPLETE
  → PLAN_COMPLETE
  → PATCH_APPLIED
  → VALIDATION_COMPLETE
  → COMMITTED
```

Any failure after transaction creation goes to `ROLLED_BACK` or, when rollback itself cannot complete, `FAILED`. State is persisted in `.seo-autopilot/runs/<run-id>/state.json`.

## Read-only audit

`audit` scans bounded UTF-8 HTML evidence, local crawl-control files, supported local image headers, and versioned policy rules. It does not execute project commands or change source files.

## Fix transaction

`fix` requires a clean Git worktree, resolves `HEAD`, creates a detached temporary worktree outside the owner repository, creates `seo-autopilot/<run-id>`, re-audits that exact commit, applies only A-level changes, runs built-in and explicitly trusted validators, repeats the audit for idempotency, commits locally, and removes the temporary worktree. The branch remains for review.

## Reports

`run.json` is the source of truth. Markdown and HTML are projections. Each finding carries a stable ID, policy rule, severity, risk, confidence, status, path, line, and evidence. A report distinguishes applied, open, skipped, deferred, failed, and rolled-back work.

## Framework adapters

The doctor detects common stacks without executing package scripts. Static HTML has a deterministic adapter. Other stacks are detected for routing and reporting but remain audit-limited until a dedicated adapter proves metadata ownership and build semantics. Unknown stacks never trigger speculative source rewriting.

## Verification architecture

`scripts/verify_local.py` is the canonical verification orchestrator. It invokes subprocesses as exact argv arrays without shell interpolation, writes redacted logs and JSON evidence, and supports deterministic, build, official release, and optional live-Codex modes. GitHub Actions is not part of the architecture.

## Release architecture

`VERSION` is canonical. `release-manifest.json` describes edition contents and artifact templates. `prepare_editions.py` validates tracked sources, builds marked trees, refuses unsafe replacement, creates deterministic ZIPs, and writes computed checksums. The local release gate performs a second build for reproducibility, creates an SPDX SBOM, verifies assets, and records the exact environment and commit. Publication is a separate owner action and never rebuilds or mutates the verified source automatically.
