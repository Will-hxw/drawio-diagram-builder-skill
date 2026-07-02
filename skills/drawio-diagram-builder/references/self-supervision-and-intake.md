# Diagram Intake And Self-Supervision Protocol

Use this protocol for any non-trivial diagram, not only exact reference-image replication. It is mandatory when the user provides mixed inputs such as prompts, project context, papers, screenshots, multiple style references, or iterative visual feedback.

The core failure to prevent is false completion: the agent renders a diagram, notices only the local change it intended to make, and misses obvious violations of the user's requirement, connector semantics, visual grammar, or basic layout hygiene.

## 1. Build A Diagram Brief

Before drawing, synthesize the user's inputs into a short working brief. If the task is complex, save it as `diagram-brief.md` next to the `.drawio` file.

Required sections:

```markdown
# Diagram Brief

## User Goal
- Output:
- Audience:
- Must communicate:
- Must not do:

## Source Inventory
| id | source | type | role | priority | notes |

## Requirement Traceability
| id | requirement | source evidence | must/should/may | planned visual encoding |

## Semantic Model
| id | entity or relationship | direction / hierarchy / cardinality | visual encoding | uncertainty |

## Style Contract
| id | font | palette | stroke | icon style | layout density | reference source |

## Open Assumptions
| assumption | risk | how to verify |
```

Source roles are different and must not be mixed:

- **content source**: what the diagram must say.
- **structure source**: how components relate.
- **style source**: colors, typography, icon language, spacing.
- **layout source**: approximate placement, density, or composition.
- **asset source**: exact icons, logos, images, or symbols.

When multiple images are provided, classify each image by role. Do not copy layout from a style-only image unless the user asked for that. If sources conflict, write the decision in the brief before drawing.

## 2. Preserve Semantics Before Styling

Every arrow, loop, bracket, and group must have a meaning before it is drawn.

For each connector, answer:

- What is the source?
- What is the target?
- Is the relation data flow, control flow, feedback, update, selection, dependency, or annotation?
- Is it one-to-one, fan-in, fan-out, bidirectional, loop, or grouping?
- Where should the arrowhead be?
- Can the route cross labels or boxes without changing meaning?

If you cannot answer these questions from the prompt, paper, code, or reference image, mark the connector as uncertain in the brief or ask the user when the risk is high.

Do not infer connector direction from convenience. In a screenshot review, a semantically wrong arrow is a blocker even if it is visually neat.

## 3. Style Extraction (MANDATORY when reference images provided as style guides)

**If the user provided reference images for style (not for exact replication), you must extract the visual language before drawing.** "Looking" is not extraction. You glanced at the images and moved on — that is why your diagram looks nothing like the reference.

Load and follow `references/style-extraction.md` before authoring a single `<mxCell>`. Fill every row of the style extraction table. The extracted values become your **style contract** — you are not allowed to deviate without a documented reason.

Common failure: user provides 4 beautiful conference-paper figures as style reference. Agent says "understood," then draws a diagram with random colors, no rhythm, and amateur spacing. Agent does not realize it looks completely different because it never wrote down what the reference actually looks like.

The style extraction table forces you to answer: what palette? what font sizes? what corner radius? what spacing rhythm? what arrow grammar? If you cannot answer these from the reference, you did not extract — you glanced.

### 3.1 Pre-Flight: Static XML Quality Check (MANDATORY)

**After writing the `.drawio` XML and BEFORE generating the first preview HTML**, run the pre-flight checker:

```powershell
python <skill-dir>/scripts/validate_visual_quality.py <file>.drawio --json --output preflight-report.json
```

Load `references/xml-preflight.md` to understand every check. Read the output. Every FAIL item must be fixed before you are allowed to render. Every WARN item must be reviewed and either fixed or documented with a reason.

The pre-flight catches computable geometry defects that you cannot perceive from XML alone:
- arrows passing through boxes
- text that will overflow its container
- font sizes wildly mismatched to box sizes
- overlapping shapes
- wildly inconsistent spacing
- color palette chaos

