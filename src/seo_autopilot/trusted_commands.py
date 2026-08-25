from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import CheckResult, RunStatus
from .utils import run_process


class UntrustedCommandError(ValueError):
    pass


@dataclass(frozen=True)
class TrustedCommand:
    name: str
    argv: tuple[str, ...]
    sha256: str
    timeout_seconds: int = 300


def command_digest(argv: list[str] | tuple[str, ...]) -> str:
    canonical = json.dumps(list(argv), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_command(raw: Any, index: int) -> TrustedCommand:
    if not isinstance(raw, dict):
        raise UntrustedCommandError(f"checks[{index}] must be an object")
    name = raw.get("name")
    argv = raw.get("argv")
    expected = raw.get("sha256")
    timeout = raw.get("timeout_seconds", 300)
    if not isinstance(name, str) or not name.strip():
        raise UntrustedCommandError(f"checks[{index}].name must be a non-empty string")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        raise UntrustedCommandError(f"checks[{index}].argv must be a non-empty string array")
    if not isinstance(expected, str) or len(expected) != 64:
        raise UntrustedCommandError(f"checks[{index}].sha256 must be a SHA-256 hex digest")
    actual = command_digest(argv)
    if actual != expected.lower():
        raise UntrustedCommandError(
            f"checks[{index}] digest mismatch; expected {expected.lower()}, calculated {actual}"
        )
    if not isinstance(timeout, int) or timeout < 1 or timeout > 3600:
        raise UntrustedCommandError(f"checks[{index}].timeout_seconds must be between 1 and 3600")
    return TrustedCommand(name=name.strip(), argv=tuple(argv), sha256=actual, timeout_seconds=timeout)


def load_trusted_commands(root: Path) -> list[TrustedCommand]:
    config_path = root / ".seo-autopilot.json"
    if not config_path.is_file():
        return []
    if config_path.stat().st_size > 1_000_000:
        raise UntrustedCommandError(".seo-autopilot.json is unexpectedly large")
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UntrustedCommandError(f"cannot parse .seo-autopilot.json: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise UntrustedCommandError(".seo-autopilot.json must use schema_version 1")
    checks = payload.get("checks", [])
    if not isinstance(checks, list):
        raise UntrustedCommandError("checks must be an array")
    return [_validate_command(item, index) for index, item in enumerate(checks)]


def execute_trusted_commands(root: Path, commands: list[TrustedCommand]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for command in commands:
        completed = run_process(command.argv, cwd=root, timeout=command.timeout_seconds)
        status = RunStatus.PASSED if completed.returncode == 0 else RunStatus.FAILED
        results.append(
            CheckResult(
                name=command.name,
                status=status,
                command=list(command.argv),
                returncode=completed.returncode,
                stdout_tail=completed.stdout[-4000:],
                stderr_tail=completed.stderr[-4000:],
            )
        )
        if completed.returncode != 0:
            break
    return results
