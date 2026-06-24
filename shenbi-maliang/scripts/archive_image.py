#!/usr/bin/env python3

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".heic"}
CATALOG_COLUMNS = ["日期", "文件", "标题", "比例", "形象", "平台", "类型", "用途", "风格标签", "场景标签", "画册短标签", "来源", "备注"]
OLD_CATALOG_COLUMNS = ["日期", "文件", "标题", "比例", "形象", "来源", "备注"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive an approved generated image into the Shenbi Maliang album.")
    parser.add_argument("--image", required=True, help="Approved image path.")
    parser.add_argument("--title", required=True, help="Short title for the album catalog.")
    parser.add_argument("--ratio", default="", help="Image ratio, such as 3:4 or 16:9.")
    parser.add_argument("--persona", default="", help="Persona id or filename used for generation.")
    parser.add_argument("--platform", default="", help="Optional platform tag, such as B站 or 微信公众号封面图.")
    parser.add_argument("--content-type", default="", help="Required content type tag, such as 评测类 or 生活类.")
    parser.add_argument("--purpose", default="", help="Required purpose tag, such as 视频封面 or 生活记录.")
    parser.add_argument("--style-tags", default="", help="Required visual style tags, separated by comma.")
    parser.add_argument("--scene-tags", default="", help="Required scene/context tags, separated by comma.")
    parser.add_argument("--board-label", default="", help="Required short label shown on album boards, within 10 Chinese chars.")
    parser.add_argument("--source", default="", help="Reference source summary.")
    parser.add_argument("--notes", default="", help="Style or scene notes.")
    parser.add_argument("--refresh", action="store_true", help="Refresh boards after archiving.")
    return parser.parse_args()


def slugify(text: str) -> str:
    text = text.strip().lower()
    replacements = {
        "3:4": "3x4",
        "4:3": "4x3",
        "16:9": "16x9",
        "9:16": "9x16",
        "1:1": "1x1",
        "2.35:1": "235x100",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "image"


def ensure_catalog(catalog: Path) -> None:
    if catalog.exists():
        normalize_catalog(catalog)
        return
    catalog.write_text(
        "# 画册索引\n\n"
        "只保存用户确认满意并明确同意沉淀的成品图。默认不要把未确认图、失败图或临时草稿写入画册。\n\n"
        + build_header(),
        encoding="utf-8",
    )


def clean_cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ").strip()


def build_header() -> str:
    header = "| " + " | ".join(CATALOG_COLUMNS) + " |\n"
    separator = "| " + " | ".join(["---"] * len(CATALOG_COLUMNS)) + " |\n"
    return header + separator


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


def derive_board_label(platform: str, content_type: str, purpose: str, style_tags: str, title: str) -> str:
    if platform and content_type:
        label = f"{platform}{content_type.replace('类', '')}"
    elif content_type:
        label = content_type
    elif purpose:
        label = purpose
    elif style_tags:
        label = re.split(r"[,，、\s]+", style_tags.strip())[0]
    else:
        label = title
    return re.sub(r"\s+", "", label)[:10] or "画册"


def normalize_catalog(catalog: Path) -> None:
    text = catalog.read_text(encoding="utf-8")
    if "| " + " | ".join(CATALOG_COLUMNS) + " |" in text:
        return

    lines = text.splitlines()
    rows: list[list[str]] = []
    for line in lines:
        cells = split_row(line)
        if not cells or is_separator(cells) or cells == OLD_CATALOG_COLUMNS:
            continue
        if len(cells) == len(OLD_CATALOG_COLUMNS):
            date, file_cell, title, ratio, persona, source, notes = cells
            board_label = derive_board_label("", "", "", notes, title)
            rows.append([date, file_cell, title, ratio, persona, "", "", "", notes, "", board_label, source, notes])

    migrated = (
        "# 画册索引\n\n"
        "只保存用户确认满意并明确同意沉淀的成品图。默认不要把未确认图、失败图或临时草稿写入画册。\n\n"
        + build_header()
    )
    for row in rows:
        migrated += "| " + " | ".join(row[: len(CATALOG_COLUMNS)]) + " |\n"
    catalog.write_text(migrated, encoding="utf-8")


def main() -> None:
    args = parse_args()
    image = Path(args.image).expanduser().resolve()
    if not image.exists():
        raise SystemExit(f"Image not found: {image}")
    if image.suffix.lower() not in IMAGE_EXTS:
        raise SystemExit(f"Unsupported image extension: {image.suffix}")

    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    album_dir = skill_root / "data" / "albums" / "approved_images"
    catalog = skill_root / "data" / "albums" / "catalog.md"
    album_dir.mkdir(parents=True, exist_ok=True)
    ensure_catalog(catalog)

    today = datetime.now().strftime("%Y-%m-%d")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    ratio_slug = slugify(args.ratio) if args.ratio else "ratio"
    title_slug = slugify(args.title)
    dest = album_dir / f"{stamp}-{title_slug}-{ratio_slug}{image.suffix.lower()}"
    shutil.copy2(image, dest)

    rel_dest = dest.relative_to(skill_root)
    row = (
        f"| {today} | `{rel_dest}` | {clean_cell(args.title)} | {clean_cell(args.ratio)} | "
        f"{clean_cell(args.persona)} | {clean_cell(args.platform)} | {clean_cell(args.content_type)} | "
        f"{clean_cell(args.purpose)} | {clean_cell(args.style_tags)} | {clean_cell(args.scene_tags)} | "
        f"{clean_cell(args.board_label or derive_board_label(args.platform, args.content_type, args.purpose, args.style_tags, args.title))} | "
        f"{clean_cell(args.source)} | {clean_cell(args.notes)} |\n"
    )
    with catalog.open("a", encoding="utf-8") as handle:
        handle.write(row)

    print(dest)

    if args.refresh:
        subprocess.run([sys.executable, str(script_dir / "refresh_boards.py")], check=True)


if __name__ == "__main__":
    main()
