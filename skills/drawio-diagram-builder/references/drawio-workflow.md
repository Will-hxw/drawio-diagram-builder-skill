# Draw.io Diagram Workflow

## 1. Intake

Classify the request before drawing:

- **Prompt-to-diagram**: user describes content, style, and components.
- **Paper-to-diagram**: read a paper or section, extract method flow, losses, datasets, models, evaluation, and labels.
- **Codebase-to-diagram**: inspect repo structure, call graph, data flow, deployment, or architecture boundaries.
- **Reference-image replication**: reproduce a provided figure visually, usually with exact layout, style, typography, and arrows.
- **Mixed-input design**: combine text requirements, project context, one or more screenshots, and style references into one diagram.
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

For mixed-input tasks, first create a source inventory:

| source role | examples | how to use |
|-------------|----------|------------|
| content | prompt, paper text, repo files | determines labels, entities, claims |
| structure | method description, code relationships, architecture notes | determines hierarchy and connector semantics |
| style | example figures, screenshots, visual adjectives | determines font, palette, spacing, icon language |
| layout | reference composition, requested orientation | determines region placement and flow |
| asset | logos, icons, screenshots | determines exact reusable visual assets |

Do not collapse these roles. A screenshot can be a style reference without being a content reference. A paper section can define content without defining visual style.

For complex work, write `diagram-brief.md` using `self-supervision-and-intake.md` before authoring XML.

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
4. Identify connector semantics, not just connector geometry: source, target, direction, fan-in/fan-out, grouping, and feedback loops.
5. Recreate the diagram with editable objects; do not trace by embedding the image as the final output.
6. Keep the reference image available for each screenshot comparison pass.

For prompt-only or freeform diagrams:

1. Convert the request into a requirement traceability table.
2. Define entities and relationships before picking layout.
3. Choose a visual grammar: pipeline, layered system, swimlane, state machine, hierarchy, feedback loop, comparison, or dashboard-like overview.
4. Establish a style contract: font, palette, density, corner radius, stroke, icon family, and caption policy.
5. Mark uncertain content or speculative relationships so the final handoff can disclose them.
6. **If reference images are provided as style guides, run the full style extraction protocol.** Load `references/style-extraction.md`. Sample hex codes, measure font sizes, note corner radii and stroke widths. Write the extraction table BEFORE authoring XML. "Looking" at a reference without extracting concrete values is the #1 cause of diagrams that look nothing like the reference.

For top-conference computer-science figures:

1. Load `topconf-paper-style.md`.
2. If the user does not provide a style reference, use the bundled images in `../assets/reference-images/` as style/layout fallback only.
3. Preserve the user's scientific content. Do not invent modules, losses, datasets, metrics, or paper claims to fill a polished layout.
4. Choose the closest figure grammar: method overview, multi-stage training pipeline, model architecture, prompt/data construction workflow, evaluation/benchmark flow, or online serving path.

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

Use a semantic plan for connectors:

- source and target
- arrowhead placement
- relation type: data, control, feedback, update, query, selection, dependency, annotation, grouping
- cardinality: one-to-one, fan-in, fan-out, many-to-many, bidirectional
- forbidden crossing zones: titles, formulas, labels, icons, and dense paragraphs

For publication-style figures:

- Use full canvas bands rather than floating cards unless the reference uses cards.
- Keep text inside shapes; avoid overflow=visible for dense paragraphs unless the shape intentionally has no visible boundary.
- Use consistent line heights. Draw.io text rendering can differ from browser text, so verify with screenshots.
- Use top-conference conventions when requested: panel labels, dashed group boxes, token/matrix miniatures, compact legends, muted fills, and explicit equations near the relevant blocks.

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

## 4.5 Pre-Flight Quality Check (MANDATORY)

**Run before the first preview.** You are blind to visual quality from XML coordinates alone. A `<mxCell x="220" y="140" width="60" height="40" fontSize="8"/>` looks like data — but it renders as illegible micro-text in a cramped box. The pre-flight checker computes these defects from geometry:

```powershell
python <skill-dir>/scripts/validate_visual_quality.py <file>.drawio
```

Checks performed without rendering:
- arrow–box collision (arrow segments intersecting non-source/non-target boxes)
- text overflow risk (estimated text bounds vs container dimensions)
- font–container proportionality (cavernous boxes vs cramped text)
- element overlap (intersecting bounding rectangles)
- spacing variance (inconsistent gaps between adjacent elements)
- color palette coherence (too many distinct fill/stroke colors)
- orphan labels (empty significant-size boxes)
- font size anomalies (< 7pt illegible or > 48pt accidental)
- edge density hotspots (arrow spaghetti regions)

