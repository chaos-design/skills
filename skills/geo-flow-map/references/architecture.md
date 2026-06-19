# 架构参考 · Geo Flow Map

Geo Flow Map 是一个单文件、零依赖的 SVG 地理地图生成架构。它把用户意图转成声明式地图数据，再由稳定渲染壳绘制真实轮廓底图、节点、区域、流向和交互。

## 1. 分层模型

```
L1 意图数据      MAP_SCENES / MAP_INTENT / GLOSSARY
L2 文案渲染      导航、标题、说明卡片、参考链接
L3 地图语义      mapScope / geoContext / 坐标校验
L4 SVG 渲染      真实底图、节点、区域、流向、标签避让、细节框、风险声明
L5 交互外壳      场景切换、tooltip、地图弹窗、loading、响应式
```

边界规则：
- L1 只写声明式数据，不写 DOM 逻辑。
- L2 不硬编码主题事实，只消费 L1 数据。
- L3 负责地图范围和地理语义，不用颜色替代国家/海洋概念。
- L4 每次切换场景都清空并全量重绘，避免状态漂移。
- L5 只处理生命周期和交互外壳，默认不改底图数据。

## 2. 数据流

```
用户点击场景
  -> selectScene(id)
  -> 读取 MAP_SCENES 中的场景
  -> 渲染右侧说明
  -> inferMapScope(scene)
  -> applyMapScope(scope)
  -> drawRegions(scene.regions)
  -> drawFlows(scene.flows)
  -> drawNodes(scene.nodes)
  -> drawDetailInset() / drawRiskNotice(scope)
  -> 绑定 tooltip / modal / keyboard 行为
```

独立专题使用 `selectIntentMap()`，流程相同，只是读取 `MAP_INTENT`。

## 3. SVG 地图层

默认 SVG 层级：

1. `mapOcean`：海洋底色。
2. 世界陆地轮廓：中国以外或跨国视野的真实轮廓。
3. 中国轮廓：中国国界、台湾轮廓、南海断续线和省级轮廓。
4. 国家/地区标签与海洋/海域标签。
5. `territoryLayer`：用户意图中的区域轮廓，可覆盖海域。
6. `routesLayer`：流向、路线、节点、标签与引线。
7. `detailInsetLayer`：左下角细节框，用于强化主图难以清晰绘制的小范围边线。
8. `riskNoticeLayer`：地图内风险声明，提示边界、海域和坐标的示意性质。

区域边界和流向线是语义层，不应被陆地 clip-path 裁切。
中国疆域涉及陆海整体表达时，应把陆地、岛屿、近海海域与南海相关边线作为同一地理整体绘制。

## 4. 地图范围推断

`inferMapScope(item)` 的规则：

1. 如果 `mapScope` 是 `world` 或 `china`，显式值优先。
2. 否则收集 `nodes`、`flows.points`、兼容字段 `routes`、`regions.range`、兼容字段 `territory.range`。
3. 全部点位在中国经纬度盒内则使用中国视野，否则使用世界视野。
4. 没有有效坐标时默认世界视野。

`applyMapScope(scope)` 只切换 `viewBox`，不改变真实轮廓数据。

## 5. 交互模型

- 场景导航：点击左侧条目调用 `selectScene`。
- 独立专题：点击专题入口调用 `selectIntentMap`。
- 术语 tooltip：挂载到 `document.body`，支持 hover、focus、移动端点击锁定。
- 地图弹窗：点击地图克隆当前 SVG 到弹窗，允许放大查看和滚动。
- 路线动画：每次重绘时路线使用 stroke-dashoffset 生长动画，动画后恢复线型。
- 标签避让：节点先绘制标点，再按候选方位和引线距离放置标签。

## 6. 扩展点

| 目标 | 改动位置 |
|---|---|
| 新主题地图 | 替换 `MAP_SCENES`、`MAP_INTENT`、`GLOSSARY` |
| 新流向类型 | 增加 type 对应颜色、线型、图例文案 |
| 新区域表达 | 扩展 `regions` 字段，但保持 `[lon, lat]` 顶点 |
| 新细节框 | 调整 `drawDetailInset()` 的框体、边线和注记 |
| 新风险声明 | 调整 `drawRiskNotice(scope)` 的文案与位置 |
| 新交互 | 在 L5 增加事件入口，仍调用 L4 全量重绘 |
| 新底图范围 | 增加真实 SVG path 与对应 `MAP_SCOPES` viewBox |

不要为了一个主题改写底图投影和标签避让。只有当用户明确要求新的地图能力时才扩展 L4/L5。

## 7. 质量约束

- 单文件、零依赖、离线可打开。
- SVG path、脚本和样式全部内联。
- 所有交互元素显式设置 `cursor: pointer`。
- 地图必须能看出国家/地区与海洋/海域语义。
- 除中国外的国家标签必须更小、更淡，且不得明显横跨无关国家区域。
- 涉及敏感边界、海域或疆域表达时，地图内必须显示风险声明。
- 主图难以清晰呈现的小岛礁、海峡或边线必须用左下角细节框补充。
- `mapScope`、坐标、路线、区域和图例必须互相一致。
- 交付前必须通过 `node --check` 和浏览器功能验证。
