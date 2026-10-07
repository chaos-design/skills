# Plan Flow 计划流

[English](./README.md)

把你发送的任务落成仓库 `plans/` 目录下的计划文件，在 Agent 执行过程中跟踪进度，并且只在真正完成时归档。遵循的约定是 `plans/README.md` 计划中心：`planing/`、`pending/`、`archive/` 三个状态目录，P0/P1/P2 优先级，以及五项完成标准（DoD）。

## 安装

```bash
npx skills add https://github.com/chaos-design/skills --skill plan-flow
```

## 能力

| 阶段 | 触发 | 结果 |
| --- | --- | --- |
| 规划 | 你发送一个多步骤任务 | 生成 `plans/planing/NN-slug.md`，含目标、范围、任务、DoD、风险与回滚；需要外部决策的任务进入 `pending/` |
| 监控 | 工作推进中，或你询问进度 | 带证据勾选任务；`status` 以 `done/total` 报告任务、DoD 与待决事项 |
| 归档 | 全部工作验证完成 | 移入 `plans/archive/NN-slug.md`；存在未勾选项时拒绝移动 |

## 设计

- **目录即状态**：计划状态就是它所在的文件夹，进度就是文件内的复选框计数。没有索引或状态字段，也就不会不同步。
- **门禁在代码里**：`move` 在存在未勾选项、缺少 DoD 键、残留占位符时拒绝归档；存在未决事项时拒绝离开 `pending`；拒绝重开 `archive` 中的计划。脚本强制的规则，Agent 不会忘。
- **每次勾选都留痕**：以 UTC+8 时间戳写入计划的进度日志，文件本身就是审计记录。
- **不制造第二个真相源**：从不修改 `plans/README.md` 的统计表。

## 用法

```bash
S=skills/plan-flow/scripts/plan_flow.py

python3 $S new "Workspace boundary" --priority P0 \
  --goal "符号链接不能越出工作区" \
  --task "增加 realpath 边界校验" --task "补充边界测试"
python3 $S status
python3 $S show 01
python3 $S tick 01 1 2 --note "12 项边界测试通过"
python3 $S move 01 archive
```

| 命令 | 作用 |
| --- | --- |
| `new <title>` | 创建计划（`--priority`、`--state planing\|pending`、`--goal`、`--task`、`--decision`、`--slug`、`--number`） |
| `status` | 列出所有计划及进度（`--state`、`--json`） |
| `show <plan>` | 查看单个计划的编号复选框 |
| `tick <plan> N...` | 勾选并追加进度日志（`--undo`、`--note`） |
| `move <plan> <state>` | 移到 `planing`、`pending`（需 `--reason`）或 `archive` |

`<plan>` 可以是 `NN` 前缀、slug 片段或文件名。计划目录按 `--root`、`PLAN_FLOW_ROOT`、工作目录向上最近的 `plans/` 顺序解析。

## 依赖

- Python 3.9+，仅标准库。
- 含 `plans/README.md` 的仓库（状态目录按需创建）。

## 非目标

- 不创建 Git 提交；版本基线由维护者处理。
- 不替你决定优先级和范围，只负责记录并强制执行。
- 不重开已归档计划；新工作新建计划。

## 许可证

Apache-2.0，见 [`LICENSE`](LICENSE)。
