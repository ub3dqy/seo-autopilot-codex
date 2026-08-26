from __future__ import annotations

import fnmatch
import hashlib
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


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
    "artifacts",
    "tmp",
    "temp",
    ".tmp",
    ".cache",
    ".turbo",
    "playwright-report",
    "test-results",
    "blob-report",
}

SENSITIVE_DIRECTORY_NAMES = {
    ".aws",
    ".azure",
    ".gnupg",
    ".ssh",
    "browser-profile",
    "browser-profiles",
    "chrome-profile",
    "chrome-profiles",
    "chrome-user-data",
    "chromium-profile",
    "chromium-profiles",
    "firefox-profile",
    "firefox-profiles",
    "playwright-profile",
    "playwright-profiles",
    "user data",
}

BROWSER_PROFILE_FILES = {
    "cookies",
    "cookies-journal",
    "history",
    "history-journal",
    "login data",
    "login data-journal",
    "local state",
    "web data",
    "web data-journal",
    "cookies.sqlite",
    "key4.db",
    "logins.json",
    "places.sqlite",
}

MAX_IGNORE_FILE_BYTES = 64 * 1024
MAX_IGNORE_PATTERNS = 512
MAX_SCOPE_PATHS = 100
MAX_SENSITIVE_SCAN_DIRECTORIES = 20_000


