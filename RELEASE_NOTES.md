# SEO Autopilot for OpenAI Codex v1.5.2

## Audit scope and privacy hotfix

Первое полевое испытание на крупном Next.js-проекте AIRSYS подтвердило работоспособность one-link bootstrap v1.5.1, но выявило шум области аудита: 628 из 638 findings относились к архивам и временным каталогам `artifacts/**` и `tmp/**`, а все 98 A-level кандидатов находились в старых снимках.

v1.5.2 исправляет этот класс ошибок.

### Deterministic scope

- `artifacts/`, `tmp/`, `temp/`, caches, Playwright/test reports и build output исключаются до HTML-парсинга;
- untracked-файлы, исключённые через `.gitignore`, не входят в аудит;
- tracked-файлы остаются видимыми, если не исключены самой политикой SEO Autopilot;
- добавлен `.seo-autopilotignore` с упорядоченными glob-правилами и `!` re-inclusion;
- добавлена команда `seo-autopilot scope <workspace> --json`;
- scope evidence содержит selected files, pruned directories, Git-ignore state и ограничения framework-аудита.

### Privacy boundary

- browser-profile и credential-bearing каталоги исключаются до разбора страниц;
- обнаружение использует только имена директорий и marker-файлов;
- Cookies, History, Login Data, Web Data, Firefox databases и иные profile contents не открываются;
- наличие таких путей возвращает `REVIEW_REQUIRED` в scope preflight и рекомендацию переместить их за пределы workspace.

### Framework behavior

Если Next.js, Astro, Nuxt, SvelteKit или другой framework-проект не содержит in-scope статического HTML, scope возвращает `READY_WITH_LIMITATIONS`, а не чистый SEO PASS. Codex должен отдельно провести read-only source review владельцев routes, metadata, canonical, robots, sitemap, hreflang, JSON-LD, internal links, real 404 и indexability.

### Safety

- dirty working tree по-прежнему разрешает read-only scope/audit, но блокирует `fix`;
- reset, clean и stash для обхода барьера запрещены;
- canonical, noindex, redirects, URLs, schema, content, push, merge и deployment автоматически не применяются;
- рейтинг, трафик, конверсии и доход не гарантируются.

## Verification

Обязательный gate выполняется локально:

```bash
python scripts/verify_local.py --release
```

Release gate должен включать:

- все unit/adversarial/transaction tests;
- AIRSYS regression на исключение `artifacts/**` и `tmp/**`;
- privacy regression без чтения browser-profile contents;
- direct-from-ZIP `scope → doctor → audit → verify` для User и Engineering Edition;
- две детерминированные сборки;
- SBOM, SHA-256 и release-asset verification.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Compatibility

v1.5.2 использует Python 3.10 или новее. v1.5.1 остаётся исправным one-link runtime, но не содержит нового scope-filter и может создавать шум на проектах с архивными HTML-копиями внутри workspace.
