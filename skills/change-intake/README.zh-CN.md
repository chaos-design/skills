# Change Intake

[English](./README.md)

把任何新改动——新功能或问题修复、大改动或小改动——落成正确的追踪结构。
先用一次探测判断仓库能否创建 GitHub issue：可以就把改动变成 RFC 或 Task Pool
及子 issue；不可以就退回到 `plan-flow`，在仓库本地的 `plans/` 中规划。

## 安装

```bash
npx skills add https://github.com/chaos-design/skills --skill change-intake
```

## 它能做什么

| 改动 | 模式 | 主追踪器 | 结果 |
| --- | --- | --- | --- |
| 新功能 | `github` | GitHub | `RFC: <标题>` 主 issue + 挂在其下的子 issue |
| 问题修复 | `github` | GitHub | `Task Pool: <问题>` 主 issue + 每个任务一条修复记录 |
| 任意 | `local` | plan-flow | `plans/planing/NN-slug.md`，含目标、任务、完成标准、风险与回滚 |

落地的第一件事是写一条 `changes/NNN-slug.md` 记录：保存路由决策、任务拆解，
以及与真正追踪器的对接信息——GitHub 上是 issue 编号，本地是计划编号——
因此同一个改动不会被规划两次，也不会无人追踪。

## 设计

- **一次决策，一条记录。** `probe` 在创建任何 issue 前先检查 origin 远端、
  `gh` 认证状态和仓库权限，决策理由写入记录。
- **远端状态只关联、不复制。** issue 编号与计划编号回写到记录；issue 正文和
  计划文件仍是各自唯一事实来源。
- **门禁写在代码里。** `check --strict` 在记录未绑定、或绑定与模式冲突时
  非零退出（GitHub 记录绑定 `--plan`、本地记录绑定 issue 编号）。
- **不重复建 RFC。** 工作流先检索已有 issue 再创建主 issue，脚本也拒绝重复
  的本地记录标题。
- **诚实兜底。** 没有 GitHub 远端、没有 `gh`、未认证或没有写权限，就走本地
  规划——绝不编造 issue 链接。

## 用法

```bash
S=skills/change-intake/scripts/change_intake.py

python3 $S init                                   # 每个仓库一次
python3 $S probe --json
python3 $S new "Add SSO login" --kind feature \
  --goal "Users can sign in with SSO" \
  --task "Add callback endpoint" --task "Verify id tokens"
python3 $S publish 001 --dry-run                         # 预览 gh 命令
python3 $S publish 001                                   # 创建 issue 并回写编号
python3 $S bind 001 --plan 07                            # local 模式
python3 $S status
python3 $S check --strict
```

| 命令 | 用途 |
| --- | --- |
| `init` | 每个仓库创建一次 `changes/README.md` |
| `probe` | 输出 `github`/`local`、仓库标识、理由与检查结果（`--json`） |
| `new <title>` | 创建路由记录（`--kind feature\|fix`、`--goal`、`--task`、`--slug`、`--mode`、`--repo`、`--cwd`） |
| `bind <id>` | 回写 `--main` / `--child`（GitHub）或 `--plan`（本地），可带 `--note` |
| `publish <id>` | 直接创建 GitHub issue 并回写真实编号（`--dry-run` 只预览）；可重复执行 |
| `show <id>` | 按编号列出记录中的任务拆解 |
| `status` | 所有已路由改动的表格（`--json`） |
| `check` | 报告不一致的绑定；`--strict` 出错时非零退出 |

根目录解析顺序：`--root`（包含 `changes/` 的仓库根目录）、
`CHANGE_INTAKE_ROOT`、当前目录向上最近的 `changes/README.md`。`new` 的
`--mode` 和 `--repo` 仅供离线演练/测试覆盖。

## GitHub 细节

功能主 issue 用 `rfc` 标签，修复主 issue 用 `task-pool`，所有 issue 都带
`change-intake`。`publish` 会确保标签存在、为每个任务创建子 issue、通过原生
sub-issues GraphQL mutation `addSubIssue` 挂载（失败时退回 REST
`POST /issues/{main}/sub_issues`），并在主 issue 正文的清单中列出。重复执行会
复用已有主 issue、只补建缺失的子 issue。两种方式都不可用时保留清单链接作为
父子结构，并如实说明限制。所有 issue 编号都来自真实的 `gh` 输出。

## 要求

- Python 3.9+，仅标准库。
- GitHub 路径：`gh` CLI 已认证，且对仓库有 `triage`/`push`/`maintain`/`admin`
  权限。
- 本地路径：`plan-flow` 技能，以及仓库中的 `plans/README.md`。

## 不做的事

- 不在本地规划或勾选进度；这些归 plan-flow 负责。
- 不 push、不关闭 issue、不提交；版本基线由维护者决定。

## 许可证

Apache-2.0。详见 [`LICENSE`](LICENSE)。
