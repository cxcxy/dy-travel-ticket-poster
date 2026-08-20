#!/usr/bin/env python3
"""Build the default photo-main-colour background with fine matte paper texture."""

from __future__ import annotations

import argparse
import colorsys
import json
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from adapt_background_plate import (
    PALETTE_MODES,
    as_hex,
    derive_theme_color,
    parse_hex,
)
from normalize_reference_layout import CANVAS_SIZE
from portrait_reference_style import PORTRAIT_REFERENCE_BACKGROUND
from ticket_layouts import LANDSCAPE, LAYOUT_IDS, PORTRAIT


DEFAULT_SEED = 40817
DEFAULT_TEXTURE_STRENGTH = 2
BACKGROUND_TREATMENTS = ("auto", "photo-matte", "portrait-reference-linen")
PORTRAIT_REFERENCE_COLOR = PORTRAIT_REFERENCE_BACKGROUND  # Backward-compatible export.
SATURATION_SCALE = 0.72
MIN_LIGHTNESS = 0.46
MAX_LIGHTNESS = 0.68
MIN_SATURATION = 0.16
MAX_SATURATION = 0.56


def supporting_color(theme_color: tuple[int, int, int]) -> tuple[int, int, int]:
    """Retain the photograph's colour identity, softened for a quiet backdrop."""
    hue, lightness, saturation = colorsys.rgb_to_hls(
        *(channel / 255.0 for channel in theme_color)
    )
    softened_saturation = min(MAX_SATURATION, max(MIN_SATURATION, saturation * SATURATION_SCALE))
    softened_lightness = min(MAX_LIGHTNESS, max(MIN_LIGHTNESS, lightness))
    values = colorsys.hls_to_rgb(hue, softened_lightness, softened_saturation)
    return tuple(round(channel * 255) for channel in values)


