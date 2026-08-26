from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .doctor import detect_stack
from .models import RunStatus
from .utils import IGNORED_DIRECTORIES, SENSITIVE_DIRECTORY_NAMES, select_files


def inspect_scope(path: Path) -> dict[str, object]:
    workspace = path.expanduser().resolve()
    if not workspace.is_dir():
        raise FileNotFoundError(f"directory not found: {workspace}")

    selection = select_files(workspace, (".html", ".htm"))
    stack = detect_stack(workspace)
    limitations: list[str] = []
    if not selection.files and stack != "static-html":
        limitations.append(
            "No in-scope static HTML was found. Framework source and rendered/live evidence require their own review."
        )
    if selection.ignore_file and not selection.ignore_patterns:
        limitations.append(
            ".seo-autopilotignore exists but supplied no usable patterns or could not be safely read."
        )

    if selection.sensitive_paths:
        status = RunStatus.REVIEW_REQUIRED
    elif limitations:
        status = RunStatus.READY_WITH_LIMITATIONS
    else:
        status = RunStatus.READY

    summary = selection.summary()
    summary["selected_paths"] = [
        item.relative_to(workspace).as_posix()
        for item in selection.files[:100]
    ]
    summary["selected_paths_truncated"] = len(selection.files) > 100

    return {
        "schema_version": 1,
        "status": status.value,
        "workspace": str(workspace),
        "stack": stack,
        "html_scope": summary,
        "privacy": {
            "sensitive_paths": selection.sensitive_paths,
            "contents_read": False,
            "action": (
                "Move browser profiles and credential-bearing directories outside the website workspace before sharing or fixing."
                if selection.sensitive_paths
                else "NONE"
            ),
        },
        "default_ignored_directories": sorted(IGNORED_DIRECTORIES),
        "default_sensitive_directory_names": sorted(SENSITIVE_DIRECTORY_NAMES),
        "limitations": limitations,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m seo_autopilot.scope",
        description="Show the deterministic HTML audit scope without reading page or browser-profile contents.",
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = inspect_scope(Path(args.path))
    except (FileNotFoundError, PermissionError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Status: {payload['status']}")
        print(f"Workspace: {payload['workspace']}")
        print(f"Stack: {payload['stack']}")
        html_scope = payload["html_scope"]
        print(f"Selected HTML files: {html_scope['selected_files']}")
        print(f"Pruned directories: {html_scope['pruned_directory_count']}")
        print(f"Git ignore applied: {html_scope['gitignore_applied']}")
        for item in payload["privacy"]["sensitive_paths"]:
            print(f"SENSITIVE_PATH_EXCLUDED: {item}")
        for item in payload["limitations"]:
            print(f"LIMITATION: {item}")

    return 1 if payload["status"] in {RunStatus.REVIEW_REQUIRED.value, RunStatus.READY_WITH_LIMITATIONS.value} else 0


if __name__ == "__main__":
    raise SystemExit(main())
