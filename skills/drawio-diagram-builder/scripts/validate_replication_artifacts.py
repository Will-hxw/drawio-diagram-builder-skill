#!/usr/bin/env python3
"""Validate required intermediate files for reference-image replication."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED = {
    "visual-spec.md": [
        "# Visual Spec",
        "## Source",
        "## Global Style",
        "## Regions",
        "## Text Blocks",
        "## Shapes",
        "## Connectors",
        "## Icons And Images",
    ],
    "layout-grid.md": [
        "# Layout Grid",
        "## Canvas",
        "## Grid Lines",
        "## Region Boxes",
        "## Repeated Components",
        "## Drawing Order",
    ],
    "asset-ledger.md": [
        "# Asset Ledger",
        "## Exact Assets",
        "## Editable Primitive Icons",
        "## Approximations",
        "## Missing Assets",
    ],
    "defect-log.md": [
        "# Defect Log",
        "## Pass 0 - Initial Plan Review",
        "## Pass 1 - Screenshot Review",
        "## Red-Team Visual Audit",
        "## Remaining Gaps",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check reference-image replication planning artifacts."
    )
    parser.add_argument("workdir", type=Path, help="Directory containing visual-spec/layout-grid/asset-ledger/defect-log.")
    parser.add_argument(
        "--require-screenshot-review",
        action="store_true",
        help="Also require defect-log.md to contain a real screenshot review entry, for final handoff.",
    )
    args = parser.parse_args()

    workdir = args.workdir.resolve()
    errors: list[str] = []

    if not workdir.exists():
        print(f"ERROR: missing directory: {workdir}", file=sys.stderr)
        return 2

    for filename, headings in REQUIRED.items():
        path = workdir / filename
        if not path.exists():
            errors.append(f"missing {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 80:
            errors.append(f"{filename} is too short to be useful")
        for heading in headings:
            if heading not in text:
                errors.append(f"{filename} missing heading: {heading}")

    if args.require_screenshot_review:
        defect_log = workdir / "defect-log.md"
        if defect_log.exists():
            text = defect_log.read_text(encoding="utf-8").lower()
            if "pending" in text:
                errors.append("defect-log.md still contains pending screenshot review entries")
            if ".png" not in text and ".jpg" not in text and ".jpeg" not in text and ".webp" not in text:
                errors.append("defect-log.md does not reference a screenshot image")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"replication artifacts OK: {workdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
