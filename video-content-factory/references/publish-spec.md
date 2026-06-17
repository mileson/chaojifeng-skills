# 发布包规范

本规范定义 `video-content-factory` 阶段2（自动剪辑与特效合成）最终输出到 `publish/` 目录的发布包结构、字幕标准、热词校正流程、封面元数据模式与输出校验流程。所有脚本、Agent 与人工审阅均按此规范执行。

## 1. 发布包目录结构

发布包是阶段2的完整输出，默认位于项目目录的 `publish/` 下（可由 `data/config.yaml` 的 `publish.output_dir` 覆盖）。每个发布包必须是一个独立的子目录，命名规则为：

```text
<项目名>_publish_<YYYYMMDD>[_v<版本号>]/
```

例如：`agent-factory-cover-video_publish_20260616_v1/`。

### 1.1 目录树

```text
<publish_package>/
├── <项目名>_final.mp4              # 最终成片（必需）
├── <项目名>.srt                    # 外挂 SRT 字幕（默认启用）
├── <项目名>.ass                    # 样式化 ASS 字幕（默认启用）
├── <项目名>_subtitle_burned.mp4    # 仅硬字幕版（可选，用于平台强制内嵌场景）
├── metadata/
│   ├── edit_decisions.json         # 剪辑决策与时间轴映射
│   ├── hidden_speech_review.md     # 隐藏语音审查报告
│   ├── hidden_speech_review.json   # 机器可读审查数据
│   ├── subtitle_plan.json          # 字幕分段与词级删除决策
│   ├── review_draft.md             # 语义剪辑评审草稿（如进行过人工评审）
│   └── asr/
│       ├── <provider>_raw.json     # ASR 原始输出
│       └── normalized_transcript.json  # 标准化转录结果
├── covers/
│   ├── cover.png                   # 封面原图
│   ├── cover_attached_pic.mp4      # attached_pic 模式输出（如启用）
│   └── intro_title_card.mp4        # intro 模式标题卡（如启用）
├── check/
│   ├── check_first_frame.png       # 首帧校验图
│   ├── check_subtitle_frame.png    # 典型字幕帧校验图
│   ├── check_cover_attachment.png  # 封面元数据校验图（attached_pic 模式）
│   ├── check_effect_frame.png      # 特效叠加关键帧校验图
│   └── check_contact_sheet.jpg     # 多帧联络表（可选）
└── PUBLISH.md                      # 发布包说明（基于 templates/PUBLISH.template.md）
```

### 1.2 文件清单与启用开关

| 文件/目录 | 来源 | 启用开关（`data/config.yaml`） | 说明 |
|-----------|------|-------------------------------|------|
| `<项目名>_final.mp4` | FFmpeg 合成 | 始终启用 | 最终发布成片，含硬字幕与封面元数据（按模式）。 |
| `<项目名>.srt` | 字幕生成 | `publish.include_sidecar_srt` | 外挂纯文本字幕，用于平台二次编辑。 |
| `<项目名>.ass` | 字幕生成 | `publish.include_sidecar_ass` | 样式化字幕，含字体、描边、位置。 |
| `metadata/edit_decisions.json` | 自动剪辑 | `publish.include_edit_decisions` | 剪辑前后时间轴映射、原因、置信度。 |
| `metadata/hidden_speech_review.*` | 字幕一致性门 | `publish.include_hidden_speech_review` | 审查被删除或被文字修正的语音。 |
| `check/*` | 校验脚本 | `publish.include_review_artifacts` | 供人工目检的代表性帧。 |
| `PUBLISH.md` | 模板渲染 | 始终启用 | 本发布包的人类可读说明。 |

## 2. 命名约定

- **项目名**：由 `scripts/init_project.py` 传入的目录名，仅含 ASCII 字母、数字、连字符、下划线，不含空格。
- **成片文件名**：`<项目名>_final.mp4`。
- **字幕文件名**：`<项目名>.srt`、`<项目名>.ass`，与成片同名不同扩展名。
- **校验图前缀**：`check_<检查项>.png`。
- **时间戳格式**：JSON 中统一使用秒（浮点数，保留 3 位小数）；SRT/ASS 中使用 `HH:MM:SS,mmm`。

## 3. 字幕规范

### 3.1 SRT 规范

SRT 为纯文本外挂字幕，用于二次编辑与平台兼容。

