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
        "## Remaining Gaps",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check reference-image replication planning artifacts."
    )
    parser.add_argument("workdir", type=Path, help="Directory containing visual-spec/layout-grid/asset-ledger/defect-log.")
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

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"replication artifacts OK: {workdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
