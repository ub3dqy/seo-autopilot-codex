#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


MAX_FILE_BYTES = 2_000_000
IGNORED_PATHS = {"scripts/secret_scan.py"}
PATTERNS = {
    "private-key": re.compile("-----BEGIN " + "(?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "github-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b"),
    "openai-key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "google-api-key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
}


def tracked_files(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip() or "git ls-files failed")
    return [root / raw.decode("utf-8", errors="surrogateescape") for raw in completed.stdout.split(b"\x00") if raw]


def scan(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in tracked_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in IGNORED_PATHS or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            continue
        payload = path.read_bytes()
        if b"\x00" in payload[:4096]:
            continue
        text = payload.decode("utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            for name, pattern in PATTERNS.items():
                match = pattern.search(line)
                if match:
                    findings.append(
                        {
                            "type": name,
                            "path": relative,
                            "line": line_number,
                            "preview": match.group(0)[:8] + "…REDACTED",
                        }
                    )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan tracked source files for high-confidence secret patterns.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    findings = scan(root)
    if args.json:
        print(json.dumps({"status": "FAIL" if findings else "PASS", "findings": findings}, indent=2, sort_keys=True))
    elif findings:
        for finding in findings:
            print(f"{finding['path']}:{finding['line']}: {finding['type']} {finding['preview']}")
    else:
        print("secret scan: PASS")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
