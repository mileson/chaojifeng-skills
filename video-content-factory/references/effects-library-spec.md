# 特效库规范

## 四件套标准

每个特效必须同时具备以下四项，缺一视为未入库：

1. **snippet**（`assets/effects_library/snippets/<id>.html`）
   - 自包含的 HTML + CSS + GSAP 动画范式。
   - 文案/素材参数化，顶部注释写明可替换字段。
   - 禁止 `repeat: -1`；持续动画一律使用有限循环（顶部放 `XXX_PLAY` 时长变量）。
2. **catalog**（`assets/effects_library/catalog.md`）
   - 每个条目包含：id、模式名、适用场景、结构要点、动画要点。
   - 按 `category` 分组，保持与 `registry.json` 一致。
3. **registry**（`assets/effects_library/registry.json`）
   - 单一事实源，根节点为 `{ "effects": [...] }`。
   - 字段：id、name、category、desc、anim、params、path、accent、since。
   - 所有 UI、Agent 查询、脚本索引都从此读取。
4. **preview**（`assets/effects_library/previews/<id>.html`）
   - 用于 `index.html` 管理界面中循环播放的独立预览页。
   - 应能在 1920×1080 iframe 中完整展示该特效中段效果。
   - 若 snippet 依赖工程内 DOM，可在 preview 中注入演示 DOM 或覆盖样式。

## 分类约定

- `skeleton`：骨架层（常驻 HUD）
- `container`：容器层（画中画/仪表盘）
- `beat`：节拍层（瞬时 3~8s 内容卡片）
- `transition`：转场
- `util`：工具层（叠加用，非独立节拍）
- `outro`：片尾（不透明拼接段）
- `product`：产品卡片

## 界面管理规范

- 管理界面入口为 `assets/effects_library/index.html`，直接用浏览器打开。
- 界面读取 `registry.json`，按 category 分组展示卡片。
- 每张卡片显示：名称、id、分类、适用场景、动画要点、参数说明。
- 提供搜索（按 id/名称/场景/动画关键词）和「复制给 Agent」按钮。
- 复制格式：`请在视频里使用特效「{id}（{name}）」→ {path}`。
- 新增/修改特效后，必须刷新界面验证预览正常、复制指令正确。

## 入库流程

1. 在真实项目中设计并验证通过（lint → validate → snapshot → 合成 → 目检）。
2. 创建/更新 snippet、catalog 条目、registry 记录、preview。
3. 打开 `index.html` 目检新特效卡片无报错、预览可见。
4. 在 `data/memory.md` 追加一条入库记录。
