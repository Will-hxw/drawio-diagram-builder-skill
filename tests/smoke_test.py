from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "drawio-diagram-builder"
EXAMPLE = ROOT / "examples" / "minimal.drawio"
OUT = ROOT / "examples" / "drawio-preview.html"


def run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def main() -> int:
    run([sys.executable, str(SKILL / "scripts" / "validate_drawio.py"), str(EXAMPLE)])
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
