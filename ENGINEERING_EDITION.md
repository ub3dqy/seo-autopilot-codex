# SEO Autopilot — Engineering Edition

Engineering Edition содержит канонические исходники, тесты, schemas, policy packs, release tooling и документацию.

## v1.5.2 architecture boundary

Основной audit path состоит из:

```text
scope.py
  → SOURCE_FIRST candidate plan
  → generated/non-production exclusions
  → metadata-only sensitive profile detection
  → static engine + framework adapter
  → structured audit_scope/evidence classes
  → transaction eligibility
```

Hard privacy exclusions применяются до чтения содержимого. A-level candidates допускаются только из `CURRENT_SOURCE`. Next.js adapter выпускает только B/C findings.

## Локальная проверка

Обязательный release gate:

```bash
python scripts/verify_local.py --release
```

Windows:

```text
VERIFY_LOCAL_WINDOWS.cmd --release
```

Gate выполняет:

- compile/import checks;
- unit, adversarial, transaction, rollback и idempotency tests;
- AIRSYS-shaped `artifacts/**`/`tmp/**`/browser-profile regression;
- schema/report validation;
- tracked-source secret scan;
- dependency-free User Edition install lifecycle;
- direct-from-ZIP version tests;
- две детерминированные сборки;
- SBOM, SHA-256 и release verification;
- post-build generated-tree verification.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Сборка

```bash
python prepare_editions.py --build-zips
python scripts/verify_release.py dist
```

Версия читается только из `VERSION`. Output-каталоги управляются marker-файлами, атомарно заменяются и не перезаписываются при неизвестных изменениях.

## Документация

- [Audit scope and privacy boundary](docs/audit-scope.md)
- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [Local verification](docs/local-verification.md)
- [Release process](docs/release-process.md)
- [Safety model](docs/safety-model.md)
- [Security](SECURITY.md)
