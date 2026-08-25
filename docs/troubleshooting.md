# Troubleshooting

## `fix mode requires a clean working tree`

Commit, stash or deliberately move your work first. SEO Autopilot does not silently exclude local changes and does not use `--force` to bypass this gate.

```bash
git status --short
seo-autopilot doctor . --json
```

## `digest mismatch` for a project check

The argv changed after approval. Review the exact executable and every argument, calculate a new digest and update `.seo-autopilot.json` only when the change is intentional.

```bash
seo-autopilot command-hash -- npm test
```

## Existing `user/`, `engineering/` or `dist/` is not managed

The release builder refuses to overwrite an unmarked directory. Move it aside and compare it, or use `--force` only after confirming it contains no unique work.

```bash
python prepare_editions.py --verify-only
python prepare_editions.py --build-zips
```

## Generated directory has local modifications

The marker hash no longer matches. Preserve the local diff before rebuilding. Generated outputs are not the canonical source; accepted changes belong in the tracked source tree.

## Local verification failed

Run the authoritative gate directly and preserve its complete output:

```bash
python scripts/verify_local.py
```

Do not weaken or skip a failed check. Fix the first failing phase, then rerun the entire gate from a clean checkout.

## GitHub Actions is red or unavailable

This is an acknowledged external condition, not the project release gate:

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

Do not rerun workflows or treat an Actions badge as test evidence. The final branch must contain no active `.github/workflows/*.yml` or `.yaml` files.

## Fix validation failed

Read `.seo-autopilot/runs/<run-id>/run.json` and `report.md`. The transaction should be `ROLLED_BACK`, and its temporary branch should no longer exist. Do not re-run with weaker checks; fix the cause or adjust an incorrect policy/fixture through review.

## Successful branch remains local

This is expected. Inspect it:

```bash
git diff HEAD..seo-autopilot/<run-id>
git show --stat seo-autopilot/<run-id>
```

Merge or push only through a separate owner decision. To discard it, use the rollback command recorded in the report.

## No static HTML files were found

The stack was detected, but no deterministic adapter owns its framework metadata yet. The tool reports a limitation instead of rewriting templates speculatively. Add a tested adapter or perform a reviewed manual change.

## Live Codex canary is `NOT_RUN`

`NOT_RUN` means the local Codex CLI or authentication was unavailable. It is not a failure of deterministic tests and must not be represented as a live PASS.

```bash
python scripts/live_codex_eval.py --timeout 900 --output artifacts/live-codex-eval.json
```

## Reports contain sensitive excerpts

Reports may include short repository excerpts. High-confidence patterns are redacted, but every report must still be reviewed before attaching it to an issue or sharing it outside the project.
