# Draw.io Diagram Workflow

## 1. Intake

Classify the request before drawing:

- **Prompt-to-diagram**: user describes content, style, and components.
- **Paper-to-diagram**: read a paper or section, extract method flow, losses, datasets, models, evaluation, and labels.
- **Codebase-to-diagram**: inspect repo structure, call graph, data flow, deployment, or architecture boundaries.
- **Reference-image replication**: reproduce a provided figure visually, usually with exact layout, style, typography, and arrows.
- **Iterative repair**: user points out screenshot defects; make localized corrections and re-verify.

For each request, capture:

- output path and desired format (`.drawio`, PNG export, SVG export, or all)
- whether the final diagram must be editable
- canvas size or aspect ratio
- typography, especially if the user names a font
- palette and stroke style
- exact icons/logos required
- caption policy
- preview/opening expectation

## 2. Content Extraction

For a paper or long prompt:

1. Identify the central claim or process.
2. Convert paragraphs into diagram entities: inputs, transformations, models, datasets, losses, rewards, outputs, serving path.
3. Decide the directional grammar: left-to-right pipeline, top/bottom stages, cyclic training loop, layered architecture, tree, swimlane, or feedback loop.
4. Preserve important terminology exactly. Simplify only explanatory filler.
5. Create a text inventory before drawing so labels are not invented mid-layout.

For a codebase:

1. Inspect files with repository-aware tools first.
2. Map components at the correct abstraction level: packages, services, modules, APIs, jobs, databases, queues, or UI screens.
3. Prefer actual names from code over generic labels.
4. Mark uncertain or inferred relationships separately if the diagram must be factual.

For reference-image replication:

1. Open the reference image and note dimensions.
2. Divide it into regions.
3. Inventory bounding boxes, text blocks, highlights, arrows, icons, and recurring elements.
4. Recreate the diagram with editable objects; do not trace by embedding the image as the final output.
5. Keep the reference image available for each screenshot comparison pass.

## 3. Layout Planning

Use a coordinate plan for high-fidelity diagrams:

- fixed canvas width and height
- outer margins
- major region boxes
- baseline y-coordinates for stage titles and content rows
- x-coordinates for pipeline columns
- repeated block dimensions
- arrow start/end points
- text line heights

For publication-style figures:

- Use full canvas bands rather than floating cards unless the reference uses cards.
- Keep text inside shapes; avoid overflow=visible for dense paragraphs unless the shape intentionally has no visible boundary.
- Use consistent line heights. Draw.io text rendering can differ from browser text, so verify with screenshots.

## 4. Authoring Approach

Prefer programmatic XML generation when:

- many objects must align precisely
- the diagram has repeated components
- user expects iterative exactness
- direct UI dragging would be slow or inconsistent

Use manual draw.io UI control when:

- the user asks to see local draw.io directly
- a small visual nudge is faster than editing XML
- an exact built-in shape is easier to pick in the UI

Use XML editing plus browser preview for the most repeatable path.

## 5. Preview Path That Avoids Long URLs

Do not pass large XML through a `#create=` URL or Windows `.url` shortcut. Use the bundled preview helpers. Resolve script paths relative to the skill directory; do not hard-code a user-specific home path.

One-command preview:

```powershell
python .\scripts\serve_drawio_preview.py D:\path\figure.drawio --port 8765
```

Or generate a preview file and serve the folder yourself:

```powershell
python .\scripts\make_drawio_preview.py `
  D:\path\figure.drawio `
  --out D:\path\drawio-preview.html

Set-Location D:\path
python -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/drawio-preview.html?rev=1
```

**Important**: The preview HTML embeds the XML inline as a JavaScript string. It does NOT read the `.drawio` file live. After editing the `.drawio` file, you MUST re-run `make_drawio_preview.py` (or `serve_drawio_preview.py`) to embed the updated XML into the HTML. Then refresh the browser to see changes.

The preview page uses an iframe to `https://embed.diagrams.net/` and sends the XML through `postMessage`, so the browser address stays short.

When the user edits the diagram in this preview, the blue Save button triggers a `.drawio` download. It does not overwrite the original local file automatically. Ask the user to place the downloaded file at the intended path, or continue from the downloaded path.

## 6. Screenshot Feedback Loop

This is the core mechanism. Without screenshots, the agent is guessing.

### How to take the screenshot

1. Start the preview server (see Section 5) — `serve_drawio_preview.py` or `python -m http.server`.
2. Navigate the browser to `http://127.0.0.1:8765/drawio-preview.html?rev=N` (increment N to bust cache).
3. **Wait 3-5 seconds** for the `embed.diagrams.net` iframe to fully render. If you snapshot too early, you'll see a blank or loading page.
4. Take a full-page or viewport screenshot. Use whatever browser tooling is available:
   - Playwright/Puppeteer MCP: `page.screenshot()`
   - Browser MCP: `browser_take_screenshot`
   - Any browser automation that can navigate to a URL and capture pixels
5. Save the screenshot and inspect it.

### Iteration loop

Each iteration should be narrow:

1. Refresh the local preview URL (with cache bust).
2. Screenshot.
3. Compare against the reference/spec.
4. Pick 3 to 5 visible issues.
5. Patch only those objects in the XML.
6. Regenerate the preview HTML (the server reads from the HTML file, not live XML — you MUST re-run `make_drawio_preview.py` after XML changes).
7. Go to step 1.

Useful issue categories:

- text overflow
- text too small/large
- line break mismatch
- box too narrow/wide
- dashed border mismatch
- arrow head type mismatch
- arrow route or bend mismatch
- loop arrow shape mismatch
- missing or wrong icon
- highlight bar not behind text
- color/stroke mismatch
- stage band alignment
- missing caption or unwanted caption

Avoid broad rewrites after a good base exists. Small visual regressions are easier to isolate when each pass changes only a few cells.

## 7. Handoff

Provide:

- final `.drawio` path
- latest screenshot path
- local preview URL if the server is still running
- validation summary
- remaining known visual gaps if any

If exact icons/logos were approximated, state that clearly and identify which assets should be supplied for the next fidelity pass.
