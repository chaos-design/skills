# Task Inject（任务执行中指令注入）

[English](./README.md)

在 Agent 已经开始执行任务的过程中，随时注入修改意见或调整指令——可以从另一个终端、另一个会话或自动化流程发起。运行中的 Agent 在固定检查点读取这些指令，按严重级别作出反应，并对每一次执行留痕确认。

## 安装

```bash
npx skills add https://github.com/chaos-design/skills --skill task-inject
```

## 它做什么

| 阶段 | 谁 | 结果 |
| --- | --- | --- |
| 注入 | 你，任意时刻 | 在 `inbox/` 写入 `NNN-slug.md`：一个动作（`halt`/`redirect`/`revise`/`note`）、可选的 `target` 和指令正文。写入是原子的，Agent 运行中注入也安全。 |
| 检查 | Agent，在固定检查点 | `check` 列出待处理指令，`halt` 永远排最前，停止命令不会被次要意见挡住。 |
| 执行 | Agent | 指令被吸收（或运行停止）后，文件被盖上 `applied:` 时间戳和证据备注，移入 `applied/`，并记入日志。 |
| 审计 | 任何人 | `LOG.md` 以 UTC+8 时间戳记录每一条已执行或已撤回的指令。 |

严重级别决定对当前工作的影响：

| 动作 | 效果 |
| --- | --- |
| `halt` | 在下一个工具调用边界立即停止；不再写文件、不提交。报告现场并等待。 |
| `redirect` | 放弃当前方向；重新拆解范围后才能继续。 |
| `revise` | 完成当前原子步骤后，先吸收该修改，再开始新的工作。 |
| `note` | 建议性意见；在下一个自然检查点吸收，工作顺序不变。 |

## 设计

- **目录即状态。** 待处理指令是 `inbox/` 里的文件，已处理在 `applied/`，日志只追加。没有第二份状态，不会漂移。
- **注入与执行解耦。** 通道就是仓库本身，因此运行中可用、共享仓库的多台机器可用、自动化流程也可用——不依赖套接字或聊天流。
- **门禁在代码里。** `halt` 不写明停止位置（`--note`）就无法被确认；id 永不复用；收件箱未清空时 `check --strict` 以非零码退出，CI 可以据此断言没有指令被遗漏。
- **执行必须留痕。** 指令不会被"默默读过"；`apply` 就是"已收到、已处理"的凭证。
- **与 plan-flow 组合。** `--target <plan NN>` 把指令绑定到某个计划；计划文件本身仍是唯一事实来源。

## 用法

```bash
S=skills/task-inject/scripts/task_inject.py

python3 $S init                                     # 每个仓库一次：创建 .injects/
# --- 你，在 Agent 工作期间 ---
python3 $S inject "先别动数据库" --action halt
python3 $S inject "改做 CLI，不是 Web" --action redirect --sender reviewer
python3 $S inject "标题改成《XX 报告》" --action revise --target 01
python3 $S discard 003 "写错了，撤回"
# --- Agent，在它的检查点 ---
python3 $S check [--json] [--strict]
python3 $S apply 004 --note "已停在迁移前；最后一个完成步骤是 schema 复核"
python3 $S log [--last 5]
```

| 命令 | 用途 |
| --- | --- |
| `init [--dir]` | 创建 `.injects/` 根目录（`inbox/`、`applied/`、`README.md`）；缺省目录取 `TASK_INJECT_ROOT`，否则为 `.injects` |
| `inject <text>` | 追加一条指令（`--action`、`--sender`、`--target`） |
| `check` | 待处理指令，按严重级别排序（`--json`、`--strict`） |
| `apply <id>` | 消费一条指令，必须附证据备注（`--note`） |
| `discard <id> <reason>` | 撤回一条尚未执行的指令（必须写原因） |
| `log [--last N]` | 执行与撤回的审计日志 |

根目录解析顺序：`--root` → `TASK_INJECT_ROOT` 环境变量 → 工作目录向上的最近 `.injects/`。

## Agent 何时检查

五个固定检查点，其余时间不轮询：

1. 接到任务时、开始规划前。
2. 每完成一个子任务后、开始下一步前。
3. 任何难以回退的操作之前（删除、改表结构、升级依赖、push、发布）。
4. 任何 Git 提交、plan-flow 勾选/归档、最终报告之前。
5. 输出最终答案之前。

## 环境要求

- Python 3.9+，仅标准库。
- 仓库中存在 `.injects/` 目录（由 `init` 创建）。

## 非目标

- 不打断已经在执行的工具调用；`halt` 在下一个边界生效。
- 不代替 Git 提交；注入的修改不构成提交授权。
- 不直接编辑 `plans/`；重新拆解范围走 plan-flow。

## 许可

Apache-2.0，见 [`LICENSE`](LICENSE)。
