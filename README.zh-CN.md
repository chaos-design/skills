# Chaos Design Skills

[English](./README.md)

Chaos Design Skills 是一组面向真实工作流的 Agent Skills，项目地址为
<https://github.com/chaos-design/skills>。本仓库将内容抓取、双语阅读、幻灯片
生成、前端演示、单页 HTML 简报、地理流向可视化和社交内容提取等能力整理为可安装、
可复用、可验证的技能包。

每个 Skill 都作为独立目录发布在 `skills/<name>` 下，目录内包含运行指令、辅助
脚本、文档、示例和许可证文件，便于 Agent 按需安装和单独使用。

## 功能特性

- 提供可直接安装的内容处理、演示生成和可视化类技能。
- 仓库级文档和每个 Skill 文档均提供英文与中文版本。
- 通过 `web-markdown` 统一内容标准化流程，供下游 Skill 继续处理。
- `html-brief` 把结构化答案渲染成单个离线 HTML 文件，图形几何与主题由代码计算，
  不由模型逐行输出。
- `live-panel` 把「正在运行的系统」渲染成一块一直在运行的架构看板，产出 mp4 或活的网页。
  每一帧都是时间的纯函数，因此无头检查可以实测版面与日志，而不是相信它们。
- 生成结果尽量保持自包含，便于预览、分享和归档。
- 使用 `tests/` 下的约定目录验证各 Skill 产物，避免不同技能的输出相互混杂。
- 仓库和每个可分发 Skill 均采用 Apache-2.0 许可证。

## 可用 Skill

| Skill | 用途 | 文档 |
| --- | --- | --- |
| `bilingual-reader` | 生成包含结构化总结、翻译和词汇表的双语阅读页面。 | [中文](./skills/bilingual-reader/README.zh-CN.md) / [English](./skills/bilingual-reader/README.md) |
| `content-slides` | 将标准化内容转换为自包含的演示幻灯片。 | [中文](./skills/content-slides/README.zh-CN.md) / [English](./skills/content-slides/README.md) |
| `frontend-slides` | 生成面向前端展示场景的幻灯片页面和视觉材料。 | [中文](./skills/frontend-slides/README.zh-CN.md) / [English](./skills/frontend-slides/README.md) |
| `geo-flow-map` | 基于结构化流动数据生成地理流向地图可视化。 | [中文](./skills/geo-flow-map/README.zh-CN.md) / [English](./skills/geo-flow-map/README.md) |
| `html-brief` | 把复杂答案渲染成单文件 HTML 简报：面板栅格、流程图与时序图、对比表、双主题与明暗切换。 | [中文](./skills/html-brief/README.zh-CN.md) / [English](./skills/html-brief/README.md) |
| `live-panel` | 把系统描述变成一直在运行的架构看板，渲染为 H.264 mp4 或活的网页。 | [中文](./skills/live-panel/README.zh-CN.md) / [English](./skills/live-panel/README.md) |
| `plan-flow` | 把任务落成 `plans/` 下的计划文件，跟踪进度，仅在全部任务与完成标准勾选后归档。 | [中文](./skills/plan-flow/README.zh-CN.md) / [English](./skills/plan-flow/README.md) |
| `task-inject` | 向 Agent 正在执行的任务中动态注入修改意见与调整指令；运行中的 Agent 在固定检查点按严重级别（halt / redirect / revise / note）消化指令，并留审计日志。 | [中文](./skills/task-inject/README.zh-CN.md) / [English](./skills/task-inject/README.md) |
| `web-markdown` | 抓取并转换网页内容，输出稳定 Markdown，供其他 Skill 使用。 | [中文](./skills/web-markdown/README.zh-CN.md) / [English](./skills/web-markdown/README.md) |
| `x-tweet-fetcher` | 提取 X/Twitter 内容，为需要社交来源输入的流程提供支持。 | [中文](./skills/x-tweet-fetcher/README.zh-CN.md) / [English](./skills/x-tweet-fetcher/README.md) |

## 安装说明

可以使用 `npx skills add` 直接从本仓库安装指定 Skill：

```bash
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
npx skills add https://github.com/chaos-design/skills --skill frontend-slides
npx skills add https://github.com/chaos-design/skills --skill geo-flow-map
npx skills add https://github.com/chaos-design/skills --skill html-brief
npx skills add https://github.com/chaos-design/skills --skill live-panel
npx skills add https://github.com/chaos-design/skills --skill plan-flow
npx skills add https://github.com/chaos-design/skills --skill task-inject
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
```

如果工作流依赖多个 Skill，请一起安装相关依赖。`bilingual-reader` 和
`content-slides` 都依赖 `web-markdown` 作为内容标准化入口：

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
```

`plan-flow` 与 `task-inject` 组合可以覆盖长任务：plan-flow 让计划文件保持为
唯一事实来源，`task-inject` 负责把执行途中的反馈注入该计划：

```bash
npx skills add https://github.com/chaos-design/skills --skill plan-flow
npx skills add https://github.com/chaos-design/skills --skill task-inject
```

`web-markdown` 在处理 X/Twitter 和已支持中文平台 URL 时，会使用
`x-tweet-fetcher` 作为底层桥接：

```bash
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
npx skills add https://github.com/chaos-design/skills --skill web-markdown
```

`html-brief` 只依赖 Python 3 标准库，可独立安装。它把 `web-markdown` 产出的
Markdown 当作草稿输入，也可以直接使用本地文档或粘贴文本：

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill html-brief
```

