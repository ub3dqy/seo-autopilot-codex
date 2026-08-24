# SEO Autopilot for OpenAI Codex

Evidence-driven SEO-аудит и консервативное внедрение исправлений в код сайта: с явными уровнями риска, изолированной Git-транзакцией, проверками, отчётом и rollback.

[![CI](https://github.com/ub3dqy/seo-autopilot-codex/actions/workflows/ci.yml/badge.svg)](https://github.com/ub3dqy/seo-autopilot-codex/actions/workflows/ci.yml)
[![Security](https://github.com/ub3dqy/seo-autopilot-codex/actions/workflows/security.yml/badge.svg)](https://github.com/ub3dqy/seo-autopilot-codex/actions/workflows/security.yml)

## Что изменилось в v1.5

Канонические исходники, skill, policies, schemas, tests и workflows находятся в обычном просматриваемом дереве Git. Кодированный source bundle больше не является источником продукта. User и Engineering Edition собираются непосредственно из текущего commit.

Продукт разделяет:

- **детерминированный локальный слой** — doctor, аудит, evidence, безопасные A-level исправления, Git-транзакция, проверки и отчёты;
- **Codex skill** — естественный пользовательский интерфейс и обязательная модель поведения агента;
- **live Codex canary** — отдельная ручная проверка фактического поведения Codex, которая честно остаётся `NOT_RUN`, пока её не запустили с доступной авторизацией.

## Быстрый старт

### Windows

Скачайте User Edition или клонируйте репозиторий и запустите:

```text
INSTALL_WINDOWS.cmd
```

### macOS / Linux

```bash
./install.sh
```

Установщик ставит локальный CLI и копирует skill в `CODEX_HOME/skills/seo-autopilot`.

После установки откройте репозиторий сайта в Codex и напишите:

```text
Проведи SEO-аудит этого сайта. Сначала только аудит и отчёт, без изменений.
```

Для безопасного внедрения только механически доказанных исправлений:

```text
Исправь только A-level замечания SEO Autopilot, выполни проверки и оставь изменения в отдельной локальной ветке. Ничего не отправляй и не развёртывай.
```

## Прямой CLI

```bash
seo-autopilot doctor . --json
seo-autopilot audit .
seo-autopilot fix .
```

Дополнительные команды:

```bash
seo-autopilot verify .seo-autopilot/runs/<run-id>/run.json
seo-autopilot rollback --state .seo-autopilot/runs/<run-id>/state.json
seo-autopilot command-hash -- npm test
seo-autopilot install-skill
```

## Модель риска

| Уровень | Поведение | Примеры |
|---|---|---|
| `A_AUTO_FIX` | Может применяться автоматически только после механического доказательства | отсутствующие width/height, прочитанные из заголовка локального PNG/JPEG/GIF/WebP |
| `B_REVIEW_REQUIRED` | Evidence и предложение, но требуется просмотр владельца | title, description, lang, alt, canonical, sitemap, internal links, JSON-LD, hreflang |
| `C_ADVISORY_ONLY` | Только отчёт | noindex, robots, redirects, URL/routes, удаление страниц, production/deployment |

Модель не может самостоятельно понизить B или C до A. Расширение A-level требует нового детерминированного адаптера и тестов.

## Что происходит в fix mode

1. Проверяется Git, стек и чистота рабочего дерева.
2. Аудит фиксирует evidence и план.
3. Из точного `HEAD` создаётся временный worktree вне каталога владельца.
4. Создаётся локальная ветка `seo-autopilot/<run-id>`.
5. Применяются только A-level изменения в пределах бюджетов.
6. Запускаются `git diff --check`, явно доверенные проектные проверки и повторный аудит.
7. Повторная A-level правка считается ошибкой идемпотентности.
8. При ошибке worktree и ветка удаляются; при успехе остаётся локальный commit для просмотра.

Команда не содержит push, merge, deploy или публикацию.

## Доверенные проектные проверки

Команды не извлекаются из README, HTML, `package.json`, Makefile или ответа модели. Они запускаются только как точный argv-массив без shell и с подтверждённым SHA-256.

```json
{
  "schema_version": 1,
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

Получить digest:

```bash
seo-autopilot command-hash -- npm test
```

## Результаты запуска

Каждый запуск формирует:

```text
.seo-autopilot/runs/<run-id>/
  run.json       канонический машиночитаемый результат
  report.md      отчёт для code review
  report.html    автономный интерактивно читаемый отчёт
  state.json     состояние транзакции и rollback
```

Каждое замечание содержит finding ID, policy rule, severity, risk, confidence, path/line, evidence и статус `OPEN`, `FIXED`, `SKIPPED` или `DEFERRED`.

Продукт не обещает ranking, indexing, traffic, rich results, AI citations или conversion. Отсутствующие Search Console, CrUX, PageSpeed, analytics, SERP или backlink данные обозначаются как ограничения, а не заменяются оценками «из головы».

## Две редакции

Собрать обе редакции:

### Windows

```text
BUILD_EDITIONS_WINDOWS.cmd
```

### macOS / Linux

```bash
./build_editions.sh
```

Ручной эквивалент:

```bash
python prepare_editions.py --build-zips
```

Сборщик:

- читает единственную версию из `VERSION`;
- проверяет `release-manifest.json`;
- запрещает symlink и выход из source root;
- не перезаписывает чужие или вручную изменённые output-каталоги;
- выполняет атомарную замену;
- создаёт детерминированные ZIP и вычисляет SHA-256.

`User Edition` содержит необходимый runtime, skill, policy pack, schema и установщики. `Engineering Edition` дополнительно содержит полное source tree, docs, tests и release tooling.

## Проверка

Локальный gate:

```bash
python -m pip install --no-deps -e .
python -m compileall -q src scripts tests prepare_editions.py
python -m unittest discover -s tests -v
python prepare_editions.py --verify-only
python scripts/secret_scan.py
```

CI выполняет матрицу Windows/macOS/Linux и Python 3.10/3.12/3.13. Security workflow запускает CodeQL и dependency review. Tag-release повторяет gates, собирает ZIP, создаёт SPDX SBOM, общие SHA-256 и GitHub provenance attestation.

Live Codex behavior не считается проверенным статическими тестами. Оно имеет отдельный ручной workflow `.github/workflows/live-eval.yml` и статусы `PASSED`, `FAILED` или `NOT_RUN`.

## Безопасность и документация

- [Security policy](SECURITY.md)
- [Safety model](docs/safety-model.md)
- [Architecture](docs/architecture.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing](CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Changelog](CHANGELOG.md)

## Лицензия

Репозиторий публично доступен для просмотра, но остаётся proprietary/source-available согласно `LICENSE.md` и не позиционируется как open source. Публичный доступ сам по себе не предоставляет право на изменение, перераспространение, сублицензирование или продажу.
