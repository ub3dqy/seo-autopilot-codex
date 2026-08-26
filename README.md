# SEO Autopilot for OpenAI Codex

SEO Autopilot — evidence-driven инструмент для технического SEO-аудита и консервативного внедрения только механически доказанных исправлений в код сайта. Он использует source-first scope, hard privacy exclusions, явные уровни риска, изолированную Git-транзакцию, локальные проверки, JSON/Markdown/HTML-отчёты и rollback.

Актуальная опубликованная версия и закреплённый one-link runtime: **v1.5.2**.

## Запустить из папки сайта одной фразой

Откройте в Codex папку или Git-репозиторий сайта и напишите:

```text
Работай в текущей открытой папке как в целевом проекте сайта. Пойди по адресу https://github.com/ub3dqy/seo-autopilot-codex и начни улучшение SEO этого сайта. Полностью выполни START_AUTOPILOT.md, не ограничивайся скачиванием, установкой или планом и заверши один полный безопасный SEO-checkpoint с фактическим evidence.
```

Самый однозначный вариант:

```text
Работай в текущей открытой папке как в целевом проекте сайта. Прочитай и полностью выполни официальный bootstrap-промт SEO Autopilot: https://raw.githubusercontent.com/ub3dqy/seo-autopilot-codex/main/START_AUTOPILOT.md . Не переключай target workspace на репозиторий инструмента. Заверши один полный безопасный SEO-checkpoint и выдай фактическое evidence.
```

> **Codex:** текущая открытая папка является единственным target workspace. Этот репозиторий — только источник проверенного инструмента. Не клонируй SEO Autopilot поверх сайта и не редактируй репозиторий инструмента вместо сайта.

