# DATA Schema — `data.json`

Use this schema for the mandatory `data.json` artifact generated after Markdown approval and before
HTML rendering. The final deliverable is still a static, human-editable `index.html` whose article
content is written directly into the HTML DOM. A generated page must not depend on `data.json`,
`window.BILINGUAL_READER_DATA`, or any other JavaScript data object at runtime.

All Chinese descriptions MUST use full-width Chinese punctuation（，。；：「」），English fields use
ASCII punctuation. Every `zh` or `zh*` field under `sections` MUST be translated into natural
Chinese from the corresponding source-backed English content; never copy the English source text
into a `zh` field.

## Mandatory Human Review

After `data.json` is generated, review and correct it before rendering HTML:

- Check every translation field (`zh` and `zh*`) sentence by sentence against its corresponding English source.
- Correct mistranslations, omissions, terminology drift, unnatural professional phrasing, and any wording that could mislead readers.
- Check close-reading summaries in `summary`, `framework`, `quiz`, summary-type `sections`, captions, and glossary explanations against the approved Markdown.
- Delete or rewrite unsupported interpretations, fabricated claims, invented causal links, over-generalized conclusions, and quiz explanations that are not traceable to the source.
- Render final HTML from the reviewed `data.json`; do not regenerate unreviewed data after corrections.

## Boundary Validation

The parser and renderer must fail with a clear error before producing artifacts when input is unsafe or incomplete:

- Markdown must be non-empty, under the parser size limit, free of unsupported control characters, and include exactly one H1 title.
- `Source` metadata must be an `http(s)` URL, and `Fetched` must be a real `YYYY-MM-DD HH:mm:ss` timestamp.
- Fenced code blocks must be closed and stay under the code-block size limit.
- Tables must have at least one row, a consistent column count, no more than 20 columns, no more than 200 rows, and no oversized cells.
- Images in Markdown and `data.json` original rows must use `http(s)` or valid `data:image` sources.
- Reviewed `data.json` must include all top-level contract fields before rendering: `metadata`, `article`, `hero`, `summary`, `framework`, `sections`, `quiz`, `original`, `glossary`, and `footer`.
- Quiz options must be unique, answers must be in bounds, Chinese fields must contain Chinese text, and glossary `autowrap` regex entries must compile and point to existing `glossary.dict` keys.
- CLI usage must choose either Markdown input or `--data-file`; `--data-only` is only valid when generating data from Markdown.

> HTML is allowed inside text fields (e.g. `<b>`, `<br>`). To mark a hover word **inside a
> summary `rows[].en` cell**, wrap it manually:
> `<span class="w" data-k="KEY">word<span class="tip"></span></span>` where `KEY` is a key in
> `glossary.dict`. In the **original** view you don't wrap manually — list regex rules in
> `glossary.autowrap` and the page auto-wraps the first occurrence of each.

