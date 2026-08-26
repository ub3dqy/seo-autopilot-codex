# Architecture

SEO Autopilot separates evidence collection, policy, scope, mutation, validation, and reporting.

## Runtime flow

```text
doctor
  → detect Git and framework
  → classify readiness

audit
  → SOURCE_FIRST scope plan
  → generated/non-production exclusions
  → metadata-only sensitive-profile detection
  → static HTML engine
  → framework source adapter
  → policy/risk classification
  → structured run.json + Markdown/HTML

fix
  → require clean Git tree
  → repeat scoped audit
  → select CURRENT_SOURCE A-level candidates only
  → isolated worktree and local branch
  → apply bounded deterministic changes
  → git diff --check + trusted validators
  → repeat audit + idempotency
  → commit or rollback
```

## Scope layer

`scope.py` is the authority for candidate selection. In Git repositories it combines tracked source with untracked files only inside known source roots. In non-Git directories it inspects only root website files and known source roots.

The scope layer records:

- tracked and untracked source candidate counts;
- static and framework files scanned;
- generated/temporary exclusions;
- non-production fixture/example exclusions;
- sensitive browser-profile exclusions;
- whether metadata discovery reached its budget.

The legacy static parser receives only paths admitted by the scope plan. This preserves existing deterministic rules while removing workspace-wide recursive noise.

## Privacy layer

Directory metadata is examined without opening file contents. Browser markers identify the nearest profile root. Once marked `EXCLUDED_SENSITIVE`, traversal stops and contents are never passed to parsers, hashing, excerpts, secret scans, or reports.

Hard privacy exclusions take precedence over custom includes.

## Evidence classes

Findings declare one evidence class:

```text
DETERMINISTIC_STATIC
FRAMEWORK_SOURCE
LIVE_BROWSER
EXTERNAL_DATA
OWNER_FACT
SCOPE_CONTROL
```

v1.5.2 emits deterministic static and framework source findings. Live/browser and external-data findings require separate factual evidence and must not be inferred from source alone.

## Framework adapters

The Next.js adapter performs conservative read-only checks for source patterns that need review:

- client hash navigation with no explicit post-render target resolution;
- stateful mobile menu controls missing accessibility evidence;
- sitemap lastModified based on build/runtime time;
- ambiguous WebSite identity;
- dynamic route metadata ownership.

Framework findings are always B/C. They cannot produce automatic source edits.

## Risk floor

- A: mechanically proven, scope-eligible `CURRENT_SOURCE` only.
- B: owner review and explicit decision.
- C: advisory only.

Canonical, robots, noindex, redirects, URL changes, structured data, content, deletion, push, merge, and deployment are never promoted to A by model judgement.

## Packaging and verification

`VERSION` is the single version source. User and Engineering Editions are built from tracked source, written deterministically, marked, hashed, rebuilt, and compared. The local release gate runs source tests, AIRSYS-shaped scope/privacy regressions, transaction tests, secret scan, direct-from-ZIP runtime checks, SBOM generation, release verification, and post-build generated-tree verification.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```
