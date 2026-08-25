# SEO Autopilot for OpenAI Codex v1.5.0

## Trust and transparency

- Канонические исходники, skill, policies, schemas, tests и release tooling опубликованы обычными просматриваемыми файлами.
- Непрозрачный base64/xz source bundle исключён из канонического дерева.
- User и Engineering Edition собираются непосредственно из текущего commit.
- `VERSION` является единственным источником номера версии.
- Output-каталоги имеют marker, проверку локальных изменений и атомарную замену.
- Детерминированные ZIP получают вычисленные SHA-256 и проверяются повторной сборкой.

## Transactional Autopilot

- Добавлены `doctor`, `audit`, `fix`, `rollback`, `verify`, `install-skill` и `command-hash`.
- Введены уровни `A_AUTO_FIX`, `B_REVIEW_REQUIRED`, `C_ADVISORY_ONLY`.
- Автоматическое применение ограничено механически доказанными исправлениями; начальный адаптер добавляет отсутствующие размеры локальных PNG/JPEG/GIF/WebP.
- Fix mode работает в изолированном Git worktree, отключает hooks, создаёт локальную ветку и не реализует push/merge/deploy.
- Проектные команды разрешены только как точный argv без shell и с подтверждённым SHA-256.
- Добавлены бюджеты, `git diff --check`, trusted validators, повторный аудит, идемпотентность и rollback.

## Evidence and reports

- Каждый finding содержит ID, rule, severity, risk, confidence, path/line, evidence и status.
- Каждый запуск формирует `run.json`, `report.md`, `report.html` и transaction state.
- Policy pack версионирован и ссылается на первичные источники.
- Отчёты проходят централизованную высокоточную редакцию секретов.
- Не обещаются ranking, indexing, traffic или rich-result outcomes.

## Verification

Обязательный gate выполняется локально:

```bash
python scripts/verify_local.py
```

Он включает компиляцию, unit/adversarial/transaction tests, prompt-injection boundary, rollback, идемпотентность, secret scan, schema/report checks, чистую установку User Edition, две детерминированные сборки и проверку восстановленных релизных файлов.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

GitHub Actions не является частью release gate. В релизном дереве отсутствуют активные workflow-файлы.

## Compatibility

v1.5.0 использует Python 3.10 или новее. Старые v1.4.0 артефакты не переписываются; исправления публикуются новой версией и новым набором SHA-256.
