#!/usr/bin/env python3
"""为 video-content-factory 项目生成 hyperframes 透明特效轨。

读取项目目录下的 STORYBOARD.md，按句提取 B-ROLL 行绑定的特效模式 ID，
从本 Skill 的 assets/effects_library/registry.json 查找对应 snippet，
生成 broll-overlay/index.html（hyperframes composition），
并调用 npx hyperframes lint/validate/render 输出透明 overlay.webm。

用法:
    python3 scripts/render_effects.py <项目目录>
    python3 scripts/render_effects.py <项目目录> --preview
    python3 scripts/render_effects.py <项目目录> --output-dir broll-overlay-v2
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# ---- 路径常量（全部相对于本 Skill 根目录） ----
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
EFFECTS_DIR = SKILL_DIR / "assets" / "effects_library"
REGISTRY_PATH = EFFECTS_DIR / "registry.json"
CONFIG_PATH = SKILL_DIR / "data" / "config.yaml"

# ---- 默认渲染参数 ----
DEFAULT_RESOLUTION = (1920, 1080)
DEFAULT_OUTPUT_FORMAT = "webm"
DEFAULT_RENDER_PRESET = "medium"


def parse_time_range(value: str) -> tuple[float, float] | None:
    """解析真实时间戳，如 '12.3-18.5' 或 '12.3s - 18.5s'。"""
    if not value or not value.strip() or value.strip() in ("-", "—"):
        return None
    cleaned = re.sub(r"[sS\s]", "", value.strip())
    if "-" in cleaned:
        parts = cleaned.split("-")
    elif "~" in cleaned:
        parts = cleaned.split("~")
    else:
        return None
    if len(parts) != 2:
        return None
    try:
        start = float(parts[0])
        end = float(parts[1])
        return (start, end) if end >= start else (start, start)
    except ValueError:
        return None


def parse_duration(value: str) -> float | None:
    """解析时长字段，如 '5s'、'6'。"""
    if not value or not value.strip():
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", value.strip())
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def load_config() -> dict[str, Any]:
    """读取 data/config.yaml 中的 hyperframes 相关配置，缺失时返回默认值。"""
    config: dict[str, Any] = {
        "resolution": DEFAULT_RESOLUTION,
        "output_format": DEFAULT_OUTPUT_FORMAT,
        "render_preset": DEFAULT_RENDER_PRESET,
    }
    if not CONFIG_PATH.exists():
        return config

    text = CONFIG_PATH.read_text(encoding="utf-8")
    # 只提取本项目会用到的几个简单键值，避免依赖 PyYAML
    res_match = re.search(
        r"composition_resolution:\s*\[(\d+)\s*,\s*(\d+)\]", text
    )
    if res_match:
        config["resolution"] = (int(res_match.group(1)), int(res_match.group(2)))

    fmt_match = re.search(r'output_format:\s*"([^"]+)"', text)
    if fmt_match:
        config["output_format"] = fmt_match.group(1)

    preset_match = re.search(r'render_preset:\s*"([^"]+)"', text)
    if preset_match:
        config["render_preset"] = preset_match.group(1)

    return config


def load_registry() -> dict[str, dict[str, Any]]:
    """加载特效注册表，返回 id -> 记录的映射。"""
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"特效注册表不存在: {REGISTRY_PATH}")
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    effects = data.get("effects", [])
    if not isinstance(effects, list):
        raise ValueError("registry.json 根节点必须包含 effects 数组")
    return {item["id"]: item for item in effects if isinstance(item, dict) and "id" in item}


def parse_storyboard(project_dir: Path) -> list[dict[str, Any]]:
    """解析 STORYBOARD.md 分镜表，返回按顺序排列的镜行。"""
    storyboard_path = project_dir / "STORYBOARD.md"
    if not storyboard_path.exists():
        raise FileNotFoundError(f"分镜稿不存在: {storyboard_path}")

    lines = storyboard_path.read_text(encoding="utf-8").splitlines()

    # 找到表头行
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "镜号" in line:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("STORYBOARD.md 中未找到分镜表头")

    headers = [cell.strip() for cell in lines[header_idx].split("|")][1:-1]
    header_map = {h: idx for idx, h in enumerate(headers)}

    def col(name: str) -> int | None:
        return header_map.get(name)

    category_col = col("类别") or col("类型") or col("A/B")
    effect_col = col("特效模式") or col("特效ID") or col("模式")
    timestamp_col = col("真实时间戳") or col("时间戳")
    duration_col = col("预估时长") or col("时长")

    if category_col is None:
        raise ValueError("分镜表缺少『类别』列")
    if effect_col is None:
        raise ValueError("分镜表缺少『特效模式』列")

    # 跳过分隔行
    rows: list[dict[str, Any]] = []
    current_time = 0.0

    for line in lines[header_idx + 2 :]:
        if not line.strip().startswith("|"):
            break
        cells = [cell.strip() for cell in line.split("|")][1:-1]
        if len(cells) < len(headers):
            # 补齐空单元格
            cells.extend([""] * (len(headers) - len(cells)))

        category = cells[category_col].strip() if category_col < len(cells) else ""
        effect_id = cells[effect_col].strip() if effect_col < len(cells) else ""

        # 解析时间
        start = None
        duration = None
        if timestamp_col is not None and timestamp_col < len(cells):
            tr = parse_time_range(cells[timestamp_col])
            if tr:
                start, end = tr
                duration = end - start

        if duration is None and duration_col is not None and duration_col < len(cells):
            duration = parse_duration(cells[duration_col])

        # 如果仍未解析到时长，默认按 5s 占位并告警
        if duration is None:
            duration = 5.0

        if start is None:
            start = current_time
        end = start + duration
        current_time = end

        rows.append(
            {
                "line": line,
                "category": category,
                "effect_id": effect_id,
                "start": start,
                "duration": duration,
                "end": end,
            }
        )

    return rows


def collect_beats(
    rows: list[dict[str, Any]], registry: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """从分镜行中筛选 B-ROLL 且绑定了有效特效 ID 的节拍。"""
    beats: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    for idx, row in enumerate(rows, start=1):
        category = row["category"]
        if not re.search(r"b[\s\-_]?roll", category, re.I):
            continue

        effect_id = row["effect_id"]
        if not effect_id or effect_id in ("-", "—", "无", "NEW", "待补充"):
            continue
        # 去掉可能的反引号
        effect_id = effect_id.strip("`").strip()

        record = registry.get(effect_id)
        if not record:
            print(
                f"[警告] 第 {idx} 行引用的特效 ID '{effect_id}' 未在 registry.json 中注册，已跳过。",
                file=sys.stderr,
            )
            continue

        snippet_rel = record.get("path", f"snippets/{effect_id}.html")
        snippet_path = EFFECTS_DIR / snippet_rel
        if not snippet_path.exists():
            print(
                f"[警告] 特效 '{effect_id}' 的 snippet 不存在: {snippet_path}，已跳过。",
                file=sys.stderr,
            )
            continue

        # 重复使用的特效需要避免 id 冲突，这里先做记录，后续统一处理
        beats.append(
            {
                "index": idx,
                "id": effect_id,
                "name": record.get("name", effect_id),
                "start": row["start"],
                "duration": row["duration"],
                "end": row["end"],
                "snippet_path": snippet_path,
            }
        )
        used_ids.add(effect_id)

    return beats


def extract_snippet_parts(path: Path) -> dict[str, list[str] | str]:
    """从 snippet HTML 中提取样式、DOM、脚本。

    支持两种形态：
    - 完整 HTML 文档（含 <html>/<body>）：提取 body 内容、所有 <style>/<script>
    - 片段式 snippet（只有 <style> + DOM + <script>）：直接复用
    """
    text = path.read_text(encoding="utf-8")

    styles = re.findall(r"<style[^>]*>(.*?)</style>", text, flags=re.S | re.I)
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", text, flags=re.S | re.I)

    body_match = re.search(r"<body[^>]*>(.*?)</body>", text, flags=re.S | re.I)
    if body_match:
        dom = body_match.group(1)
    else:
        dom = text

    # 去掉已经单独提取出来的 style/script 标签，避免重复
    dom = re.sub(r"<style[^>]*>.*?</style>", "", dom, flags=re.S | re.I)
    dom = re.sub(r"<script[^>]*>.*?</script>", "", dom, flags=re.S | re.I)

    return {"styles": styles, "dom": dom.strip(), "scripts": scripts}


def build_composition(
    beats: list[dict[str, Any]], resolution: tuple[int, int]
) -> str:
    """根据节拍列表拼接成完整的 hyperframes composition HTML。"""
    width, height = resolution
    total_duration = max((b["end"] for b in beats), default=0.0)

    styles_parts: list[str] = []
    beats_html_parts: list[str] = []
    scripts_parts: list[str] = []

    for i, beat in enumerate(beats, start=1):
        parts = extract_snippet_parts(beat["snippet_path"])

        # 为当前 beat 的样式加注释，便于调试
        styles_parts.append(f"/* === beat-{i}: {beat['id']} ({beat['name']}) === */")
        for style in parts["styles"]:
            styles_parts.append(style)

        # beat 容器，避免 id 冲突：所有子元素 id 保留原样，容器 id 唯一
        beats_html_parts.append(
            f'<div id="beat-{i}" class="clip beat" '
            f'data-start="{beat["start"]:.3f}" '
            f'data-duration="{beat["duration"]:.3f}" '
            f'data-track-index="0">\n'
            f'  <!-- snippet: {beat["id"]} -->\n'
            f"  {parts['dom']}\n"
            f"</div>"
        )

        # 包装脚本：提供 t0 / tEnd / tl 作用域，并把子时间轴挂到 master
        snippet_script = "\n".join(parts["scripts"]).strip()
        # snippet 自包含时通常会声明自己的 const tl；在 composition 里统一使用 wrapper 提供的 tl
        snippet_script = re.sub(
            r"const\s+tl\s*=\s*gsap\.timeline\([^)]*\)\s*;?",
            "",
            snippet_script,
            count=1,
        )
        if snippet_script:
            script_body = snippet_script
        else:
            # 没有脚本时给一个默认淡入淡出
            script_body = (
                f"tl.to(beatEl, {{ autoAlpha: 1, duration: 0.05 }}, t0);\n"
                f"tl.to(beatEl, {{ autoAlpha: 0, duration: 0.25 }}, tEnd - 0.25);"
            )

        scripts_parts.append(
            f"(function() {{\n"
            f"  const beatEl = document.getElementById('beat-{i}');\n"
            f"  const t0 = {beat['start']:.3f};\n"
            f"  const tEnd = {beat['end']:.3f};\n"
            f"  const tl = gsap.timeline({{ paused: true }});\n"
            f"  gsap.set(beatEl, {{ autoAlpha: 0 }});\n"
            f"  {script_body}\n"
            f"  master.add(tl, 0);\n"
            f"}})();"
        )

    composition = f"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8" />
<title>broll overlay</title>
<style>
  /* 透明 overlay：html/body 不设背景 */
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ background: transparent; }}
  [data-composition-id="broll"] {{
    position: relative;
    width: {width}px;
    height: {height}px;
    overflow: hidden;
    font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
  }}
  .beat {{
    position: absolute;
    inset: 0;
    pointer-events: none;
    visibility: hidden;
  }}
</style>
{chr(10).join(styles_parts)}
</head>
<body>
<div id="root" data-composition-id="broll" data-start="0" data-width="{width}" data-height="{height}" data-duration="{total_duration:.3f}">
{chr(10).join(beats_html_parts)}
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
  window.__timelines = window.__timelines || {{}};
  const master = gsap.timeline({{ paused: true }});
{chr(10).join(scripts_parts)}
  window.__timelines["broll"] = master;
</script>
</body>
</html>
"""
    return composition


