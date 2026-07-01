from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "drawio-diagram-builder"
EXAMPLE = ROOT / "examples" / "minimal.drawio"
OUT = ROOT / "examples" / "drawio-preview.html"


REQUIRED_REFERENCE_TEXT = {
    SKILL / "SKILL.md": [
        "references/primitive-icons.md",
        "references/self-supervision-and-intake.md",
        "references/topconf-paper-style.md",
        "assets/reference-images/",
        "append-only",
        "do not run validators in parallel",
    ],
    SKILL / "references" / "reference-replication-protocol.md": [
        "append-only",
        "Do not run artifact validation in parallel",
        "## Screenshot Evidence",
        "Requirement And Semantic Audit",
        "editor-partial",
        "Red-Team Visual Audit",
        "fan-in/fan-out",
    ],
    SKILL / "references" / "drawio-workflow.md": [
        "Canvas-only or deliberate crop capture",
        "Do not run XML generation, preview generation, screenshot capture, and artifact validation concurrently",
        "semantic audit",
        "topconf-paper-style.md",
    ],
    SKILL / "references" / "topconf-paper-style.md": [
        "Top-Conference Computer-Science Figure Style",
        "assets/reference-images/",
        "Style can be inferred; scientific content cannot.",
        "--strict",
    ],
    SKILL / "assets" / "reference-images" / "REFERENCE-IMAGES.md": [
        "topconf-memory-routing.png",
        "topconf-knowledge-mining-pipeline.png",
        "topconf-ccf-adapter-architecture.png",
        "topconf-handdrawn-rl-pipeline.png",
    ],
    SKILL / "references" / "self-supervision-and-intake.md": [
        "Diagram Brief",
        "Requirement Traceability",
        "Semantic Model",
        "Blockers That Prevent Handoff",
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
        "math-function.svg",
        "database-search.svg",
        "arrows-split.svg",
        "search.svg",
        "sparkles.svg",
    ],
    SKILL / "scripts" / "make_drawio_preview.py": [
        "DRAWIO_ORIGIN",
        "evt.origin !== DRAWIO_ORIGIN",
        "evt.source !== iframe.contentWindow",
    ],
    SKILL / "scripts" / "validate_drawio.py": [
        "--strict",
        "--json",
        "duplicate mxCell ids",
        "external image references",
        "base64 payload exceeds limit",
    ],
    SKILL / "scripts" / "validate_replication_artifacts.py": [
        "CAPTURE_TYPES",
        "editor-partial",
        "Requirement And Semantic Audit",
        "final review needs full-canvas evidence",
    ],
}


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result


def run_expect_failure(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode == 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"expected command to fail: {' '.join(command)}")
    return result


def main() -> int:
    for path, snippets in REQUIRED_REFERENCE_TEXT.items():
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            assert snippet in text, f"{path} missing required reference text: {snippet}"

    icon_dir = SKILL / "assets" / "icons" / "tabler" / "outline"
    icons = sorted(icon_dir.glob("*.svg"))
    assert len(icons) >= 90, f"expected at least 90 bundled SVG icons, found {len(icons)}"
    assert (SKILL / "assets" / "icons" / "tabler" / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")

    reference_dir = SKILL / "assets" / "reference-images"
    for filename in (
        "topconf-memory-routing.png",
        "topconf-knowledge-mining-pipeline.png",
        "topconf-ccf-adapter-architecture.png",
        "topconf-handdrawn-rl-pipeline.png",
    ):
        assert (reference_dir / filename).stat().st_size > 100_000, f"missing reference image: {filename}"

    run([sys.executable, str(SKILL / "scripts" / "validate_drawio.py"), str(EXAMPLE)])
    result = run([sys.executable, str(SKILL / "scripts" / "validate_drawio.py"), "--json", str(EXAMPLE)])
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["stats"]["duplicate_id_count"] == 0
    assert payload["stats"]["edges"] == 2

    with tempfile.TemporaryDirectory() as temp_dir:
        bad = Path(temp_dir) / "bad.drawio"
        bad.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mxfile><diagram id="bad"><mxGraphModel pageWidth="800" pageHeight="600"><root>
  <mxCell id="0" />
  <mxCell id="1" parent="0" />
  <mxCell id="dup" value="A" vertex="1" parent="1"><mxGeometry x="10" y="10" width="80" height="40" as="geometry" /></mxCell>
  <mxCell id="dup" value="B" vertex="1" parent="1"><mxGeometry x="120" y="10" width="80" height="40" as="geometry" /></mxCell>
  <mxCell id="bad_edge" value="" edge="1" parent="1" source="dup" target="missing"><mxGeometry relative="1" as="geometry" /></mxCell>
</root></mxGraphModel></diagram></mxfile>
""",
            encoding="utf-8",
        )
        failure = run_expect_failure([sys.executable, str(SKILL / "scripts" / "validate_drawio.py"), "--json", str(bad)])
        failure_payload = json.loads(failure.stdout)
        assert failure_payload["ok"] is False
        assert any("duplicate mxCell ids" in error for error in failure_payload["errors"])
        assert any("target 'missing' does not exist" in error for error in failure_payload["errors"])

        encoded_external = Path(temp_dir) / "encoded-external-image.drawio"
        encoded_external.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<mxfile><diagram id="external"><mxGraphModel pageWidth="800" pageHeight="600"><root>
  <mxCell id="0" />
  <mxCell id="1" parent="0" />
  <mxCell id="img" value="" style="shape=image;image=https%3A%2F%2Fexample.com%2Fpaper-figure.png;" vertex="1" parent="1">
    <mxGeometry x="10" y="10" width="80" height="40" as="geometry" />
  </mxCell>
</root></mxGraphModel></diagram></mxfile>
""",
            encoding="utf-8",
        )
        failure = run_expect_failure(
            [sys.executable, str(SKILL / "scripts" / "validate_drawio.py"), "--json", str(encoded_external)]
        )
        failure_payload = json.loads(failure.stdout)
        assert failure_payload["ok"] is False
        assert failure_payload["stats"]["external_image_count"] == 1
        assert any("external image references found" in error for error in failure_payload["errors"])
        allowed = run(
            [
                sys.executable,
                str(SKILL / "scripts" / "validate_drawio.py"),
                "--json",
                "--allow-external-images",
                str(encoded_external),
            ]
        )
        allowed_payload = json.loads(allowed.stdout)
        assert allowed_payload["ok"] is True
        assert allowed_payload["stats"]["external_image_count"] == 1

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
    assert "DRAWIO_ORIGIN = 'https://embed.diagrams.net'" in html
    assert "evt.origin !== DRAWIO_ORIGIN" in html
    assert "evt.source !== iframe.contentWindow" in html
    assert "), '*')" not in html
    OUT.unlink()
    print("smoke test OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
