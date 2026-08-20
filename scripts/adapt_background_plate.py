#!/usr/bin/env python3
"""Adapt a material background plate to photo-derived or unified theme colors."""

from __future__ import annotations

import argparse
import colorsys
import json
import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps

from normalize_reference_layout import CANVAS_SIZE
from ticket_layouts import LANDSCAPE, LAYOUT_IDS, get_layout


PALETTE_MODES = ("adaptive", "unified")
ANALYSIS_SIZE = (310, 203)
TARGET_LIGHTNESS = 0.62
MIN_SATURATION = 0.12
MAX_SATURATION = 0.28


def parse_hex(value: str) -> tuple[int, int, int]:
    normalized = value.strip().lstrip("#")
    if len(normalized) != 6:
        raise argparse.ArgumentTypeError("theme color must be a 6-digit RGB hex value")
    try:
        return tuple(int(normalized[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("theme color must be a 6-digit RGB hex value") from exc


def as_hex(color: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def _hls(color: tuple[int, int, int]) -> tuple[float, float, float]:
    return colorsys.rgb_to_hls(*(channel / 255.0 for channel in color))


def _rgb(hue: float, lightness: float, saturation: float) -> tuple[int, int, int]:
    values = colorsys.hls_to_rgb(hue % 1.0, lightness, saturation)
    return tuple(round(channel * 255) for channel in values)


def _candidate_theme_color(
    photo_path: Path,
    center_y: float,
    layout_id: str = LANDSCAPE,
) -> tuple[int, int, int]:
    if not 0.0 <= center_y <= 1.0:
        raise ValueError("photo center_y must be between 0 and 1")
    layout = get_layout(layout_id)
    analysis_size = (
        ANALYSIS_SIZE[0],
        max(64, round(ANALYSIS_SIZE[0] * layout.photo_h / layout.photo_w)),
    )
    with Image.open(photo_path) as photo:
        panel = ImageOps.fit(
            photo.convert("RGB"),
            analysis_size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, center_y),
        )

    quantized = panel.quantize(colors=20, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    if palette is None:
        raise ValueError(f"unable to extract a palette from {photo_path}")

    width, height = quantized.size
    weighted_counts: dict[int, float] = {}
    for y in range(height):
        for x in range(width):
            dx = (x + 0.5) / width - 0.5
            dy = (y + 0.5) / height - 0.5
            center_weight = 0.35 + 1.65 * math.exp(-(dx * dx + dy * dy) / 0.11)
            index = int(quantized.getpixel((x, y)))
            weighted_counts[index] = weighted_counts.get(index, 0.0) + center_weight

    total_weight = sum(weighted_counts.values())
    ranked: list[tuple[float, tuple[int, int, int]]] = []
    for index, weight in weighted_counts.items():
        offset = index * 3
        color = tuple(palette[offset : offset + 3])
        hue, lightness, saturation = _hls(color)
        if not 0.10 < lightness < 0.90:
            continue
        population = weight / total_weight
        chroma_weight = 0.15 + 0.85 * saturation
        midtone_weight = 0.70 + 0.30 * (1.0 - abs(lightness - 0.55) / 0.55)
        ranked.append((population * chroma_weight * midtone_weight, color))

    if not ranked:
        raise ValueError(f"no usable theme color found in {photo_path}")
    return max(ranked, key=lambda item: item[0])[1]


def _hue_distance(left: float, right: float) -> float:
    distance = abs(left - right)
    return min(distance, 1.0 - distance)


def _group_medoid(colors: Iterable[tuple[int, int, int]]) -> tuple[int, int, int]:
    candidates = list(colors)
    if not candidates:
        raise ValueError("at least one source photo is required to derive a unified color")

    profiles = [_hls(color) for color in candidates]

    def distance(index: int) -> float:
        hue, lightness, saturation = profiles[index]
        total = 0.0
        for other_hue, other_lightness, other_saturation in profiles:
            total += (
                _hue_distance(hue, other_hue) * 2.0
                + abs(lightness - other_lightness) * 0.5
                + abs(saturation - other_saturation) * 0.5
            )
        return total

    return candidates[min(range(len(candidates)), key=distance)]


def derive_theme_color(
    source_photos: list[Path],
    center_ys: list[float],
    palette_mode: str,
    layout_id: str = LANDSCAPE,
) -> tuple[tuple[int, int, int], list[tuple[int, int, int]]]:
    get_layout(layout_id)
    if palette_mode not in PALETTE_MODES:
        raise ValueError(f"unknown palette mode: {palette_mode}")
    if not source_photos:
        raise ValueError("at least one source photo is required when --theme-color is omitted")
    if palette_mode == "adaptive" and len(source_photos) != 1:
        raise ValueError("adaptive mode accepts exactly one source photo per background")

    if not center_ys:
        center_ys = [0.5] * len(source_photos)
    elif len(center_ys) == 1 and len(source_photos) > 1:
        center_ys = center_ys * len(source_photos)
    elif len(center_ys) != len(source_photos):
        raise ValueError("provide one --photo-center-y per source photo, or one shared value")

    extracted = [
        _candidate_theme_color(path, center_y, layout_id)
        for path, center_y in zip(source_photos, center_ys)
    ]
    selected = extracted[0] if palette_mode == "adaptive" else _group_medoid(extracted)
    return selected, extracted


def supporting_color(theme_color: tuple[int, int, int]) -> tuple[int, int, int]:
    hue, _lightness, saturation = _hls(theme_color)
    muted_saturation = min(MAX_SATURATION, max(MIN_SATURATION, saturation * 0.70))
    return _rgb(hue, TARGET_LIGHTNESS, muted_saturation)


def adapt_plate(
    plate_path: Path,
    output_path: Path,
    theme_color: tuple[int, int, int],
) -> tuple[int, int, int]:
    with Image.open(plate_path) as plate:
        plate = plate.convert("RGB")
    if plate.size != CANVAS_SIZE:
        raise ValueError(
            f"background plate must be exactly {CANVAS_SIZE[0]} x {CANVAS_SIZE[1]}, got {plate.size}"
        )

    base = supporting_color(theme_color)
    hue, lightness, saturation = _hls(base)
    dark = _rgb(hue, 0.14, saturation * 0.90)
    light = _rgb(hue, 0.96, saturation * 0.45)

    gray = ImageOps.grayscale(plate)
    safe_sample = gray.crop((100, 100, 700, 450)).resize((60, 35))
    midpoint = sorted(safe_sample.getdata())[len(safe_sample.getdata()) // 2]
    recolored = ImageOps.colorize(
        gray,
        black=dark,
        mid=base,
        white=light,
        blackpoint=0,
        whitepoint=255,
        midpoint=midpoint,
    ).convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    recolored.save(output_path, format="PNG", compress_level=6)
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--palette-mode", choices=PALETTE_MODES, default="adaptive")
    parser.add_argument("--source-photo", type=Path, action="append", default=[])
    parser.add_argument("--photo-center-y", type=float, action="append", default=[])
    parser.add_argument("--theme-color", type=parse_hex)
    parser.add_argument("--layout", choices=LAYOUT_IDS, default=LANDSCAPE)
    args = parser.parse_args()

    extracted: list[tuple[int, int, int]] = []
    if args.theme_color is not None:
        selected = args.theme_color
    else:
        selected, extracted = derive_theme_color(
            args.source_photo,
            args.photo_center_y,
            args.palette_mode,
            args.layout,
        )
    base = adapt_plate(args.plate, args.output, selected)
    print(
        json.dumps(
            {
                "status": "ok",
                "palette_mode": args.palette_mode,
                "source_theme_colors": [as_hex(color) for color in extracted],
                "selected_theme_color": as_hex(selected),
                "supporting_background_color": as_hex(base),
                "output": str(args.output.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
