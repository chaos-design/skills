# Geo Flow Map Harness

生成一个**纯原生、单文件、零依赖**的交互式 SVG 地理地图。核心产物是根据用户意图绘制地图：自动选择世界地图或中国地图真实轮廓，标注地点，绘制区域边界、路线、流向箭头、标签、图例和 tooltip，并提供必要的地图交互。

`assets/template.html` 是完整参考实现，可直接打开运行，也是生成新地图的起点。生成新主题时，优先替换声明式地图数据，不重写底图、投影、标签避让、路线动画、tooltip、弹窗和响应式外壳。

---

## 一、生成流程

1. **解析用户意图**
   - 判断地图主题：迁徙、贸易、战争、传播、物流、行政区划、事件地点、区域对比或综合叙事。
   - 提取地理对象：国家/地区、海洋/海域、城市、节点、起点、终点、中转点、区域范围。
   - 判断交互需求：hover/click tooltip、图例筛选、路线动画、地图放大弹窗、分场景切换。

2. **选择底图范围**
   - 跨国、跨洲、国际贸易、外交路线、全球传播、海外节点：`mapScope: "world"`。
   - 所有节点、路线和区域均在中国范围内：`mapScope: "china"`。
   - 信息不足或需要模板自动判断：`mapScope: "auto"`，并提供真实经纬度。

3. **构造地图数据**
   - `MAP_SCENES`：主地图场景数组，左侧导航顺序等于数组顺序。
   - `MAP_INTENT`：可选独立地图主题，用于不参与主序列的专题地图。
   - `GLOSSARY`：术语解释词典，命中正文后自动高亮并弹出 tooltip。
   - 每个场景必须尽量提供 `geoContext`，不要让颜色成为唯一语义来源。
   - 模板数据只保留地图相关内容；删除与地图绘制、标签、路线、区域、声明和交互无关的叙事、人物词条、参考链接或演示数据。

4. **绘制 SVG 地图**
   - 使用真实 SVG 轮廓底图：世界陆地轮廓、中国国界、台湾轮廓、南海断续线、省级轮廓、国家/地区标注、海洋/海域标注。
   - 用真实经纬度 `[lon, lat]` 绘制节点、路线、区域边界。
   - 路线和流向应能体现方向；必要时补充中转点避免线段误穿陆地或海域。
   - 中国疆域涉及陆海整体时，按陆地、岛屿、近海海域与南海相关边线合并绘制，不拆成彼此割裂的疆域图层。
   - 除中国外的国家名称使用小字号、低饱和颜色，并通过坐标微调避免文字横跨覆盖到其他国家区域。
   - 线条保持细、柔和、可辨识；边界与路线不能用粗重高饱和线条压过底图。
   - 对主图难以清晰表达的岛礁、海峡、边线或敏感小范围区域，在左下角增加细节放大框。
   - 涉及疆域、海域、争议或敏感边界时，地图上必须出现风险声明，说明示意图性质并以标准地图和正式文件为准。

5. **交互与校验**
   - 切换场景时清空并重绘地图。
   - tooltip 挂载到 `document.body`，确保浮层不被裁切。
   - 地图可点击放大查看；交互元素必须显式设置 `cursor: pointer`。
   - 交付前格式化生成的 HTML；HTML、SVG、CSS、JavaScript 的嵌套缩进按 tab 语义处理，indent 宽度为 2 个空格。
   - 交付前运行语法、自检和浏览器功能验证。

---

## 二、核心数据骨架

