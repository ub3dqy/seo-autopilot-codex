# Release process

## Source of truth

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

GitHub Actions is not used to build, test or publish this project. Do not create a tag or release from an unverified working tree.

## Required sequence

1. Update `VERSION`, `CHANGELOG.md` and `RELEASE_NOTES.md` in one coherent branch.
2. Start from a clean Git checkout and record the exact commit.
3. Run:

   ```bash
   python scripts/verify_local.py
   ```

4. Confirm the report records PASS for compilation, tests, secret scan, source verification, clean installation, two deterministic builds, restore verification and SHA-256.
5. Run the manual live Codex canary when local authentication is available; record `PASSED`, `FAILED` or `NOT_RUN` separately. `NOT_RUN` is never a deterministic PASS.
6. Build final assets from the same verified commit:

   ```bash
   python prepare_editions.py --build-zips
   python scripts/verify_release.py dist
   ```

7. Recompute and compare SHA-256 with the local verification evidence.
8. Review the complete diff and confirm that `.github/workflows/` contains no `.yml` or `.yaml` files.
9. Merge only the verified source tree. If the merge method changes the commit SHA, confirm that the resulting Git tree is identical to the verified branch tree.
10. Create tag `v<VERSION>` on the verified `main` commit.
11. Create a GitHub Release manually and attach:

    - User Edition ZIP;
    - Engineering Edition ZIP;
    - `SHA256SUMS`;
    - release manifest/build report;
    - sanitized local verification report and log;
    - optional SPDX SBOM.

12. Download the published assets and verify them again against `SHA256SUMS` before announcing the release.

## Immutability

Do not overwrite an existing tag or release asset. Publish a patch version for corrections. Repository settings such as branch protection, private vulnerability reporting, secret scanning and immutable releases remain explicit owner controls.
