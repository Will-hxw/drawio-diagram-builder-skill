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
| **Vision / image-reading tool** (required when user provides reference images as style guides) | Style extraction (see `references/style-extraction.md`) requires sampling pixel colors from reference images. You need one of: vision-capable model with image reading, a color-picker MCP/browser tool, or the ability to ask the user for hex codes. Without this, you CANNOT complete the style extraction table — do not fabricate hex codes. Fallback: ask the user for the palette. |
| **Internet access** | Preview loads `https://embed.diagrams.net/` in an iframe. Offline won't work. |
| **File write access** | You will create `.drawio` files. |

Script paths in this document are relative to the skill directory. Resolve them like `<skill-dir>/scripts/serve_drawio_preview.py`. If you can't find the skill directory, look under the agent's installed skills path (e.g., `~/.claude/skills/drawio-diagram-builder/` or `~/.codex/skills/drawio-diagram-builder/`).

If Playwright reports a missing bundled browser, first try an installed browser channel before giving up, for example `npx playwright screenshot --channel chrome ...` or `--channel msedge ...`.

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

Load `references/drawio-workflow.md` for the detailed end-to-end process. Load `references/self-supervision-and-intake.md` for any non-trivial diagram, mixed prompt-plus-image input, project-context diagram, or iterative visual repair. Load `references/style-extraction.md` when the user provides reference images as style guides — mandatory before authoring XML; you must extract palette, typography, spacing, and arrow grammar before drawing. Load `references/topconf-paper-style.md` when the user asks for a computer-science paper, top-conference, camera-ready, method, ML pipeline, multimodal architecture, benchmark, or polished research figure, especially when the user gives weak or missing style references. Load `references/xml-authoring.md` when writing or repairing XML shapes, styles, edges, and text layout. Load `references/xml-preflight.md` before rendering any diagram — it documents static XML quality checks that catch computable defects (arrow-box collisions, text overflow, spacing variance, color chaos) without a screenshot. Load `references/primitive-icons.md` when a reference figure contains small modality, memory, warning, tool, clock, document, or other paper-style icons that should remain editable. Load `assets/icons/ICON-MANIFEST.md` when generic SVG icon assets would improve fidelity.

For any reference-image replication request, load `references/reference-replication-protocol.md` before creating XML. This is mandatory. Treat high-fidelity replication as an evidence pipeline: observe the reference, specify geometry, author XML, render, compare, patch, and repeat. Do not start drawing from a reference image until the protocol's required intermediate artifacts exist.

Resolve all references relative to the skill directory.

## Standard Workflow

1. **Verify prerequisites** — confirm Python 3 and browser automation are available. If not, stop and tell the user what's missing.

2. **Collect input context**
   - Read the user's prompt, reference images, paper sections, codebase files, or domain notes.
   - Identify the task type: research figure creation, paper-method diagramming, visual replication, architecture diagramming, repository diagramming, or iterative polish.
   - Classify every input by role: content source, structure source, style source, layout source, or asset source. A style reference does not automatically define content or connector semantics.
   - For top-conference paper figures with weak or missing style input, use `references/topconf-paper-style.md` and the bundled images under `assets/reference-images/` as style/layout fallback only. Do not invent scientific content to fill the layout.
   - If exact assets are needed, locate them locally or ask for them. Do not silently replace a required logo/icon with an unrelated one.
   - **If reference images were provided as style guides, extract their visual language BEFORE drawing.** "Looking" at a reference is not extraction. Load and follow `references/style-extraction.md`. Fill every row of the extraction table — palette hex codes, font sizes, corner radii, stroke widths, spacing rhythms. The extracted values become your mandatory style contract. Do not skip this. When your diagram looks nothing like the reference, the root cause is almost always: no style extraction was done.

3. **Build the diagram brief and visual specification**
   - For mixed inputs, prompt-only diagrams, paper/code diagrams, or any complex task, create a brief with: user goal, source inventory, requirement traceability, semantic model, style contract, and open assumptions. Use `references/self-supervision-and-intake.md`.
   - Record canvas size, major regions, hierarchy, labels, colors, line styles, fonts, arrows, icons, captions, and spacing.
   - Define the meaning of every connector before drawing it: source, target, direction, fan-in/fan-out, feedback, grouping, and arrowhead placement. Do not draw arrows whose semantics you cannot explain.
   - For reference-image replication, create a coordinate-level inventory: bounding boxes, text lines, highlight bars, connectors, loops, and repeated blocks.
   - For paper figures, preserve exact method terminology and distinguish data construction, training, evaluation, inference, and serving flows.
   - Decide what must be exact and what can be approximated.
   - For reference-image replication, write the required protocol artifacts before XML:
     - `visual-spec.md`
     - `layout-grid.md`
     - `asset-ledger.md`
     - `defect-log.md`

