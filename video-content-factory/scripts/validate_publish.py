#!/usr/bin/env python3
"""校验 video-content-factory 发布包是否符合 references/publish-spec.md。

用法：
    python3 scripts/validate_publish.py <publish_package_dir> [--strict]

返回码：
    0  所有自动校验通过
    1  文件缺失或格式错误
    2  时长/分辨率/封面元数据不一致
    3  字幕语法错误
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SRT_TIME_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


def error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


def run_ffprobe(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json",
        str(path),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=60
        )
    except FileNotFoundError as exc:
        raise RuntimeError("未找到 ffprobe，请安装 FFmpeg 并加入 PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffprobe 解析失败: {exc.stderr.strip()}") from exc
    return json.loads(result.stdout)


def timecode_to_ms(h: int, m: int, s: int, ms: int) -> int:
    return ((h * 60 + m) * 60 + s) * 1000 + ms


def validate_srt(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        errors.append(f"SRT 文件不存在: {path}")
        return errors
    text = path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    expected_index = 1
    last_end_ms = -1
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            errors.append(f"SRT 块行数不足: {block[:80]!r}")
            continue
        try:
            index = int(lines[0].strip())
        except ValueError:
            errors.append(f"SRT 事件编号不是整数: {lines[0]!r}")
            continue
        if index != expected_index:
            errors.append(f"SRT 事件编号不连续: 期望 {expected_index}，实际 {index}")
        expected_index += 1

        match = SRT_TIME_RE.match(lines[1].strip())
        if not match:
            errors.append(f"SRT 时间码格式错误: {lines[1]!r}")
            continue
        start_ms = timecode_to_ms(*map(int, match.groups()[:4]))
        end_ms = timecode_to_ms(*map(int, match.groups()[4:]))
        if start_ms >= end_ms:
            errors.append(f"SRT 事件开始时间不早于结束时间: {lines[1]!r}")
        if start_ms < last_end_ms:
            errors.append(f"SRT 事件时间重叠或回退: {lines[1]!r}")
        last_end_ms = end_ms

        content = "\n".join(lines[2:]).strip()
        if not content:
            errors.append(f"SRT 事件 {index} 内容为空")
        line_count = len(lines[2:])
        if line_count > 2:
            errors.append(f"SRT 事件 {index} 超过 2 行（实际 {line_count} 行）")
    return errors


def validate_ass(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        errors.append(f"ASS 文件不存在: {path}")
        return errors
    text = path.read_text(encoding="utf-8")
    if "[Script Info]" not in text:
        errors.append("ASS 缺少 [Script Info] 节")
    if "[V4+ Styles]" not in text and "[V4 Styles]" not in text:
        errors.append("ASS 缺少 [V4+ Styles] 节")
    if "[Events]" not in text:
        errors.append("ASS 缺少 [Events] 节")
    dialogue_count = text.count("\nDialogue:")
    if dialogue_count == 0:
        errors.append("ASS 没有 Dialogue 事件")
    return errors


def validate_package(package_dir: Path, strict: bool) -> int:
    if not package_dir.exists():
        error(f"发布包目录不存在: {package_dir}")
        return 1
    if not package_dir.is_dir():
        error(f"路径不是目录: {package_dir}")
        return 1

    exit_code = 0
    project_name = package_dir.name.split("_publish_")[0]
    final_mp4 = package_dir / f"{project_name}_final.mp4"

    # 1. 必需文件检查
    required_files = [
        final_mp4,
        package_dir / "PUBLISH.md",
    ]
    for f in required_files:
        if not f.exists():
            error(f"缺少必需文件: {f}")
            exit_code = 1

    # 2. ffprobe 解析
    if not final_mp4.exists():
        error("最终成片不存在，跳过后续视频校验")
        return 1

    try:
        probe = run_ffprobe(final_mp4)
    except RuntimeError as exc:
        error(str(exc))
        return 2

    streams = probe.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    if not video_streams:
        error("成片缺少视频流")
        exit_code = 2
    if not audio_streams:
        error("成片缺少音频流")
        exit_code = 2

    # 3. 封面元数据校验
    attached_pics = [
        s for s in video_streams
        if s.get("disposition", {}).get("attached_pic") == 1
    ]
    cover_mode_path = package_dir / "PUBLISH.md"
    cover_mode = None
    if cover_mode_path.exists():
        m = re.search(
            r"封面模式\s*[:：]\s*`<?(attached_pic|first_frame|intro)>?`",
            cover_mode_path.read_text(encoding="utf-8"),
        )
        if m:
            cover_mode = m.group(1)

    if cover_mode == "attached_pic" and not attached_pics:
        error("封面模式声明为 attached_pic，但成片未检测到 attached_pic 流")
        exit_code = 2
    elif cover_mode in ("first_frame", "intro") and attached_pics:
        error(f"封面模式声明为 {cover_mode}，但成片仍包含 attached_pic 流")
        exit_code = 2

    # 4. 时长校验
    fmt_duration = probe.get("format", {}).get("duration")
    if fmt_duration is None:
        error("ffprobe 无法读取成片时长")
        exit_code = 2
    else:
        info(f"成片时长: {float(fmt_duration):.3f}s")

    # 5. 字幕校验
    srt_path = package_dir / f"{project_name}.srt"
    ass_path = package_dir / f"{project_name}.ass"
    for path in (srt_path, ass_path):
        if path.exists():
            if path.suffix == ".srt":
                errs = validate_srt(path)
            else:
                errs = validate_ass(path)
            if errs:
                for e in errs:
                    error(f"{path.name}: {e}")
                exit_code = 3
            else:
                info(f"{path.name} 语法校验通过")
        else:
            warn(f"未找到字幕文件: {path}")
            if strict:
                exit_code = 1

    # 6. 校验图检查
    check_dir = package_dir / "check"
    required_checks = ["check_first_frame.png", "check_subtitle_frame.png"]
    if cover_mode == "attached_pic":
        required_checks.append("check_cover_attachment.png")
    for name in required_checks:
        if not (check_dir / name).exists():
            warn(f"缺少校验图: check/{name}")
            if strict:
                exit_code = 1

    # 7. 元数据目录检查
    meta_dir = package_dir / "metadata"
    for name in ("edit_decisions.json", "hidden_speech_review.md"):
        if not (meta_dir / name).exists():
            warn(f"缺少元数据文件: metadata/{name}")
            if strict:
                exit_code = 1

    if exit_code == 0:
        info("发布包自动校验通过")
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 video-content-factory 发布包")
    parser.add_argument("package_dir", type=Path, help="发布包目录路径")
    parser.add_argument(
        "--strict", action="store_true",
        help="严格模式：缺少可选文件（字幕、校验图、元数据）也报错"
    )
    args = parser.parse_args()
    return validate_package(args.package_dir, args.strict)


if __name__ == "__main__":
    sys.exit(main())
