from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

from .models import ScopeExclusion, ScopeExclusionStatus


_ACTIVATED = False


def _metadata_exclusions(root: Path):
    """Metadata-only scope discovery with file-type validation for profile markers.

    Browser databases such as ``Cookies`` and ``History`` are files. Route and
    content directories with the same names are ordinary source directories and
    must never become privacy exclusions. No marker content is opened here.
    """
    from . import scope

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
                # Critical boundary: Next.js routes such as app/cookies/ and
                # app/history/ are directories, not browser databases.
                continue
            marker_relative = (
                (PurePosixPath(relative_dir) / entry.name).as_posix()
                if relative_dir != "."
                else entry.name
            )
            profile_root = scope._profile_root_from_marker(marker_relative)
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