Do **not** generate the first preview if `validate_visual_quality.py` exits with a non-zero code. A first screenshot that is structurally broken is a waste of an entire iteration cycle. The pre-flight is your eyes before you have a screenshot.

After fixing FAILs and reviewing WARNs, re-run the checker to confirm zero FAILs, then proceed to preview.

## 4. Self-Supervision Loop

After each rendered screenshot, inspect the result as if reviewing someone else's diagram. The review target is the whole current output, not only the last edited region.

### 4.1 Complete Defect Inventory (MANDATORY — REPLACES "find 5 defects")

**Before you can inspect, the screenshot must be valid.** A full browser window screenshot (with diagrams.net sidebar, toolbar, browser chrome) is INVALID. The diagram content must fill at least 80% of the screenshot image. If you cannot read every text label at a glance, the screenshot is too small — retake as a canvas-only crop.

**After each valid screenshot, BEFORE you fix anything, create a COMPLETE defect inventory.** Do not start fixing after finding 5 or 10 problems. Find ALL of them. Systematically scan every region of the diagram.

**Scanning order — cover every pixel:**

| Scan zone | What to look for | Check |
|-----------|-----------------|-------|
| Zone 1: Text readability | Text too small? Blurry? Clipped by container? Hidden behind a shape/arrow? Overflowing container edge? | Every text cell |
| Zone 2: Arrow hygiene | Arrow passing through a box? Through text? Through an icon? Overlapping another arrow? Wrong direction? Missing arrowhead? Arrowhead at wrong end? | Every edge |
| Zone 3: Box integrity | Box overlapping another box? Box overlapping an icon? Box too big for its content (cavernous)? Box too small (text cramped)? | Every shape |
| Zone 4: Spacing consistency | Adjacent gaps unequal? Margins inconsistent? Padding inside boxes uneven? Elements misaligned (same-row y differs, same-col x differs)? | Every pair of adjacent elements |
| Zone 5: Color & palette | Wrong color (doesn't match extracted style contract)? Too many colors? Clashing adjacent colors? Fill missing where reference has fill? | Every vertex |
| Zone 6: Typography | Font mismatch (doesn't match extracted style)? Font size mismatch? Weight mismatch? Inconsistent font within same element type? | Every text cell |
| Zone 7: Layout & composition | Region placement wrong? Flow direction wrong? Density too sparse/dense vs reference? Missing panel labels? Missing legend? Missing caption? | Overall canvas |
| Zone 8: Icons | Icon missing where reference has one? Wrong icon? Icon too large/small? Icon color wrong? Icon overlapping text/border? Two icons overlapping? | Every icon cell |
| Zone 9: Style coherence | Does the whole diagram feel like the reference family? Or does it feel like a different genre? Honest answer. | Overall impression |

**For each zone, list EVERY defect found.** A defect is specific: element id, what is wrong, evidence (screenshot observation or reference comparison), severity (P0/P1/P2). Example:

```
Z3-BOX-03 | `decoder_box` | Box is 320×180px but contains only 2 words at 10pt — looks hollow and amateur | screenshot pass-3, zone-3 | P1
Z2-ARR-07 | `edge_feedback` | Arrow from `loss` to `encoder` passes through the `attention` box at pixel (450, 380) | screenshot pass-3, zone-2 | P0
```

**Minimum per zone:**
- P0 (blocker) — find every single one. An arrow passing through a box is P0. If you miss even one, you failed the audit.
- P1 (visible defect) — find at least 2 per zone. Text a little too small? Spacing uneven? Color doesn't match style contract? These are P1.
- P2 (polish) — find at least 2 per zone. Slightly off-center alignment? Box 2px wider than siblings? Find them.

**Total minimum: graduated by cycle — the floor drops as quality improves:**

| Cycle | Minimum defects | Rationale |
|-------|----------------|-----------|
| Cycle 1 (first draft) | **≥30** | A garbage first draft ALWAYS has 30+ visible problems. Find them all. |
| Cycle 2 | **≥15** | After fixing 30+ defects from cycle 1, 10-15 real defects remain. Do not invent fake ones to hit 30. |
| Cycle 3 | **≥8**, or **≥5 if P0=0 and self-score≥40** | A stable diagram has few real defects. If you cannot find 8, the diagram may be done — switch to verification-mode red-team. |
| Red-team (always after cycle 3+) | **≥15** | The red-team is looking for RESIDUAL problems on a diagram that already survived 3 fix cycles. 15 real findings (not 30 fake ones) proves hostile auditing. If the self-score card shows ≥45/50, red-team minimum is **≥10** (verification audit, not full adversarial pass). |

**The graduated minimum prevents a known failure mode:** after cycle 2, a clean diagram has only 5-10 real defects left. Forcing 30 forces the agent to fabricate trivial fake defects ("box A is 1px wider than box B") which pollutes the defect log and wastes time. Real improvements stop; compliance theater begins. The graduated minimum keeps the audit honest.

Organize the defect inventory as:

```markdown
## Defect Inventory — Cycle N

### P0 — Blockers (must fix this cycle)
| id | zone | element | description | evidence |
|----|------|---------|-------------|----------|

### P1 — Visible Defects (fix this cycle)
| id | zone | element | description | evidence |
|----|------|---------|-------------|----------|

### P2 — Polish (fix if time, document if deferred)
| id | zone | element | description | evidence |
|----|------|---------|-------------|----------|
```

### 4.2 P0/P1/P2 Grading (AUTO-GRADED from pre-flight, not self-assigned)

**Defect severity is NOT self-assigned.** The agent cannot downgrade a real P0 to P2 by writing "minor." Severity is derived from the pre-flight checker output + the screenshot audit:

| Source | Grading |
|--------|---------|
| Pre-flight FAIL | **P0** — must fix this cycle, cannot be downgraded |
| Pre-flight WARN | **P1** — must fix unless explicitly justified as acceptable |
| Screenshot-only finding | Agent assigns P0/P1/P2 with concrete evidence; pre-flight output (if re-run) constrains the grade — an element flagged as FAIL by the checker is always P0 |

**Document this in the defect inventory:**
```markdown
| defect id | zone | element | description | source | severity |
|-----------|------|---------|-------------|--------|----------|
| Z2-ARR-07 | Arrow hygiene | edge_e1 | Arrow passes through text box `title_label` | pre-flight FAIL: arrow-box-collision | P0 |
| Z3-BOX-12 | Box integrity | box_enc | Box 200×100 with 8pt text, ratio 12.5 | screenshot zone-3 | P1 |
```

**Rule: if `validate_visual_quality.py` flagged the element as FAIL, it is P0. If it flagged as WARN, it is P1. The agent CANNOT downgrade pre-flight severity.** Screenshot-only findings are agent-graded but must be honestly assessed — an arrow passing through a box found only on screenshot is still P0.

### 4.3 Fix All Defects In Priority Order

After the inventory is complete, fix defects in order: P0 → P1 → P2. Do not fix P1s before P0s. Do not skip a P0 because it's "hard" — that's what makes it a P0.

Fix ALL P0 and P1 defects in the current cycle. Yes, ALL of them. Not just 3-5. If your inventory found 12 P0/P1 defects, you fix all 12 this cycle. If you fixed them correctly, the next screenshot will show improvement across the entire diagram, not just 3 spots.

**Defer P2 defects only with an explicit reason.** "Ran out of time" is not a reason when the user hasn't set a time limit.

### 4.4 Fix Verification (MANDATORY after each fix pass)

After fixing defects and regenerating the preview:
1. Take the new screenshot.
2. For EACH defect in your inventory that you claimed to fix, compare the old screenshot to the new screenshot at that exact location.
3. Mark each defect as: ✅ FIXED (visible in new screenshot) | ❌ NOT FIXED (still present) | ⚠️ PARTIAL (improved but not resolved) | 🔄 REGRESSION (fix introduced new problem)

**If any P0 or P1 is marked ❌ NOT FIXED, you did not fix it.** Re-open the XML, find the actual cause, and fix it again. Do not claim it's fixed because you intended it to be fixed. The screenshot is the only truth.

```markdown
## Fix Verification — Cycle N

| defect id | claimed fix | old screenshot | new screenshot | status |
|-----------|-------------|---------------|---------------|--------|
| Z2-ARR-07 | Moved arrow waypoints up 40px to bypass `attention` box | pass-3 zone-2 crop | pass-4 zone-2 crop | ✅ FIXED |
| Z3-BOX-03 | Reduced box height from 180→80px, increased font to 14pt | pass-3 zone-3 crop | pass-4 zone-3 crop | ⚠️ PARTIAL — text now fits but box is still 20px wider than needed |
```

### 4.4 Minimum Iteration Requirement (MANDATORY)

**For any high-fidelity or user-critical diagram, you MUST complete at least 3 full cycles** (screenshot → inventory → fix P0/P1 → regenerate → verify). A first draft is never good enough. The only exception is if the user explicitly says "stop here and give me what you have."

Record each cycle in the defect log.

### 4.5 The 5-Dimension Audit (Confirm Your Inventory Is Complete)

After creating your defect inventory, cross-check it against the 5 dimensions to ensure you didn't miss a category:

1. **Requirement audit** — compare the screenshot against the user's prompt, brief, and source context. Every entity from the spec must be present. Every connector from the spec must exist in the correct direction.
2. **Semantic audit** — inspect arrows, loops, brackets, grouping, fan-in/fan-out. For each arrow: source→target correct? Arrowhead placement correct? Meaning matches spec?
3. **Visual hygiene audit** — check text readability, text overflow, clipped text, line crossings, z-order, overlap, unreadable icons, and component alignment. **Every pixel of text must be readable. No arrow may pass through a box. No two boxes may overlap unintentionally.**
4. **Style audit** — compare typography, stroke, colors, corner radius, shadows, icon language, and density against the extracted style contract (Section 3). If you extracted `fontSize=11` and your diagram uses `fontSize=14`, that's a defect.
5. **Regression audit** — check that the latest fix did not break an earlier acceptable region. A fix that introduces a new problem is not a fix.

### 4.6 Iteration Discipline

Each cycle: inventory ALL defects → fix ALL P0/P1 → regenerate → verify each fix → log everything.

Do not fix a few things and claim the rest are fine. If you skipped a defect, explain why. A defect still visible in the screenshot is still a defect — your intention to fix it does not make it fixed.

## 5. Red-Team Role Switch (MANDATORY BEFORE HANDOFF)

Before you are allowed to hand off the diagram, you must switch roles. You are no longer the author. You are now a hostile reviewer whose goal is to find every remaining problem.

Read the following prompt aloud (in your thinking) and answer honestly:

> "I am a senior designer reviewing this diagram for submission to a top conference. I do not care how long you spent on it. I will list every visible flaw, no matter how small. I will be harsh, systematic, and thorough."

**The red-team audit must re-scan ALL NINE zones from Section 4.1 with fresh eyes, on a CANVAS-ONLY screenshot (≥ 80% diagram content).** The fact that you "already fixed" the spacing zone in cycle 2 does not mean it's clean now. Regression happens. If your screenshot shows browser chrome, you cannot audit properly — retake it.

For each zone, explicitly answer: "Did I find problems here that the author missed?"

| Zone | What to inspect ruthlessly | Minimum new findings |
|------|---------------------------|---------------------|
| 1. Text readability | Squint at every text element. Is it readable? Is any character clipped? Any text ghosting behind an arrow? Any text so small you'd need to zoom to read it? | 4+ |
| 2. Arrow hygiene | Trace every arrow from source to target. Does it cross any box? Cross any text? Cross any icon? Cross another arrow? Is the arrowhead visible? Is the route the shortest clean path? Are there meaningless arrows? | 4+ |
| 3. Box integrity | Check every box's size vs content. Any hollow giants? Any sardine cans? Any boxes with uneven internal padding? Any boxes overlapping? | 3+ |
| 4. Spacing consistency | Measure gaps. Are same-type gaps identical? Are margins equal on all four sides? Is the grid rhythm visible or chaotic? Are any elements nearly touching? | 4+ |
| 5. Color & palette | Compare against the extracted style contract (Section 3). Every hex code. Every font size. Every stroke width. Any color that doesn't belong in the palette? Pure color blocks that mean nothing? | 3+ |
| 6. Typography | Check font family, size, weight, alignment on every text cell. Does it match the style contract row by row? Is there a clear hierarchy (heading > subheading > body > caption)? | 3+ |
| 7. Layout & composition | Step back. Does the overall composition feel like the reference family? Are regions in the right places? Is the flow direction consistent? Does the density match? | 4+ |
| 8. Icons | Check every icon for size, color, alignment, and semantic correctness. Any two icons overlapping? Any icon the wrong size relative to its neighbors? Any icon that looks like cheap clipart? | 3+ |
| 9. Style coherence | Be brutally honest. Would you submit this to a top conference? If not — what would you change first? What are the 3 ugliest things about this diagram? | 2+ |

**Total minimum: graduated (see Section 4.1 for the model).** The red-team examines the diagram AFTER 3 fix cycles. The default floor is **≥15 findings** — sufficient to prove hostile intent without forcing fabrication on a clean diagram. If the self-score card shows **≥45/50** (near-perfect), red-team minimum drops to **≥10** — this is a verification audit, not a full adversarial pass. Per-zone floors are proportionally reduced: halve each floor when the total minimum is 15, quarter when it is 10.

A diagram with 30+ self-supervision defects does not become "clean" after one pass. But after 3 cycles of fixing 30+ defects per cycle, a genuinely clean diagram will have <10 residual issues. A hostile reviewer who "finds" 30 issues on such a diagram is fabricating compliance noise — real auditing finds real problems, even if there are only 10 of them.

Record every red-team finding with the same format as the defect inventory (Section 4.1). Fix all P0 and P1 findings. Document P2 findings as acknowledged gaps.

## 6. Self-Scoring (MANDATORY BEFORE HANDOFF)

Before offering the diagram to the user, you must score it yourself. Scores below threshold **block handoff** — you must continue iterating.

| Dimension | Score (1–10) | Evidence / Reason for deduction |
|-----------|-------------|-------------------------------|
| Text readability | /10 | |
| Arrow accuracy | /10 | |
| Color coherence | /10 | |
| Layout consistency | /10 | |
| Style match to reference/spec | /10 | |
| **TOTAL** | **/50** | |

**Handoff thresholds (canonical — all files use these exact values):**

- **BLOCKED** — TOTAL < 30, OR any dimension ≤ 4. You must continue iterating. Do not ask the user — just keep working.
- **BORDERLINE** — 30 ≤ TOTAL < 40 with no dimension ≤ 4. List 5+ specific things you would fix in the next pass. Handoff only if the user explicitly asked for a quick result.
- **ALLOWED** — TOTAL ≥ 40 AND every dimension ≥ 6. A dimension scored 5 is NOT allowed — it is borderline; review and improve it before handoff.

If you give yourself a score, you must explain why each point was deducted with concrete, screenshot-visible evidence. "Lost a point for overall feel" is not acceptable. "Font size 8pt on the `data_pipeline` box is illegible at normal zoom, confirmed by screenshot measurement — deducted 2 points" is.

If your self-score is 45+/50, re-run the red-team audit. Perfection is usually self-deception.

## 7. Blockers That Prevent Handoff

Do not claim completion while any of these remain visible in the latest screenshot:

- required component missing
- required connector missing
- arrow direction, fan-in/fan-out, or feedback semantics wrong
- connector passes through important text or hides labels
- text escapes, is clipped, or is hidden behind a shape or arrow
- boxes overlap unintentionally
- icons are incoherent, mismatched, or represent the wrong concept
- style visibly conflicts with an explicit user constraint
- screenshot is partial or clipped and cannot prove the full diagram is acceptable
- self-score is below threshold (Section 6)
- fewer than 3 screenshot→review→fix cycles completed (Section 4.1)
- red-team audit not completed (Section 5)

For high-fidelity or user-critical work, treat these as P0/P1 defects and iterate. If time or tooling prevents another pass, list the blocker explicitly as a remaining gap and state why it was not fixed.

## 8. Defect Logging For Any Iterative Diagram

For exact replication, also follow `reference-replication-protocol.md` for artifact requirements. For non-replication diagrams, maintain:

```markdown
## Screenshot Review Cycle N
| # | issue | observed screenshot | requirement/source evidence | cells to change | severity | status |

## Red-Team Audit (pre-handoff)
| # | finding | location | severity | fix or accept? |

## Self-Score (pre-handoff)
| dimension | score | evidence |

## Remaining Gaps
| gap | severity | reason | next action |
```

The log must include negative findings, not only confirmations. A useful self-review says what is still wrong, ambiguous, or approximated.

**The defect log is append-only after Cycle 1.** Do not delete or regenerate earlier cycle reports. A reviewer must be able to see the full debugging chain. If a fix regressed, an earlier row's fix → this cycle's regression tells the story.

## 9. How To Respond To User Visual Feedback

When the user points out a visual or semantic mistake:

1. **Do not defend the output.** If the user can see it and you did not flag it, your self-supervision failed. Acknowledge this.
2. Re-open the relevant reference/prompt context and the latest screenshot.
3. Explain the corrected interpretation in one sentence before editing.
4. Patch the source `.drawio` or generator, not only the screenshot.
5. Render again and inspect a focused crop plus the full canvas.
6. Append the mistake and correction to the defect log with a note: "Found by user, missed by self-supervision cycle N."
7. **Re-run the red-team audit.** A user-found defect proves your self-supervision was incomplete. Find the other defects you also missed.

## 10. Completion Standard

A diagram can be handed off only after:

- style extraction completed (Section 3) if reference images were provided
- the latest screenshot was reviewed against the brief or references
- a COMPLETE defect inventory across all 9 zones was created and logged
- all P0 and P1 defects from the latest inventory were fixed
- fix verification confirmed each claimed fix actually resolved the issue
- no P0/P1 blockers remain unmentioned
- at least 3 screenshot→inventory→fix→verify cycles are documented in the defect log (with graduated defect minima per cycle, see Section 4.1)
- a red-team audit was performed across all 9 zones (≥15 findings; ≥10 if self-score ≥45/50 — see Section 5)
- style-reference tasks: the latest screenshot was compared **side-by-side against the reference image** (not just against the extraction table) — mandatory every cycle
- self-score meets the ALLOWED threshold (TOTAL ≥ 40 AND every dimension ≥ 6; a dimension of 5 is borderline — review and improve before handoff)
- `validate_visual_quality.py` passed (zero FAILs) before the first preview
- `validate_drawio.py` passed after the final XML edit
- remaining approximations and P2 defects are explicitly listed
- the user receives the `.drawio` path, latest screenshot path, preview URL if running, self-score card, defect inventory summary, and known gaps

For "100% reproduction", never say the work is perfect unless the latest side-by-side review finds no visible mismatch. Otherwise say exactly what remains and what the next patch target is.
