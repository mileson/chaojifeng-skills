# 阶段2：自动剪辑与特效合成

> 本文件描述视频内容工厂阶段2 的完整实现流程：从接收/下载源视频 → ASR 转录 → 自动剪辑 → 时间轴回填 → 生成 hyperframes 工程 → 渲染透明 WebM → FFmpeg 合成 → 发布前处理。所有路径均为相对路径，以项目目录为基准；脚本调用以 `data/config.yaml` 为默认配置来源。

## 1. 目标与输入输出

### 1.1 目标
把用户录制好的口播视频加工成带透明特效轨的发布包，过程中不改原片画面与声音的本质内容，只切除口误/停顿/重复，并按分镜稿叠加 B-Roll 特效。

### 1.2 输入

| 输入项 | 说明 | 来源 |
| --- | --- | --- |
| 源视频 | 本地文件、HTTP(S) URL，或项目目录内 `aroll/` 下已存在的视频 | 用户上传/提供 |
| 项目目录 | 阶段1 生成的目录，至少包含 `SCRIPT.md`、`STORYBOARD.md` | 阶段1 产物 |
| 已有字幕（可选） | SRT / ASS / VTT / JSON，优先级高于 ASR | 用户或外部工具 |
| 修正词表（可选） | `data/corrections.yaml` 或项目级 `corrections.yaml` | 长期记忆 |

### 1.3 输出

输出默认写入项目目录下的 `publish/`（可在 `data/config.yaml` 的 `publish.output_dir` 修改）：

| 文件 | 说明 |
| --- | --- |
| `publish/final.mp4` | 最终成片 |
| `publish/final.srt` | 外挂字幕（当 `include_sidecar_srt=true`） |
| `publish/final.ass` | 样式化外挂字幕（当 `include_sidecar_ass=true`） |
| `publish/edit_decisions.json` | 编辑决策，含原片/成片时间映射、原因、攻击性级别 |
| `publish/hidden_speech_review.md` | 字幕-音频一致性检查结果 |
| `publish/check_first_frame.png` | 首帧校验图 |
| `publish/check_subtitle_frame.png` | 代表性字幕帧校验图 |
| `publish/PUBLISH.md` | 发布说明，诚实披露未验证项 |

## 2. 环境准备与前置检查

阶段2 依赖以下工具链，执行前应做 `which` / `ffprobe -version` / `npx hyperframes --version` 检查：

| 工具 | 用途 | 最低要求 |
| --- | --- | --- |
| `ffmpeg` / `ffprobe` | 媒体信息提取、剪辑、合成、抽帧 | ffmpeg 5.0+ |
| `npx hyperframes` | hyperframes 工程 lint/validate/snapshot/render | 最新版 |
| `python3` | 运行本 Skill 脚本 | 3.10+ |
| `curl` / `wget` | 下载 URL 源视频 | 系统自带 |

若使用火山引擎 ASR，需通过环境变量或 `secrets-vault` 命名空间 `volcengine` 读取 `api_key`，禁止把密钥写入 Skill 文件、日志或命令行。

## 3. 输入解析

### 3.1 识别输入类型

运行入口脚本：

```bash
python3 ../scripts/ingest_input.py ./my-project --video "https://example.com/raw.mp4"
```

`ingest_input.py` 按以下顺序解析 `--video` 参数：

1. 若以 `http://` 或 `https://` 开头，下载到 `./my-project/aroll/source_raw.<ext>`。
2. 若是本地文件路径，校验存在后软链接或复制到 `./my-project/aroll/source_video.<ext>`。
3. 若 `--video` 省略且 `./my-project/aroll/` 内只有一个视频文件，直接使用。
4. 若 `--transcript` 已提供且 `--skip-download` 为真，可跳过视频解析。

### 3.2 读取工程文件

解析成功后，脚本读取：

- `SCRIPT.md`：核对实际口播与稿件差异。
- `STORYBOARD.md`：提取分镜表，后续生成节拍表。
- `data/config.yaml`：决定 ASR provider 顺序、字幕样式、hyperframes 预设等。

### 3.3 下载命令示例

```bash
mkdir -p ./my-project/aroll
curl -L -o ./my-project/aroll/source_raw.mp4 "https://example.com/raw.mp4"
```