- **编码**：UTF-8，带 BOM 可选，但推荐无 BOM。
- **时间码**：`HH:MM:SS,mmm --> HH:MM:SS,mmm`（注意逗号）。
- **事件编号**：从 1 开始连续递增，不允许跳号或重复。
- **每事件行数**：1~2 行，禁止 3 行及以上。
- **每行字数**：按 `subtitle.style_presets.<preset>.max_line_chars` 控制（默认 20 个汉字或等效字符）。
- **空行**：事件之间用空行分隔。
- **内容清理**：
  - 已删除的口误、重复片段不得出现在 SRT 中。
  - 仅允许文字级修正：ASR 错别字、专有名词、标点、中英文间距。
  - 禁止用文字替换隐藏未剪辑的口语音（必须通过 `word_cut_ranges` 物理删除）。

### 3.2 ASS 规范

ASS 为样式化字幕，用于烧录到成片。样式从 `data/config.yaml` 的 `subtitle.style_presets` 读取。

- **脚本信息头**：

```ass
[Script Info]
Title: <项目名>
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080
```

- **样式节**：必须引用配置中指定的 `default_style_preset`，例如 `bilibili_white_heavy_outline`：

```ass
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Hiragino Sans GB,58,&H00FFFFFF,&H000000FF,&H00000000,&H66000000,1,0,0,0,100,100,0,0,1,7,1,2,120,120,66,1
```

- **颜色格式**：ABGR（例如 `&H00FFFFFF` 为不透明白色）。
- **对齐方式**：`Alignment` 使用 ASS 标准（1=左下，2=中下，3=右下，5=左中，6=中中，7=右中，9=左上，10=中上，11=右上）。口播字幕默认使用 `2`（底部居中）。
- **事件节**：每条字幕一个 `Dialogue` 行，时间码同样使用 `HH:MM:SS.mm`（注意 ASS 使用点号而非逗号）。

```ass
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:05.00,0:00:08.50,Default,,0,0,0,,这是一条口播字幕
```

- **字体回退**：若目标平台缺少 `Hiragino Sans GB`，FFmpeg 烧录时由系统字体回退；发布前应在 `check_subtitle_frame.png` 中确认字形正确。

### 3.3 字幕分段原则

- 按完整语义单元分段，避免把两个独立句子挤进同一事件。
- 两行字幕的换行应作为视觉停顿，第一行末尾不保留仅因换行而存在的逗号。
- 中文口播断句不依赖空格；空格仅用于中英混排、产品名、数字与单位。
- 钩子、算账、对比、总结等关键节拍优先在节拍切换处分段。

### 3.4 字幕格式与时间规则（硬规范）

1. **句末标点**：
   - 单句字幕事件末尾**不得加句号**（保持口语化）。
   - 允许保留问句、感叹句的 `？`、`！`。
   - 顿号、逗号仅在句子内部需要视觉停顿时使用，避免句末残留。

2. **时间对齐**：
   - 字幕 `start` 不得早于对应口播第一个词的起音；`end` 不得晚于最后一个词的收音后 0.3s。
   - 优先使用词级 ASR 时间戳，而非片段级近似值。
   - 若经过自动剪辑，字幕时间必须映射到**成片时间轴**，禁止直接复用原片 ASR 时间。

3. **事件间隔**：
   - 相邻字幕事件之间至少保留 0.08s 间隙，防止播放器端出现重叠或闪烁。
   - 同一语义单元内上下行字幕使用同一时间码，禁止行间出现时间差。

4. **安全区与可读性**：
   - 每行不超过 20 个汉字（或等效字符），超出必须换行，总事件行数 ≤ 2。
   - 字幕底部边距（`MarginV`）≥ 66（以 1920×1080 PlayRes 为基准），避免与特效元素或平台 UI 冲突。

5. **隐藏语音一致性**：
   - 被剪辑切除的词不得出现在字幕中。
   - 文字级修正（错别字、专有名词）必须记录到 `subtitle_plan.json`，并在 `hidden_speech_review.md` 中说明。

## 4. 热词校正流程

热词校正的目标是让 ASR 正确识别专有名词、产品名、人名，并在字幕与成片时间轴中保持一致。

### 4.1 配置文件

主配置文件为 `data/corrections.yaml`（如不存在则由 Agent 在首次校正时创建）。结构如下：

```yaml
# data/corrections.yaml
literal_replacements:
  - from: "超级风"
    to: "超级峰"
  - from: "超级分"
    to: "超级峰"
  - from: "Claude fable"
    to: "Claude Fable"

preferred_terms:
  - term: "超级峰"
    context: "本账号作者名"
  - term: "video-content-factory"
    context: "本 Skill 名称"

homophone_groups:
  - canonical: "超级峰"
    variants: ["超级风", "超级分", "超几峰"]

hotwords_for_asr:
  - "video-content-factory"
  - "hyperframes"
  - "GSAP"
  - "FFmpeg"
```

### 4.2 校正执行顺序

