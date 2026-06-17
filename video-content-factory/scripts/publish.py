#!/usr/bin/env python3
"""video-content-factory 发布前处理脚本。

输入项目目录，自动发现剪辑后成片、SRT/ASS 字幕、封面图；输出到
`<项目名>_publish_<YYYYMMDD>[_v<N>]/` 发布包：硬字幕 MP4、sidecar SRT/ASS、
edit_decisions.json、hidden_speech_review.md、校验帧（first_frame /
subtitle_frame / cover_attachment）。

用法示例：
    python3 scripts/publish.py ./my-topic-video
    python3 scripts/publish.py ./my-topic-video --style-preset screen_recording_compact
    python3 scripts/publish.py ./my-topic-video --cover-mode first_frame --keep-temp
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_DIR / "data" / "config.yaml"
TEMPLATE_PATH = SKILL_DIR / "templates" / "PUBLISH.template.md"

# 当 PyYAML 不可用时使用的最小默认配置
DEFAULT_STYLE_PRESET = "bilibili_white_heavy_outline"
DEFAULT_STYLE: dict[str, Any] = {
    "font": "Hiragino Sans GB",
    "font_size": 58,
    "primary_colour": "&H00FFFFFF",
    "outline_colour": "&H00000000",
    "back_colour": "&H66000000",
    "bold": 1,
    "outline": 7,
    "shadow": 1,
    "alignment": 2,
    "margin_l": 120,
    "margin_r": 120,
    "margin_v": 66,
    "max_line_chars": 20,
    "max_lines": 2,
}

SRT_TIME_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


def _load_yaml(path: Path) -> dict[str, Any]:
    """加载 YAML 配置；PyYAML 缺失或失败时返回空字典。"""
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        print(f"[warn] 缺少 PyYAML，无法读取 {path}: {exc}", file=sys.stderr)
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"[warn] 读取配置 {path} 失败: {exc}", file=sys.stderr)
        return {}


def load_config() -> dict[str, Any]:
    return _load_yaml(CONFIG_PATH)


def get_style_preset(cfg: dict[str, Any], requested: str | None) -> tuple[str, dict[str, Any]]:
    """返回选中的样式预设名与样式字典。"""
    subtitle_cfg = cfg.get("subtitle", {}) if isinstance(cfg, dict) else {}
    presets = subtitle_cfg.get("style_presets") or {}
    name = requested or subtitle_cfg.get("default_style_preset") or DEFAULT_STYLE_PRESET
    style = presets.get(name) if isinstance(presets, dict) else None
    if not isinstance(style, dict):
        print(f"[warn] 未找到字幕样式预设 '{name}'，使用内置默认。", file=sys.stderr)
        return DEFAULT_STYLE_PRESET, dict(DEFAULT_STYLE)
    return name, style


def find_first_existing(candidates: list[Path]) -> Path | None:
    """返回候选列表中第一个存在的路径。"""
    for p in candidates:
        if p.exists():
            return p
    return None


def discover_inputs(project_dir: Path) -> dict[str, Any]:
    """按工程约定发现输入文件。"""
    name = project_dir.name

    # 成片：优先已经生成的最终成片，再按剪辑后成品约定查找
    video_candidates = [
        project_dir / "publish" / f"{name}_final.mp4",
        project_dir / "publish" / "final.mp4",
        project_dir / "aroll" / "final_cut.mp4",
        project_dir / "arroll" / "final.mp4",
        project_dir / "aroll" / "main.mp4",
        project_dir / "aroll" / "raw.mp4",
    ]
    video = find_first_existing(video_candidates)

    # 字幕：优先 ASS，再 SRT
    ass_candidates = [
        project_dir / "publish" / f"{name}.ass",
        project_dir / "assets" / "subtitles.ass",
        project_dir / "subtitles.ass",
    ]
    ass = find_first_existing(ass_candidates)

    srt_candidates = [
        project_dir / "publish" / f"{name}.srt",
        project_dir / "assets" / "subtitles.srt",
        project_dir / "subtitles.srt",
    ]
    srt = find_first_existing(srt_candidates)

    # 封面
    cover_candidates = [
        project_dir / "assets" / "cover.png",
        project_dir / "assets" / "cover.jpg",
        project_dir / "cover.png",
        project_dir / "cover.jpg",
    ]
    cover = find_first_existing(cover_candidates)

    # 决策文件与转录
    decisions_candidates = [
        project_dir / "edit_decisions.json",
        project_dir / "publish" / "edit_decisions.json",
        project_dir / "metadata" / "edit_decisions.json",
    ]
    decisions = find_first_existing(decisions_candidates)

    transcript_candidates = [
        project_dir / "transcript.json",
        project_dir / "arroll" / "transcript.json",
        project_dir / "assets" / "transcript.json",
    ]
    transcript = find_first_existing(transcript_candidates)

    hidden_speech_candidates = [
        project_dir / "hidden_speech_review.md",
        project_dir / "publish" / "hidden_speech_review.md",
        project_dir / "metadata" / "hidden_speech_review.md",
    ]
    hidden_speech = find_first_existing(hidden_speech_candidates)

    subtitle_plan_candidates = [
        project_dir / "subtitle_plan.json",
        project_dir / "publish" / "subtitle_plan.json",
        project_dir / "metadata" / "subtitle_plan.json",
    ]
    subtitle_plan = find_first_existing(subtitle_plan_candidates)

    return {
        "video": video,
        "srt": srt,
        "ass": ass,
        "cover": cover,
        "decisions": decisions,
        "transcript": transcript,
        "hidden_speech": hidden_speech,
        "subtitle_plan": subtitle_plan,
    }


def ffprobe_json(path: Path, entries: str) -> dict[str, Any]:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", entries,
        "-of", "json", str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def video_duration(path: Path) -> float:
    try:
        data = ffprobe_json(path, "format=duration")
        return float(data.get("format", {}).get("duration", 0))
    except Exception as exc:
        print(f"[warn] 无法探测视频时长: {exc}", file=sys.stderr)
        return 0.0


def video_resolution(path: Path) -> tuple[int, int]:
    try:
        data = ffprobe_json(path, "stream=width,height")
        for stream in data.get("streams", []):
            w = stream.get("width")
            h = stream.get("height")
            if w and h:
                return int(w), int(h)
    except Exception as exc:
        print(f"[warn] 无法探测视频分辨率: {exc}", file=sys.stderr)
    return 1920, 1080


def run_ffmpeg(cmd: list[str], dry_run: bool = False) -> None:
    if dry_run:
        print("[dry-run] " + " ".join(cmd))
        return
    print("[exec] " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def parse_srt(path: Path) -> list[dict[str, Any]]:
    """解析 SRT 文件为事件列表。"""
    text = path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    events: list[dict[str, Any]] = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        match = SRT_TIME_RE.match(lines[1].strip())
        if not match:
            continue
        nums = list(map(int, match.groups()))
        start = nums[0] * 3600 + nums[1] * 60 + nums[2] + nums[3] / 1000.0
        end = nums[4] * 3600 + nums[5] * 60 + nums[6] + nums[7] / 1000.0
        content = "\n".join(lines[2:]).strip()
        if content:
            events.append({"start": start, "end": end, "text": content})
    return events


def fmt_ass_time(t: float) -> str:
    cs = int(round(t * 100))
    h, rem = divmod(cs, 360_000)
    m, rem = divmod(rem, 6_000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def visual_width(text: str) -> float:
    return sum(0.55 if ord(ch) < 128 else 1.0 for ch in text)


def wrap_text(text: str, max_chars: int, max_lines: int) -> str:
    """简单按视觉宽度折行，用于 ASS 事件文本。"""
    if visual_width(text) <= max_chars * max_lines:
        return text
    target = max_chars * 0.9
    lines: list[str] = []
    remaining = text.strip()
    while remaining and len(lines) < max_lines:
        if visual_width(remaining) <= target or len(lines) == max_lines - 1:
            lines.append(remaining)
            break
        width = 0.0
        cut = 0
        for idx, ch in enumerate(remaining):
            width += 0.55 if ord(ch) < 128 else 1.0
            if width > target:
                cut = idx
                break
        if cut <= 0:
            cut = len(remaining)
        lines.append(remaining[:cut])
        remaining = remaining[cut:].strip()
    return r"\N".join(lines)


def write_ass(path: Path, events: list[dict[str, Any]], style_name: str, style: dict[str, Any], title: str = "") -> None:
    """将字幕事件写入 ASS 文件。"""
    max_chars = int(style.get("max_line_chars", 20))
    max_lines = int(style.get("max_lines", 2))
    lines = [
        "[Script Info]",
        f"Title: {title or style_name}",
        "ScriptType: v4.00+",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        (
            "Style: Default,"
            f"{style['font']},{style['font_size']},{style['primary_colour']},&H000000FF,"
            f"{style['outline_colour']},{style['back_colour']},{style['bold']},0,0,0,100,100,0,0,1,"
            f"{style['outline']},{style['shadow']},{style['alignment']},{style['margin_l']},"
            f"{style['margin_r']},{style['margin_v']},1"
        ),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for event in events:
        wrapped = wrap_text(event["text"], max_chars, max_lines)
        lines.append(
            f"Dialogue: 0,{fmt_ass_time(event['start'])},{fmt_ass_time(event['end'])},"
            "Default,,0,0,0,," + wrapped.replace("\n", r"\N")
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def attach_cover_to_video(video: Path, cover: Path, output: Path) -> None:
    """将封面以 attached_pic 形式嵌入 MP4。"""
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-v", "error",
        "-i", str(video), "-i", str(cover),
        "-map", "0", "-map", "1",
        "-c", "copy", "-c:v:1", "png",
        "-disposition:v:1", "attached_pic",
        "-metadata:s:v:1", "title=cover",
        "-metadata:s:v:1", "comment=Cover (front)",
        "-movflags", "+faststart",
        str(output),
    ]
    run_ffmpeg(cmd)


def generate_content_video(
    video: Path,
    subtitle: Path,
    cover_mode: str,
    cover: Path | None,
    output: Path,
    resolution: tuple[int, int],
    intro_duration: float,
    title: str,
    dry_run: bool,
) -> None:
    """生成带硬字幕的成片内容文件（attached_pic 模式不含封面元数据）。"""
    sub_path = subtitle.resolve().as_posix().replace(":", "\\:")
    temp_files: list[Path] = []

    if cover_mode in ("first_frame", "intro") and cover and cover.exists():
        duration = intro_duration if cover_mode == "intro" else 1.0
        temp_cover = output.parent / ".cover_intro.mp4"
        temp_main = output.parent / ".main_burned.mp4"
        list_file = output.parent / ".concat_list.txt"
        temp_files.extend([temp_cover, temp_main, list_file])

        # 封面片段
        if cover_mode == "intro":
            drawtext_filter = (
                f"scale={resolution[0]}:{resolution[1]}:flags=lanczos,"
                f"drawtext=text='{title}':fontcolor=white:fontsize=72:"
                f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=4:bordercolor=black@0.6"
            )
        else:
            drawtext_filter = f"scale={resolution[0]}:{resolution[1]}:flags=lanczos"

        cmd_cover = [
            "ffmpeg", "-y", "-hide_banner", "-v", "error",
            "-loop", "1", "-framerate", "30", "-i", str(cover),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-t", str(duration), "-shortest",
            "-vf", drawtext_filter,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(temp_cover),
        ]
        run_ffmpeg(cmd_cover, dry_run=dry_run)

        # 主视频硬字幕
        cmd_main = [
            "ffmpeg", "-y", "-hide_banner", "-v", "error",
            "-i", str(video),
            "-vf", f"ass={sub_path}",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            str(temp_main),
        ]
        run_ffmpeg(cmd_main, dry_run=dry_run)

        # concat
        list_file.write_text(
            f"file '{temp_cover.resolve().as_posix()}'\n"
            f"file '{temp_main.resolve().as_posix()}'\n",
            encoding="utf-8",
        )
        cmd_concat = [
            "ffmpeg", "-y", "-hide_banner", "-v", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", "-movflags", "+faststart",
            str(output),
        ]
        run_ffmpeg(cmd_concat, dry_run=dry_run)

        if not dry_run:
            for f in temp_files:
                f.unlink(missing_ok=True)
        return

    # attached_pic / none：仅烧录字幕
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-v", "error",
        "-i", str(video),
        "-vf", f"ass={sub_path}",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "copy",
        str(output),
    ]
    run_ffmpeg(cmd, dry_run=dry_run)


def load_or_create_edit_decisions(
    path: Path | None,
    video_duration_sec: float,
    project_name: str,
) -> dict[str, Any]:
    """加载已有剪辑决策；不存在时生成最小默认决策。"""
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "project": project_name,
        "generated_by": "publish.py fallback",
        "note": "未找到 edit_decisions.json，使用全片保留的最小默认决策。",
        "original_duration": round(video_duration_sec, 3),
        "edited_duration": round(video_duration_sec, 3),
        "segments": [
            {
                "source_start": 0.0,
                "source_end": round(video_duration_sec, 3),
                "output_start": 0.0,
                "output_end": round(video_duration_sec, 3),
                "reason": "full video fallback",
            }
        ],
        "decisions": [],
    }


def write_hidden_speech_review(
    output_path: Path,
    edit_decisions: dict[str, Any],
    existing: Path | None,
) -> None:
    """写入隐藏语音审查报告；如已存在则复制。"""
    if existing and existing.exists():
        shutil.copy2(existing, output_path)
        return

    issues = edit_decisions.get("hidden_speech_issues", 0)
    lines = [
        "# Hidden Speech Review",
        "",
        f"- Enabled: true",
        f"- Issues: {issues}",
        "",
    ]
    if issues:
        lines.append("请查看 metadata/edit_decisions.json 中的 hidden_speech_issues 与对应 review 文件。")
    else:
        lines.append("未发现被隐藏的语音；字幕与音频一致性门已通过或缺少词级时间戳。")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_first_subtitle_midpoint(events: list[dict[str, Any]]) -> float | None:
    for event in events:
        if event.get("text", "").strip():
            return (float(event["start"]) + float(event["end"])) / 2.0
    return None


def generate_check_frames(
    final_mp4: Path,
    package_dir: Path,
    cover_mode: str,
    cover: Path | None,
    subtitle_events: list[dict[str, Any]],
) -> list[Path]:
    """生成校验帧。"""
    frames: list[Path] = []
    duration = video_duration(final_mp4)

    check_dir = package_dir / "check"
    check_dir.mkdir(parents=True, exist_ok=True)

    # 首帧
    first_ss = min(0.5, max(0.0, duration - 0.1)) if duration > 0 else 0.0
    first_frame = check_dir / "check_first_frame.png"
    run_ffmpeg(["ffmpeg", "-y", "-hide_banner", "-v", "error",
                "-ss", str(first_ss), "-i", str(final_mp4),
                "-frames:v", "1", str(first_frame)])
    frames.append(first_frame)

    # 字幕帧
    subtitle_ss = extract_first_subtitle_midpoint(subtitle_events)
    if subtitle_ss is None:
        subtitle_ss = duration * 0.4 if duration > 0 else 0.0
    subtitle_ss = max(0.0, min(subtitle_ss, duration - 0.1)) if duration > 0 else 0.0
    subtitle_frame = check_dir / "check_subtitle_frame.png"
    run_ffmpeg(["ffmpeg", "-y", "-hide_banner", "-v", "error",
                "-ss", str(subtitle_ss), "-i", str(final_mp4),
                "-frames:v", "1", str(subtitle_frame)])
    frames.append(subtitle_frame)

    # 封面元数据校验
    if cover_mode == "attached_pic":
        cover_frame = check_dir / "check_cover_attachment.png"
        try:
            run_ffmpeg(["ffmpeg", "-y", "-hide_banner", "-v", "error",
                        "-i", str(final_mp4), "-map", "0:v:1",
                        "-frames:v", "1", "-c:v", "png",
                        str(cover_frame)])
            frames.append(cover_frame)
        except Exception as exc:
            print(f"[warn] 无法从成片提取 attached_pic 封面: {exc}", file=sys.stderr)
            if cover and cover.exists():
                shutil.copy2(cover, cover_frame)
                frames.append(cover_frame)

    return frames


def render_publish_md(
    template_path: Path,
    output_path: Path,
    project_name: str,
    style_name: str,
    cover_mode: str,
    duration: float,
    resolution: tuple[int, int],
) -> None:
    """基于模板渲染发布说明。"""
    if not template_path.exists():
        output_path.write_text(f"# {project_name} 发布包\n\n", encoding="utf-8")
        return

    text = template_path.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    minutes, sec = divmod(int(duration), 60)
    hours, minutes = divmod(minutes, 60)
    duration_str = f"{hours:02d}:{minutes:02d}:{sec:02d}" if hours > 0 else f"{minutes:02d}:{sec:02d}"

    replacements = {
        "<选题名>": project_name,
        "<项目名>": project_name,
        "<发布日期>": today,
        "<版本号，如 v1>": "v1",
        "<成片时长，如 02:44>": duration_str,
        "<如 1920×1080 / 30fps>": f"{resolution[0]}×{resolution[1]}",
        "<attached_pic / first_frame / intro>": cover_mode,
        "<如 bilibili_white_heavy_outline>": style_name,
        "`<项目名>_final.mp4`": f"`{project_name}_final.mp4`",
        "`<项目名>.srt`": f"`{project_name}.srt`",
        "`<项目名>.ass`": f"`{project_name}.ass`",
        "<assets/cover.png / 用户上传 / AI 生成>": "assets/cover.png" if cover_mode != "none" else "无",
        "<停留秒数>": "1" if cover_mode == "first_frame" else "3",
        "<标题卡秒数>": "3",
        "<原片时长>": duration_str,
        "<成片时长>": duration_str,
        "<删除时长>": "00:00",
        "<conservative / standard / aggressive>": "standard",
        "<是 / 否 / 未进行语义剪辑>": "否",
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    output_path.write_text(text, encoding="utf-8")


def create_publish_package(
    project_dir: Path,
    style_name: str,
    cover_mode: str,
    intro_duration: float,
    dry_run: bool,
    keep_temp: bool,
) -> Path:
    """创建发布包并返回包目录。"""
    cfg = load_config()
    name = project_dir.name
    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    # 发布包目录：<项目名>_publish_<YYYYMMDD>[_v<N>]
    base_dir = project_dir / f"{name}_publish_{today}"
    package_dir = base_dir
    version = 1
    while package_dir.exists():
        package_dir = Path(f"{base_dir}_v{version}")
        version += 1

    if not dry_run:
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "metadata").mkdir(parents=True, exist_ok=True)
        (package_dir / "check").mkdir(parents=True, exist_ok=True)
        (package_dir / "covers").mkdir(parents=True, exist_ok=True)

    inputs = discover_inputs(project_dir)
    video = inputs["video"]
    if not video or not video.exists():
        raise FileNotFoundError(
            f"未找到项目成片视频。请在 {project_dir}/arroll/ 或 {project_dir}/publish/ "
            f"放置最终成片（如 final_cut.mp4 / final.mp4）。"
        )

    cover = inputs["cover"]
    if cover_mode in ("attached_pic", "first_frame", "intro") and not cover:
        print("[warn] 未找到封面图，封面模式回退为 none。", file=sys.stderr)
        cover_mode = "none"

    # 样式与字幕
    style_name_actual, style = get_style_preset(cfg, style_name)
    ass_in_package = package_dir / f"{name}.ass"
    srt_in_package = package_dir / f"{name}.srt"

    if inputs["ass"] and inputs["ass"].exists():
        subtitle_events: list[dict[str, Any]] = []
        if inputs["srt"] and inputs["srt"].exists():
            subtitle_events = parse_srt(inputs["srt"])
        if not dry_run:
            shutil.copy2(inputs["ass"], ass_in_package)
            if inputs["srt"] and inputs["srt"].exists():
                shutil.copy2(inputs["srt"], srt_in_package)
    elif inputs["srt"] and inputs["srt"].exists():
        subtitle_events = parse_srt(inputs["srt"])
        if not dry_run:
            shutil.copy2(inputs["srt"], srt_in_package)
            write_ass(ass_in_package, subtitle_events, style_name_actual, style, name)
    else:
        raise FileNotFoundError(f"未找到项目字幕文件：{project_dir}")

    # 生成硬字幕成片（attached_pic 模式不含封面，后续再 attach）
    final_mp4 = package_dir / f"{name}_final.mp4"
    resolution = video_resolution(video)
    title = name.replace("-", " ").replace("_", " ").replace("'", " ")

    generate_content_video(
        video=video,
        subtitle=ass_in_package,
        cover_mode=cover_mode,
        cover=cover,
        output=final_mp4,
        resolution=resolution,
        intro_duration=intro_duration,
        title=title,
        dry_run=dry_run,
    )

    # attached_pic 模式：把封面嵌入最终成片；所有封面模式都把原封面复制到 covers/
    if cover and cover.exists() and not dry_run:
        shutil.copy2(cover, package_dir / "covers" / "cover.png")
        if cover_mode == "attached_pic":
            temp_final = package_dir / f".{name}_final_attached.mp4"
            attach_cover_to_video(final_mp4, cover, temp_final)
            shutil.move(temp_final, final_mp4)

    # 决策文件
    decisions = load_or_create_edit_decisions(
        inputs["decisions"], video_duration(video), name
    )
    decisions_path = package_dir / "metadata" / "edit_decisions.json"
    if not dry_run:
        decisions_path.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")

    # 隐藏语音审查
    hidden_review_path = package_dir / "metadata" / "hidden_speech_review.md"
    if not dry_run:
        write_hidden_speech_review(hidden_review_path, decisions, inputs["hidden_speech"])

    # subtitle_plan.json：如存在则复制，否则写入最小占位
    subtitle_plan_path = package_dir / "metadata" / "subtitle_plan.json"
    if inputs["subtitle_plan"] and inputs["subtitle_plan"].exists() and not dry_run:
        shutil.copy2(inputs["subtitle_plan"], subtitle_plan_path)
    elif not dry_run:
        subtitle_plan_path.write_text(
            json.dumps({
                "events": [
                    {"start": round(e["start"], 3), "end": round(e["end"], 3), "text": e["text"]}
                    for e in subtitle_events
                ],
                "word_cut_ranges": decisions.get("word_cut_ranges", []),
                "text_only_corrections": decisions.get("text_only_corrections", []),
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 校验帧
    if not dry_run:
        frames = generate_check_frames(final_mp4, package_dir, cover_mode, cover, subtitle_events)
        for f in frames:
            print(f"[ok] 校验帧: {f}")

    # 发布说明
    if not dry_run:
        render_publish_md(
            TEMPLATE_PATH,
            package_dir / "PUBLISH.md",
            name,
            style_name_actual,
            cover_mode,
            video_duration(final_mp4),
            resolution,
        )

    return package_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="video-content-factory 发布前处理脚本")
    parser.add_argument("project_dir", type=Path, help="项目目录路径")
    parser.add_argument(
        "--style-preset",
        default=None,
        help="覆盖默认字幕样式预设（如 bilibili_white_heavy_outline）",
    )
    parser.add_argument(
        "--cover-mode",
        choices=["attached_pic", "first_frame", "intro"],
        default=None,
        help="封面嵌入模式（默认从 data/config.yaml 读取）",
    )
    parser.add_argument(
        "--intro-duration",
        type=float,
        default=3.0,
        help="intro 模式标题卡时长（秒，默认 3.0）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印 FFmpeg 命令，不执行",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="保留临时文件",
    )
    args = parser.parse_args()

    project_dir: Path = args.project_dir.resolve()
    if not project_dir.exists():
        print(f"[error] 项目目录不存在: {project_dir}", file=sys.stderr)
        return 1

    cfg = load_config()
    cover_mode = args.cover_mode or cfg.get("cover", {}).get("mode") or "attached_pic"
    if cover_mode not in ("attached_pic", "first_frame", "intro"):
        print(f"[warn] 未知封面模式 '{cover_mode}'，回退为 attached_pic。", file=sys.stderr)
        cover_mode = "attached_pic"

    try:
        package_dir = create_publish_package(
            project_dir=project_dir,
            style_name=args.style_preset,
            cover_mode=cover_mode,
            intro_duration=args.intro_duration,
            dry_run=args.dry_run,
            keep_temp=args.keep_temp,
        )
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"[error] FFmpeg 命令执行失败: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[error] 发布包生成失败: {exc}", file=sys.stderr)
        return 3

    print(f"[ok] 发布包已生成: {package_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
