# 调研简报：AI 口播视频自动化生产线

## 核心论点

1. **口播视频制作是高度可工程化的重复劳动**。选题、写稿、分镜、录制、剪辑、特效、字幕、封面，每一步都有明确的输入输出和判定标准，适合用 Skill/Agent 管线串联。
2. **最大的时间黑洞在"录制后"**。根据常见创作者反馈，后期（剪辑、字幕、特效、封面）往往占整条视频工时的 60% 以上。
3. **预绑定特效模式能显著降低返工**。写稿阶段就把 B-Roll/特效节拍定下来，录制时心里有数，剪辑时直接按表渲染，避免"先剪完再想办法加画面"。
4. **透明特效轨是后期叠加的最优解**。不改原视频画面与声音，只在上面叠加一条透明 WebM，FFmpeg 合成即可，渲染与修改成本远低于传统非线性剪辑。

## 可引用数据

| 数据点 | 数值 | 来源/备注 |
| --- | --- | --- |
| 单条口播视频常见后期工时 | 2~4 小时 | 基于创作者社群访谈与 Skill 用户反馈，示例取 3 小时 |
| 目标压缩工时 | ≤20 分钟 | 本 Skill 阶段 2 自动化剪辑 + 特效合成目标 |
| B-Roll 覆盖率建议门槛 | ≥40% | `video-storyboard-pipeline` 质量门禁 |
| 最长 A-Roll 连续段建议 | ≤20 秒 | 避免观众视觉疲劳 |
| 口播语速估算 | ~4 字/秒 | 本 Skill 脚本写作与时长预估基准 |

## 竞品/对标表达方式

- **HeyGen HyperFrames**：官方 `website-to-hyperframes` skill 强调"网页/设计稿 → 透明视频叠加"，但缺少中文口播场景下的写稿-分镜-剪辑闭环。
- **剪映/CapCut**：提供自动字幕、口误识别，但特效/包装仍依赖手动操作，难以批量复用风格。
- **传统 A-Roll/B-Roll 工作流**：Yihui 等独立开发者倡导的"先写稿、再拆镜、最后叠画面"，本 Skill 用 Agent 管线把它自动化。

## 素材候选清单

| 素材用途 | 素材类型 | 获取方式 | 候选文件名 |
| --- | --- | --- | --- |
| 开头钩子「3 小时→20 分钟」反差 | AI 生成图 / 设计稿 | AI 图生成 | `assets/hook-time-comparison.png` |
| 八步骤工具链碎片 | AI 生成图 / 图标组合 | AI 图生成 | `assets/fragmented-tools.png` |
| 分镜表特效模式列高亮 | 屏录 | 录制 STORYBOARD.md | `assets/storyboard-table-scroll.mp4` |
| 自动剪辑口误段消失 | 屏录 | 录制剪辑时间轴 | `assets/edit-decisions-demo.mp4` |
| hyperframes 渲染透明轨 | 屏录 | 录制终端/渲染预览 | `assets/hyperframes-render.mp4` |
| publish/ 目录输出包 | 屏录 | 录制文件管理器 | `assets/publish-folder.png` |
| 算账「180 分钟→20 分钟」 | AI 生成图 / 数据卡 | AI 图生成 | `assets/countup-comparison.png` |
| CTA 关注按钮 | AI 生成图 / 设计稿 | AI 图生成 | `assets/follow-cta.png` |
| 主讲人 A-Roll | 实拍视频 | 口播录制 | `aroll/take-01.mp4` |

## 关键术语与热词

- `video-content-factory`
- `A-Roll` / `B-Roll`
- `hyperframes`
- `特效模式 ID`
- `透明 WebM`
- `FFmpeg 合成`
- `ASR 转录`
- `发布包`
