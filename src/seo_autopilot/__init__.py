from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")


def _source_tree_version() -> str | None:
    """Resolve VERSION when the package is executed directly from a release/source tree."""
    package_dir = Path(__file__).resolve().parent
    if package_dir.parent.name != "src":
        return None
    candidate = package_dir.parent.parent / "VERSION"
    try:
        value = candidate.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None
    return value if _VERSION_RE.fullmatch(value) else None


_source_version = _source_tree_version()
if _source_version is not None:
    # A verified unpacked release must identify itself, even if another version is installed globally.
    __version__ = _source_version
else:
    try:
        __version__ = version("seo-autopilot-codex")
    except PackageNotFoundError:
        __version__ = "0+unknown"

__all__ = ["__version__"]
