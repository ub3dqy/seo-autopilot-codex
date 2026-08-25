#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify release assets against SHA256SUMS and release-build.json.")
    parser.add_argument("directory", nargs="?", default="dist")
    args = parser.parse_args()
    root = Path(args.directory).resolve()
    sums_path = root / "SHA256SUMS"
    expected: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, filename = line.split(None, 1)
        expected[filename.strip().lstrip("*")] = digest.lower()
    failures = []
    for filename, digest in expected.items():
        path = root / filename
        actual = sha256(path) if path.is_file() else "MISSING"
        if actual != digest:
            failures.append(f"{filename}: expected {digest}, got {actual}")
    build = root / "release-build.json"
    if build.is_file():
        payload = json.loads(build.read_text(encoding="utf-8"))
        for artifact in payload.get("artifacts", []):
            filename = artifact["filename"]
            actual = sha256(root / filename) if (root / filename).is_file() else "MISSING"
            if actual != artifact["sha256"]:
                failures.append(f"release-build.json mismatch for {filename}")
    if failures:
        print("release verification: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"release verification: PASS ({len(expected)} assets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
