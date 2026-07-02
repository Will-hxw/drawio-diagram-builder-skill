#!/usr/bin/env python3
"""Pre-render static quality checks for draw.io (.drawio) XML files.

Catches computable visual defects — arrow-box collisions, text overflow risk,
font proportionality, spacing variance, color incoherence, decoration blocks,
orphans, font-size anomalies, edge density — BEFORE the first screenshot.
Zero rendering needed.

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

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

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

    def effective_font_size(self) -> Optional[float]:
        """Return fontSize if set, else draw.io default 12."""
        return self.font_size if self.font_size else 12.0


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
    # Derived from source/target vertex centers when no explicit mxPoint exists (#1)
    derived_source: Optional[Tuple[float, float]] = None
    derived_target: Optional[Tuple[float, float]] = None

    @property
    def all_points(self) -> List[Tuple[float, float]]:
        pts = []
        sp = self.source_point if self.source_point else self.derived_source
        tp = self.target_point if self.target_point else self.derived_target
        if sp:
            pts.append(sp)
        pts.extend(self.waypoints)
        if tp:
            pts.append(tp)
        return pts


@dataclass
class Finding:
    severity: str  # FAIL | WARN
    rule: str
    element_id: str
    message: str
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_STYLE_RE = re.compile(r"([a-zA-Z0-9_]+)(?:=([^;]*))?")
_HTML_TAG_RE = re.compile(r'<[^>]*>')


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


def _strip_html(text: str) -> str:
    """Remove HTML tags and common XML entities for character counting."""
    stripped = _HTML_TAG_RE.sub('', text)
    stripped = stripped.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    stripped = stripped.replace('&quot;', '"').replace('&#39;', "'")
    stripped = stripped.replace('&nbsp;', ' ')
    return stripped


def _is_semantic_label(text: str) -> bool:
    """Check if a label carries semantic meaning or is just decorative.

    Decorative evasion patterns: '1', '2 3 4', 'x', '●', ' ', 'A', 'B', single-digit
    or single-alpha sequences, short pure-numeric sequences.
    Real labels: words, phrases, abbreviations, multi-character identifiers.
    """
    stripped = text.strip()
    if not stripped:
        return False
    # Single char (digit, symbol, or single letter) → decoration marker
    if len(stripped) == 1:
        return False
    # Very short strings with only digits/symbols → decoration
    if len(stripped) <= 2 and not any(c.isalpha() for c in stripped):
        return False
    # Pure numeric sequence like "1 2 3 4" → likely decoration
    if all(c.isdigit() or c.isspace() for c in stripped) and len(stripped.replace(' ', '')) <= 6:
        return False
    return True


def _estimate_text_bounds(
    text: str, font_size: float, container_width: float
) -> Tuple[float, float]:
    """Return estimated (width, height) in px for rendered text.
    HTML tags are stripped before counting (#10).
    """
    if not text or font_size <= 0:
        return 0, 0

    # Strip HTML to avoid inflating text estimate (#10)
    clean = _strip_html(text)
    if not clean:
        return 0, 0

    # Average character width: ~0.58×font_size for Latin, ~0.92× for CJK
    latin_chars = sum(1 for c in clean if ord(c) < 0x2E80)
    cjk_chars = len(clean) - latin_chars
    char_width = font_size * 0.58
    cjk_width = font_size * 0.92
    total_width = latin_chars * char_width + cjk_chars * cjk_width

    # Line wrapping
    if container_width > 0 and total_width > container_width:
        lines = math.ceil(total_width / container_width)
    else:
        lines = clean.count("\n") + 1

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
    """Does line segment intersect rectangle? Cohen-Sutherland with collinear fallback."""
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
    """Check if two line segments intersect. Handles collinear overlap (#9)."""
    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)

    o1 = ccw(x1, y1, x2, y2, x3, y3)
    o2 = ccw(x1, y1, x2, y2, x4, y4)
    o3 = ccw(x3, y3, x4, y4, x1, y1)
    o4 = ccw(x3, y3, x4, y4, x2, y2)

    # Standard ccw test
    if ((o1 > 0) != (o2 > 0)) and ((o3 > 0) != (o4 > 0)):
        return True

    # Collinear overlap check (#9): all ccw zero AND projections overlap
    if o1 == 0 and o2 == 0 and o3 == 0 and o4 == 0:
        # Project onto bounding intervals
        min1x, max1x = min(x1, x2), max(x1, x2)
        min1y, max1y = min(y1, y2), max(y1, y2)
        min2x, max2x = min(x3, x4), max(x3, x4)
        min2y, max2y = min(y3, y4), max(y3, y4)
        if max1x >= min2x and max2x >= min1x and max1y >= min2y and max2y >= min1y:
            return True

    return False


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

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

    # --- Resolve edge endpoints from vertex rects when explicit mxPoints are missing (#1) ---
    vertex_rects = {v.id: v.rect for v in vertices}
    for edge in edges:
        if edge.source_point is None and edge.source_id in vertex_rects:
            r = vertex_rects[edge.source_id]
            edge.derived_source = (r.cx, r.cy)
        if edge.target_point is None and edge.target_id in vertex_rects:
            r = vertex_rects[edge.target_id]
            edge.derived_target = (r.cx, r.cy)

    return vertices, edges, page_w, page_h


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def check_arrow_box_collision(
    vertices: List[Vertex], edges: List[Edge]
) -> List[Finding]:
    """Arrow-box collision check — now covers text vertices too (#5) and
    edges without explicit mxPoints via derived endpoints (#1)."""
    findings = []
    # Include all vertices EXCEPT containers (text, shape, and image all checked)
    check_targets = [v for v in vertices if not v.is_container]
    rects = {v.id: v.rect for v in vertices}

    for edge in edges:
        pts = edge.all_points
        if len(pts) < 2:
            continue
        segs = _line_segments(pts)
        src_id = edge.source_id
        tgt_id = edge.target_id

        for seg in segs:
            for v in check_targets:
                # Skip the edge's own source/target (#7 fix: only skip if ref is valid)
                if (v.id == src_id and src_id in rects) or (v.id == tgt_id and tgt_id in rects):
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
                            "box_type": "text" if v.is_text else ("image" if v.is_image else "shape"),
                            "box_rect": f"{v.rect.x:.0f},{v.rect.y:.0f} {v.rect.w:.0f}×{v.rect.h:.0f}",
                            "segment": f"({seg[0]:.0f},{seg[1]:.0f})→({seg[2]:.0f},{seg[3]:.0f})",
                        },
                    ))
                    break  # one finding per edge-box pair is enough

    return findings


