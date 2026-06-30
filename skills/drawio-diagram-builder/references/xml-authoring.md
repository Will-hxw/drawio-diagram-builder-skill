# Draw.io XML Authoring Notes

## File Structure

A minimal editable draw.io file is:

```xml
<mxfile host="app.diagrams.net" agent="Codex" version="26.0.9" pages="1">
  <diagram id="page-id" name="Page Name">
    <mxGraphModel page="1" pageWidth="1718" pageHeight="728" grid="1" gridSize="10">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        ...
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Use stable IDs. Human-readable IDs help iterative repairs (`stage1_box`, `reward_loop_a`, `ad_line_03`).

## Shapes

Common styles:

- Rounded rectangle:
  `rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor=#ffffff;strokeColor=#b7b7b7;strokeWidth=2;`
- Dashed container:
  `rounded=1;dashed=1;dashPattern=8 8;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#b7b7b7;strokeWidth=2;`
- Text-only:
  `text;html=1;strokeColor=none;fillColor=none;whiteSpace=wrap;overflow=visible;fontFamily=Comic Sans MS;`
- Ellipse:
  `ellipse;whiteSpace=wrap;html=1;fillColor=#dcecff;strokeColor=#000000;`
- Cylinder:
  `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;`

Set explicit geometry:

```xml
<mxCell id="box" value="" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="200" height="80" as="geometry" />
</mxCell>
```

## Text Layout

Draw.io text rendering can shift between editor, embed, and export. For high fidelity:

- Use one cell per visually important line.
- Put highlight rectangles behind those individual line cells.
- Avoid long wrapped HTML paragraphs when exact line breaks matter.
- Reduce font size before allowing text to escape its container.
- Prefer `whiteSpace=wrap` with fixed geometry for bounded labels.
- Use `overflow=visible` only for standalone labels that have no enclosing box.
- Keep `fontFamily` explicit. If the user requests Comic Sans MS, set it on every text cell that matters.

For rich text:

```xml
value="&lt;b&gt;&lt;font color=&quot;#b31313&quot;&gt;Title&lt;/font&gt;&lt;/b&gt;"
```

Escape `<`, `>`, and quotes inside attributes.

## Edges and Arrows

For straight or orthogonal edges:

```xml
<mxCell id="edge1" value="Input"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;endFill=1;strokeWidth=2;strokeColor=#9c9c9c;fontFamily=Comic Sans MS;"
  edge="1" parent="1" source="source_id" target="target_id">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

For exact manual route, use source/target points and optional bend points:

```xml
<mxCell id="edge2" value="" style="edgeStyle=orthogonalEdgeStyle;endArrow=classic;html=1;" edge="1" parent="1">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="100" y="120" as="sourcePoint" />
    <mxPoint x="250" y="120" as="targetPoint" />
    <Array as="points">
      <mxPoint x="160" y="120" />
      <mxPoint x="160" y="180" />
    </Array>
  </mxGeometry>
</mxCell>
```

For loop arrows, avoid giant Unicode glyphs when fidelity matters. Use two editable curved connectors:

```xml
<mxCell id="loop_a" value=""
  style="curved=1;endArrow=classic;endFill=1;html=1;rounded=1;strokeWidth=6;strokeColor=#8aa08e;opacity=70;"
  edge="1" parent="1">
  <mxGeometry relative="1" as="geometry">
    <mxPoint x="735" y="295" as="sourcePoint" />
    <mxPoint x="784" y="238" as="targetPoint" />
    <Array as="points">
      <mxPoint x="723" y="267" />
      <mxPoint x="752" y="239" />
    </Array>
  </mxGeometry>
</mxCell>
```

Create a second curved connector in the opposite direction to form a recycle loop.

## Icons

Use this decision order:

1. Exact user-provided icon/logo.
2. Exact downloadable icon from an allowed source, with provenance.
3. Editable approximation using draw.io primitives.
4. Simple symbolic substitute, explicitly disclosed.

For maximum editability, build icons from small rectangles, ellipses, lines, and text symbols. If using embedded SVG/image assets, keep the source file and explain that the icon itself is not fully primitive-editable.

## Color and Style Matching

Sample colors from the reference when possible. Keep a palette table during work:

- red headings
- green stage titles/model labels
- blue result labels/highlights
- orange reward accents
- gray dashed containers
- pale fills

Use consistent stroke widths. Publication figures often use:

- 1-1.5 px for small icon outlines
- 2 px for normal boxes and arrows
- 3-6 px for large loop arrows
- dash patterns such as `8 8` for stage/container borders

## Validation Checklist

Before handoff:

- XML parses.
- Page dimensions are intentional.
- No accidental `data:image/png` or `data:image/jpeg` exists when final must be editable.
- Text does not overflow important boxes in the latest screenshot.
- Highlight rectangles sit behind the intended text lines.
- Arrowheads, bend points, and labels match the intended flow.
- Caption is present only if requested.
- Preview HTML was regenerated after the last XML edit.
- If the user edited inside the preview, the saved/downloaded `.drawio` file has been copied back into the working path before further XML edits.
