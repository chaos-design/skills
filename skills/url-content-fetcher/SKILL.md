---
name: url-content-fetcher
description: >
  Fetches platform-specific social and article URLs, including X/Twitter,
  Weibo, Zhihu, Xiaohongshu, Bilibili, and WeChat Articles, then reconstructs
  the raw content into a high-quality, structured Markdown document with
  metadata, headings, lists, inline code, and preserved media links.
---

# URL Content Fetcher

Use this skill when the user asks to fetch content from X/Twitter, Weibo,
Zhihu, Xiaohongshu, Bilibili, or WeChat Articles and wants the result delivered
as a clean, well-formatted Markdown file. For X/Twitter content, the skill wraps
the upstream `x-tweet-fetcher` CLI and adds a deterministic post-processing
pipeline that recovers semantic structure (headings, ordered/unordered lists,
inline code, media) from the flattened `--text-only` output.

This skill is the preferred route for those platforms even when the request is
phrased as a generic webpage-to-Markdown conversion.

Before running, read `references/harness.md` for the full workflow, formatting rules, file
naming convention, and validation checklist.

## Workflow Overview

Use this checkpointed workflow when the skill output is a publishable article-style artifact. Keep checkpoints explicit and stop at each checkpoint until the user confirms the listed decisions.

```
Phase 0  Intake
         Decide whether this skill applies and identify the initial article type.
  🔽
Phase 1  Source -> Markdown
         Convert URL/PDF/DOCX/MD/text into source.md + extraction-notes.md.
         The main agent runs a 5-item inline checklist; only complex or low-confidence sources escalate to a SubAgent.
  🔽
Phase 2  Editorial Planning
         Create one plan.md with four sections: Brief / Outline / Theme / Assets.
         The main agent self-checks inline; no SubAgent and no review file.
  🔽
Phase 3  Plan Checkpoint
         Checkpoint 1 must stop. Confirm five items one by one:
         article type with standard retention ratio / theme / layout / image mode / cover.
  🔽
Phase 4  First Spread
         Build the hero, first section, and one representative visual block. Create the scaffold here.
         First Spread Reviewer SubAgent writes review/first-spread-review.md.
         Checkpoint 2 must stop. Confirm two items one by one:
         acceptance result / development mode A or B.
  🔽
Phase 5  Full Article Build
         Generate the complete web article. Default to one agent; isolate by section only for very long articles.
         Section Reviewer SubAgent returns pass/fail in the message and does not write a review file.
  🔽
Phase 6  Final Review
         Run Editorial / Visual / Technical final review and write review/final-review.md.
  🔽
Phase 7  Repair
         Apply minimal-slice repairs. Write repair-log.md only when repairs are made.
  🔽
Phase 8  Delivery
         Checkpoint 3 must stop. Confirm the delivery decision one by one.
         Deliver article.html plus a short editorial note.
```


## Dependency Installation

Required dependency: `x-tweet-fetcher` must be installed and available when processing X/Twitter URLs. Install it from this repository with:

```bash
npx skills add https://github.com/chaos-design/skills --skill x-tweet-fetcher
```

If `x-tweet-fetcher` is not installed or cannot be discovered by the agent, pause before fetching X/Twitter content and ask the user whether to install the dependency. After the user agrees, run or ask them to run the install command according to the current agent environment, then retry discovery.

If the user declines installation, you may fall back to cloning the upstream fetcher into `/tmp/x-tweet-fetcher` only for the current run. State that this fallback is temporary and does not install the reusable skill. For non-X platforms, use the platform-specific workflow in `references/harness.md` and only ask about `x-tweet-fetcher` when an X/Twitter URL is actually involved.

## Core Requirements

1. Produce a single Markdown file per source URL under
   `<platform>/<slug>.md` in the current working directory. Use `x/` for
   X/Twitter, `weibo/` for Weibo, `zhihu/` for Zhihu, `xiaohongshu/` for
   Xiaohongshu, `bilibili/` for Bilibili, and `wechat/` for WeChat Articles.
   Do not emit auxiliary files unless the user explicitly asks for them.
2. Always start the Markdown with a metadata header that includes the source
   URL, platform, available author information, publication date, engagement
   counts, and word count. Leave fields blank only when the upstream fetch did
   not return them.