def check_text_overflow(vertices: List[Vertex]) -> List[Finding]:
    findings = []
    for v in vertices:
        text = _strip_html(v.value)  # #10: strip HTML before checking
        text = text.strip()
        if not text or v.rect.w <= 0 or v.rect.h <= 0:
            continue
        # #11: use effective font size (default 12 if None)
        fs = v.effective_font_size()
        if fs is None:
            continue

        est_w, est_h = _estimate_text_bounds(text, fs, v.rect.w)

        # Graduated severity (#P2.3): borderline overflow is WARN — the
        # estimator is approximate; draw.io may render text differently.
        # Only high-confidence overflow (>1.5x) blocks preview.
        if est_h > v.rect.h * 1.5:
            findings.append(Finding(
                severity="FAIL",
                rule="text-overflow-vertical",
                element_id=v.id,
                message=f"Text in '{v.id}' overflows vertically: "
                        f"estimated {est_h:.0f}px needed, container is {v.rect.h:.0f}px tall. "
                        f"Text: \"{text[:60]}{'...' if len(text)>60 else ''}\" "
                        f"(fontSize={fs}, width={v.rect.w:.0f})",
                detail={
                    "estimated_height": round(est_h, 1),
                    "container_height": v.rect.h,
                    "font_size": fs,
                    "text_preview": text[:100],
                },
            ))
        elif est_h > v.rect.h * 1.05:
            findings.append(Finding(
                severity="WARN",
                rule="text-overflow-vertical",
                element_id=v.id,
                message=f"Text in '{v.id}' may overflow vertically (borderline): "
                        f"estimated {est_h:.0f}px needed, container is {v.rect.h:.0f}px tall. "
                        f"Verify with screenshot — draw.io may fit the text.",
                detail={
                    "estimated_height": round(est_h, 1),
                    "container_height": v.rect.h,
                    "font_size": fs,
                    "text_preview": text[:100],
                },
            ))

        if est_w > v.rect.w * 1.5 and v.rect.w > 0:
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
                    "font_size": fs,
                    "text_preview": text[:100],
                },
            ))
        elif est_w > v.rect.w * 1.1 and v.rect.w > 0:
            findings.append(Finding(
                severity="WARN",
                rule="text-overflow-horizontal",
                element_id=v.id,
                message=f"Text in '{v.id}' may overflow horizontally (borderline): "
                        f"estimated {est_w:.0f}px needed, container is {v.rect.w:.0f}px wide. "
                        f"Verify with screenshot — draw.io may fit the text.",
                detail={
                    "estimated_width": round(est_w, 1),
                    "container_width": v.rect.w,
                    "font_size": fs,
                    "text_preview": text[:100],
                },
            ))

    return findings


