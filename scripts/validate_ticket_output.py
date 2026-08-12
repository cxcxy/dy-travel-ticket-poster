#!/usr/bin/env python3
"""Validate source-photo fidelity and the canonical ticket separator geometry."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

from normalize_reference_layout import (
    CANVAS_SIZE,
    PERFORATION_COLOR,
    PERFORATION_DASH_H,
    PERFORATION_GAP,
    PERFORATION_GUARD_W,
    PERFORATION_W,
    PHOTO_W,
    TICKET_H,
    TICKET_X,
    TICKET_Y,
)


def validate(
    output_path: Path,
    source_path: Path,
    photo_center_y: float,
) -> None:
    output = Image.open(output_path).convert("RGB")
    if output.size != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {output.size}")

    source = Image.open(source_path).convert("RGB")
    expected = ImageOps.fit(
        source,
        (PHOTO_W, TICKET_H),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, photo_center_y),
    )
    actual = output.crop(
        (TICKET_X, TICKET_Y, TICKET_X + PHOTO_W, TICKET_Y + TICKET_H)
    )
    safe_expected = expected.crop((16, 16, PHOTO_W - 9, TICKET_H - 16))
    safe_actual = actual.crop((16, 16, PHOTO_W - 9, TICKET_H - 16))
    if ImageChops.difference(safe_expected, safe_actual).getbbox() is not None:
        raise ValueError("photo panel does not match the aspect-preserving source crop")

    split_x = TICKET_X + PHOTO_W
    x1 = split_x - PERFORATION_W // 2
    x2 = x1 + PERFORATION_W
    step = PERFORATION_DASH_H + PERFORATION_GAP
    expected_rows = {
        y
        for start in range(0, TICKET_H, step)
        for y in range(start, min(start + PERFORATION_DASH_H, TICKET_H))
    }
    for local_y in range(TICKET_H):
        row = [output.getpixel((x, TICKET_Y + local_y)) for x in range(x1, x2)]
        should_be_dash = local_y in expected_rows
        if should_be_dash and any(pixel != PERFORATION_COLOR for pixel in row):
            raise ValueError(f"perforation dash mismatch at local y={local_y}")
        if not should_be_dash and all(pixel == PERFORATION_COLOR for pixel in row):
            raise ValueError(f"unexpected perforation color in gap at local y={local_y}")

    top_row = [output.getpixel((x, TICKET_Y)) for x in range(x1, x2)]
    if any(pixel != PERFORATION_COLOR for pixel in top_row):
        raise ValueError("top perforation dash must start flush and square at ticket y=0")

    # The normalized stub reserves a flat guard band immediately to the right of
    # the canonical divider. Any variation here indicates a second generated
    # perforation, bright seam, border, or divider shadow survived cleanup.
    guard_x1 = x2
    guard_x2 = split_x + PERFORATION_GUARD_W
    guard = output.crop(
        (guard_x1, TICKET_Y, guard_x2, TICKET_Y + TICKET_H)
    )
    extrema = guard.getextrema()
    if any(low != high for low, high in extrema):
        raise ValueError(
            "stub guard band is not flat; possible second perforation or seam"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--photo-source", type=Path, required=True)
    parser.add_argument("--photo-center-y", type=float, default=0.5)
    args = parser.parse_args()
    if not 0.0 <= args.photo_center_y <= 1.0:
        parser.error("--photo-center-y must be between 0 and 1")
    validate(args.output, args.photo_source, args.photo_center_y)
    print(f"PASS: {args.output}")


if __name__ == "__main__":
    main()