错误处理要点：

- URL 返回非 2xx 时停止并打印 HTTP 状态码，不生成空文件。
- 下载中断后保留 `.part` 临时文件，下次可断点续传（`curl -C -`）。
- 下载完成后用 `ffprobe` 验证文件可解析，失败则标记为损坏并退出。

## 4. ASR 转录

### 4.1 优先级

按 `data/config.yaml` 中 `asr.provider_order` 顺序尝试：

1. `volcengine_bigmodel_flash`：大模型极速版，适合长视频。
2. `volcengine_vc`：语音合成同源 ASR，专名词识别较好。
3. `local_existing_transcript`：使用用户提供的本地字幕/转写文件。

若用户显式提供了 `--transcript <文件>`，直接走 `local_existing_transcript` 分支，跳过云端 ASR。

### 4.2 热词导出

云端 ASR 前，先导出热词：

```bash
python3 ../scripts/export_hotwords.py \
  --corrections data/corrections.yaml \
  --output ./my-project/aroll/hotwords.txt
```

`data/corrections.yaml` 格式约定：

```yaml
preferred_terms:
  超级峰: ["超级风", "超级分"]
hotwords:
  - "HyperFrames"
  - "ASR"
  - "口播"
```

### 4.3 调用火山引擎 ASR

```bash
python3 ../scripts/transcribe_volcengine.py \
  --audio ./my-project/aroll/source_audio.wav \
  --provider volcengine_bigmodel_flash \
  --hotwords ./my-project/aroll/hotwords.txt \
  --language zh-CN \
  --output ./my-project/aroll/asr_raw.json
```

### 4.4 标准化输出格式

所有 ASR provider 的输出必须归一化为统一格式，供后续剪辑与字幕使用：

```bash
python3 ../scripts/normalize_asr.py \
  --provider volcengine_bigmodel_flash \
  --input ./my-project/aroll/asr_raw.json \
  --output ./my-project/aroll/transcript.json
```

标准化格式（`transcript.json`）：

```json
{
  "duration": 136.45,
  "language": "zh-CN",
  "segments": [
    {
      "start": 0.32,
      "end": 4.71,
      "text": "很贵？每次调用其实只需要两毛钱。",
      "words": [
        {"start": 0.32, "end": 0.78, "word": "很贵"},
        {"start": 0.90, "end": 1.25, "word": "每次"},
        {"start": 1.25, "end": 1.58, "word": "调用"},
        {"start": 2.10, "end": 2.45, "word": "其实"},
        {"start": 2.45, "end": 2.80, "word": "只"},
        {"start": 2.80, "end": 3.15, "word": "需要"},
        {"start": 3.15, "end": 3.78, "word": "两毛"},
        {"start": 3.78, "end": 4.20, "word": "钱"}
      ]
    }
  ]
}
```

### 4.5 应用修正词表

```bash
python3 ../scripts/apply_corrections.py \
  --transcript ./my-project/aroll/transcript.json \
  --corrections data/corrections.yaml \
  --output ./my-project/aroll/transcript_corrected.json
```

修正规则：

- `preferred_terms`：把同音错别字替换为规范词（如 `超级风` → `超级峰`）。
- 仅修改文本，不动时间戳。
- 修正后输出 `transcript_corrected.json`，原 `transcript.json` 保留备查。

## 5. 自动剪辑

### 5.1 读取剪辑规则

自动剪辑遵循 `references/clip-edit-rules.md` 与 `data/config.yaml` 中 `clip_edit` 参数。核心参数：

| 参数 | 含义 | 默认值 |
| --- | --- | --- |
| `default_aggression` | 剪辑攻击性：`conservative` / `standard` / `aggressive` | `standard` |
| `protect_first_word_guard_ms` | 首词前保留呼吸量 | 120 ms |
| `protect_last_word_guard_ms` | 尾词后保留呼吸量 | 180 ms |
| `max_silence_to_cut_ms` | 超过该时长的无语音静音段/空白段才切除 | 300 ms |

### 5.2 攻击性级别

