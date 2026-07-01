#!/usr/bin/env python3
"""Sanity-check editable .drawio XML files."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import unquote


BASE64_RE = re.compile(r"data:[^;,\s]+;base64,([A-Za-z0-9+/=\s]+)")
EXTERNAL_IMAGE_RE = re.compile(
    r"(?:image=|src=['\"]?|xlink:href=['\"]?)(https?://[^;'\"]+)",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(
    r"\b(?:todo|tbd|fixme|lorem ipsum|placeholder|replace me|sample text)\b|待定|占位",
    re.IGNORECASE,
)
RASTER_MARKERS = ("data:image/png", "data:image/jpeg", "data:image/jpg", "data:image/webp")


def clean_label(value: Optional[str]) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", html.unescape(value))
    return " ".join(text.split())


def numeric(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def find_geometry(cell: ET.Element) -> Optional[ET.Element]:
    for child in cell:
        if child.tag == "mxGeometry" and child.attrib.get("as") == "geometry":
            return child
    return None


def edge_needs_endpoints(edge: ET.Element, label: str) -> bool:
    style = edge.attrib.get("style", "").lower()
    has_start_arrow = "startarrow=" in style and "startarrow=none" not in style
    has_end_arrow = "endarrow=" in style and "endarrow=none" not in style
    return bool(label) or has_start_arrow or has_end_arrow


def external_image_references(text: str) -> list[str]:
    variants = {
        text,
        html.unescape(text),
        unquote(text),
        html.unescape(unquote(text)),
    }
    references: set[str] = set()
    for variant in variants:
        references.update(EXTERNAL_IMAGE_RE.findall(variant))
    return sorted(references)


def page_size(root: ET.Element) -> Tuple[Optional[float], Optional[float]]:
    model = root.find(".//mxGraphModel")
    if model is None:
        return None, None
    return numeric(model.attrib.get("pageWidth")), numeric(model.attrib.get("pageHeight"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate basic .drawio XML integrity.")
    parser.add_argument("drawio", type=Path, help="Path to .drawio file.")
    parser.add_argument("--allow-raster", action="store_true", help="Allow embedded raster images.")
    parser.add_argument("--allow-external-images", action="store_true", help="Allow externally hosted image references.")
    parser.add_argument("--expect-no-caption", action="store_true", help="Fail if common figure captions are found.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as validation failures.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    parser.add_argument("--min-cells", type=int, default=0, help="Minimum required mxCell count.")
    parser.add_argument(
        "--max-base64-chars",
        type=int,
        default=200_000,
        help="Maximum allowed base64 payload length before failing.",
    )
    parser.add_argument(
        "--off-page-margin",
        type=float,
        default=120.0,
        help="Allowed pixels beyond the page before reporting an off-page vertex.",
    )
    args = parser.parse_args()

    path = args.drawio.resolve()
    if not path.exists():
        if args.json:
            print(json.dumps({"ok": False, "errors": [f"missing file: {path}"], "warnings": [], "stats": {}}, indent=2))
        else:
            print(f"ERROR: missing file: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        if args.json:
            print(json.dumps({"ok": False, "errors": [f"XML parse failed: {exc}"], "warnings": [], "stats": {}}, indent=2))
        else:
            print(f"ERROR: XML parse failed: {exc}", file=sys.stderr)
        return 2

    diagrams = root.findall(".//diagram")
    cells = root.findall(".//mxCell")
    cell_ids = [cell.attrib.get("id", "") for cell in cells]
    id_counts = Counter(cell_ids)
    known_ids = {cell_id for cell_id in cell_ids if cell_id}
    duplicate_ids = sorted(cell_id for cell_id, count in id_counts.items() if cell_id and count > 1)
    missing_id_count = sum(1 for cell_id in cell_ids if not cell_id)
    vertices = [cell for cell in cells if cell.attrib.get("vertex") == "1"]
    edges = [cell for cell in cells if cell.attrib.get("edge") == "1"]
    page_width, page_height = page_size(root)
    base64_payloads = [re.sub(r"\s+", "", match.group(1)) for match in BASE64_RE.finditer(text)]
    huge_base64_payloads = [len(payload) for payload in base64_payloads if len(payload) > args.max_base64_chars]
    has_raster = any(marker in text for marker in RASTER_MARKERS)
    has_caption = "Figure " in text or "Fig. " in text or "Figure:" in text
    external_images = external_image_references(text)

    errors: list[str] = []
    warnings: list[str] = []
    if root.tag != "mxfile":
        errors.append(f"root tag is {root.tag!r}, expected 'mxfile'")
    if not diagrams:
        errors.append("no diagram pages found")
    if not cells:
        errors.append("no mxCell elements found")
    if args.min_cells and len(cells) < args.min_cells:
        errors.append(f"mxCell count {len(cells)} is below --min-cells {args.min_cells}")
    if duplicate_ids:
        errors.append(f"duplicate mxCell ids found: {', '.join(duplicate_ids[:20])}")
    if missing_id_count:
        errors.append(f"{missing_id_count} mxCell elements are missing id attributes")
    if has_raster and not args.allow_raster:
        errors.append("embedded raster image found; final editable diagrams should avoid this unless explicitly allowed")
    if external_images and not args.allow_external_images:
        errors.append(f"external image references found: {', '.join(external_images[:5])}")
    if huge_base64_payloads:
        errors.append(
            "base64 payload exceeds limit: "
            + ", ".join(str(length) for length in sorted(huge_base64_payloads, reverse=True)[:5])
        )
    if has_caption and args.expect_no_caption:
        errors.append("caption-like text found")
    if page_width is None or page_height is None or page_width <= 0 or page_height <= 0:
        warnings.append("pageWidth/pageHeight are missing or invalid")

    parent_refs: defaultdict[str, list[str]] = defaultdict(list)
    edge_ref_errors: list[str] = []
    missing_geometry: list[str] = []
    invalid_geometry: list[str] = []
    off_page_vertices: list[str] = []
    empty_vertex_labels = 0
    empty_edge_labels = 0
    placeholder_labels: list[str] = []

    for cell in cells:
        cell_id = cell.attrib.get("id", "<missing>")
        parent = cell.attrib.get("parent")
        if parent and parent not in known_ids:
            parent_refs[parent].append(cell_id)

        label = clean_label(cell.attrib.get("value"))
        if cell.attrib.get("vertex") == "1":
            if not label:
                empty_vertex_labels += 1
            elif PLACEHOLDER_RE.search(label):
                placeholder_labels.append(cell_id)
        elif cell.attrib.get("edge") == "1":
            if not label:
                empty_edge_labels += 1
            elif PLACEHOLDER_RE.search(label):
                placeholder_labels.append(cell_id)

    for parent, children in sorted(parent_refs.items()):
        errors.append(f"parent reference {parent!r} does not exist (children: {', '.join(children[:8])})")

    for edge in edges:
        edge_id = edge.attrib.get("id", "<missing>")
        source = edge.attrib.get("source")
        target = edge.attrib.get("target")
        label = clean_label(edge.attrib.get("value"))
        if source and source not in known_ids:
            edge_ref_errors.append(f"{edge_id} source {source!r} does not exist")
        if target and target not in known_ids:
            edge_ref_errors.append(f"{edge_id} target {target!r} does not exist")
        if edge_needs_endpoints(edge, label):
            if not source:
                warnings.append(f"connector edge {edge_id} is missing source")
            if not target:
                warnings.append(f"connector edge {edge_id} is missing target")
        geometry = find_geometry(edge)
        if geometry is None:
            missing_geometry.append(edge_id)

    for vertex in vertices:
        vertex_id = vertex.attrib.get("id", "<missing>")
        geometry = find_geometry(vertex)
        if geometry is None:
            missing_geometry.append(vertex_id)
            continue

        x = numeric(geometry.attrib.get("x")) or 0.0
        y = numeric(geometry.attrib.get("y")) or 0.0
        width = numeric(geometry.attrib.get("width"))
        height = numeric(geometry.attrib.get("height"))
        if width is None or height is None or width <= 0 or height <= 0:
            invalid_geometry.append(vertex_id)
            continue
        if page_width and page_height:
            margin = args.off_page_margin
            if x < -margin or y < -margin or x + width > page_width + margin or y + height > page_height + margin:
                off_page_vertices.append(vertex_id)

    errors.extend(edge_ref_errors)
    if missing_geometry:
        errors.append(f"mxGeometry missing for cells: {', '.join(missing_geometry[:20])}")
    if invalid_geometry:
        errors.append(f"invalid vertex geometry for cells: {', '.join(invalid_geometry[:20])}")
    if off_page_vertices:
        warnings.append(f"vertices extend beyond page margin: {', '.join(off_page_vertices[:20])}")
    if placeholder_labels:
        warnings.append(f"placeholder-like labels found: {', '.join(placeholder_labels[:20])}")

    stats = {
        "file": str(path),
        "pages": len(diagrams),
        "cells": len(cells),
        "vertices": len(vertices),
        "edges": len(edges),
        "embedded_raster": has_raster,
        "external_image_count": len(external_images),
        "base64_payload_count": len(base64_payloads),
        "largest_base64_payload_chars": max((len(payload) for payload in base64_payloads), default=0),
        "caption_like_text": has_caption,
        "duplicate_id_count": len(duplicate_ids),
        "missing_id_count": missing_id_count,
        "empty_vertex_labels": empty_vertex_labels,
        "empty_edge_labels": empty_edge_labels,
        "placeholder_label_count": len(placeholder_labels),
        "page_width": page_width,
        "page_height": page_height,
    }

    effective_errors = errors + warnings if args.strict else errors

    if args.json:
        print(
            json.dumps(
                {
                    "ok": not effective_errors,
                    "strict": args.strict,
                    "errors": errors,
                    "warnings": warnings,
                    "stats": stats,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1 if effective_errors else 0

    print(f"file: {path}")
    print(f"pages: {stats['pages']}")
    print(f"cells: {stats['cells']}")
    print(f"vertices: {stats['vertices']}")
    print(f"edges: {stats['edges']}")
    print(f"embedded_raster: {stats['embedded_raster']}")
    print(f"external_image_count: {stats['external_image_count']}")
    print(f"base64_payload_count: {stats['base64_payload_count']}")
    print(f"largest_base64_payload_chars: {stats['largest_base64_payload_chars']}")
    print(f"caption_like_text: {stats['caption_like_text']}")
    print(f"duplicate_id_count: {stats['duplicate_id_count']}")
    print(f"empty_vertex_labels: {stats['empty_vertex_labels']}")
    print(f"empty_edge_labels: {stats['empty_edge_labels']}")
    print(f"placeholder_label_count: {stats['placeholder_label_count']}")
    print(f"page_width: {stats['page_width']}")
    print(f"page_height: {stats['page_height']}")

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if effective_errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if args.strict:
            for warning in warnings:
                print(f"ERROR(strict): {warning}", file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
