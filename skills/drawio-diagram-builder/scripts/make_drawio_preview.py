#!/usr/bin/env python3
"""Create a short local diagrams.net preview page for a .drawio XML file."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def build_html(xml: str, title: str) -> str:
    xml_json = json.dumps(xml)
    title_json = json.dumps(title)
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>{escaped_title}</title>
<style>
  html, body {{ margin: 0; width: 100%; height: 100%; overflow: hidden; background: #f7f7f7; }}
  iframe {{ border: 0; width: 100vw; height: 100vh; display: block; }}
</style>
</head>
<body>
<iframe id="drawio" src="https://embed.diagrams.net/?embed=1&proto=json&spin=1&ui=atlas&libraries=0&grid=0&pv=0"></iframe>
<script>
const xml = {xml_json};
const diagramTitle = {title_json};
const DRAWIO_ORIGIN = 'https://embed.diagrams.net';
const iframe = document.getElementById('drawio');
let loaded = false;
function downloadXml(savedXml) {{
  const blob = new Blob([savedXml], {{ type: 'application/xml' }});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const cleanTitle = diagramTitle.endsWith('.drawio') ? diagramTitle : `${{diagramTitle}}.drawio`;
  link.href = url;
  link.download = cleanTitle;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}}
function sendLoad() {{
  iframe.contentWindow.postMessage(JSON.stringify({{
    action: 'load',
    autosave: 0,
    modified: 0,
    title: diagramTitle,
    xml
  }}), DRAWIO_ORIGIN);
}}
window.__drawioPreview = {{
  requestSave: () => iframe.contentWindow.postMessage(JSON.stringify({{ action: 'save' }}), DRAWIO_ORIGIN)
}};
window.addEventListener('message', (evt) => {{
  if (evt.source !== iframe.contentWindow || evt.origin !== DRAWIO_ORIGIN) return;
  let msg = evt.data;
  try {{ if (typeof msg === 'string') msg = JSON.parse(msg); }} catch (e) {{ return; }}
  if (!msg) return;
  if (msg.event === 'save' && msg.xml) {{
    downloadXml(msg.xml);
    iframe.contentWindow.postMessage(JSON.stringify({{
      action: 'status',
      modified: false,
      message: 'Downloaded .drawio file'
    }}), DRAWIO_ORIGIN);
    return;
  }}
  if (!loaded && (msg.event === 'init' || msg.event === 'configure')) {{
    loaded = true;
    sendLoad();
  }}
}});
setTimeout(() => {{ if (!loaded) sendLoad(); }}, 2500);
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a short local draw.io preview HTML page.")
    parser.add_argument("drawio", type=Path, help="Path to the .drawio XML file.")
    parser.add_argument("--out", type=Path, default=None, help="Output HTML path. Defaults to drawio-preview.html next to the input.")
    parser.add_argument("--title", default=None, help="Title shown in diagrams.net.")
    args = parser.parse_args()

    drawio_path = args.drawio.resolve()
    if not drawio_path.exists():
        raise SystemExit(f"Input does not exist: {drawio_path}")

    xml = drawio_path.read_text(encoding="utf-8")
    title = args.title or drawio_path.name
    out_path = (args.out or drawio_path.with_name("drawio-preview.html")).resolve()
    out_path.write_text(build_html(xml, title), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
