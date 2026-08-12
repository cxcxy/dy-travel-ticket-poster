#!/usr/bin/env python3
"""Replace only the outer canvas background of an approved ticket poster."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from normalize_reference_layout import (
    CANVAS_SIZE,
    TICKET_H,
    TICKET_W,
    TICKET_X,
    TICKET_Y,
    apply_ticket_shadow,
    build_background,
    make_ticket_mask,
    parse_color,
)


def recolor(input_path: Path, output_path: Path, color: tuple[int, int, int]) -> None:
    source = Image.open(input_path).convert("RGB")
    if source.size != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {source.size}")

    ticket = source.crop(
        (TICKET_X, TICKET_Y, TICKET_X + TICKET_W, TICKET_Y + TICKET_H)
    )
    mask = make_ticket_mask()
    background = build_background(color)

    apply_ticket_shadow(background, mask)
    background.paste(ticket, (TICKET_X, TICKET_Y), mask)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")
    background.save(output_path, format="PNG", compress_level=6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--background-color", type=parse_color, required=True)
    args = parser.parse_args()
    recolor(args.input, args.output, args.background_color)


if __name__ == "__main__":
    main()
