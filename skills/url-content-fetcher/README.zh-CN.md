# URL Content Fetcher

[English](./README.md)

抓取 `x.com` 上的推文和长推文（X Article），并将原始文本重构为高质量、带层级结构的
Markdown 文档，方便归档、知识库或下游内容流水线消费。

## 安装

```bash
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
```

`x-tweet-fetcher` 是处理 X/Twitter URL 的必需依赖。当 Agent 发现该依赖缺失时，应先询问用户是否安装，展示上面的安装命令，并在依赖可用后再继续执行。如果用户拒绝安装，本技能可以在当前任务中临时使用 `/tmp/x-tweet-fetcher` clone，但该回退不会安装可复用的 Skill。

## 能力

- 封装上游
  [`x-tweet-fetcher`](https://github.com/ythx-101/x-tweet-fetcher) CLI，并对其
  `--text-only` 输出做规整后处理。
- 还原 Markdown 语义结构（标题、有序 / 无序列表、行内代码、围栏代码块、引用），
  弥补原始扁平文本丢失的层级信息。
- 完整保留推文中的所有图片、视频和外链。
- 每个 URL 输出一个 Markdown 文件至当前工作目录下的 `x/<slug>.md`，slug 为小写、
  连字符分隔，且具备确定性。
- 文件头自带 metadata（来源 URL、作者、发布日期、点赞 / 转推 / 浏览数、字数），
  使文件具备自描述能力。

## 适用场景

- 将一条有价值的推文或长推文归档进笔记体系。
- 将推文内容接入下游 Markdown 处理链（RSS、静态站点生成器、知识库摄取）。
- 生成与原文语言和语气保持一致的高保真可读副本。

## 示例

```text
用户：抓取 https://x.com/akshay_pachaar/status/2064051835636498924 ，
      并保存为 Markdown。

Agent：Saved x/your-agent-harness-should-repair-itself.md
       — Akshay (@akshay_pachaar) · 1,247 words ·
       https://x.com/akshay_pachaar/status/2064051835636498924
```

最终文件以 metadata 引用块开头，随后是章节标题、重构后的列表，结尾的 `## Media`
段落汇总了从原始推文保留下来的所有图片链接。

## 依赖

- Python 3.7+，用于运行上游 fetcher。
- 处理 X/Twitter URL 时优先使用已安装的 `x-tweet-fetcher` Skill；仅在用户拒绝安装或无法安装时，才临时使用 `/tmp/x-tweet-fetcher` clone。
- 若需要抓取完整的长推文（X Article），需在本地运行
  [Camofox](https://camoufox.com) 浏览器服务并监听 `localhost:9377`；否则 Skill
  会回退至公开预览文本。

## 不做什么

- 不会翻译、摘要或改写推文内容。
- 不会主动抓取上游 fetcher 未携带的额外回复。
- 不会上传文件至远端存储，输出仅落盘到本地。

## 许可证

Apache-2.0，详见 [`LICENSE`](LICENSE)。
