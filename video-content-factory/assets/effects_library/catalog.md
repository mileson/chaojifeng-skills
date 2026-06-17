# 特效库目录

给 Agent 参考的已验证 overlay 模式库。每个 snippet 是自包含的「CSS + HTML 结构 + GSAP 动画」范式，**结构与动画可直接套用，文案与素材每次必须按当前视频重写**。

新增规则：新模式必须在真实项目里渲染合成并通过视觉 QA 后，才能入库；入库时同步更新本目录、`registry.json`、`data/memory.md` 与 `previews/`。

## 节拍层 · 内容卡片

| snippet | 模式名 | 适用场景 | 结构要点 | 动画要点 |
| --- | --- | --- | --- | --- |
| `snippets/stamp-hook.html` | 盖章钩子 | 开场 3~5s 制造反差（贵？→ ¥0.2） | 两枚旋转色块印章 + 贯穿删除线 | 砸入 back.out → 删除线 scaleX 划过 → 反转项 elastic 弹出 |
| `snippets/countup-price.html` | 数字滚动印章 | 价格/数据结论强调 | 绿色印章 + tabular-nums 数字 | elastic 弹出 → count-up 滚到终值 → yoyo 脉冲 |
| `snippets/follow-pill.html` | 关注引导 | 片尾关注/订阅引导 | 黑色大药丸按钮 + 白底副标语 | elastic 弹出 + 多次 yoyo 脉冲，整组淡出收尾 |
| `snippets/title-card.html` | 大标题卡片 | 钩子/反问句整屏放大 | 主标题 + 副标题上下居中 | 主标题 elastic 放大入场 → 副标题淡入 → yoyo 呼吸 → 整卡淡出 |
| `snippets/workflow-list.html` | 流程清单 | 工作流步骤逐项强调 | 圆角条形容器 + 左侧圆点 | 每项 back.out 左侧滑入 → 当前项高亮 → 整体淡出 |
