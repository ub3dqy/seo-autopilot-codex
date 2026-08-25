# SEO Autopilot — Engineering Edition

Engineering Edition содержит канонический source tree, Codex skill, versioned policy packs, JSON Schema, deterministic engine, transaction layer, tests, docs и локальные release tools.

## Mandatory local gate

```bash
python scripts/verify_local.py
```

Windows:

```text
VERIFY_LOCAL_WINDOWS.cmd
```

Gate проверяет компиляцию, unit/adversarial/transaction tests, prompt-injection boundary, rollback, идемпотентность, secret scan, отчёты и schema, установку User Edition, двойную детерминированную сборку, восстановление release assets и SHA-256.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Release build

```bash
python scripts/verify_local.py
python prepare_editions.py --build-zips
python scripts/verify_release.py dist
```

`VERSION` является единственным version literal. `release-manifest.json` задаёт состав редакций и шаблоны имён. Output-каталоги имеют проверяемый marker и не заменяются при локальном изменении без явного `--force`.

Релиз публикуется только после PASS локального gate. В репозитории не должно быть активных `.github/workflows/*.yml` или `.yaml`; hosted status не используется как доказательство.

## Safety invariants

- no shell interpolation;
- no implicit project commands;
- exact argv SHA-256 trust;
- clean-tree gate;
- isolated worktree and owned local branch;
- disabled Git hooks;
- A/B/C risk floor;
- bounded writes;
- validation plus second-run idempotency;
- rollback on failure;
- no push, merge, deploy or remote mutation from the product runtime.

See `docs/architecture.md`, `docs/safety-model.md`, `docs/local-verification.md`, `SECURITY.md` and `CONTRIBUTING.md` before changing mutation behavior.
