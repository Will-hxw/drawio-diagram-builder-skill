from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "drawio-diagram-builder"
EXAMPLE = ROOT / "examples" / "minimal.drawio"
OUT = ROOT / "examples" / "drawio-preview.html"


REQUIRED_REFERENCE_TEXT = {
    SKILL / "SKILL.md": [
        "references/primitive-icons.md",
        "append-only",
        "do not run validators in parallel",
    ],
    SKILL / "references" / "reference-replication-protocol.md": [
        "append-only",
        "Do not run artifact validation in parallel",
        "## Screenshot Evidence",
        "editor-partial",
        "Red-Team Visual Audit",
    ],
    SKILL / "references" / "drawio-workflow.md": [
        "Canvas-only or deliberate crop capture",
        "Do not run XML generation, preview generation, screenshot capture, and artifact validation concurrently",
    ],
    SKILL / "references" / "xml-authoring.md": [
        "Safe rich-text helper for Python generators",
        "raw_html=True",
    ],
    SKILL / "references" / "primitive-icons.md": [
        "Editable Primitive Icon Recipes",
        "Document Or Text",
        "Gauge Or Uncertainty",
    ],
    SKILL / "assets" / "icons" / "ICON-MANIFEST.md": [
        "Tabler Icons",
        "MIT",
        "file-text.svg",
        "search.svg",
        "sparkles.svg",
    ],
    SKILL / "scripts" / "validate_replication_artifacts.py": [
        "CAPTURE_TYPES",
        "editor-partial",
        "final review needs full-canvas evidence",
    ],
}


def run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main() -> int:
    for path, snippets in REQUIRED_REFERENCE_TEXT.items():
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            assert snippet in text, f"{path} missing required reference text: {snippet}"

    icon_dir = SKILL / "assets" / "icons" / "tabler" / "outline"
    icons = sorted(icon_dir.glob("*.svg"))
    assert len(icons) >= 50, f"expected at least 50 bundled SVG icons, found {len(icons)}"
    assert (SKILL / "assets" / "icons" / "tabler" / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")

    run([sys.executable, str(SKILL / "scripts" / "validate_drawio.py"), str(EXAMPLE)])
    local_version = (SKILL / "VERSION").read_text(encoding="utf-8").strip()
    run(
        [
            sys.executable,
            str(SKILL / "scripts" / "check_skill_update.py"),
            "--skill-dir",
            str(SKILL),
            "--latest-version",
            local_version,
        ]
    )
    protocol_dir = ROOT / "tests" / "fixtures" / "replication-artifacts"
    run([sys.executable, str(SKILL / "scripts" / "validate_replication_artifacts.py"), str(protocol_dir)])
    run(
        [
            sys.executable,
            str(SKILL / "scripts" / "validate_replication_artifacts.py"),
            str(protocol_dir),
            "--require-screenshot-review",
        ]
    )
    run(
        [
            sys.executable,
            str(SKILL / "scripts" / "make_drawio_preview.py"),
            str(EXAMPLE),
            "--out",
            str(OUT),
        ]
    )
    html = OUT.read_text(encoding="utf-8")
    assert "https://embed.diagrams.net/" in html
    assert "requestSave" in html
    OUT.unlink()
    print("smoke test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
