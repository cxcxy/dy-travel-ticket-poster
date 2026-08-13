#!/usr/bin/env python3
"""Replace the canvas color and rebuild its canonical, palette-aware shadow."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, PngImagePlugin

from normalize_reference_layout import (
    CANVAS_SIZE,
    TICKET_H,
    TICKET_W,
    TICKET_X,
    TICKET_Y,
    apply_ticket_shadow,
    build_background,
    draw_single_perforation,
    make_ticket_mask,
)
from palette_utils import parse_canvas_color
from palette_utils import rgb_to_hex


def recolor(input_path: Path, output_path: Path, color: tuple[int, int, int]) -> None:
    with Image.open(input_path) as opened:
        metadata = {
            key: value for key, value in opened.info.items() if isinstance(value, str)
        }
        source = opened.convert("RGB")
    if source.size != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {source.size}")

    ticket = source.crop(
        (TICKET_X, TICKET_Y, TICKET_X + TICKET_W, TICKET_Y + TICKET_H)
    )
    # The divider is a visual cut through to the canvas. Repaint it whenever
    # the canvas changes so an old warm or cool divider cannot contaminate the
    # new palette.
    draw_single_perforation(ticket, color)
    mask = make_ticket_mask()
    background = build_background(color)

    apply_ticket_shadow(background, mask, color)
    background.paste(ticket, (TICKET_X, TICKET_Y), mask)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")
    metadata["dy_ticket_background"] = rgb_to_hex(color)
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
    parser.add_argument("--background-color", type=parse_canvas_color, required=True)
    args = parser.parse_args()
    recolor(args.input, args.output, args.background_color)


if __name__ == "__main__":
    main()