4. **Author the `.drawio` file**
   - The `.drawio` file is the primary artifact. Preview HTML is only a derived artifact.
   - Use one `mxfile` with one or more `diagram` pages.
   - Use explicit `mxGeometry` positions and sizes for high-fidelity work.
   - Split dense text into multiple cells when line-level alignment matters.
   - Build important icons and arrows with editable draw.io primitives when possible. Use `references/primitive-icons.md` for common research-figure icon recipes before inventing one-off symbols. Use bundled SVG icons from `assets/icons/` when fidelity matters more than primitive editability, and record them in `asset-ledger.md`.
   - Keep colors, strokes, fonts, and rounded corners consistent with the reference or requested style.
   - **Before rendering, run the pre-flight checker.** You cannot perceive visual quality from XML alone — arrow-box collisions, text overflow, font-box mismatches, spacing chaos, palette scatter, and **meaningless decorative color blocks copied from references** are all invisible to you but computable from geometry:
     ```powershell
     python <skill-dir>/scripts/validate_visual_quality.py <file>.drawio
     ```
     **Zero FAILs required before the first preview HTML is generated.** Review every WARN. If the checker exits non-zero, fix and re-run. Do not skip this step. Load `references/xml-preflight.md` for the full explanation of each rule.

5. **Preview without long URLs**
   - **Preferred**: run `scripts/serve_drawio_preview.py <file>.drawio --port 8765`. It generates the preview HTML, starts a server, and opens the browser.
   - **Manual**: run `scripts/make_drawio_preview.py <file>.drawio --out drawio-preview.html`, then `python -m http.server 8765 --bind 127.0.0.1` in the output directory.
   - Open `http://127.0.0.1:8765/drawio-preview.html?rev=1` in the browser.
   - Wait 2-5 seconds for the diagrams.net embed iframe to initialize.
   - Take a screenshot of the rendered diagram.

6. **Iterate from evidence**
   - **HARD GATE: Minimum 3 screenshot→inventory→fix→verify cycles for any high-fidelity or user-critical diagram.** A first draft is never acceptable. The only exception is if the user explicitly says "stop here." Record every cycle in the defect log.
   - Each cycle follows: screenshot → complete defect inventory (all 9 zones) → fix ALL P0/P1 → regenerate → verify each fix.
   - Compare the screenshot against the reference or requested spec.
   - **The screenshot MUST be a canvas-only crop, NOT the full browser window.** A full browser screenshot includes the diagrams.net sidebar, toolbar, and chrome — this shrinks the diagram so much that you cannot read text, see icon details, or spot spacing defects. The screenshot is USELESS for quality inspection if the diagram occupies less than 80% of the image.
   - **How to crop:** After taking a full-page screenshot, locate the draw.io canvas/page rectangle (the white area where your diagram renders). Crop to that rectangle. With Playwright: `await page.screenshot({ clip: { x, y, width, height } })`. The crop coordinates must come from the CURRENT screenshot, not from memory or XML — inspect the screenshot, find the canvas edges, then crop.
   - **If you cannot crop, zoom the viewport:** Navigate the browser to a larger viewport (e.g., 1920×1400 or higher) and zoom out (Ctrl+-) until the full canvas is visible, then screenshot. A zoomed-out full-canvas view is better than a clipped browser chrome view.
   - **Invalid screenshot → do not proceed to audit.** If the screenshot shows more browser UI than diagram, retake it. A blurry full-browser shot where you cannot read text is not evidence — it is a waste of an iteration cycle.
   - **MANDATORY: Create a COMPLETE defect inventory scanning all 9 zones (text, arrows, boxes, spacing, color, typography, layout, icons, style coherence) BEFORE fixing anything.** Graduated minimum per cycle: Cycle 1 ≥30, Cycle 2 ≥15, Cycle 3 ≥8 (or ≥5 if P0=0 and self-score≥40). Do NOT fabricate false defects to hit quotas on a clean diagram. Load `references/self-supervision-and-intake.md` Section 4.1 for the zone-by-zone scanning guide.
   - **MANDATORY: Fix ALL P0 and P1 defects (not just the most important ones), then verify each fix against the new screenshot.** If your inventory found 40 P0/P1 items, fix all 40. Mark each as FIXED/NOT FIXED/PARTIAL/REGRESSION. A defect marked NOT FIXED means you failed — fix it again.
   - Run all 5 dimensions of the self-supervision audit to cross-check your inventory: requirement audit, semantic audit, visual hygiene audit, style audit, and regression audit.
   - Regenerate the preview HTML, refresh the browser (add a cache-busting `?rev=N`), screenshot again, and repeat.
   - Name the specific defects being fixed rather than claiming broad perfection.
   - For reference-image replication, append every screenshot pass to `defect-log.md` with: observed defect, reference evidence, XML cells to change, patch summary, and remaining risk. After the first screenshot row exists, treat `defect-log.md` as append-only.
   - **Before claiming improvement, run a red-team role switch on the latest screenshot.** You are no longer the author. You are a hostile reviewer. Re-scan all 9 zones with fresh eyes. Minimum findings: ≥15 (≥10 if self-score ≥45/50). After 3 fix cycles, a clean diagram has <15 residual issues — real auditing finds real problems, even if only 10 of them.
   - If the user points out an obvious screenshot defect, treat it as a self-supervision failure: re-open the source/reference, correct the interpretation, patch the diagram, screenshot a focused crop plus the full canvas, and record the lesson in the defect log. Then re-run the red-team audit — a user-found defect proves you missed others.
   - If the first screenshot is structurally wrong, go back to `visual-spec.md` and `layout-grid.md` before making XML patches. A structural miss means an observation, coordinate, asset, or draw.io-rendering assumption was wrong.