| 级别 | 行为 |
| --- | --- |
| `conservative` | 只切除长静音、完全重复的整句。 |
| `standard` | 默认。按 `max_silence_to_cut_ms=300ms` 切除 >0.3s 的空白/静音；切除明显口癖、重复过渡句、不完整起句；保留自然语气词。 |
| `aggressive` | 与 standard 共用 300 ms 静音阈值，进一步压缩停顿、删除更多填充词，适合短视频快节奏；需人工复核。 |

用户可通过 `--aggression` 覆盖默认级别：

```bash
python3 ../scripts/build_edit_decisions.py \
  --transcript ./my-project/aroll/transcript_corrected.json \
  --aggression standard \
  --config ../data/config.yaml \
  --output ./my-project/aroll/edit_decisions.json
```

### 5.3 编辑决策文件格式

`edit_decisions.json`：

```json
{
  "source_duration": 198.50,
  "output_duration": 136.45,
  "aggression": "standard",
  "keep_segments": [
    {"source_start": 2.30, "source_end": 45.60, "output_start": 0.00, "output_end": 43.30, "reason": "保留"},
    {"source_start": 52.10, "source_end": 198.50, "output_start": 43.30, "output_end": 136.45, "reason": "保留"}
  ],
  "cut_ranges": [
    {"source_start": 0.00, "source_end": 2.30, "reason": "开头垃圾帧/未开始说话"},
    {"source_start": 45.60, "source_end": 52.10, "reason": "口误重录：删前保后"}
  ],
  "word_cut_ranges": [
    {"source_start": 67.20, "source_end": 68.95, "reason": "填充词'那个'连带呼吸间隙"}
  ]
}
```

### 5.4 剪辑原则

- **删前保后**：说话人重起一句时，保留更完整的后一版本，删除前一不完整版本或重复尾部。
- **边界保护**：不要在 ASR 词边界精确切断，保留 `protect_first_word_guard_ms` / `protect_last_word_guard_ms` 呼吸量。
- **语义复核**：对涉及内容意思的切除生成 `review_draft.md`，经用户确认后再渲染。
- **只删不改**：不为了“润色”把口播改写成另一句话。

### 5.5 物理剪辑

基于 `edit_decisions.json` 生成静音片段或拼接命令。推荐做法：

```bash
ffmpeg -i ./my-project/aroll/source_video.mp4 \
  -vf "select='between(t,2.30,45.60)+between(t,52.10,198.50)',setpts=N/FRAME_RATE/TB" \
  -af "aselect='between(t,2.30,45.60)+between(t,52.10,198.50)',asetpts=N/SR/TB" \
  -c:v libx264 -crf 18 -preset medium \
  ./my-project/aroll/cut_video.mp4
```

更精确的做法是按 `keep_segments` 生成 concat 文件：

```bash
# segments.txt
file 'source_video.mp4'
inpoint 2.30
outpoint 45.60
file 'source_video.mp4'
inpoint 52.10
outpoint 198.50
```

```bash
ffmpeg -f concat -safe 0 -i ./my-project/aroll/segments.txt \
  -c copy ./my-project/aroll/cut_video.mp4
```

## 6. 时间轴对齐

### 6.1 为什么必须对齐

ASR 时间戳基于**原片**；如果视频经过剪辑，节拍表必须按**成片**时间设计，否则特效会全体错位。

### 6.2 生成时间映射表

```bash
python3 ../scripts/map_timeline.py \
  --decisions ./my-project/aroll/edit_decisions.json \
  --transcript ./my-project/aroll/transcript_corrected.json \
  --output ./my-project/aroll/timeline_map.json
```

输出示例：

```json
{
  "output_duration": 136.45,
  "segments": [
    {
      "output_start": 0.00,
      "output_end": 43.30,
      "source_start": 2.30,
      "source_end": 45.60,
      "text": "很贵？每次调用其实只需要两毛钱..."
    },
    {
      "output_start": 43.30,
      "output_end": 136.45,
      "source_start": 52.10,
      "source_end": 198.50,
      "text": "..."
    }
  ]
}
```

### 6.3 回填 STORYBOARD.md

把每个分镜行的 `真实时间戳` 列更新为成片时间。脚本会按 `台词` 与 `transcript_corrected.json` 中的文本做模糊匹配：

