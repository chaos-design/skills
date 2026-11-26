---
id: 001
title: 本地兜底自动初始化 plans 契约
kind: feature
mode: github
repo: chaos-design/skills
main: 18
children: 19, 20, 21
plan: ""
created: 2026-11-26 22:57:47
updated: 2026-11-26 23:03:28
---

# 本地兜底自动初始化 plans 契约

## 决策

- 模式：github（仓库 chaos-design/skills；chaos-design/skills accepts issues）
- 类型：feature → RFC 主 issue + 子 issue

## 目标

没有 plans/README.md 的仓库在 local 模式下也能直接由 plan-flow 建计划，无需人工补文件

## 拆解

### RFC: 本地兜底自动初始化 plans 契约（主）

- 包含：待补充
- 不包含：待补充

- [ ] 探测目标仓库是否已有 plans/README.md，缺失时按 plan-flow 契约生成最小文件
- [ ] 生成后用 plan_flow.py new 验证计划可创建
- [ ] 补一条 CI 用例覆盖缺失契约的本地兜底

- 风险与回滚：待补充

## 远端映射

- 主 issue：#18（RFC）
- 子 issue：#19, #20, #21
- 本地计划：不适用

## 进度日志

- 2026-11-26 22:57:47 创建路由记录（mode=github, kind=feature）
- 2026-11-26 22:58:10 publish: created RFC #18
- 2026-11-26 22:58:17 publish: created child #19 — 探测目标仓库是否已有 plans/README.md，缺失时按 plan-flow 契约生成最小文件
- 2026-11-26 22:58:25 publish: created child #20 — 生成后用 plan_flow.py new 验证计划可创建
- 2026-11-26 22:58:34 publish: created child #21 — 补一条 CI 用例覆盖缺失契约的本地兜底
- 2026-11-26 22:58:38 publish: linked 3 child issue(s) to #18
- 2026-11-26 23:01:43 publish: linked 3 child issue(s) to #18
- 2026-11-26 23:02:21 publish: linked 3 child issue(s) to #18
- 2026-11-26 23:03:28 publish: linked 3 child issue(s) to #18




