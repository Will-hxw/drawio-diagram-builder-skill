# Top-Conference Computer-Science Figure Style

Use this guide when the user asks for a figure suitable for a computer-science paper, top conference, camera-ready paper, method overview, system architecture, ML pipeline, multimodal model, agent workflow, or benchmark/evaluation figure.

## Fallback Style References

If the user does not provide a style image, or the style input is too weak to guide a polished paper figure, load `assets/reference-images/REFERENCE-IMAGES.md` and inspect the bundled images in `assets/reference-images/`.

Use them only as style references:

- `topconf-memory-routing.png`: dense method/system overview with strong hierarchy, token bars, side modality panel, equations, and routing arrows.
- `topconf-knowledge-mining-pipeline.png`: algorithmic multi-panel pipeline with matrices, prompt pools, iteration axes, dashed groups, legends, and compact labels.
- `topconf-ccf-adapter-architecture.png`: model architecture with subfigures, encoder branches, expert/adaptor blocks, token sequences, loss arrows, and trainable/frozen legend.
- `topconf-handdrawn-rl-pipeline.png`: staged data-generation/training/RL workflow with soft dashed containers, input excerpts, reward models, serving block, and lightly hand-drawn emphasis.

Do not copy the reference topic or labels unless the user supplied the same content. Preserve the user's method and use the images only to decide layout, density, visual hierarchy, and component vocabulary.

## When Input Is Underspecified

Style can be inferred; scientific content cannot.

If the user provides a goal but not a style, use the bundled reference images as fallback style guidance. If the user omits core content such as modules, data flow, training stages, variables, losses, or architecture boundaries, ask for that missing content or make a clearly labeled conservative assumption in the brief.

Never invent a paper contribution, dataset, metric, loss, theorem, or module name just to fill a polished layout.

## Visual Language

- Prefer a wide landscape canvas for method overview figures and a multi-panel layout for dense methods.
- Use clear section labels such as `(a) Overall Architecture`, `Stage 1`, `Stage 2`, `Training`, `Inference`, or `Online Serving` when they match the content.
- Use muted academic palettes: pale blue, teal, green, orange, yellow, lavender, and light gray, with dark strokes and high-contrast text.
- Use dashed containers for groups, memory banks, prompt pools, datasets, reward models, or optional branches.

### The First Principle: Every Visual Element Must Mean Something

**A figure is not a decoration. Every shape, color, arrow, and icon must carry semantic load.** If you cannot answer "what does this element represent in the method?" in one sentence, the element must not exist. Drawing meaningless colored blocks to "look like a paper figure" is the single most common amateur failure — it produces noise, not communication.

Reference figures look good **because every element earns its place**. The token bars in a transformer paper represent actual token sequences. The matrix grids represent actual tensors. The stacked cards represent actual hierarchical levels. They are not "paper-figure-ish decorations" — they are the data itself, drawn. Copying the visual form without the semantic content produces a figure that looks busy but says nothing.

### What To Learn From Reference Images (And What NOT To Learn)

**Learn the essence, not the surface:**

| DO learn from the reference | DO NOT copy from the reference |
|----------------------------|-------------------------------|
| Overall composition and region hierarchy | Specific decorative shapes (token bars, matrix grids) unless your content has the same semantics |
| Whitespace rhythm and spacing discipline | Colorful blocks that have no meaning in your diagram |
| Font hierarchy (heading / subheading / body / caption sizes) | Layouts whose regions only make sense for the reference's topic |
| Arrow grammar (how data/control/feedback are distinguished) | The reference's exact labels or terminology |
| Palette coherence (muted, intentional, 5-8 colors) | Decorative gradients or rainbow strips |
| Density calibration (how much content fits per square inch) | Stacked cards or mini-tables with no data behind them |
| How every element is placed exactly where it belongs | Pure-color squares "because the reference had small squares" |

The reference figure is good because **the composition, spacing, typography, arrow language, and palette are perfect AND every element has a reason to exist.** The small squares in the reference are good because they represent tokens. The same squares in your diagram are garbage because they represent nothing.

### When Token Bars / Matrix Grids / Stacked Cards Are Justified

Use these visual forms **only when your content actually has the corresponding semantics:**

- **Token bars** — only when your method processes a discrete token sequence (LLM input/output, sequence models). Each cell should be a token or a position. Do not draw empty colored cells.
- **Matrix grids** — only when your method operates on an actual matrix/tensor (attention maps, weight matrices, feature maps). Each cell should be labeled or axis-annotated. Do not draw a rainbow grid "for show."
- **Mini tables** — only when you have actual tabular data (hyperparameters, benchmark results, dataset stats). Headers and rows must be real.
- **Stacked cards** — only when representing an actual hierarchy or stack of layers (memory levels, encoder layers). Each card must be labeled with its level.
- **Small legends** — only when the figure uses color coding that needs explanation. Every legend entry must map to a real category in the figure.

**Before drawing any of these, answer in the brief:**
> "This [token bar / matrix / table / card stack] represents [concrete thing in the user's method], and each cell/row/level corresponds to [concrete unit]."

If you cannot fill that sentence with real content, **do not draw the element.** Use a labeled box with a text description instead. A labeled box that says "Token sequence (T=128)" is always better than a rainbow strip that says nothing.

### What "Looking Like A Paper Figure" Actually Requires

Amateur agents think a figure looks like a paper figure because it has small colored shapes. Wrong. A figure looks like a paper figure because:

1. **Composition is deliberate** — regions are placed with intent, not scattered. Hierarchy reads top-to-bottom or left-to-right cleanly.
2. **Whitespace is generous and even** — no cramped corners, no cavernous empty boxes, no inconsistent margins.
3. **Typography has clear hierarchy** — heading > subheading > body > caption, each at a deliberate size, consistently applied.
4. **Palette is muted and coherent** — 5-8 colors that form a family, each used for a semantic category, not one random color per shape.
5. **Arrows are precise** — every arrow has a source, a target, a direction, and a meaning. No arrow crosses a box or text. No arrow is decorative.
6. **Every element earns its place** — nothing is there "to look full." If you removed any element, the figure would lose information.
7. **Density matches content** — not sparse (4 boxes on a huge canvas), not crammed (50 elements overlapping). Each element has room to breathe.

Master these seven and your figure looks like a top-conference figure — with or without token bars. Master none of them and no amount of colored squares will save you.

- Use equations sparingly and place them near the arrow or block they explain.
- Use consistent arrow semantics: data flow, control flow, feedback, update/writeback, loss, reward, and retrieval should be visually distinguishable.
- Prefer editable primitives for recurring elements. Use bundled SVG icons only when a primitive approximation would be slower or less clear.

## Top-Conference Quality Bar

Before handoff, the latest screenshot must satisfy:

- no clipped labels, hidden text, accidental overlaps, or arrows crossing labels
- every connector has a defined source, target, direction, and semantic meaning
- subfigure labels, legends, equations, and color coding are internally consistent
- the figure reads at paper scale: important text remains legible when the screenshot is scaled down
- the `.drawio` passes `scripts/validate_drawio.py`; use `--strict` for final camera-ready work when warnings should block handoff
