# Web Markdown

[中文](./README.zh-CN.md)

Converts URLs, PDFs, DOCX files, Markdown files, plain text, screenshots/images,
and pasted notes into faithful Markdown with Microsoft MarkItDown. For URLs, it
keeps Camofox as a rendered-page fallback when direct conversion fails.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
```

## What it does

- Uses Microsoft MarkItDown for URL, PDF, DOCX, Markdown, plain text,
  screenshot/image, and pasted-note conversion.
- Uses local Camofox rendering as a URL fallback for JavaScript-heavy or
  bot-protected pages.
- Extracts the primary content area from `article`, `main`, `[role=main]`, or
  content-like containers.
- Filters common non-content regions such as navigation, headers, footers,
  sidebars, cookie banners, ads, and share widgets.
- Converts rendered HTML into Markdown while preserving normal text, images,
  links, blockquotes, lists, tables, inline code, and fenced code blocks.
- Renders tables as a single contiguous block, and strips rendered line-number
  gutters from code while adding a language hint to each fence for syntax
  highlighting.
- Writes one Markdown file per URL under `web/<slug>.md` unless an explicit
  output path is provided.

## Used by

`web-markdown` is the standard Markdown preprocessing dependency for
`bilingual-reader` and `content-slides`. The collaboration flow is:

```text
raw input -> web-markdown converts it to standard Markdown -> bilingual-reader / content-slides processes the Markdown -> close-reading page or HTML slide deck
```

If `bilingual-reader` or `content-slides` fails to process content, produces an
empty body, or misses images/code blocks, first confirm that this skill is
installed correctly and can produce valid Markdown for the same input.

Install this dependency before either downstream skill:

```bash
npx skills add https://github.com/chaos-design/skills --skill web-markdown
npx skills add https://github.com/chaos-design/skills --skill bilingual-reader
npx skills add https://github.com/chaos-design/skills --skill content-slides
```

When an agent discovers that `web-markdown` is missing while using a
downstream skill, it should ask the user before installing it, show the command,
and continue only after the dependency is available.

## Routing to url-content-fetcher

Do not use `web-markdown` for platform-specific social/content URLs such as
X/Twitter, Weibo, Zhihu, Xiaohongshu, Bilibili, or WeChat Articles. Route those
requests to `url-content-fetcher` instead, even when the user asks for Markdown
output.

If `url-content-fetcher` is not installed or cannot be discovered, stop before
fetching and clearly tell the user how to install the required skill:

```bash
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
```

For X/Twitter URLs, do not install `x-tweet-fetcher` from `web-markdown`.
`url-content-fetcher` owns its own X/Twitter dependency discovery and setup.

## Usage

```bash
python3 skills/web-markdown/scripts/web_markdown.py \
  "https://example.com/article"
```

Local files supported by MarkItDown:

```bash
python3 skills/web-markdown/scripts/web_markdown.py ./paper.pdf
python3 skills/web-markdown/scripts/web_markdown.py ./brief.docx
python3 skills/web-markdown/scripts/web_markdown.py ./notes.md
python3 skills/web-markdown/scripts/web_markdown.py ./notes.txt
python3 skills/web-markdown/scripts/web_markdown.py ./screenshot.png
```

Pasted notes:

```bash
python3 skills/web-markdown/scripts/web_markdown.py --text "Meeting notes..."
pbpaste | python3 skills/web-markdown/scripts/web_markdown.py --stdin
```

With an explicit output file:

```bash
python3 skills/web-markdown/scripts/web_markdown.py \
  "https://example.com/article" \
  --output web/example-article.md
```

## Requirements

- Python 3.9+.
- Microsoft MarkItDown with full document/image extras.

```bash
pip install 'markitdown[all]'
```

- A local Camofox service on `localhost:9377` when URL fallback rendering is
  needed.

```bash
curl http://localhost:9377/health
```

## Non-goals

- It does not translate, summarise, or rewrite the source page.
- It does not bypass authentication, paywalls, private workspaces, or access
  controls.
- It is not the X/Twitter-specific archive path; use `url-content-fetcher` for
  tweets and X Articles.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
