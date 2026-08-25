# Local release process

GitHub Actions is not used and is not a release dependency.

1. Check out the exact commit intended for release and confirm the branch is clean.
2. Update `VERSION`, `CHANGELOG.md`, and `RELEASE_NOTES.md` in one reviewed change.
3. Run the official local gate:

   ```bash
   python scripts/verify_local.py --release
   ```

4. Inspect `local-verification/latest.json`. Required conditions are `status: PASS`, the expected `git_head`, and `git_dirty: false`.
5. When Codex credentials are available, run the live canary separately and record `PASSED`, `FAILED`, or `NOT_RUN` without conflation:

   ```bash
   python scripts/verify_local.py --live --require-live
   ```

6. For every platform claimed in release notes, repeat the same commit on that platform and retain its JSON/log evidence. One machine cannot prove another platform.
7. Review `dist/SHA256SUMS`, `dist/release-build.json`, the two deterministic ZIPs and the SPDX SBOM.
8. Create a protected or signed tag `v<VERSION>` only after the required local reports pass.
9. Publish the already verified files from `dist/` manually with GitHub CLI or the GitHub UI. Do not rebuild different bytes during publication.
10. Verify downloaded assets against `SHA256SUMS` before announcing the release.
11. Never overwrite an existing tag or release asset. Publish a new patch version for corrections.

The local tooling never pushes, merges, tags, publishes or deploys automatically. Repository settings such as branch protection, private vulnerability reporting, secret scanning/push protection and immutable releases remain explicit owner decisions.
