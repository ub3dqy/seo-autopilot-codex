# SEO Autopilot for OpenAI Codex v1.5.1

## Bootstrap runtime hotfix

- Исправлено определение версии при прямом запуске из распакованной User или Engineering Edition через `PYTHONPATH=<edition>/src`.
- Runtime теперь читает и валидирует корневой `VERSION`, когда package metadata ещё не установлены.
- Команда `<python> -S -m seo_autopilot --version` из проверенной распакованной поставки возвращает `seo-autopilot 1.5.1`, а не `0+unknown`.
- User Edition теперь содержит `release-manifest.json`, поэтому policy pack, schemas и source root доступны при прямом временном запуске без постоянной установки.
- Добавлен регрессионный тест, точно воспроизводящий bootstrap-сценарий без site-packages.

## Safety and compatibility

- Version gate остаётся обязательным: несовпадающая или неопределённая версия по-прежнему блокирует mutation.
- Архив должен пройти SHA-256 и безопасную распаковку до импорта runtime.
- Dirty working tree не очищается через reset, clean или stash.
- `doctor` и `audit` остаются read-only; `fix` допускается только для чистого Git-репозитория и механически доказанных A-level исправлений.
- Push, merge и deployment не выполняются автоматически.

## Verification

Обязательный gate выполняется локально:

```bash
python scripts/verify_local.py --release
```

Он включает компиляцию, source-layout version smoke test, unit/adversarial/transaction tests, prompt-injection boundary, rollback, идемпотентность, secret scan, чистую установку, две детерминированные сборки, SBOM и проверку release assets.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Compatibility

v1.5.1 использует Python 3.10 или новее. v1.5.0 остаётся историческим релизом, но его direct-from-archive bootstrap не следует использовать из-за подтверждённого `0+unknown` version-gate defect.
