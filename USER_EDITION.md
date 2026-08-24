# SEO Autopilot — User Edition

User Edition предназначена для запуска без выбора внутренних промтов, validators или режимов агента.

## Установка

### Windows

Запустите `INSTALL_WINDOWS.cmd`.

### macOS / Linux

```bash
./install.sh
```

Установщик ставит CLI и Codex skill. После этого откройте репозиторий сайта в Codex и попросите:

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

## Ограничения

Canonical, noindex, robots, redirects, routes, schema, content, URL, удаление страниц и deployment не исправляются автоматически. Рейтинг, индексация, трафик и rich results не гарантируются.
