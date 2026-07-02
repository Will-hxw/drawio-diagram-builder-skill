# XML Pre-Flight Quality Checks

## Why This Exists

When you write `<mxCell x="220" y="140" width="60" height="40" fontSize="8"/>`, you cannot see the rendered result. The model is blind to:

- Text that will overflow its container
- Arrows whose coordinates pass straight through boxes
- Boxes 200px tall containing 8pt text (hollow, amateur look)
- Five adjacent boxes with gaps of 12, 47, 8, 33 pixels (no rhythm)
- A palette built by picking random colors per element

These defects are **computable from geometry alone**. You do not need a screenshot to detect them. You need to run the numbers.

Catching these before the first render eliminates the "first screenshot is garbage" problem. The first render should already pass basic hygiene.

## Mandatory Pre-Flight

**After writing `.drawio` XML and before generating the first preview HTML, run:**

```powershell
python <skill-dir>/scripts/validate_visual_quality.py <file>.drawio --json --output preflight-report.json
```

Read the JSON report. Every `WARN` and `FAIL` must be addressed. Do not proceed to preview until:
- Zero FAIL items remain
- Every WARN item has been reviewed and either fixed or documented with a reason why it is acceptable

## What The Pre-Flight Catches (Without Rendering)

### 1. Arrow–Box Collision (FAIL)

Every edge path (source → waypoints → target) is tested against every vertex bounding rectangle. If an arrow segment intersects a box that is neither its source nor its target, it is flagged.

This catches: arrows cutting diagonally through unrelated boxes, connectors crossing text regions, waypoint-based paths that collide with shapes.

### 2. Text Overflow Risk (FAIL — with graduated severity)

Estimated text rendering bounds vs container geometry:
- `estimated_width ≈ char_count × font_size × 0.55` (Latin) or `× 0.9` (CJK) — approximate; draw.io may render differently
- `estimated_height ≈ line_count × font_size × 1.35`
- If estimated > container × 1.5 → FAIL (high-confidence overflow — text will definitely not fit)
- If estimated > container × 1.1 but ≤ 1.5 → WARN (borderline — screenshot will reveal the truth)
- If estimated ≤ container → pass

This catches: tiny boxes with long labels, multi-line text stuffed into single-line containers, CJK text that is wider than the model assumed. Borderline cases are WARN, not FAIL — the approximate estimator should not block preview when text MAY actually fit.

### 3. Font–Container Proportionality (WARN)

- `box_height / font_size > 10` → box is cavernous, text will look lost
- `box_height / font_size < 1.5` → text likely clipped or touching borders
- `box_width / (font_size × 0.6) < len(text) × 0.5` → text likely wider than box

This catches: "big box, tiny text" amateur look and "text crammed into a matchbox."

### 4. Element Overlap (FAIL)

Two non-container, non-background vertices whose bounding rectangles intersect. Layout elements should not overlap unless one is explicitly a parent container.

This catches: shapes placed on top of each other, text cells overlapping arrows, accidental z-order issues visible in geometry.

### 4.5 Icon Consistency (WARN)

Icons (image elements) are checked for size consistency:
- If the largest icon is >3× the size of the smallest icon across the diagram → WARN

This catches: a 60px icon next to 16px icons in the same row — a common amateur inconsistency that makes the figure look sloppy.

### 5. Spacing Variance (WARN)

For elements in the same row (y within 10px) or column (x within 10px):
- Compute all horizontal gaps between adjacent elements
- Flag if coefficient of variation (stddev/mean) > 0.5
- Flag if min_gap < 4px (elements nearly touching) or max_gap > 4× min_gap

This catches: "here tight, there loose" inconsistent rhythm — a hallmark of machine-generated layout.

### 6. Color Palette Coherence (WARN)

Count distinct fill colors and stroke colors across all vertices:
- > 8 distinct fill colors → palette is scattered
- > 6 distinct stroke colors → no unified stroke language
- Mix of warm and cool tones with no apparent system

