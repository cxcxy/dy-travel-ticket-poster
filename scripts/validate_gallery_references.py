#!/usr/bin/env python3
"""Validate the local 12-image gallery against registry provenance anchors."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

from PIL import Image


DEFAULT_REGISTRY = (
    Path(__file__).resolve().parent.parent
    / "references"
    / "gallery-12-background-styles.json"
)


def background_median(image: Image.Image) -> str:
    """Measure safe top and bottom regions that never intersect the reference ticket."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    if (width, height) != (1086, 1448):
        raise ValueError(f"expected 1086x1448 reference, found {width}x{height}")
    pixels: list[tuple[int, int, int]] = []
    for box in ((0, 0, width, 420), (0, 1050, width, height)):
        crop = rgb.crop(box)
        crop = crop.resize((crop.width // 8, crop.height // 8))
        pixels.extend(crop.getdata())
    median = tuple(round(statistics.median(channel)) for channel in zip(*pixels))
    return "#{:02X}{:02X}{:02X}".format(*median)


def validate_references(registry: dict[str, Any], source_dir: Path) -> list[str]:
    errors: list[str] = []
    observed_canvas = tuple(registry["reference_set"]["observed_canvas"])
    for style_id, style in registry["styles"].items():
        anchor = style["reference_anchor"]
        path = source_dir / anchor["source_file"]
        if not path.is_file():
            errors.append(f"{style_id}: missing {path}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != anchor["sha256"]:
            errors.append(
                f"{style_id}: SHA-256 mismatch, expected {anchor['sha256']}, found {digest}"
            )
        try:
            with Image.open(path) as image:
                if image.size != observed_canvas:
                    errors.append(
                        f"{style_id}: expected {observed_canvas[0]}x{observed_canvas[1]}, "
                        f"found {image.width}x{image.height}"
                    )
                measured = background_median(image)
        except (OSError, ValueError) as exc:
            errors.append(f"{style_id}: cannot inspect reference: {exc}")
            continue
        if measured != anchor["observed_base"]:
            errors.append(
                f"{style_id}: background median mismatch, "
                f"expected {anchor['observed_base']}, found {measured}"
            )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    errors = validate_references(registry, args.source_dir)
    result = {
        "status": "error" if errors else "ok",
        "reference_set": registry["reference_set"]["name"],
        "reference_count": len(registry["styles"]),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
