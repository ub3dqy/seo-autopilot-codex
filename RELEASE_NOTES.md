# SEO Autopilot for OpenAI Codex v1.5.4

## Next.js metadata and site-verification accuracy

v1.5.4 is a focused field-test patch for the AIRSYS v1.5.3 checkpoint. The v1.5.3 privacy and route-scope fixes passed, but 10 of 11 deterministic findings were not actionable: two treated framework-owned `/robots.txt` and `/sitemap.xml` as missing, and eight treated Google/Yandex ownership-verification files as ordinary pages.

### Fixed

- recognized Next.js App Router metadata owners at `app/robots.ts`, `src/app/robots.ts`, `app/sitemap.ts`, and `src/app/sitemap.ts` suppress generic missing-file findings only when a default export is present;
- static `app/robots.txt`, `src/app/robots.txt`, `app/sitemap.xml`, and `src/app/sitemap.xml` are also recognized as endpoint owners;
- exact Google and Yandex site-ownership verification files are excluded from title, description, canonical, language, duplicate-title, image, and auto-fix checks;
- verification-file exclusions are recorded explicitly in `audit_scope.excluded_site_verification_files` instead of disappearing silently;
- a Next.js project with no production static HTML now reports framework-source coverage rather than the obsolete “no explicit adapter” limitation.

### Guardrails

- a filename alone is insufficient to classify an HTML file as an ownership-verification asset;
- classification requires a small file in the repository root, `public/`, or `static/`, plus an exact provider-specific filename/content contract;
- similarly named real pages remain in scope;
- `robots.ts` or `sitemap.ts` without a default export do not suppress missing-endpoint findings;
- live HTTP verification of `/robots.txt` and `/sitemap.xml` remains a separate check and is never inferred from source alone;
- confirmed source/live findings such as hash-navigation delay, legal-text drift, schema identity, CSP, or server disclosure are not suppressed.

### Regression coverage

The release gate includes an AIRSYS-shaped Next.js fixture with:

```text
src/app/robots.ts
src/app/sitemap.ts
public/google55fef1f505cfa1c3.html
public/yandex_ee018aae7c9cfe7f.html
scripts/static-first-loader.js
```

Acceptance requires the two verification files to be recorded but not audited as pages, framework-owned endpoints not to produce `TECH-ROBOTS-001` or `TECH-SITEMAP-001`, and the real hash-navigation finding to remain.

## Verification

The canonical cross-platform release gate remains:

```bash
python scripts/verify_local.py --release
```

The UTF-8-safe Windows entry point is:

```text
VERIFY_LOCAL_WINDOWS.cmd --release
```

The one-link bootstrap remains pinned to published v1.5.3 until v1.5.4 assets pass the exact local gate, direct-from-ZIP field smoke, publication, download, and SHA-256 round-trip verification. A separate verified bootstrap commit then switches all public pins to v1.5.4.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```
