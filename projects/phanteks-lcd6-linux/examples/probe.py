#!/usr/bin/env python3
"""Read-only Phanteks LCD6-HD device-information probe."""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from phanteks_lcd6 import open_lcd, verify_device  # noqa: E402


def main() -> int:
    fd, path = open_lcd()
    print(f"Using {path}")
    print("Sending read-only device-information request (0x22)...")
    try:
        print(verify_device(fd))
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