@dataclass
class FileSelection:
    files: list[Path]
    candidate_files_seen: int
    ignored_file_count: int
    pruned_directories: list[str] = field(default_factory=list)
    sensitive_paths: list[str] = field(default_factory=list)
    ignore_file: str | None = None
    ignore_patterns: list[str] = field(default_factory=list)
    gitignore_applied: bool = False

    def summary(self) -> dict[str, object]:
        return {
            "candidate_files_seen": self.candidate_files_seen,
            "selected_files": len(self.files),
            "ignored_file_count": self.ignored_file_count,
            "pruned_directory_count": len(self.pruned_directories),
            "pruned_directories": self.pruned_directories[:MAX_SCOPE_PATHS],
            "sensitive_paths": self.sensitive_paths[:MAX_SCOPE_PATHS],
            "ignore_file": self.ignore_file,
            "ignore_patterns": self.ignore_patterns,
            "gitignore_applied": self.gitignore_applied,
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


def _normalize_relative(path: Path | str) -> str:
    if isinstance(path, Path):
        value = path.as_posix()
    else:
        value = str(path).replace("\\", "/")
    return value.lstrip("./")


def _read_ignore_patterns(root: Path) -> tuple[Path | None, list[str]]:
    path = root / ".seo-autopilotignore"
    if not path.is_file() or path.is_symlink():
        return None, []
    try:
        if path.stat().st_size > MAX_IGNORE_FILE_BYTES:
            return path, []
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return path, []
    patterns: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "\x00" in line or len(line) > 512:
            continue
        patterns.append(line.replace("\\", "/"))
        if len(patterns) >= MAX_IGNORE_PATTERNS:
            break
    return path, patterns


def _pattern_matches(relative: str, pattern: str, *, is_dir: bool = False) -> bool:
    negated = pattern.startswith("!")
    if negated:
        pattern = pattern[1:]
    pattern = pattern.strip()
    if not pattern:
        return False
    anchored = pattern.startswith("/")
    pattern = pattern.lstrip("/")
    directory_pattern = pattern.endswith("/")
    pattern = pattern.rstrip("/")
    if not pattern:
        return False
    candidates = [relative]
    if not anchored:
        parts = relative.split("/")
        candidates.extend("/".join(parts[index:]) for index in range(1, len(parts)))
    for candidate in candidates:
        if directory_pattern:
            if candidate == pattern or candidate.startswith(pattern + "/"):
                return True
            if fnmatch.fnmatchcase(candidate, pattern + "/**"):
                return True
        elif fnmatch.fnmatchcase(candidate, pattern) or PurePosixPath(candidate).match(pattern):
            return True
    return False


def _default_ignored(relative: str) -> bool:
    ignored_names = {value.casefold() for value in IGNORED_DIRECTORIES}
    sensitive_names = {value.casefold() for value in SENSITIVE_DIRECTORY_NAMES}
    return any(
        part.casefold() in ignored_names or part.casefold() in sensitive_names
        for part in relative.split("/")
        if part
    )


def _ignored_by_patterns(relative: str, patterns: Sequence[str], *, is_dir: bool = False) -> bool:
    ignored = _default_ignored(relative)
    for pattern in patterns:
        if _pattern_matches(relative, pattern, is_dir=is_dir):
            ignored = not pattern.startswith("!")
    return ignored


def _may_reinclude_directory(relative: str, patterns: Sequence[str]) -> bool:
    prefix = relative.rstrip("/") + "/"
    for pattern in patterns:
        if not pattern.startswith("!"):
            continue
        candidate = pattern[1:].lstrip("/")
        if candidate.startswith(prefix) or candidate == relative:
            return True
    return False


def _git_visible_paths(root: Path) -> set[str] | None:
    if shutil.which("git") is None or not (root / ".git").exists():
        return None
    try:
        completed = run_process(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if completed.returncode != 0:
        return None
    return {
        _normalize_relative(value)
        for value in completed.stdout.split("\x00")
        if value
    }


def _looks_like_profile_directory(name: str) -> bool:
    lowered = name.casefold()
    return (
        lowered in SENSITIVE_DIRECTORY_NAMES
        or (
            "profile" in lowered
            and any(token in lowered for token in ("chrome", "chromium", "browser", "firefox", "playwright"))
        )
        or (
            "user" in lowered
            and "data" in lowered
            and any(token in lowered for token in ("chrome", "chromium", "browser"))
        )
    )


def discover_sensitive_paths(root: Path) -> list[str]:
    root = root.resolve()
    found: set[str] = set()
    visited = 0
    hard_prune = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", ".next", ".nuxt", ".output"}
    for current_name, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
        visited += 1
        if visited > MAX_SENSITIVE_SCAN_DIRECTORIES:
            break
        current = Path(current_name)
        try:
            relative = current.relative_to(root)
        except ValueError:
            directory_names[:] = []
            continue
        if any(part.casefold() in hard_prune for part in relative.parts):
            directory_names[:] = []
            continue
        directory_names[:] = [name for name in directory_names if name.casefold() not in hard_prune]
        lowered_files = {name.casefold() for name in file_names}
        lowered_dirs = {name.casefold() for name in directory_names}
        current_lower = current.name.casefold()
        marker_count = len(lowered_files.intersection(BROWSER_PROFILE_FILES))
        chrome_root = "local state" in lowered_files and any(
            name == "default" or name.startswith("profile ") for name in lowered_dirs
        )
        chrome_profile = (
            current_lower == "default"
            or current_lower.startswith("profile ")
            or _looks_like_profile_directory(current.name)
        ) and marker_count >= 2
        firefox_profile = {"cookies.sqlite", "places.sqlite"}.issubset(lowered_files) or (
            "cookies.sqlite" in lowered_files and ({"logins.json", "key4.db"} & lowered_files)
        )
        if (
            chrome_root
            or chrome_profile
            or firefox_profile
            or (_looks_like_profile_directory(current.name) and marker_count >= 1)
        ):
            location = relative.as_posix() or "."
            found.add(location)
            directory_names[:] = []
    return sorted(found)


def select_files(root: Path, suffixes: tuple[str, ...]) -> FileSelection:
    root = root.resolve()
    ignore_path, patterns = _read_ignore_patterns(root)
    git_visible = _git_visible_paths(root)
    files: list[Path] = []
    pruned: set[str] = set()
    candidate_files_seen = 0
    ignored_file_count = 0
    normalized_suffixes = tuple(value.casefold() for value in suffixes)

    for current_name, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_name)
        try:
            current_relative = current.relative_to(root)
        except ValueError:
            directory_names[:] = []
            continue
        kept_directories: list[str] = []
        for name in directory_names:
            candidate = current_relative / name
            relative = _normalize_relative(candidate)
            if _ignored_by_patterns(relative, patterns, is_dir=True) and not _may_reinclude_directory(relative, patterns):
                pruned.add(relative)
                continue
            path = current / name
            if path.is_symlink():
                pruned.add(relative)
                continue
            kept_directories.append(name)
        directory_names[:] = kept_directories

        for name in file_names:
            path = current / name
            if path.suffix.casefold() not in normalized_suffixes:
                continue
            candidate_files_seen += 1
            try:
                relative_path = path.relative_to(root)
            except ValueError:
                ignored_file_count += 1
                continue
            relative = _normalize_relative(relative_path)
            if path.is_symlink():
                ignored_file_count += 1
                continue
            if _ignored_by_patterns(relative, patterns):
                ignored_file_count += 1
                continue
            if git_visible is not None and relative not in git_visible:
                ignored_file_count += 1
                continue
            if not path.is_file():
                ignored_file_count += 1
                continue
            files.append(path)

    return FileSelection(
        files=sorted(files),
        candidate_files_seen=candidate_files_seen,
        ignored_file_count=ignored_file_count,
        pruned_directories=sorted(pruned),
        sensitive_paths=discover_sensitive_paths(root),
        ignore_file=ignore_path.relative_to(root).as_posix() if ignore_path else None,
        ignore_patterns=patterns,
        gitignore_applied=git_visible is not None,
    )


def iter_files(root: Path, suffixes: tuple[str, ...]) -> Iterable[Path]:
    yield from select_files(root, suffixes).files
