# 数据结构参考 · Geo Flow Map

本文件定义交互式 SVG 地图的数据契约。新主题优先使用 `MAP_SCENES`、`MAP_INTENT`、`GLOSSARY`、`mapScope`、`geoContext`、`nodes`、`regions`、`flows`。模板保留对旧字段 `routes`、`territory`、`land/sea/frontier` 的兼容，但新增内容不要继续扩散旧命名。模板数据必须只保留地图绘制、标签、路线、区域、声明和交互相关信息。

## 1. 顶层常量

```js
const MAP_SCENES = [/* 场景对象 */];
const MAP_INTENT = {/* 可选独立专题 */};
const GLOSSARY = {/* 术语: 解释 */};
```

- `MAP_SCENES`：主地图场景列表，数组顺序即导航顺序。
- `MAP_INTENT`：可选独立地图主题，不参与 `MAP_SCENES` 排序。
- `GLOSSARY`：术语解释词典，正文原样命中后自动高亮；无地图术语时可为空对象。

## 2. 场景对象

```js
{
  id: "domestic-flow",
  name: "国内流向示例",
  time: "2020—2025",
  value: "本场景综合说明。",
  mapScope: "auto",
  geoContext: {
    countries: ["中国"],
    oceans: ["渤海", "黄海", "东海"]
  },
  nodes: [
    { name: "北京", modern: "起点", lon: 116.4, lat: 39.9, type: "land" }
  ],
  regions: [
    {
      id: "coastal-zone",
      label: "东部沿海与近海范围",
      range: [[116,20], [126,20], [126,41], [116,41]],
      labelAt: [121,30]
    }
  ],
  flows: [
    {
      id: "north-south-flow",
      type: "land",
      label: "北方至华东流向",
      points: [[116.4,39.9], [117.2,39.1], [121.5,31.2]],
      direction: "forward"
    }
  ],
  groups: [
    {
      key: "land",
      icon: "⛰",
      title: "陆路流向",
      events: ["一句完整事实。"],
      range: "北京—天津—上海",
      value: "该流向的解释。"
    }
  ],
  refs: [{ t: "资料标题", u: "https://example.com" }]
}
```

## 3. `mapScope`

| 值 | 场景 |
|---|---|
| `world` | 跨国、跨洲、全球网络、国际贸易、外交路线、海外传播，或任一坐标不在中国范围内 |
| `china` | 所有节点、路线和区域均在中国境内 |
| `auto` | 信息不确定，交给模板按 `nodes`、`flows/routes`、`regions/territory` 坐标判断 |

自动判断使用近似中国经纬度盒：经度 `73—136`，纬度 `3—54`。这只用于视野切换，不替代法律或测绘边界。

## 4. `geoContext`

```js
geoContext: {
  countries: ["中国", "韩国", "日本"],
  oceans: ["黄海", "东海", "日本海"]
}
```

- `countries`：国家、地区或政治地理实体。
- `oceans`：海洋、海域、海峡、海湾、河口或重要水域。
- 只要地图出现节点、路线、流向或区域轮廓，就应填写 `geoContext`。

## 5. `nodes`

```js
{ name: "上海", modern: "港口节点", lon: 121.5, lat: 31.2, type: "sea" }
```

| 字段 | 说明 |
|---|---|
| `name` | 地图标签主文本 |
| `modern` | 标签副文本，可写今名、角色、说明 |
| `lon` / `lat` | 真实经纬度 |
| `type` | `land`、`sea`、`frontier` 或自定义语义类型 |

节点必须落在真实坐标上。标签由模板避让，不要把点位说明移到脱离地图的列表里。

## 6. `regions`

```js
{
  id: "region-a",
  label: "区域名称",
  range: [[110,20], [126,20], [126,36], [110,36]],
  labelAt: [118,28]
}
```

- `range` 是多边形顶点，至少 3 个点，模板自动闭合。
- 区域可以覆盖陆地和海域，不要裁切到陆地。
- 区域含义由边界、标签和 `geoContext` 共同表达；颜色只作为视觉辅助。
- 涉及中国疆域时，`regions` 应能表达陆地、岛屿、近海海域与南海相关边线的整体关系，不要把陆地和海域拆成互相割裂的疆域图。

## 7. `flows`

```js
{
  id: "flow-a",
  type: "sea",
  label: "海上航线",
  points: [[121.5,31.2], [103.8,1.3], [79.8,6.9]],
  direction: "forward"
}
```

| 字段 | 说明 |
|---|---|
| `id` | 流向唯一标识 |
| `type` | 语义类型，决定默认颜色和线型 |
| `label` | 图例或 tooltip 文案 |
| `points` | 折线经纬度点，按流向顺序排列 |
| `direction` | `forward`、`backward`、`both`、`none`，默认 `forward` |

路线应尽量经过对应 `nodes`。海线可补航路点绕开陆地；陆线可补中转点贴合真实通道。

## 8. `groups`

`groups` 用于右侧说明卡片，不参与地图投影。

```js
{
  key: "sea",
  icon: "⛵",
  title: "海上流向",
  events: ["事实一句话。"],
  range: "上海—南海—印度洋",
  value: "说明该流向的意义。"
}
```

如果旧数据仍使用 `land`、`sea`、`frontier` 三个分段对象，模板会兼容渲染；新数据优先使用 `groups`。

## 9. `GLOSSARY`

```js
const GLOSSARY = {
  "马六甲海峡": "连接南海与印度洋的关键海上通道。"
};
```

键为正文中原样出现的术语，值为一句解释。模板按长词优先匹配，并自动转义正则字符。

## 10. 风险声明与细节框

风险声明由模板绘制到地图层，涉及疆域、海域、争议或敏感边界时必须保留。声明应说明地图为可视化示意，边界、海域范围和坐标以标准地图、正式测绘成果和适用法律文件为准。

左下角细节框用于补充主图中难以清晰呈现的位置，例如小岛礁、海峡、海域边线或密集边界。细节框不得替代主地图，也不得成为唯一的地理语义来源。

## 11. 固定国名标签

- 中国国名可以加重显示。
- 其他国家名称应使用更小字号、更淡颜色和低饱和描边。
- 标签坐标应按地理区域微调，避免文字明显横跨覆盖其他国家区域。