def check_font_proportionality(vertices: List[Vertex]) -> List[Finding]:
    findings = []
    for v in vertices:
        if v.rect.h <= 0 or v.is_container or v.is_image:
            continue
        text = _strip_html(v.value).strip()
        if not text:
            continue
        fs = v.effective_font_size()
        if fs is None or fs <= 0:
            continue

        ratio = v.rect.h / fs
        width_ratio = v.rect.w / fs if fs > 0 else 0

        # Cavernous: box much taller than font (#11: tighter threshold, use effective font)
        if ratio > 10:
            findings.append(Finding(
                severity="WARN",
                rule="font-box-cavernous",
                element_id=v.id,
                message=f"Box '{v.id}' is {v.rect.h:.0f}px tall with effective fontSize={fs} "
                        f"(ratio {ratio:.1f}:1). Text will look tiny and lost. "
                        f"Either shrink box or increase font.",
                detail={"box_height": v.rect.h, "font_size": fs,
                         "ratio": round(ratio, 1)},
            ))

        if ratio < 1.3 and v.rect.h > 20:
            findings.append(Finding(
                severity="FAIL",
                rule="font-box-cramped",
                element_id=v.id,
                message=f"Box '{v.id}' is {v.rect.h:.0f}px tall with effective fontSize={fs} "
                        f"(ratio {ratio:.1f}:1). Text will be squeezed or clipped.",
                detail={"box_height": v.rect.h, "font_size": fs,
                         "ratio": round(ratio, 1)},
            ))

        # Widened: shape boxes with short text in very wide boxes (not just is_text)
        if width_ratio > 25 and len(_strip_html(text)) < 6:
            findings.append(Finding(
                severity="WARN",
                rule="font-box-wide-empty",
                element_id=v.id,
                message=f"Box '{v.id}' is {v.rect.w:.0f}px wide for "
                        f"effective fontSize={fs} with short text '{text}'. "
                        f"Box is disproportionately wide. Reduce width or increase font.",
                detail={"box_width": v.rect.w, "font_size": fs,
                         "text": text[:50]},
            ))

    return findings


