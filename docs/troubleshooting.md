# Troubleshooting

## `fix mode requires a clean working tree`

Commit, stash, or deliberately move your work first. SEO Autopilot does not silently exclude local changes and does not use `--force` to bypass this gate.

```bash
git status --short
seo-autopilot doctor . --json
```

## `digest mismatch` for a project check

The argv changed after approval. Review the exact executable and every argument, calculate a new digest, and update `.seo-autopilot.json` only when the change is intentional.

```bash
seo-autopilot command-hash -- npm test
```

Example configuration:

```json
{
  "schema_version": 1,
  "checks": [
    {
      "name": "project tests",
      "argv": ["npm", "test"],
      "sha256": "PASTE_THE_EXACT_DIGEST_HERE",
      "timeout_seconds": 300
    }
  ]
}
```

## Existing `user/`, `engineering/`, or `dist/` is not managed

The release builder refuses to overwrite an unmarked directory. Move it aside and compare it, or use `--force` only after confirming it contains no unique work.

```bash
python prepare_editions.py --verify-only
python prepare_editions.py --build-zips
```

## Generated directory has local modifications

The marker hash no longer matches. Preserve the local diff before rebuilding. Generated outputs are not the canonical source; accepted changes belong in the tracked source tree.

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

`NOT_RUN` means the CLI or authentication was unavailable. It is not a failure of deterministic tests and must not be represented as a live PASS. Configure the GitHub secret or local Codex authentication, then manually run `.github/workflows/live-eval.yml`.

## Reports contain sensitive excerpts

Reports are local artifacts and may include short source excerpts. Review and redact them before attaching to an issue or sharing outside the project.
