# SEO Autopilot — Engineering Edition

Engineering Edition содержит канонический source tree, Codex skill, versioned policy packs, JSON Schema, deterministic engine, transaction layer, tests, docs и release workflows.

## Development gate

```bash
python -m pip install --no-deps -e .
python -m compileall -q src scripts tests prepare_editions.py
python -m unittest discover -s tests -v
python prepare_editions.py --verify-only
python scripts/secret_scan.py
```

## Release build

```bash
python prepare_editions.py --build-zips
```

`VERSION` является единственным version literal. `release-manifest.json` задаёт состав редакций и шаблоны имён. Output-каталоги имеют проверяемый marker и не заменяются при локальном изменении без явного `--force`.

Tag workflow повторяет gates, создаёт deterministic ZIP, SPDX SBOM, SHA-256 и provenance attestation. Live Codex canary запускается отдельно вручную и не подменяется статическими тестами.

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
- no push, merge, deploy or remote mutation.

See `docs/architecture.md`, `docs/safety-model.md`, `SECURITY.md` and `CONTRIBUTING.md` before changing mutation behavior.
