# SEO Autopilot — User Edition

User Edition предназначена для запуска без выбора внутренних промтов, validators или режимов агента. Установка выполняется локально стандартной библиотекой Python: pip, сеть и build backend не требуются.

## Установка

### Windows

Запустите `INSTALL_WINDOWS.cmd`.

### macOS / Linux

```bash
./install.sh
```

Установщик копирует Python-пакет в user site-packages, создаёт локальный launcher `seo-autopilot` и устанавливает Codex skill в `CODEX_HOME/skills/seo-autopilot`. Существующий неуправляемый каталог не перезаписывается без явного `--force`.

После установки откройте репозиторий сайта в Codex и попросите:

```text
Проведи SEO-аудит этого сайта. Сначала покажи фактическую область аудита, исключи архивы и временные файлы, затем создай отчёт без изменений исходников.
```

## Scope preflight

Перед аудитом выполните read-only проверку области:

```bash
seo-autopilot scope . --json
```

Она показывает:

- какие статические HTML-файлы попадут в аудит;
- какие каталоги исключены;
- применены ли правила `.gitignore`;
- используется ли `.seo-autopilotignore`;
- обнаружены ли browser-profile или credential-bearing пути.

По умолчанию исключены `artifacts/`, `tmp/`, `temp/`, Playwright/test reports, caches, dependencies и build output. Cookies, History, Login Data и другие данные browser profile не читаются.

Для локальных правил создайте `.seo-autopilotignore` в корне сайта:

```gitignore
legacy-export/**
reports/**
!artifacts/current-production-snapshot/**
```

Подробности: `docs/audit-scope.md` в Engineering Edition или исходном репозитории.

## Аудит и исправления

Для детерминированной проверки без Codex:

```bash
seo-autopilot scope . --json
seo-autopilot doctor . --json
seo-autopilot audit .
```

Dirty working tree не блокирует read-only `scope` и `audit`, но блокирует `fix`. Инструмент не выполняет `reset`, `clean` или `stash` для обхода этого барьера.

`fix` применяет только механически доказанные A-level изменения в отдельной локальной Git-ветке. Он не отправляет, не объединяет и не развёртывает код.

```bash
seo-autopilot fix .
```

Результаты находятся в `.seo-autopilot/runs/<run-id>/`. Перед передачей отчёта третьим лицам проверьте содержащиеся в нём excerpts.

## Проверка поставки

Engineering Edition и исходный репозиторий используют единый обязательный локальный gate:

```bash
python scripts/verify_local.py --release
```

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Ограничения

Canonical, noindex, robots, redirects, routes, schema, content, URL, удаление страниц и deployment не исправляются автоматически. Рейтинг, индексация, трафик, конверсии, выручка и rich results не гарантируются. Framework source, rendered-browser, Search Console, Яндекс Вебмастер, CrUX, PageSpeed, analytics, SERP и backlink evidence отмечаются как ограничения, если фактически не предоставлены или не измерены.
