---
name: drawio-diagram-builder
description: Create, edit, replicate, and iteratively refine editable research and technical diagrams in diagrams.net/draw.io (.drawio XML) from prompts, papers, repositories, screenshots, or existing diagrams. Use when asked to generate a scientific figure, paper method diagram, ML/system architecture diagram, draw.io file, reference figure reproduction, browser screenshot feedback loop, Windows-safe draw.io preview, or layout fixes for text overlap, arrows, colors, icons, fonts, and component alignment.
---

# Research Draw.io Diagram Builder

## Prerequisites

Before starting, verify these are available. If anything is missing, tell the user immediately — do not proceed without them.

| Requirement | Why |
|-------------|-----|
| **Python 3** (3.7+) | All preview/validation scripts are Python. Run `python --version` to check. |
| **Browser automation** | The iterative refinement loop depends on taking screenshots of a local preview. You need one of: Playwright MCP, Puppeteer MCP, browser-evaluate/screenshot tools, or equivalent. |
| **Internet access** | Preview loads `https://embed.diagrams.net/` in an iframe. Offline won't work. |
| **File write access** | You will create `.drawio` files. |

Script paths in this document are relative to the skill directory. Resolve them like `<skill-dir>/scripts/serve_drawio_preview.py`. If you can't find the skill directory, look under the agent's installed skills path (e.g., `~/.claude/skills/drawio-diagram-builder/` or `~/.codex/skills/drawio-diagram-builder/`).

## Core Principle

Produce an editable draw.io diagram first, especially for research and technical figures. Do not use an embedded screenshot as the final answer when the user asks for redraw, replica, vector, editable, or 100% reproduction. Raster images may be used only as references, temporary overlays, or explicitly approved assets.

Prefer direct `.drawio` XML authoring plus browser screenshot feedback for complex or high-fidelity diagrams. Use local draw.io UI control only when it materially improves inspection or user handoff.

## Tool Strategy

Use this priority order:

1. **Direct `.drawio` XML generation/editing** — reliable, reproducible. Write XML with explicit `mxGeometry` positions.
2. **Local preview HTML + diagrams.net iframe postMessage** — run `scripts/serve_drawio_preview.py` (one command, starts server + opens browser) or `scripts/make_drawio_preview.py` + `python -m http.server`. This keeps the browser URL short, avoiding the Windows long-URL crash.
3. **Browser automation screenshots** — navigate browser to `http://127.0.0.1:<port>/drawio-preview.html`, wait for the draw.io embed to load (2-5 seconds), take a full-page or viewport screenshot. This is the evidence you compare against the reference.
4. **draw.io MCP / `@drawio/mcp`** — only for small diagrams or quick opening. On Windows, large encoded URLs fail with `The data area passed to a system call is too small`; do not rely on `.url` shortcuts for large XML.
5. **draw.io desktop/CLI export** — if installed. Treat as optional; always have the local iframe preview fallback.

Load `references/drawio-workflow.md` for the detailed end-to-end process. Load `references/xml-authoring.md` when writing or repairing XML shapes, styles, edges, and text layout. Resolve both relative to the skill directory.

## Standard Workflow

1. **Verify prerequisites** — confirm Python 3 and browser automation are available. If not, stop and tell the user what's missing.

2. **Collect input context**
   - Read the user's prompt, reference images, paper sections, codebase files, or domain notes.
   - Identify the task type: research figure creation, paper-method diagramming, visual replication, architecture diagramming, repository diagramming, or iterative polish.
   - If exact assets are needed, locate them locally or ask for them. Do not silently replace a required logo/icon with an unrelated one.

3. **Extract the visual specification**
   - Record canvas size, major regions, hierarchy, labels, colors, line styles, fonts, arrows, icons, captions, and spacing.
   - For reference-image replication, create a coordinate-level inventory: bounding boxes, text lines, highlight bars, connectors, loops, and repeated blocks.
   - For paper figures, preserve exact method terminology and distinguish data construction, training, evaluation, inference, and serving flows.
   - Decide what must be exact and what can be approximated.

