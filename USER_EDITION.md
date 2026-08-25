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
Проведи SEO-аудит этого сайта. Сначала только аудит и отчёт, без изменений.
```

Для детерминированной проверки без Codex:

```bash
seo-autopilot doctor . --json
seo-autopilot audit .
```

`fix` применяет только механически доказанные A-level изменения в отдельной локальной Git-ветке. Он не отправляет, не объединяет и не развёртывает код.

```bash
seo-autopilot fix .
```

Результаты находятся в `.seo-autopilot/runs/<run-id>/`. Перед передачей отчёта третьим лицам проверьте содержащиеся в нём excerpts.

## Проверка поставки

Engineering Edition и исходный репозиторий используют единый обязательный локальный gate:

```bash
python scripts/verify_local.py
```

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Ограничения

Canonical, noindex, robots, redirects, routes, schema, content, URL, удаление страниц и deployment не исправляются автоматически. Рейтинг, индексация, трафик и rich results не гарантируются.