def check_element_overlap(vertices: List[Vertex]) -> List[Finding]:
    """Check for overlapping elements. Now includes images/icons (#24) and
    skips parent-child relationships (#20)."""
    findings = []
    # Include both shapes and images (icons) in overlap check (#24)
    shapes = [v for v in vertices if (v.is_shape or v.is_image) and not v.is_container]
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            a, b = shapes[i], shapes[j]
            # Skip parent-child relationships (#20)
            if a.parent == b.id or b.parent == a.id:
                continue
            # Skip if they share the same non-"1" parent (siblings in same group)
            if a.parent == b.parent and a.parent not in ("", "1"):
                continue
            if a.rect.intersects(b.rect):
                findings.append(Finding(
                    severity="FAIL",
                    rule="element-overlap",
                    element_id=a.id,
                    message=f"Element '{a.id}' ({'icon' if a.is_image else 'shape'}) "
                            f"overlaps '{b.id}' ({'icon' if b.is_image else 'shape'}): "
                            f"({a.rect.x:.0f},{a.rect.y:.0f} {a.rect.w:.0f}×{a.rect.h:.0f}) "
                            f"vs ({b.rect.x:.0f},{b.rect.y:.0f} {b.rect.w:.0f}×{b.rect.h:.0f})",
                    detail={
                        "elem_a": a.id, "elem_b": b.id,
                        "a_type": "icon" if a.is_image else "shape",
                        "b_type": "icon" if b.is_image else "shape",
                        "rect_a": f"{a.rect.x:.0f},{a.rect.y:.0f} {a.rect.w:.0f}×{a.rect.h:.0f}",
                        "rect_b": f"{b.rect.x:.0f},{b.rect.y:.0f} {b.rect.w:.0f}×{b.rect.h:.0f}",
                    },
                ))
    return findings