```bash
python3 ../scripts/fill_storyboard_time.py \
  --storyboard ./my-project/STORYBOARD.md \
  --timeline ./my-project/aroll/timeline_map.json \
  --output ./my-project/STORYBOARD.md
```

若某句台词无法匹配（例如录制时漏念、改词），该行 `真实时间戳` 留空，并在 `PUBLISH.md` 的“未验证部分”披露。

## 7. 特效规划：从分镜表到节拍表

### 7.0 特效与字幕绑定总则（硬规范）

特效不是画面装饰，而是对口播关键信息的可视化翻译。所有 B-Roll 特效必须同时满足以下三条约束：

1. **密度约束**：成片每连续 10~15 秒内必须出现至少一个 B-Roll 特效；超过 15 秒无特效的 A-Roll 段落必须在分镜阶段补特效或合并到相邻特效段落。
2. **字幕绑定约束**：每个 B-Roll 行的 `真实时间戳` 必须落在其对应字幕事件的时间范围内，或与其起始点对齐（偏差 ≤ 0.3s）。特效的 `data-start` 不得早于字幕事件开始，退场不得晚于字幕事件结束后 0.5s。
3. **语义绑定约束**：`特效模式` 必须直接解释该句台词中的数字、对比、结论或行动号召；禁止在无关句子上硬加特效。

违反以上任意一条，`build_beat_sheet.py` 必须告警；若 B-Roll 覆盖率因此低于 40%，禁止进入渲染阶段，除非用户显式 `--skip-coverage-check`。

### 7.1 读取分镜稿

`scripts/build_beat_sheet.py` 读取 `STORYBOARD.md` 的表格，只处理 `类别=B-ROLL` 且 `特效模式` 列非空的行。

### 7.2 校验特效 ID

每个 `特效模式` 必须在 `assets/effects_library/registry.json` 中存在。校验失败时：

- 打印错误行号、镜号、台词、未识别的特效 ID。
- 建议用户在 `assets/effects_library/index.html` 中搜索可用 ID。
- 不生成 beat sheet，直到所有 ID 合法或标为 `NEW:` 占位。

### 7.3 生成节拍表

```bash
python3 ../scripts/build_beat_sheet.py \
  --storyboard ./my-project/STORYBOARD.md \
  --registry ../assets/effects_library/registry.json \
  --timeline ./my-project/aroll/timeline_map.json \
  --output ./my-project/overlay/beat_sheet.json
```

`beat_sheet.json` 示例：

```json
{
  "composition_duration": 136.45,
  "resolution": [1920, 1080],
  "beats": [
    {
      "id": "b1",
      "start": 0.30,
      "duration": 4.40,
      "mode": "stamp-hook",
      "text": "很贵？",
      "params": {"stamp": "很贵？", "answer": "¥0.2 / 次"},
      "track_index": 0
    },
    {
      "id": "b2",
      "start": 8.20,
      "duration": 5.30,
      "mode": "countup-price",
      "text": "每次调用其实只需要两毛钱",
      "params": {"value": 0.2, "unit": "元/次"},
      "track_index": 0
    }
  ]
}
```

### 7.4 读取特效范式

对每个 beat：

1. 在 `registry.json` 查 `id`，获取 `path`。
2. 读 `assets/effects_library/catalog.md` 对应条目，确认适用场景与动画要点。
3. 读 `assets/effects_library/<path>`（snippet），复制到 `overlay/snippets/<id>.html` 作为引用。
4. 按 `params` 替换 snippet 顶部注释中标注的可替换字段。

### 7.5 特效与字幕时间轴对齐

`beat_sheet.json` 必须包含 `subtitle_event_id` 字段，指向对应字幕事件的唯一标识（如 `s03`）。生成 hyperframes composition 时：

- 特效 `.clip` 的 `data-start` 取自字幕事件的开始时间，允许向后偏移 0~0.3s 制造入场呼吸。
- 特效 `.clip` 的 `data-duration` 不超过字幕事件持续时间 + 0.5s；若字幕事件短于 2s，特效时长可延长至 2s，但不得覆盖后续字幕。
- GSAP timeline 的动画时间使用**成片全局时间**，与字幕事件时间一一对应。
- 如果某句台词对应字幕被剪辑合并或删除，其绑定的特效必须同步删除或重新绑定到相邻有效字幕。

