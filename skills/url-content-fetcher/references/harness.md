# URL Content Fetcher Harness

Convert platform-specific social and article URLs into structured,
reading-ready Markdown. This includes X/Twitter, Weibo, Zhihu, Xiaohongshu,
Bilibili, and WeChat Articles. This prompt is the canonical reference for the
skill; load it before executing any fetch or formatting step.

---

## 1. Workflow

### 1.0 Identify the platform

Use this skill, not `web-markdown`, when the URL belongs to any of
these platforms:

| Platform | Common hosts | Output folder |
| --- | --- | --- |
| X/Twitter | `x.com`, `twitter.com` | `x/` |
| Weibo | `weibo.com`, `m.weibo.cn` | `weibo/` |
| Zhihu | `zhihu.com`, `zhuanlan.zhihu.com` | `zhihu/` |
| Xiaohongshu | `xiaohongshu.com`, `xhslink.com` | `xiaohongshu/` |
| Bilibili | `bilibili.com`, `b23.tv` | `bilibili/` |
| WeChat Articles | `mp.weixin.qq.com` | `wechat/` |

If a supported platform URL needs login, cookie import, or private access,
stop and ask for an accessible source. Do not bypass authentication or invent
missing content.

### 1.1 Resolve the fetcher

For X/Twitter URLs, the skill depends on the upstream
[`x-tweet-fetcher`](https://github.com/ythx-101/x-tweet-fetcher) project.

```bash
# Reuse a local clone if it exists, otherwise clone fresh.
if [ ! -d /tmp/x-tweet-fetcher ]; then
  git clone https://github.com/ythx-101/x-tweet-fetcher.git /tmp/x-tweet-fetcher
fi
```

Treat `/tmp/x-tweet-fetcher` as the canonical install path for X/Twitter. Never
modify files inside that clone; only invoke its scripts.

For Weibo, Zhihu, Xiaohongshu, Bilibili, and WeChat Articles, use the
platform-appropriate accessible fetch path available in the workspace or
browser environment, then apply the same metadata, reconstruction, persistence,
and validation rules below.

### 1.2 Fetch the content

For a regular X/Twitter tweet (including long tweets):

```bash
python3 /tmp/x-tweet-fetcher/scripts/fetch_tweet.py \
  --url "<URL>" --text-only
```

For an X Article (long-form), if Camofox is available locally:

```bash
python3 /tmp/x-tweet-fetcher/scripts/fetch_tweet.py \
  --article "<ARTICLE_ID_OR_URL>" --text-only
```

If Camofox is not running, fall back to the standard `--url` form and accept
the partial preview that the public endpoint exposes.

If the command exits non-zero or the JSON output contains an `error` field,
stop immediately. Print the original error to the user, do not create any
file under the platform output folder, and do not invent a fallback payload.

### 1.3 Capture metadata

From the fetcher output, capture the following fields when present:

| Field             | Source field                              |
|-------------------|--------------------------------------------|
| Source URL        | input URL                                  |
| Author (display)  | `tweet.author`                             |
| Author (handle)   | `@${tweet.screen_name}`                    |
| Date              | `tweet.created_at`, normalized to `YYYY-MM-DD HH:mm:ss` |
| Likes             | `tweet.likes`                              |
| Retweets          | `tweet.retweets`                           |
| Bookmarks         | `tweet.bookmarks`                          |
| Views             | `tweet.views`                              |
| Replies           | `tweet.replies_count`                      |
| Word count        | `tweet.article.word_count` or computed     |
| Article title     | `tweet.article.title` (X Articles only)    |
| Body text         | `tweet.article.full_text` or `tweet.text`  |
| Media URLs        | `tweet.media`, embedded `![](url)` tokens  |

For non-X platforms, capture the nearest equivalent source fields: platform,
source URL, author or account name, publication date, body text, engagement
counts, media URLs, and external links. Leave any missing field blank. Do not
guess values.

### 1.4 Reconstruct Markdown

The X/Twitter `--text-only` mode and other platform extractors may return a
flattened paragraph stream with hard line breaks but no Markdown structure.
Apply the heuristics below in order:

1. **Title detection.**
   - X Articles: use `tweet.article.title` verbatim as the H1.
   - Regular tweets: use the first sentence (up to the first `.`, `!`, `?`,
     `\n`, or 80 characters) as the H1.
2. **Section headings.** Treat short, capitalised lines that act as topical
   transitions (e.g. `Why Current Observability Breaks`,
   `What Should Be Done`) as `##` headings. Promote sub-transitions to
   `###` where the surrounding paragraphs make the hierarchy obvious.
3. **Unordered lists.** Detect parallel bullet-like sentences (e.g. lines
   starting with the same verb, lines separated by `•`, lines that all
   describe a feature). Convert them into `-` lists, preserving order.
4. **Ordered lists.** Detect sequential steps such as
   `Instrument with X. Declare Y. Something fails. Restore.` Re-number them as
   `1.`, `2.`, `3.` Markdown ordered lists.
5. **Inline code.** Wrap obvious tokens in backticks: decorators
   (`@opik.track`), config object paths (`opik.Config.openai_api_key`),
   command-line invocations, identifiers in `snake_case`, `camelCase`, or
   `kebab-case` that look like code, and short literal flags (`--text-only`).
6. **Fenced code blocks.** When a contiguous block of three or more lines is
   clearly source code, terminal output, or JSON, fence it with triple
   backticks and a language tag if inferable.
7. **Quotes.** Lines prefixed with `>` or quoted reply blocks should map to
   Markdown blockquotes (`> …`).
8. **Media.** Preserve every image link in `![alt](url)` form. If the alt
   text is empty, leave it empty rather than fabricating one. Embedded video
   links may stay as plain Markdown links.
9. **External links.** Keep them as `[text](url)`. Do not shorten, expand, or
   redirect URLs.

### 1.5 Compose the file

Layout the final document in this order:

```markdown
# <Title>

> **Source:** <URL>
> **Platform:** <platform>
> **Author:** <Display Name> (`@handle`)
> **Date:** <YYYY-MM-DD HH:mm:ss>
> **Stats:** ❤ <likes> · 🔁 <retweets> · 👁 <views> · 💬 <replies>
> **Word count:** <n>

<Body — reconstructed Markdown>

---

## Media

- ![](https://...jpg)
- ![](https://...png)
```

Omit the `Stats` line entirely when none of the counters are available. Drop
the `Media` section when there are no media URLs.

Before writing the Markdown file, format it for readability. Treat indentation
as tab-based structure with an indent width of 2 spaces for nested Markdown
structures such as lists, blockquotes, and tables, while preserving source
fenced-code indentation exactly as extracted.

### 1.6 Persist to disk

```bash
mkdir -p ./<platform>
```

Slug derivation:

1. Lowercase the chosen title.
2. Replace any run of whitespace with a single hyphen.
3. Strip every character that is not in `[a-z0-9-]`.
4. Collapse repeated hyphens; trim leading/trailing hyphens.
5. Cap the slug at 80 characters; if truncation lands inside a word,
   trim back to the previous hyphen.
6. Append `.md`.

If `<platform>/<slug>.md` already exists, append the smallest integer suffix
`-N` (starting at `2`) that produces an unused filename.

Write the Markdown using UTF-8 with a trailing newline.

### 1.7 Report back

After saving, output a one-line confirmation:

```
Saved <platform>/<slug>.md — <Author> · <word_count> words · <URL>
```

---

## 2. Validation Checklist

Run these checks before declaring success:

- [ ] Metadata header present and free of placeholder text.
- [ ] No `TODO`, `FIXME`, or `<...>` template artefacts remain.
- [ ] Every `1.`, `2.`, `3.` block is monotonic and reset per list.
- [ ] Every fenced code block has matching opening and closing fences.
- [ ] Every image/link URL preserved from the source matches a token in
      the rendered Markdown.
- [ ] File saved under the correct platform folder, slug matches the regex
      `^[a-z0-9-]{1,80}$`.
- [ ] Output language matches the source language.

If any check fails, fix the Markdown and re-run the checklist. Do not deliver
partially valid output.

---

## 3. Error Handling

| Condition                                     | Action |
|-----------------------------------------------|--------|
| `git clone` fails                             | Surface the git error verbatim and stop. |
| `fetch_tweet.py` exits non-zero               | Print stderr; do not write a file. |
| JSON output contains `error`                  | Print the error message; do not write a file. |
| Source text empty after fetch                 | Treat as failure; print a clear notice. |
| Camofox required but not running (X Article)  | Fall back to `--url` form and warn the user. |
| Slug collapses to empty                       | Use the tweet ID as the slug. |

---

## 4. Examples

### 4.1 Tweet → Markdown

Input: `https://x.com/akshay_pachaar/status/2064051835636498924`

Output file: `x/your-agent-harness-should-repair-itself.md`

```markdown
# Your agent harness should repair itself

> **Source:** https://x.com/akshay_pachaar/status/2064051835636498924
> **Author:** Akshay 🚀 (`@akshay_pachaar`)
> **Date:** 2026-01-01 12:00:00
> **Stats:** ❤ 1.2k · 🔁 320 · 👁 84k · 💬 41

## Why Current Observability Breaks

- Logs are append-only and scattered across services.
- Traces stop at the LLM boundary.
- ...

## What Should Be Done

1. Instrument the agent with `@opik.track`.
2. Declare `opik.Config.openai_api_key`.
3. Replay any failed step from the trace store.
```

### 4.2 X Article → Markdown

Input: `https://x.com/i/article/1234567890`

Output file: `x/<article-title-slug>.md`, including section headings,
ordered/unordered lists, and any embedded images preserved.

---

## 5. Non-goals

- This skill does not translate, summarise, or rewrite the source content.
- It does not crawl reply threads or quoted tweets unless the upstream
  fetcher already inlined them.
- It does not push the resulting Markdown to remote storage; that is a
  downstream concern.