def check_icon_consistency(vertices: List[Vertex]) -> List[Finding]:
    """Check icon size consistency (#24). Flags when icons vary wildly in size."""
    findings = []
    icons = [v for v in vertices if v.is_image and v.rect.w > 0 and v.rect.h > 0]
    if len(icons) < 3:
        return findings

    # Group by approximate size and check variance
    sizes = [(v.rect.w, v.rect.h) for v in icons]
    max_w = max(s[0] for s in sizes)
    min_w = min(s[0] for s in sizes)
    max_h = max(s[1] for s in sizes)
    min_h = min(s[1] for s in sizes)

    if min_w > 0 and max_w / min_w > 3:
        # Representative mid-size icon anchor for diagnostic context
        mid_icon = sorted([v for v in icons], key=lambda v: v.rect.w)[len(icons)//2]
        findings.append(Finding(
            severity="WARN",
            rule="icon-inconsistent-size",
            element_id=mid_icon.id,
            message=f"Icon sizes vary widely: {min_w:.0f}–{max_w:.0f}px wide, "
                    f"{min_h:.0f}–{max_h:.0f}px tall. "
                    f"Use consistent icon dimensions (e.g., all 24×24 or all 32×32).",
            detail={"min_w": min_w, "max_w": max_w, "min_h": min_h, "max_h": max_h,
                     "icon_count": len(icons)},
        ))

    return findings


def _cluster_by_axis(values: List[float], threshold: float) -> Dict[int, List[int]]:
    """Cluster indices by axis value, grouping values within threshold.
    Returns {cluster_key: [indices]}.
    Fixed replacement for round(y/15)*15 row grouping (#22)."""
    if not values:
        return {}
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    clusters = {}
    current_cluster = [indexed[0][0]]
    current_key = indexed[0][1]

    for idx, val in indexed[1:]:
        if abs(val - current_key) <= threshold:
            current_cluster.append(idx)
            current_key = val  # rolling anchor: compare against last-admitted value
        else:
            clusters[round(current_key)] = current_cluster
            current_cluster = [idx]
            current_key = val
    clusters[round(current_key)] = current_cluster
    return clusters


def check_spacing_variance(vertices: List[Vertex]) -> List[Finding]:
    """Check spacing consistency — now covers BOTH horizontal rows AND vertical
    columns (#21), uses cluster-based grouping (#22), and flags negative gaps
    (overlaps) instead of discarding them (#23)."""
    findings = []
    shapes = [
        v for v in vertices
        if (v.is_shape or v.is_image) and not v.is_container
        and v.rect.w > 0 and v.rect.h > 0
    ]
    if len(shapes) < 3:
        return findings

    # ---- Horizontal (row) spacing ----
    y_clusters = _cluster_by_axis([v.rect.y for v in shapes], 15)
    for key, indices in y_clusters.items():
        if len(indices) < 3:
            continue
        row_items = [shapes[i] for i in indices]
        row_items.sort(key=lambda v: v.rect.x)

        gaps = []
        overlaps = []
        for i in range(len(row_items) - 1):
            gap = row_items[i + 1].rect.x - row_items[i].rect.x2
            if gap >= 0:
                gaps.append(gap)
            else:
                overlaps.append((row_items[i].id, row_items[i + 1].id, gap))

        # Flag overlaps (#23: negative gaps → overlap FAIL, not discarded)
        for a_id, b_id, gap in overlaps:
            findings.append(Finding(
                severity="FAIL",
                rule="element-overlap-row",
                element_id=a_id,
                message=f"Boxes '{a_id}' and '{b_id}' overlap horizontally in row "
                        f"(gap={gap:.0f}px). Adjust positions.",
                detail={"box_a": a_id, "box_b": b_id, "gap": round(gap, 1)},
            ))

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
                rule="spacing-inconsistent-h",
                element_id=row_items[0].id,
                message=f"Row at y≈{row_items[0].rect.y:.0f}: horizontal gaps vary "
                        f"(gaps={[f'{g:.0f}' for g in gaps]}, "
                        f"mean={mean_gap:.0f}, cv={cv:.2f}). "
                        f"Use uniform spacing.",
                detail={
                    "row_y": round(row_items[0].rect.y),
                    "gaps": [round(g, 1) for g in gaps],
                    "mean": round(mean_gap, 1),
                    "cv": round(cv, 2),
                    "element_ids": [v.id for v in row_items],
                },
            ))

        if gaps and min(gaps) < 3:
            findings.append(Finding(
                severity="FAIL",
                rule="spacing-too-tight-h",
                element_id=row_items[0].id,
                message=f"Row at y≈{row_items[0].rect.y:.0f}: min horizontal gap is "
                        f"{min(gaps):.0f}px — elements nearly touch. Add breathing room.",
                detail={"row_y": round(row_items[0].rect.y),
                         "min_gap": round(min(gaps), 1)},
            ))

    # ---- Vertical (column) spacing (#21) ----
    x_clusters = _cluster_by_axis([v.rect.x for v in shapes], 15)
    for key, indices in x_clusters.items():
        if len(indices) < 3:
            continue
        col_items = [shapes[i] for i in indices]
        col_items.sort(key=lambda v: v.rect.y)

        gaps = []
        overlaps = []
        for i in range(len(col_items) - 1):
            gap = col_items[i + 1].rect.y - col_items[i].rect.y2
            if gap >= 0:
                gaps.append(gap)
            else:
                overlaps.append((col_items[i].id, col_items[i + 1].id, gap))

        for a_id, b_id, gap in overlaps:
            findings.append(Finding(
                severity="FAIL",
                rule="element-overlap-col",
                element_id=a_id,
                message=f"Boxes '{a_id}' and '{b_id}' overlap vertically in column "
                        f"(gap={gap:.0f}px). Adjust positions.",
                detail={"box_a": a_id, "box_b": b_id, "gap": round(gap, 1)},
            ))

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
                rule="spacing-inconsistent-v",
                element_id=col_items[0].id,
                message=f"Column at x≈{col_items[0].rect.x:.0f}: vertical gaps vary "
                        f"(gaps={[f'{g:.0f}' for g in gaps]}, "
                        f"mean={mean_gap:.0f}, cv={cv:.2f}). "
                        f"Use uniform spacing.",
                detail={
                    "col_x": round(col_items[0].rect.x),
                    "gaps": [round(g, 1) for g in gaps],
                    "mean": round(mean_gap, 1),
                    "cv": round(cv, 2),
                    "element_ids": [v.id for v in col_items],
                },
            ))

        if gaps and min(gaps) < 3:
            findings.append(Finding(
                severity="FAIL",
                rule="spacing-too-tight-v",
                element_id=col_items[0].id,
                message=f"Column at x≈{col_items[0].rect.x:.0f}: min vertical gap is "
                        f"{min(gaps):.0f}px — elements nearly touch. Add breathing room.",
                detail={"col_x": round(col_items[0].rect.x),
                         "min_gap": round(min(gaps), 1)},
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
        fs = v.effective_font_size()  # #11: use effective font (default 12)
        if fs is None:
            continue
        if fs < 7:
            findings.append(Finding(
                severity="FAIL",
                rule="font-too-small",
                element_id=v.id,
                message=f"'{v.id}' uses fontSize={v.font_size or '(inherited)'} "
                        f"(effective {fs}pt) — likely illegible. "
                        f"Minimum 8pt for body, 10pt recommended.",
                detail={"font_size": fs, "element_id": v.id, "inherited": v.font_size is None},
            ))
        if fs > 48 and v.is_text:
            findings.append(Finding(
                severity="WARN",
                rule="font-too-large",
                element_id=v.id,
                message=f"'{v.id}' uses fontSize={fs} — verify this is "
                        f"intentional (heading?) and not a copy-paste error.",
                detail={"font_size": fs, "element_id": v.id},
            ))
    return findings


def check_decoration_blocks(vertices: List[Vertex]) -> List[Finding]:
    """Detect clustered shapes that carry no semantic load.

    #6 (semantic label check): a shape whose label is just numbers,
    single chars, or whitespace is still decoration — not evaded by
    labeling cells '1 2 3 4'.

    #7 (chain-grow + bidirectional): grows clusters iteratively from
    the last added cell, checking both left and right adjacency,
    so runs of any length and in any direction are caught.
    """
    findings = []

    # Candidate decoration blocks: filled, non-container, non-image, non-text,
    # no SEMANTIC label, small-to-medium size.
    candidates = []
    for v in vertices:
        if v.is_container or v.is_image or v.is_text:
            continue
        if v.fill_color is None or v.fill_color == "none":
            continue
        if 15 <= v.rect.w <= 120 and 15 <= v.rect.h <= 120:
            # #6: check label has semantic content, not just digits/symbols
            if not _is_semantic_label(v.value):
                candidates.append(v)

    # #7: chain-grow clusters with iterative frontier expansion + bidirectional check
    visited = set()
    for seed in candidates:
        if seed.id in visited:
            continue
        cluster = [seed]
        visited.add(seed.id)

        # Grow cluster iteratively: for each member, find unvisited adjacent candidates
        idx = 0
        while idx < len(cluster):
            member = cluster[idx]
            for other in candidates:
                if other.id in visited:
                    continue
                same_row = abs(other.rect.y - member.rect.y) < 8
                same_col = abs(other.rect.x - member.rect.x) < 8
                # Check both directions (left and right, above and below)
                gap_r = abs(other.rect.x - member.rect.x2)
                gap_l = abs(member.rect.x - other.rect.x2)
                gap_b = abs(other.rect.y - member.rect.y2)
                gap_t = abs(member.rect.y - other.rect.y2)
                adjacent_row = same_row and min(gap_r, gap_l) < member.rect.w * 1.5
                adjacent_col = same_col and min(gap_b, gap_t) < member.rect.h * 1.5
                if adjacent_row or adjacent_col:
                    cluster.append(other)
                    visited.add(other.id)
            idx += 1

        if len(cluster) >= 3:
            ids = [c.id for c in cluster]
            colors = sorted({c.fill_color for c in cluster if c.fill_color})
            labels = [c.value.strip() for c in cluster if c.value.strip()]
            findings.append(Finding(
                severity="WARN",
                rule="decoration-block-cluster",
                element_id=seed.id,
                message=f"Cluster of {len(cluster)} adjacent colored shapes "
                        f"(ids: {ids[:5]}{'...' if len(ids)>5 else ''}, "
                        f"colors: {colors}, labels: {labels[:5] if labels else 'none'}). "
                        f"These look like decorative token/matrix cells copied from a "
                        f"reference without semantic content. "
                        f"Either add meaningful text labels (not just '1 2 3 4') stating "
                        f"what each cell represents, or delete the cluster and replace "
                        f"with a single labeled box. "
                        f"Paper figures use colored cells to represent REAL data "
                        f"(tokens, matrix entries) — empty or trivially labeled cells are noise.",
                detail={
                    "cluster_size": len(cluster),
                    "element_ids": ids,
                    "fill_colors": colors,
                    "labels": labels,
                    "rects": [f"{c.rect.x:.0f},{c.rect.y:.0f} {c.rect.w:.0f}×{c.rect.h:.0f}"
                              for c in cluster[:6]],
                },
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


def check_typography_hierarchy(vertices: List[Vertex]) -> List[Finding]:
    """Check that fonts have deliberate hierarchy, not all-same-size (#P1).

    A diagram where all text is 11pt has no heading/subheading/body/caption
    distinction — typical amateur output. A paper-quality figure uses
    deliberate size steps: heading ~16-18pt, subheading ~13-14pt,
    body ~10-12pt, caption ~8-9pt.
    """
    findings = []
    sizes = []
    for v in vertices:
        fs = v.effective_font_size()
        if fs is None or not v.value.strip():
            continue
        sizes.append(fs)

    if len(sizes) < 3:
        return findings

    max_sz = max(sizes)
    min_sz = min(sizes)

    # If the ratio of largest to smallest font is < 1.5, there's no
    # discernible hierarchy — everything is roughly the same size.
    if min_sz > 0 and max_sz / min_sz < 1.5:
        findings.append(Finding(
            severity="WARN",
            rule="no-typography-hierarchy",
            element_id="*",
            message=f"Font sizes range from {min_sz:.0f}pt to {max_sz:.0f}pt "
                    f"(ratio {max_sz/min_sz:.1f}:1). No visible heading/body "
                    f"hierarchy — all text is nearly the same size. "
                    f"Paper-quality figures use deliberate size steps: "
                    f"headings ~16-18pt, subheadings ~13-14pt, body ~10-12pt, "
                    f"captions ~8-9pt.",
            detail={"min_font_size": min_sz, "max_font_size": max_sz,
                     "ratio": round(max_sz / min_sz, 1) if min_sz > 0 else 0,
                     "total_text_cells": len(sizes)},
        ))

    return findings


def check_composition_density(vertices: List[Vertex], page_w: float, page_h: float) -> List[Finding]:
    """Check that the canvas isn't suspiciously empty (#P1).

    A 1600x1200 canvas with only 5 shapes is a strong signal that the
    diagram is under-developed — the agent didn't populate the layout.
    Paper figures fill their canvas with meaningful content.
    """
    findings = []
    shapes = [v for v in vertices if v.is_shape and not v.is_container and v.rect.w > 0]
    area = page_w * page_h

    if area <= 0 or len(shapes) == 0:
        return findings

    # Compute total shape area vs canvas area
    shape_area = sum(v.rect.w * v.rect.h for v in shapes)
    density = shape_area / area

    # Very low density: shapes cover < 10% of canvas
    if len(shapes) < 6 and area > 800 * 600:
        findings.append(Finding(
            severity="WARN",
            rule="low-composition-density",
            element_id="*",
            message=f"Only {len(shapes)} shapes on a {page_w:.0f}x{page_h:.0f} canvas "
                    f"(density {density:.1%}). The diagram looks sparse. "
                    f"Either reduce canvas size to fit content, or add the "
                    f"additional regions/panels/elements that a paper figure "
                    f"at this scale would normally contain.",
            detail={"shape_count": len(shapes), "canvas": f"{page_w:.0f}x{page_h:.0f}",
                     "density": round(density, 3)},
        ))

    return findings


def check_solitary_decorations(vertices: List[Vertex]) -> List[Finding]:
    """Catch individual unlabeled colored shapes (< 3 in a cluster) that
    still have no semantic label (#P1).

    check_decoration_blocks needs 3+ adjacent cells to trigger. A single
    solitary colored square with a non-semantic label is still noise.
    This rule flags the isolates.
    """
    findings = []
    for v in vertices:
        if v.is_container or v.is_image or v.is_text:
            continue
        if v.fill_color is None or v.fill_color == "none":
            continue
        if 15 <= v.rect.w <= 120 and 15 <= v.rect.h <= 120:
            if not _is_semantic_label(v.value):
                findings.append(Finding(
                    severity="WARN",
                    rule="solitary-decoration-block",
                    element_id=v.id,
                    message=f"Isolated colored shape '{v.id}' "
                            f"({v.rect.w:.0f}x{v.rect.h:.0f}, "
                            f"fill={v.fill_color}, label={repr(v.value.strip() or '')}) "
                            f"has no semantic label. If it carries no meaning, "
                            f"delete it or replace with a labeled box.",
                    detail={"element_id": v.id, "fill_color": v.fill_color,
                             "label": v.value.strip(),
                             "size": f"{v.rect.w:.0f}x{v.rect.h:.0f}"},
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
    ("icon-consistency", check_icon_consistency),
    ("spacing-variance", check_spacing_variance),
    ("color-coherence", check_color_coherence),
    ("decoration-blocks", check_decoration_blocks),
    ("solitary-decorations", check_solitary_decorations),
    ("orphan-labels", check_orphan_labels),
    ("font-size-anomalies", check_font_size_anomalies),
    ("typography-hierarchy", check_typography_hierarchy),
    ("composition-density", check_composition_density),
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
        if rule_name in ("edge-density", "composition-density"):
            findings = rule_fn(edges, page_w, page_h) if rule_name == "edge-density" else rule_fn(vertices, page_w, page_h)
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
    ap.add_argument("--json", action="store_true", help="Output JSON report")
    ap.add_argument("--output", "-o", type=Path, help="Write report to file")
    ap.add_argument("--strict", action="store_true",
                    help="Treat WARN as FAIL (for CI / handoff gate)")
    ap.add_argument("--rules", nargs="*",
                    help="Only run specific rules (name or prefix)")
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
        if rule_name in ("edge-density", "composition-density"):
            results = rule_fn(edges, page_w, page_h) if rule_name == "edge-density" else rule_fn(vertices, page_w, page_h)
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
            "fails": [{"rule": f.rule, "element_id": f.element_id,
                       "message": f.message, "detail": f.detail} for f in fails],
            "warns": [{"rule": f.rule, "element_id": f.element_id,
                       "message": f.message, "detail": f.detail} for f in warns],
            "vertex_count": len(vertices),
            "edge_count": len(edges),
            "canvas": f"{page_w:.0f}x{page_h:.0f}",
        }
        output = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(output, encoding="utf-8")
            print(f"Report written to {args.output}")
        else:
            print(output)
    else:
        # Platform-safe output: avoid emoji on Windows (✅❌ crash with GBK)
        pass_str = "PASSED" if len(fails) == 0 else "BLOCKED"
        print(f"Pre-flight report for: {args.drawio}")
        print(f"  Canvas: {page_w:.0f}x{page_h:.0f}  |  "
              f"Vertices: {len(vertices)}  |  Edges: {len(edges)}")
        print(f"  FAIL: {len(fails)}  |  WARN: {len(warns)}  |  {pass_str}")
        print()

        if fails:
            print("-- FAIL (must fix before preview) --")
            for f in fails:
                print(f"  [{f.rule}] {f.element_id}: {f.message}")

        if warns:
            print()
            print("-- WARN (review before preview) --")
            for f in warns:
                print(f"  [{f.rule}] {f.element_id}: {f.message}")

        if not findings:
            print("  All checks pass. Ready for preview.")

    return 0 if len(fails) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