```js
const MAP_SCENES = [
  {
    id: "scene-a",
    name: "地图场景名称",
    time: "时间 / 副标题",
    value: "本场景说明",
    mapScope: "auto", // "world" | "china" | "auto"
    geoContext: {
      countries: ["中国", "哈萨克斯坦"],
      oceans: ["南海", "印度洋"]
    },
    regions: [
      {
        id: "region-a",
        label: "区域边界",
        range: [[110, 20], [126, 20], [126, 36], [110, 36]],
        labelAt: [118, 28]
      }
    ],
    flows: [
      {
        id: "flow-a",
        type: "land",
        label: "陆路流向",
        points: [[116.4, 39.9], [87.6, 43.8], [66.9, 39.6]],
        direction: "forward"
      }
    ],
    nodes: [
      { name: "北京", modern: "起点", lon: 116.4, lat: 39.9, type: "land" }
    ],
    groups: [
      {
        key: "land",
        icon: "⛰",
        title: "陆路流向",
        events: ["一句事实说明。"],
        range: "北京—新疆—中亚",
        value: "说明这条流向的含义。"
      }
    ],
    refs: [{ t: "资料名", u: "https://example.com" }]
  }
];

const MAP_INTENT = {
  name: "独立地图主题",
  subtitle: "不参与主场景排序",
  intro: "专题说明。",
  mapScope: "world",
  geoContext: { countries: ["中国", "希腊"], oceans: ["印度洋", "地中海"] },
  flows: [{ type: "sea", points: [[121.5,31.2], [79.8,6.9], [23.6,37.9]] }],
  nodes: [{ name: "上海", modern: "海上起点", lon: 121.5, lat: 31.2, type: "sea" }]
};

const GLOSSARY = {
  "台湾海峡": "连接东海与南海的重要海峡。"
};
```

> 兼容旧数据时，模板仍可读取 `routes`、`territory`、`land/sea/frontier` 字段；新内容优先使用 `flows`、`regions`、`groups`。

---

## 三、地图规则

- 所有坐标使用真实经纬度 `[lon, lat]`。
- 世界地图和中国地图都必须来自真实 SVG 轮廓。
- 区域边界是多边形轮廓，不是颜色块；区域可以覆盖陆地和海域。
- 不允许把海峡、海湾、近海范围强行裁切到陆地。
- 中国疆域表达需要把陆地与海域整体呈现，不要把陆地和海域拆成互相独立的疆域图。
- 地图必须保留国家/地区概念和海洋/海域概念。
- 标点必须靠真实坐标落位；标签自动避让，不要用左下角列表替代地图标注。
- 国名标签应优先服务地理参照：除中国外，其他国家标签应更小、更淡，位置不得明显跨压无关国家。
- 左下角细节框只用于补充主图难以辨认的边线和小范围位置，不替代主地图。
- 风险声明是地图的一部分，不应只放在正文中。
- 流向线必须有语义类型，默认类型为 `land`、`sea`、`frontier`，也可扩展为 `migration`、`trade`、`conflict` 等。
- 如果用户只给地名，先补齐合理坐标；拿不准则保守标注为近似，并在文案中说明。

---

## 四、编辑方法

模板较大，底图 path 字符串很多。优先整块替换声明式常量：

```python
s = open("OUTPUT.html", encoding="utf-8").read()
assert s.count("const MAP_SCENES = [") == 1
# 定位常量块后整体替换，不逐行改底图 path。
```

默认不要改底图常量、投影函数、避让算法、tooltip、地图弹窗和 bootstrap。除非用户要求新的地图交互，否则只替换数据和少量主题文案。

---

## 五、交付前自检

```python
import re
s = open("OUTPUT.html", encoding="utf-8").read()
css = re.search(r"<style>(.*?)</style>", s, re.S).group(1)
print("CSS braces:", css.count("{"), css.count("}"))
print("U+FFFD:", s.count(chr(0xfffd)))
bodies = re.findall(r"<script>(.*?)</script>", s, re.S)
open("/tmp/_geo_flow_map_check.js", "w", encoding="utf-8").write("\n;\n".join(bodies))
# 再跑: node --check /tmp/_geo_flow_map_check.js
```

功能自检：
- `MAP_SCENES` 非空且 `id` 唯一。
- `mapScope` 与坐标一致；`auto` 能正确推断世界/中国地图。
- `geoContext.countries` 与 `geoContext.oceans` 覆盖地图语义。
- 节点坐标、路线端点、区域边界均在合理经纬度范围内。
- 路线和流向与节点吻合，方向、颜色、图例不互相矛盾。
- 区域轮廓可覆盖海域，不被陆地轮廓裁切。
- hover/click tooltip、地图放大弹窗、导航切换、响应式布局可用。
- 无旧技能名、`TODO`、占位文本或断链路径残留。
