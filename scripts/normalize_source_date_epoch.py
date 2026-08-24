#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone


def normalize(value: str) -> int:
    value = value.strip()
    if value.isdigit():
        return int(value)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize an ISO-8601 or numeric timestamp to Unix epoch seconds.")
    parser.add_argument("value")
    args = parser.parse_args()
    print(normalize(args.value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
