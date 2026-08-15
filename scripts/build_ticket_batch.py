#!/usr/bin/env python3
"""Build deterministic travel-ticket posters from a JSON batch manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from normalize_reference_layout import (
    CANVAS_SIZE,
    PERFORATION_GUARD_W,
    PHOTO_W,
    STUB_W,
    TICKET_H,
    TICKET_W,
    TICKET_X,
    TICKET_Y,
    apply_ticket_shadow,
    build_background,
    draw_single_perforation,
    load_background_image,
    make_ticket_mask,
)


TITLE_FONT = Path("/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf")
MONO_FONT = Path("/System/Library/Fonts/SFNSMono.ttf")
TEXT_COLOR = (245, 240, 224)


def parse_hex(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"invalid RGB color: {value}")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def fitted_title_font(lines: list[str], max_width: int) -> ImageFont.FreeTypeFont:
    for size in range(72, 43, -1):
        font = ImageFont.truetype(str(TITLE_FONT), size)
        if max(font.getlength(line) for line in lines) <= max_width:
            return font
    return ImageFont.truetype(str(TITLE_FONT), 43)


def draw_barcode(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], seed: str) -> None:
    """Draw a deterministic decorative barcode with quiet-zone padding."""
    x1, y1, x2, y2 = box
    pattern = [1, 1, 1, 2, 1, 1]
    for char in seed:
        value = ord(char)
        pattern.extend((1 + (value >> shift) % 3) for shift in (0, 2, 4, 6))
        pattern.append(1)
    total = sum(pattern)
    scale = max(1.0, (x2 - x1) / total)
    cursor = float(x1)
    black = True
    for units in pattern:
        next_cursor = min(float(x2), cursor + units * scale)
        if black:
            draw.rectangle(
                (round(cursor), y1, max(round(cursor), round(next_cursor) - 1), y2),
                fill=TEXT_COLOR,
            )
        cursor = next_cursor
        black = not black
        if cursor >= x2:
            break


def build_stub(item: dict[str, object]) -> Image.Image:
    stub_color = parse_hex(str(item["stub_color"]))
    stub = Image.new("RGB", (STUB_W, TICKET_H), stub_color)
    draw = ImageDraw.Draw(stub)

    left = PERFORATION_GUARD_W + 22
    right = STUB_W - 29
    lines = [str(part).strip() for part in item["title_lines"]]
    title_font = fitted_title_font(lines, right - left)
    title_y = 39
    line_step = 68
    for index, line in enumerate(lines):
        draw.text((left, title_y + index * line_step), line, font=title_font, fill=TEXT_COLOR)

    mono_large = ImageFont.truetype(str(MONO_FONT), 30)
    mono_small = ImageFont.truetype(str(MONO_FONT), 27)
    draw.text((left, 235), str(item["date"]), font=mono_large, fill=TEXT_COLOR)
    draw.text((left, 306), str(item["number"]), font=mono_small, fill=TEXT_COLOR)
    draw.text((left, 349), str(item["code"]), font=mono_small, fill=TEXT_COLOR)
    draw_barcode(draw, (left, 421, right, 477), str(item["code"]))
    return stub


def build_ticket(item: dict[str, object], output_dir: Path, overwrite: bool = False) -> Path:
    source_path = Path(str(item["source"]))
    output_path = output_dir / str(item["filename"])
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite: {output_path}")

    center_y = float(item.get("photo_center_y", 0.5))
    photo = Image.open(source_path).convert("RGB")
    photo = ImageOps.fit(
        photo,
        (PHOTO_W, TICKET_H),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, center_y),
    )
    stub = build_stub(item)

    ticket = Image.new("RGB", (TICKET_W, TICKET_H))
    ticket.paste(photo, (0, 0))
    ticket.paste(stub, (PHOTO_W, 0))
    draw_single_perforation(ticket)

    has_color = "background" in item
    has_image = "background_image" in item
    if has_color == has_image:
        raise ValueError(
            "each manifest item must provide exactly one of background or background_image"
        )
    background = (
        build_background(parse_hex(str(item["background"])))
        if has_color
        else load_background_image(Path(str(item["background_image"])))
    )
    mask = make_ticket_mask()
    shadow_preset = item.get("shadow_preset")
    apply_ticket_shadow(
        background,
        mask,
        shadow_preset=str(shadow_preset) if shadow_preset else None,
    )
    background.paste(ticket, (TICKET_X, TICKET_Y), mask)

    output_dir.mkdir(parents=True, exist_ok=True)
    background.save(output_path, format="PNG", compress_level=6)
    return output_path


def build_contact_sheet(outputs: list[Path], output_path: Path) -> None:
    thumb_w, thumb_h = 351, 468
    gap = 24
    cols = 3
    rows = (len(outputs) + cols - 1) // cols
    canvas = Image.new(
        "RGB",
        (cols * thumb_w + (cols + 1) * gap, rows * thumb_h + (rows + 1) * gap),
        (30, 30, 28),
    )
    for index, path in enumerate(outputs):
        image = Image.open(path).convert("RGB").resize(
            (thumb_w, thumb_h), Image.Resampling.LANCZOS
        )
        col, row = index % cols, index // cols
        canvas.paste(image, (gap + col * (thumb_w + gap), gap + row * (thumb_h + gap)))
    canvas.save(output_path, format="PNG", compress_level=6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    outputs = [
        build_ticket(item, args.output_dir, overwrite=args.overwrite)
        for item in manifest["items"]
    ]
    if args.contact_sheet:
        if args.contact_sheet.exists() and not args.overwrite:
            raise FileExistsError(f"refusing to overwrite: {args.contact_sheet}")
        build_contact_sheet(outputs, args.contact_sheet)
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
