#!/usr/bin/env python3
"""Validate replication artifact completeness and quality-gate thresholds.

Checks that required intermediate files (visual-spec, layout-grid, asset-ledger,
defect-log) exist and have substantive content. Also verifies quality-gate
thresholds from the defect-log when --require-screenshot-review is used (#2):
- defect count >= 30
- self-score TOTAL >= 40 and every dimension >= 6
- red-team findings >= 30
- screenshot is canvas-only and meets minimum resolution

Usage:
  python validate_replication_artifacts.py <workdir>
  python validate_replication_artifacts.py <workdir> --require-screenshot-review
"""

import argparse
import re
import sys
from pathlib import Path

REQUIRED = {
    "visual-spec.md": {
        "main": "# Visual Spec",
        "sections": [
            "## Source",
            "## Global Style",
            "## Regions",
            "## Text Blocks",
            "## Shapes",
            "## Connectors",
            "## Semantic Relations And Flow",
            "## Icons And Images",
        ],
    },
    "layout-grid.md": {
        "main": "# Layout Grid",
        "sections": [
            "## Canvas",
            "## Grid Lines",
            "## Region Boxes",
        ],
    },
    "asset-ledger.md": {
        "main": "# Asset Ledger",
        "sections": [
            "## Exact Assets",
            "## Editable Primitive Icons",
            "## Approximations",
            "## Missing Assets",
        ],
    },
    "defect-log.md": {
        "main": "# Defect Log",
        "sections": [
            "## Pass",
            "## Screenshot Review",
            "## Requirement And Semantic Audit",
            "## Red-Team Visual Audit",
            "## Remaining Gaps",
        ],
    },
}

CAPTURE_TYPES = [
    "full-page",
    "canvas-only",
    "deliberate-crop",
    "editor-full-canvas",
    "editor-partial",
]


def _has_real_colors(text: str) -> bool:
    """Check if hex codes in text are actual values, not placeholders (#8)."""
    # Look for hex patterns
    hex_patterns = re.findall(r'#[0-9a-fA-F]{6}', text)
    if not hex_patterns:
        return False
    # Check if they're placeholder patterns like '#ffffff' or '#______'
    placeholder_count = sum(1 for h in hex_patterns if h.lower() == '#ffffff' or h.lower() == '#000000' or '_' in h)
    if placeholder_count >= len(hex_patterns):
        return False
    return True


def _count_defects(text: str) -> int:
    """Count defect entries in the defect log.
    Looks for table rows with defect IDs or issue descriptions."""
    # Count lines that look like defect table rows: | Z2-ARR-07 | ... | or | issue | ... |
    count = 0
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and not stripped.startswith("|---") and not stripped.startswith("| #"):
            # Skip header rows and metadata rows
            if any(hdr in stripped.lower() for hdr in ("defect id", "issue", "screenshot", "evidence", "gap", "severity")):
                continue
            # Count as a defect row if it has at least 2 pipe-separated fields with content
            fields = [f.strip() for f in stripped.split("|") if f.strip()]
            if len(fields) >= 2:
                count += 1
    return count


def _parse_self_score(text: str) -> dict:
    """Extract self-score dimensions and total from defect log."""
    result = {"dimensions": {}, "total": None}
    # Look for score table: | Text readability | /10 | or | **TOTAL** | **/50** |
    score_section = False
    for line in text.split("\n"):
        stripped = line.strip()
        if "self-score" in stripped.lower() or "self score" in stripped.lower():
            score_section = True
            continue
        if score_section and stripped.startswith("|") and not stripped.startswith("|---"):
            fields = [f.strip() for f in stripped.split("|") if f.strip()]
            if len(fields) >= 2:
                dim = fields[0].lower()
                score_str = fields[-1].replace("/10", "").replace("/50", "").replace("**", "").strip()
                try:
                    score = float(score_str)
                    if "total" in dim:
                        result["total"] = score
                    else:
                        result["dimensions"][dim] = score
                except ValueError:
                    pass
        # Stop when we hit the next section
        if score_section and stripped.startswith("##"):
            score_section = False
    return result


def _count_red_team_findings(text: str) -> int:
    """Count red-team findings from the red-team audit section."""
    # Find the red-team section by heading
    section_start = text.lower().find("## red-team")
    if section_start == -1:
        return 0
    section_text = text[section_start:]
    # Find the next ## heading to bound the section
    next_heading = re.search(r'^## ', section_text[4:], re.MULTILINE)
    if next_heading:
        section_text = section_text[:next_heading.start() + 4]

    # Count finding rows in the table
    count = 0
    in_table = False
    for line in section_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|---"):
            in_table = True
            continue
        if in_table and stripped.startswith("|") and len(stripped) > 5:
            fields = [f.strip() for f in stripped.split("|") if f.strip()]
            if len(fields) >= 2:
                # Skip header row
                first_field = fields[0].lower()
                if any(h in first_field for h in ("zone", "finding", "id", "#")):
                    continue
                count += 1
    return count


