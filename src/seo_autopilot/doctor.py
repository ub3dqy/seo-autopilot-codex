from __future__ import annotations

import json
import shutil
from pathlib import Path

from .models import DoctorResult, RunStatus
from .utils import run_process


def repository_root(path: Path) -> Path | None:
    if shutil.which("git") is None:
        return None
    result = run_process(["git", "rev-parse", "--show-toplevel"], cwd=path, timeout=15)
    if result.returncode != 0:
        return None
    candidate = Path(result.stdout.strip()).resolve()
    return candidate if candidate.is_dir() else None


def git_commit(root: Path) -> str | None:
    result = run_process(["git", "rev-parse", "HEAD"], cwd=root, timeout=15)
    return result.stdout.strip() if result.returncode == 0 else None


def worktree_is_clean(root: Path) -> bool:
    result = run_process(
        ["git", "status", "--porcelain=v1", "--untracked-files=normal"],
        cwd=root,
        timeout=30,
    )
    return result.returncode == 0 and not result.stdout.strip()


def detect_stack(root: Path) -> str:
    package_json = root / "package.json"
    if package_json.is_file() and package_json.stat().st_size <= 2_000_000:
        try:
            package = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            package = {}
        dependencies: dict[str, object] = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            value = package.get(key, {})
            if isinstance(value, dict):
                dependencies.update(value)
        names = set(dependencies)
        if "next" in names:
            return "nextjs"
        if "astro" in names:
            return "astro"
        if "nuxt" in names:
            return "nuxt"
        if "@sveltejs/kit" in names:
            return "sveltekit"
        if "vite" in names and ("react" in names or "@vitejs/plugin-react" in names):
            return "vite-react"
        if "vite" in names:
            return "vite"

    if (root / "manage.py").is_file():
        return "django"
    if any((root / name).is_file() for name in ("hugo.toml", "hugo.yaml", "hugo.yml")):
        return "hugo"
    if (root / "_config.yml").is_file() or (root / "_config.yaml").is_file():
        return "jekyll"
    if (root / "wp-content" / "themes").is_dir():
        return "wordpress"
    if any(root.glob("*.html")) or (root / "public" / "index.html").is_file():
        return "static-html"
    return "unknown"


def run_doctor(path: Path) -> DoctorResult:
    requested = path.resolve()
    git_available = shutil.which("git") is not None
    codex_available = shutil.which("codex") is not None
    root = repository_root(requested) if git_available else None
    if root is None:
        return DoctorResult(
            status=RunStatus.BLOCKED,
            repository_root=None,
            stack="unknown",
            git_available=git_available,
            codex_available=codex_available,
            clean_worktree=None,
            blockers=["A Git repository is required for transactional fixes."],
        )

    clean = worktree_is_clean(root)
    stack = detect_stack(root)
    limitations: list[str] = []
    blockers: list[str] = []
    status = RunStatus.READY
    if not clean:
        status = RunStatus.REVIEW_REQUIRED
        blockers.append(
            "The working tree is not clean. Audit is allowed, but fix mode is blocked to avoid omitting local changes."
        )
    if stack == "unknown":
        limitations.append("Framework adapter is unknown; only repository-level and static HTML evidence will be evaluated.")
        if status == RunStatus.READY:
            status = RunStatus.READY_WITH_LIMITATIONS
    if not codex_available:
        limitations.append("Codex CLI is not installed; deterministic local checks remain available.")
        if status == RunStatus.READY:
            status = RunStatus.READY_WITH_LIMITATIONS

    return DoctorResult(
        status=status,
        repository_root=str(root),
        stack=stack,
        git_available=git_available,
        codex_available=codex_available,
        clean_worktree=clean,
        limitations=limitations,
        blockers=blockers,
    )
