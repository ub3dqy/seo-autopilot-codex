from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".seo-autopilot",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    ".output",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_environment() -> dict[str, str]:
    blocked = {
        "BASH_ENV",
        "ENV",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "NODE_OPTIONS",
        "RUBYOPT",
        "PERL5OPT",
    }
    env = {key: value for key, value in os.environ.items() if key not in blocked}
    # Preserve Git's effective system configuration. Git for Windows commonly
    # stores core.autocrlf there; disabling it after checkout can make a clean
    # CRLF worktree appear dirty. Hooks are disabled explicitly by Git callers.
    env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "HUSKY": "0",
            "PAGER": "cat",
            "GIT_PAGER": "cat",
        }
    )
    return env


def run_process(
    argv: Iterable[str],
    *,
    cwd: Path,
    timeout: int = 120,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [str(item) for item in argv]
    if not command or any("\x00" in item for item in command):
        raise ValueError("invalid command argv")
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=safe_environment(),
        shell=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=check,
    )


def iter_files(root: Path, suffixes: tuple[str, ...]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        yield path
