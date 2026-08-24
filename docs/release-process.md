# Release process

1. Update `VERSION`, `CHANGELOG.md`, and `RELEASE_NOTES.md` in one reviewed pull request.
2. Run the complete deterministic gate locally and in CI.
3. Run the manual live Codex canary when credentials are available; record `PASSED`, `FAILED`, or `NOT_RUN` without conflation.
4. Create a signed or protected tag `v<VERSION>` only after all required gates pass.
5. `.github/workflows/release.yml` rebuilds from the tag, creates deterministic User and Engineering ZIPs, SPDX SBOM, SHA-256 checksums, and provenance attestations.
6. Verify the published release and assets with GitHub CLI before announcing it.
7. Do not overwrite an existing tag or release asset. Publish a new patch version for corrections.

Repository settings that cannot be enforced by tracked files must be enabled by the owner: branch protection, required checks, private vulnerability reporting, secret scanning/push protection where available, and immutable releases.
