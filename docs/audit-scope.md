# Audit scope and privacy

SEO Autopilot separates current website evidence from generated copies, test output and sensitive local runtime state before parsing HTML.

## Read-only preflight

Installed command:

```bash
seo-autopilot scope /absolute/path/to/site --json
```

Directly from a verified release root:

```bash
PYTHONPATH=src PYTHONNOUSERSITE=1 python -S -m seo_autopilot scope /absolute/path/to/site --json
```

The command reports:

- detected stack;
- selected static HTML paths;
- directories pruned by default;
- whether Git ignore rules were applied;
- the optional `.seo-autopilotignore` file and accepted patterns;
- browser-profile-like or credential-bearing paths detected from names only;
- limitations when framework source or rendered/live evidence is still required.

The scope command does not parse page contents. Browser-profile detection does not open Cookies, History, Login Data, Web Data, Firefox databases or similar files.

## Default exclusions

The default audit excludes common repository metadata, dependencies and generated output at any depth:

```text
.git/
.seo-autopilot/
node_modules/
.next/
.nuxt/
.output/
dist/
build/
coverage/
.cache/
.turbo/
```

The following generic generated names are excluded only when they are top-level directories in the target workspace, so a legitimate route such as `src/app/artifacts/` is not silently removed:

```text
artifacts/
tmp/
temp/
playwright-report/
test-results/
blob-report/
```

Credential-bearing and browser-profile directory names such as `.ssh`, `.aws`, `chrome-profile`, `browser-profile`, `firefox-profile` and `User Data` are excluded before HTML parsing. Symlink and Windows junction/reparse-point directories are not traversed.

Tracked files remain eligible even when a later Git ignore rule matches them. Untracked files excluded by `.gitignore` are not audited by default. Git-path comparison follows the host filesystem's case behavior instead of forcing all paths to lowercase.

## Project-specific `.seo-autopilotignore`

Create `.seo-autopilotignore` in the target repository root when the standard scope needs adjustment. Syntax is an ordered subset of Git-style glob rules:

```gitignore
# Ignore obsolete static exports
legacy-export/**
reports/**

# Re-include a reviewed subtree from a normally excluded directory
!artifacts/current-production-snapshot/**
```

Rules are evaluated in order. A leading `!` re-includes a matching ordinary file or subtree. The file is bounded to 64 KiB and 512 usable patterns. Invalid, overlong and NUL-containing lines are ignored.

Re-inclusion cannot override any of these hard privacy boundaries:

- named credential directories such as `.ssh` or `.aws`;
- detected browser profiles;
- symlink or junction traversal;
- Git's ignored-untracked boundary.

A generated export that must be audited should be placed in an explicitly reviewed, non-sensitive location and either tracked intentionally or made visible to Git.

## Framework projects

A Next.js, Astro, Nuxt, SvelteKit or other framework repository may contain no in-scope static HTML. This is not a clean SEO pass. The scope result becomes `READY_WITH_LIMITATIONS`, and Codex must separately inspect the source owners of:

- routes;
- title and description metadata;
- canonical URLs;
- robots and sitemap generation;
- hreflang;
- JSON-LD;
- internal links;
- real 404 behavior;
- indexability.

Rendered-browser, Search Console, Яндекс Вебмастер, CrUX, PageSpeed, analytics, SERP and backlink evidence remains `DEFERRED` or `NOT_RUN` when it was not actually supplied or measured.

## Dirty working trees

The scope preflight and `audit` remain read-only and may run against a dirty repository. Transactional `fix` stays blocked until the owner establishes a clean baseline. SEO Autopilot never uses `reset`, `clean` or `stash` to hide existing work.
