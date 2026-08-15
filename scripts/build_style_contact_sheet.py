#!/usr/bin/env python3
"""Build a labeled comparison sheet for a background-style poster batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FONT_REGULAR = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
FONT_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def style_id_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    marker = "-old-town-"
    if marker not in stem:
        raise ValueError(f"cannot derive style_id from filename: {filename}")
    return stem.split(marker, 1)[1]


def build_sheet(
    manifest_path: Path,
    posters_dir: Path,
    registry_path: Path,
    output_path: Path,
    overwrite: bool,
) -> None:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite: {output_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    items = manifest["items"]

    width = 1440
    outer = 44
    gap = 24
    columns = 4
    header_h = 190
    tile_w = (width - outer * 2 - gap * (columns - 1)) // columns
    preview_w = tile_w
    preview_h = round(preview_w * 4 / 3)
    label_h = 105
    tile_h = preview_h + label_h
    rows = (len(items) + columns - 1) // columns
    height = header_h + outer + rows * tile_h + (rows - 1) * gap + outer

    canvas = Image.new("RGB", (width, height), (28, 29, 27))
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(FONT_BOLD, 46)
    subtitle_font = load_font(FONT_REGULAR, 24)
    name_font = load_font(FONT_REGULAR, 25)
    id_font = load_font(FONT_BOLD, 18)
    number_font = load_font(FONT_BOLD, 21)

    draw.text((outer, 42), "BACKGROUND STYLE SYSTEM V2 · 20 STYLES", font=title_font, fill=(244, 240, 229))
    draw.text(
        (outer, 112),
        "同一照片 · 同一票根 · BALANCED 强度 · STRICT 主体保护",
        font=subtitle_font,
        fill=(175, 178, 169),
    )

    for index, item in enumerate(items):
        filename = item["filename"]
        style_id = style_id_from_filename(filename)
        style = registry["styles"][style_id]
        poster_path = posters_dir / filename
        poster = Image.open(poster_path).convert("RGB")
        poster.thumbnail((preview_w, preview_h), Image.Resampling.LANCZOS)

        column = index % columns
        row = index // columns
        x = outer + column * (tile_w + gap)
        y = header_h + outer + row * (tile_h + gap)
        canvas.paste(poster, (x, y))

        label_y = y + preview_h + 14
        draw.text((x, label_y), f"{index + 1:02d}", font=number_font, fill=(222, 172, 88))
        draw.text((x + 42, label_y - 2), style["name"], font=name_font, fill=(244, 240, 229))
        draw.text((x, label_y + 46), style_id, font=id_font, fill=(142, 148, 140))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", compress_level=6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--posters-dir", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    build_sheet(
        args.manifest,
        args.posters_dir,
        args.registry,
        args.output,
        args.overwrite,
    )
    print(args.output)


if __name__ == "__main__":
    main()
