# Task Inject — Design Notes

[中文](./design.zh-CN.md)

This document explains how task-inject works internally: the architecture, the
message lifecycle, the checkpoint decision procedure, and the principles behind
each design choice.

## 1. Architecture overview

There are exactly three moving parts: writers who append instructions, the
inbox that holds them, and the running agent that drains them at checkpoints.
The repo itself is the message bus — there is no daemon, socket, or chat
stream to keep alive.

```mermaid
flowchart LR
    subgraph writers["指令写入方（任意数量，任意时刻）"]
        U["用户 / 另一终端"]
        R["评审者 / 另一会话"]
        A["自动化 / CI 机器人"]
    end

    subgraph store[".injects/（仓库内，唯一状态）"]
        INBOX["inbox/<br/>待处理指令<br/>NNN-slug.md"]
        APPLIED["applied/<br/>已消费指令<br/>（applied:/note:/discarded: 元数据）"]
        LOG["LOG.md<br/>只追加审计日志"]
    end

    subgraph agent["运行中的 Agent"]
        CP["五个固定检查点"]
        CHK["check<br/>按严重级别排序"]
        DEC["按动作分派"]
        APP["apply &lt;id&gt; --note"]
    end

    PLAN["plan-flow 计划文件<br/>--target &lt;plan NN&gt;"]

    U -->|"inject --action ..."| INBOX
    R -->|"inject --action ... --sender reviewer"| INBOX
    A -->|"inject --action ... --sender ci"| INBOX

    CP --> CHK --> INBOX
    CHK --> DEC
    DEC -->|"halt / redirect / revise / note"| APP
    APP --> APPLIED
    APP --> LOG
    DEC -.->|"revise/redirect 落到计划"| PLAN
```

Key points:

- **Writers never touch the agent.** They append a file and leave; the agent
  notices at its next checkpoint.
- **The agent never watches a channel.** `check` is a read-only directory
  scan, cheap enough to run five times per task.
- **`applied/` and `LOG.md` are append-mostly.** Nothing is ever deleted;
  history is the audit trail.

## 2. Message lifecycle

A message is created in `inbox/` and leaves it exactly once — by `apply`
(consumed with evidence) or `discard` (withdrawn with a reason). Both endings
keep the file and log the event, so every instruction has a provable outcome.

```mermaid
stateDiagram-v2
    [*] --> Inbox: inject（原子写入, 临时文件+rename）
    Inbox --> Inbox: 继续注入（id 递增, 永不复用）
    Inbox --> Applied: apply --note "证据"<br/>（halt 无 note 则拒绝）
    Inbox --> Applied: discard "原因"<br/>（撤回未消费指令）
    Applied --> [*]: 文件保留, LOG.md 追加一行
```

Guarantees enforced by the script:

| Guarantee | Mechanism |
| --- | --- |
| No half-written message is ever read | `inject` writes to a temp file, then `os.replace` (atomic rename) |
| A halt cannot be consumed silently | `apply` refuses a `halt` without `--note` |
| Ids never repeat | Next id = max id across `inbox/` + `applied/` + 1 |
| An instruction cannot be double-applied | `apply`/`discard` only resolve ids still in `inbox/` |
| No instruction is silently dropped | `check --strict` exits non-zero while `inbox/` is non-empty |

## 3. Checkpoint decision procedure

The agent runs `check` at five fixed checkpoints and nowhere else. Each pending
message is handled strictly in the printed order — severity first, so a stop
order can never hide behind a cosmetic note.

```mermaid
flowchart TD
    S["检查点到达<br/>（接任务前 / 子任务后 / 不可逆操作前 /<br/>提交·归档·报告前 / 最终答案前）"] --> C{"check：收件箱有指令？"}
    C -->|"空"| W["继续原工作"]
    C -->|"有"| H{"最严重的是 halt？"}
    H -->|"是"| HS["在下一个工具调用边界停止<br/>不写文件、不提交、不归档"]
    HS --> HR["报告：最后完成的步骤、<br/>在途修改、剩余工作"]
    HR --> HA["apply &lt;id&gt; --note '停止现场'"]
    HA --> WAIT["等待人工新指令，不自行恢复"]
    H -->|"否"| RD{"有 redirect？"}
    RD -->|"是"| RS["放弃当前方向<br/>复述新目标并重新拆解范围"]
    RS --> RA["apply &lt;id&gt; --note '新方向'"]
    RA --> W2["按新范围继续"]
    RD -->|"否"| RV{"有 revise？"}
    RV -->|"是"| RVS["完成当前原子步骤<br/>先把修改吸收进产物"]
    RVS --> RVA["apply &lt;id&gt; --note '改了什么'"]
    RVA --> W3["再开始新工作"]
    RV -->|"否"| NT["note：下一自然检查点吸收"]
    NT --> NTA["apply &lt;id&gt; --note '如何吸收'"]
    NTA --> W
```

