#!/usr/bin/env python3
"""FFmpeg 合成脚本：主视频 + 透明特效轨 overlay + 硬字幕 + 封面元数据 → 最终 MP4。

用法示例：
    python3 scripts/compose_final.py --project-dir ./my-topic-video
    python3 scripts/compose_final.py --project-dir ./my-topic-video \
        --video ./my-topic-video/aroll/final_cut.mp4 \
        --overlay ./my-topic-video/assets/overlay.webm \
        --ass ./my-topic-video/publish/my-topic-video.ass \
        --cover ./my-topic-video/assets/cover.png
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

try:
    import yaml

    _HAS_YAML = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]
    _HAS_YAML = False

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_DIR / "data" / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """加载 Skill 全局配置，失败时返回最小默认结构。"""
    if not path.exists():
        print(f"[warn] 配置文件缺失: {path}", file=sys.stderr)
        return {}
    if not _HAS_YAML:
        print(
            f"[warn] 缺少 PyYAML，无法解析配置 {path}；将使用内置默认值。",
            file=sys.stderr,
        )
        print("提示：运行 `pip install pyyaml` 安装依赖。", file=sys.stderr)
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:  # pragma: no cover - yaml 异常兜底
        print(f"[warn] 解析配置文件失败: {exc}", file=sys.stderr)
        return {}


def find_file(*candidates: Path) -> Path | None:
    """返回第一个存在的路径，都不存在返回 None。"""
    for p in candidates:
        if p.exists():
            return p
    return None


def discover_inputs(project_dir: Path, args: argparse.Namespace) -> dict:
    """根据命令行参数与工程目录默认约定发现输入文件。"""
    cfg = load_config()

    # 主视频：优先命令行，再按工程约定自动发现
    video = args.video
    if not video:
        video = find_file(
            project_dir / "aroll" / "final_cut.mp4",
            project_dir / "aroll" / "raw.mp4",
            project_dir / "aroll" / "main.mp4",
        )

    # 透明特效轨
    overlay = args.overlay
    if not overlay:
        overlay = find_file(project_dir / "assets" / "overlay.webm")

    # 字幕：优先 ASS，再 SRT
    ass = args.ass
    srt = args.srt
    if not ass and not srt:
        srt = find_file(
            project_dir / "assets" / "subtitles.srt",
            project_dir / "subtitles.srt",
            project_dir / "publish" / f"{project_dir.name}.srt",
        )
        ass = find_file(
            project_dir / "assets" / "subtitles.ass",
            project_dir / "publish" / f"{project_dir.name}.ass",
        )

    # 封面：优先命令行，再工程约定，再全局配置
    cover = args.cover
    if not cover:
        cover = find_file(
            project_dir / "assets" / "cover.png",
            project_dir / "assets" / "cover.jpg",
        )
    if not cover and cfg.get("cover", {}).get("default_cover_asset"):
        cover = find_file(project_dir / cfg["cover"]["default_cover_asset"])

    return {
        "video": video,
        "overlay": overlay,
        "srt": srt,
        "ass": ass,
        "cover": cover,
    }


def run(cmd: list[str], dry_run: bool = False) -> subprocess.CompletedProcess:
    """执行或打印外部命令。"""
    if dry_run:
        print("[dry-run] " + " ".join(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    print("[exec] " + " ".join(cmd))
    return subprocess.run(cmd, check=True)


def ffprobe_json(path: Path, entries: str) -> dict:
    """使用 ffprobe 抓取指定条目并返回 JSON。"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", entries,
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def video_resolution(path: Path) -> tuple[int, int]:
    """返回视频宽高；失败时回退 1920x1080。"""
    try:
        data = ffprobe_json(path, "stream=width,height")
        for stream in data.get("streams", []):
            w = stream.get("width")
            h = stream.get("height")
            if w and h:
                return int(w), int(h)
    except Exception as exc:  # pragma: no cover
        print(f"[warn] 无法探测视频分辨率: {exc}", file=sys.stderr)
    return 1920, 1080


def video_duration(path: Path) -> float:
    """返回视频时长（秒）。"""
    try:
        data = ffprobe_json(path, "format=duration")
        return float(data.get("format", {}).get("duration", 0))
    except Exception as exc:  # pragma: no cover
        print(f"[warn] 无法探测视频时长: {exc}", file=sys.stderr)
        return 0.0


