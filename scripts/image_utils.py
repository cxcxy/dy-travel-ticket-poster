#!/usr/bin/env python3
"""Shared, conservative image preparation for source-faithful ticket crops."""

from __future__ import annotations

from PIL import Image, ImageOps


CONNECTED_BORDER_LIMIT = 0.12


def strip_connected_neutral_borders(image: Image.Image) -> Image.Image:
    """Remove only solid, edge-connected white or black framing bars."""
    current = image
    for _ in range(2):
        width, height = current.size
        if width < 16 or height < 16:
            break
        maximum_x = max(1, round(width * CONNECTED_BORDER_LIMIT))
        maximum_y = max(1, round(height * CONNECTED_BORDER_LIMIT))

        def neutral_ratio(box: tuple[int, int, int, int]) -> float:
            pixels = list(current.crop(box).resize((1, 32)).getdata())
            neutral = sum(
                1
                for red, green, blue in pixels
                if (max(red, green, blue) <= 32 or min(red, green, blue) >= 225)
                and max(red, green, blue) - min(red, green, blue) <= 30
            ) / len(pixels)
            channel_spread = max(
                max(channel) - min(channel) for channel in zip(*pixels)
            )
            return neutral if channel_spread <= 14 else 0.0

        left = 0
        while left < maximum_x and neutral_ratio((left, 0, left + 1, height)) >= 0.90:
            left += 1
        right = width
        while right > width - maximum_x and neutral_ratio((right - 1, 0, right, height)) >= 0.90:
            right -= 1
        top = 0
        while top < maximum_y and neutral_ratio((0, top, width, top + 1)) >= 0.90:
            top += 1
        bottom = height
        while bottom > height - maximum_y and neutral_ratio((0, bottom - 1, width, bottom)) >= 0.90:
            bottom -= 1
        if (left, top, right, bottom) == (0, 0, width, height):
            break
        current = current.crop((left, top, right, bottom))
    return current


def open_prepared_source(path, strip_neutral_borders: bool = True) -> Image.Image:
    with Image.open(path) as opened:
        oriented = ImageOps.exif_transpose(opened)
        if "A" in oriented.getbands() or "transparency" in oriented.info:
            # Composite only visible pixels. Hidden RGB values under alpha must
            # never leak into the crop or palette (a common transparent-PNG
            # failure mode). The warm-white backing is excluded by palette
            # lightness filters and is often removed as connected framing.
            rgba = oriented.convert("RGBA")
            backing = Image.new("RGBA", rgba.size, (244, 240, 229, 255))
            source = Image.alpha_composite(backing, rgba).convert("RGB")
        else:
            source = oriented.convert("RGB")
    return strip_connected_neutral_borders(source) if strip_neutral_borders else source