Two rules resolve conflicts when several messages are pending:

1. **Severity beats FIFO.** `check` prints `halt → redirect → revise → note`;
   the agent handles them in that order.
2. **The higher severity wins.** A `note` that contradicts a `halt` is still
   acknowledged, but the run stays stopped.

## 4. Mid-run timeline

The whole point of the skill: the instruction arrives *while the agent is
working*, without interrupting the tool call in flight.

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户（另一终端）
    participant I as inject CLI
    participant B as .injects/inbox/
    participant G as 运行中的 Agent
    participant L as LOG.md

    Note over G: 正在执行子任务（不感知注入）
    U->>I: inject "先别动数据库" --action halt
    I->>B: 原子写入 003-stop-before-the-migration.md
    Note over G: 子任务完成，到达检查点
    G->>B: check（只读扫描）
    B-->>G: 003 [halt]（排最前）
    G->>G: 在下一个工具调用边界停止
    G->>U: 报告停止现场与剩余工作
    G->>L: apply 003 --note "已停在迁移前…"
    Note over G,L: halt 已确认，运行挂起，等待新指令
    U->>I: inject "改为只读迁移" --action revise
    I->>B: 原子写入 004-….md
    G->>B: check（恢复前检查）
    G->>G: 按 revise 语义吸收后继续
    G->>L: apply 004 --note "…"
```

## 5. Design principles

### 5.1 目录即状态

Pending instructions *are* files in `inbox/`; consumed ones *are* files in
`applied/`. There is no index, queue table, or status field that can drift out
of sync with reality. A corrupted run can always be reconstructed by listing
the directory and reading `LOG.md`. This is the same principle plan-flow uses
for plans, which is also why the two compose cleanly.

### 5.2 注入与执行解耦

The channel is the repo, not a socket or chat stream. Consequences:

- Feedback works **mid-run** — the agent does not need to be listening; it
  reads at checkpoints.
- Feedback works **across machines** that share the repo, and from automations
  (CI bots reacting to review comments) with no special wiring.
- There is **nothing to keep alive**: no daemon means no reconnection logic,
  no missed-message replay, no delivery guarantees to implement. The
  filesystem already provides durability and atomic rename.

### 5.3 严重级别前置，而非先进先出

A pure FIFO queue fails in exactly the case this skill exists for: a `halt`
enqueued behind three cosmetic notes gets read third, after the agent has
already spent three checkpoints doing work that should have stopped. Sorting
by severity guarantees the most urgent instruction is always surfaced first.
Within one severity, FIFO applies.

### 5.4 中断边界是工具调用，而非工具内部

`halt` stops "at the next tool-call boundary". Interrupting a tool call
mid-flight would leave partial writes and undefined state — the exact mess the
instruction is trying to prevent. Waiting for the boundary keeps every finished
step consistent and makes "报告现场" (report the scene) truthful: what is done
is really done, what is in flight is enumerable.

### 5.5 消费必须留痕（证据驱动的确认）

Reading a message is not consuming it. `apply` is the only path out of the
inbox, it stamps the file with `applied:` + a free-text evidence note, moves it
to `applied/`, and appends one line to `LOG.md`. This closes three failure
modes: the agent *reads and forgets* (note lost), *claims to have complied*
without doing anything (no evidence), or *consumes twice* (no single exit).
For `halt` the evidence note is mandatory and must state the stopping position,
so a resumed session can be reconstructed from the log alone.

### 5.6 门禁在代码，不在模型记忆

A rule the script does not enforce is a suggestion. The agent cannot "forget"
that a halt needs a note if `apply` refuses to proceed without one, and cannot
reuse ids if allocation is computed from existing files. Everything safety-
critical lives in `task_inject.py`; SKILL.md only tells the agent *when* to
call it and *how to behave* at each severity.

### 5.7 检查点而非轮询

Polling `check` in a tight loop would burn tokens and turn the inbox into a
real-time channel, re-coupling injection with execution. Five checkpoints
bound the latency of any instruction to "the current atomic step" — good
enough for feedback, and the agent's attention stays on the work between
checkpoints.

### 5.8 与现有工作流组合而非替代

- **plan-flow**: `--target <plan NN>` binds an instruction to a plan. The skill
  never edits `plans/` itself; instead, applying a `revise`/`redirect` must be
  reflected in the plan file, keeping the plan the single source of truth.
- **Git**: an injected change never authorizes a commit; commit rules are the
  repository's own.
- **CI**: `check --strict` turns "did we miss any feedback?" into an exit code
  a pipeline can assert on.

## 6. Known limitations

- A `halt` cannot interrupt the tool call currently executing; worst-case
  latency is one atomic step.
- The `.injects/` directory must be shared (committed or synced) for
  cross-machine injection; local-only use works too.
- The id space is 999 messages per inject root; archive the root to reset.