def _check_screenshot_validity(text: str) -> list:
    """Check screenshot evidence meets canvas-only + resolution requirements (#18)."""
    errors = []
    lower = text.lower()

    if ".png" not in lower and ".jpg" not in lower and ".jpeg" not in lower and ".webp" not in lower:
        errors.append("defect-log.md does not reference a screenshot image")
        return errors

    # Check capture type
    if "canvas-only" not in lower:
        errors.append(
            "screenshot is not marked as canvas-only — full-browser screenshots are invalid. "
            "Crop to the canvas rectangle and record 'canvas-only' in the screenshot evidence table"
        )

    # Check for minimum dimension evidence (look for resolution mentions)
    has_resolution = bool(re.search(r'\b(1[2-9]\d{2}|[2-9]\d{3})\b', text))
    if not has_resolution:
        errors.append(
            "no pixel resolution recorded for screenshot — minimum 1280px width required. "
            "Record the screenshot dimensions in the evidence table"
        )

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate replication artifacts and quality-gate thresholds"
    )
    ap.add_argument("workdir", type=Path, help="Working directory with artifact files")
    ap.add_argument(
        "--require-screenshot-review",
        action="store_true",
        help="Also enforce quality-gate thresholds from defect-log"
    )
    args = ap.parse_args()

    workdir = args.workdir
    if not workdir.is_dir():
        print(f"ERROR: {workdir} is not a directory", file=sys.stderr)
        return 2

    errors = []

    for filename, spec in REQUIRED.items():
        path = workdir / filename
        if not path.exists():
            errors.append(f"missing {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 80:
            errors.append(f"{filename} is too short to be useful")
        if spec["main"] not in text:
            errors.append(f"{filename} missing main heading: {spec['main']}")
        for heading in spec["sections"]:
            if heading not in text:
                errors.append(f"{filename} missing section heading: {heading}")

    # --- Style extraction validation (#8) ---
    # Check style-extraction.md exists and has real hex codes (not placeholders)
    style_ext = workdir / "style-extraction.md"
    style_ext_global = workdir.parent / "references" / "style-extraction.md"
    style_ext_found = style_ext.exists() or style_ext_global.exists()

    visual_spec = workdir / "visual-spec.md"
    if visual_spec.exists():
        vtext = visual_spec.read_text(encoding="utf-8")
        if "#______" in vtext or "___pt" in vtext or "___px" in vtext:
            errors.append(
                "visual-spec.md contains placeholder values (#______, ___pt, ___px). "
                "Style extraction was not completed — fill actual hex codes and font sizes."
            )

    if args.require_screenshot_review:
        defect_log = workdir / "defect-log.md"
        if not defect_log.exists():
            errors.append("defect-log.md not found (required with --require-screenshot-review)")
        else:
            text = defect_log.read_text(encoding="utf-8").lower()

            # Check for pending entries
            if "pending" in text:
                errors.append("defect-log.md still contains pending screenshot review entries")

            # --- Screenshot validity (#18) ---
            screenshot_errors = _check_screenshot_validity(text)
            errors.extend(screenshot_errors)

            # Verify capture type is recorded
            if not any(capture_type in text for capture_type in CAPTURE_TYPES):
                errors.append(
                    "defect-log.md does not record screenshot capture type "
                    f"(expected one of: {', '.join(CAPTURE_TYPES)})"
                )

            # Read full text (not lowercase) for content parsing
            full_text = defect_log.read_text(encoding="utf-8")

            # --- Defect count enforcement (#2) ---
            defect_count = _count_defects(full_text)
            if defect_count < 30:
                errors.append(
                    f"defect-log.md only contains ~{defect_count} defects "
                    f"(minimum 30 required by quality gate)"
                )

            # --- Self-score enforcement (#2) ---
            score_data = _parse_self_score(full_text)
            total = score_data.get("total")
            dims = score_data.get("dimensions", {})
            if total is None:
                errors.append("defect-log.md does not contain a self-score TOTAL")
            else:
                if total < 40:
                    errors.append(
                        f"self-score TOTAL is {total}/50 (minimum 40 required by quality gate)"
                    )
                for dim_name, dim_score in dims.items():
                    if dim_score <= 5:
                        errors.append(
                            f"self-score dimension '{dim_name}' scored {dim_score}/10 "
                            f"(≤5 is borderline or blocked — every dimension must be ≥6 for ALLOWED)"
                        )

            # --- Red-team enforcement (#2) ---
            red_count = _count_red_team_findings(full_text)
            if red_count < 30:
                errors.append(
                    f"red-team section contains ~{red_count} countable findings "
                    f"(minimum 30 required across all 9 zones by quality gate)"
                )

            # Check semantic and red-team audit sections exist with substantial content
            semantic_start = full_text.lower().find("## requirement and semantic audit")
            red_team_start = full_text.lower().find("## red-team visual audit")
            if semantic_start != -1:
                semantic_section = full_text[semantic_start:]
                next_section = re.search(r'^## ', semantic_section[4:], re.MULTILINE)
                if next_section:
                    semantic_section = semantic_section[:next_section.start() + 4]
                if len(semantic_section.strip()) < 120:
                    errors.append("requirement and semantic audit section is too short")

            if red_team_start == -1:
                errors.append("defect-log.md missing red-team visual audit section")

    if errors:
        print(f"VALIDATION FAILED for {workdir}:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"All checks passed for {workdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