### 7.6 密度与覆盖率检查

`build_beat_sheet.py` 输出后自动检查：

- 任意两个相邻 B-Roll 节拍结束与开始之间间隔 ≤ 15s；超出则标记 `density_gap` 并建议补充特效。
- B-Roll 总时长 / 成片时长 ≥ 40%；不足则告警。
- 所有 B-Roll 的 `subtitle_event_id` 必须能在字幕计划中找到；缺失则停止渲染。

## 8. 搭建 hyperframes 工程

### 8.1 目录结构

在项目目录下创建：

```text
my-project/
└── overlay/
    ├── composition.html      # hyperframes 主工程
    ├── beat_sheet.json       # 节拍表
    ├── assets/               # 本视频专用素材（图片、图标）
    └── snippets/             # 引用的特效范式副本
```

### 8.2 composition.html 模板要点

`composition.html` 需遵循 hyperframes 约定：

- 根节点：`<div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="<成片时长>">`
- 每个节拍一个 `.clip` 容器，使用 `data-start` 与 `data-duration`。
- 不设置 `html/body` 背景，保持透明。
- 动画使用 GSAP，`window.__timelines["main"]` 注册主 timeline。

参考本 Skill 的 composition 示例（后续在 `examples/demo-project/overlay/composition.html` 补充）。

### 8.3 素材准备

把 `STORYBOARD.md` 中 `素材文件` 列指定的图片复制到 `overlay/assets/`，并重命名为 ASCII 文件名（避免中文/空格导致路径问题）：

```bash
python3 ../scripts/prepare_overlay_assets.py \
  --storyboard ./my-project/STORYBOARD.md \
  --assets ./my-project/assets \
  --output ./my-project/overlay/assets
```

## 9. 渲染透明 MOV 特效轨

### 9.1 lint 与 validate

首次渲染前必须先过 lint：

```bash
cd ./my-project/overlay
npx hyperframes lint . && npx hyperframes validate .
```

常见 lint 问题：

- `repeat: -1`：本 Skill 特效库禁止无限循环，必须改用有限循环。
- CSS transform 与 GSAP transform 冲突：居中用 `gsap.set(xPercent: -50, yPercent: -50)`。
- 文字压到字幕安全区以下：确保关键元素不进入底部 10% 区域。

### 9.2 snapshot 抽帧目检

全片渲染很贵，先用 snapshot 在关键节拍抽帧：

```bash
npx hyperframes snapshot . --at 1.5,8.0,23.5,62.3,83.4,112.5,129.8
```

每改一个节拍 → 抽该节拍 2~3 个关键时刻 → 目检通过后再全片渲染。

### 9.3 渲染透明 MOV

```bash
npx hyperframes render . --format mov -o effects.mov
```

关键参数：

- `--format mov` 必须显式给出；默认输出 ProRes 4444（`yuva444p12le`），保留 alpha 通道。
- 不要再用 webm 作为透明中间格式：默认 webm 编码为 `yuv420p`，会丢弃 alpha，导致黑屏叠加在原片上。
- 分辨率保持 1920×1080；4K 源在 FFmpeg 合成时再放大，渲染速度更快。

## 10. FFmpeg 合成

### 10.1 提取媒体信息

```bash
ffprobe -v error \
  -show_entries format=duration \
  -show_entries stream=width,height,r_frame_rate \
  -of json ./my-project/aroll/cut_video.mp4 > ./my-project/aroll/media_info.json
```

### 10.2 合成特效轨

```bash
ffmpeg -i ./my-project/aroll/cut_video.mp4 \
  -i ./my-project/overlay/effects.mov \
  -filter_complex "\
    [1:v]scale=1920:1080:flags=lanczos,format=rgba[ov];\
    [0:v][ov]overlay=0:0:shortest=1:format=auto[v]" \
  -map "[v]" -map 0:a \
  -c:a copy \
  -c:v libx264 -crf 18 -preset medium \
  -movflags +faststart \
  ./my-project/aroll/with_effects.mp4
```

要点：

