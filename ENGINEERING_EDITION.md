# SEO Autopilot — Engineering Edition

Engineering Edition содержит канонический source tree, Codex skill, versioned policy packs, JSON Schema, deterministic engine, transaction layer, tests, docs и локальные verification/release tools.

GitHub Actions не используется и не требуется.

## Development gate

Windows:

```text
VERIFY_LOCAL_WINDOWS.cmd
```

macOS / Linux:

```bash
./verify_local.sh
```

Прямой эквивалент:

```bash
python scripts/verify_local.py
```

Evidence сохраняется в `local-verification/latest.json` и `latest.log`.

## Build and release gates

Собрать и проверить обе редакции:

```bash
python scripts/verify_local.py --build
```

Официальный release gate из чистого Git checkout:

```bash
python scripts/verify_local.py --release
```

`VERSION` является единственным version literal. `release-manifest.json` задаёт состав редакций и шаблоны имён. Output-каталоги имеют проверяемый marker и не заменяются при локальном изменении без явного решения.

Локальный release gate выполняет тесты, две детерминированные сборки, сравнение SHA-256, SPDX SBOM и проверку release assets. Live Codex canary запускается отдельно локально и не подменяется статическими тестами.

## Safety invariants

- no shell interpolation;
- no implicit project commands;
- exact argv SHA-256 trust;
- clean-tree gate for official release evidence;
- isolated worktree and owned local branch;
- disabled Git hooks;
- A/B/C risk floor;
- bounded writes;
- validation plus second-run idempotency;
- rollback on failure;
- no push, merge, deploy or remote mutation.

See `docs/architecture.md`, `docs/safety-model.md`, `docs/local-verification.md`, `SECURITY.md` and `CONTRIBUTING.md` before changing mutation behavior.
