# Research Draw.io Diagram Skill

面向 AI 编程助手的可移植技能包，用于根据论文、Prompt、代码仓库或截图生成适合发表的、可编辑的 diagrams.net / draw.io 图表。

```bash
npx skills add Will-hxw/drawio-diagram-builder-skill
```

> [English version](README.md)

## 前置依赖

| 依赖 | 原因 |
|------|------|
| **Python 3** (3.7+) | 预览和验证脚本 |
| **浏览器自动化**（Playwright MCP / Puppeteer / 浏览器工具等） | 截图反馈循环 — 这是技能的核心价值 |
| **网络连接** | 预览页面需要加载 `https://embed.diagrams.net/` |

没有浏览器自动化，agent 仍然可以生成 `.drawio` XML，但无法视觉验证结果。迭代精修是本技能的主要价值所在。

## 为什么需要这个

LLM 能写 draw.io XML，但一次成型的结果通常有问题：

- 文字溢出或露出框外
- 箭头路径错误
- 循环箭头走样
- 图标缺失或不对
- 参考图被直接嵌入为图片而非重绘为可编辑对象
- 大图表在 Windows 上因 URL 过长崩溃

这个技能提供一套可复现的流程：生成可编辑 XML → 本地短 URL 预览（非巨型编码 URL）→ 截图 → 修正可见缺陷 → 重复 → 验证。

## 产出示例

![可编辑的 draw.io 工作区](assets/drawio-editable-workspace.png)

![精修后的研究风格图表](assets/research-figure-output.png)

## 适用场景

- 将论文插图重绘为可编辑的 draw.io 对象
- 根据论文绘制方法总览图
- 将代码仓库转化为架构/数据流图
- 创建 ML 流水线图（阶段、模型、数据集、训练循环等）
- 迭代精修排版、配色、箭头、图标、间距

## 不适用场景

- 它不是 draw.io 的替代品，也与 diagrams.net / JGraph 无关
- 不保证一次性完美 — 高保真复现通常需要多轮截图反馈
- **⚠️ 不要用于敏感/机密图表** — 预览页面通过 `https://embed.diagrams.net/`（第三方托管页面）加载

## 仓库结构

```text
.
├── skills/drawio-diagram-builder/    # 技能目录（npx skills add 自动发现）
│   ├── SKILL.md                      # 主流程说明
│   ├── agents/openai.yaml
│   ├── references/
│   │   ├── drawio-workflow.md
│   │   └── xml-authoring.md
│   └── scripts/
│       ├── make_drawio_preview.py
│       ├── serve_drawio_preview.py
│       └── validate_drawio.py
├── assets/                           # README 配图
├── examples/minimal.drawio
├── tests/smoke_test.py
├── README.md
└── LICENSE
```

## 手动安装（不使用 npx skills）

### Claude Code

```bash
git clone https://github.com/Will-hxw/drawio-diagram-builder-skill.git
cp -R drawio-diagram-builder-skill/skills/drawio-diagram-builder ~/.claude/skills/
```

### Codex

**Windows:**

```powershell
git clone https://github.com/Will-hxw/drawio-diagram-builder-skill.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force .\drawio-diagram-builder-skill\skills\drawio-diagram-builder "$env:USERPROFILE\.codex\skills\"
```

**macOS / Linux:**

```bash
git clone https://github.com/Will-hxw/drawio-diagram-builder-skill.git
mkdir -p "$HOME/.codex/skills"
cp -R drawio-diagram-builder-skill/skills/drawio-diagram-builder "$HOME/.codex/skills/"
```

安装后重启 agent。

## 示例 Prompt

```text
使用 $drawio-diagram-builder 读取这段论文内容，创建一张可编辑的 draw.io 方法总览图。
```

```text
使用 $drawio-diagram-builder 将这张参考图重绘为可编辑的 draw.io XML。本地预览、截图、比对、迭代。
```

```text
使用本仓库中的 drawio-diagram-builder 技能，根据代码仓库绘制一张系统架构图。
```

## 辅助脚本

所有脚本均为纯 Python 3，无需 pip 依赖。

### 校验 `.drawio` 文件

```powershell
python .\skills\drawio-diagram-builder\scripts\validate_drawio.py .\examples\minimal.drawio
```

默认标记内嵌位图。仅在有意使用图片素材时加 `--allow-raster`。

### 一键生成预览并启动服务

```powershell
python .\skills\drawio-diagram-builder\scripts\serve_drawio_preview.py .\examples\minimal.drawio --port 8765
```

自动打开浏览器访问 `http://127.0.0.1:8765/drawio-preview.html`。

### 仅生成预览 HTML

```powershell
python .\skills\drawio-diagram-builder\scripts\make_drawio_preview.py .\examples\minimal.drawio --out .\drawio-preview.html
python -m http.server 8765 --bind 127.0.0.1
```

然后打开 `http://127.0.0.1:8765/drawio-preview.html?rev=1`。

预览页面通过 iframe 加载 `https://embed.diagrams.net/`，利用 `postMessage` 注入 XML，浏览器地址栏保持短 URL，避免 Windows 长 URL 崩溃。

## Windows 注意事项

- 带编码 draw.io URL 的大型 `.url` 快捷方式在 Windows 上会崩溃，请使用预览脚本替代
- 预览页面的蓝色保存按钮会下载 `.drawio` 文件 — 不会自动覆盖本地源文件（浏览器沙箱限制），需手动移回
- 使用 `127.0.0.1` 而非 `localhost` 以规避 IPv6 解析延迟

## 冒烟测试

```powershell
python .\tests\smoke_test.py
```

验证 XML 解析、预览 HTML 生成，确认输出包含 diagrams.net iframe。

## License

MIT。详见 [LICENSE](LICENSE)。
