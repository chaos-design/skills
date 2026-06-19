# Web Markdown

[English](./README.md)

将 URL、PDF、DOCX、Markdown 文件、纯文本、截图/图片和粘贴笔记通过 Microsoft
MarkItDown 转换为高保真 Markdown。对于 URL，当直接转换失败时会保留 Camofox 渲染页面作为兜底路径。

## 安装

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
```

## 能力

- 使用 Microsoft MarkItDown 转换 URL、PDF、DOCX、Markdown、纯文本、截图/图片和粘贴笔记。
- 对 JavaScript 较重或普通 HTTP 抓取不完整的 URL，使用本地 Camofox 渲染作为兜底。
- 从 `article`、`main`、`[role=main]` 或内容特征明显的容器中抽取主体内容。
- 过滤导航、页眉、页脚、侧栏、Cookie 横幅、广告和分享组件等非正文区域。
- 将渲染后的 HTML 转为 Markdown，并保留普通文本、图片、链接、引用、列表、表格、
  行内代码和围栏代码块。
- 表格会作为连续区块输出（行间不留空行）；代码块会去除渲染出的行号槽，并在围栏上
  补充语言标识以便语法高亮。
- 默认每个 URL 输出一个 Markdown 文件到 `web/<slug>.md`；也支持显式指定输出路径。

## 被依赖关系

`web-markdown` 是 `bilingual-reader` 和 `content-slides` 的标准 Markdown 预处理依赖。协作流程为：

```text
原始输入 → web-markdown 转换为标准 Markdown → bilingual-reader / content-slides 处理 Markdown → 输出精读页面或 HTML 幻灯片
```

如果 `bilingual-reader` 或 `content-slides` 出现内容处理失败、正文为空、图片/代码块缺失等问题，请先确认本技能已正确安装，并能为同一输入生成有效 Markdown。

安装下游技能前，请先安装本依赖：

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
```

当 Agent 在使用下游技能时发现 `web-markdown` 缺失，应先询问用户是否安装，展示安装命令，并在依赖可用后再继续执行。

## 路由到 url-content-fetcher

不要用 `web-markdown` 处理平台特定的社交 / 内容 URL，例如 X/Twitter、微博、知乎、小红书、Bilibili 或微信公众号文章。即使用户要求输出 Markdown，这类请求也应改用 `url-content-fetcher`。

如果当前环境没有安装或无法发现 `url-content-fetcher`，应在抓取前停止，并明确告诉用户需要安装依赖 Skill：

```bash
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
```

对于 X/Twitter URL，不要从 `web-markdown` 要求用户安装 `x-tweet-fetcher`；`url-content-fetcher` 内部负责自己的 X/Twitter 依赖发现与安装逻辑。

## 使用

```bash
python3 skills/web-markdown/scripts/web_markdown.py \
  "https://example.com/article"
```

MarkItDown 支持的本地文件：

```bash
python3 skills/web-markdown/scripts/web_markdown.py ./paper.pdf
python3 skills/web-markdown/scripts/web_markdown.py ./brief.docx
python3 skills/web-markdown/scripts/web_markdown.py ./notes.md
python3 skills/web-markdown/scripts/web_markdown.py ./notes.txt
python3 skills/web-markdown/scripts/web_markdown.py ./screenshot.png
```

粘贴笔记：

```bash
python3 skills/web-markdown/scripts/web_markdown.py --text "Meeting notes..."
pbpaste | python3 skills/web-markdown/scripts/web_markdown.py --stdin
```

指定输出文件：

```bash
python3 skills/web-markdown/scripts/web_markdown.py \
  "https://example.com/article" \
  --output web/example-article.md
```

## 依赖

- Python 3.9+。
- Microsoft MarkItDown 及完整文档/图片扩展。

```bash
pip install 'markitdown[all]'
```

- 仅当 URL 需要兜底渲染时，需要本地 Camofox 服务监听 `localhost:9377`。

```bash
curl http://localhost:9377/health
```

## 不做什么

- 不翻译、摘要或改写源页面。
- 不绕过登录、付费墙、私有工作区或访问控制。
- 不替代 X/Twitter 专用归档流程；推文和 X Article 请使用 `url-content-fetcher`。

## 许可证

Apache-2.0，详见 [`LICENSE`](LICENSE)。
