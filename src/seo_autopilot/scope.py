from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from .models import AuditScope, ScopeExclusion, ScopeExclusionStatus
from .utils import run_process


STATIC_SUFFIXES = {".html", ".htm"}
FRAMEWORK_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
RELEVANT_SUFFIXES = STATIC_SUFFIXES | FRAMEWORK_SUFFIXES

DEFAULT_SOURCE_ROOTS = (
    "src",
    "app",
    "pages",
    "public",
    "static",
    "content",
    "components",
    "widgets",
    "scripts",
    "lib",
    "server",
    "client",
)

GENERATED_DIRECTORY_NAMES = {
    ".cache",
    ".next",
    ".nuxt",
    ".output",
    ".parcel-cache",
    ".seo-autopilot",
    ".turbo",
    "artifacts",
    "archive",
    "archives",
    "backup",
    "backups",
    "build",
    "coverage",
    "dist",
    "generated",
    "logs",
    "out",
    "output",
    "playwright-report",
    "reports",
    "runtime-artifacts",
    "snapshot",
    "snapshots",
    "storybook-static",
    "temp",
    "tmp",
    "test-results",
}

NON_PRODUCTION_DIRECTORY_NAMES = {
    "__fixtures__",
    "__mocks__",
    "__snapshots__",
    "__tests__",
    "demo",
    "demos",
    "example",
    "examples",
    "fixture",
    "fixtures",
    "sample",
    "samples",
    "test",
    "tests",
}

ALWAYS_PRUNE_DIRECTORY_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
}

BROWSER_PROFILE_FILE_MARKERS = {
    "bookmarks",
    "cert9.db",
    "cookies",
    "cookies.sqlite",
    "favicons",
    "formhistory.sqlite",
    "history",
    "key4.db",
    "local state",
    "login data",
    "logins.json",
    "places.sqlite",
    "preferences",
    "secure preferences",
    "transportsecurity",
    "visited links",
    "web data",
}

PROFILE_DIRECTORY_RE = re.compile(
    r"^(?:default|guest profile|profile \d+|user data|user-data-dir|browser-profile(?:-\w+)?|playwright-profile(?:-\w+)?)$",
    re.IGNORECASE,
)

ROOT_SOURCE_FILENAMES = {
    "index.html",
    "robots.ts",
    "robots.js",
    "sitemap.ts",
    "sitemap.js",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
}

MAX_METADATA_ENTRIES = 250_000
MAX_EXCLUSION_RECORDS = 500


@dataclass
class ScopePlan:
    manifest: AuditScope
    static_paths: list[Path]
    framework_paths: list[Path]
    auto_fix_eligible: set[str]

    def is_auto_fix_eligible(self, relative: str) -> bool:
        return relative.replace("\\", "/") in self.auto_fix_eligible


