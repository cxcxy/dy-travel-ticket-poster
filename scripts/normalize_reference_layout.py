#!/usr/bin/env python3
"""Normalize a generated ticket poster to the user's measured reference layout."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps, PngImagePlugin

from image_utils import open_prepared_source
from palette_utils import (
    file_sha256,
    mix_colors,
    parse_canvas_color,
    parse_hex_color,
    rgb_to_hex,
)


CANVAS_SIZE = (1170, 1560)
TICKET_X = 55  # 4.7% of canvas width
TICKET_Y = 501  # 32.1% of canvas height
TICKET_W = 1057  # right edge at 95.0% of canvas width
TICKET_H = 507  # bottom edge at 64.6% of canvas height
PHOTO_W = 774  # 73.2% of ticket width
STUB_W = TICKET_W - PHOTO_W
CORNER_RADIUS = 15
NOTCH_RADIUS = 43
PERFORATION_COLOR = (235, 229, 210)
PERFORATION_W = 7
PERFORATION_DASH_H = 14
PERFORATION_GAP = 12
PERFORATION_GUARD_W = 20

AMBIENT_SHADOW_OFFSET = (2, 12)
AMBIENT_SHADOW_BLUR = 26
AMBIENT_SHADOW_OPACITY = 52
CONTACT_SHADOW_OFFSET = (3, 5)
CONTACT_SHADOW_BLUR = 8
CONTACT_SHADOW_OPACITY = 38


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = tuple(int(item) for item in value.split(","))
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox must be x1,y1,x2,y2")
    return parts


def parse_color(value: str) -> tuple[int, int, int]:
    """Backward-compatible argparse color parser used by sibling scripts."""
    return parse_hex_color(value)


def build_background(color: tuple[int, int, int]) -> Image.Image:
    """Build the quiet, flat adaptive background required by the Skill."""
    return Image.new("RGB", CANVAS_SIZE, color)


def make_ticket_mask() -> Image.Image:
    mask = Image.new("L", (TICKET_W, TICKET_H), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        (0, 0, TICKET_W - 1, TICKET_H - 1),
        radius=CORNER_RADIUS,
        fill=255,
    )
    center_y = TICKET_H // 2
    draw.ellipse(
        (
            TICKET_W - NOTCH_RADIUS,
            center_y - NOTCH_RADIUS,
            TICKET_W + NOTCH_RADIUS,
            center_y + NOTCH_RADIUS,
        ),
        fill=0,
    )
    return mask


def clean_stub_leading_edge(stub: Image.Image) -> Image.Image:
    """Remove any generated divider before drawing the one canonical perforation."""
    cleaned = stub.copy()
    sample_x1 = PERFORATION_GUARD_W + 8
    sample_x2 = min(sample_x1 + 24, stub.width)
    upper = stub.crop((sample_x1, 0, sample_x2, min(96, stub.height)))
    lower = stub.crop(
        (sample_x1, max(0, stub.height - 96), sample_x2, stub.height)
    )
    # Median suppresses text and generated perforation highlights while preserving stub color.
    # getdata() is supported across the Pillow versions used by Agent hosts;
    # get_flattened_data() is not available in Pillow 11.x.
    samples = list(upper.getdata()) + list(lower.getdata())
    channels = list(zip(*samples))
    fill = tuple(sorted(channel)[len(channel) // 2] for channel in channels)
    ImageDraw.Draw(cleaned).rectangle(
        (0, 0, PERFORATION_GUARD_W - 1, stub.height - 1),
        fill=fill,
    )
    return cleaned


def draw_single_perforation(
    ticket: Image.Image,
    color: tuple[int, int, int] = PERFORATION_COLOR,
) -> None:
    """Draw one square-ended divider, flush and square at the ticket top."""
    draw = ImageDraw.Draw(ticket)
    x1 = PHOTO_W - PERFORATION_W // 2
    x2 = x1 + PERFORATION_W - 1
    step = PERFORATION_DASH_H + PERFORATION_GAP
    for dash_y in range(0, TICKET_H, step):
        draw.rectangle(
            (x1, dash_y, x2, min(dash_y + PERFORATION_DASH_H - 1, TICKET_H - 1)),
            fill=color,
        )


def apply_ticket_shadow(
    background: Image.Image,
    mask: Image.Image,
    background_color: tuple[int, int, int] | None = None,
) -> None:
    """Render a grounded two-stage shadow without creating a second card edge."""
    if background_color is None:
        background_color = background.getpixel((0, 0))
    # Tie the shadow to the canvas hue instead of imposing a warm-black cast on
    # every cool or saturated palette.
    shadow_color = mix_colors(background_color, (19, 20, 21), 0.72)
    for offset, blur, opacity in (
        (AMBIENT_SHADOW_OFFSET, AMBIENT_SHADOW_BLUR, AMBIENT_SHADOW_OPACITY),
        (CONTACT_SHADOW_OFFSET, CONTACT_SHADOW_BLUR, CONTACT_SHADOW_OPACITY),
    ):
        shadow_mask = Image.new("L", CANVAS_SIZE, 0)
        shadow_mask.paste(mask, (TICKET_X + offset[0], TICKET_Y + offset[1]))
        shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(blur))
        shadow = Image.new("RGB", CANVAS_SIZE, shadow_color)
        background.paste(
            shadow,
            (0, 0),
            shadow_mask.point(lambda value, alpha=opacity: value * alpha // 255),
        )


def normalize(
    input_path: Path,
    output_path: Path,
    bbox: tuple[int, int, int, int],
    split_x: int,
    photo_source_path: Path | None,
    photo_center_y: float,
    background_color: tuple[int, int, int],
    perforation_color: tuple[int, int, int] | None = None,
    strip_neutral_borders: bool = True,
) -> None:
    with Image.open(input_path) as opened:
        metadata = {
            key: value for key, value in opened.info.items() if isinstance(value, str)
        }
        source = ImageOps.exif_transpose(opened).convert("RGB")
    x1, y1, x2, y2 = bbox
    if not (0 <= x1 < split_x < x2 <= source.width and 0 <= y1 < y2 <= source.height):
        raise ValueError("bbox or split-x falls outside the source image")

    if photo_source_path is None:
        photo = source.crop((x1, y1, split_x, y2))
    else:
        photo = open_prepared_source(photo_source_path, strip_neutral_borders)
    stub = source.crop((split_x, y1, x2, y2))

    photo = ImageOps.fit(
        photo,
        (PHOTO_W, TICKET_H),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, photo_center_y),
    )
    stub = ImageOps.fit(
        stub,
        (STUB_W, TICKET_H),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    stub = clean_stub_leading_edge(stub)

    ticket = Image.new("RGB", (TICKET_W, TICKET_H))
    ticket.paste(photo, (0, 0))
    ticket.paste(stub, (PHOTO_W, 0))
    draw_single_perforation(ticket, perforation_color or background_color)

    background = build_background(background_color)
    mask = make_ticket_mask()

    apply_ticket_shadow(background, mask, background_color)

    background.paste(ticket, (TICKET_X, TICKET_Y), mask)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")
    if photo_source_path is not None and metadata.get("dy_ticket_renderer") == "1":
        metadata["dy_ticket_source_sha256"] = file_sha256(photo_source_path)
        metadata["dy_ticket_photo_center_y"] = f"{photo_center_y:.9f}"
        metadata["dy_ticket_strip_neutral_borders"] = (
            "1" if strip_neutral_borders else "0"
        )
        metadata["dy_ticket_background"] = rgb_to_hex(background_color)
    png_info = PngImagePlugin.PngInfo()
    for key, value in metadata.items():
        png_info.add_text(key, value)
    background.save(
        output_path,
        format="PNG",
        compress_level=6,
        pnginfo=png_info,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bbox", type=parse_box, required=True)
    parser.add_argument("--split-x", type=int, required=True)
    parser.add_argument("--photo-source", type=Path)
    parser.add_argument(
        "--allow-generated-photo",
        action="store_true",
        help="Explicitly allow using the generated photo panel instead of original pixels",
    )
    parser.add_argument("--photo-center-y", type=float, default=0.5)
    parser.add_argument(
        "--background-color",
        type=parse_canvas_color,
        required=True,
        help="Visually approved RGB hex color derived from the source photograph",
    )
    parser.add_argument(
        "--perforation-color",
        type=parse_color,
        help="Divider color; defaults to the exact canvas color",
    )
    parser.add_argument(
        "--keep-neutral-borders",
        action="store_true",
        help="Preserve intentional solid white/black framing at the photo edge",
    )
    args = parser.parse_args()
    if not 0.0 <= args.photo_center_y <= 1.0:
        parser.error("--photo-center-y must be between 0 and 1")
    if args.photo_source is None and not args.allow_generated_photo:
        parser.error(
            "--photo-source is required for source-photo fidelity; "
            "use --allow-generated-photo only for an intentional exception"
        )
    normalize(
        args.input,
        args.output,
        args.bbox,
        args.split_x,
        args.photo_source,
        args.photo_center_y,
        args.background_color,
        args.perforation_color,
        not args.keep_neutral_borders,
    )


if __name__ == "__main__":
    main()
