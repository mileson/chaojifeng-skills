#!/usr/bin/env python3

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".heic"}


@dataclass
class BoardItem:
    path: Path
    label: str
    details: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a numbered reference board for image generation.")
    parser.add_argument("--image", action="append", default=[], help="Input image path. Repeat for multiple images.")
    parser.add_argument("--label", action="append", default=[], help="Short Chinese label for the matching --image.")
    parser.add_argument("--detail", action="append", default=[], help="Optional detail lines for the matching --image. Use \\n between lines.")
    parser.add_argument("--input-dir", action="append", default=[], help="Add all images in a directory.")
    parser.add_argument("--output", required=True, help="Output PNG path.")
    parser.add_argument("--title", default="复刻参考板", help="Board title.")
    parser.add_argument("--cols", type=int, default=3, help="Number of columns.")
    parser.add_argument("--cell-width", type=int, default=520, help="Cell width in px.")
    parser.add_argument("--cell-height", type=int, default=680, help="Cell height in px.")
    parser.add_argument("--pad", type=int, default=24, help="Outer and inner padding in px.")
    parser.add_argument("--max-caption-chars", type=int, default=10, help="Maximum label length.")
    parser.add_argument("--max-detail-chars", type=int, default=24, help="Maximum detail length per line.")
    parser.add_argument("--max-detail-lines", type=int, default=3, help="Maximum detail lines per image.")
    return parser.parse_args()


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def clean_label(raw: str, max_chars: int) -> str:
    label = re.sub(r"\s+", "", raw.strip())
    if not label:
        return "参考"
    return label[:max_chars]


def label_from_stem(path: Path, max_chars: int) -> str:
    stem = re.sub(r"[_\-]+", " ", path.stem)
    stem = re.sub(r"\s+", "", stem)
    return clean_label(stem or "参考", max_chars)


def clean_detail_lines(raw: str, max_lines: int, max_chars: int) -> list[str]:
    normalized = raw.replace("\\n", "\n")
    lines = []
    for line in normalized.splitlines():
        cleaned = re.sub(r"\s+", " ", line.strip())
        if cleaned:
            lines.append(cleaned[:max_chars])
        if len(lines) >= max_lines:
            break
    return lines


def collect_items(args: argparse.Namespace) -> list[BoardItem]:
    if args.label and len(args.label) != len(args.image):
        raise SystemExit("--label must be omitted or repeated once for each --image.")
    if args.detail and len(args.detail) != len(args.image):
        raise SystemExit("--detail must be omitted or repeated once for each --image.")

    items: list[BoardItem] = []
    labels = args.label or []
    details = args.detail or []

    for idx, raw_path in enumerate(args.image):
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Image not found: {path}")
        label = labels[idx] if labels else label_from_stem(path, args.max_caption_chars)
        detail_lines = clean_detail_lines(details[idx], args.max_detail_lines, args.max_detail_chars) if details else []
        items.append(BoardItem(path=path, label=clean_label(label, args.max_caption_chars), details=detail_lines))

    for raw_dir in args.input_dir:
        input_dir = Path(raw_dir).expanduser().resolve()
        if not input_dir.exists():
            raise SystemExit(f"Input directory not found: {input_dir}")
        for path in sorted(input_dir.iterdir()):
            if path.suffix.lower() in IMAGE_EXTS:
                items.append(BoardItem(path=path, label=label_from_stem(path, args.max_caption_chars), details=[]))

    if not items:
        raise SystemExit("No input images provided.")
    return items


def flatten(img: Image.Image) -> Image.Image:
    if img.mode in {"RGBA", "LA"}:
        base = Image.new("RGB", img.size, "white")
        base.paste(img, mask=img.getchannel("A"))
        return base
    return img.convert("RGB")


def fit_image(path: Path, max_w: int, max_h: int) -> Image.Image:
    with Image.open(path) as img:
        preview = flatten(img)
    preview.thumbnail((max_w, max_h))
    return preview


def draw_centered(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font: ImageFont.ImageFont, fill: str) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    height = box[3] - box[1]
    draw.text((xy[0] - width / 2, xy[1] - height / 2), text, fill=fill, font=font)