7. **Validate before handoff**
   - **HARD GATE: Self-score card (mandatory).** Before handing off, score your own diagram on a 1-10 scale:
     | Dimension | Score (1-10) |
     |-----------|-------------|
     | Text readability | /10 |
     | Arrow accuracy | /10 |
     | Color coherence | /10 |
     | Layout consistency | /10 |
     | Style match to reference/spec | /10 |
     | **TOTAL** | **/50** |
     - **TOTAL < 30 or any dimension ≤ 4 → BLOCKED.** Continue iterating. Do not ask — just fix it.
     - **TOTAL 30–39 (and no dimension ≤ 4) → BORDERLINE.** List 5+ specific things you'd fix next. Ship only if user explicitly asked for a quick result.
     - **TOTAL ≥ 40 and every dimension ≥ 6 → ALLOWED.** A dimension scored 5 is borderline, not allowed — review and improve it.
     - Each point deducted must cite concrete, screenshot-visible evidence.
   - **HARD GATE: Red-team audit completed and logged.** The red-team pass must find at least 15 findings (≥10 if self-score ≥45/50). If it found fewer, you did not try hard enough or the diagram is ready for handoff — check the self-score card to determine which.
   - **HARD GATE: At least 3 screenshot→inventory→fix→verify cycles documented in defect log** (each cycle = screenshot → 9-zone inventory → fix ALL P0/P1 → regenerate → verify).
   - Run `scripts/validate_drawio.py <file>.drawio`.
   - Use `scripts/validate_drawio.py --strict --json <file>.drawio` when a CI-friendly final gate is useful, or when warnings such as off-page vertices or placeholder-like labels should block handoff.
   - For reference-image replication, also run `scripts/validate_replication_artifacts.py <workdir> --require-screenshot-review` after the latest screenshot pass. Run validation after generation/preview writes finish; do not run validators in parallel with scripts that write the same artifact directory.
   - Confirm: XML parses, page count is expected, ids and references are valid, required geometry exists, no unwanted embedded raster or external images are present, captions included/removed as requested, latest screenshot reviewed.
   - Provide the `.drawio` path, the latest screenshot path, the self-score card, and the defect log summary. Leave the local preview server running if the user wants to continue iterating.

## Editing Rules

- Edit `.drawio` files by writing or patching XML directly. For small targeted fixes, use the file editing tool (e.g., Edit/Write in Claude Code).
- Preserve user files and unrelated generated files.
- Keep a working copy and a handoff copy only when useful; keep them synchronized.
- Never claim the diagram is complete without visual verification (a screenshot).
- Never claim the diagram is complete if the latest screenshot still has a visible P0/P1 blocker: wrong connector semantics, hidden text, clipped text, missing required content, accidental overlap, or a direct violation of the user's prompt/style reference.
- Never claim the diagram is complete if any hard gate is unmet: style not extracted from references, fewer than 3 screenshot cycles, no complete defect inventory across 9 zones (graduated minimum: C1≥30, C2≥15, C3≥8), no fix verification, no red-team audit (≥15 findings, or ≥10 if self-score ≥45/50), self-score below 40, or self-score has any dimension ≤ 4 (≤5 is borderline and must be improved before handoff).
- When the user asks for "100% reproduction", treat that as an iterative standard: keep finding and fixing visible differences until the user accepts or identifies next issues.
- For reference-image replication, never skip the intermediate artifacts. A low-quality first draw usually means the observation inventory, coordinate plan, asset ledger, or rendering assumptions were underspecified.

## Common Failure Handling

