#!/usr/bin/env python3
"""Render an exact, source-faithful travel-ticket poster with Pillow."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps, PngImagePlugin

from image_utils import open_prepared_source

from normalize_reference_layout import (
    CANVAS_SIZE,
    PHOTO_W,
    STUB_W,
    TICKET_H,
    TICKET_W,
    TICKET_X,
    TICKET_Y,
    apply_ticket_shadow,
    build_background,
    draw_single_perforation,
    make_ticket_mask,
)
from palette_utils import (
    RGB,
    file_sha256,
    load_palette_candidate,
    parse_canvas_color,
    parse_hex_color,
    rgb_to_hex,
)


STUB_TEXT_X = PHOTO_W + 48
TITLE_TOP = 48
TITLE_MAX_W = STUB_W - 72
DATE_TOP = 238
DATE_MAX_W = STUB_W - 104  # Keep clear of the centered right-edge notch.
NUMBER_TOP = 326
CODE_TOP = 367
BARCODE_TOP = 420
BARCODE_H = 43
BARCODE_MAX_W = STUB_W - 91


HEAVY_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)
BOLD_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)
CJK_FONT_CANDIDATES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
)


def _font_path(requested: Path | None, heavy: bool, needs_cjk: bool = False) -> str:
    if requested:
        if not requested.is_file():
            raise FileNotFoundError(f"font does not exist: {requested}")
        return str(requested)
    candidates = CJK_FONT_CANDIDATES if needs_cjk else (
        HEAVY_FONT_CANDIDATES if heavy else BOLD_FONT_CANDIDATES
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    raise FileNotFoundError(
        "no suitable bold font found; pass --font with a local TTF, OTF or TTC file"
    )


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _font_identity(path: str) -> dict[str, str]:
    font = _font(path, 16)
    family, style = font.getname()
    return {
        "name": f"{family} {style}".strip(),
        "sha256": file_sha256(Path(path)),
    }


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _balanced_word_lines(
    words: list[str], draw: ImageDraw.ImageDraw, font_path: str
) -> list[str]:
    if len(words) <= 1:
        return words
    measure_font = _font(font_path, 58)
    candidates = []
    for split in range(1, len(words)):
        first = " ".join(words[:split])
        second = " ".join(words[split:])
        first_w = _text_width(draw, first, measure_font)
        second_w = _text_width(draw, second, measure_font)
        score = max(first_w, second_w) + abs(first_w - second_w) * 0.35
        candidates.append((score, [first, second]))
    return min(candidates, key=lambda item: item[0])[1]


def _split_long_word(word: str, draw: ImageDraw.ImageDraw, font_path: str) -> list[str]:
    measure_font = _font(font_path, 52)
    candidates = []
    for split in range(2, len(word) - 1):
        first, second = word[:split], word[split:]
        first_w = _text_width(draw, first, measure_font)
        second_w = _text_width(draw, second, measure_font)
        score = max(first_w, second_w) + abs(first_w - second_w) * 0.45
        candidates.append((score, [first, second]))
    return min(candidates, key=lambda item: item[0])[1] if candidates else [word]


def _prepare_title_lines(
    title: str | None,
    explicit_lines: list[str] | None,
    draw: ImageDraw.ImageDraw,
    font_path: str,
) -> list[str]:
    if explicit_lines:
        lines = [line.strip() for line in explicit_lines if line.strip()]
    else:
        normalized = " ".join((title or "").strip().split())
        lines = _balanced_word_lines(normalized.split(" "), draw, font_path)
        if len(lines) == 1 and len(lines[0]) >= 7:
            # Keep a meaningful single word intact whenever it remains legible
            # at the supported minimum title size. Split only as a last resort.
            test_font = _font(font_path, 32)
            if _text_width(draw, lines[0], test_font) > TITLE_MAX_W:
                lines = _split_long_word(lines[0], draw, font_path)
    if not 1 <= len(lines) <= 2:
        raise ValueError("title must resolve to one or two non-empty lines")
    return lines


def _fit_title_font(
    lines: list[str], draw: ImageDraw.ImageDraw, font_path: str
) -> ImageFont.FreeTypeFont:
    for size in range(64, 31, -1):
        candidate = _font(font_path, size)
        if all(_text_width(draw, line, candidate) <= TITLE_MAX_W for line in lines):
            return candidate
    raise ValueError(
        "title cannot fit the information stub at the minimum size; provide --title-line values"
    )


def _fit_single_line_font(
    text: str,
    draw: ImageDraw.ImageDraw,
    font_path: str,
    preferred_size: int,
    minimum_size: int,
    maximum_width: int,
) -> ImageFont.FreeTypeFont:
    for size in range(preferred_size, minimum_size - 1, -1):
        candidate = _font(font_path, size)
        if _text_width(draw, text, candidate) <= maximum_width:
            return candidate
    raise ValueError(f'text does not fit the information stub: "{text}"')


def _draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: RGB,
    tracking: int,
) -> None:
    x_pos, y_pos = position
    for character in text:
        draw.text((x_pos, y_pos), character, font=font, fill=fill)
        x_pos += _text_width(draw, character, font) + tracking


def _draw_barcode(
    draw: ImageDraw.ImageDraw,
    x_pos: int,
    y_pos: int,
    maximum_width: int,
    height: int,
    color: RGB,
    code: str,
) -> None:
    digest = hashlib.sha256(code.encode("ascii")).digest()
    cursor = x_pos
    index = 0
    while cursor < x_pos + maximum_width - 2:
        value = digest[index % len(digest)]
        bar_width = 2 + value % 4
        gap = 2 + (value // 4) % 3
        bar_height = height - (value % 3) * 3
        if cursor + bar_width > x_pos + maximum_width:
            break
        draw.rectangle(
            (cursor, y_pos + height - bar_height, cursor + bar_width - 1, y_pos + height - 1),
            fill=color,
        )
        cursor += bar_width + gap
        index += 1


def build_stub(
    title: str | None,
    title_lines: list[str] | None,
    date: str,
    number: str,
    code: str,
    stub_color: RGB,
    text_color: RGB,
    requested_font: Path | None = None,
) -> tuple[Image.Image, dict[str, str]]:
    """Build the exact deterministic information stub and font identity."""
    stub = Image.new("RGB", (STUB_W, TICKET_H), stub_color)
    draw = ImageDraw.Draw(stub)
    raw_title = " ".join(title_lines or [title or ""])
    needs_cjk = any(ord(character) > 127 for character in raw_title)
    title_font_path = _font_path(requested_font, heavy=True, needs_cjk=needs_cjk)
    body_font_path = _font_path(requested_font, heavy=False, needs_cjk=False)
    lines = _prepare_title_lines(title, title_lines, draw, title_font_path)
    title_font = _fit_title_font(lines, draw, title_font_path)
    title_box = draw.textbbox((0, 0), "Ag", font=title_font)
    title_line_h = title_box[3] - title_box[1] + 5
    local_text_x = STUB_TEXT_X - PHOTO_W
    for index, line in enumerate(lines):
        draw.text(
            (local_text_x, TITLE_TOP + index * title_line_h),
            line,
            font=title_font,
            fill=text_color,
        )

    date_font = _fit_single_line_font(date, draw, body_font_path, 31, 25, DATE_MAX_W)
    number_font = _fit_single_line_font(number, draw, body_font_path, 27, 23, BARCODE_MAX_W)
    code_font = _fit_single_line_font(code, draw, body_font_path, 27, 23, BARCODE_MAX_W)
    _draw_tracked_text(draw, (local_text_x, DATE_TOP), date, date_font, text_color, 1)
    _draw_tracked_text(draw, (local_text_x, NUMBER_TOP), number, number_font, text_color, 1)
    _draw_tracked_text(draw, (local_text_x, CODE_TOP), code, code_font, text_color, 1)
    _draw_barcode(
        draw,
        local_text_x,
        BARCODE_TOP,
        BARCODE_MAX_W,
        BARCODE_H,
        text_color,
        code,
    )
    title_font_identity = _font_identity(title_font_path)
    body_font_identity = _font_identity(body_font_path)
    identity = {
        "title_font_name": title_font_identity["name"],
        "title_font_sha256": title_font_identity["sha256"],
        "body_font_name": body_font_identity["name"],
        "body_font_sha256": body_font_identity["sha256"],
    }
    return stub, identity


def _load_palette(
    path: Path,
    candidate_id: str,
    source_path: Path,
    photo_center_y: float,
    strip_neutral_borders: bool,
) -> tuple[RGB, RGB, RGB]:
    return load_palette_candidate(
        path,
        candidate_id,
        source_path,
        photo_center_y,
        strip_neutral_borders,
    )


def render(
    photo_source_path: Path,
    output_path: Path,
    title: str | None,
    title_lines: list[str] | None,
    date: str,
    number: str,
    code: str,
    background_color: RGB,
    stub_color: RGB,
    text_color: RGB,
    photo_center_y: float,
    requested_font: Path | None = None,
    strip_neutral_borders: bool = True,
) -> dict[str, str]:
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")
    source = open_prepared_source(photo_source_path, strip_neutral_borders)
    photo = ImageOps.fit(
        source,
        (PHOTO_W, TICKET_H),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, photo_center_y),
    )

    stub, font_identity = build_stub(
        title,
        title_lines,
        date,
        number,
        code,
        stub_color,
        text_color,
        requested_font,
    )
    ticket = Image.new("RGB", (TICKET_W, TICKET_H), stub_color)
    ticket.paste(photo, (0, 0))
    ticket.paste(stub, (PHOTO_W, 0))
    draw_single_perforation(ticket, background_color)

    mask = make_ticket_mask()
    background = build_background(background_color)
    apply_ticket_shadow(background, mask, background_color)
    background.paste(ticket, (TICKET_X, TICKET_Y), mask)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "dy_ticket_renderer": "1",
        "dy_ticket_source_sha256": file_sha256(photo_source_path),
        "dy_ticket_photo_center_y": f"{photo_center_y:.9f}",
        "dy_ticket_strip_neutral_borders": "1" if strip_neutral_borders else "0",
        "dy_ticket_background": rgb_to_hex(background_color),
        "dy_ticket_stub": rgb_to_hex(stub_color),
        "dy_ticket_text": rgb_to_hex(text_color),
        "dy_ticket_title": title or "",
        "dy_ticket_title_lines": json.dumps(title_lines or [], ensure_ascii=False),
        "dy_ticket_date": date,
        "dy_ticket_number": number,
        "dy_ticket_code": code,
        "dy_ticket_title_font_name": font_identity["title_font_name"],
        "dy_ticket_title_font_sha256": font_identity["title_font_sha256"],
        "dy_ticket_body_font_name": font_identity["body_font_name"],
        "dy_ticket_body_font_sha256": font_identity["body_font_sha256"],
    }
    png_info = PngImagePlugin.PngInfo()
    for key, value in metadata.items():
        png_info.add_text(key, value)
    background.save(
        output_path,
        format="PNG",
        compress_level=6,
        pnginfo=png_info,
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    title_group = parser.add_mutually_exclusive_group(required=True)
    title_group.add_argument("--title")
    title_group.add_argument("--title-line", action="append", dest="title_lines")
    parser.add_argument("--date", required=True)
    parser.add_argument("--number", required=True)
    parser.add_argument("--code", required=True)
    parser.add_argument("--palette-json", type=Path)
    parser.add_argument("--palette-candidate", default="quiet-light")
    parser.add_argument("--background-color", type=parse_canvas_color)
    parser.add_argument("--stub-color", type=parse_hex_color)
    parser.add_argument("--text-color", type=parse_hex_color)
    parser.add_argument("--photo-center-y", type=float, default=0.5)
    parser.add_argument("--font", type=Path)
    parser.add_argument(
        "--keep-neutral-borders",
        action="store_true",
        help="Preserve intentional solid white/black framing at the photo edge",
    )
    args = parser.parse_args()

    if not args.photo_source.is_file():
        parser.error(f"photo source does not exist: {args.photo_source}")
    if not 0.0 <= args.photo_center_y <= 1.0:
        parser.error("--photo-center-y must be between 0 and 1")
    if args.title_lines and len(args.title_lines) > 2:
        parser.error("pass --title-line once or twice")
    if not re.fullmatch(r"\d{4} - \d{2}", args.date):
        parser.error('--date must use the exact format "YYYY - MM"')
    number = args.number.upper()
    if re.fullmatch(r"\d{5}", number):
        number = f"NO.{number}"
    if not re.fullmatch(r"NO\.\d{5}", number):
        parser.error('--number must be five digits or the exact form "NO.12345"')
    code = args.code.upper()
    if not re.fullmatch(r"[A-Z0-9]{8}", code):
        parser.error("--code must contain exactly eight uppercase letters or digits")

    palette_colors: tuple[RGB, RGB, RGB] | None = None
    if args.palette_json:
        palette_colors = _load_palette(
            args.palette_json,
            args.palette_candidate,
            args.photo_source,
            args.photo_center_y,
            not args.keep_neutral_borders,
        )
    background = args.background_color or (palette_colors[0] if palette_colors else None)
    stub = args.stub_color or (palette_colors[1] if palette_colors else None)
    text_color = args.text_color or (palette_colors[2] if palette_colors else None)
    if not all((background, stub, text_color)):
        parser.error(
            "provide --palette-json or all of --background-color, --stub-color and --text-color"
        )

    metadata = render(
        args.photo_source,
        args.output,
        args.title,
        args.title_lines,
        args.date,
        number,
        code,
        background,
        stub,
        text_color,
        args.photo_center_y,
        args.font,
        not args.keep_neutral_borders,
    )
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "background": rgb_to_hex(background),
                "stub": rgb_to_hex(stub),
                "text": rgb_to_hex(text_color),
                "title_font": metadata["dy_ticket_title_font_name"],
                "title_font_sha256": metadata["dy_ticket_title_font_sha256"],
                "body_font": metadata["dy_ticket_body_font_name"],
                "body_font_sha256": metadata["dy_ticket_body_font_sha256"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
