---
name: drawio-diagram-builder
description: Create, edit, replicate, and iteratively refine editable diagrams.net/draw.io diagrams (.drawio XML) from prompts, papers, repositories, screenshots, or existing diagrams. Use when asked to generate a draw.io file, reproduce a reference figure, avoid drawio MCP long-URL failures, preview through a browser, compare screenshots, or fix diagram layout problems such as text overlap, arrows, colors, icons, fonts, and component alignment.
---

# Draw.io Diagram Builder

## Core Principle

Produce an editable draw.io diagram first. Do not use an embedded screenshot as the final answer when the user asks for redraw, replica, vector, editable, or 100% reproduction. Raster images may be used only as references, temporary overlays, or explicitly approved assets.

Prefer direct `.drawio` XML authoring plus browser screenshot feedback for complex or high-fidelity diagrams. Use local draw.io UI control only when it materially improves inspection or user handoff.

## Tool Strategy

Use this priority order:

1. **Direct `.drawio` XML generation/editing** for reliable, reproducible diagrams.
2. **Local preview HTML + diagrams.net iframe postMessage** for large diagrams and Windows reliability.
3. **Browser automation screenshots** for verification and iterative refinement.
4. **drawio MCP / `@drawio/mcp`** only for small diagrams or quick opening. On Windows, large encoded URLs can fail with `The data area passed to a system call is too small`; do not rely on `.url` shortcuts for large XML.
5. **draw.io desktop/CLI export** if installed. Treat it as optional; always have the local iframe preview fallback.

Use `references/drawio-workflow.md` for the detailed end-to-end process. Use `references/xml-authoring.md` when writing or repairing XML shapes, styles, edges, and text layout.

## Standard Workflow

1. **Collect input context**
   - Read the user's prompt, reference images, paper sections, codebase files, or domain notes.
   - Identify whether the task is conceptual diagram creation, visual replication, architecture diagramming, paper figure recreation, or iterative polish.
   - If exact assets are needed, locate them locally or ask for them. Do not silently replace a required logo/icon with an unrelated one.

2. **Extract the visual specification**
   - Record canvas size, major regions, hierarchy, labels, colors, line styles, fonts, arrows, icons, captions, and spacing.
   - For reference-image replication, create a coordinate-level inventory: bounding boxes, text lines, highlight bars, connectors, loops, and repeated blocks.
   - Decide what must be exact and what can be approximated.

3. **Author the `.drawio` file**
   - Use one `mxfile` with one or more `diagram` pages.
   - Use explicit `mxGeometry` positions and sizes for high-fidelity work.
   - Split dense text into multiple cells when line-level alignment matters.
   - Build important icons and arrows with editable draw.io primitives when possible.
   - Keep colors, strokes, fonts, and rounded corners consistent with the reference or requested style.

4. **Preview without long URLs**
   - Prefer `scripts/serve_drawio_preview.py` for a one-command local preview.
   - Or generate a local preview page using `scripts/make_drawio_preview.py` and serve the folder with a short local URL:
     ```powershell
     python -m http.server 8765 --bind 127.0.0.1
     ```
   - Open `http://127.0.0.1:8765/<preview>.html` with browser automation.
   - Screenshot the editor/preview state and inspect the rendered result.

5. **Iterate from evidence**
   - Compare the screenshot against the reference or requested spec.
   - Fix a small batch of concrete issues per pass: text overflow, a bad arrow, one misaligned block, wrong color, incorrect icon, spacing, or missing component.
   - Rebuild preview, refresh with a cache-busting query string, screenshot again, and repeat.
   - In user updates, name the specific defects being fixed rather than claiming broad perfection.

6. **Validate before handoff**
   - Run `scripts/validate_drawio.py`.
   - Confirm the file parses, page count is expected, no unwanted embedded raster images exist, captions are included or removed according to the request, and the latest screenshot was reviewed.
   - Provide the `.drawio` path and the latest screenshot path. Keep the local preview URL available if the user wants to continue iterating.

## Editing Rules

- Use `apply_patch` or structured XML scripts for manual file edits.
- Preserve user files and unrelated generated files.
- Keep a working copy and a handoff copy only when useful; keep them synchronized.
- Never claim the diagram is complete without visual verification.
- When the user asks for "100% reproduction", treat that as an iterative standard: keep finding and fixing visible differences until the user accepts or identifies the next issues.

## Common Failure Handling

- **Windows long URL failure**: Do not open large diagrams through `.url` files or huge hash URLs. Use local preview HTML with postMessage.
- **Saving from preview**: The local preview cannot silently overwrite local files because browser sandboxes block arbitrary filesystem writes. Use the save-enabled preview page to download the edited `.drawio`, or ask the user where to place the downloaded file before continuing.
- **Text overlap or overflow**: Split paragraphs into smaller text cells, reduce font size, increase container width, set stable geometry, and screenshot-check.
- **Misaligned highlight bars**: Put highlight rectangles behind individual text lines, not behind the whole paragraph.
- **Ugly loop arrows**: Use editable curved connectors or arcs, not large Unicode arrow glyphs, unless the reference explicitly uses glyphs.
- **Wrong icon fidelity**: Build editable approximations from primitives, or ask for/download the exact icon when exactness matters.
- **Stale preview**: Add a query string such as `?rev=3`, regenerate preview HTML, or reopen the tab.
- **Editor chrome hiding details**: Resize viewport, zoom inside draw.io, or export a PNG when draw.io CLI is available.

## Bundled Helpers

- `scripts/make_drawio_preview.py`: build a local short-URL preview HTML that loads a `.drawio` XML file into diagrams.net via `postMessage`.
- `scripts/serve_drawio_preview.py`: generate the preview HTML and serve it on `127.0.0.1` with an optional browser launch.
- `scripts/validate_drawio.py`: parse and sanity-check `.drawio` files before handoff.
- `references/drawio-workflow.md`: full professional workflow for prompt/paper/code/reference-image to editable draw.io.
- `references/xml-authoring.md`: XML, layout, style, edge, text, icon, and iteration patterns.
