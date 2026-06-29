# Draw.io Diagram Builder Skill

An open-source Codex skill for creating, previewing, and iteratively refining editable diagrams.net / draw.io diagrams.

This skill is designed for workflows where an agent must generate a real `.drawio` XML file from a prompt, paper, codebase, architecture description, or reference image, then visually verify and improve it through browser screenshots.

It was built around a practical Windows failure mode: large draw.io diagrams can break when opened through huge encoded URLs or `.url` shortcuts. The bundled preview helper avoids that path by serving a short local URL and loading XML into diagrams.net with `postMessage`.

## What It Does

- Guides Codex to create editable `.drawio` XML instead of embedding screenshots.
- Supports prompt-to-diagram, paper-to-diagram, codebase-to-diagram, and reference-image replication.
- Provides a Windows-friendly local preview workflow that avoids long URL failures.
- Encourages screenshot-driven refinement for text overlap, arrows, icons, colors, and layout.
- Includes helper scripts for local preview and `.drawio` sanity checks.

## Repository Layout

```text
.
+-- drawio-diagram-builder/      # The Codex skill folder to install
|   +-- SKILL.md
|   +-- agents/openai.yaml
|   +-- references/
|   +-- scripts/
+-- examples/minimal.drawio
+-- tests/smoke_test.py
+-- README.md
+-- LICENSE
+-- .gitignore
```

## Requirements

- Codex with local skills support.
- Python 3.9 or newer.
- A browser.
- Internet access to `https://embed.diagrams.net/` for the bundled preview page.

No Python packages are required.

Optional:

- draw.io desktop or draw.io CLI for export workflows.
- `@drawio/mcp` for small quick-open diagrams. For large diagrams on Windows, prefer this skill's local preview workflow.

## Install

### AI-assisted install

If you use Claude, Codex, or another local coding agent, the easiest path is to copy this prompt into the agent and let it install the skill for you:

```text
Please install the open-source Codex skill from this repository:

https://github.com/Will-hxw/drawio-diagram-builder-skill

Tasks:
1. Clone or download the repository.
2. Locate the skill folder named drawio-diagram-builder.
3. Copy that folder into my local Codex skills directory.
   - On Windows, use %USERPROFILE%\.codex\skills
   - On macOS/Linux, use ~/.codex/skills
4. Verify that SKILL.md exists at:
   - Windows: %USERPROFILE%\.codex\skills\drawio-diagram-builder\SKILL.md
   - macOS/Linux: ~/.codex/skills/drawio-diagram-builder/SKILL.md
5. Run the included smoke test if Python is available:
   python tests/smoke_test.py
6. Tell me whether I need to restart Codex for the skill to be discovered.

Do not overwrite unrelated local skills. If a drawio-diagram-builder folder already exists, back it up or ask me before replacing it.
```

### Windows PowerShell

```powershell
git clone https://github.com/Will-hxw/drawio-diagram-builder-skill.git
Set-Location .\drawio-diagram-builder-skill

New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force .\drawio-diagram-builder "$env:USERPROFILE\.codex\skills\"
```

Start a new Codex session after copying the skill.

### macOS / Linux

```bash
git clone https://github.com/Will-hxw/drawio-diagram-builder-skill.git
cd drawio-diagram-builder-skill

mkdir -p "$HOME/.codex/skills"
cp -R drawio-diagram-builder "$HOME/.codex/skills/"
```

Start a new Codex session after copying the skill.

## Usage

Ask Codex to use the skill explicitly:

```text
Use $drawio-diagram-builder to create an editable draw.io architecture diagram from this repository.
```

```text
Use $drawio-diagram-builder to reproduce this reference figure as an editable .drawio file. Iterate with screenshots until the layout matches.
```

```text
Use $drawio-diagram-builder to read this paper section and draw the method pipeline in diagrams.net style.
```

## Local Preview Workflow

Generate and serve a preview from a `.drawio` file:

```powershell
python .\drawio-diagram-builder\scripts\serve_drawio_preview.py .\examples\minimal.drawio --port 8765
```

Open the printed URL:

```text
http://127.0.0.1:8765/drawio-preview.html?rev=1
```

The URL stays short. The XML is sent into the diagrams.net iframe by `postMessage`, which avoids the Windows `.url` failure:

```text
The data area passed to a system call is too small.
```

You can also generate only the preview HTML:

```powershell
python .\drawio-diagram-builder\scripts\make_drawio_preview.py `
  .\examples\minimal.drawio `
  --out .\drawio-preview.html

python -m http.server 8765 --bind 127.0.0.1
```

## Saving Edited Diagrams

The preview page cannot silently overwrite local files. Browsers intentionally block arbitrary filesystem writes.

When you edit the diagram in the preview and click the blue Save button, the helper page downloads a `.drawio` file. Move that downloaded file back to your intended working path before continuing automated edits.

## Validate a Diagram

```powershell
python .\drawio-diagram-builder\scripts\validate_drawio.py .\examples\minimal.drawio
```

For editable-only outputs, the validator flags embedded raster images unless you pass `--allow-raster`.

## Development Smoke Test

```powershell
python .\tests\smoke_test.py
```

The smoke test checks that:

- the example `.drawio` parses,
- the validator passes,
- the preview HTML is generated,
- the generated preview contains the diagrams.net iframe and save hook.

## Design Philosophy

The skill optimizes for diagrams that can survive real review:

- create editable XML, not screenshot wrappers;
- use fixed geometry for high-fidelity layout;
- split dense text into smaller cells when line alignment matters;
- use editable curved connectors for loop arrows;
- preview through a real browser and refine from evidence;
- fix a few visible issues per iteration instead of rewriting the whole diagram.

## Limitations

- diagrams.net rendering may differ slightly between editor, embed, desktop, and exported image.
- Exact icon/logo fidelity may require user-provided assets.
- The bundled preview uses the hosted diagrams.net embed page. Do not use it for sensitive diagrams unless that is acceptable for your environment.
- "100% visual reproduction" usually requires multiple screenshot comparison passes.

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

This project is not affiliated with or endorsed by diagrams.net, draw.io, or JGraph.
