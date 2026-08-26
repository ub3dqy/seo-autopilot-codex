#!/usr/bin/env python3
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def configure_utf8_runtime() -> None:
    """Make the Windows verification harness and every child process UTF-8 safe."""
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (OSError, ValueError):
            # The stream may be provided by an embedding host. The child
            # environment is still forced to UTF-8, and verify_local.py keeps
            # the canonical UTF-8 file log.
            pass


def main() -> int:
    configure_utf8_runtime()
    if sys.argv[1:] == ["--self-test-console"]:
        print("UTF-8 console probe: \ufffd ✓")
        print("UTF-8 stderr probe: \ufffd ✓", file=sys.stderr)
        return 0

    target = Path(__file__).with_name("verify_local.py").resolve()
    if not target.is_file():
        print(f"ERROR: verification entry point is missing: {target}", file=sys.stderr)
        return 2
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