- 透明 MOV 直接作为第二个输入；ProRes 4444 自带 alpha，无需 `-c:v libvpx-vp9`。
- `scale` 后接 `format=rgba` 确保 alpha 通道被 overlay 滤镜识别。
- `overlay=0:0:shortest=1:format=auto` 让特效轨与原片等长，并自动处理 RGBA 叠加。
- 若源视频为 4K，把 `scale=` 改为源分辨率。

### 10.3 硬烧字幕

先生成 ASS：

```bash
python3 ../scripts/transcript_to_ass.py \
  --transcript ./my-project/aroll/transcript_corrected.json \
  --decisions ./my-project/aroll/edit_decisions.json \
  --style bilibili_white_heavy_outline \
  --config ../data/config.yaml \
  --output ./my-project/aroll/subtitles.ass
```

再烧录到视频：

```bash
ffmpeg -i ./my-project/aroll/with_effects.mp4 \
  -vf "ass=./my-project/aroll/subtitles.ass" \
  -c:a copy \
  -c:v libx264 -crf 18 -preset medium \
  ./my-project/aroll/with_subtitles.mp4
```

### 10.4 封面元数据

`data/config.yaml` 中 `cover.mode` 可选：

| 模式 | 行为 |
| --- | --- |
| `attached_pic` | 把封面图以 MP4 内置封面（attached pic）方式写入，播放仍从第一帧开始。 |
| `first_frame` | 把封面图烧录为视频第一帧，持续 1 秒后切回原片。 |
| `intro` | 生成 3 秒片头标题卡，需额外素材。 |

默认 `attached_pic`：

```bash
ffmpeg -i ./my-project/aroll/with_subtitles.mp4 \
  -i ./my-project/assets/cover.png \
  -map 0 -map 1 -c copy -disposition:v:1 attached_pic \
  ./my-project/publish/final.mp4
```

## 11. 发布前处理

### 11.1 生成外挂字幕

在 10.3 步骤已生成 `subtitles.ass`，同时输出 SRT：

```bash
python3 ../scripts/ass_to_srt.py \
  --input ./my-project/aroll/subtitles.ass \
  --output ./my-project/publish/final.srt
```

或直接从 transcript 生成 SRT：

```bash
python3 ../scripts/transcript_to_srt.py \
  --transcript ./my-project/aroll/transcript_corrected.json \
  --decisions ./my-project/aroll/edit_decisions.json \
  --output ./my-project/publish/final.srt
```

### 11.2 字幕-音频一致性检查

运行检查脚本，确保没有“字幕删了但声音还在”的隐藏语音：

```bash
python3 ../scripts/hidden_speech_check.py \
  --transcript ./my-project/aroll/transcript_corrected.json \
  --ass ./my-project/aroll/subtitles.ass \
  --decisions ./my-project/aroll/edit_decisions.json \
  --output ./my-project/publish/hidden_speech_review.md
```

若发现问题，停止渲染，回到 5.2 修正 `edit_decisions.json` 或字幕 plan。

### 11.3 校验帧

```bash
# 首帧
ffmpeg -ss 00:00:00 -i ./my-project/publish/final.mp4 -frames:v 1 \
  ./my-project/publish/check_first_frame.png

# 代表性字幕帧（取成片 20% 处）
ffmpeg -ss 00:00:27 -i ./my-project/publish/final.mp4 -frames:v 1 \
  ./my-project/publish/check_subtitle_frame.png
```

目检要点：

- 不遮字幕、不压人脸。
- 文字无错别字。
- 动画进出场干净。
- 转场退场顺序正确（文字先收、背景后揭开）。

### 11.4 发布包说明

基于 `templates/PUBLISH.template.md` 生成 `PUBLISH.md`，必须包含：

- 成片路径、时长、分辨率、文件大小。
- 使用的特效模式列表。
- 自动剪辑攻击性级别与主要切除项摘要。
- **诚实披露：未验证部分**（如某句口播与稿件不一致、某镜未找到真实时间戳等）。

## 12. 完整命令链示例

一次从头到尾的调用链：

