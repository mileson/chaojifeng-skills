#!/usr/bin/env python3

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".heic"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive a persona image for the Shenbi Maliang skill.")
    parser.add_argument("--image", required=True, help="Persona image path.")
    parser.add_argument("--id", required=True, help="Stable persona id, such as default or chaojifeng.")
    parser.add_argument("--status", default="active", help="Catalog status. Default: active.")
    parser.add_argument("--notes", default="", help="Short notes about this persona image.")
    parser.add_argument("--refresh", action="store_true", help="Refresh persona and album boards after archiving.")
    return parser.parse_args()


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "persona"


def ensure_catalog(catalog: Path) -> None:
    if catalog.exists():
        return
    catalog.write_text(
        "# 形象照索引\n\n"
        "只记录用户明确提供给本 Skill 复用的形象照。调用本 Skill 时必须先使用这里的形象照，"
        "或要求用户提供并归档后再生成。\n\n"
        "| id | 文件 | 状态 | 说明 |\n"
        "| --- | --- | --- | --- |\n",
        encoding="utf-8",
    )


def clean_cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ").strip()


def main() -> None:
    args = parse_args()
    image = Path(args.image).expanduser().resolve()
    if not image.exists():
        raise SystemExit(f"Image not found: {image}")
    if image.suffix.lower() not in IMAGE_EXTS:
        raise SystemExit(f"Unsupported image extension: {image.suffix}")

    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    persona_dir = skill_root / "data" / "personas" / "images"
    catalog = skill_root / "data" / "personas" / "catalog.md"
    persona_dir.mkdir(parents=True, exist_ok=True)
    ensure_catalog(catalog)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    persona_id = slugify(args.id)
    dest = persona_dir / f"{persona_id}-{stamp}{image.suffix.lower()}"
    shutil.copy2(image, dest)

    rel_dest = dest.relative_to(skill_root)
    row = f"| {persona_id} | `{rel_dest}` | {clean_cell(args.status)} | {clean_cell(args.notes)} |\n"
    with catalog.open("a", encoding="utf-8") as handle:
        handle.write(row)

    print(dest)

    if args.refresh:
        subprocess.run([sys.executable, str(script_dir / "refresh_boards.py")], check=True)


if __name__ == "__main__":
    main()
