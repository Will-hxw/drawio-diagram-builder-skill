# Editable Primitive Icon Recipes

Use these recipes when a research figure needs small icons but exact source assets are unavailable. The goal is not decorative icon design; the goal is consistent, editable, recognizable primitives that survive draw.io editing and screenshot comparison.

For higher visual fidelity with generic icons, the skill also bundles MIT-licensed SVG assets under `assets/icons/`. Use those assets when a clean vector symbol matters more than object-level primitive editability. Use this file when the icon should be built from editable draw.io cells or when the reference has a hand-built paper-figure style.

## Rules

- Build icons from draw.io rectangles, ellipses, triangles, lines, arcs/connectors, and short text glyphs.
- Keep each icon inside an explicit bounding box `(x, y, w, h)` and record that box in `asset-ledger.md`.
- Use the same stroke width, corner radius, and scale for repeated icons in one figure.
- Put icon cells above background fills and below labels unless the reference places labels inside the icon.
- Do not use a generic symbol when the reference meaning is specific. If the recipe is insufficient, list the gap in `asset-ledger.md`.

Default small-icon style:

```text
strokeColor=#4f5d6b;strokeWidth=1.5;fillColor=#ffffff;whiteSpace=wrap;html=1;
```

Scale the coordinates below from a `24 x 24` box unless noted.

## Document Or Text

Meaning: note, instruction, title, record, text stream.

Cells:

- page rectangle: `x+4,y+3,w=16,h=18`, white fill, gray stroke
- folded corner triangle: points near `(x+15,y+3) -> (x+20,y+8) -> (x+15,y+8)`, pale fill
- text lines: three thin horizontal lines at `y+9`, `y+13`, `y+17`

Use for: paper sheets, "note content", instruction cards.

## Image

Meaning: image modality, screenshot, visual input.

Cells:

- frame rectangle: `x+3,y+4,w=18,h=16`
- sun dot: small ellipse `x+15,y+7,w=3,h=3`
- mountain polyline: `(x+5,y+18) -> (x+10,y+12) -> (x+14,y+16) -> (x+18,y+10) -> (x+21,y+18)`

Use muted blue or pale cyan fills when the reference uses modality colors.

## Audio

Meaning: audio modality or sound token.

Cells:

- speaker body: small rectangle `x+4,y+10,w=5,h=6`
- speaker horn: triangle/polygon from `(x+9,y+10)`, `(x+14,y+6)`, `(x+14,y+20)`, `(x+9,y+16)`
- sound waves: two curved connectors or arcs on the right, no fill

If arcs are hard in the target generator, use two short curved connectors with `curved=1;endArrow=none`.

## Video

Meaning: video stream, playback, temporal input.

Cells:

- rounded frame: `x+3,y+5,w=18,h=14`
- top clapper stripe: thin rectangle or alternating dark small bars at `y+5`
- play triangle: centered triangle inside the frame

Keep the play triangle direction consistent with the reference.

## Retrieval

Meaning: retrieval document, search, external lookup.

Cells:

- small document rectangle at `x+3,y+4,w=12,h=15`
- magnifier lens: ellipse `x+12,y+12,w=7,h=7`
- handle: diagonal line from `(x+18,y+18)` to `(x+22,y+22)`

Avoid replacing retrieval with a plain database icon unless the reference uses a database cylinder.

## Tools

Meaning: tools, APIs, actions, external utilities.

Cells:

- wrench approximation: diagonal thick line with small open circle at one end
- screwdriver approximation: crossing diagonal line with small rectangular handle
- optional sparkle/dot if the reference uses a tool-call marker

For tiny icons, a crossed-tools primitive is clearer than detailed teeth.

## Stacked Memory

Meaning: memory bank, cache, slots, layered storage.

Cells:

- three rounded rectangles offset by `(2,2)`, each `w=16,h=6`
- back layers use lighter fill; front layer uses the primary memory color
- optional tiny label block inside the front rectangle

Use this for working cache, episodic memory, semantic memory, and key-value packets.

## Clock Or Temporal Trace

Meaning: time, temporal traces, history.

Cells:

- circle `x+4,y+4,w=16,h=16`
- hour hand line from center to `(x+12,y+8)`
- minute hand line from center to `(x+16,y+12)`
- optional tiny tick marks at top/right/bottom/left

Keep hands simple; detailed clock faces blur at paper-figure scale.

## Warning

Meaning: risk, alert, context growth warning.

Cells:

- triangle outline or filled pale red triangle
- exclamation mark as text or a vertical line plus dot

Use a red/orange stroke, but keep it consistent with the figure palette.

## Gauge Or Uncertainty

Meaning: score, uncertainty, routing confidence.

Cells:

- semicircle arc or curved connector from left to right
- small tick marks on the arc
- needle line from center to upper-right
- optional small center dot

If draw.io arc geometry is unreliable, use three short curved connectors to approximate the semicircle.

## Primitive Icon Ledger Entry

Record each icon family in `asset-ledger.md`:

```markdown
| id | built from | fidelity notes |
| image_stream_icon | primitive-icons.md image recipe; rectangle, dot, mountain polyline | editable approximation; no source bitmap available |
```

If the reference uses a branded logo, molecule, neural-network symbol, or paper-specific mark that these recipes cannot capture, do not force-fit it. Mark it as an approximation or missing asset and ask for the source if exact fidelity matters.
