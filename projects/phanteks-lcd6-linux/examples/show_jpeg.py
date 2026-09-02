#!/usr/bin/env python3
"""Display a 1480x720 JPEG on a Phanteks LCD6-HD."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from phanteks_lcd6 import show_jpeg  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jpeg", type=Path, help="1480x720 JPEG to display")
    parser.add_argument(
        "--brightness",
        type=int,
        default=70,
        help="LCD brightness, 0-100 (default: 70, the validated Linux test value)",
    )
    args = parser.parse_args()

    jpeg = args.jpeg.read_bytes()
    show_jpeg(jpeg, brightness=args.brightness)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