def escape_filter_path(path: Path) -> str:
    """转义 FFmpeg filter 路径中的特殊字符（冒号、反斜杠）。"""
    return path.resolve().as_posix().replace("\\", "/").replace(":", "\\:")


def build_ffmpeg_command(
    video: Path,
    overlay: Path | None,
    subtitle: Path | None,
    cover: Path | None,
    output: Path,
    cover_mode: str,
    resolution: tuple[int, int] | None,
) -> list[str]:
    """构造最终 FFmpeg 命令。"""
    w, h = resolution or video_resolution(video)

    inputs: list[str] = []
    maps: list[str] = []
    filters: list[str] = []
    attach: list[str] = []
    outputs: list[str] = []

    # 主视频：输入 0
    inputs.extend(["-i", str(video)])

    # 透明特效轨：输入 1（如存在）
    overlay_idx = None
    if overlay and overlay.exists():
        inputs.extend(["-c:v", "libvpx-vp9", "-i", str(overlay)])
        overlay_idx = 1

    # 封面首帧叠加：输入 +1（如需要且尚未作为输入）
    cover_idx = None
    if cover_mode == "first_frame" and cover and cover.exists():
        # 1 秒封面静帧，用于覆盖首帧
        inputs.extend(["-loop", "1", "-framerate", "30", "-t", "1", "-i", str(cover)])
        cover_idx = 2 if overlay_idx is not None else 1

    # 组装视频滤镜链
    # 当前视频标签
    current = "[0:v]"

    if overlay_idx is not None:
        # 缩放透明轨到主视频分辨率后 overlay
        filters.append(
            f"[{overlay_idx}:v]scale={w}:{h}:flags=lanczos[ov];"
            f"{current}[ov]overlay=0:0:shortest=1[vo]"
        )
        current = "[vo]"

    if cover_idx is not None:
        # 首帧叠加封面 1 秒
        filters.append(
            f"[{cover_idx}:v]scale={w}:{h}:flags=lanczos[cov_s];"
            f"{current}[cov_s]overlay=0:0:enable='between(t\\,0\\,1)'[covered]"
        )
        current = "[covered]"

    if subtitle and subtitle.exists():
        sub_path = escape_filter_path(subtitle)
        filters.append(f"{current}subtitles={sub_path}[outv]")
        current = "[outv]"

    # 滤镜链收尾：确保有输出标签
    if current == "[0:v]":
        filters.append("[0:v]copy[outv]")
    elif current != "[outv]":
        filters.append(f"{current}copy[outv]")

    # 封面元数据 attached_pic
    if cover_mode == "attached_pic" and cover and cover.exists():
        attach.extend([
            "-attach", str(cover),
            "-metadata:s:t:0", "mimetype=image/png",
        ])

    cmd = ["ffmpeg", "-y"] + inputs
    if filters:
        cmd.extend(["-filter_complex", ";".join(filters)])
    cmd.extend([
        "-map", "[outv]",
        "-map", "0:a?",
    ])
    cmd.extend(attach)
    cmd.extend([
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "copy",
    ])
    cmd.append(str(output))

    return cmd


def generate_review_frames(
    output: Path,
    publish_dir: Path,
    cover_mode: str,
    cover: Path | None,
    dry_run: bool = False,
) -> list[Path]:
    """生成首帧、字幕帧、封面校验帧。"""
    frames: list[Path] = []
    if dry_run:
        return frames

    duration = video_duration(output)
    first_frame = publish_dir / "check_first_frame.png"
    subtitle_frame = publish_dir / "check_subtitle_frame.png"

    # 首帧：第 0.5 秒，避免某些片头黑帧
    ss_first = min(0.5, max(0.0, duration - 0.1)) if duration > 0 else 0.0
    run(["ffmpeg", "-y", "-ss", str(ss_first), "-i", str(output), "-frames:v", "1", str(first_frame)])
    frames.append(first_frame)

    # 字幕帧：约 40% 处
    ss_sub = duration * 0.4 if duration > 0 else 0.0
    if ss_sub > ss_first:
        run(["ffmpeg", "-y", "-ss", str(ss_sub), "-i", str(output), "-frames:v", "1", str(subtitle_frame)])
        frames.append(subtitle_frame)

    # 封面校验帧
    if cover_mode == "attached_pic" and cover and cover.exists():
        cover_check = publish_dir / "check_cover_attachment.png"
        # 直接使用源封面作为视觉校验；如需要也可以从输出抽取 attached_pic
        run(["cp", str(cover), str(cover_check)])
        frames.append(cover_check)

    return frames


