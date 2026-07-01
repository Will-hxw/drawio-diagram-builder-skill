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

## Semantic Justification (MANDATORY — The Anti-Decoration Rule)

**The #1 failure mode this protocol prevents: you copy the reference's surface (colored squares, matrix grids, token bars) without copying its meaning.** A reference figure's token bar represents real tokens. When you copy the token-bar shape into a diagram that has no token sequence, you produce meaningless colored noise.

For EVERY visual element you plan to draw, fill this justification table **before** authoring its XML:

```markdown
## Semantic Justification

| element | visual form | what it represents in the user's method | each unit corresponds to | justified? |
|---------|-------------|------------------------------------------|--------------------------|-----------|
| e.g. top-row 4 colored squares | token bar | the 4 modalities (text/image/audio/video) | one square = one modality | YES — real semantic categories |
| e.g. right-side gradient matrix | matrix grid | ??? | ??? | NO — delete or replace with labeled box |
| e.g. bottom colored strip | token bar | ??? | ??? | NO — delete |
```

**Rules:**
- If "what it represents" is empty or a question mark, the element is decoration. **Delete it or replace it with a labeled box that states the content in text.**
- A labeled box ("`Token Sequence (T=128)`") is ALWAYS preferable to an unlabeled colored shape. Always.
- Colored shapes are justified ONLY when each color/cell maps to a real, nameable category in the user's content.
- "It looks more like a paper figure" is NOT a justification. Paper figures look good because every element means something, not because they have colored shapes.

### Concrete Example Of The Failure To Prevent

**Bad (what the agent did):** Drew a 4-square blue/yellow/red/green block in the top-left of a Cog architecture diagram. The squares represent nothing — they're there because the reference image had small colored squares.

**Good:** The reference's small squares represented token positions. The Cog diagram has no token sequence at that position. So: delete the squares. Replace with a labeled box: "`Multimodal Input`" containing text labels for each input type.

### Cross-Check Against The Reference

After extraction, ask: "Did the reference use this visual form because it had the corresponding content, or because the form itself is good?" The answer is always the former. Token bars exist because there are tokens. Matrix grids exist because there are matrices. The form follows the content. If your content doesn't have the thing, don't use the form.

## How To Extract The RIGHT Things

When you look at a reference image, your instinct will be to copy the visible shapes. Resist this. Extract instead:

1. **Composition** — how many regions? how are they arranged? where is the main flow? (This is the essence. Copy freely.)
2. **Density** — how many elements per region? how full is each region? (Copy the density level.)
3. **Hierarchy** — what is the heading/subheading/body/caption structure? (Copy the hierarchy, not the words.)
4. **Spacing rhythm** — what are the gap sizes between regions, between elements? (Copy the numbers.)
5. **Palette** — what colors, used for what semantic categories? (Copy the palette and the category-mapping, not "color #3 goes top-right.")
6. **Arrow grammar** — how are data/control/feedback distinguished? (Copy the visual distinction.)
7. **Typography** — font sizes per hierarchy level? (Copy the sizes per level.)

Do NOT extract:
- Specific decorative shapes and reproduce them without the underlying content
- A colorful block because "the reference had a colorful block"
- A matrix grid because "the reference had a grid"
- Anything whose meaning in the reference you cannot explain

The reference is good because of points 1-7, not because of its decorative shapes. Learn 1-7. Leave the decorative shapes unless your content matches their semantics.

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
