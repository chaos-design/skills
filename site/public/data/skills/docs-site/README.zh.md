# 文档站（Docs Site）

将 Markdown 内容与一份小型 JSON 配置，生成为**响应式、多页面、自包含**的静态文档站。无构建步骤、无外部运行时请求——每个页面都是一个可离线打开的 HTML 文件。

布局是一套深色优先、零依赖的响应式文档设计：固定 300px 侧边栏（品牌头部、可滚动的分组导航、吸底的 GitHub / 语言成对控件），内容列在锁定视口的外壳中独立滚动；860px 及以下时，固定顶栏（品牌、GitHub、语言胶囊、三横线菜单键）将侧边栏展开为带独立滚动区和遮罩的全宽抽屉。内置明暗主题切换与真正的 中/EN 文案切换，两者均持久化到 localStorage。

## 特性

- **自动结构**——按配置为每个页面生成一个自包含 HTML 文件。
- **可配置导航**——扁平或分组菜单，带激活态追踪，链接指向真实的同级页面；桌面端为固定侧边栏，移动端为全宽抽屉，展开时自动把当前页滚动到可见区域。
- **格式集成**——文档页用 Markdown（支持可选 front-matter），列表页用 JSON 数据。
- **响应式 + 多页面**——视口锁定的双栏外壳中仅内容区滚动；≤860px 时启用固定顶栏与可变形汉堡键，点击遮罩或 Esc 关闭抽屉，内容宽度流式自适应不溢出。
- **列表页类型**——数据表格，支持客户端排序（任意列，包括提交数量与最后更新时间）、全文搜索、状态筛选与彩色状态徽章，以及实时匹配计数。
- **图表弹层**——` ```mermaid ` 代码块渲染为图形，点击在视口全屏弹层中缩放/平移适配。
- **主题 + 国际化**——持久化的明暗切换（默认深色），以及可就地切换全部界面文案、导航项、列表控件与弹层按钮的中/EN 开关，并同步 `<html lang>`。

## 使用

```bash
python3 skills/docs-site/scripts/docs_site.py generate \
  --config site.json --content ./docs --out ./out
python3 skills/docs-site/scripts/docs_site.py check --out ./out
```

## 配置

```json
{
  "title": "我的文档",
  "tagline": "一句话简介",
  "repo": "github.com/owner/repo",
  "theme": "dark",
  "lang": "zh",
  "i18n": ["zh", "en"],
  "brand_mark": "M",
  "brand_sub": "Documentation",
  "brand_sub_zh": "文档中心",
  "nav": [
    {"slug": "introduction", "label": "Introduction", "label_zh": "简介"},
    {"slug": "guides", "label": "Guides", "label_zh": "指南", "group": "Deep dive",
     "group_zh": "深入阅读",
     "items": [{"slug": "quick-start", "label": "Quick start", "label_zh": "快速开始"}]}
  ],
  "pages": [
    {"slug": "introduction", "type": "doc", "source": "docs/introduction.md"},
    {"slug": "pull-requests", "type": "list",
     "source_data": "pr-data/pull-requests.json",
     "columns": [
       {"key": "number", "label": "#"},
       {"key": "title", "label": "标题", "link": "url"},
       {"key": "commits", "label": "提交数"},
       {"key": "last_updated", "label": "最后更新"},
       {"key": "status", "label": "状态"}
     ],
     "sortable": ["commits", "last_updated"],
     "status_field": "status",
     "filters": ["merged", "closed", "open", "in-review"]}
  ]
}
```

完整字段见 `templates/site-config.sample.json` 与 `references/design.md`。

## 拉取请求列表

`list` 页类型专为渲染 Pull Request 表格设计。请填入**真实数据**（来自 git 历史或 GitHub API），不要手写假数据。`sortable` 中的列可点击排序；`status_field` 列渲染为徽章；`filters` 驱动状态下拉筛选。

```json
[
  {"number": 8, "title": "feat(site): mobile navigation panel",
   "author": "Rain120", "commits": 5, "status": "merged",
   "last_updated": "2026-10-14 14:17:19",
   "url": "https://github.com/chaos-design/skills/pull/8"}
]
```

## 输出

生成的文件位于 `--out` 目录下，每个页面对应一个 `<slug>.html`，自包含（内联 CSS/JS），可离线打开。

## 许可证

Apache-2.0。见 [LICENSE](https://github.com/chaos-design/skills/blob/main/skills/docs-site/LICENSE)。