1. **ASR 前导出热词**：若使用云端 ASR，先运行 `scripts/export_hotwords.py` 将 `hotwords_for_asr` 写入 provider 指定的热词文件/参数，提升识别准确率。
2. **标准化转录**：运行 `scripts/normalize_asr_result.py` 将各 provider 输出统一为 `{duration, segments:[{start,end,text,words}]}`。
3. **字面替换**：在生成字幕前对 `segments[].text` 与 `segments[].words[].word` 应用 `literal_replacements`。替换必须区分大小写，且优先最长匹配。
4. **偏好术语检查**：对 `preferred_terms` 进行全局扫描，若 ASR 输出与偏好术语冲突，按上下文替换并记录到 `subtitle_plan.json` 的 `text_only_corrections`。
5. **同音词消歧**：对 `homophone_groups` 中的变体，根据 `data/memory.md` 与 `data/brand-profile.yaml` 的上下文规则回正到 `canonical`。
6. **一致性门**：最终渲染前运行字幕-音频一致性检查，确保被删除或被文字替换的口语音已物理删除或已列入允许的文本级修正。

### 4.3 文字级修正的允许范围

| 类型 | 是否允许仅改字幕 | 必须物理删除音频 | 示例 |
|------|------------------|------------------|------|
| ASR 错别字 | 是 | 否 | "超级风" → "超级峰" |
| 专有名词大小写/空格 | 是 | 否 | "claude fable" → "Claude Fable" |
| 标点补充 | 是 | 否 | 句末加句号 |
| 口癖/重复片段 | 否 | 是 | "那个那个" 删除 |
| 半截重说 | 否 | 是 | "今天我们——今天我们来…" |
| 长停顿 | 否 | 是 | 无语音静音段 |

## 5. 封面元数据嵌入模式

封面模式由 `data/config.yaml` 的 `cover.mode` 控制，可选 `attached_pic`、`first_frame`、`intro`。默认使用 `attached_pic`。

### 5.1 attached_pic（默认）

将封面图作为 MP4 的 `attached_pic` 元数据流嵌入，播放器列表页显示封面，点击播放后从第一帧真实画面开始。

- **输入**：`cover.default_cover_asset`（默认 `assets/cover.png`）或阶段2传入的封面图。
- **FFmpeg 命令**：

```bash
ffmpeg -i <成片无封面>.mp4 -i <封面>.png \
  -map 0 -map 1 -c copy -disposition:v:1 attached_pic \
  <项目名>_final.mp4
```

- **约束**：封面图分辨率建议与视频一致（如 1920×1080），避免播放器缩放失真；文件大小 ≤ 1 MB。
- **校验**：`ffprobe` 应显示 `Stream #0:1: Video: mjpeg` 且 `DISPOSITION:attached_pic=1`。

### 5.2 first_frame

将封面图烧录为成片的第一可见帧，持续指定时长（默认 1.0 秒），随后切入真实视频。适用于平台不读取 `attached_pic` 但会抓取首帧作为封面的场景。

- **输入**：封面图 + 原成片。
- **实现**：生成 1 秒静帧视频，再与原片 concat。

```bash
# 生成 1 秒封面帧
ffmpeg -loop 1 -i <封面>.png -c:v libx264 -t 1 -pix_fmt yuv420p -vf "fps=30,scale=1920:1080" cover_1s.mp4
# concat
printf "file '%s'\nfile '%s'\n" cover_1s.mp4 <成片无封面>.mp4 > concat.txt
ffmpeg -f concat -safe 0 -i concat.txt -c copy <项目名>_final.mp4
```

- **音频处理**：封面帧段使用原片音频的淡入前 0.1 秒静音或保持原音频起始点；禁止在封面段暴露突兀原声。
- **校验**：`check_first_frame.png` 必须为封面图内容，`ffprobe` 第一视频流不得带有 `attached_pic`。

### 5.3 intro

在成片开头追加一个独立的标题卡片段（通常 2~4 秒），包含视频标题、副标题、作者署名，然后切入真实视频。适用于需要品牌开场或章节引子的内容。

- **输入**：标题文案、品牌配置 `data/brand-profile.yaml`。
- **实现**：
  1. 用 hyperframes 或静态图生成 `intro_title_card.mp4`（长度 `intro_duration`，默认 3 秒）。
  2. 与原片 concat，必要时在衔接处加入 0.2 秒黑场或淡入。
- **音频处理**：标题卡段配品牌音效或静音，音量归一化到 -23 LUFS。
- **校验**：`check_first_frame.png` 显示标题卡内容，`check_effect_frame.png` 显示 intro 到正片的过渡帧。

### 5.4 模式选择矩阵

