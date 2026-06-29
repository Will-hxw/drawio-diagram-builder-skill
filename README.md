# Research Draw.io Diagram Skill

A portable agent skill for producing publication-style, editable diagrams.net / draw.io figures.

This repository is for AI agents that need to turn papers, method descriptions, codebases, screenshots, or rough prompts into clean `.drawio` diagrams, then inspect and refine them with browser screenshots. It works best for research figures, ML/system diagrams, framework overviews, training/inference pipelines, dataset construction flows, and architecture diagrams.

The skill is not limited to Codex. Codex can install it as a local skill, while Claude Code, OpenCode, or other local agents can use it as an instruction pack: read `drawio-diagram-builder/SKILL.md`, load the relevant references, and run the bundled helper scripts.

## Why This Exists

LLMs can write draw.io XML, but the first result is often not review-ready:

- text overlaps or escapes boxes;
- arrows route incorrectly;
- loop arrows look wrong;
- icons are missing or inconsistent;
- reference figures are embedded as images instead of redrawn as editable objects;
- large diagrams fail on Windows when opened through huge draw.io URLs or `.url` shortcuts.

This skill gives an agent a repeatable workflow: create editable XML, preview it through a short local URL, screenshot the result, fix visible defects, and validate the `.drawio` file before handoff.

## What It Is Good For

- Recreating a paper figure as editable draw.io objects.
- Drawing a method overview from a research paper or technical report.
- Converting a repository into an architecture or data-flow diagram.
- Creating ML pipeline diagrams with stages, models, datasets, rewards, losses, and serving paths.
- Iteratively polishing visual details such as typography, colors, dashed containers, highlights, arrows, icons, and spacing.
- Avoiding the Windows long-URL failure caused by large draw.io payloads.

## What It Is Not

- It is not a draw.io replacement.
- It is not affiliated with diagrams.net, draw.io, or JGraph.
- It does not guarantee one-shot pixel perfection. High-fidelity reproduction usually requires several screenshot-feedback passes.
- It should not be used with sensitive diagrams through the hosted diagrams.net embed page unless that is acceptable for your environment.

## Repository Layout

```text
.
+-- drawio-diagram-builder/      # Agent skill folder
|   +-- SKILL.md                 # Main workflow loaded by the agent
|   +-- agents/openai.yaml       # Optional Codex/OpenAI UI metadata
|   +-- references/
|   |   +-- drawio-workflow.md   # Research and screenshot iteration workflow
|   |   +-- xml-authoring.md     # Draw.io XML patterns and layout notes
|   +-- scripts/
|       +-- make_drawio_preview.py
|       +-- serve_drawio_preview.py
|       +-- validate_drawio.py
+-- examples/minimal.drawio
+-- tests/smoke_test.py
+-- README.md
+-- LICENSE
+-- .gitignore
```

## Agent-Assisted Install

If you use Claude, Codex, or another local coding agent, copy this prompt into the agent:

```text
Install this open-source research draw.io diagram skill for my local AI-agent workflow:

https://github.com/Will-hxw/drawio-diagram-builder-skill

Requirements:
1. Clone or download the repository.
2. Locate the folder named drawio-diagram-builder.
3. If my agent supports a local skills directory, install the folder there.
   - For Codex on Windows, use %USERPROFILE%\.codex\skills
   - For Codex on macOS/Linux, use ~/.codex/skills
   - For other agents, use their documented skills/instructions location.
4. If my agent does not support skills, keep the repository in a stable local path and tell me to reference drawio-diagram-builder/SKILL.md when asking for diagram work.
5. Verify that SKILL.md exists in the installed folder.
6. If Python is available, run:
   python tests/smoke_test.py
7. Do not overwrite an existing drawio-diagram-builder folder without asking me first.
8. Tell me whether I need to restart the agent for the skill to be discovered.
```

## Manual Install

### Codex on Windows

```powershell
git clone https://github.com/Will-hxw/drawio-diagram-builder-skill.git
Set-Location .\drawio-diagram-builder-skill

New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force .\drawio-diagram-builder "$env:USERPROFILE\.codex\skills\"
```

Restart Codex after copying the skill.

### Codex on macOS / Linux