```bash
PROJECT=./my-project
SKILL=..

# 1. 初始化（若阶段1 未做）
python3 ${SKILL}/scripts/init_project.py ${PROJECT} --topic "Cursor 按次计费"

# 2. 输入解析与下载
python3 ${SKILL}/scripts/ingest_input.py ${PROJECT} \
  --video "https://example.com/raw.mp4"

# 3. ASR 与标准化
python3 ${SKILL}/scripts/export_hotwords.py \
  --corrections ${SKILL}/data/corrections.yaml \
  --output ${PROJECT}/aroll/hotwords.txt

python3 ${SKILL}/scripts/transcribe_volcengine.py \
  --audio ${PROJECT}/aroll/source_video.mp4 \
  --provider volcengine_bigmodel_flash \
  --hotwords ${PROJECT}/aroll/hotwords.txt \
  --output ${PROJECT}/aroll/asr_raw.json

python3 ${SKILL}/scripts/normalize_asr.py \
  --provider volcengine_bigmodel_flash \
  --input ${PROJECT}/aroll/asr_raw.json \
  --output ${PROJECT}/aroll/transcript.json

python3 ${SKILL}/scripts/apply_corrections.py \
  --transcript ${PROJECT}/aroll/transcript.json \
  --corrections ${SKILL}/data/corrections.yaml \
  --output ${PROJECT}/aroll/transcript_corrected.json

# 4. 自动剪辑
python3 ${SKILL}/scripts/build_edit_decisions.py \
  --transcript ${PROJECT}/aroll/transcript_corrected.json \
  --config ${SKILL}/data/config.yaml \
  --aggression standard \
  --output ${PROJECT}/aroll/edit_decisions.json

# 5. 时间轴对齐
python3 ${SKILL}/scripts/map_timeline.py \
  --decisions ${PROJECT}/aroll/edit_decisions.json \
  --transcript ${PROJECT}/aroll/transcript_corrected.json \
  --output ${PROJECT}/aroll/timeline_map.json

# 6. 物理剪辑（可选，若只需特效叠加可跳过）
ffmpeg -f concat -safe 0 -i ${PROJECT}/aroll/segments.txt \
  -c copy ${PROJECT}/aroll/cut_video.mp4

# 7. 特效规划
python3 ${SKILL}/scripts/build_beat_sheet.py \
  --storyboard ${PROJECT}/STORYBOARD.md \
  --registry ${SKILL}/assets/effects_library/registry.json \
  --timeline ${PROJECT}/aroll/timeline_map.json \
  --output ${PROJECT}/overlay/beat_sheet.json

# 8. 素材准备
python3 ${SKILL}/scripts/prepare_overlay_assets.py \
  --storyboard ${PROJECT}/STORYBOARD.md \
  --assets ${PROJECT}/assets \
  --output ${PROJECT}/overlay/assets

# 9. hyperframes 渲染
cd ${PROJECT}/overlay
npx hyperframes lint . && npx hyperframes validate .
npx hyperframes snapshot . --at 1.5,8.0,23.5
npx hyperframes render . --format mov -o effects.mov
cd -

# 10. FFmpeg 合成
ffmpeg -i ${PROJECT}/aroll/cut_video.mp4 \
  -i ${PROJECT}/overlay/effects.mov \
  -filter_complex "[1:v]scale=1920:1080:flags=lanczos,format=rgba[ov];[0:v][ov]overlay=0:0:shortest=1:format=auto[v]" \
  -map "[v]" -map 0:a -c:a copy -c:v libx264 -crf 18 -preset medium \
  ${PROJECT}/aroll/with_effects.mp4

python3 ${SKILL}/scripts/transcript_to_ass.py \
  --transcript ${PROJECT}/aroll/transcript_corrected.json \
  --decisions ${PROJECT}/aroll/edit_decisions.json \
  --config ${SKILL}/data/config.yaml \
  --style bilibili_white_heavy_outline \
  --output ${PROJECT}/aroll/subtitles.ass

ffmpeg -i ${PROJECT}/aroll/with_effects.mp4 \
  -vf "ass=${PROJECT}/aroll/subtitles.ass" \
  -c:a copy -c:v libx264 -crf 18 -preset medium \
  ${PROJECT}/aroll/with_subtitles.mp4

# 11. 发布包
python3 ${SKILL}/scripts/render_publish.py \
  --project ${PROJECT} \
  --video ${PROJECT}/aroll/with_subtitles.mp4 \
  --ass ${PROJECT}/aroll/subtitles.ass \
  --decisions ${PROJECT}/aroll/edit_decisions.json \
  --cover ${PROJECT}/assets/cover.png \
  --config ${SKILL}/data/config.yaml \
  --output ${PROJECT}/publish
```

