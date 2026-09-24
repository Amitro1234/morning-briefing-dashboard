#!/usr/bin/env python3
"""Build morning-briefing.skill from the canonical skill directory."""

from __future__ import annotations

import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "morning-briefing"
OUTPUT = ROOT / "morning-briefing.skill"
INCLUDE = (
    "SKILL.md",
    "scripts/render_board.py",
)


def main() -> None:
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in INCLUDE:
            path = SOURCE / relative
            data = path.read_bytes().replace(b"\r\n", b"\n")
            archive.writestr(f"morning-briefing/{relative.replace(chr(92), '/')}", data)
    print(OUTPUT)


if __name__ == "__main__":
    main()
