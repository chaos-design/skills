# Third-party notices

## live-panel engine (MIT)

`assets/template.html`, `scripts/livepanel.py`, `scripts/render.py`,
`scripts/check_frames.py`, `references/config-schema.md` and
`references/motion-grammar.md` are taken from
[ythx-101/live-panel-skill](https://github.com/ythx-101/live-panel-skill) and
remain under that project's MIT license, reproduced below. The Apache-2.0 license
of this repository covers the material authored for it: `SKILL.md`, `README.md`,
`README.zh-CN.md`, `manifest.json`, `scripts/check_truth.py`, the example config
and the documentation around the vendored files.

Changes made to the vendored files in this repository:

| File | Change |
| --- | --- |
| `assets/template.html` | Added `window.__vars()`, a plain snapshot of machine state at the current `t`, used by `scripts/check_truth.py`. Nothing else. |
| `references/config-schema.md` | Documented `window.__vars()`. |
| `references/motion-grammar.md` | Retargeted the "same grammar on a light infographic" section from the upstream example folder to `examples/skills-pipeline/`, and dropped the reference to an example that is not bundled here. |
| `scripts/check_truth.py` | New, authored here. |

```text
MIT License

Copyright (c) 2026 live-panel contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## The look and the motion grammar

The idea the upstream project documents — a diagram is the monitoring panel of a
running system, so the motion is system state rather than decoration — comes from
an architecture-diagram clip by **[@thedelost](https://x.com/thedelost/status/2105398038026195279)**,
which reached a wider audience through a quote-post by
**[@slashui](https://x.com/slashui/status/2105850132365443528)**. That design
belongs to the original author. This repository bundles neither that clip nor a
recreation of it: `examples/skills-pipeline/` is an original panel about this
repository's own skill pipeline.

If you render output that recreates or re-animates someone else's diagram, put the
original author and link on the video footer (the config's `credit` field) and in
the post.