def _relative_posix(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _first_named_root(relative: str, names: set[str]) -> str | None:
    parts = PurePosixPath(relative.replace("\\", "/")).parts
    for index, part in enumerate(parts):
        if part.casefold() in names:
            return PurePosixPath(*parts[: index + 1]).as_posix()
    return None


def _under(relative: str, root: str) -> bool:
    rel = PurePosixPath(relative.replace("\\", "/"))
    candidate = PurePosixPath(root.replace("\\", "/"))
    return rel == candidate or candidate in rel.parents


def _dedupe_exclusions(records: Iterable[ScopeExclusion]) -> list[ScopeExclusion]:
    selected: dict[tuple[str, str], ScopeExclusion] = {}
    for item in records:
        key = (item.status.value, item.path.casefold())
        previous = selected.get(key)
        if previous is None:
            selected[key] = item
            continue
        markers = sorted(set(previous.detection_markers) | set(item.detection_markers))
        entries = None
        if previous.entries_not_read is not None or item.entries_not_read is not None:
            entries = max(previous.entries_not_read or 0, item.entries_not_read or 0)
        selected[key] = ScopeExclusion(
            path=previous.path,
            status=previous.status,
            reason=previous.reason,
            detection_markers=markers,
            files_not_read=True,
            entries_not_read=entries,
        )
    ordered = sorted(selected.values(), key=lambda item: (item.status.value, item.path.casefold()))
    return ordered[:MAX_EXCLUSION_RECORDS]


def _is_junction(path: Path) -> bool:
    checker = getattr(os.path, "isjunction", None)
    if checker is None:
        return False
    try:
        return bool(checker(path))
    except OSError:
        return True


def _profile_root_from_marker(relative: str) -> str | None:
    parts = list(PurePosixPath(relative.replace("\\", "/")).parts)
    if not parts:
        return None
    marker = parts[-1].casefold()
    if marker not in BROWSER_PROFILE_FILE_MARKERS:
        return None
    parent = parts[:-1]
    if marker == "cookies" and parent and parent[-1].casefold() == "network":
        parent = parent[:-1]
    if marker == "local state":
        return PurePosixPath(*parent).as_posix() if parent else "."
    for index in range(len(parent) - 1, -1, -1):
        if PROFILE_DIRECTORY_RE.match(parent[index]):
            return PurePosixPath(*parent[: index + 1]).as_posix()
    return PurePosixPath(*parent).as_posix() if parent else "."


def _metadata_exclusions(root: Path) -> tuple[list[ScopeExclusion], list[ScopeExclusion], list[ScopeExclusion], int, bool]:
    generated: list[ScopeExclusion] = []
    non_production: list[ScopeExclusion] = []
    sensitive: list[ScopeExclusion] = []
    sensitive_roots: set[str] = set()
    entries_examined = 0
    truncated = False
    stack: list[Path] = [root]

    while stack:
        directory = stack.pop()
        try:
            relative_dir = directory.resolve().relative_to(root.resolve()).as_posix()
        except (OSError, ValueError):
            continue
        relative_dir = "." if relative_dir == "." else relative_dir
        if any(_under(relative_dir, sensitive_root) for sensitive_root in sensitive_roots):
            continue
        if directory != root and (directory.is_symlink() or _is_junction(directory)):
            continue
        try:
            with os.scandir(directory) as iterator:
                entries = list(iterator)
        except (OSError, PermissionError):
            continue
        entries_examined += len(entries)
        if entries_examined > MAX_METADATA_ENTRIES:
            truncated = True
            break

        for entry in entries:
            marker = entry.name.casefold()
            if marker not in BROWSER_PROFILE_FILE_MARKERS:
                continue
            marker_relative = (PurePosixPath(relative_dir) / entry.name).as_posix() if relative_dir != "." else entry.name
            profile_root = _profile_root_from_marker(marker_relative)
            if profile_root is None:
                continue
            sensitive_roots.add(profile_root)
            sensitive.append(
                ScopeExclusion(
                    path=profile_root,
                    status=ScopeExclusionStatus.EXCLUDED_SENSITIVE,
                    reason="browser_profile",
                    detection_markers=[marker_relative],
                    files_not_read=True,
                    entries_not_read=len(entries),
                )
            )
        if any(_under(relative_dir, sensitive_root) for sensitive_root in sensitive_roots):
            continue

        if relative_dir != ".":
            generated_root = _first_named_root(relative_dir, GENERATED_DIRECTORY_NAMES)
            if generated_root:
                generated.append(
                    ScopeExclusion(
                        path=generated_root,
                        status=ScopeExclusionStatus.EXCLUDED_BY_SCOPE,
                        reason="generated_or_temporary_directory",
                        files_not_read=True,
                    )
                )
            non_production_root = _first_named_root(relative_dir, NON_PRODUCTION_DIRECTORY_NAMES)
            if non_production_root:
                non_production.append(
                    ScopeExclusion(
                        path=non_production_root,
                        status=ScopeExclusionStatus.EXCLUDED_BY_SCOPE,
                        reason="non_production_fixture_or_example",
                        files_not_read=True,
                    )
                )

        for entry in entries:
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
                is_link = entry.is_symlink()
            except OSError:
                continue
            if not is_dir or is_link:
                continue
            name = entry.name.casefold()
            child = Path(entry.path)
            if name in ALWAYS_PRUNE_DIRECTORY_NAMES:
                generated.append(
                    ScopeExclusion(
                        path=_relative_posix(root, child),
                        status=ScopeExclusionStatus.EXCLUDED_BY_SCOPE,
                        reason="dependency_or_vcs_directory",
                        files_not_read=True,
                    )
                )
                continue
            if _is_junction(child):
                generated.append(
                    ScopeExclusion(
                        path=_relative_posix(root, child),
                        status=ScopeExclusionStatus.EXCLUDED_BY_SCOPE,
                        reason="junction_or_reparse_point",
                        files_not_read=True,
                    )
                )
                continue
            stack.append(child)

    return (
        _dedupe_exclusions(generated),
        _dedupe_exclusions(non_production),
        _dedupe_exclusions(sensitive),
        entries_examined,
        truncated,
    )


def _git_paths(root: Path, argv: list[str]) -> list[str] | None:
    result = run_process(["git", *argv], cwd=root, timeout=120)
    if result.returncode != 0:
        return None
    return sorted({item.replace("\\", "/") for item in result.stdout.split("\0") if item})


def _load_scope_config(root: Path) -> tuple[list[str], set[str]]:
    path = root / ".seo-autopilot.json"
    if not path.is_file() or path.stat().st_size > 1_000_000:
        return [], set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [], set()
    scope = payload.get("scope") if isinstance(payload, dict) else None
    if not isinstance(scope, dict):
        return [], set()
    includes: list[str] = []
    excludes: set[str] = set()
    for raw in scope.get("include_roots", []):
        if not isinstance(raw, str) or not raw.strip():
            continue
        value = PurePosixPath(raw.replace("\\", "/"))
        if value.is_absolute() or ".." in value.parts:
            continue
        includes.append(value.as_posix().strip("/"))
    for raw in scope.get("exclude_directories", []):
        if not isinstance(raw, str) or not raw.strip():
            continue
        value = PurePosixPath(raw.replace("\\", "/"))
        if value.is_absolute() or ".." in value.parts:
            continue
        excludes.add(value.as_posix().strip("/").casefold())
    return sorted(set(includes)), excludes


def _is_source_rooted(relative: str, roots: set[str]) -> bool:
    parts = PurePosixPath(relative.replace("\\", "/")).parts
    if len(parts) == 1:
        return parts[0].casefold() in ROOT_SOURCE_FILENAMES or Path(parts[0]).suffix.lower() in STATIC_SUFFIXES
    return bool(parts) and parts[0].casefold() in roots


def _custom_exclusion_root(relative: str, custom: set[str]) -> str | None:
    lowered = relative.replace("\\", "/").casefold().strip("/")
    for item in sorted(custom):
        if lowered == item or lowered.startswith(item + "/"):
            return item
    return None


def _candidate_classification(relative: str, *, sensitive_roots: set[str], custom_exclusions: set[str]) -> tuple[str, str | None]:
    for sensitive in sensitive_roots:
        if _under(relative, sensitive):
            return "SENSITIVE", sensitive
    custom = _custom_exclusion_root(relative, custom_exclusions)
    if custom:
        return "OUT_OF_SCOPE", custom
    generated = _first_named_root(relative, GENERATED_DIRECTORY_NAMES)
    if generated:
        return "GENERATED", generated
    non_production = _first_named_root(relative, NON_PRODUCTION_DIRECTORY_NAMES)
    if non_production:
        return "NON_PRODUCTION", non_production
    return "CURRENT_SOURCE", None


def _filesystem_candidates(root: Path, roots: set[str]) -> list[str]:
    candidates: set[str] = set()
    for entry in root.iterdir():
        if entry.is_file() and (entry.suffix.lower() in RELEVANT_SUFFIXES or entry.name.casefold() in ROOT_SOURCE_FILENAMES):
            candidates.add(entry.name)
    for source_root in sorted(roots):
        directory = root / source_root
        if not directory.is_dir() or directory.is_symlink() or _is_junction(directory):
            continue
        for current, directories, files in os.walk(directory, followlinks=False):
            directories[:] = [
                name
                for name in directories
                if name.casefold() not in ALWAYS_PRUNE_DIRECTORY_NAMES
                and name.casefold() not in GENERATED_DIRECTORY_NAMES
                and name.casefold() not in NON_PRODUCTION_DIRECTORY_NAMES
            ]
            current_path = Path(current)
            for filename in files:
                path = current_path / filename
                if path.suffix.lower() not in RELEVANT_SUFFIXES:
                    continue
                try:
                    candidates.add(path.resolve().relative_to(root.resolve()).as_posix())
                except (OSError, ValueError):
                    continue
    return sorted(candidates)


def build_scope(root: Path, *, stack: str = "unknown") -> ScopePlan:
    root = root.resolve()
    configured_roots, custom_exclusions = _load_scope_config(root)
    source_roots = {item.casefold() for item in DEFAULT_SOURCE_ROOTS}
    source_roots.update(item.casefold() for item in configured_roots)

    generated, non_production, sensitive, metadata_entries, truncated = _metadata_exclusions(root)
    sensitive_roots = {item.path for item in sensitive}

    tracked = _git_paths(root, ["ls-files", "-z"])
    untracked = _git_paths(root, ["ls-files", "-z", "--others", "--exclude-standard"])
    git_repository = tracked is not None and untracked is not None
    if not git_repository:
        tracked = []
        untracked = _filesystem_candidates(root, source_roots)

    static_paths: list[Path] = []
    framework_paths: list[Path] = []
    eligible: set[str] = set()
    tracked_candidates = 0
    untracked_candidates = 0
    seen: set[str] = set()

    for origin, paths in (("tracked", tracked or []), ("untracked", untracked or [])):
        for relative in paths:
            relative = relative.replace("\\", "/")
            while relative.startswith("./"):
                relative = relative[2:]
            if not relative or relative in seen:
                continue
            suffix = Path(relative).suffix.lower()
            if suffix not in RELEVANT_SUFFIXES:
                continue
            if origin == "untracked" and not _is_source_rooted(relative, source_roots):
                continue
            classification, _ = _candidate_classification(relative, sensitive_roots=sensitive_roots, custom_exclusions=custom_exclusions)
            if classification != "CURRENT_SOURCE":
                continue
            candidate = (root / relative).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                continue
            if not candidate.is_file() or candidate.is_symlink():
                continue
            seen.add(relative)
            if origin == "tracked":
                tracked_candidates += 1
            else:
                untracked_candidates += 1
            if suffix in STATIC_SUFFIXES:
                static_paths.append(candidate)
                eligible.add(relative)
            elif suffix in FRAMEWORK_SUFFIXES:
                framework_paths.append(candidate)

    existing_roots = sorted(relative for relative in set(DEFAULT_SOURCE_ROOTS) | set(configured_roots) if (root / relative).is_dir())
    manifest = AuditScope(
        mode="SOURCE_FIRST",
        git_repository=git_repository,
        source_roots=existing_roots,
        tracked_candidates=tracked_candidates,
        untracked_source_candidates=untracked_candidates,
        candidate_files=len(static_paths) + len(framework_paths),
        excluded_generated_directories=generated,
        excluded_non_production_directories=non_production,
        excluded_sensitive_directories=sensitive,
        metadata_entries_examined=metadata_entries,
        metadata_scan_truncated=truncated,
    )
    return ScopePlan(
        manifest=manifest,
        static_paths=sorted(static_paths),
        framework_paths=sorted(framework_paths),
        auto_fix_eligible=eligible,
    )