```bash
git clone https://github.com/Will-hxw/drawio-diagram-builder-skill.git
cd drawio-diagram-builder-skill

mkdir -p "$HOME/.codex/skills"
cp -R drawio-diagram-builder "$HOME/.codex/skills/"
```

Restart Codex after copying the skill.

### Other Agents

If your agent has a skill or instruction directory, copy `drawio-diagram-builder/` there.

If it does not, keep the repository locally and include this in your prompt:

```text
Use the research draw.io diagram skill at /path/to/drawio-diagram-builder.
Read SKILL.md first. Load references/drawio-workflow.md for the end-to-end workflow and references/xml-authoring.md when writing or repairing draw.io XML. Use the scripts folder for preview and validation.
```

## Example Prompts

```text
Use $drawio-diagram-builder to read this paper section and create an editable draw.io method overview. Make it look like a polished research figure, not a generic flowchart.
```

```text
Use $drawio-diagram-builder to reproduce this reference figure as editable draw.io XML. Do not embed the screenshot as the final result. Preview it locally, screenshot it, compare defects, and iterate.
```

```text
Use the drawio-diagram-builder skill in this repository to inspect the codebase and draw a system architecture diagram with services, data stores, queues, and request flow.
```

## Agent Workflow

The skill expects the agent to follow this loop:

1. Understand the source material: prompt, paper, repository, screenshot, or existing diagram.
2. Extract the figure specification: entities, stages, labels, visual hierarchy, colors, typography, icons, arrows, and caption policy.
3. Generate editable `.drawio` XML with stable object IDs and explicit geometry.
4. Preview through a short local URL instead of a huge encoded draw.io URL.
5. Capture a screenshot of the rendered diagram.
6. Compare the screenshot against the reference or requirements.
7. Fix a small batch of visible defects.
8. Repeat until the diagram is ready.
9. Validate the file before handoff.

This is intentionally evidence-driven. The agent should not claim a high-fidelity diagram is done without inspecting a rendered screenshot.

## Helper Scripts

No third-party Python packages are required.

### Validate a `.drawio` file

```powershell
python .\drawio-diagram-builder\scripts\validate_drawio.py .\examples\minimal.drawio
```

By default, the validator flags embedded raster images because final research diagrams should usually remain editable. Use `--allow-raster` only when image assets are intentional.

### Generate a short-URL preview page

```powershell
python .\drawio-diagram-builder\scripts\make_drawio_preview.py `
  .\examples\minimal.drawio `
  --out .\drawio-preview.html

python -m http.server 8765 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8765/drawio-preview.html?rev=1
```

### Generate and serve in one command

```powershell
python .\drawio-diagram-builder\scripts\serve_drawio_preview.py .\examples\minimal.drawio --port 8765
```

The preview page loads diagrams.net in an iframe and sends XML with `postMessage`. This avoids passing the whole diagram through the browser address bar.

## Windows Notes

Large draw.io diagrams can fail on Windows when a tool tries to open a huge `.url` shortcut or a `#create=` URL. The error can look like this:

```text
The data area passed to a system call is too small.
```

Use `serve_drawio_preview.py` or `make_drawio_preview.py` instead. They keep the browser URL short and inject the XML after the page loads.

When editing inside the preview, the blue Save button downloads a `.drawio` file. It cannot silently overwrite your local source file because browsers block arbitrary filesystem writes. Move the downloaded file back to your intended working path before continuing automated edits.

## Research Figure Guidance

For scientific diagrams, prefer:

- exact terminology from the paper or codebase;
- visible stage boundaries and readable hierarchy;
- consistent font family, stroke width, and color palette;
- explicit arrow grammar for generation, training, feedback, evaluation, and serving flows;
- editable icons or documented asset substitutions;
- line-level text cells when highlights or dense labels must align precisely;
- screenshot-based inspection before declaring completion.

Avoid:

- embedding a screenshot as the final "editable" figure;
- decorative layouts that obscure the method;
- vague labels such as "process" or "model" when the paper gives real names;
- one-shot delivery for high-fidelity reference reproduction.

## Development Smoke Test

```powershell
python .\tests\smoke_test.py
```

The smoke test checks that the example parses, preview generation works, and the generated preview contains the diagrams.net iframe and save hook.

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

This project is not affiliated with or endorsed by diagrams.net, draw.io, or JGraph.