**Zero FAILs required.** Review every WARN. If the checker exits non-zero, fix the issues and re-run. Do not generate the preview HTML until pre-flight passes. Load `references/xml-preflight.md` for the full explanation.

A skipped pre-flight is the #1 cause of a garbage first screenshot. If your first screenshot looks terrible, you almost certainly skipped this step.

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

**HARD GATES — these are non-negotiable:**

1. **Style extraction before authoring** — if reference images provided, complete the extraction table in `references/style-extraction.md` before drawing anything.
2. **Pre-flight before first preview** — `validate_visual_quality.py` with zero FAILs.
3. **Minimum 3 cycles.** For any high-fidelity or user-critical diagram, complete at least 3 full screenshot→inventory→fix ALL P0/P1→regenerate→verify cycles.
4. **Graduated defect inventory (all 9 zones) per cycle.** Minimum defects vary by cycle: Cycle 1 ≥30, Cycle 2 ≥15, Cycle 3 ≥8 (or ≥5 if P0=0 and self-score≥40). A garbage first draft has 30+ visible problems. A clean third draft doesn't — do not fabricate false defects to hit quotas. See `references/self-supervision-and-intake.md` Section 4.1.
5. **Fix ALL P0/P1 defects per cycle.** If your inventory found 40 P0/P1 items, you fix all 40. Not "the most important ones." ALL of them.
6. **Fix verification after each fix pass.** Compare old vs new screenshot at each defect location. Mark FIXED/NOT FIXED/PARTIAL/REGRESSION.
7. **Red-team audit before handoff.** Re-scan all 9 zones as a hostile reviewer. Minimum findings: ≥15 (≥10 if self-score ≥45/50). After 3 fix cycles a clean diagram has <15 residual issues — a red-team that "finds" 30 is fabricating noise. Real auditing finds real problems, even if only 10.
8. **Self-score card before handoff.** Score 5 dimensions (1–10). BLOCKED if TOTAL <30 or any dimension ≤4. BORDERLINE if 30≤TOTAL<40 with no dim ≤4 — ship only with explicit user acceptance. ALLOWED if TOTAL ≥40 AND every dimension ≥6 (a dimension of 5 is borderline, not allowed — improve it).

Use one workdir state at a time. Do not run XML generation, preview generation, screenshot capture, and artifact validation concurrently against the same directory. The safe order is:

1. extract style from references (if provided) — fill the extraction table completely
2. run pre-flight (`validate_visual_quality.py`) — zero FAILs
3. write or patch `.drawio`
4. regenerate preview HTML
5. refresh browser and capture a canvas-only screenshot (diagram content ≥80% of image, ≥1280px wide)
6. create COMPLETE 9-zone defect inventory — graduated minimum per cycle (C1≥30, C2≥15, C3≥8)
7. fix ALL P0 and P1 defects
8. regenerate preview HTML and take new screenshot
9. verify each fix: mark FIXED/NOT FIXED/PARTIAL/REGRESSION by comparing old vs new screenshot at each defect location
10. append `defect-log.md` with the inventory, all fixes, and verification results
11. repeat from step 3 until ≥3 cycles, red-team done (≥15, or ≥10 if self-score ≥45), self-score ALLOWED
12. run validators

### How to take the screenshot

**CRITICAL: You MUST capture the draw.io canvas/page area ONLY, not the full browser window.** A full browser screenshot includes the diagrams.net sidebar, toolbar, and browser chrome — this shrinks the diagram so much that text becomes illegible, icons blur into dots, and spacing defects become invisible. Such a screenshot is WORTHLESS for quality inspection.

If the diagram content occupies less than 80% of the screenshot image, the screenshot is invalid. Retake it.

1. Start the preview server (see Section 5) — `serve_drawio_preview.py` or `python -m http.server`.
2. Navigate the browser to `http://127.0.0.1:8765/drawio-preview.html?rev=N` (increment N to bust cache).
3. **Wait 3-5 seconds** for the `embed.diagrams.net` iframe to fully render. If you snapshot too early, you'll see a blank or loading page.
4. **First, take a full-page screenshot** to locate the canvas/page rectangle — the white/light area where your diagram renders. Find its (x, y, width, height) in pixels.
5. **Then, take a canvas-only cropped screenshot:**
   - Playwright/Puppeteer: `await page.screenshot({ path: "canvas-N.png", clip: { x, y, width, height } })`
   - Browser MCP with evaluate: get canvas bounds, then screenshot with clip
   - If cropping is unavailable: resize viewport to 1920×1400+, zoom out (Ctrl+-) until the full canvas fills the viewport, and take a viewport-only screenshot