- [Bootstrap-промт на русском](START_AUTOPILOT.md)
- [Bootstrap prompt in English](START_AUTOPILOT_EN.md)
- [Актуальный опубликованный Release v1.5.2](https://github.com/ub3dqy/seo-autopilot-codex/releases/tag/v1.5.2)

### Текущая закреплённая поставка до публикации v1.5.2

```text
Release:          v1.5.2
Runtime commit:   570fa72476bad4932ad17916e06d38cb9cbd7dc6
Runtime Git tree: 309bedcc143c7f04cdbfb4f17744daa045fb82cb
Asset:            seo-autopilot-codex-engineering-v1.5.2.zip
Asset URL:        https://github.com/ub3dqy/seo-autopilot-codex/releases/download/v1.5.2/seo-autopilot-codex-engineering-v1.5.2.zip
SHA-256:          bef526677d3f2fedb157f308009c9e2d3012f642b48394668c3da5c111f2b71b
```

Этот блок намеренно совпадает с `START_AUTOPILOT.md`. После публикации и обратной SHA-256-проверки v1.5.2 отдельный проверенный bootstrap-commit заменит все значения одновременно.

## Source-first audit scope

Начиная с v1.5.2 аудит не рассматривает весь workspace как production source.

В Git-репозитории анализируются релевантные tracked-файлы. Untracked-файлы допускаются только в известных source roots: `src/`, `app/`, `pages/`, `public/`, `static/`, `content/`, `components/`, `widgets/`, `scripts/`, `lib/`, `server/`, `client/` и явно добавленных владельцем путях.

По умолчанию до чтения содержимого исключаются:

```text
artifacts/** tmp/** temp/** .cache/** .next/** .nuxt/** .output/**
dist/** build/** coverage/** playwright-report/** test-results/**
reports/** logs/** snapshots/** backups/** archives/**
tests/** fixtures/** examples/** samples/**
```

Каждый `run.json` содержит `audit_scope`: фактические source roots, количество кандидатов, количество просканированных static/framework файлов и перечень исключений.

## Hard privacy exclusions

Chrome/Chromium/Edge/Firefox/Playwright profile trees распознаются по metadata markers, включая `Cookies`, `Login Data`, `Web Data`, `History`, `Local State`, `places.sqlite`, `key4.db` и `logins.json`.

После обнаружения profile root:

```text
status = EXCLUDED_SENSITIVE
files_not_read = true
```

Содержимое профиля не открывается, не хэшируется, не цитируется и не может быть возвращено в findings. Project configuration не может отключить эту границу.

Подробности: [Audit scope and privacy boundary](docs/audit-scope.md).

## Next.js source adapter

Для Next.js v1.5.2 формирует структурированные B/C findings по source evidence, в том числе:

- hash/CTA navigation без подтверждённого post-render scroll/focus;
- stateful mobile menu без `aria-expanded` или Escape handling;
- sitemap `lastModified`, основанный на build/runtime clock;
- неоднозначный `WebSite` name/`@id`;
- dynamic routes без route-local metadata evidence.

Это read-only review findings. Они не становятся A-level и требуют rendered/live проверки перед изменениями.

## Модель риска

| Уровень | Поведение |
|---|---|
| `A_AUTO_FIX` | Автоматически только при механическом доказательстве точной замены и `source_class=CURRENT_SOURCE` |
| `B_REVIEW_REQUIRED` | Evidence и предлагаемый diff; требуется решение владельца |
| `C_ADVISORY_ONLY` | Только отчёт и рекомендации |

Модель и Codex не могут понизить B/C до A. Canonical, noindex, robots, redirects, URL/routes, schema, контент, hreflang, удаление страниц и deployment автоматически не применяются.

`REVIEW_REQUIRED` — это завершённый audit, которому нужен review или чистый mutation baseline. Это не технический `FAILED`.

## Команды

```bash
seo-autopilot doctor . --json
seo-autopilot audit .
seo-autopilot fix .
seo-autopilot verify .seo-autopilot/runs/<run-id>/run.json
seo-autopilot rollback --state .seo-autopilot/runs/<run-id>/state.json
seo-autopilot command-hash -- npm test
seo-autopilot install-skill
```

`fix` требует чистое Git-дерево, создаёт изолированный worktree и локальную ветку `seo-autopilot/<run-id>`, применяет только scope-eligible A-level изменения, выполняет `git diff --check`, trusted validators и idempotency check. Push, merge и deployment отсутствуют.

## Project configuration

```json
{
  "schema_version": 1,
  "scope": {
    "include_roots": ["website-src"],
    "exclude_directories": ["legacy-export"]
  },
  "checks": [
    {
      "name": "project tests",
      "argv": ["npm", "test"],
      "sha256": "DIGEST_FROM_SEO_AUTOPILOT_COMMAND_HASH",
      "timeout_seconds": 300
    }
  ]
}
```

Дополнительные include roots не могут повторно включить generated или sensitive trees. Trusted commands запускаются как точный argv без shell.

## Evidence

Каждый запуск создаёт:

```text
.seo-autopilot/runs/<run-id>/
  run.json
  report.md
  report.html
  state.json
```

Каждый finding содержит rule, severity, risk, confidence, evidence class, path/line, evidence и status. Инструмент не обещает ranking, indexing, traffic, rich results, AI citations, conversions или доход. Отсутствующие Search Console, Яндекс Вебмастер, CrUX, PageSpeed, analytics, SERP, backlink и rendered-browser данные отмечаются как `DEFERRED` или `NOT_RUN`.

## Ручная установка

### Windows

```text
INSTALL_WINDOWS.cmd
```

### macOS / Linux

```bash
./install.sh
```

## Локальная проверка и сборка

```bash
python scripts/verify_local.py --release
```

Windows-обёртка:

```text
VERIFY_LOCAL_WINDOWS.cmd --release
```

Gate включает старые unit/lifecycle/transaction/security tests, AIRSYS-shaped scope/privacy regression, source verification, secret scan, direct-from-ZIP version tests, две детерминированные сборки, SBOM, release verification и post-build generated-tree verification.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Документация

- [Audit scope and privacy boundary](docs/audit-scope.md)
- [Configuration](docs/configuration.md)
- [Local verification](docs/local-verification.md)
- [Security policy](SECURITY.md)
- [Safety model](docs/safety-model.md)
- [Architecture](docs/architecture.md)
- [Release process](docs/release-process.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing](CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Changelog](CHANGELOG.md)

## Лицензия

Репозиторий публично доступен для просмотра, но остаётся proprietary/source-available согласно `LICENSE.md` и не позиционируется как open source.