def run_command(cmd: list[str], cwd: Path, description: str) -> None:
    """运行外部命令，失败时给出清晰提示。"""
    print(f"$ {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as exc:
        print(f"[失败] {description}", file=sys.stderr)
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise
    if result.stdout:
        print(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="按 STORYBOARD.md 生成 hyperframes 透明特效轨"
    )
    parser.add_argument(
        "project_dir",
        type=Path,
        help="视频项目目录（需包含 STORYBOARD.md）",
    )
    parser.add_argument(
        "--output-dir",
        default="broll-overlay",
        help="特效工程输出目录，相对于项目目录（默认: broll-overlay）",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="只生成 index.html，不执行 hyperframes render",
    )
    parser.add_argument(
        "--skip-qa",
        action="store_true",
        help="跳过 lint/validate/render 等所有外部调用（仅生成文件）",
    )
    parser.add_argument(
        "--resolution",
        help="覆盖 composition 分辨率，格式 WIDTHxHEIGHT，例如 1920x1080",
    )
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    if not project_dir.exists():
        parser.error(f"项目目录不存在: {project_dir}")

    config = load_config()
    if args.resolution:
        match = re.match(r"(\d+)x(\d+)", args.resolution)
        if not match:
            parser.error("--resolution 格式应为 WIDTHxHEIGHT，例如 1920x1080")
        resolution = (int(match.group(1)), int(match.group(2)))
    else:
        resolution = config["resolution"]

    registry = load_registry()
    rows = parse_storyboard(project_dir)
    beats = collect_beats(rows, registry)

    if not beats:
        print(
            "[提示] STORYBOARD.md 中没有找到绑定有效特效的 B-ROLL 行，无需生成特效轨。",
            file=sys.stderr,
        )
        sys.exit(0)

    output_dir = project_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.html"

    composition = build_composition(beats, resolution)
    index_path.write_text(composition, encoding="utf-8")

    print(f"已生成分镜特效合成页: {index_path}")
    print(f"共 {len(beats)} 个节拍，总时长 {max(b['end'] for b in beats):.3f}s")
    for beat in beats:
        print(
            f"  - beat-{beat['index']}: {beat['id']} ({beat['name']}) "
            f"{beat['start']:.3f}s ~ {beat['end']:.3f}s"
        )

    if args.skip_qa:
        print("已跳过 lint/validate/render（--skip-qa）。")
        return

    # 检查 npx 是否可用
    if not shutil.which("npx"):
        print("[错误] 未找到 npx，无法调用 hyperframes CLI。", file=sys.stderr)
        sys.exit(1)

    run_command(
        ["npx", "hyperframes", "lint", "."],
        cwd=output_dir,
        description="hyperframes lint 失败",
    )
    run_command(
        ["npx", "hyperframes", "validate", "."],
        cwd=output_dir,
        description="hyperframes validate 失败",
    )

    if args.preview:
        print("--preview 模式：已跳过 render。")
        return

    fmt = config["output_format"]
    overlay_path = output_dir / f"overlay.{fmt}"
    run_command(
        [
            "npx",
            "hyperframes",
            "render",
            ".",
            "--format",
            fmt,
            "-o",
            overlay_path.name,
        ],
        cwd=output_dir,
        description="hyperframes render 失败",
    )
    print(f"已渲染透明特效轨: {overlay_path}")


if __name__ == "__main__":
    main()
