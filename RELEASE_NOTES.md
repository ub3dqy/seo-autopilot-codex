# SEO Autopilot for OpenAI Codex v1.5.2

## Audit Scope & Privacy Hardening

- Source-first candidate selection replaces recursive workspace-wide HTML scanning.
- Generated, temporary, archived, report, fixture, example, and build trees are excluded before content reads.
- Browser profiles are hard privacy exclusions detected from metadata markers; profile contents are never opened by the audit engine.
- A-level fixes require a `CURRENT_SOURCE` scope classification.
- `run.json` schema version 1 now records `audit_scope`, exclusions, scan counts, and evidence classes.
- A deterministic Next.js source adapter records review findings for hash navigation, mobile-menu accessibility, sitemap dates, WebSite identity, and dynamic metadata ownership.
- `REVIEW_REQUIRED` remains a completed read-only audit outcome that blocks mutation until owner review or a clean baseline.

## Verification

The mandatory gate remains local:

```bash
python scripts/verify_local.py --release
```

It must pass the AIRSYS-shaped scope/privacy regression, all prior unit/lifecycle/transaction tests, secret scan, direct-from-ZIP runtime tests, deterministic double build, SBOM, release verification, and post-build generated-tree verification.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```