def paste_badge(canvas: Image.Image, box: tuple[int, int, int, int], label: str, font: ImageFont.ImageFont) -> None:
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = box
    pad_x = 14
    pad_y = 9
    text_box = draw.textbbox((0, 0), label, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    bx0 = x0 + 18
    by1 = y1 - 18
    bx1 = min(x1 - 18, bx0 + text_w + 2 * pad_x)
    by0 = by1 - text_h - 2 * pad_y
    draw.rounded_rectangle((bx0, by0, bx1, by1), radius=14, fill=(0, 0, 0, 176))
    draw.text((bx0 + pad_x, by0 + pad_y - 1), label, fill="white", font=font)
    canvas.alpha_composite(overlay)


def fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
        return text
    suffix = "..."
    trimmed = text
    while trimmed and draw.textbbox((0, 0), trimmed + suffix, font=font)[2] > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + suffix) if trimmed else suffix


def paste_detail_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    label: str,
    details: list[str],
    label_font: ImageFont.ImageFont,
    detail_font: ImageFont.ImageFont,
) -> None:
    x0, y0, x1, y1 = box
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    pad_x = 14
    pad_y = 8
    panel_x = x0 + 18
    panel_top = y1 - 126
    max_text_width = x1 - x0 - 44

    label_box = draw.textbbox((0, 0), label, font=label_font)
    label_w = label_box[2] - label_box[0]
    label_h = label_box[3] - label_box[1]
    bx0 = panel_x
    by0 = panel_top
    bx1 = min(x1 - 18, bx0 + label_w + 2 * pad_x)
    by1 = by0 + label_h + 2 * pad_y
    draw.rounded_rectangle((bx0, by0, bx1, by1), radius=12, fill=(0, 0, 0, 176))
    draw.text((bx0 + pad_x, by0 + pad_y - 1), label, fill="white", font=label_font)

    text_y = by1 + 10
    for line in details[:3]:
        fitted = fit_text(draw, line, detail_font, max_text_width)
        draw.text((panel_x, text_y), fitted, fill="#3a352d", font=detail_font)
        text_y += 26

    canvas.alpha_composite(overlay)


def main() -> None:
    args = parse_args()
    items = collect_items(args)
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    cols = max(1, args.cols)
    rows = math.ceil(len(items) / cols)
    title_height = 78 if args.title else 0
    canvas_w = cols * args.cell_width + (cols + 1) * args.pad
    canvas_h = rows * args.cell_height + (rows + 1) * args.pad + title_height

    canvas = Image.new("RGBA", (canvas_w, canvas_h), "#f5f2ec")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(34, bold=True)
    number_font = load_font(30, bold=True)
    caption_font = load_font(24, bold=True)
    detail_font = load_font(19)

    grid_top = args.pad
    if args.title:
        draw_centered(draw, (canvas_w / 2, args.pad + 18), args.title, title_font, "#2d2a26")
        draw.line((args.pad, args.pad + 54, canvas_w - args.pad, args.pad + 54), fill="#d8d0c4", width=3)
        grid_top += title_height

    for index, item in enumerate(items, start=1):
        row, col = divmod(index - 1, cols)
        x0 = args.pad + col * args.cell_width
        y0 = grid_top + row * args.cell_height
        x1 = x0 + args.cell_width
        y1 = y0 + args.cell_height

        draw.rounded_rectangle((x0, y0, x1, y1), radius=16, fill="white", outline="#ddd6cb", width=2)
        detail_area_h = 134 if item.details else 80
        image_area_h = args.cell_height - 62 - detail_area_h
        preview = fit_image(item.path, args.cell_width - 2 * args.pad, image_area_h)
        px = x0 + (args.cell_width - preview.width) // 2
        py = y0 + 62 + (image_area_h - preview.height) // 2
        canvas.paste(preview, (px, py))

        badge_x, badge_y, badge_r = x0 + 18, y0 + 14, 23
        draw.ellipse((badge_x, badge_y, badge_x + 2 * badge_r, badge_y + 2 * badge_r), fill="#111111")
        draw_centered(draw, (badge_x + badge_r, badge_y + badge_r - 1), f"{index:02d}", number_font, "white")
        if item.details:
            paste_detail_panel(canvas, (x0, y0, x1, y1), item.label, item.details, caption_font, detail_font)
        else:
            paste_badge(canvas, (x0, y0, x1, y1), item.label, caption_font)

    canvas.convert("RGB").save(output)
    print(output)


if __name__ == "__main__":
    main()
