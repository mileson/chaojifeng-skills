#!/usr/bin/env python3

import subprocess
import sys
import re
from pathlib import Path


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".heic"}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def maybe_build(script: Path, input_dir: Path, output: Path, title: str) -> None:
    images = [path for path in sorted(input_dir.iterdir()) if path.suffix.lower() in IMAGE_EXTS]
    if not images:
        print(f"skip empty directory: {input_dir}")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    run([
        sys.executable,
        str(script),
        "--input-dir",
        str(input_dir),
        "--output",
        str(output),
        "--title",
        title,
    ])


def split_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells)


def strip_code(cell: str) -> str:
    cell = cell.strip()
    if cell.startswith("`") and cell.endswith("`"):
        return cell[1:-1]
    return cell


def first_tag(text: str) -> str:
    for separator in [",", "，", "、", " "]:
        if separator in text:
            return text.split(separator)[0].strip()
    return text.strip()


def compact_tags(text: str, max_tags: int = 4) -> str:
    tags = [tag.strip() for tag in re.split(r"[,，、/ ]+", text) if tag.strip()]
    return " / ".join(tags[:max_tags])


def derive_label(row: dict[str, str]) -> str:
    board_label = row.get("画册短标签", "").strip()
    if board_label:
        return board_label

    platform = row.get("平台", "").strip()
    content_type = row.get("类型", "").strip()
    purpose = row.get("用途", "").strip()
    style_tags = row.get("风格标签", "").strip()
    title = row.get("标题", "").strip()

    if platform and platform != "未指定" and content_type:
        label = f"{platform}{content_type.replace('类', '')}"
    elif content_type:
        label = content_type
    elif purpose:
        label = purpose
    elif style_tags:
        label = first_tag(style_tags)
    else:
        label = title
    return "".join(label.split())[:10] or "画册"


def derive_details(row: dict[str, str]) -> list[str]:
    details: list[str] = []
    purpose = row.get("用途", "").strip()
    style_tags = compact_tags(row.get("风格标签", ""))
    scene_tags = compact_tags(row.get("场景标签", ""))

    if purpose:
        details.append(f"用途：{purpose}")
    if style_tags:
        details.append(f"风格：{style_tags}")
    if scene_tags:
        details.append(f"场景：{scene_tags}")
    return details


def read_catalog_items(skill_root: Path, catalog: Path) -> list[tuple[Path, str, list[str]]]:
    if not catalog.exists():
        return []

    lines = catalog.read_text(encoding="utf-8").splitlines()
    headers: list[str] = []
    items: list[tuple[Path, str, list[str]]] = []

    for line in lines:
        cells = split_row(line)
        if not cells or is_separator(cells):
            continue
        if not headers and "文件" in cells:
            headers = cells
            continue
        if not headers or len(cells) != len(headers):
            continue

        row = dict(zip(headers, cells))
        raw_file = strip_code(row.get("文件", ""))
        if not raw_file:
            continue
        image_path = Path(raw_file)
        if not image_path.is_absolute():
            image_path = skill_root / image_path
        if image_path.suffix.lower() not in IMAGE_EXTS or not image_path.exists():
            print(f"skip missing catalog image: {image_path}")
            continue
        items.append((image_path, derive_label(row), derive_details(row)))

    return items


def build_album_board(script: Path, skill_root: Path, input_dir: Path, output: Path, title: str) -> None:
    catalog = skill_root / "data" / "albums" / "catalog.md"
    items = read_catalog_items(skill_root, catalog)
    if not items:
        maybe_build(script, input_dir, output, title)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(script),
        "--output",
        str(output),
        "--title",
        title,
    ]
    for image_path, label, details in items:
        cmd.extend(["--image", str(image_path), "--label", label])
        cmd.extend(["--detail", "\n".join(details)])
    run(cmd)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    build_script = script_dir / "build_reference_board.py"

    persona_images = skill_root / "data" / "personas" / "images"
    persona_board = skill_root / "data" / "personas" / "boards" / "persona_board.png"
    album_images = skill_root / "data" / "albums" / "approved_images"
    album_board = skill_root / "data" / "albums" / "boards" / "album_board.png"

    maybe_build(build_script, persona_images, persona_board, "形象照看板")
    build_album_board(build_script, skill_root, album_images, album_board, "历史画册")

    print(persona_board)
    print(album_board)


if __name__ == "__main__":
    main()
