# SEO Autopilot — User Edition

User Edition предназначена для запуска без выбора внутренних промтов, validators или режимов агента. Установка выполняется локально стандартной библиотекой Python: pip, сеть и build backend не требуются.

## Установка

### Windows

Запустите `INSTALL_WINDOWS.cmd`.

### macOS / Linux

```bash
./install.sh
```

Установщик копирует Python-пакет в user site-packages, создаёт launcher `seo-autopilot` и устанавливает Codex skill в `CODEX_HOME/skills/seo-autopilot`. Существующий неуправляемый каталог не перезаписывается без явного `--force`.

После установки откройте репозиторий сайта в Codex и попросите провести SEO-аудит или используйте:

```bash
seo-autopilot doctor . --json
seo-autopilot audit .
```

`fix` применяет только механически доказанные A-level изменения в отдельной локальной Git-ветке. Он не отправляет, не объединяет и не развёртывает код.

```bash
seo-autopilot fix .
```

## Source-first scope

v1.5.2 анализирует актуальный source, а не каждый HTML-файл внутри workspace. Generated, temporary, archive, snapshot, fixture, example, report и build trees исключаются до чтения содержимого.

Browser profiles определяются по metadata markers и получают `EXCLUDED_SENSITIVE`. Их содержимое не открывается и не попадает в evidence. A-level исправления разрешены только для `CURRENT_SOURCE`.

Каждый запуск сохраняет scope manifest и отчёты в:

```text
.seo-autopilot/runs/<run-id>/
  run.json
  report.md
  report.html
  state.json
```

`REVIEW_REQUIRED` означает, что read-only audit завершён, но для изменения нужен review или чистый Git baseline. Это не технический failure.

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

Canonical, noindex, robots, redirects, routes, schema, content, URL, удаление страниц и deployment не исправляются автоматически. Ranking, indexing, traffic, conversions и revenue не гарантируются.