- **Windows long URL failure**: Do not open large diagrams through `.url` files or huge `#create=` URLs. Use local preview HTML with postMessage.
- **Skipping pre-flight**: The most common cause of a garbage first screenshot. If you did not run `validate_visual_quality.py` before rendering, you deserve the disaster you see. Run it now, fix the FAILs, regenerate.
- **First screenshot is terrible**: This means the pre-flight was skipped or its warnings were ignored. Go back to step 4, run `validate_visual_quality.py`, fix every FAIL, review every WARN, then re-render.
- **Full browser screenshot (with sidebar/toolbar)**: The diagram is too small to read. CROP TO THE CANVAS. Locate the white draw.io page area in the screenshot, crop to its (x, y, w, h). If you cannot crop, resize viewport to 1920×1400, zoom out (Ctrl+-), and retake. A screenshot where the diagram is < 80% of the image is invalid for quality inspection.
- **"I only found 8 defects"**: You are not scanning all 9 zones systematically. Minimum 30. Start over from zone 1, pixel by pixel. Every cell, every edge, every gap.
- **Saving from preview**: The local preview cannot silently overwrite local files (browser sandbox). The blue Save button triggers a `.drawio` download. Move the downloaded file back to your working path before further edits.
- **Text overlap or overflow**: Split paragraphs into smaller text cells, reduce font size, increase container width, set stable geometry, and screenshot-check.
- **Misaligned highlight bars**: Put highlight rectangles behind individual text lines, not behind the whole paragraph.
- **Ugly loop arrows**: Use editable curved connectors or arcs, not large Unicode arrow glyphs, unless the reference explicitly uses glyphs.
- **Wrong icon fidelity**: Build editable approximations from primitives, or ask for/download the exact icon when exactness matters.
- **Missing generic icons**: Check `assets/icons/ICON-MANIFEST.md` before searching the web. Use the bundled MIT-licensed Tabler SVGs for generic document, media, storage, routing, tool, metric, and status icons.
- **Rich text or formulas render literally**: Use the safe helper pattern in `references/xml-authoring.md`; escape normal text and use deliberate raw HTML only for agent-authored tags such as `<i>` or `<sub>`.
- **Stale preview**: Add a query string such as `?rev=3`, regenerate preview HTML, or reopen the tab.
- **Editor chrome hiding details**: Resize viewport, zoom inside draw.io, or export a PNG if draw.io CLI is available.
- **Partial screenshot false positives**: If the screenshot clips any page edge, retake it with a larger viewport, a lower draw.io zoom, or a canvas-only crop before judging fidelity.
- **Research-label drift**: Re-read the source paper or code when labels start becoming generic. Prefer exact names from the source material.
- **Preview iframe not loading**: Wait a few more seconds — the `embed.diagrams.net` iframe can take 3-5 seconds on slow connections. If it still fails, verify internet access.

## Bundled Helpers

- `VERSION`: installed skill version marker. Use it through `scripts/check_skill_update.py`, not by checking for a specific feature string.
- `scripts/check_skill_update.py`: compare the installed skill version with the canonical GitHub version.
- `scripts/make_drawio_preview.py`: build a local short-URL preview HTML that loads `.drawio` XML into diagrams.net via `postMessage`.
- `scripts/serve_drawio_preview.py`: generate the preview HTML and serve it on `127.0.0.1` with an optional browser launch.
- `scripts/validate_drawio.py`: parse, structurally validate, count labels/assets, and sanity-check `.drawio` files before handoff. Supports `--strict` and `--json`.
- `scripts/validate_visual_quality.py`: **pre-render static checker.** Parses `.drawio` XML and computes visual defects without rendering — arrow-box collisions, text overflow risk, font proportionality, spacing variance, color incoherence, element overlap, orphan labels, font size anomalies, and edge density. Run before first preview. Zero FAILs required. Supports `--json`, `--strict`, `--rules`.
- `assets/icons/ICON-MANIFEST.md`: local MIT-licensed SVG icon inventory and usage rules.
- `assets/reference-images/REFERENCE-IMAGES.md`: bundled top-conference-style figure references for style fallback.
- `references/drawio-workflow.md`: full professional workflow for prompt/paper/code/reference-image to editable draw.io.
- `references/self-supervision-and-intake.md`: mixed-input intake, diagram brief, mandatory 5-dimension audit, red-team role switch, self-scoring card, and hard gates before handoff.
- `references/xml-preflight.md`: explains every pre-render static check — what it catches, why it matters, and why XML alone blinds the agent to these defects.
- `references/style-extraction.md`: mandatory style extraction protocol — how to sample palettes, measure typography, identify layout rhythm, and extract arrow grammar from reference images before drawing. Use whenever the user provides style reference images.
- `references/topconf-paper-style.md`: top-conference computer-science figure style, fallback reference selection, and paper-quality bar.
- `references/primitive-icons.md`: reusable editable primitive recipes for common research-figure icons.
- `references/reference-replication-protocol.md`: low-freedom protocol for high-fidelity reference-image replication.
- `references/xml-authoring.md`: XML, layout, style, edge, text, icon, and iteration patterns.
