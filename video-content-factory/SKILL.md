---
name: video-content-factory
description: 一体化口播视频内容工厂 Skill。阶段1：用户提供选题、背景材料或产品信息，需要生成可直接对照录制的口播稿/分镜稿，并按句预绑定特效模式 ID 时触发；阶段2：用户提供已录制视频的路径/地址，需要自动完成 ASR 转录、自动剪辑（去口误/停顿/重复）、按分镜表生成透明 hyperframes 特效轨、FFmpeg 合成、字幕/热词校正/封面元数据并输出 MP4 发布包时触发。触发语包括：做一条口播视频、写口播稿、生成分镜、按句绑特效、自动剪辑、加字幕、合成特效版、输出发布包。
---

# Video Content Factory（一体化口播视频工厂）

> 来源：超级峰个人工作流沉淀。本说明仅保留在 Skill 层，不进入用户产物。

把口播视频从选题/稿件到录制后自动剪辑、特效合成、发布前处理串联成两阶段闭环。两个阶段可独立触发，也可串联使用。

## 触发条件

- **阶段1 · 稿件生产**：用户给选题、背景材料、产品或参考链接，要求生成口播稿/分镜稿/按句绑定特效模式时触发。
- **阶段2 · 自动剪辑与特效合成**：用户发送已录制视频（文件路径、下载地址或项目目录），要求自动剪辑、加字幕、叠加特效、输出发布包时触发。

## 特效库

本 Skill 自带**自成体系、可迭代、可界面管理**的特效库，四件套标准为 `snippet + catalog + registry + preview`：

- 所有特效通过 `assets/effects_library/registry.json` 注册，是后续 Agent 查询和界面渲染的单一事实源。
- `assets/effects_library/catalog.md` 给 Agent 阅读，说明每个特效的适用场景、结构要点、动画要点。
- `assets/effects_library/snippets/` 存放每个特效的自包含 HTML/GSAP 代码范式。
- `assets/effects_library/previews/` 存放特效在管理界面中循环播放的预览页。
- 管理界面 `assets/effects_library/index.html` 读取 `registry.json` 渲染卡片；因浏览器安全策略限制，需先启动本地 HTTP 服务器（`python3 -m http.server 8000`）再用浏览器打开 `http://localhost:8000/index.html`，或运行 `python3 scripts/validate_effects_gallery.py --browser-check` 自动验证。

新增特效必须完成四件套并更新界面；未进 registry 的 snippet 视为未入库。

## 阶段1：稿件生产（选题 → 录制对照稿）

1. **读记忆与品牌配置**：先读 `data/memory.md` 与 `data/brand-profile.yaml`，复用历史偏好与署名边界。
2. **初始化工程**：运行 `python3 scripts/init_project.py <项目目录>`，生成标准工程骨架。
3. **选题与调研**：产出 `topic-brief.md`、`research.md`。
4. **策略锁定**：产出 `BRIEF.md`，锁定 Message、叙事弧、受众、时长、平台画幅等 9 项。
5. **口播稿**：产出 `SCRIPT.md`，短句分行、口语化，约 4 字/秒估算时长。
6. **分镜稿**：产出 `STORYBOARD.md`，按句拆分，每行判定 A-ROLL/B-ROLL，B-ROLL 句在 `特效模式` 列绑定 `registry.json` 中的特效 ID。

阶段1 产物是**可直接对照录制**的稿件，用户录完进入阶段2。

## 阶段2：自动剪辑与特效合成（成片 → 发布包）

1. **解析输入**：读取视频、已有字幕/分镜稿、工程配置文件。
2. **ASR 转录**：按 `data/config.yaml` 中的 provider 顺序调用 ASR，优先使用用户提供的字幕。
3. **自动剪辑**：依据 `references/clip-edit-rules.md` 去口误、停顿、重复；生成 `edit_decisions.json`。
4. **时间轴对齐**：若存在剪辑映射，先把原片时间戳映射到成片时间轴。
5. **特效规划**：按 `STORYBOARD.md` 的 `特效模式` 列生成节拍表；每个绑定模式在 `registry.json` 查记录、读 `catalog.md`、读对应 snippet。
6. **hyperframes 透明轨**：按节拍表搭工程，渲染透明 WebM 特效轨。
7. **FFmpeg 合成**：将原片、特效轨、字幕、封面元数据合成为最终 MP4。
8. **发布包**：运行 `python3 scripts/publish.py <项目目录>`，输出到 `<项目名>_publish_<YYYYMMDD>/`，包含硬字幕 MP4、sidecar SRT/ASS、`edit_decisions.json`、`hidden_speech_review.md`、校验帧。

两个阶段的具体实现细节见 `references/phase-1-script-storyboard.md` 与 `references/phase-2-auto-edit-effects.md`。

## 目录结构

```text
video-content-factory/
├── SKILL.md                              # 本文件：触发条件与核心流程
├── data/
│   ├── brand-profile.yaml                # 品牌配置与署名边界
│   ├── config.yaml                       # 阶段2 全局配置
│   └── memory.md                         # 长期复用型记忆
├── assets/effects_library/
│   ├── registry.json                     # 特效注册表（单一事实源）
│   ├── catalog.md                        # 特效目录（Agent 参考）
│   ├── index.html                        # 特效库管理界面
│   ├── snippets/                         # 特效代码范式
│   └── previews/                         # 界面预览页
├── references/
│   ├── effects-library-spec.md           # 特效库四件套规范
│   ├── phase-1-script-storyboard.md      # 阶段1 实现参考
│   ├── phase-2-auto-edit-effects.md      # 阶段2 实现参考
│   ├── clip-edit-rules.md                # 自动剪辑规则
│   └── publish-spec.md                   # 发布包规范
├── templates/
│   ├── SCRIPT.template.md                # 口播稿模板
│   ├── STORYBOARD.template.md            # 分镜稿模板
│   └── PUBLISH.template.md               # 发布包说明模板
├── scripts/
│   ├── init_project.py                   # 初始化视频工程目录
│   ├── auto_edit.py                      # 自动剪辑，生成 edit_decisions.json
│   ├── render_effects.py                 # 按 STORYBOARD 渲染 hyperframes 透明轨
│   ├── compose_final.py                  # FFmpeg 合成最终成片
│   ├── publish.py                        # 发布前处理，输出标准发布包
│   └── validate_publish.py               # 发布包校验
└── examples/demo-project/                # 示例工程占位
```

## 快速开始

### 初始化一个视频项目

```bash
python3 scripts/init_project.py ./my-topic-video
```

会在 `./my-topic-video/` 下生成：

```text
my-topic-video/
├── topic-brief.md
├── research.md
├── BRIEF.md
├── SCRIPT.md
├── STORYBOARD.md
├── assets/
├── aroll/
└── publish/
```

### 打开特效库管理界面

在 `assets/effects_library/` 目录启动本地 HTTP 服务器：

```bash
cd assets/effects_library
python3 -m http.server 8000
```

然后用浏览器打开 `http://localhost:8000/index.html`，即可按分类浏览、搜索、复制特效 ID 给 Agent。

或一键验证：

```bash
python3 scripts/validate_effects_gallery.py --browser-check
```

## 持久记忆

- 开始新项目前读 `data/memory.md`。
- 每次交付后追加一行记录：日期、视频主题、使用特效、新增特效、踩坑与 workaround。
- 只记结论与模式，不记流水账；超过 20 条时归纳旧记录。