```jsonc
{
  "pageTitle": "构建高效 AI Agent",   // <title>
  "headerTitle": "构建高效 <span>AI Agent</span>", // 顶栏，<span> 部分上强调色

  "article": {
    "title": "Building Effective Agents",
    "sourceUrl": "https://www.anthropic.com/engineering/building-effective-agents",
    "fetchedAt": "2026-06-19 12:12:12",
    "tags": ["Agent", "系统设计", "安全护栏"],
    // anchors MUST include first-level document headings only. Never include H2/H3/lower headings.
    "anchors": [
      {"id": "og-1", "label": "Introduction"},
      {"id": "og-2", "label": "Design foundations"}
    ]
  },

  "hero": {
    "title": "Building Effective Agents",
    "meta": "Anthropic Engineering · 2024-12-19",   // 作者/日期/出处
    "en": "One-sentence English hook from the article.",
    "zh": "对应中文导语。"
  },
  // hero MUST NOT include stats, metric cards, counters, or dashboard numbers.
  // Put useful numbers in summary.cards or sections instead.

  "summary": {                                       // “总结”视图：速览
    "lead": "导语，可用 <b>…</b> 强调。",
    "cards": [
      {"icon": "🧠", "title": "核心区分", "body": "卡片正文，可含 <b>。"}
    ],
    // keyPoints 是“结论输出”模块的分析要点，每条都必须基于原文推导。
    // 缺省时渲染器会回退到 cards，确保结论输出始终先给出分析，再给证据。
    "keyPoints": [
      {"label": "核心判断", "text": "从原文推导出的核心结论。"}
    ]
  },

  "framework": {
    "title": "文章逻辑框架",
    "nodes": [
      {"id": "fw-1", "label": "定义问题", "summary": "从原文段落提炼出的短说明。"},
      {"id": "fw-2", "label": "设计原则", "summary": "从下一节原文提炼出的短说明。"}
    ],
    "edges": [
      {"from": "fw-1", "to": "fw-2"}
    ]
  },

  "quiz": [
    {
      "question": "关于“Design foundations”，哪一项最符合原文？",
      "options": ["正确选项", "来自其他章节的干扰项", "无法从该节原文判断此说法成立。"],
      "answer": 0,
      "explain": "依据原文段落：...",
      "wrongReason": "该选项没有对应本节原文，或混淆了其他章节的观点。",
      "sourceAnchor": "Design foundations"
    }
  ],

  "sections": [                                      // “总结”视图正文（也提供右侧锚点）
    // 普通双语章节
    {"num": "1", "toc": "什么是 Agent", "title": "什么是 Agents？",
     "rows": [
       {"en": "English with <span class=\"w\" data-k=\"autonomous\">autonomous<span class=\"tip\"></span></span> word.",
        "zh": "对应中文翻译。"}
     ]},
    // 卡片章节（如工作流模式）
    {"num": "4", "toc": "五种模式", "title": "五种模式", "type": "cards",
     "note": "点击卡片展开详情 👇",
     "cards": [
       {"ico": "🔗", "en": "Prompt Chaining", "zh": "提示链",
        "body": "正文。", "when": "适用场景。"}
     ]},
    // 测验章节
    {"num": "6", "toc": "小测验", "title": "理解小测验", "type": "quiz",
     "quiz": [
       {"q": "题干？", "opts": ["选项A","选项B","选项C","选项D"], "a": 1, "fb": "✅ 解析。"}
     ]},
    // 总结框章节
    {"num": "7", "toc": "核心总结", "title": "核心总结", "type": "summary",
     "box": {
       "heading": "一句话精髓",
       "enQuote": "\"English quote.\"",
       "zhQuote": "\"中文引述。\"",
       "intro": "引导语。",
       "principles": [
         {"big": "🧩", "title": "保持简单 Simplicity",
          "en": "English principle.", "zh": "中文原则。"}
       ]
     }}
  ],

  "original": { // “原文”视图：连续正文按大段落整体对照
    "title": "Building Effective Agents · 原文全文对照",
    "meta": "Anthropic Engineering · 2024-12-19",
    "groups": [
      {"group": "Introduction · 引言",
       "rows": [
         {"type": "image", "src": "data:image/jpeg;base64,...", "alt": "Source image alt text.",
          "caption": "Source caption or short context."},
         {"type": "table", "rows": [["English content", "中文翻译"], ["Agent", "智能体"]],
          "zhRows": [["英文内容", "中文翻译"], ["智能体", "智能体"]]},
         {"en": "Merged source paragraphs EN.", "zh": "合并后的整段中文。"}
       ]}
    ]
  },

  "footer": {
    "sourceUrl": "https://www.anthropic.com/engineering/building-effective-agents",
    "sourceText": "Building Effective Agents"
  },

  "glossary": {
    "groupDesc": { // 可选，覆盖默认分组描述
      "B1": "入门进阶 · 日常常用", "B2": "中级 · 学术与职场高频",
      "C1": "高级 · 专业写作词汇", "C2": "精通 · 地道高阶表达",
      "术语": "文章相关专有名词 · AI / Agent 领域"
    },
    "dict": { // 词典：key 即 data-k 引用名
      "autonomous": {"w": "autonomous", "ipa": "/ɔːˈtɒnəməs/", "pos": "adj.",
        "level": "C1", "def": "自主的，自治的；无需外部控制即可运作的。",
        "eg": "Fully autonomous systems operate independently.",
        "egzh": "完全自主的系统能独立运行。"}
      // level ∈ {B1,B2,C1,C2,术语}; 术语条目 pos 用 "术语"，ipa 可留空
    },
    "autowrap": [ // 原文视图自动高亮规则
      // [正则源, 标志, dict key]；每条仅匹配首次出现处
      ["\\bautonomous\\b", "i", "autonomous"],
      ["Model Context Protocol", "i", "MCP"]
    ]
  }
}
```

## Default completeness rule

For normal article-length source material, generate data for every supported learning structure:

