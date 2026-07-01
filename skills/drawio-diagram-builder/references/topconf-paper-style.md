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
- Use token bars, matrix grids, mini tables, stacked cards, and small legends to communicate ML workflows.
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