3. Reconstruct semantic Markdown structure from the flattened text output.
   Detect section transitions, parallel bullet phrases, sequential steps, and
   inline code-like tokens, and convert each into the appropriate Markdown
   primitive (`##`, `###`, `-`, `1.`, backticks, fenced code blocks).
4. Preserve every image, video, and external link from the original payload.
   Image links remain in `![](url)` form; outbound links remain as inline
   Markdown links and never get rewritten or shortened.
5. Keep the output in the same primary language as the source content. Do not
   translate, summarise, or paraphrase the original content.
6. Generate the filename by lowercasing the chosen title, collapsing
   whitespace into single hyphens, stripping characters outside
   `[a-z0-9-]`, trimming leading/trailing hyphens, and capping the slug at
   80 characters. Append `.md`.
7. For X/Twitter, prefer the installed `x-tweet-fetcher` skill and Python
   3.7+. Clone the upstream fetcher into `/tmp/x-tweet-fetcher` only as a
   temporary fallback when the user declines or cannot perform skill
   installation.
8. Surface fetch failures faithfully. When the upstream call exits non-zero or
   the JSON response contains an `error` field, stop the pipeline, do not
   write a Markdown file, and report the exact error message back to the user.
9. Validate the final Markdown before delivery: metadata header is present,
   no unreplaced placeholders remain, every detected list is well-formed, and
   every image/link is reachable from the rendered Markdown source.
10. Format the generated Markdown before delivery. Treat indentation as
    tab-based structure with an indent width of 2 spaces for nested Markdown
    structures such as lists, blockquotes, and tables, while preserving source
    fenced-code indentation exactly as extracted.

## Workflow Summary

1. **Identify the platform.** Route X/Twitter, Weibo, Zhihu, Xiaohongshu,
   Bilibili, and WeChat Articles through this skill instead of
   `web-markdown`.
2. **Resolve the fetcher.** For X/Twitter, first use the installed
   `x-tweet-fetcher` skill. If it is unavailable, follow
   [Dependency Installation](#dependency-installation); use a local
   `/tmp/x-tweet-fetcher` clone only as a temporary fallback.
3. **Fetch the content.** For X/Twitter, call the `scripts/fetch_tweet.py`
   script from the installed `x-tweet-fetcher` skill; if using the temporary
   fallback, call
   `python3 /tmp/x-tweet-fetcher/scripts/fetch_tweet.py --url "<URL>" --text-only`
   for tweets. For long-form X Articles, prefer
   `--article <ID>` when Camofox is configured locally; otherwise fall back to
   the standard URL form.
4. **Reconstruct Markdown.** Apply the heuristics in `references/harness.md` to rebuild
   headings, lists, inline code, and media references from the flattened
   text.
5. **Persist.** Ensure the platform folder exists in the current working
   directory, derive the slug from the title, and write the formatted
   Markdown to `<platform>/<slug>.md`.
6. **Report.** Print the saved path and a one-line summary (author, source
   URL, word count) so the caller can confirm completion.

## Examples

- “Fetch <https://x.com/akshay_pachaar/status/2064051835636498924> and save it
  as a Markdown file.” -> `x/your-agent-harness-should-repair-itself.md`
- “Archive this X Article into our notes folder.” -> formatted Markdown with
  metadata header, section headings, and preserved imagery.
- “Convert the linked tweet thread into reading-ready Markdown.” -> ordered
  list reconstructed from sequential steps, inline code wrapped where
  warranted.
- “Save this WeChat Article as Markdown.” -> `wechat/<slug>.md`
- “Convert this Zhihu / Bilibili / Weibo / Xiaohongshu URL.” -> platform folder
  with source-faithful Markdown.

## Guidelines

- ALWAYS prefer high-fidelity structural reconstruction over verbatim
  text dumps; readability is the primary success criterion.
- NEVER drop content from the original source, including emoji, hashtags,
  mentions, image alt text, or trailing call-to-action lines.
- NEVER invent metadata. If a field cannot be derived from the fetch result,
  leave it empty rather than guessing.
- NEVER overwrite an existing file in the platform output folder without first
  appending a numeric suffix (e.g. `slug-2.md`) to avoid clobbering prior
  archives.
- NEVER add commentary, summaries, or editorial annotations to the Markdown
  body. The output represents the source faithfully.
- Keep the workflow idempotent: re-running on the same URL with no upstream
  changes should produce a byte-identical Markdown file.
