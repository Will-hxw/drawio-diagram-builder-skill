# Bundled Icon Assets

This directory contains a curated set of SVG icons for research and technical diagrams.

## Source And License

- Source: Tabler Icons, outline SVG set
- Repository: https://github.com/tabler/tabler-icons
- License: MIT
- Local license copy: `tabler/LICENSE`
- Local SVG path: `tabler/outline/*.svg`

These assets are bundled so agents do not need to search the web for every small paper-figure icon. Use them only when the license copy is present in the installed skill.

## When To Use

Use bundled SVG icons when:

- the reference figure clearly contains small semantic icons
- a primitive approximation would take too long or look inconsistent
- the user values visual fidelity over fully primitive-editable icon internals
- the icon is generic enough for a Tabler symbol, such as document, image, video, database, clock, tools, search, server, route, or warning

Use `references/primitive-icons.md` instead when:

- the user explicitly requires every icon to be made from editable draw.io primitives
- the reference icon is simple enough to build from rectangles, ellipses, lines, and arrows
- the icon must match a hand-drawn or paper-specific style

Ask for an exact asset when:

- the reference uses a branded logo
- the icon has paper-specific meaning that a generic symbol would distort
- the user asks for exact reproduction and no bundled icon matches

## Inventory

### Documents And Text

- `file-text.svg`
- `file-description.svg`
- `file-analytics.svg`
- `notes.svg`
- `list-details.svg`
- `clipboard-text.svg`
- `forms.svg`

### Media And Modalities

- `photo.svg`
- `camera.svg`
- `video.svg`
- `volume.svg`
- `microphone.svg`
- `music.svg`

### Storage And Infrastructure

- `database.svg`
- `database-search.svg`
- `database-cog.svg`
- `server.svg`
- `server-cog.svg`
- `cloud.svg`
- `cloud-cog.svg`
- `folder.svg`
- `folders.svg`
- `archive.svg`
- `package.svg`
- `schema.svg`
- `stack.svg`
- `layers-intersect.svg`

### Models, Graphs, And Routing

- `brain.svg`
- `robot.svg`
- `cpu.svg`
- `cpu-2.svg`
- `binary-tree.svg`
- `binary.svg`
- `graph.svg`
- `network.svg`
- `network-off.svg`
- `hierarchy.svg`
- `sitemap.svg`
- `route.svg`
- `route-square.svg`
- `git-branch.svg`
- `git-commit.svg`
- `git-merge.svg`

### Arrows, Loops, And Iteration

- `arrows-right-left.svg`
- `arrows-split.svg`
- `arrows-join.svg`
- `arrow-right.svg`
- `arrow-left.svg`
- `arrow-loop-right.svg`
- `refresh.svg`
- `repeat.svg`
- `transfer.svg`
- `timeline.svg`

### Metrics, Rewards, And Status

- `target.svg`
- `scale.svg`
- `chart-bar.svg`
- `chart-line.svg`
- `chart-dots.svg`
- `trophy.svg`
- `alert-triangle.svg`
- `info-circle.svg`
- `circle-check.svg`
- `circle-x.svg`
- `clock.svg`
- `hourglass.svg`

### Code, Math, And Scientific Notation

- `code.svg`
- `terminal-2.svg`
- `braces.svg`
- `function.svg`
- `math-function.svg`
- `sum.svg`
- `vector.svg`
- `atom.svg`
- `flask.svg`
- `microscope.svg`
- `hexagon.svg`

### Security, Privacy, And Visibility

- `key.svg`
- `lock.svg`
- `shield-check.svg`
- `eye.svg`
- `eye-off.svg`

### Devices, Context, And Product Workflow

- `device-desktop.svg`
- `device-mobile.svg`
- `world.svg`
- `bulb.svg`
- `wand.svg`
- `rocket.svg`

### Tools And Controls

- `tools.svg`
- `tool.svg`
- `settings.svg`
- `search.svg`
- `zoom-scan.svg`
- `filter.svg`
- `plug.svg`
- `api.svg`

### Basic Marks And Visual Accents

- `box.svg`
- `square.svg`
- `circle.svg`
- `dots.svg`
- `sparkles.svg`

## Asset Ledger Entry

When using a bundled SVG, record it in `asset-ledger.md`:

```markdown
| id | source | path | usage |
| retrieval_icon | Tabler Icons MIT | assets/icons/tabler/outline/search.svg | search/retrieval symbol |
```

If the bundled SVG is only an approximation of the reference icon, also record it under `## Approximations`.
