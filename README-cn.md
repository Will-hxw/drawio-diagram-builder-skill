# Research Draw.io Diagram Skill

用于根据论文、Prompt、代码仓库、项目上下文、截图，以及一张或多张视觉参考图，生成适合发表的、可编辑的 diagrams.net / draw.io 图表。

```bash
npx skills add Will-hxw/drawio-diagram-builder-skill
```

> [English version](README.md)

## 让 Agent 直接安装

把下面这段话复制给 Codex、Claude Code 或其他本地 coding agent：

```text
请从下面这个仓库安装并测试 drawio-diagram-builder skill：
https://github.com/Will-hxw/drawio-diagram-builder-skill

安装完成后运行 smoke test，并告诉我实际安装到哪个 skill 路径。
```

安装后让 agent 针对它实际加载的 skill 路径运行内置更新检查：

```powershell
python <installed-skill-dir>\scripts\check_skill_update.py
```

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

这个技能提供一套可复现的流程：把用户的文字和图片输入综合成 diagram brief → 生成可编辑 XML → 本地短 URL 预览（非巨型编码 URL）→ 截图 → 自监督检查可见缺陷和语义缺陷 → 修正 → 重复 → 验证。

针对参考图复刻，技能会走更严格的协议：agent 必须先写视觉规格、坐标网格、素材台账和缺陷日志，再开始画 `.drawio`。最终交付时必须证明已经截图复审，而不是只生成一份能解析的 XML。

对于 Prompt、论文、代码库或混合输入的绘图任务，技能也要求走自监督协议：把每个输入区分为内容来源、结构来源、风格来源、版式来源或素材来源；画箭头前先定义连接语义；截图后检查需求偏差、箭头含义、文字遮挡、图标一致性、风格漂移和回归问题。

这是高保真科研绘图本来就应该遵循的工作流：把用户输入转化为可观察的需求和视觉约束，渲染可编辑的 draw.io 结果，对照 brief 和参考图，再修复具体差异。

## 产出示例

![可编辑的 draw.io 工作区](assets/drawio-editable-workspace.png)

![精修后的研究风格图表](assets/research-figure-output.png)

## 适用场景

- 将论文插图重绘为可编辑的 draw.io 对象
- 根据论文绘制方法总览图
- 将代码仓库转化为架构/数据流图
- 创建 ML 流水线图（阶段、模型、数据集、训练循环等）
- 将文字需求与多张图片/风格参考综合为一份清晰的绘图 brief
- 审查 fan-in、fan-out、反馈回路、分组路径、箭头方向等连接语义
- 迭代精修排版、配色、箭头、图标、间距
- 内置一批 MIT 许可的 Tabler SVG 图标，覆盖常见科研图符号

## 不适用场景

- 它不是 draw.io 的替代品，也与 diagrams.net / JGraph 无关
- 不保证一次性完美 — 高保真复现通常需要多轮截图反馈
- 内置 SVG 图标是矢量资产，但其内部不会拆成 draw.io primitive 对象；如果要求图标内部也完全可编辑，请使用 primitive recipes

## 仓库结构

```text
.
├── skills/drawio-diagram-builder/    # 技能目录（npx skills add 自动发现）
│   ├── SKILL.md                      # 主流程说明
│   ├── VERSION                       # 已安装 skill 的版本标识
│   ├── agents/openai.yaml
│   ├── assets/icons/                 # 内置 MIT 许可 SVG 图标集
│   ├── references/
│   │   ├── drawio-workflow.md
│   │   ├── primitive-icons.md
│   │   ├── reference-replication-protocol.md
│   │   ├── self-supervision-and-intake.md
│   │   └── xml-authoring.md
│   └── scripts/
│       ├── check_skill_update.py
│       ├── make_drawio_preview.py
│       ├── serve_drawio_preview.py
│       ├── validate_drawio.py
│       └── validate_replication_artifacts.py
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

为避免读到旧版本，请让 agent 报告它实际读取的 skill 路径，并运行：

```powershell
python <installed-skill-dir>\scripts\check_skill_update.py
```

如果脚本返回 `OUTDATED` 或 `UNKNOWN`，请从官方仓库重新安装，不要靠检查某个文件名或某段文本来判断是否最新。

## 示例 Prompt

```text
使用 $drawio-diagram-builder 读取这段论文内容，创建一张可编辑的 draw.io 方法总览图。
```

```text
使用 $drawio-diagram-builder 综合我的项目上下文、绘图需求和这两张风格参考图，生成一张科研论文风格的架构图。本地预览、截图、自监督检查箭头语义和文字遮挡，然后迭代。
```

```text
使用 $drawio-diagram-builder 将这张参考图重绘为可编辑的 draw.io XML。本地预览、截图、比对、迭代。
```

```text
使用本仓库中的 drawio-diagram-builder 技能，根据代码仓库绘制一张系统架构图。
```

## 辅助脚本

所有脚本都是纯 Python 3，无需安装 pip 依赖。

## 内置图标资产

skill 内置了一批 Tabler Icons outline SVG：

```text
skills/drawio-diagram-builder/assets/icons/tabler/outline/
```

完整清单和许可证说明见 `skills/drawio-diagram-builder/assets/icons/ICON-MANIFEST.md`。这些图标适合通用的文档、媒体、存储、模型、路由、状态、指标、工具类符号。如果高保真复刻需要品牌图标或论文专属符号，应提供精确资产，或在 `asset-ledger.md` 中记录为近似项。

### 检查已安装 skill 是否为最新版

```powershell
python .\skills\drawio-diagram-builder\scripts\check_skill_update.py
```

脚本会比较本地 `VERSION` 和 GitHub main 上的最新 `VERSION`。更新检查请使用这个脚本，不要检查某个特定功能字符串，因为 skill 以后还会继续演进。

### 校验 `.drawio` 文件

```powershell
python .\skills\drawio-diagram-builder\scripts\validate_drawio.py .\examples\minimal.drawio
```

默认标记内嵌位图。仅在有意使用图片素材时加 `--allow-raster`。

### 校验参考图复刻过程文档

从参考图开始绘制前：

```powershell
python .\skills\drawio-diagram-builder\scripts\validate_replication_artifacts.py .\workdir
```

最终交付前，在至少完成一次渲染截图复审后：

```powershell
python .\skills\drawio-diagram-builder\scripts\validate_replication_artifacts.py .\workdir --require-screenshot-review
```

严格模式会在 `defect-log.md` 仍然包含截图占位内容时失败。

复刻验证还要求包含需求/语义审查。这是刻意设计的：一张图即使看起来干净，也可能把箭头方向、汇聚/分叉关系或关键关系画错。

参考图迭代复刻时，第一次渲染截图复审后应把 `defect-log.md` 视为追加日志。正确顺序是：生成、预览、截图、追加复审记录，然后再验证；不要在其他进程重写同一工作目录时并发运行验证。

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
