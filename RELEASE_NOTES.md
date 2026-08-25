# SEO Autopilot for OpenAI Codex v1.5.0

## Trust and transparency

- Канонические исходники, skill, policies, schemas, tests и локальные verification/release tools опубликованы обычными просматриваемыми файлами.
- Непрозрачный base64/xz source bundle удалён из source tree.
- User и Engineering Edition собираются непосредственно из текущего commit.
- `VERSION` стал единственным источником номера версии.
- Output-каталоги имеют marker, проверку локальных изменений и атомарную замену.
- Детерминированные ZIP получают вычисленные SHA-256; локальный release gate добавляет SPDX SBOM.
- GitHub Actions не используется и не является условием приёмки или релиза.

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

## Local verification

- Один локальный harness выполняет deterministic tests, source verification, secret scan, reproducibility build, SBOM и asset verification.
- Каждая проверка сохраняет `local-verification/latest.json` и `latest.log` с commit, ОС, Python, argv и return codes.
- Официальный `--release` gate требует чистый Git checkout.
- Поддержка конкретной ОС заявляется только после фактического PASS на этой ОС.
- Live Codex canary запускается отдельно локально. До фактического успешного запуска его статус остаётся `NOT_RUN`, а не PASS.

## Compatibility

v1.5.0 использует Python 3.10 или новее. Старые v1.4.0 release assets не переписываются; новый release публикуется отдельным tag после прохождения локальных gates.