This catches: "rainbow vomit" — each shape picked its own color.

### 7. Orphan & Missing Labels (WARN)

- Edge without `value` attribute → arrow has no semantic label
- Vertex with `value=""` where width > 60 and height > 30 → empty box, probably forgotten text
- Edge with `source` or `target` referencing a non-existent cell id → broken reference

This catches: arrows that should say "gradient", "feedback", "query" but are blank. Empty boxes.

### 8. Font Size Anomalies (WARN)

- `fontSize < 7` → likely unreadable at normal zoom
- `fontSize > 48` → likely a heading, but check if it's accidentally applied to body text

This catches: text that will be illegible before any rendering happens.

### 9. Edge Density Hotspots (WARN)

Grid the canvas into 200×200px cells. Count edges passing through each cell.
- > 5 edges in one cell → likely arrow spaghetti

This catches: regions where so many arrows converge that the reader cannot trace any of them.

### 10. Decoration Block Clusters (WARN)

Detects clusters of 3+ adjacent unlabeled colored shapes (15–120px each). These are almost certainly decorative token-bar / matrix-grid cells copied from a reference figure without any semantic content behind them.

This catches the #1 amateur failure: an agent sees small colored squares in a top-conference reference and reproduces them in its own diagram — but the reference's squares represented real tokens/matrices, while the agent's squares represent nothing. The result is meaningless visual noise.

Fix: either add a text label to each cell stating what it represents ("text", "image", "audio", "video" for a 4-modality token bar), or delete the cluster entirely and replace with a single labeled box. See `topconf-paper-style.md` "The First Principle" and `style-extraction.md` "Semantic Justification."

### 11. Solitary Decorations (WARN)

Catches individual isolated colored shapes (15–120px) that carry no semantic label — "below the cluster threshold" of rule #10. A single decorative square is still noise.

This catches: a lone colored rectangle labeled "x" or "1" — the decoration-blocks check needs 3+ adjacent cells to fire, so individual decorations slip through. This rule catches the isolates.

### 12. Typography Hierarchy (WARN)

Checks whether font sizes form a deliberate hierarchy. If the ratio of the largest to smallest font size is < 1.5 (all text is near-identical), the diagram lacks heading/subheading/body/caption distinction.

This catches: every text element at 11-12pt with no visual hierarchy — typical amateur output. Paper-quality figures use deliberate size steps: headings ~16-18pt, subheadings ~13-14pt, body ~10-12pt, captions ~8-9pt.

### 13. Composition Density (WARN)

Checks whether the canvas is suspiciously empty. If the diagram has < 6 shapes on a canvas > 800×600, the layout is under-developed.

This catches: a 1600×1200 canvas with only 4 boxes — the diagram looks sparse and unfinished. Either reduce canvas size to fit content, or populate the additional regions a paper figure at this scale would normally contain.

## What The Pre-Flight CANNOT Catch (Still Needs Screenshot)

- **Aesthetic judgment**: a color combination that is "ugly" but within palette limits
- **Font rendering quirks**: draw.io may kern or wrap differently than estimated
- **Z-order visual issues**: a background rectangle covering text (geometry is correct, rendering is wrong)
- **Style match to reference**: "does this look like a NeurIPS figure?" requires visual comparison
- **Semantic correctness**: does the arrow mean the right thing?

The pre-flight catches **computable** defects. The screenshot loop catches **perceptual** defects. Both are mandatory.

## Integration With The Workflow

```
Author XML → validate_visual_quality.py → fix FAILs → fix WARNs
    ↓
  (only after pre-flight passes)
    ↓
Preview HTML → Screenshot → Self-Supervision → Defect Log → Iterate
```

Do not skip pre-flight. A first screenshot that is structurally broken wastes an entire iteration loop. A pre-flight that catches 15 geometry problems before the first render saves 3-4 screenshot cycles.
