#!/usr/bin/env python3
"""Generate and serve a short local diagrams.net preview page."""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import webbrowser
from pathlib import Path

from make_drawio_preview import build_html


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate drawio-preview.html and serve it from a short localhost URL."
    )
    parser.add_argument("drawio", type=Path, help="Path to the .drawio XML file.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind. Use 0 to let the OS choose.")
    parser.add_argument("--out", type=Path, default=None, help="Preview HTML path. Defaults next to the input.")
    parser.add_argument("--title", default=None, help="Title shown in diagrams.net.")
    parser.add_argument("--no-open", action="store_true", help="Do not open the URL in the default browser.")
    args = parser.parse_args()

    drawio_path = args.drawio.resolve()
    if not drawio_path.exists():
        raise SystemExit(f"Input does not exist: {drawio_path}")

    xml = drawio_path.read_text(encoding="utf-8")
    title = args.title or drawio_path.name
    out_path = (args.out or drawio_path.with_name("drawio-preview.html")).resolve()
    out_path.write_text(build_html(xml, title), encoding="utf-8")

    handler = functools.partial(QuietHandler, directory=str(out_path.parent))
    try:
        with ReusableThreadingTCPServer((args.host, args.port), handler) as httpd:
            actual_port = httpd.server_address[1]
            url = f"http://{args.host}:{actual_port}/{out_path.name}?rev=1"
            print(f"Preview: {url}", flush=True)
            print("Press Ctrl+C to stop.", flush=True)
            if not args.no_open:
                webbrowser.open(url)
            httpd.serve_forever()
    except OSError as exc:
        raise SystemExit(f"Could not start server on {args.host}:{args.port}: {exc}") from exc
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
