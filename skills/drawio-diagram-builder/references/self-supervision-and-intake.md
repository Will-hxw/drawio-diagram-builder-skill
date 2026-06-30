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

## 3. Self-Supervision Loop

After each rendered screenshot, inspect the result as if reviewing someone else's diagram. The review target is the whole current output, not only the last edited region.

Use this order:

1. **Requirement audit** - compare the screenshot against the user's prompt, brief, and source context.
2. **Semantic audit** - inspect arrows, loops, brackets, grouping, fan-in/fan-out, direction, and labels.
3. **Visual hygiene audit** - inspect text overflow, clipped text, line crossing, z-order, overlap, unreadable icons, and component alignment.
4. **Style audit** - compare typography, stroke, colors, corner radius, shadows, icon language, and density against the style contract or reference.
5. **Regression audit** - check that the latest fix did not break an earlier acceptable region.

For reference-image tasks, put the reference crop and current crop side by side when a local detail matters. For prompt-only tasks, compare the screenshot against the `diagram-brief.md` instead of pretending there is no reference.

## 4. Blockers That Prevent Handoff

Do not claim completion while any of these remain visible:

- required component missing
- required connector missing
- arrow direction, fan-in/fan-out, or feedback semantics wrong
- connector passes through important text or hides labels
- text escapes, is clipped, or is hidden behind a shape or arrow
- boxes overlap unintentionally
- icons are incoherent, mismatched, or represent the wrong concept
- style visibly conflicts with an explicit user constraint
- screenshot is partial or clipped and cannot prove the full diagram is acceptable

For high-fidelity or user-critical work, treat these as P0/P1 defects and iterate. If time or tooling prevents another pass, list the blocker explicitly as a remaining gap.

## 5. Defect Logging For Any Iterative Diagram

For exact replication, use `defect-log.md` from `reference-replication-protocol.md`. For non-replication diagrams, use the same discipline with a lighter table:

```markdown
## Screenshot Review
| issue | observed screenshot | requirement or source evidence | cells to change | patch summary | status |

## Requirement And Semantic Audit
| check | screenshot | expected from brief/source | actual | decision |

## Remaining Gaps
| gap | severity | reason | next action |
```

The table must include negative findings, not only confirmations. A useful self-review says what is still wrong, ambiguous, or approximated.

## 6. How To Respond To User Visual Feedback

When the user points out a visual or semantic mistake:

1. Treat it as evidence that the previous self-supervision missed something.
2. Re-open the relevant reference/prompt context and the latest screenshot.
3. Explain the corrected interpretation in one sentence before editing.
4. Patch the source `.drawio` or generator, not only the screenshot.
5. Render again and inspect a focused crop plus the full canvas.
6. Append the mistake and correction to the defect log.

Do not defend the previous output if the screenshot contradicts it. The objective is to make the diagram correct, not to justify the prior pass.

## 7. Completion Standard

A diagram can be handed off only after:

- the latest screenshot was reviewed against the brief or references
- no P0/P1 blockers remain unmentioned
- remaining approximations are explicitly listed
- validation scripts passed when available
- the user receives the `.drawio` path, latest screenshot path, preview URL if running, and known gaps

For "100% reproduction", never say the work is perfect unless the latest side-by-side review finds no visible mismatch. Otherwise say exactly what remains and what the next patch target is.
