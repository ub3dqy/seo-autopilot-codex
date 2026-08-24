from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("seo-autopilot-codex")
except PackageNotFoundError:  # source checkout before installation
    __version__ = "0+unknown"

__all__ = ["__version__"]