## 使用指南

1. 根据任务选择合适的 Skill，并阅读该 Skill 的专属 README。
2. 使用 `npx skills add` 安装 Skill 及其文档声明的依赖。
3. 向 Agent 提供真实输入，例如 URL、Markdown 文件或 Skill 支持的结构化数据。
4. 在对应测试或输出目录中检查生成结果。
5. 按 Skill 文档中的校验步骤验证产物后再正式使用。

内容类工作流通常遵循以下处理路径：

```text
原始输入 -> web-markdown -> 标准 Markdown -> 下游 Skill -> 最终产物
```

如果遇到内容抓取、正文缺失、图片或代码块丢失、下游处理失败等问题，请先确认
`web-markdown` 已正确安装，并能为同一输入生成有效 Markdown。

当 Agent 发现必需 Skill 依赖缺失时，应先询问用户是否安装，展示准确的
`npx skills add` 命令，并在依赖可用后继续执行。如果用户拒绝安装，应停止流程，
或仅使用文档明确允许的临时回退方案。

## 技术架构

```text
.
|-- skills/
|   |-- <skill-name>/
|   |   |-- SKILL.md
|   |   |-- README.md
|   |   |-- README.zh-CN.md
|   |   |-- LICENSE
|   |   `-- scripts/ or references/
|-- screenshots/
|   `-- <skill-name>/
`-- tests/
    |-- <skill-name>/
    `-- index.html
```

- `skills/<skill-name>/SKILL.md` 是 Agent 使用该 Skill 的标准指令入口。
- `skills/<skill-name>/README.md` 和 `README.zh-CN.md` 负责说明安装、用法、
  示例和运行注意事项。
- `scripts/` 与 `references/` 用于存放 Skill 所需的实现辅助脚本和详细流程说明。
- `screenshots/<skill-name>/` 保存对应 Skill 文档中使用的截图。
- `tests/<skill-name>/` 保存对应 Skill 的生成式验证产物。
- `tests/index.html` 在 Skill 生成 HTML 预览时提供统一入口。

## 开发说明

克隆仓库后，可以先查看目标 Skill 的目录结构：

```bash
git clone https://github.com/chaos-design/skills.git
cd skills
find skills/<skill-name> -maxdepth 2 -type f | sort
```

请将改动控制在相关 Skill 目录、截图目录或测试目录内。生成的测试产物必须放在
`tests/<skill-name>/` 下。处理单个问题时，不要重命名、删除或重组无关 Skill 的
文件和产物。

提交拉取请求前，请根据修改内容运行相应检查。对于 Python 辅助脚本，可以运行
语法检查或仓库已配置的测试命令：

```bash
python -m py_compile skills/<skill-name>/scripts/*.py
pytest
```

如果只修改文档，请检查 Markdown 结构、相对链接、截图引用和新增预览入口是否
正确。

## 贡献指南

欢迎提交问题反馈、文档修正、缺陷修复和 Skill 改进。请尽量保持每次贡献聚焦、
可复现、便于审查。

### 提交 Issue

提交 Issue 时请包含：

- 受影响的 Skill 名称。
- 预期行为和实际行为的清晰描述。
- 使用真实、可访问输入的复现步骤。
- 相关日志、生成文件、截图或命令输出。
- 操作系统、运行时版本和已安装 Skill 依赖等环境信息。

如果输入内容是私有、不可访问或占位内容，请提供足够的替代信息，确保维护者能
复现或定位问题。

### 发起 Pull Request

提交 Pull Request 前请确认：

- 已检查是否存在相关 Issue 或 Pull Request。
- 每个 PR 聚焦一个 Skill、一个缺陷或一个文档主题。
- 用户可见行为变化时，同步更新英文和中文文档。
- 输出行为变化时，在 `tests/<skill-name>/` 下新增或刷新验证产物。
- 修改 `tests/index.html` 时只做必要的增量补充，不破坏既有预览入口。
- PR 描述中写明已运行的命令，以及无法运行的检查和原因。

### 代码与文档规范

- 遵循当前 Skill 目录内已有的代码和文档风格。
- 面向前端的文件名使用小写字母和连字符。
- 生成产物应保持确定性和自包含。
- 使用真实可访问输入进行验证，不捏造来源内容、截图或成功测试结果。
- 生成的 `Date` 字段统一使用 UTC+8，格式为 `YYYY-MM-DD HH:mm:ss`。
- 文档应保持实用，说明 Skill 能做什么、何时使用、如何运行、如何验证，以及已知限制。
- 仅在解释不明显逻辑时添加简洁注释。

## 维护者

本仓库由 Chaos Design 维护。项目级问题请通过 GitHub Issue 反馈；Skill 相关问题
请在标题或正文中注明 Skill 名称，方便维护者快速分流处理。

## 许可证

本仓库采用 [Apache License 2.0](./LICENSE) 许可。每个 Skill 目录也包含同一许可证
副本，便于独立分发。
