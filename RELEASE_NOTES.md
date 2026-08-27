# SEO Autopilot for OpenAI Codex v1.5.3

## Route-safe privacy marker detection

v1.5.3 is a focused field-test hotfix for the AIRSYS result produced by v1.5.2.

### Fixed

- directories named `cookies`, `history`, `preferences`, `bookmarks`, and similar browser-marker words are no longer interpreted as browser profile databases;
- active Next.js source such as `src/app/(site)/(legacy)/cookies/page.tsx` remains inside `SOURCE_FIRST` audit scope;
- a lone ambiguous marker file inside a known source root cannot exclude the surrounding source tree.

### Privacy behavior retained

- marker entries must be regular files; directories and symlinks are ignored as browser database evidence;
- actual Chrome/Chromium/Edge/Firefox/Playwright profiles remain `EXCLUDED_SENSITIVE`;
- `files_not_read=true` remains mandatory;
- no browser database content is opened, excerpted, or hashed;
- distinctive database markers outside source roots continue to fail closed.

### Regression coverage

The release gate includes a Next.js fixture containing active routes named:

```text
cookies
history
preferences
bookmarks
```

alongside a real browser-profile-shaped tree containing `Network/Cookies` and `Login Data`. Acceptance requires all route files to be scanned, the browser profile to be excluded, zero source paths to be classified sensitive, and repeat audits to be deterministic.

## Verification

The canonical cross-platform release gate remains:

```bash
python scripts/verify_local.py --release
```

The UTF-8-safe Windows entry point used for the exact release run is:

```text
VERIFY_LOCAL_WINDOWS.cmd --release
```

It invokes the UTF-8 wrapper with `-X utf8`, `PYTHONUTF8=1`, and `PYTHONIOENCODING=utf-8` while preserving the same verification contract.

The one-link bootstrap remains pinned to published v1.5.2 until v1.5.3 assets are built, executed directly from both ZIP editions, published, downloaded again, and verified by SHA-256. A separate verified bootstrap commit then switches all public pins to v1.5.3.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```