6. **Verify the screenshot is usable:** Open it. Can you read every text label? Can you see icon details? Can you visually measure spacing? If any answer is "no", the screenshot is invalid — go back to step 4.
7. Save the screenshot at a descriptive path (e.g., `diagram-pass-3.png`).

### Canvas-only or deliberate crop capture

Editor screenshots are useful for debugging, but they include diagrams.net chrome, sidebars, zoom state, and sometimes a clipped page. For final high-fidelity comparison, prefer one of these evidence types:

- a full-page screenshot where the complete draw.io page is visible and not clipped
- a deliberate crop that contains only the canvas/page and all visible diagram content
- a draw.io PNG/SVG export if a local export path is available and the output matches the editable XML

When using Playwright-style APIs, take a normal screenshot first, determine the canvas/page rectangle, then capture a clipped screenshot. Example shape:

```javascript
await page.screenshot({
  path: "canvas-pass-3.png",
  clip: { x: 280, y: 95, width: 1470, height: 805 }
});
```

The numbers must come from the current browser screenshot, not from memory. If the crop cuts off any page edge, retake it with a larger viewport, lower draw.io zoom, or wider clip. Keep the editor screenshot when it explains UI state, but use the canvas-only or full-page evidence for fidelity claims.

### Iteration loop

Each cycle is: **screenshot → inventory → fix ALL P0/P1 → verify → log**.

1. Refresh the local preview URL (with cache bust).
2. Screenshot.
3. **Create a COMPLETE defect inventory across all 9 zones BEFORE fixing anything.** Scan: text readability, arrow hygiene, box integrity, spacing consistency, color/palette, typography, layout/composition, icons, style coherence. Find EVERY visible problem. Organize by P0/P1/P2 severity. Do not stop at 5 defects — find them all.
4. Run all 5 dimensions of self-supervision to cross-check your inventory:
   - requirement audit
   - semantic audit
   - visual hygiene audit
   - style audit
   - regression audit
5. **Fix ALL P0 and P1 defects** (not just 3-5). If your inventory found 15 P0/P1 items, fix all 15.
6. Regenerate the preview HTML.
7. Take a new screenshot.
8. **Verify each fix:** compare old vs new screenshot at each defect location. Mark FIXED/NOT FIXED/PARTIAL/REGRESSION. A defect marked NOT FIXED means you must fix it again — the intention doesn't count.
9. Append the pass and verification to `defect-log.md`; after the first screenshot row exists, do not overwrite earlier review rows.
10. Go to step 1 (continue until ≥ 3 cycles, red-team done (≥15, or ≥10 if self-score ≥45), self-score ALLOWED (TOTAL ≥40 AND every dimension ≥6)).

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

Blocker categories that prevent handoff:

- style not extracted from reference images (if provided)
- pre-flight not passed (zero FAILs required)
- wrong connector direction, fan-in/fan-out, or feedback meaning
- missing required entity or relationship
- arrows crossing or hiding text, boxes, or icons
- text hidden by boxes, clipped by boundaries, or escaping its intended region
- obvious icon mismatch or missing icon for a required concept
- visual result conflicts with an explicit style constraint
- screenshot evidence is clipped or too partial to verify the full diagram
- fewer than 3 screenshot→inventory→fix→verify cycles completed
- complete defect inventory not created for the latest cycle (graduated minimum per cycle: C1≥30, C2≥15, C3≥8)
- any P0 or P1 defect marked NOT FIXED in the latest verification
- red-team audit not performed or found insufficient findings (default ≥15, or ≥10 if self-score ≥45/50)
- self-score below threshold (TOTAL < 40, or any dimension ≤ 4, or any dimension = 5 not yet improved)

Avoid broad rewrites after a good base exists. Small visual regressions are easier to isolate when each pass changes only a few cells.

## 7. Handoff

Provide:

- final `.drawio` path
- latest screenshot path
- local preview URL if the server is still running
- validation summary (`validate_drawio.py` + `validate_visual_quality.py`)
- self-score card with evidence for each deduction
- defect inventory summary (total P0/P1 fixed, remaining P2)
- fix verification log from the latest cycle
- remaining known visual gaps if any

If exact icons/logos were approximated, state that clearly and identify which assets should be supplied for the next fidelity pass.

Do not describe a diagram as complete if the latest screenshot still contains a visible P0/P1 blocker, if fix verification shows unresolved defects, or if any hard gate is unmet. Either iterate again or explicitly list the blocker as unresolved with a reason.
