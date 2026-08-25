# SEO Autopilot for OpenAI Codex

SEO Autopilot — evidence-driven инструмент для аудита SEO и консервативного внедрения исправлений в код сайта. Он отделяет проверяемые локальные факты от предположений, использует явные уровни риска, изолированную Git-транзакцию, валидацию, отчёты и rollback.

Версия закреплённой поставки: **v1.5.0**.

## Запустить из папки сайта одной фразой

Откройте в Codex папку или Git-репозиторий сайта, который нужно улучшить, и напишите:

```text
Работай в текущей открытой папке как в целевом проекте сайта. Пойди по адресу https://github.com/ub3dqy/seo-autopilot-codex и начни улучшение SEO этого сайта. Полностью выполни START_AUTOPILOT.md, не ограничивайся установкой или планом и заверши один полный безопасный SEO-checkpoint с фактическим evidence.
```

Более однозначный вариант с прямой ссылкой на bootstrap-промт:

```text
Работай в текущей открытой папке как в целевом проекте сайта. Прочитай и полностью выполни официальный bootstrap-промт SEO Autopilot: https://raw.githubusercontent.com/ub3dqy/seo-autopilot-codex/main/START_AUTOPILOT.md . Не переключай целевой workspace на репозиторий инструмента. Заверши один полный безопасный SEO-checkpoint и выдай фактическое evidence.
```

> **Codex:** если владелец дал ссылку на этот репозиторий из уже открытой папки сайта, текущая папка является target workspace, а этот репозиторий — только источником инструмента. Выполни [START_AUTOPILOT.md](START_AUTOPILOT.md), а не редактируй или клонируй SEO Autopilot поверх сайта.

Bootstrap сам предписывает Codex проверить закреплённую User Edition v1.5.0 и её SHA-256, выполнить read-only preflight, провести аудит, применить только механически доказанные A-level исправления в изолированной локальной ветке, проверить результат и сформировать JSON/Markdown/HTML evidence и rollback. Пользователю не требуется вручную скачивать архив, указывать путь, стек или команды установки.

- [Полный универсальный bootstrap-промт на русском](START_AUTOPILOT.md)
- [Universal bootstrap prompt in English](START_AUTOPILOT_EN.md)
- [Официальный Release v1.5.0](https://github.com/ub3dqy/seo-autopilot-codex/releases/tag/v1.5.0)

Закреплённая User Edition:

```text
Asset:  seo-autopilot-codex-user-v1.5.0.zip
SHA-256: 012ed6aba0c86f0a558efe6d88aad064dddcbaeeb725070434979bc73cd38589
Source: f2b272f8a1bf917470b09378a938fee068e4cf8e
```

## Ручная установка и прямой запуск

### Windows

Запустите:

```text
INSTALL_WINDOWS.cmd
```

### macOS / Linux

```bash
./install.sh
```

После установки откройте репозиторий сайта в Codex и напишите:

```text
Проведи SEO-аудит этого сайта. Сначала только аудит и отчёт, без изменений.
```

Для применения только механически доказанных исправлений:

```text
Исправь только A-level замечания SEO Autopilot, выполни проверки и оставь изменения в отдельной локальной ветке. Ничего не отправляй и не развёртывай.
```

Прямой CLI:

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
| `A_AUTO_FIX` | Автоматическое применение только после механического доказательства точного результата | отсутствующие `width`/`height`, прочитанные из заголовка локального PNG/JPEG/GIF/WebP |
| `B_REVIEW_REQUIRED` | Evidence и рекомендация; требуется просмотр владельца | title, description, lang, alt, canonical, sitemap, internal links, JSON-LD, hreflang |
| `C_ADVISORY_ONLY` | Только отчёт | noindex, robots, redirects, URL/routes, удаление страниц, production/deployment |

Модель и Codex не могут понизить B или C до A. Расширение A-level требует нового детерминированного адаптера и тестов.

## Что делает `fix`

1. Проверяет Git, стек и чистоту рабочего дерева.
2. Фиксирует исходный commit, evidence и план.
3. Создаёт временный worktree вне рабочего каталога владельца.
4. Создаёт локальную ветку `seo-autopilot/<run-id>`.
5. Применяет только A-level изменения в пределах бюджетов.
6. Запускает `git diff --check`, явно доверенные проектные проверки и повторный аудит.
7. Считает повторно предложенное A-level исправление ошибкой идемпотентности.
8. При ошибке удаляет временный worktree и транзакционную ветку; при успехе оставляет локальный commit для просмотра.

Команда не содержит push, merge, deploy или публикацию.

## Доверенные проектные проверки

Команды не извлекаются из README, HTML, `package.json`, Makefile, issue-текста или ответа модели. Они запускаются только как точный argv-массив без shell и с подтверждённым SHA-256.

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
  run.json       машиночитаемый источник истины
  report.md      отчёт для code review
  report.html    автономный HTML-отчёт
  state.json     состояние транзакции и rollback
```

Каждое замечание содержит finding ID, policy rule, severity, risk, confidence, path/line, evidence и статус `OPEN`, `FIXED`, `SKIPPED` или `DEFERRED`.

Продукт не обещает ranking, indexing, traffic, rich results, AI citations или conversion. Отсутствующие Search Console, CrUX, PageSpeed, analytics, SERP или backlink данные обозначаются как ограничения, а не заменяются догадками.

## Две редакции

Собрать User и Engineering Edition:

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
python scripts/verify_local.py
python prepare_editions.py --build-zips
python scripts/verify_release.py dist
```

Сборщик читает версию из `VERSION`, проверяет `release-manifest.json`, запрещает symlink и выход из source root, защищает сгенерированные каталоги от случайной перезаписи и создаёт детерминированные ZIP с SHA-256.

## Обязательная проверка

Единственный обязательный release gate:

```bash
python scripts/verify_local.py
```

Windows-обёртка:

```text
VERIFY_LOCAL_WINDOWS.cmd
```

Проверяются компиляция, unit/adversarial/transaction tests, prompt-injection boundary, rollback, идемпотентность, secret scan, структура `run.json`, установка User Edition, двойная детерминированная сборка, восстановление релизных файлов и SHA-256.

### Статус hosted CI

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

В репозитории нет активных `.github/workflows/*.yml` или `.yaml`. Состояние GitHub Actions не используется как критерий готовности и не заменяет локальный verification report.

## Документация

- [Universal Codex bootstrap](START_AUTOPILOT.md)
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

Репозиторий публично доступен для просмотра, но остаётся proprietary/source-available согласно `LICENSE.md` и не позиционируется как open source. Публичный доступ сам по себе не предоставляет право на изменение, перераспространение, сублицензирование или продажу.