- `summary.lead` and `summary.cards`
- `article.tags` and `article.anchors` for the original tab header and right-side anchor list; anchors include first-level document headings only
- `framework.nodes` and `framework.edges` for the close-reading logic flow
- Regular bilingual `sections[].rows`
- `quiz[]` with article-grounded questions, answer index, wrong-answer reason, and source evidence
- One `sections[]` item with `type: "cards"` when the source supports card-style comparison
- One `sections[]` item with `type: "summary"`
- `original.groups` with consecutive prose paragraphs merged into larger English/Chinese rows, plus meaningful source images when accessible
- `footer.sourceUrl` and `footer.sourceText`
- `glossary.groupDesc`, `glossary.dict`, and `glossary.autowrap`

Render `footer.sourceUrl` and `footer.sourceText` as:

```html
原文：<a href="SOURCE_URL" target="_blank" rel="noopener">《SOURCE_TITLE》</a>
```

If `footer.sourceText` is unavailable, use the URL as the visible text inside `《》`.

Only omit one of these structures when the source is too short, the structure would require
inventing unsupported content, or the user explicitly asks for a compact result. Do not leave a
structure empty just to satisfy the shape; every generated structure must contain useful data that
comes from or directly explains the article.

## Field rules & gotchas

- **`summary.cards[]`**: each card MUST contain exactly `icon`, `title`, and `body`, all strings.
  Do not use `k`/`v`, `ico`, or any extra fields. Use `icon: ""` when no icon is needed.
- **`summary.keyPoints[]`**: each item has `label` and `text`; both must be source-grounded
  analysis, never raw quotes. These feed the close-reading “结论输出” analysis column. When
  `keyPoints` is omitted, the renderer derives analysis from `summary.cards`, so cards must always
  carry real source-grounded conclusions. Close-reading evidence (the source quote/blockquote
  column) is only rendered next to a non-empty analysis column; a block must never show evidence
  without an analysis conclusion.
- **Summary hover words** (`sections[].rows[].en`): wrap manually with the `<span class="w"
  data-k="KEY">…<span class="tip"></span></span>` pattern. `KEY` must exist in `dict`.
- **Section Chinese fields**: every `sections[].rows[].zh`, `sections[].cards[].zh`,
  `sections[].box.zhQuote`, and nested `sections[].box.principles[].zh` value must be Chinese
  translation or Chinese explanation grounded in the source. Do not leave English prose in these
  fields.
- **Hover markup integrity**: manual hover markup must be complete and non-nested. Do not emit
  partial spans, duplicate `.tip` elements, or overlapping `.w` spans. Templates and runtime code
  must never apply string-based autowrap to HTML that already contains `.w`; autowrap should only
  wrap plain text nodes and skip existing `.w`, `script`, and `style` descendants.
- **Word integrity**: hover text and autowrap matches must cover complete source words or phrases.
  Do not highlight stems inside longer words or truncate plurals, hyphenated compounds, or
  possessives. Use explicit lexical boundaries in regexes, such as `\\bagents?\\b`,
  `\\bhigh-impact\\b`, or `\\bhuman intervention\\b`.
- **Inflection matching**: glossary autowrap rules for single English words must match common
  inflected forms in the original text, not only the lemma. Include plural / third-person singular,
  past tense, past participle, and present participle forms where applicable. Irregular words must
  use explicit variants, for example `have` should match `have`, `has`, `had`, and `having`.
  Use the glossary `pos` field to avoid fabricated forms: verbs can expand to tense/participle
  variants, nouns and terms can expand to plural variants, and adjectives/adverbs should not be
  expanded into fake verb forms.
- **Original hover words**: do NOT wrap manually. Add regex rules to `autowrap`; the page wraps
  the first matching cell only, keeping the text clean.
- **Original source images**: when the source includes meaningful accessible images, add them
  directly to `original.groups[].rows` as `{ "type": "image", "src": string, "alt": string,
  "caption": string }` near their source reading-order position. For screenshots, scans, or OCR
  image inputs, put the source image at the top of the original view before paragraph rows. Prefer
  inline `data:` image URLs when bytes are accessible so the final page works from `file://`. Render
  original images centered in a fixed 720x405 bounded image box with `object-fit: contain`; never
  emit unconstrained natural image dimensions. If an image is referenced but inaccessible, state the
  gap instead of inventing a replacement.
- **Escaping in JSON**: backslashes in regex need doubling (`\\b`), quotes inside text need `\"`.
- **CEFR grading**: build the glossary from the article content and learner needs. Aim for a broad
  spread across B1→C2 plus a `术语` (domain terms) group. 60–90 words is a good target for a
  medium article when enough source terms exist; long articles may include up to 120 high-value
  entries. Use fewer for short material and never add unrelated filler words.
- If the compact-result exception applies, optional section types can be omitted entirely. If
  there is no `quiz`/`cards`/`summary` section, those features simply do not render.
