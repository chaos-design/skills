# Review 代码评审

[English](./README.md)

评审代码变更，给出按严重程度分级、可直接执行的结论。Bug 优先，其次才是结构、性能与行为变化。支持四种输入：未提交的工作区改动、某次提交、分支差异、GitHub Pull Request——当请求里带 "comment" / "评论" 时，评审完成后通过 `gh` 以评论形式发到 PR 上。

## 安装

```bash
npx skills add https://github.com/chaos-design/skills --skill review
```

## 能力

| 输入 | 触发 | 结果 |
| --- | --- | --- |
| 无参数（默认） | "review 未提交的改动" | 评审 `git diff`、`git diff --cached` 与未跟踪的新文件 |
| 提交哈希 | "review 4d97295" | `git show <hash>` |
| 分支 | "review main...HEAD" / "对照 main 评审当前分支" | `git diff <branch>...HEAD` |
| PR 链接 / 编号 | "review https://github.com/org/repo/pull/9，并且comment" | 通过 `gh pr` 获取上下文与 diff；要求时以 PR 评论发出评审 |

请求是自由文本：目标可能和附加指令写在同一句话里，技能会先解析出目标和标志位（如 "comment"），再开始执行。

## 设计

- **只看 diff 不够**。每个被修改的文件都会完整读一遍——孤立看有问题的代码，放在上下文里可能是对的，反之亦然。PR 场景会读 PR 描述里的意图；意图与 diff 不一致本身就是一条发现。
- **不确定就不说**。每条发现都经过调查才报告；不虚构假设性问题；无法验证时会明确说 "不确定 X"，而不是当作确定问题提出。
- **给场景，不给感觉**。每条发现都会写清触发它所需的确切输入、环境或场景，严重程度取决于这些条件。
- **只发普通评论，不做裁决**。PR 评审以一条普通评论发出（`gh pr comment --body-file`），不会提交 approve / request-changes 评审，合并决定留给维护者。

## 用法

直接用自然语言触发，四种模式任选：

```text
review                              # 评审未提交的改动（默认）
review 4d97295                      # 评审指定提交
review main...HEAD                  # 评审相对 main 的分支差异
review https://github.com/org/repo/pull/9            # 评审指定 Pull Request
review https://github.com/org/repo/pull/9，并且comment   # 评审并将结论发布为 PR 评论
```

发现按严重程度排序：

| 标签 | 含义 |
| --- | --- |
| **P0** | 阻断性 bug；在真实场景中必然出问题 |
| **P1** | 疑似 bug 或有风险的行为变化；需要修复或确认 |
| **P2** | 轻微问题：结构、命名、可维护性 |

每条发现引用 `path:line`，说明哪里会坏、需要什么场景、建议怎么改。报告以一行结论收尾：各严重程度的数量，以及是否可以直接合并。

## 示例（One-shot）

```text
review https://github.com/org/repo/pull/42
```

报告形态（示意）：

> **P1** `src/lib/upstream.ts:31` — 创建了 5 秒的 `AbortSignal.timeout`，但没有传给
> `fetch`：上游停滞时不会按 5 秒快速失败，而是挂到平台默认超时。任何经过卡死代理的
> 请求都会触发。修复：`fetch(url, { signal })`。
>
> **P2** `src/lib/upstream.ts:12` — `MAX_RETRIES` 只在本模块内引用，导出是多余的，
> 建议移除。
>
> 结论：0 P0 · 1 P1 · 1 P2 — 修复 P1 后即可合并。

## 依赖

- diff 模式需要 `git`；PR 模式需要已认证的 `gh`（`gh auth status`）。
- 对被评审仓库有读权限；PR 全文件上下文需要 `gh pr checkout`。

## 非目标

- 不负责修复代码，只负责评审；修复单独进行。
- 不 approve、也不阻塞 PR；评论只是建议。
- 不评审 diff 之外的既有代码。

## 许可证

Apache-2.0，见 [`LICENSE`](LICENSE)。
