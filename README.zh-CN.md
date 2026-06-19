# Chaos Design Skills

本仓库用于维护 Chaos Design 提供的 Agent Skills：
<https://github.com/chaos-design/skills>。

每个 Skill 都放在 `skills/<name>` 目录下，并以 `SKILL.md` 作为标准入口文件。
Skill 的介绍、安装命令、使用示例和扩展说明位于对应的 Skill 目录中。

# 安装

可以使用 `npx skills add` 直接从本仓库安装指定 Skill：

```bash
npx skills add https://github.com/chaos-design/skills --skill <skill-name>
```

当前可安装的 Skill：

```bash
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
npx skills add https://github.com/chaos-design/skills --skill frontend-slides
npx skills add https://github.com/chaos-design/skills --skill geo-flow-map
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
```

# 依赖关系

`bilingual-reader` 和 `content-slides` 都依赖 `web-markdown` 作为内容标准化入口。使用这两个技能时，协作流程为：

```text
原始输入 → web-markdown 转换为标准 Markdown → bilingual-reader / content-slides 处理 Markdown → 输出最终结果
```

因此安装 `bilingual-reader` 或 `content-slides` 时，必须同时安装 `web-markdown`：

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
```

如果遇到内容抓取、正文缺失、图片/代码块丢失或后续处理失败，请先检查 `web-markdown` 是否已正确安装，并确认它能为同一输入生成有效 Markdown。

`url-content-fetcher` 在处理 X/Twitter URL 时依赖 `x-tweet-fetcher`：

```bash
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
```

当 Agent 发现必需技能依赖缺失时，应先询问用户是否安装，展示准确的 `npx skills add` 命令，并在依赖可用后再继续执行。如果用户拒绝安装，应停止流程，或仅使用文档明确允许的临时回退方案。

# Skill 文档

- [Bilingual Reader](./skills/bilingual-reader/README.zh-CN.md) ([English](./skills/bilingual-reader/README.md))
- [Content Slides](./skills/content-slides/README.zh-CN.md) ([English](./skills/content-slides/README.md))
- [Frontend Slides](./skills/frontend-slides/README.zh-CN.md) ([English](./skills/frontend-slides/README.md))
- [Geo Flow Map](./skills/geo-flow-map/README.zh-CN.md) ([English](./skills/geo-flow-map/README.md))
- [URL Content Fetcher](./skills/url-content-fetcher/README.zh-CN.md) ([English](./skills/url-content-fetcher/README.md))
- [Web Markdown](./skills/web-markdown/README.zh-CN.md) ([English](./skills/web-markdown/README.md))
- [X Tweet Fetcher](./skills/x-tweet-fetcher/README.zh-CN.md) ([English](./skills/x-tweet-fetcher/README.md))

`skills/` 下的每个 Skill 目录都只包含运行该 Skill 所需的文件，并包含一份
与仓库根目录一致的 Apache-2.0 `LICENSE`。

# Skill 结构

每个 Skill 都是一个包含 `SKILL.md` 文件的目录。`SKILL.md` 需要包含 YAML
frontmatter 和具体指令：

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Add your instructions here that Claude will follow when this skill is active]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

必填 frontmatter 字段：

- `name`：Skill 的唯一标识，使用小写字母，并用连字符分隔单词。
- `description`：清晰描述该 Skill 的能力，以及应该在什么场景下使用。