def build_subtle_background(
    output_path: Path,
    theme_color: tuple[int, int, int],
    seed: int = DEFAULT_SEED,
    texture_strength: int = DEFAULT_TEXTURE_STRENGTH,
) -> tuple[int, int, int]:
    if not 1 <= texture_strength <= 5:
        raise ValueError("texture_strength must be between 1 and 5")

    base = supporting_color(theme_color)
    width, height = CANVAS_SIZE
    rng = random.Random(seed)

    fine_size = (width // 2, height // 2)
    # Fine, low-contrast tooth keeps the field matte and tactile without
    # introducing visible noise, fibres, gradients, or directional light.
    fine = Image.frombytes(
        "L",
        fine_size,
        bytes(
            rng.randint(128 - texture_strength, 128 + texture_strength)
            for _ in range(fine_size[0] * fine_size[1])
        ),
    ).resize(CANVAS_SIZE, Image.Resampling.LANCZOS)

    broad_size = (65, 87)
    broad = Image.frombytes(
        "L",
        broad_size,
        bytes(
            rng.randint(127, 129)
            for _ in range(broad_size[0] * broad_size[1])
        ),
    ).resize(CANVAS_SIZE, Image.Resampling.BICUBIC).filter(
        ImageFilter.GaussianBlur(radius=18)
    )
    texture = Image.blend(fine, broad, 0.22)
    texture = texture.point(
        lambda value: max(
            128 - texture_strength,
            min(128 + texture_strength, value),
        )
    )

    channels = []
    for channel in base:
        channels.append(
            texture.point(
                lambda value, base_channel=channel: max(
                    0, min(255, base_channel + value - 128)
                )
            )
        )
    background = Image.merge("RGB", channels)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    background.save(output_path, format="PNG", compress_level=6)
    return base


def resolve_background_treatment(
    requested: str,
    layout_id: str,
    palette_mode: str,
    theme_color: tuple[int, int, int] | None,
) -> str:
    """Resolve the default without preventing any explicit background choice."""
    if requested not in BACKGROUND_TREATMENTS:
        raise ValueError(f"unknown background treatment: {requested}")
    if requested != "auto":
        return requested
    if (
        layout_id == PORTRAIT
        and palette_mode == "adaptive"
        and theme_color is None
    ):
        return "portrait-reference-linen"
    return "photo-matte"


def build_portrait_reference_background(
    output_path: Path,
    seed: int = DEFAULT_SEED,
    base: tuple[int, int, int] = PORTRAIT_REFERENCE_BACKGROUND,
) -> tuple[int, int, int]:
    """Build the olive woven-fabric backdrop measured from the portrait reference."""
    width, height = CANVAS_SIZE
    rng = random.Random(seed)

    # Measured from exposed reference areas: the upper-left sits roughly
    # 18-20 levels above the colour anchor, while the lower-right sits about
    # 16-18 below it. The horizontal falloff is stronger than the vertical
    # one; a weak diagonal gradient makes the fabric look flat and synthetic.
    shade_size = (65, 87)
    shade_values = []
    for y_pos in range(shade_size[1]):
        y_ratio = y_pos / (shade_size[1] - 1)
        for x_pos in range(shade_size[0]):
            x_ratio = x_pos / (shade_size[0] - 1)
            shade_values.append(round(148 - 23 * x_ratio - 15 * y_ratio))
    shade = Image.frombytes("L", shade_size, bytes(shade_values)).resize(
        CANVAS_SIZE,
        Image.Resampling.BICUBIC,
    ).filter(ImageFilter.GaussianBlur(radius=10))

    # The reference has 4-5 px thread spacing, but it is not a perfect screen
    # grid. Build the warp and weft separately with alternating highlight,
    # trough and shoulder values, then vary their segment brightness and
    # spacing. This gives each yarn a rounded cross-section and avoids a
    # repeated digital checkerboard.
    warp = Image.new("L", CANVAS_SIZE, 128)
    warp_draw = ImageDraw.Draw(warp)
    x_pos = -rng.randint(0, 4)
    while x_pos < width:
        segment_y = 0
        while segment_y < height:
            segment_h = rng.randint(42, 92)
            jitter = rng.choices((-1, 0, 1), weights=(1, 10, 1), k=1)[0]
            light = rng.randint(136, 142)
            dark = rng.randint(117, 123)
            shoulder = rng.randint(125, 130)
            x_thread = x_pos + jitter
            if 0 <= x_thread < width:
                warp_draw.line(
                    (x_thread, segment_y, x_thread, min(height, segment_y + segment_h)),
                    fill=light,
                    width=1,
                )
            if 0 <= x_thread + 1 < width:
                warp_draw.line(
                    (x_thread + 1, segment_y, x_thread + 1, min(height, segment_y + segment_h)),
                    fill=dark,
                    width=1,
                )
            if 0 <= x_thread + 2 < width:
                warp_draw.line(
                    (x_thread + 2, segment_y, x_thread + 2, min(height, segment_y + segment_h)),
                    fill=shoulder,
                    width=1,
                )
            segment_y += segment_h
        x_pos += rng.choice((4, 4, 5, 5, 5))

    weft = Image.new("L", CANVAS_SIZE, 128)
    weft_draw = ImageDraw.Draw(weft)
    y_pos = -rng.randint(0, 4)
    while y_pos < height:
        segment_x = 0
        while segment_x < width:
            segment_w = rng.randint(44, 104)
            jitter = rng.choices((-1, 0, 1), weights=(1, 10, 1), k=1)[0]
            light = rng.randint(139, 145)
            dark = rng.randint(111, 118)
            shoulder = rng.randint(123, 130)
            y_thread = y_pos + jitter
            if 0 <= y_thread < height:
                weft_draw.line(
                    (segment_x, y_thread, min(width, segment_x + segment_w), y_thread),
                    fill=light,
                    width=1,
                )
            if 0 <= y_thread + 1 < height:
                weft_draw.line(
                    (segment_x, y_thread + 1, min(width, segment_x + segment_w), y_thread + 1),
                    fill=dark,
                    width=1,
                )
            if 0 <= y_thread + 2 < height:
                weft_draw.line(
                    (segment_x, y_thread + 2, min(width, segment_x + segment_w), y_thread + 2),
                    fill=shoulder,
                    width=1,
                )
            segment_x += segment_w
        y_pos += rng.choice((4, 4, 5, 5))

    weave = ImageChops.add(warp, weft, scale=1.0, offset=-128)
    weave = Image.blend(
        Image.new("L", CANVAS_SIZE, 128),
        weave,
        0.78,
    ).filter(ImageFilter.GaussianBlur(radius=0.25))

    fine_size = (width // 2, height // 2)
    fine = Image.frombytes(
        "L",
        fine_size,
        bytes(rng.randint(123, 133) for _ in range(fine_size[0] * fine_size[1])),
    ).resize(CANVAS_SIZE, Image.Resampling.LANCZOS)
    texture = ImageChops.add(shade, weave, scale=1.0, offset=-128)
    texture = ImageChops.add(texture, fine, scale=1.0, offset=-128)

    channels = [
        texture.point(
            lambda value, base_channel=channel: max(
                0,
                min(255, base_channel + value - 128),
            )
        )
        for channel in base
    ]
    background = Image.merge("RGB", channels)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    background.save(output_path, format="PNG", compress_level=6)
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--palette-mode", choices=PALETTE_MODES, default="adaptive")
    parser.add_argument("--source-photo", type=Path, action="append", default=[])
    parser.add_argument("--photo-center-y", type=float, action="append", default=[])
    parser.add_argument("--theme-color", type=parse_hex)
    parser.add_argument("--layout", choices=LAYOUT_IDS, default=LANDSCAPE)
    parser.add_argument(
        "--background-treatment",
        choices=BACKGROUND_TREATMENTS,
        default="auto",
        help="auto uses olive woven fabric for portrait and photo-derived matte paper for landscape",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--texture-strength",
        type=int,
        choices=range(1, 6),
        default=DEFAULT_TEXTURE_STRENGTH,
    )
    args = parser.parse_args()

    treatment = resolve_background_treatment(
        args.background_treatment,
        args.layout,
        args.palette_mode,
        args.theme_color,
    )
    extracted: list[tuple[int, int, int]] = []
    if treatment == "portrait-reference-linen":
        selected = PORTRAIT_REFERENCE_BACKGROUND
        base = build_portrait_reference_background(
            args.output,
            seed=args.seed,
        )
    else:
        if args.theme_color is not None:
            selected = args.theme_color
        else:
            selected, extracted = derive_theme_color(
                args.source_photo,
                args.photo_center_y,
                args.palette_mode,
                args.layout,
            )
        base = build_subtle_background(
            args.output,
            selected,
            seed=args.seed,
            texture_strength=args.texture_strength,
        )
    print(
        json.dumps(
            {
                "status": "ok",
                "treatment": treatment,
                "palette_mode": args.palette_mode,
                "layout": args.layout,
                "source_theme_colors": [as_hex(color) for color in extracted],
                "selected_theme_color": as_hex(selected),
                "supporting_background_color": as_hex(base),
                "reference_color": (
                    as_hex(PORTRAIT_REFERENCE_COLOR)
                    if treatment == "portrait-reference-linen"
                    else None
                ),
                "texture_strength": (
                    args.texture_strength if treatment == "photo-matte" else None
                ),
                "seed": args.seed,
                "output": str(args.output.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
