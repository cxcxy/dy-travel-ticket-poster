#!/usr/bin/env python3
"""Build the default photo-main-colour background with fine matte paper texture."""

from __future__ import annotations

import argparse
import colorsys
import json
import random
from pathlib import Path

from PIL import Image, ImageFilter

from adapt_background_plate import (
    PALETTE_MODES,
    as_hex,
    derive_theme_color,
    parse_hex,
)
from normalize_reference_layout import CANVAS_SIZE


DEFAULT_SEED = 40817
DEFAULT_TEXTURE_STRENGTH = 2
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--palette-mode", choices=PALETTE_MODES, default="adaptive")
    parser.add_argument("--source-photo", type=Path, action="append", default=[])
    parser.add_argument("--photo-center-y", type=float, action="append", default=[])
    parser.add_argument("--theme-color", type=parse_hex)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--texture-strength",
        type=int,
        choices=range(1, 6),
        default=DEFAULT_TEXTURE_STRENGTH,
    )
    args = parser.parse_args()

    extracted: list[tuple[int, int, int]] = []
    if args.theme_color is not None:
        selected = args.theme_color
    else:
        selected, extracted = derive_theme_color(
            args.source_photo,
            args.photo_center_y,
            args.palette_mode,
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
                "treatment": "photo-main-colour-fine-matte-paper",
                "palette_mode": args.palette_mode,
                "source_theme_colors": [as_hex(color) for color in extracted],
                "selected_theme_color": as_hex(selected),
                "supporting_background_color": as_hex(base),
                "texture_strength": args.texture_strength,
                "seed": args.seed,
                "output": str(args.output.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
