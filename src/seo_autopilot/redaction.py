from __future__ import annotations

import re
from collections.abc import Iterable


TOKEN_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(
        r"(?i)(\b(?:access[_-]?token|api[_-]?key|auth|password|secret|signature|sig|token)=)[^&\s\"'<>]+"
    ),
)


def redact_text(text: str, exact_values: Iterable[str] = ()) -> str:
    result = text
    for value in exact_values:
        if value and len(value) >= 8:
            result = result.replace(value, "[REDACTED_EXACT_SECRET]")
    for pattern in TOKEN_PATTERNS:
        if pattern.groups:
            result = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", result)
        else:
            result = pattern.sub("[REDACTED_SECRET]", result)
    return result
