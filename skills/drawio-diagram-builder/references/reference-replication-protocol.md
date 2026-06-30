# Reference Image Replication Protocol

Use this protocol whenever the user provides a reference image and asks to reproduce, redraw, copy, replicate, or closely match it in draw.io.

The goal is to make high-fidelity drawing an evidence-driven engineering process. First convert the image into a mechanical visual specification, then draw from that specification, then verify with rendered screenshots.

## Hard Rules

1. Do not begin `.drawio` XML until the required intermediate artifacts exist.
2. The primary output is a `.drawio` file. Preview HTML is derived and must not be treated as the source of truth.
3. Never silently omit a visible component. If an icon, formula, symbol, or image cannot be reproduced exactly, add it to `asset-ledger.md`.
4. Do not use "close enough" language for high-fidelity work. Record remaining mismatches in `defect-log.md`.
5. Do not finish without at least one rendered screenshot review. For 100% reproduction requests, keep iterating until the user accepts or the remaining gaps are explicitly listed.
6. Do not judge fidelity from a clipped browser viewport. The screenshot must include the full draw.io page/canvas or a deliberate canvas-only crop.
7. If the screenshot shows large structural errors, repair `visual-spec.md` and `layout-grid.md` first, then patch XML. Do not keep nudging objects without updating the plan.

## Required Artifacts

Create these files next to the working `.drawio` file:

```text
visual-spec.md
layout-grid.md
asset-ledger.md
defect-log.md
```

Run `scripts/validate_replication_artifacts.py <workdir>` before authoring XML.

After the latest screenshot pass and before handoff, run:

```powershell
python scripts/validate_replication_artifacts.py <workdir> --require-screenshot-review
```

This final check fails if `defect-log.md` still contains placeholder screenshot rows.

## 1. visual-spec.md

This file captures what is visible.

Required sections:

```markdown
# Visual Spec

## Source
- Reference image:
- Target drawio:
- Canvas:
- Font policy:

## Global Style
- Background:
- Primary font:
- Stroke style:
- Arrow style:
- Color palette:

## Regions
| id | bbox x,y,w,h | role | visual notes |

## Text Blocks
| id | bbox x,y,w,h | text | font | alignment | priority |

## Shapes
| id | bbox x,y,w,h | type | fill | stroke | notes |

## Connectors
| id | from | to | route | arrowheads | label | notes |

## Icons And Images
| id | bbox x,y,w,h | meaning | exact/approx/missing | replacement plan |
```

For complex research figures, use region IDs such as:

- `top_problem_statement`
- `bottom_method_overview`
- `memory_hierarchy`
- `routing_controller`
- `latent_workspace`
- `multimodal_streams`

## 2. layout-grid.md

This file turns the visual spec into coordinates. High-fidelity drawing needs explicit geometry, not vague relative placement.

Required sections:

```markdown
# Layout Grid

## Canvas
- width:
- height:
- scale assumption:
- margin:

## Grid Lines
| name | x | y | purpose |

## Region Boxes
| id | x | y | w | h |

## Repeated Components
| family | count | cell size | spacing | start x,y |

## Drawing Order
1. background regions
2. containers
3. internal shapes
4. connectors
5. text
6. icons
7. highlights/overlays
```

If the reference has a dense layout, do not rely on relative placement only. Use explicit x/y/w/h for each major container.

## 3. asset-ledger.md

This file prevents silent icon loss.

Required sections:

```markdown
# Asset Ledger

## Exact Assets
| id | source | path | usage |

## Editable Primitive Icons
| id | built from | fidelity notes |

## Approximations
| id | reference meaning | approximation | why |

## Missing Assets
| id | reference meaning | blocking issue | user action needed |
```

If using an embedded raster image, state why editability is intentionally reduced.

## 4. defect-log.md

This file records screenshot-based refinement.

Required sections:

```markdown
# Defect Log

## Pass 0 - Initial Plan Review
| issue | reference evidence | planned fix |

## Pass 1 - Screenshot Review
| issue | observed screenshot | reference evidence | XML cells to change | patch summary | status |

## Red-Team Visual Audit
| check | observed screenshot | finding | XML cells to change | status |

## Remaining Gaps
| gap | severity | reason | next action |
```

Each screenshot pass must add concrete defects. Avoid entries like "looks bad"; write "right-side multimodal panel is 18% too narrow" or "top dense-token bar missing icon cells".

The red-team audit is a separate pass whose goal is to find mistakes, not to confirm improvement. It must explicitly inspect:

- arrow direction and arrowhead placement
- bracket orientation and grouped annotation direction
- connector paths that cross text, pass through boxes, or create impossible flow
- box overlaps, clipped shapes, and z-order mistakes
- text overflow, wrapped titles, illegible formulas, and labels crossed by lines
- regressions introduced by the latest patch

## Minimum Quality Gate

Before handoff, verify:

- The `.drawio` file exists and is the primary artifact.
- `validate_drawio.py` passes.
- `validate_replication_artifacts.py <workdir> --require-screenshot-review` passes.
- Preview HTML was regenerated after the latest XML edit.
- At least one screenshot was reviewed.
- `defect-log.md` includes a red-team visual audit of the latest screenshot.
- `defect-log.md` lists remaining mismatches.
- No visible reference component was silently omitted.

For a "100% reproduction" request, the defect log must not claim perfection. It must either show that no visible mismatches remain after screenshot review, or list the exact remaining mismatches and the next patch targets.

## High-Fidelity Replication Discipline

If the first draft is messy, do not continue patching randomly. Return to `visual-spec.md` and `layout-grid.md`, identify which observation or coordinate assumption failed, and repair the plan before editing XML again.

Prefer a simpler but structurally faithful first draft over a visually dense but incoherent drawing:

1. Correct canvas and major regions.
2. Correct container hierarchy.
3. Correct text placement.
4. Correct arrows.
5. Correct icons.
6. Correct colors and polish.

Only after the structure is correct should the agent increase visual density.

When a generated result looks bad, inspect these first-principles failure points:

- canvas scale or browser zoom makes the page clipped
- headings are too large and wrap unexpectedly
- multiline labels overlap nearby annotations
- bottom labels escape or touch the page edge
- connector routes use straight lines where the reference uses loops
- icons were silently replaced with generic symbols
- background fills, shadows, and dashed borders were skipped

Use the defect log as an engineering ledger: every visible mismatch should map to either a missing observation, an incorrect coordinate, an unavailable asset, or a draw.io rendering difference.
