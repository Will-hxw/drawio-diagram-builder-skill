#!/usr/bin/env python3
"""Sanity-check editable .drawio XML files."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate basic .drawio XML integrity.")
    parser.add_argument("drawio", type=Path, help="Path to .drawio file.")
    parser.add_argument("--allow-raster", action="store_true", help="Allow embedded raster images.")
    parser.add_argument("--expect-no-caption", action="store_true", help="Fail if common figure captions are found.")
    args = parser.parse_args()

    path = args.drawio.resolve()
    if not path.exists():
        print(f"ERROR: missing file: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        print(f"ERROR: XML parse failed: {exc}", file=sys.stderr)
        return 2

    diagrams = root.findall(".//diagram")
    cells = root.findall(".//mxCell")
    raster_markers = ("data:image/png", "data:image/jpeg", "data:image/jpg", "data:image/webp")
    has_raster = any(marker in text for marker in raster_markers)
    has_caption = "Figure " in text or "Fig. " in text or "Figure:" in text

    errors: list[str] = []
    if root.tag != "mxfile":
        errors.append(f"root tag is {root.tag!r}, expected 'mxfile'")
    if not diagrams:
        errors.append("no diagram pages found")
    if not cells:
        errors.append("no mxCell elements found")
    if has_raster and not args.allow_raster:
        errors.append("embedded raster image found; final editable diagrams should avoid this unless explicitly allowed")
    if has_caption and args.expect_no_caption:
        errors.append("caption-like text found")

    print(f"file: {path}")
    print(f"pages: {len(diagrams)}")
    print(f"cells: {len(cells)}")
    print(f"embedded_raster: {has_raster}")
    print(f"caption_like_text: {has_caption}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