| 场景 | 推荐模式 | 理由 |
|------|----------|------|
| B站/YouTube/视频号，平台读取封面元数据 | `attached_pic` | 播放体验最自然，不从封面图开始。 |
| 平台只抓取首帧，忽略 attached_pic | `first_frame` | 确保列表封面与首帧一致。 |
| 品牌开场、系列化内容 | `intro` | 提供独立标题卡，强化品牌识别。 |
| 用户明确要求「封面就是开头」 | `first_frame` 或 `intro` | 按用户要求的呈现方式选择。 |

## 6. 输出校验流程

输出校验分自动校验与人工目检两步。自动校验未通过不得进入人工目检；人工目检问题必须回改并重新校验。

### 6.1 自动校验项

| 校验项 | 工具/命令 | 通过标准 |
|--------|-----------|----------|
| 视频可解析 | `ffprobe -v error -show_format -show_streams -of json <成片>` | 返回 0，包含视频流与音频流。 |
| 时长一致性 | 对比 `edit_decisions.json` 的 `output_duration` 与 `ffprobe` 的 `duration` | 误差 ≤ 0.1 秒。 |
| 分辨率与帧率 | `ffprobe` | 与 `BRIEF.md` 或 `STORYBOARD.md` 声明一致。 |
| 封面元数据 | `ffprobe -v error -show_streams -of json <成片>` | `attached_pic` 模式：存在 disposition 为 attached_pic 的 mjpeg 流；`first_frame`/`intro` 模式：不存在 attached_pic 流。 |
| 字幕文件语法 | `ffmpeg` 模拟烧录或专用 SRT/ASS lint | SRT 事件编号连续、时间码单调递增；ASS 能正常解析。 |
| 文件大小 | `stat` / `ls -l` | 不超过平台上限或用户声明上限。 |
| 校验帧生成 | `ffmpeg -ss <t> -i <成片> -frames:v 1 -q:v 2 <图>` | 成功生成 PNG。 |

### 6.2 校验帧清单

以下校验帧必须生成到 `check/` 目录：

| 校验图 | 截取时刻 | 检查内容 |
|--------|----------|----------|
| `check_first_frame.png` | 0.5 秒 | 首帧画面：封面模式为 attached_pic 时应为真实视频第一帧；first_frame/intro 时应为封面图或标题卡。 |
| `check_subtitle_frame.png` | 首个非空字幕事件的中点 | 字幕不遮人脸、不压关键画面、描边清晰、换行自然。 |
| `check_cover_attachment.png` | 不适用（取封面流解码） | attached_pic 模式：从 MP4 提取封面图与原图对比像素一致。 |
| `check_effect_frame.png` | 每个关键节拍的中间帧（至少 3 个） | hyperframes 特效正确叠加、透明度保留、无穿帮。 |
| `check_contact_sheet.jpg`（可选） | 等间距 9~16 帧 | 全片视觉连续性快速目检。 |

### 6.3 人工目检清单

- [ ] 开头 3 秒有钩子，画面与口播同步。
- [ ] 字幕无错别字、无半截句子、无重叠。
- [ ] 特效不遮挡人脸、字幕、品牌 Logo。
- [ ] 转场节奏自然，无闪烁或黑帧异常。
- [ ] 封面/首帧无黑边、无拉伸、文字清晰。
- [ ] 音频无爆音、无截断、结尾不突兀。
- [ ] 片尾 CTA 单一明确，无多个并列动作。

### 6.4 校验脚本入口（规范约定）

建议实现 `scripts/validate_publish.py` 并支持如下调用：

```bash
python3 scripts/validate_publish.py <publish_package_dir> [--strict]
```

返回码：

- `0`：所有自动校验通过。
- `1`：文件缺失或格式错误。
- `2`：时长/分辨率/封面元数据不一致。
- `3`：字幕语法错误。

## 7. 诚实披露

`PUBLISH.md` 必须包含「诚实披露」段落，列出所有未经过完整验证的部分。典型条目包括：

- 口播稿是否经过本人口述定稿。
- ASR 是否使用词级时间戳。
- 自动剪辑是否包含人工确认的语义删除。
- 特效是否逐帧目检。
- 封面图是否经过人工审核。
- 音频是否经过响度归一化。

## 8. 附录：典型 ffprobe 输出（attached_pic 模式）

```json
{
  "streams": [
    {
      "codec_name": "h264",
      "codec_type": "video",
      "disposition": { "attached_pic": 0 }
    },
    {
      "codec_name": "mjpeg",
      "codec_type": "video",
      "disposition": { "attached_pic": 1 }
    },
    {
      "codec_name": "aac",
      "codec_type": "audio"
    }
  ],
  "format": {
    "duration": "164.800000",
    "bit_rate": "5242880"
  }
}
```
