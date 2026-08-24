# SEO Autopilot for OpenAI Codex v1.5.0

## Trust and transparency

- Канонические исходники, skill, policies, schemas, tests и workflows опубликованы обычными просматриваемыми файлами.
- Непрозрачный base64/xz source bundle удалён из source tree.
- User и Engineering Edition собираются непосредственно из текущего commit.
- `VERSION` стал единственным источником номера версии.
- Output-каталоги имеют marker, проверку локальных изменений и атомарную замену.
- Детерминированные ZIP получают вычисленные SHA-256; tag-release добавляет SPDX SBOM и GitHub provenance attestation.

## Real Autopilot safety

- Добавлены `doctor`, `audit`, `fix`, `rollback`, `verify`, `install-skill` и `command-hash`.
- Введены уровни `A_AUTO_FIX`, `B_REVIEW_REQUIRED`, `C_ADVISORY_ONLY`.
- Автоматическое применение первоначально ограничено отсутствующими width/height, которые доказаны заголовком локального PNG/JPEG/GIF/WebP.
- Fix mode работает в изолированном Git worktree, отключает hooks, создаёт локальную ветку и не реализует push/merge/deploy.
- Проектные команды разрешены только как точный argv без shell и с подтверждённым SHA-256.
- Добавлены бюджеты, `git diff --check`, trusted validators, повторный аудит и rollback.

## Evidence and reports

- Каждый finding содержит ID, rule, severity, risk, confidence, path/line, evidence и status.
- Каждый запуск формирует `run.json`, `report.md`, `report.html` и transaction state.
- Policy pack версионирован и ссылается на первичные источники.
- Не обещаются ranking, indexing, traffic или rich-result outcomes.

## Verification

- Cross-platform CI: Windows, macOS, Linux; Python 3.10, 3.12, 3.13.
- Deterministic unit, transaction, rollback, prompt-injection, budget, reporting, release and idempotency tests.
- CodeQL, dependency review and tracked-source secret scan.
- Live Codex canary вынесен в отдельный manual workflow. До фактического успешного запуска его статус остаётся `NOT_RUN`, а не PASS.

## Compatibility

v1.5.0 использует Python 3.10 или новее. Старые v1.4.0 release assets не переписываются; новый release должен публиковаться отдельным immutable tag после прохождения gates.
