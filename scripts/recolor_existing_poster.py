#!/usr/bin/env python3
"""Replace the canvas color and rebuild its canonical, palette-aware shadow."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, PngImagePlugin

from normalize_reference_layout import (
    CANVAS_SIZE,
    apply_ticket_shadow,
    build_background,
    draw_single_perforation,
    make_ticket_mask,
)
from palette_utils import parse_canvas_color
from palette_utils import rgb_to_hex
from ticket_layouts import (
    LANDSCAPE,
    PORTRAIT,
    draw_portrait_perforation,
    get_layout,
    make_portrait_ticket_mask,
)


def recolor(input_path: Path, output_path: Path, color: tuple[int, int, int]) -> None:
    with Image.open(input_path) as opened:
        metadata = {
            key: value for key, value in opened.info.items() if isinstance(value, str)
        }
        source = opened.convert("RGB")
    if source.size != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {source.size}")

    layout_id = metadata.get("dy_ticket_layout", LANDSCAPE)
    layout = get_layout(layout_id)

    ticket = source.crop(
        (
            layout.ticket_x,
            layout.ticket_y,
            layout.ticket_x + layout.ticket_w,
            layout.ticket_y + layout.ticket_h,
        )
    )
    # The divider is a visual cut through to the canvas. Repaint it whenever
    # the canvas changes so an old warm or cool divider cannot contaminate the
    # new palette.
    if layout_id == PORTRAIT:
        draw_portrait_perforation(ticket, color, layout)
        mask = make_portrait_ticket_mask(layout)
    else:
        draw_single_perforation(ticket, color)
        mask = make_ticket_mask()
    background = build_background(color)

    recorded_shadow = metadata.get("dy_ticket_shadow_preset", "default")
    shadow_preset = None if recorded_shadow == "default" else recorded_shadow
    apply_ticket_shadow(
        background,
        mask,
        color,
        shadow_preset,
        (layout.ticket_x, layout.ticket_y),
    )
    background.paste(ticket, (layout.ticket_x, layout.ticket_y), mask)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")
    metadata["dy_ticket_background"] = rgb_to_hex(color)
    if metadata.get("dy_ticket_renderer") == "2":
        metadata["dy_ticket_background_source"] = "color"
        metadata["dy_ticket_background_image_sha256"] = ""
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
