# SEO Autopilot for OpenAI Codex

SEO Autopilot — evidence-driven инструмент для технического SEO-аудита и консервативного внедрения только механически доказанных исправлений в код сайта. Инструмент использует явные уровни риска, изолированную Git-транзакцию, локальные проверки, JSON/Markdown/HTML-отчёты и rollback.

Закреплённый runtime для запуска по ссылке: **v1.5.1**.

## Запустить из папки сайта одной фразой

Откройте в Codex папку или Git-репозиторий сайта и напишите:

```text
Работай в текущей открытой папке как в целевом проекте сайта. Пойди по адресу https://github.com/ub3dqy/seo-autopilot-codex и начни улучшение SEO этого сайта. Полностью выполни START_AUTOPILOT.md, не ограничивайся скачиванием, установкой или планом и заверши один полный безопасный SEO-checkpoint с фактическим evidence.
```

Самый однозначный вариант:

```text
Работай в текущей открытой папке как в целевом проекте сайта. Прочитай и полностью выполни официальный bootstrap-промт SEO Autopilot: https://raw.githubusercontent.com/ub3dqy/seo-autopilot-codex/main/START_AUTOPILOT.md . Не переключай target workspace на репозиторий инструмента. Заверши один полный безопасный SEO-checkpoint и выдай фактическое evidence.
```

> **Codex:** текущая открытая папка является единственным target workspace. Этот репозиторий — только источник проверенного инструмента. Выполни [START_AUTOPILOT.md](START_AUTOPILOT.md), не клонируй SEO Autopilot поверх сайта и не редактируй репозиторий инструмента вместо сайта.

Bootstrap автоматически предписывает:

- скачать Engineering Edition во временный каталог;
- проверить точный SHA-256 до распаковки и запуска;
- безопасно распаковать архив;
- запустить runtime непосредственно из поставки без постоянной установки;
- выполнить `doctor → audit → verify`;
- при чистом Git и наличии A-level кандидатов выполнить `fix`;
- оставить изменения только в отдельной локальной ветке;
- сформировать `run.json`, `report.md`, `report.html` и rollback;
- не выполнять push, merge или deployment.

Пользователю не требуется вручную указывать путь, стек или команды установки.

- [Bootstrap-промт на русском](START_AUTOPILOT.md)
- [Bootstrap prompt in English](START_AUTOPILOT_EN.md)
- [Официальный Release v1.5.1](https://github.com/ub3dqy/seo-autopilot-codex/releases/tag/v1.5.1)

## Закреплённая поставка

```text
Release:          v1.5.1
Runtime commit:   3d2cf23866b7e73a94150eb8c5fd2cd48a5b198e
Runtime Git tree: 0cc73afd79b098e5416f68d9260b277d31ede61b
Asset:            seo-autopilot-codex-engineering-v1.5.1.zip
Asset URL:        https://github.com/ub3dqy/seo-autopilot-codex/releases/download/v1.5.1/seo-autopilot-codex-engineering-v1.5.1.zip
SHA-256:          15db8eb4a8c6514dba77bcc175b05a3e31af55cfa9dccfa6fc32f89a18aaa01a
```

Engineering Edition проверена прямым запуском из распакованного ZIP:

```text
seo-autopilot --version
doctor
audit
verify run.json
```

## Ручная установка

### Windows

```text
INSTALL_WINDOWS.cmd
```

### macOS / Linux

```bash
./install.sh
```

После установки:

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

| Уровень | Поведение |
|---|---|
| `A_AUTO_FIX` | Автоматически только при механическом доказательстве точной замены |
| `B_REVIEW_REQUIRED` | Evidence и предлагаемый diff; требуется решение владельца |
| `C_ADVISORY_ONLY` | Только отчёт и рекомендации |

Модель и Codex не могут понизить B/C до A. Canonical, noindex, robots, redirects, URL/routes, schema, контент, hreflang, удаление страниц и deployment автоматически не применяются.

## Транзакционный `fix`

`fix`:

1. требует Git и чистое рабочее дерево;
2. создаёт изолированный временный worktree;
3. создаёт локальную ветку `seo-autopilot/<run-id>`;
4. применяет только A-level изменения в пределах бюджетов;
5. запускает `git diff --check`, trusted validators и повторный аудит;
6. проверяет идемпотентность;
7. при ошибке удаляет worktree и ветку;
8. при успехе оставляет локальный commit для review.

Команда не содержит push, merge, deploy или публикацию.

## Доверенные проектные проверки

Команды запускаются только из `.seo-autopilot.json` как точный argv-массив без shell и с SHA-256:

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

## Evidence

Каждый запуск создаёт:

```text
.seo-autopilot/runs/<run-id>/
  run.json
  report.md
  report.html
  state.json
```

Каждый finding содержит rule, severity, risk, confidence, path/line, evidence и status.

Инструмент не обещает ranking, indexing, traffic, rich results, AI citations, conversions или доход. Отсутствующие Search Console, Яндекс Вебмастер, CrUX, PageSpeed, analytics, SERP, backlink и rendered-browser данные отмечаются как `DEFERRED` или `NOT_RUN`.

## Локальная проверка релиза

```bash
python scripts/verify_local.py --release
```

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Документация

- [Local verification](docs/local-verification.md)
- [Security policy](SECURITY.md)
- [Safety model](docs/safety-model.md)
- [Architecture](docs/architecture.md)
- [Release process](docs/release-process.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Changelog](CHANGELOG.md)

## Лицензия

Репозиторий является proprietary/source-available согласно `LICENSE.md`.
