#!/usr/bin/env python3
"""Build the canonical deterministic ticket posters from a JSON manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from PIL import Image

from palette_utils import parse_hex_color
from render_ticket_poster import render


def build_ticket(
    item: dict[str, object],
    output_dir: Path,
    requested_font: Path | None = None,
    overwrite: bool = False,
) -> Path:
    source_path = Path(str(item["source"]))
    output_path = output_dir / str(item["filename"])
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite: {output_path}")

    title_lines = [str(part).strip() for part in item.get("title_lines", [])]
    title = None if title_lines else str(item.get("title", "TRAVEL"))
    number = str(item["number"]).upper()
    if re.fullmatch(r"\d{5}", number):
        number = f"NO.{number}"
    code = str(item["code"]).upper()
    render(
        source_path,
        output_path,
        title,
        title_lines or None,
        str(item["date"]),
        number,
        code,
        parse_hex_color(str(item["background"])),
        parse_hex_color(str(item["stub_color"])),
        parse_hex_color(str(item.get("text_color", "#F4F0E5"))),
        float(item.get("photo_center_y", 0.5)),
        requested_font,
        bool(item.get("strip_neutral_borders", True)),
    )
    return output_path


def build_contact_sheet(outputs: list[Path], output_path: Path) -> None:
    thumb_w, thumb_h = 351, 468
    gap = 24
    cols = 3
    rows = (len(outputs) + cols - 1) // cols
    canvas = Image.new(
        "RGB",
        (cols * thumb_w + (cols + 1) * gap, rows * thumb_h + (rows + 1) * gap),
        (30, 30, 28),
    )
    for index, path in enumerate(outputs):
        with Image.open(path) as opened:
            image = opened.convert("RGB").resize(
                (thumb_w, thumb_h), Image.Resampling.LANCZOS
            )
        col, row = index % cols, index // cols
        canvas.paste(image, (gap + col * (thumb_w + gap), gap + row * (thumb_h + gap)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", compress_level=6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    outputs = [
        build_ticket(item, args.output_dir, args.font, overwrite=args.overwrite)
        for item in manifest["items"]
    ]
    if args.contact_sheet:
        if args.contact_sheet.exists() and not args.overwrite:
            raise FileExistsError(f"refusing to overwrite: {args.contact_sheet}")
        build_contact_sheet(outputs, args.contact_sheet)
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
