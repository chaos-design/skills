# Content Slides

[English](./README.md)

Content Slides 用于把已有来源材料转换为自包含的 16:9 HTML 幻灯片。当用户提供 URL、PDF、DOCX 文件、Markdown 文件、纯文本、截图或粘贴笔记，并希望生成 slides、presentation、frontend slide deck 或 HTML deck 时使用。它依赖 [Web Markdown](../web-markdown/README.zh-CN.md) 先把原始输入转换为标准 Markdown，再基于 Markdown 生成最终 deck。

Content Slides 是转换优先的技能：来源内容已经存在，技能负责提取、重组、设计、验证并交付一个可直接运行的 HTML deck 文件。如果需要可复用的 deck-stage 模板和更完整的视觉模板图库，请参考 [Frontend Slides](../frontend-slides/README.zh-CN.md)。

## 安装

可以直接从 Chaos Design Skills 仓库安装该 Skill：

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill content-slides
```

`web-markdown` 是必需依赖，必须与 `content-slides` 同时安装。若只安装 `content-slides`，URL 或复杂来源内容可能无法先转换为标准 Markdown，后续幻灯片生成也可能失败。

当 Agent 发现 `web-markdown` 缺失时，应先询问用户是否安装，展示上面的安装命令，并在依赖可用后再继续执行。

## 功能

- 标准工作流：原始输入 → `web-markdown` 转换为 Markdown → `content-slides` 提取内容简报并生成 HTML deck。
- 在 Agent 平台可访问的前提下，支持 URL、PDF、DOCX 文件、Markdown 文件、纯文本、截图和粘贴笔记。
- 最终只保留 `source.md` 和一个可在浏览器运行的 HTML deck，HTML 按固定 1920×1080 舞台创作。
- 除非用户要求其他语言，默认生成简体中文幻灯片内容。
- 支持键盘、滚轮、触摸和紧凑的底部上一页/下一页控制；默认不生成锚点或跳转点信息，侧边锚点仅在用户明确要求时生成。
- 包含内容提取兜底辅助脚本。

## 截图

<img src="../../screenshots/content-slides/a-practical-guide-to-building-ai-agents.webp" width="520" alt="Content Slides 示例 deck 截图">

截图从 `tests/content-slides/a-practical-guide-to-building-ai-agents/a-practical-guide-to-building-ai-agents.html` 生成。

## 使用方式

当用户希望把已有材料变成幻灯片时调用该技能，例如：

```text
Use content-slides to turn this article URL into a Chinese HTML presentation: https://example.com/report
```

```text
用 content-slides 把这份 PDF 做成高密度阅读型汇报页，保留关键数据和来源。
```

```text
Make a slide deck from the attached screenshot. Treat the screenshot as the source content.
```

来源可以是 URL、PDF、DOCX 文件、Markdown 文件、纯文本、截图、粘贴笔记，或笔记加截图的组合，只要 Agent 平台能够访问这些输入。

### 工作流

1. 判断输入类型：URL、PDF、DOCX 文件、Markdown 文件、纯文本、截图或粘贴笔记。
2. 调用 `web-markdown` 将原始输入标准化为 Markdown，保留标题、来源、正文、图片、链接、表格和代码块。
3. 询问用户生成的 Markdown 是否可接受、是否需要修改；用户确认前不得继续。
4. 从标准 Markdown 中提取干净的内容简报：标题、来源、章节、关键事实、引用、数据和可用图片。
5. 选择密度模式：
   - **低密度 / 演讲型**：适合演讲、keynote 和 pitch。
   - **高密度 / 阅读型**：适合报告、文章和异步阅读材料。
6. 从 `references/style-presets.md` 中选择一个视觉风格，并保持全 deck 一致。
7. 在固定 1920×1080 舞台上生成一个自包含 HTML 文件。
8. 验证单页可见、16:9 缩放、导航、动画、内联图片渲染和溢出情况。
9. 流程结束前删除临时 review、revision、metadata、scratch、截图或规划产物。

### 输出

最终输出只保留标准化 Markdown 来源和生成的 HTML deck。生成的 HTML 文件应基于来源标题命名，不要使用 `index.html` 或 `slides.html` 这类泛名：

```text
source.md
<source-title-slug>.html
```

### 实践注意事项

- 默认 deck 语言是简体中文，除非用户要求其他语言。
- 保留事实、数字、引用和来源归因；不要编造填充内容。
- 内容溢出时拆分为更多幻灯片，不要把字号缩到难以阅读。
- 幻灯片 chrome 应放在缩放舞台之外，交付前验证键盘、滚轮、触摸和底部控制导航。

### 故障排查

- 如果内容处理失败、正文为空、图片/代码块缺失，先确认 `web-markdown` 已正确安装。
- 单独运行 `web-markdown` 检查同一输入是否能生成有效 Markdown；若该步骤失败，应先修复抓取或 Markdown 转换问题。

## 技能文件

```text
skills/content-slides/
├── SKILL.md
├── references/
│   ├── animation-patterns.md
│   ├── html-template.md
│   ├── style-presets.md
│   └── viewport-base.css
└── scripts/
    └── extract_content.py
```

完整工作流与生成规则见 [SKILL.md](SKILL.md)。

## 更新截图

示例 deck 变化时，从 1280×720 的测试夹具重新生成截图，并保存为：

```text
screenshots/content-slides/a-practical-guide-to-building-ai-agents.webp
```
