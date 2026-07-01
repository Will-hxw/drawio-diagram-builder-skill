# Style Extraction Protocol

## Why This Exists

You were given reference images as style guides. You looked at them. Then you drew a diagram that looks nothing like them — wrong palette, wrong typography, wrong density, wrong everything.

This happens because you did not **extract** the style. You glanced at the images and moved on. "Looking" is not extraction. Extraction means writing down concrete, actionable style parameters that you can apply to your own diagram.

This protocol is mandatory when the user provides reference images as style sources (not for exact replication — that's `reference-replication-protocol.md`).

## The Rule

**You may not draw a single `<mxCell>` until you have completed the style extraction table below.** If you cannot fill a row, you do not understand the reference well enough to draw.

## Style Extraction Table

For each reference image provided, fill this table before authoring XML:

```markdown
## Style Extraction: [image name]

### 1. Palette (sample exact hex codes from the image)
| role | hex | used on |
|------|-----|---------|
| background | #______ | |
| primary fill | #______ | |
| secondary fill | #______ | |
| accent / highlight | #______ | |
| border stroke | #______ | |
| arrow stroke | #______ | |
| heading text | #______ | |
| body text | #______ | |
| muted / gray | #______ | |
| special (e.g. orange for loss) | #______ | |

Total distinct colors: ____ (should be 5-8 for a coherent palette)

### 2. Typography
- Heading font: ___________  size: ___pt  weight: ________
- Subheading font: ___________  size: ___pt
- Body text font: ___________  size: ___pt
- Small label / caption font: ___________  size: ___pt
- Code / mono font (if any): ___________  size: ___pt

### 3. Shape Language
- Corner radius: ___px (or "sharp" / "subtle" / "pill")
- Stroke width for boxes: ___px
- Stroke width for arrows: ___px
- Dash pattern for containers: ____ (e.g. "8 8")
- Shadow: yes / no  |  opacity: ___%  |  offset: (_, _)
- Fill opacity for background regions: ___%

### 4. Layout Rhythm
- Outer margin (canvas edge to first content): ___px each side
- Gap between major regions (vertical): ___px
- Gap between same-row elements (horizontal): ___px
- Padding inside boxes (text to border): ___px vertical, ___px horizontal
- Typical box width: ___px  |  height: ___px
- Grid alignment: ___px grid (i.e. all positions multiples of __)

### 5. Arrow Grammar
- Default arrow type: __________ (e.g. "classic", "block", "open")
- Arrow color: #______
- Arrowhead size: small / medium / large
- Routing style: straight / orthogonal / curved
- Do arrows have labels? yes / no  |  font size: ___pt
- Do arrows use color coding by meaning? yes / no

### 6. Icon Language
- Icon style: outline / filled / duotone / minimal
- Icon size: ___px × ___px (typical)
- Icon stroke width: ___px
- Are icons color-coded by category? yes / no
- Source: bundled Tabler SVGs / user-provided / must download

### 7. Density & Composition
- Diagram type: pipeline / layered / grid / tree / swimlane / feedback loop
- Number of major regions: ___
- Content density: sparse / medium / dense / very dense
- Use of whitespace: generous / moderate / tight
- Panel labels: A/B/C style / numbered / named / none
- Legend: yes / no  |  position: __________
- Caption below diagram: yes / no
```

## How To Use The Extracted Style

After filling the table, the extracted values become your **style contract**. You are not allowed to deviate from them unless you have a specific, documented reason.

When authoring XML:
1. Set your palette to exactly the hex codes you extracted. Do not pick random colors.
2. Set your font sizes to exactly the extracted values. Do not eyeball it.
3. Match the corner radius, stroke width, and dash pattern exactly.
4. Use the same gap values between all same-type elements. Consistency is the cheapest way to look professional.
5. Mirror the arrow grammar: same type, same color, same routing style.

## When Style Extraction Fails

If you extract styles and the diagram still looks wrong, check:

- **Did you actually use the extracted values?** Writing down `#3a7bd5` and then using `#4a90d9` in XML is not using the extracted value.
- **Did you apply them consistently?** One box with 12px corner radius and another with 4px looks random even if both values are "fine."
- **Did you match density?** A "dense" reference with 15 boxes in 1200×800 cannot be replicated by 4 boxes on the same canvas. The density IS the style.
- **Did you copy the composition?** If the reference has a top-band-of-icons → middle-pipeline → bottom-evaluation layout, and you drew left-right-flow, you ignored the structure.

## Multi-Reference Style Synthesis

When multiple reference images are provided, they share a common visual language. Extract each one separately, then synthesize:

```markdown
## Synthesized Style Contract

### Common across all references
| parameter | value | evidence |
|-----------|-------|----------|
| ... | ... | |

### Variations per reference (if any)
| parameter | ref 1 | ref 2 | ref 3 | chosen |
|-----------|-------|-------|-------|--------|
| ... | ... | ... | ... | ... |
```

If the references conflict on a parameter (e.g., one has blue headings, another green), pick one and document the choice. Don't average — pick.
