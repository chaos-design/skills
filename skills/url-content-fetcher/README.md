# URL Content Fetcher

[中文](./README.zh-CN.md)

Fetches tweets and X Articles from `x.com` and reconstructs the raw text into
high-quality, structured Markdown documents — ready for archival, knowledge
bases, or downstream content pipelines.

## Install

```bash
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
npx skills add https://github.com/chaos-design/skills --skill url-content-fetcher
```

`x-tweet-fetcher` is a required dependency for X/Twitter URLs. When an agent discovers that it is missing, it should ask the user before installing it, show the command above, and continue only after the dependency is available. If the user declines, the skill may use a temporary `/tmp/x-tweet-fetcher` clone for the current run, but that fallback does not install the reusable skill.

## What it does

- Wraps the upstream
  [`x-tweet-fetcher`](https://github.com/ythx-101/x-tweet-fetcher) CLI and
  cleans up its `--text-only` output.
- Reconstructs Markdown structure (headings, ordered / unordered lists,
  inline code, fenced code blocks, blockquotes) that the flat text payload
  loses.
- Preserves every image, video, and external link from the source tweet.
- Emits one Markdown file per source URL into `x/<slug>.md` under the current
  working directory, with a deterministic, lowercase, hyphenated slug.
- Adds a metadata header (source URL, author, date, like / retweet / view
  counters, word count) so the file is self-contained.

## When to use it

- Archiving an interesting tweet thread or X Article into a notes folder.
- Feeding tweet content into a downstream Markdown processor (RSS, static
  site generator, knowledge base ingestion).
- Producing a faithful, reading-ready transcription that keeps the original
  language and tone intact.

## Example

```text
User: Fetch https://x.com/akshay_pachaar/status/2064051835636498924
      and save it as Markdown.

Agent: Saved x/your-agent-harness-should-repair-itself.md
       — Akshay (@akshay_pachaar) · 1,247 words ·
       https://x.com/akshay_pachaar/status/2064051835636498924
```

The resulting file starts with a metadata blockquote, followed by section
headings, reconstructed lists, and a trailing `## Media` section listing every
image preserved from the source.

## Requirements

- Python 3.7+ to run the upstream fetcher.
- The installed `x-tweet-fetcher` skill for X/Twitter URLs, or a temporary
  `/tmp/x-tweet-fetcher` clone only when installation is declined or
  unavailable.
- For full long-form X Article extraction, run a local
  [Camofox](https://camoufox.com) browser service on `localhost:9377`. Without
  it the skill falls back to the public preview text.

## Non-goals

- The skill does **not** translate, summarise, or paraphrase tweets.
- It does **not** auto-crawl reply threads beyond what the fetcher already
  inlines.
- It does **not** push files to remote storage; persistence is local only.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
