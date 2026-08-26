# SEO Autopilot — Engineering Edition

Engineering Edition содержит канонический source tree, Codex skill, versioned policy packs, JSON Schema, deterministic engine, audit-scope layer, transaction layer, tests, docs и локальные release tools.

## Mandatory local gate

```bash
python scripts/verify_local.py --release
```

Windows:

```text
VERIFY_LOCAL_WINDOWS.cmd --release
```

Gate проверяет компиляцию, unit/adversarial/transaction tests, prompt-injection boundary, audit scope, browser-profile privacy boundary, rollback, идемпотентность, secret scan, отчёты и schema, установку User Edition, двойную детерминированную сборку, direct-from-ZIP smoke, восстановление release assets и SHA-256.

```text
GitHub Actions: BLOCKED_EXTERNAL / WAIVED_BY_OWNER
Release gate: LOCAL VERIFICATION ONLY
```

## Audit scope regression

```bash
PYTHONPATH=src python -m seo_autopilot scope /path/to/site --json
PYTHONPATH=src python -m unittest tests.test_scope tests.test_engine -v
```

Обязательные invariants:

- `artifacts/`, `tmp/`, caches, reports and build output не создают findings;
- untracked Git-ignored files не входят в scope;
- `.seo-autopilotignore` применяет ordered glob rules и `!` re-inclusion;
- browser-profile detection не открывает Cookies, History, Login Data, Web Data и аналогичные файлы;
- scope сообщает sensitive paths, selected files и pruned directories;
- framework без in-scope static HTML получает limitation, а не чистый SEO PASS;
- грязное дерево блокирует `fix`, но не read-only `scope` и `audit`.

Подробности: `docs/audit-scope.md`.

## Release build

```bash
python scripts/verify_local.py --release
python prepare_editions.py --build-zips
python scripts/verify_release.py dist
```

`VERSION` является единственным version literal. `release-manifest.json` задаёт состав редакций и шаблоны имён. Output-каталоги имеют проверяемый marker и не заменяются при локальном изменении без явного `--force`.

Релиз публикуется только после PASS локального gate. В репозитории не должно быть активных `.github/workflows/*.yml` или `.yaml`; hosted status не используется как доказательство.

## Safety invariants

- no shell interpolation;
- no implicit project commands;
- exact argv SHA-256 trust;
- deterministic audit scope before parsing;
- generated and sensitive directories excluded by default;
- clean-tree gate for mutation;
- isolated worktree and owned local branch;
- disabled Git hooks;
- A/B/C risk floor;
- bounded writes;
- validation plus second-run idempotency;
- rollback on failure;
- no push, merge, deploy or remote mutation from the product runtime.

See `docs/architecture.md`, `docs/safety-model.md`, `docs/audit-scope.md`, `docs/local-verification.md`, `SECURITY.md` and `CONTRIBUTING.md` before changing scope or mutation behavior.
