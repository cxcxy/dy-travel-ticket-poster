#!/usr/bin/env python3
"""Small, dependency-free color helpers for the ticket-poster scripts."""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable


RGB = tuple[int, int, int]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_hex_color(value: str) -> RGB:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise argparse.ArgumentTypeError("color must be a 6-digit RGB hex value")
    try:
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "color must be a 6-digit RGB hex value"
        ) from exc


def rgb_to_hex(color: RGB) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def parse_canvas_color(value: str) -> RGB:
    color = parse_hex_color(value)
    _, lightness, saturation = colorsys.rgb_to_hls(
        *(channel / 255.0 for channel in color)
    )
    if lightness < 0.08:
        raise argparse.ArgumentTypeError(
            "canvas color is too close to black for reliable ticket shadows"
        )
    return color


def _srgb_to_linear(value: float) -> float:
    value /= 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(value: float) -> float:
    if value <= 0.0031308:
        encoded = 12.92 * value
    else:
        encoded = 1.055 * (max(value, 0.0) ** (1.0 / 2.4)) - 0.055
    return encoded * 255.0


def rgb_to_oklab(color: RGB) -> tuple[float, float, float]:
    red, green, blue = (_srgb_to_linear(channel) for channel in color)
    l_value = 0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue
    m_value = 0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue
    s_value = 0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue

    l_root = math.copysign(abs(l_value) ** (1.0 / 3.0), l_value)
    m_root = math.copysign(abs(m_value) ** (1.0 / 3.0), m_value)
    s_root = math.copysign(abs(s_value) ** (1.0 / 3.0), s_value)
    return (
        0.2104542553 * l_root + 0.7936177850 * m_root - 0.0040720468 * s_root,
        1.9779984951 * l_root - 2.4285922050 * m_root + 0.4505937099 * s_root,
        0.0259040371 * l_root + 0.7827717662 * m_root - 0.8086757660 * s_root,
    )


def oklab_to_rgb_unclipped(l_value: float, a_value: float, b_value: float) -> tuple[float, float, float]:
    l_root = l_value + 0.3963377774 * a_value + 0.2158037573 * b_value
    m_root = l_value - 0.1055613458 * a_value - 0.0638541728 * b_value
    s_root = l_value - 0.0894841775 * a_value - 1.2914855480 * b_value
    l_linear = l_root**3
    m_linear = m_root**3
    s_linear = s_root**3
    red = +4.0767416621 * l_linear - 3.3077115913 * m_linear + 0.2309699292 * s_linear
    green = -1.2684380046 * l_linear + 2.6097574011 * m_linear - 0.3413193965 * s_linear
    blue = -0.0041960863 * l_linear - 0.7034186147 * m_linear + 1.7076147010 * s_linear
    return tuple(_linear_to_srgb(channel) for channel in (red, green, blue))


def rgb_to_oklch(color: RGB) -> tuple[float, float, float]:
    l_value, a_value, b_value = rgb_to_oklab(color)
    chroma = math.hypot(a_value, b_value)
    hue = math.degrees(math.atan2(b_value, a_value)) % 360.0
    return l_value, chroma, hue


def oklch_to_rgb(l_value: float, chroma: float, hue: float) -> RGB:
    """Convert OKLCH to in-gamut sRGB by reducing chroma when necessary."""
    hue_radians = math.radians(hue)
    current_chroma = max(0.0, chroma)
    for _ in range(40):
        values = oklab_to_rgb_unclipped(
            l_value,
            current_chroma * math.cos(hue_radians),
            current_chroma * math.sin(hue_radians),
        )
        if all(-0.001 <= channel <= 255.001 for channel in values):
            return tuple(max(0, min(255, round(channel))) for channel in values)
        current_chroma *= 0.92
    values = oklab_to_rgb_unclipped(l_value, 0.0, 0.0)
    return tuple(max(0, min(255, round(channel))) for channel in values)


def delta_ok(color_a: RGB, color_b: RGB) -> float:
    lab_a = rgb_to_oklab(color_a)
    lab_b = rgb_to_oklab(color_b)
    return math.sqrt(sum((first - second) ** 2 for first, second in zip(lab_a, lab_b)))


def relative_luminance(color: RGB) -> float:
    red, green, blue = (_srgb_to_linear(channel) for channel in color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(color_a: RGB, color_b: RGB) -> float:
    lighter, darker = sorted(
        (relative_luminance(color_a), relative_luminance(color_b)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def hue_distance(first: float, second: float) -> float:
    difference = abs(first - second) % 360.0
    return min(difference, 360.0 - difference)


def mix_colors(first: RGB, second: RGB, second_weight: float) -> RGB:
    weight = max(0.0, min(1.0, second_weight))
    return tuple(
        round(channel_a * (1.0 - weight) + channel_b * weight)
        for channel_a, channel_b in zip(first, second)
    )


def median_color(colors: Iterable[RGB]) -> RGB:
    values = list(colors)
    if not values:
        raise ValueError("cannot calculate a median color from an empty sequence")
    channels = list(zip(*values))
    return tuple(sorted(channel)[len(channel) // 2] for channel in channels)


def load_palette_candidate(
    path: Path,
    candidate_id: str,
    source_path: Path | None = None,
    photo_center_y: float | None = None,
    strip_neutral_borders: bool | None = None,
    layout_id: str | None = None,
) -> tuple[RGB, RGB, RGB]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if source_path is not None:
        recorded_source = data.get("source")
        if not recorded_source or Path(recorded_source).resolve() != source_path.resolve():
            raise ValueError(
                f"palette provenance mismatch: {path} was not generated for {source_path.resolve()}"
            )
        if data.get("source_sha256") != file_sha256(source_path):
            raise ValueError(
                "palette provenance mismatch: source content changed after palette generation"
            )
    if photo_center_y is not None:
        recorded_center = data.get("photo_center_y")
        if recorded_center is None or abs(float(recorded_center) - photo_center_y) > 1e-9:
            raise ValueError(
                "palette crop mismatch: regenerate the palette with the same --photo-center-y"
            )
    if strip_neutral_borders is not None:
        recorded_strip = bool(data.get("strip_neutral_borders", True))
        if recorded_strip != strip_neutral_borders:
            raise ValueError(
                "palette border-preparation mismatch: regenerate with matching border handling"
            )
    if layout_id is not None:
        recorded_layout = data.get("layout", "landscape")
        if recorded_layout != layout_id:
            raise ValueError(
                "palette layout mismatch: regenerate the palette with matching --layout"
            )
    for candidate in data.get("candidates", []):
        if candidate.get("id") == candidate_id:
            return tuple(
                parse_hex_color(candidate[key])
                for key in ("background", "stub", "text")
            )
    raise ValueError(f'palette candidate "{candidate_id}" not found in {path}')