def main() -> int:
    parser = argparse.ArgumentParser(
        description="把主视频、透明特效轨、字幕与封面元数据合成为最终 MP4。"
    )
    parser.add_argument("--project-dir", type=Path, required=True, help="工程目录路径")
    parser.add_argument("--video", type=Path, default=None, help="主视频路径（默认自动发现 aroll/final_cut.mp4 等）")
    parser.add_argument("--overlay", type=Path, default=None, help="透明特效轨 overlay.webm 路径")
    parser.add_argument("--srt", type=Path, default=None, help="SRT 字幕路径")
    parser.add_argument("--ass", type=Path, default=None, help="ASS 字幕路径（优先使用）")
    parser.add_argument("--cover", type=Path, default=None, help="封面图片路径")
    parser.add_argument("--output", type=Path, default=None, help="最终 MP4 输出路径（默认 publish/<项目名>_final.mp4）")
    parser.add_argument("--cover-mode", choices=["attached_pic", "first_frame", "intro"], default=None, help="封面嵌入模式")
    parser.add_argument("--resolution", type=str, default=None, help="强制输出分辨率，如 1920x1080")
    parser.add_argument("--dry-run", action="store_true", help="只打印 FFmpeg 命令，不执行")
    parser.add_argument("--no-frames", action="store_true", help="不生成校验帧")
    args = parser.parse_args()

    project_dir: Path = args.project_dir.resolve()
    cfg = load_config()

    inputs = discover_inputs(project_dir, args)
    video = inputs["video"]
    if not video or not video.exists():
        print(f"[error] 未找到主视频，请使用 --video 指定。工程: {project_dir}", file=sys.stderr)
        return 1

    # 输出路径
    output = args.output
    if not output:
        publish_dir = project_dir / cfg.get("publish", {}).get("output_dir", "publish")
        publish_dir.mkdir(parents=True, exist_ok=True)
        output = publish_dir / f"{project_dir.name}_final.mp4"
    else:
        output.parent.mkdir(parents=True, exist_ok=True)

    # 字幕优先级：ASS > SRT
    subtitle = inputs["ass"] or inputs["srt"]
    if not subtitle:
        print("[warn] 未找到字幕文件，将输出无字幕成片。", file=sys.stderr)

    # 封面模式
    cover_mode = args.cover_mode or cfg.get("cover", {}).get("mode", "attached_pic")
    if cover_mode == "intro":
        print("[warn] intro 封面模式尚未实现，回退为 attached_pic。", file=sys.stderr)
        cover_mode = "attached_pic"

    cover = inputs["cover"]
    if cover_mode in ("attached_pic", "first_frame") and not cover:
        print("[warn] 未找到封面图片，跳过封面嵌入。", file=sys.stderr)
        cover_mode = "none"

    # 分辨率
    resolution = None
    if args.resolution:
        parts = args.resolution.lower().split("x")
        if len(parts) == 2:
            resolution = (int(parts[0]), int(parts[1]))

    cmd = build_ffmpeg_command(
        video=video,
        overlay=inputs["overlay"],
        subtitle=subtitle,
        cover=cover,
        output=output,
        cover_mode=cover_mode,
        resolution=resolution,
    )

    try:
        run(cmd, dry_run=args.dry_run)
    except subprocess.CalledProcessError as exc:
        print(f"[error] FFmpeg 合成失败: {exc}", file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"[ok] 已生成最终成片: {output}")
        if not args.no_frames:
            frames = generate_review_frames(
                output=output,
                publish_dir=output.parent,
                cover_mode=cover_mode,
                cover=cover,
                dry_run=False,
            )
            for f in frames:
                print(f"[ok] 校验帧: {f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
