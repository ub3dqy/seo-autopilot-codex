from __future__ import annotations

import sys
from typing import Sequence

from . import cli
from . import scope


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "scope":
        return scope.main(arguments[1:])
    return cli.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