## 13. 错误处理要点

### 13.1 输入阶段

- 视频无法解析：`ffprobe` 返回非零 → 停止，提示检查文件完整性。
- URL 下载失败：保留 `.part` 文件，打印 HTTP 状态码与 Content-Length，不生成空文件。
- 项目目录缺少 `STORYBOARD.md` → 提示先运行阶段1 或手动创建。

### 13.2 ASR 阶段

- 云端 ASR 返回空结果或置信度过低 → 回退到下一个 provider。
- 所有 provider 失败 → 停止并提示用户提供字幕。
- 密钥缺失 → 明确提示从环境变量或 secrets-vault 配置，禁止写死密钥。

### 13.3 剪辑阶段

- `build_edit_decisions.py` 发现 `aggression=aggressive` 且切除总时长超过原片 40% → 生成 `review_draft.md` 并要求用户确认。
- 边界保护导致两个保留段重叠 → 报错并退出，要求人工检查。
- 应用修正词表后出现时间戳错位 → 修正只改文本不改时间。

### 13.4 时间轴对齐阶段

- 某句台词在 `timeline_map.json` 中找不到 → 在 `STORYBOARD.md` 对应行 `真实时间戳` 留空，并写入 `PUBLISH.md` 未验证部分。
- 成片时长与 `STORYBOARD.md` 预估时长偏差 > 15% → 警告但不阻断，由用户决定是否调分镜。

### 13.5 特效规划阶段

- `特效模式` ID 在 `registry.json` 中不存在 → 列出相近 ID 建议，停止生成 beat sheet。
- `STORYBOARD.md` 表格解析失败（列数不一致） → 打印行号，提示检查 Markdown 表格格式。
- B-Roll 覆盖率 < 40% → 警告，建议用户补充 B-Roll。
- 特效与字幕时间戳偏差 > 0.3s → 标记为 `misaligned_beat`，要求更新 `STORYBOARD.md` 或字幕时间轴。
- 任意连续 15s 区间无 B-Roll → 标记为 `density_gap`，必须补充特效或合并 A-Roll 段落。

### 13.6 hyperframes 阶段

- `lint` / `validate` 失败 → 不进入 snapshot/render，按错误提示修复 composition。
- `render` 输出无 alpha 或黑屏叠加 → 检查 `--format mov` 是否显式给出，避免默认 webm 的 `yuv420p` 丢 alpha。
- 素材路径含中文或空格导致读取失败 → `prepare_overlay_assets.py` 已统一改为 ASCII 文件名。

### 13.7 FFmpeg 合成阶段

- 特效轨分辨率与原片不一致 → 用 `scale=` 滤镜对齐。
- 字幕字体缺失 → `data/config.yaml` 中字体应使用系统常见字体（如 `Hiragino Sans GB`），或项目级配置覆盖。
- 输出文件大小异常（如 0 字节） → 用 `ffprobe` 验证输出流。

### 13.8 发布前处理阶段

- `hidden_speech_check.py` 发现隐藏语音 → 停止发布，回退修正剪辑或字幕。
- 封面图不存在且 `cover.mode=attached_pic` → 回退到 `first_frame` 模式或报错。
- 校验帧目检发现问题 → 回到对应步骤（剪辑 / hyperframes / 字幕）修复后重跑。

## 14. 迭代与回灌

每次项目交付后，若新增了验证通过的特效模式，按 `references/effects-library-spec.md` 完成四件套入库：

1. snippet → `assets/effects_library/snippets/<id>.html`
2. catalog 条目 → `assets/effects_library/catalog.md`
3. registry 记录 → `assets/effects_library/registry.json`
4. preview → `assets/effects_library/previews/<id>.html`

然后刷新 `assets/effects_library/index.html` 目检，并在 `data/memory.md` 追加入库记录。
