from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath

from .models import ScopeExclusion, ScopeExclusionStatus


_ACTIVATED = False

_STRONG_PROFILE_MARKERS = {
    "cert9.db",
    "cookies.sqlite",
    "formhistory.sqlite",
    "key4.db",
    "local state",
    "login data",
    "logins.json",
    "places.sqlite",
    "secure preferences",
    "web data",
}

_BROWSER_CONTAINER_RE = re.compile(
    r"(?:chrome|chromium|edge|firefox|playwright|browser[-_ ]?profile|user[-_ ]?data)",
    re.IGNORECASE,
)


def _parts(relative: str) -> tuple[str, ...]:
    return PurePosixPath(relative.replace("\\", "/")).parts


def _is_source_rooted(relative: str, source_roots: set[str]) -> bool:
    parts = _parts(relative)
    return bool(parts) and parts[0].casefold() in source_roots


def _marker_context(scope, marker_relative: str) -> tuple[bool, bool]:
    parts = _parts(marker_relative)
    parent = parts[:-1]
    has_profile_directory = any(scope.PROFILE_DIRECTORY_RE.match(part) for part in parent)
    has_explicit_browser_container = any(_BROWSER_CONTAINER_RE.search(part) for part in parent)
    if len(parent) >= 1 and parts[-1].casefold() == "cookies" and parent[-1].casefold() == "network":
        has_profile_directory = True
    return has_profile_directory, has_explicit_browser_container


def _qualifies_as_profile(
    *,
    profile_root: str,
    marker_names: set[str],
    has_profile_directory: bool,
    has_explicit_browser_container: bool,
    source_roots: set[str],
) -> bool:
    strong = bool(marker_names.intersection(_STRONG_PROFILE_MARKERS))
    multiple = len(marker_names) >= 2
    source_rooted = _is_source_rooted(profile_root, source_roots)

    if source_rooted:
        # Source trees may legitimately contain routes/directories named
        # cookies, history, preferences, bookmarks, or default. Require an
        # explicit browser container, or a profile-shaped path plus stronger
        # corroboration, before excluding any source subtree.
        return has_explicit_browser_container or (
            has_profile_directory and (strong or multiple)
        )

    # Outside known source roots, one distinctive database filename is enough
    # to fail closed. Ambiguous filenames still require browser-shaped context
    # or multiple independent markers.
    return strong or multiple or has_profile_directory or has_explicit_browser_container


def _metadata_exclusions(root: Path):
    """Discover scope/privacy exclusions using metadata only.

    Browser marker names are considered only when the directory entry is a
    regular file. A Next.js route directory such as ``app/cookies/`` therefore
    remains current source. Marker content is never opened, excerpted, or
    hashed by this function.
    """
    from . import scope

    configured_roots, _ = scope._load_scope_config(root)
    source_roots = {item.casefold() for item in scope.DEFAULT_SOURCE_ROOTS}
    source_roots.update(item.casefold() for item in configured_roots)

    generated: list[ScopeExclusion] = []
    non_production: list[ScopeExclusion] = []
    sensitive: list[ScopeExclusion] = []
    sensitive_roots: set[str] = set()
    candidate_paths: dict[str, set[str]] = defaultdict(set)
    candidate_names: dict[str, set[str]] = defaultdict(set)
    candidate_profile_context: dict[str, bool] = defaultdict(bool)
    candidate_container_context: dict[str, bool] = defaultdict(bool)
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
        if any(scope._under(relative_dir, sensitive_root) for sensitive_root in sensitive_roots):
            continue
        if directory != root and (directory.is_symlink() or scope._is_junction(directory)):
            continue
        try:
            with os.scandir(directory) as iterator:
                entries = list(iterator)
        except (OSError, PermissionError):
            continue
        entries_examined += len(entries)
        if entries_examined > scope.MAX_METADATA_ENTRIES:
            truncated = True
            break

        for entry in entries:
            marker = entry.name.casefold()
            if marker not in scope.BROWSER_PROFILE_FILE_MARKERS:
                continue
            try:
                is_file = entry.is_file(follow_symlinks=False)
                is_link = entry.is_symlink()
            except OSError:
                continue
            if not is_file or is_link:
                # Critical regression boundary: route/content directories named
                # cookies, history, preferences, bookmarks, etc. are not
                # browser database markers.
                continue

            marker_relative = (
                (PurePosixPath(relative_dir) / entry.name).as_posix()
                if relative_dir != "."
                else entry.name
            )
            profile_root = scope._profile_root_from_marker(marker_relative)
            if profile_root is None:
                continue
            profile_context, container_context = _marker_context(scope, marker_relative)
            candidate_paths[profile_root].add(marker_relative)
            candidate_names[profile_root].add(marker)
            candidate_profile_context[profile_root] |= profile_context
            candidate_container_context[profile_root] |= container_context

            if not _qualifies_as_profile(
                profile_root=profile_root,
                marker_names=candidate_names[profile_root],
                has_profile_directory=candidate_profile_context[profile_root],
                has_explicit_browser_container=candidate_container_context[profile_root],
                source_roots=source_roots,
            ):
                continue

            sensitive_roots.add(profile_root)
            sensitive.append(
                ScopeExclusion(
                    path=profile_root,
                    status=ScopeExclusionStatus.EXCLUDED_SENSITIVE,
                    reason="browser_profile",
                    detection_markers=sorted(candidate_paths[profile_root]),
                    files_not_read=True,
                    entries_not_read=len(entries),
                )
            )

        if any(scope._under(relative_dir, sensitive_root) for sensitive_root in sensitive_roots):
            continue

        if relative_dir != ".":
            generated_root = scope._first_named_root(relative_dir, scope.GENERATED_DIRECTORY_NAMES)
            if generated_root:
                generated.append(
                    ScopeExclusion(
                        path=generated_root,
                        status=ScopeExclusionStatus.EXCLUDED_BY_SCOPE,
                        reason="generated_or_temporary_directory",
                        files_not_read=True,
                    )
                )
            non_production_root = scope._first_named_root(
                relative_dir, scope.NON_PRODUCTION_DIRECTORY_NAMES
            )
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
            if name in scope.ALWAYS_PRUNE_DIRECTORY_NAMES:
                generated.append(
                    ScopeExclusion(
                        path=scope._relative_posix(root, child),
                        status=ScopeExclusionStatus.EXCLUDED_BY_SCOPE,
                        reason="dependency_or_vcs_directory",
                        files_not_read=True,
                    )
                )
                continue
            if scope._is_junction(child):
                generated.append(
                    ScopeExclusion(
                        path=scope._relative_posix(root, child),
                        status=ScopeExclusionStatus.EXCLUDED_BY_SCOPE,
                        reason="junction_or_reparse_point",
                        files_not_read=True,
                    )
                )
                continue
            stack.append(child)

    return (
        scope._dedupe_exclusions(generated),
        scope._dedupe_exclusions(non_production),
        scope._dedupe_exclusions(sensitive),
        entries_examined,
        truncated,
    )


def activate() -> None:
    global _ACTIVATED
    if _ACTIVATED:
        return
    from . import scope

    scope._metadata_exclusions = _metadata_exclusions
    _ACTIVATED = True
