#!/usr/bin/env python3
"""Build a minimal stacked source-photo / ticket-poster comparison card."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


CANVAS = (1170, 1560)
BG = (173, 152, 133)
PHOTO_BOX = (55, 70, 1112, 775)
FINAL_CROP = (0, 430, 1170, 1090)
FINAL_TOP = 875
RADIUS = 15
FONT = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")


def rounded_image(image: Image.Image, size: tuple[int, int]) -> tuple[Image.Image, Image.Image]:
    fitted = ImageOps.fit(
        image.convert("RGB"),
        size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1), radius=RADIUS, fill=255
    )
    return fitted, mask


def add_shadow(canvas: Image.Image, mask: Image.Image, xy: tuple[int, int]) -> None:
    for offset, blur, opacity in (((2, 13), 28, 48), ((2, 6), 9, 34)):
        layer = Image.new("L", CANVAS, 0)
        layer.paste(mask, (xy[0] + offset[0], xy[1] + offset[1]))
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        shadow = Image.new("RGB", CANVAS, (34, 29, 25))
        canvas.paste(shadow, (0, 0), layer.point(lambda value: value * opacity // 255))


def label(canvas: Image.Image, xy: tuple[int, int], text: str) -> None:
    font = ImageFont.truetype(str(FONT), 30)
    draw = ImageDraw.Draw(canvas)
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0] + 42
    height = 50
    draw.rounded_rectangle(
        (xy[0], xy[1], xy[0] + width, xy[1] + height),
        radius=25,
        fill=(29, 26, 23),
    )
    draw.text(
        (xy[0] + 21, xy[1] + 8),
        text,
        font=font,
        fill=(247, 242, 230),
        stroke_width=0,
    )


def build(source_path: Path, final_path: Path, output_path: Path) -> None:
    canvas = Image.new("RGB", CANVAS, BG)

    photo, photo_mask = rounded_image(
        Image.open(source_path),
        (PHOTO_BOX[2] - PHOTO_BOX[0], PHOTO_BOX[3] - PHOTO_BOX[1]),
    )
    add_shadow(canvas, photo_mask, PHOTO_BOX[:2])
    canvas.paste(photo, PHOTO_BOX[:2], photo_mask)
    label(canvas, (80, 94), "原图")

    final = Image.open(final_path).convert("RGB")
    if final.size != CANVAS:
        raise ValueError(f"expected final poster {CANVAS}, got {final.size}")
    lower = final.crop(FINAL_CROP)
    canvas.paste(lower, (0, FINAL_TOP))

    draw = ImageDraw.Draw(canvas)
    center_x = CANVAS[0] // 2
    draw.line((center_x, 800, center_x, 854), fill=(81, 69, 59), width=2)
    draw.ellipse((center_x - 22, 814, center_x + 22, 858), fill=(81, 69, 59))
    arrow_font = ImageFont.truetype(str(FONT), 28)
    draw.text(
        (center_x, 834),
        "↓",
        font=arrow_font,
        anchor="mm",
        fill=(247, 242, 230),
    )
    label(canvas, (80, 892), "SKILL 成品")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")
    canvas.save(output_path, "PNG", compress_level=6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.final, args.output)


if __name__ == "__main__":
    main()
