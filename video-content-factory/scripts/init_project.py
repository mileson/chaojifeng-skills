#!/usr/bin/env python3
"""初始化一个 video-content-factory 视频项目目录。"""

from __future__ import annotations

import argparse
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"


def copy_or_stub(src: Path | None, dst: Path, placeholders: dict[str, str]) -> None:
    text = src.read_text(encoding="utf-8") if src and src.exists() else ""
    for key, value in placeholders.items():
        text = text.replace(key, value)
    if not text.strip():
        text = f"# {dst.stem}\n\nTODO: 填写内容。\n"
    dst.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化 video-content-factory 视频项目目录")
    parser.add_argument("project_dir", type=Path, help="项目目录路径")
    parser.add_argument("--topic", default="未命名选题", help="选题名称")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    placeholders = {"<选题名>": args.topic, "<项目名>": project.name}

    # 创建目录
    (project / "assets").mkdir(parents=True, exist_ok=True)
    (project / "aroll").mkdir(parents=True, exist_ok=True)
    (project / "publish").mkdir(parents=True, exist_ok=True)

    files = [
        ("topic-brief.md", None),
        ("research.md", None),
        ("BRIEF.md", None),
        ("SCRIPT.md", TEMPLATES_DIR / "SCRIPT.template.md"),
        ("STORYBOARD.md", TEMPLATES_DIR / "STORYBOARD.template.md"),
    ]

    for name, template in files:
        copy_or_stub(template, project / name, placeholders)

    print(f"已初始化项目: {project}")
    print("生成文件:")
    for name, _ in files:
        print(f"  - {project / name}")
    print("生成目录:")
    for sub in ("assets", "aroll", "publish"):
        print(f"  - {project / sub}")


if __name__ == "__main__":
    main()
