# Technology Selection

把项目需求转化为明确的技术选型。该 Skill 先检查文件系统状态，判断应该初始化一个
pnpm monorepo 还是向已有 monorepo 中添加产物，然后套用默认技术栈（前端 React +
TypeScript + Vite CSR、Tailwind CSS、shadcn/ui；后端 Node.js + TypeScript；工程化
使用 pnpm 与 Biome），并在任何脚手架动作开始前记录一份强制性的执行计划。

## 安装

```bash
npx skills add https://github.com/chaos-design/skills --skill technology-selection
```

## 功能说明

| 阶段 | 触发条件 | 结果 |
| --- | --- | --- |
| 检查 | 收到项目、应用或库的请求 | 文件系统状态被归类为空目录、非 monorepo 或已有 monorepo |
| 决策 | 状态明确后 | 选择路径 A（初始化 pnpm monorepo）或路径 B（新增前端应用 / 后端应用 / React 库 / TS 库） |
| 配置 | 技术栈确定后 | 套用默认栈：Vite CSR 前端 + Tailwind CSS + shadcn/ui + lucide-react；Node.js + TypeScript 后端；pnpm、Biome 与 GitHub Actions 工程化 |
| 记录 | 写入任何文件之前 | 执行计划保存到 `data/execution_plans/<时间戳>_<动作>_plan.md` |

## 决策规则

- **禁止全栈元框架**：生成的前端应用不得使用 Next.js、Remix、Nuxt、SvelteKit
  等框架，前端统一为标准 Vite CSR 渲染的 React 应用。
- **Monorepo 目录结构固定**：`apps/` 放前端应用，`packages/` 放共享库，
  `server/` 放后端应用。
- **共享库双格式产物**：无论输出 React 组件还是纯 TypeScript 能力，都同时提供
  ESM 与 CJS 格式及 `.d.ts` 类型定义。
- **执行计划为强制项**：在创建第一个文件之前必须先落盘决策记录，便于事后审查
  架构选择。

## 内置参考文档

| 参考文档 | 用途 |
| --- | --- |
| [`references/vite-tailwind.md`](https://github.com/chaos-design/skills/blob/main/skills/technology-selection/references/vite-tailwind.md) | JSX 源码位置追踪的 Babel 插件及 Vite + Tailwind 配置 |
| [`references/better-auth.md`](https://github.com/chaos-design/skills/blob/main/skills/technology-selection/references/better-auth.md) | 前端认证组件 Better Auth 的集成细节 |
| [`references/supabase.md`](https://github.com/chaos-design/skills/blob/main/skills/technology-selection/references/supabase.md) | 默认数据库 Supabase 的配置与使用 |
| [`references/github-actions-git-pages.md`](https://github.com/chaos-design/skills/blob/main/skills/technology-selection/references/github-actions-git-pages.md) | 部署到 GitHub Pages 的 GitHub Actions 工作流 |

## 使用方式

本 Skill 以 Agent 指令形式运行，没有可执行脚本。让 Agent 指向某个目录并请求新建
项目、应用或库，它便会按照 [`SKILL.md`](https://github.com/chaos-design/skills/blob/main/skills/technology-selection/SKILL.md) 中的四个步骤执行。

## 许可证

Apache-2.0，详见 [`LICENSE`](LICENSE)。