4. **Author the `.drawio` file**
   - Use one `mxfile` with one or more `diagram` pages.
   - Use explicit `mxGeometry` positions and sizes for high-fidelity work.
   - Split dense text into multiple cells when line-level alignment matters.
   - Build important icons and arrows with editable draw.io primitives when possible.
   - Keep colors, strokes, fonts, and rounded corners consistent with the reference or requested style.

5. **Preview without long URLs**
   - **Preferred**: run `scripts/serve_drawio_preview.py <file>.drawio --port 8765`. It generates the preview HTML, starts a server, and opens the browser.
   - **Manual**: run `scripts/make_drawio_preview.py <file>.drawio --out drawio-preview.html`, then `python -m http.server 8765 --bind 127.0.0.1` in the output directory.
   - Open `http://127.0.0.1:8765/drawio-preview.html?rev=1` in the browser.
   - Wait 2-5 seconds for the diagrams.net embed iframe to initialize.
   - Take a screenshot of the rendered diagram.

6. **Iterate from evidence**
   - Compare the screenshot against the reference or requested spec.
   - Fix a small batch of concrete issues per pass: text overflow, a bad arrow, one misaligned block, wrong color, incorrect icon, spacing, or missing component.
   - Regenerate the preview HTML, refresh the browser (add a cache-busting `?rev=N`), screenshot again, and repeat.
   - Name the specific defects being fixed rather than claiming broad perfection.

7. **Validate before handoff**
   - Run `scripts/validate_drawio.py <file>.drawio`.
   - Confirm: XML parses, page count is expected, no unwanted embedded raster images, captions included/removed as requested, latest screenshot reviewed.
   - Provide the `.drawio` path and the latest screenshot path. Leave the local preview server running if the user wants to continue iterating.

## Editing Rules

- Edit `.drawio` files by writing or patching XML directly. For small targeted fixes, use the file editing tool (e.g., Edit/Write in Claude Code).
- Preserve user files and unrelated generated files.
- Keep a working copy and a handoff copy only when useful; keep them synchronized.
- Never claim the diagram is complete without visual verification (a screenshot).
- When the user asks for "100% reproduction", treat that as an iterative standard: keep finding and fixing visible differences until the user accepts or identifies next issues.

## Common Failure Handling

- **Windows long URL failure**: Do not open large diagrams through `.url` files or huge `#create=` URLs. Use local preview HTML with postMessage.
- **Saving from preview**: The local preview cannot silently overwrite local files (browser sandbox). The blue Save button triggers a `.drawio` download. Move the downloaded file back to your working path before further edits.
- **Text overlap or overflow**: Split paragraphs into smaller text cells, reduce font size, increase container width, set stable geometry, and screenshot-check.
- **Misaligned highlight bars**: Put highlight rectangles behind individual text lines, not behind the whole paragraph.
- **Ugly loop arrows**: Use editable curved connectors or arcs, not large Unicode arrow glyphs, unless the reference explicitly uses glyphs.
- **Wrong icon fidelity**: Build editable approximations from primitives, or ask for/download the exact icon when exactness matters.
- **Stale preview**: Add a query string such as `?rev=3`, regenerate preview HTML, or reopen the tab.
- **Editor chrome hiding details**: Resize viewport, zoom inside draw.io, or export a PNG if draw.io CLI is available.
- **Research-label drift**: Re-read the source paper or code when labels start becoming generic. Prefer exact names from the source material.
- **Preview iframe not loading**: Wait a few more seconds — the `embed.diagrams.net` iframe can take 3-5 seconds on slow connections. If it still fails, verify internet access.

## Bundled Helpers

- `scripts/make_drawio_preview.py`: build a local short-URL preview HTML that loads `.drawio` XML into diagrams.net via `postMessage`.
- `scripts/serve_drawio_preview.py`: generate the preview HTML and serve it on `127.0.0.1` with an optional browser launch.
- `scripts/validate_drawio.py`: parse and sanity-check `.drawio` files before handoff.
- `references/drawio-workflow.md`: full professional workflow for prompt/paper/code/reference-image to editable draw.io.
- `references/xml-authoring.md`: XML, layout, style, edge, text, icon, and iteration patterns.
