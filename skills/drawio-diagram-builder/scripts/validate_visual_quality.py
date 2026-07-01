#!/usr/bin/env python3
"""Pre-render static quality checks for draw.io (.drawio) XML files.

Catches computable visual defects — arrow-box collisions, text overflow risk,
font proportionality, spacing variance, color incoherence, overlaps, orphans —
BEFORE the first screenshot.  Zero rendering needed.

Usage:
  python validate_visual_quality.py diagram.drawio
  python validate_visual_quality.py diagram.drawio --json --output report.json
  python validate_visual_quality.py diagram.drawio --strict   (WARN → FAIL)
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    def intersects(self, other: Rect) -> bool:
        return (
            self.x < other.x2
            and self.x2 > other.x
            and self.y < other.y2
            and self.y2 > other.y
        )

    def contains_point(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x2 and self.y <= py <= self.y2


@dataclass
class Vertex:
    id: str
    rect: Rect
    style: str
    value: str
    parent: str

    # Parsed style properties
    fill_color: Optional[str] = None
    stroke_color: Optional[str] = None
    font_size: Optional[float] = None
    font_family: Optional[str] = None
    rounded: bool = False
    dashed: bool = False
    shape: Optional[str] = None

    # Classification
    is_text: bool = False
    is_shape: bool = False
    is_image: bool = False
    is_edge: bool = False
    is_container: bool = False  # dashed, no fill, large


@dataclass
class Edge:
    id: str
    source_id: str
    target_id: str
    label: str
    source_point: Optional[Tuple[float, float]] = None
    target_point: Optional[Tuple[float, float]] = None
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    style: str = ""

    @property
    def all_points(self) -> List[Tuple[float, float]]:
        pts = []
        if self.source_point:
            pts.append(self.source_point)
        pts.extend(self.waypoints)
        if self.target_point:
            pts.append(self.target_point)
        return pts


@dataclass
class Finding:
    severity: str  # FAIL | WARN
    rule: str
    element_id: str
    message: str
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_STYLE_RE = re.compile(r"([a-zA-Z0-9_]+)(?:=([^;]*))?")


def _parse_style(style_str: str) -> Dict[str, str]:
    props = {}
    if not style_str:
        return props
    for m in _STYLE_RE.finditer(style_str):
        key = m.group(1)
        val = m.group(2) if m.group(2) is not None else "1"
        props[key] = val
    return props


def _parse_color(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    raw = raw.strip().lower()
    if raw in ("none", ""):
        return None
    return raw


def _parse_font_size(raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _estimate_text_bounds(
    text: str, font_size: float, container_width: float
) -> Tuple[float, float]:
    """Return estimated (width, height) in px for rendered text.

    Very rough heuristic — draw.io rendering varies by font and OS.
    """
    if not text or font_size <= 0:
        return 0, 0

    # Average character width: ~0.55×font_size for Latin, ~0.9× for CJK
    latin_chars = sum(1 for c in text if ord(c) < 0x2E80)
    cjk_chars = len(text) - latin_chars
    char_width = font_size * 0.58
    cjk_width = font_size * 0.92
    total_width = latin_chars * char_width + cjk_chars * cjk_width

    # Line wrapping
    if container_width > 0 and total_width > container_width:
        lines = math.ceil(total_width / container_width)
    else:
        lines = text.count("\n") + 1

    line_height = font_size * 1.35
    return (min(total_width, container_width) if container_width > 0 else total_width,
            lines * line_height)


def _line_segments(
    pts: List[Tuple[float, float]],
) -> List[Tuple[float, float, float, float]]:
    """Return list of (x1,y1,x2,y2) segments."""
    segs = []
    for i in range(len(pts) - 1):
        segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]))
    return segs


def _seg_rect_intersect(
    x1: float, y1: float, x2: float, y2: float, r: Rect
) -> bool:
    """Cohen-Sutherland based check: does line segment intersect rectangle?"""
    # Quick reject: both points left/right/above/below
    if (max(x1, x2) < r.x or min(x1, x2) > r.x2 or
            max(y1, y2) < r.y or min(y1, y2) > r.y2):
        return False
    # If either endpoint inside → intersect
    if r.contains_point(x1, y1) or r.contains_point(x2, y2):
        return True
    # Check all four edges
    edges = [
        (r.x, r.y, r.x2, r.y),   # top
        (r.x2, r.y, r.x2, r.y2), # right
        (r.x2, r.y2, r.x, r.y2), # bottom
        (r.x, r.y2, r.x, r.y),   # left
    ]
    for ex1, ey1, ex2, ey2 in edges:
        if _lines_intersect(x1, y1, x2, y2, ex1, ey1, ex2, ey2):
            return True
    return False


def _lines_intersect(
    x1, y1, x2, y2, x3, y3, x4, y4
) -> bool:
    """Check if two line segments intersect (excluding collinear)."""
    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)

    return (
        ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4)
        and ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4)
    )


def parse_drawio(path: Path) -> Tuple[List[Vertex], List[Edge], float, float]:
    """Parse a .drawio file and return vertices, edges, canvas width, height."""
    tree = ET.parse(path)
    root = tree.getroot()

    vertices: List[Vertex] = []
    edges: List[Edge] = []

    for diagram in root.iter("diagram"):
        for model in diagram.iter("mxGraphModel"):
            page_w = float(model.get("pageWidth", 1600))
            page_h = float(model.get("pageHeight", 1200))

            cell_elements = {}
            for cell in model.findall(".//mxCell"):
                cid = cell.get("id", "")
                cell_elements[cid] = cell

            for cell in model.findall(".//mxCell"):
                cid = cell.get("id", "")
                parent = cell.get("parent", "")
                style_str = cell.get("style", "")
                value = cell.get("value", "") or ""
                vertex_attr = cell.get("vertex")
                edge_attr = cell.get("edge")

                if cid in ("0", "1"):
                    continue

                props = _parse_style(style_str)

                geom = cell.find("mxGeometry")
                if geom is None:
                    continue

                if edge_attr == "1" or "edge" in props:
                    # --- Edge ---
                    src = cell.get("source", "")
                    tgt = cell.get("target", "")
                    sp = tp = None
                    wp: List[Tuple[float, float]] = []

                    sp_el = geom.find("mxPoint[@as='sourcePoint']")
                    tp_el = geom.find("mxPoint[@as='targetPoint']")
                    if sp_el is not None:
                        sp = (float(sp_el.get("x", 0)), float(sp_el.get("y", 0)))
                    if tp_el is not None:
                        tp = (float(tp_el.get("x", 0)), float(tp_el.get("y", 0)))

                    # waypoints
                    arr = geom.find("Array[@as='points']")
                    if arr is not None:
                        for pt in arr.findall("mxPoint"):
                            wp.append(
                                (float(pt.get("x", 0)), float(pt.get("y", 0)))
                            )

                    edges.append(Edge(
                        id=cid,
                        source_id=src,
                        target_id=tgt,
                        label=value.strip(),
                        source_point=sp,
                        target_point=tp,
                        waypoints=wp,
                        style=style_str,
                    ))

                elif vertex_attr == "1" or "shape" in props or "rounded" in props or "ellipse" in props:
                    # --- Vertex ---
                    x = float(geom.get("x", 0))
                    y = float(geom.get("y", 0))
                    w = float(geom.get("width", 0))
                    h = float(geom.get("height", 0))

                    v = Vertex(
                        id=cid,
                        rect=Rect(x, y, w, h),
                        style=style_str,
                        value=value,
                        parent=parent,
                        fill_color=_parse_color(props.get("fillColor")),
                        stroke_color=_parse_color(props.get("strokeColor")),
                        font_size=_parse_font_size(props.get("fontSize")),
                        font_family=props.get("fontFamily"),
                        rounded="rounded" in props,
                        dashed="dashed" in props,
                        shape=props.get("shape"),
                    )

                    # Classify
                    v.is_text = (
                        props.get("shape") == "text"
                        or props.get("strokeColor") == "none"
                        or ("text" in style_str.lower() and v.fill_color is None)
                    )
                    v.is_image = props.get("shape") == "image"
                    v.is_shape = not v.is_text and not v.is_image
                    # Heuristic: large dashed boxes with no fill are containers
                    v.is_container = bool(
                        v.dashed
                        and v.fill_color is None
                        and v.rect.w > 200
                        and v.rect.h > 100
                    )

                    vertices.append(v)

    return vertices, edges, page_w, page_h


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def check_arrow_box_collision(
    vertices: List[Vertex], edges: List[Edge]
) -> List[Finding]:
    findings = []
    non_container = [v for v in vertices if not v.is_container and not v.is_text]
    rects = {v.id: v.rect for v in vertices}

    for edge in edges:
        pts = edge.all_points
        if len(pts) < 2:
            continue
        segs = _line_segments(pts)
        src_id = edge.source_id
        tgt_id = edge.target_id

        for seg in segs:
            for v in non_container:
                if v.id == src_id or v.id == tgt_id:
                    continue
                if _seg_rect_intersect(*seg, v.rect):
                    findings.append(Finding(
                        severity="FAIL",
                        rule="arrow-box-collision",
                        element_id=edge.id,
                        message=f"Edge '{edge.id}' passes through box '{v.id}' "
                                f"({v.rect.x:.0f},{v.rect.y:.0f} {v.rect.w:.0f}×{v.rect.h:.0f})",
                        detail={
                            "edge_id": edge.id,
                            "box_id": v.id,
                            "box_rect": f"{v.rect.x:.0f},{v.rect.y:.0f} {v.rect.w:.0f}×{v.rect.h:.0f}",
                            "segment": f"({seg[0]:.0f},{seg[1]:.0f})→({seg[2]:.0f},{seg[3]:.0f})",
                        },
                    ))
                    break  # one finding per edge-box pair is enough

    return findings


def check_text_overflow(vertices: List[Vertex]) -> List[Finding]:
    findings = []
    for v in vertices:
        text = v.value.strip()
        if not text or v.font_size is None or v.rect.w <= 0 or v.rect.h <= 0:
            continue

        est_w, est_h = _estimate_text_bounds(text, v.font_size, v.rect.w)

        if est_h > v.rect.h * 1.05:
            findings.append(Finding(
                severity="FAIL",
                rule="text-overflow-vertical",
                element_id=v.id,
                message=f"Text in '{v.id}' overflows vertically: "
                        f"estimated {est_h:.0f}px needed, container is {v.rect.h:.0f}px tall. "
                        f"Text: \"{text[:60]}{'...' if len(text)>60 else ''}\" "
                        f"(fontSize={v.font_size}, width={v.rect.w:.0f})",
                detail={
                    "estimated_height": round(est_h, 1),
                    "container_height": v.rect.h,
                    "font_size": v.font_size,
                    "text_preview": text[:100],
                },
            ))

        if est_w > v.rect.w * 1.1 and v.rect.w > 0:
            findings.append(Finding(
                severity="FAIL",
                rule="text-overflow-horizontal",
                element_id=v.id,
                message=f"Text in '{v.id}' overflows horizontally: "
                        f"estimated {est_w:.0f}px needed, container is {v.rect.w:.0f}px wide. "
                        f"Text: \"{text[:60]}{'...' if len(text)>60 else ''}\"",
                detail={
                    "estimated_width": round(est_w, 1),
                    "container_width": v.rect.w,
                    "font_size": v.font_size,
                    "text_preview": text[:100],
                },
            ))

    return findings


def check_font_proportionality(vertices: List[Vertex]) -> List[Finding]:
    findings = []
    for v in vertices:
        if v.font_size is None or v.rect.h <= 0 or v.is_container or v.is_image:
            continue
        text = v.value.strip()
        if not text:
            continue

        ratio = v.rect.h / v.font_size
        width_ratio = v.rect.w / v.font_size if v.font_size > 0 else 0

        if ratio > 12:
            findings.append(Finding(
                severity="WARN",
                rule="font-box-cavernous",
                element_id=v.id,
                message=f"Box '{v.id}' is {v.rect.h:.0f}px tall with fontSize={v.font_size} "
                        f"(ratio {ratio:.1f}:1). Text will look tiny and lost. "
                        f"Either shrink box or increase font.",
                detail={"box_height": v.rect.h, "font_size": v.font_size,
                         "ratio": round(ratio, 1)},
            ))

        if ratio < 1.3 and v.rect.h > 20:
            findings.append(Finding(
                severity="FAIL",
                rule="font-box-cramped",
                element_id=v.id,
                message=f"Box '{v.id}' is {v.rect.h:.0f}px tall with fontSize={v.font_size} "
                        f"(ratio {ratio:.1f}:1). Text will be squeezed or clipped.",
                detail={"box_height": v.rect.h, "font_size": v.font_size,
                         "ratio": round(ratio, 1)},
            ))

        # Check width proportion for text-only cells
        if v.is_text and width_ratio > 30 and len(text) < 5:
            findings.append(Finding(
                severity="WARN",
                rule="font-box-wide-empty",
                element_id=v.id,
                message=f"Text cell '{v.id}' is {v.rect.w:.0f}px wide for "
                        f"fontSize={v.font_size} with short text '{text}'. "
                        f"Box is disproportionately wide.",
                detail={"box_width": v.rect.w, "font_size": v.font_size,
                         "text": text},
            ))

    return findings


def check_element_overlap(vertices: List[Vertex]) -> List[Finding]:
    findings = []
    shapes = [v for v in vertices if v.is_shape and not v.is_container]
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            a, b = shapes[i], shapes[j]
            if a.rect.intersects(b.rect):
                findings.append(Finding(
                    severity="FAIL",
                    rule="element-overlap",
                    element_id=a.id,
                    message=f"Box '{a.id}' overlaps box '{b.id}': "
                            f"({a.rect.x:.0f},{a.rect.y:.0f} {a.rect.w:.0f}×{a.rect.h:.0f}) "
                            f"vs ({b.rect.x:.0f},{b.rect.y:.0f} {b.rect.w:.0f}×{b.rect.h:.0f})",
                    detail={
                        "box_a": a.id, "box_b": b.id,
                        "rect_a": f"{a.rect.x:.0f},{a.rect.y:.0f} {a.rect.w:.0f}×{a.rect.h:.0f}",
                        "rect_b": f"{b.rect.x:.0f},{b.rect.y:.0f} {b.rect.w:.0f}×{b.rect.h:.0f}",
                    },
                ))
    return findings


def check_spacing_variance(vertices: List[Vertex]) -> List[Finding]:
    findings = []
    shapes = [
        v for v in vertices
        if v.is_shape and not v.is_container and v.rect.w > 0 and v.rect.h > 0
    ]
    if len(shapes) < 3:
        return findings

    # Group by approximate row (y within 15px)
    rows: Dict[int, List[Vertex]] = defaultdict(list)
    for v in shapes:
        row_key = round(v.rect.y / 15) * 15
        rows[row_key].append(v)

    for row_key, row_shapes in rows.items():
        if len(row_shapes) < 3:
            continue
        row_shapes.sort(key=lambda v: v.rect.x)
        gaps = []
        for i in range(len(row_shapes) - 1):
            gap = row_shapes[i + 1].rect.x - row_shapes[i].rect.x2
            if gap > 0:
                gaps.append(gap)

        if len(gaps) < 2:
            continue

        mean_gap = sum(gaps) / len(gaps)
        if mean_gap < 1:
            continue
        variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
        stddev = math.sqrt(variance)
        cv = stddev / mean_gap

        if cv > 0.5:
            findings.append(Finding(
                severity="WARN",
                rule="spacing-inconsistent",
                element_id=row_shapes[0].id,
                message=f"Row at y≈{row_key}: horizontal gaps vary wildly "
                        f"(gaps={[f'{g:.0f}' for g in gaps]}, "
                        f"mean={mean_gap:.0f}, cv={cv:.2f}). "
                        f"Use uniform spacing.",
                detail={
                    "row_y": row_key,
                    "gaps": [round(g, 1) for g in gaps],
                    "mean": round(mean_gap, 1),
                    "cv": round(cv, 2),
                    "element_ids": [v.id for v in row_shapes],
                },
            ))

        if min(gaps) < 3:
            findings.append(Finding(
                severity="FAIL",
                rule="spacing-too-tight",
                element_id=row_shapes[0].id,
                message=f"Row at y≈{row_key}: min gap is {min(gaps):.0f}px — "
                        f"elements nearly touch. Add breathing room.",
                detail={"row_y": row_key, "min_gap": round(min(gaps), 1)},
            ))

    return findings


def check_color_coherence(vertices: List[Vertex]) -> List[Finding]:
    findings = []
    fills = set()
    strokes = set()
    for v in vertices:
        if v.fill_color and v.fill_color != "none":
            fills.add(v.fill_color)
        if v.stroke_color and v.stroke_color != "none":
            strokes.add(v.stroke_color)

    if len(fills) > 8:
        findings.append(Finding(
            severity="WARN",
            rule="color-too-many-fills",
            element_id="*",
            message=f"{len(fills)} distinct fill colors used across diagram. "
                    f"Palette is scattered — reduce to 3-6 fill colors. "
                    f"Colors: {', '.join(sorted(fills))}",
            detail={"fill_count": len(fills), "colors": sorted(fills)},
        ))

    if len(strokes) > 6:
        findings.append(Finding(
            severity="WARN",
            rule="color-too-many-strokes",
            element_id="*",
            message=f"{len(strokes)} distinct stroke colors used. "
                    f"Use 2-3 consistent stroke colors. "
                    f"Colors: {', '.join(sorted(strokes))}",
            detail={"stroke_count": len(strokes), "colors": sorted(strokes)},
        ))

    return findings


def check_orphan_labels(vertices: List[Vertex], edges: List[Edge]) -> List[Finding]:
    findings = []

    # Edges without labels
    for edge in edges:
        if not edge.label:
            # Some edges legitimately don't need labels (structural connectors),
            # but flag them so the agent verifies intent.
            pass  # Too noisy as FAIL; the semantic audit in self-supervision catches this

    # Shapes with empty value and significant size (> 60x30)
    for v in vertices:
        if v.is_shape and not v.value.strip() and v.rect.w > 60 and v.rect.h > 30:
            findings.append(Finding(
                severity="WARN",
                rule="orphan-empty-box",
                element_id=v.id,
                message=f"Box '{v.id}' ({v.rect.w:.0f}×{v.rect.h:.0f}) has no text label. "
                        f"Add content or reduce size.",
                detail={"box_id": v.id, "size": f"{v.rect.w:.0f}×{v.rect.h:.0f}"},
            ))

    return findings


def check_font_size_anomalies(vertices: List[Vertex]) -> List[Finding]:
    findings = []
    for v in vertices:
        if v.font_size is None:
            continue
        if v.font_size < 7:
            findings.append(Finding(
                severity="FAIL",
                rule="font-too-small",
                element_id=v.id,
                message=f"'{v.id}' uses fontSize={v.font_size} — likely illegible. "
                        f"Minimum 8pt for body, 10pt recommended.",
                detail={"font_size": v.font_size, "element_id": v.id},
            ))
        if v.font_size > 48 and v.is_text:
            findings.append(Finding(
                severity="WARN",
                rule="font-too-large",
                element_id=v.id,
                message=f"'{v.id}' uses fontSize={v.font_size} — verify this is "
                        f"intentional (heading?) and not a copy-paste error.",
                detail={"font_size": v.font_size, "element_id": v.id},
            ))
    return findings


def check_edge_density(edges: List[Edge], page_w: float, page_h: float) -> List[Finding]:
    findings = []
    cell_size = 200
    grid: Dict[Tuple[int, int], int] = defaultdict(int)

    for edge in edges:
        pts = edge.all_points
        for (x1, y1, x2, y2) in _line_segments(pts):
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            grid_key = (int(cx // cell_size), int(cy // cell_size))
            grid[grid_key] += 1

    for (gx, gy), count in grid.items():
        if count > 5:
            findings.append(Finding(
                severity="WARN",
                rule="edge-density-hotspot",
                element_id="*",
                message=f"Cell ({gx*cell_size},{gy*cell_size}) has {count} edge "
                        f"segments — potential arrow spaghetti. "
                        f"Reroute connectors or add explicit waypoints.",
                detail={"cell_x": gx * cell_size, "cell_y": gy * cell_size,
                         "edge_count": count},
            ))

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

ALL_RULES = [
    ("arrow-box-collision", check_arrow_box_collision),
    ("text-overflow", check_text_overflow),
    ("font-proportionality", check_font_proportionality),
    ("element-overlap", check_element_overlap),
    ("spacing-variance", check_spacing_variance),
    ("color-coherence", check_color_coherence),
    ("orphan-labels", check_orphan_labels),
    ("font-size-anomalies", check_font_size_anomalies),
    ("edge-density", check_edge_density),
]


def run_all_checks(
    vertices: List[Vertex],
    edges: List[Edge],
    page_w: float,
    page_h: float,
    strict: bool = False,
) -> List[Finding]:
    all_findings: List[Finding] = []
    for rule_name, rule_fn in ALL_RULES:
        if rule_name == "edge-density":
            findings = rule_fn(edges, page_w, page_h)
        elif rule_name in ("arrow-box-collision", "orphan-labels"):
            findings = rule_fn(vertices, edges)
        else:
            findings = rule_fn(vertices)
        all_findings.extend(findings)

    if strict:
        for f in all_findings:
            if f.severity == "WARN":
                f.severity = "FAIL"

    return all_findings


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Pre-render visual quality checks for .drawio files"
    )
    ap.add_argument("drawio", type=Path, help="Path to .drawio file")
    ap.add_argument(
        "--json", action="store_true", help="Output JSON report"
    )
    ap.add_argument(
        "--output", "-o", type=Path, help="Write report to file"
    )
    ap.add_argument(
        "--strict", action="store_true",
        help="Treat WARN as FAIL (for CI / handoff gate)"
    )
    ap.add_argument(
        "--rules", nargs="*",
        help="Only run specific rules (name or prefix)"
    )
    args = ap.parse_args()

    if not args.drawio.exists():
        print(f"ERROR: file not found: {args.drawio}", file=sys.stderr)
        return 1

    try:
        vertices, edges, page_w, page_h = parse_drawio(args.drawio)
    except ET.ParseError as e:
        print(f"ERROR: XML parse failed: {e}", file=sys.stderr)
        return 1

    # Filter rules if requested
    if args.rules:
        selected = []
        for rn, rf in ALL_RULES:
            if any(rn.startswith(p) for p in args.rules):
                selected.append((rn, rf))
    else:
        selected = list(ALL_RULES)

    findings = []
    for rule_name, rule_fn in selected:
        if rule_name == "edge-density":
            results = rule_fn(edges, page_w, page_h)
        elif rule_name in ("arrow-box-collision", "orphan-labels"):
            results = rule_fn(vertices, edges)
        else:
            results = rule_fn(vertices)
        findings.extend(results)

    if args.strict:
        for f in findings:
            if f.severity == "WARN":
                f.severity = "FAIL"

    fails = [f for f in findings if f.severity == "FAIL"]
    warns = [f for f in findings if f.severity == "WARN"]

    if args.json:
        report = {
            "file": str(args.drawio),
            "summary": {
                "total_findings": len(findings),
                "fail": len(fails),
                "warn": len(warns),
                "passed": len(fails) == 0,
                "clean": len(findings) == 0,
            },
            "fails": [
                {
                    "rule": f.rule,
                    "element_id": f.element_id,
                    "message": f.message,
                    "detail": f.detail,
                }
                for f in fails
            ],
            "warns": [
                {
                    "rule": f.rule,
                    "element_id": f.element_id,
                    "message": f.message,
                    "detail": f.detail,
                }
                for f in warns
            ],
            "vertex_count": len(vertices),
            "edge_count": len(edges),
            "canvas": f"{page_w:.0f}×{page_h:.0f}",
        }
        output = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(output, encoding="utf-8")
            print(f"Report written to {args.output}")
        else:
            print(output)
    else:
        print(f"Pre-flight report for: {args.drawio}")
        print(f"  Canvas: {page_w:.0f}×{page_h:.0f}  |  "
              f"Vertices: {len(vertices)}  |  Edges: {len(edges)}")
        print(f"  FAIL: {len(fails)}  |  WARN: {len(warns)}  |  "
              f"{'❌ BLOCKED' if fails else '✅ PASSED'}")
        print()

        if fails:
            print("── FAIL (must fix before preview) ──")
            for f in fails:
                print(f"  [{f.rule}] {f.element_id}: {f.message}")

        if warns:
            print()
            print("── WARN (review before preview) ──")
            for f in warns:
                print(f"  [{f.rule}] {f.element_id}: {f.message}")

        if not findings:
            print("  All checks pass. Ready for preview.")

    return 0 if len(fails) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
