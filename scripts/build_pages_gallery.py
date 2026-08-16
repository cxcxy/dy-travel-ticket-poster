#!/usr/bin/env python3
"""Build the static GitHub Pages gallery from the locked 12-style registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "references" / "gallery-12-background-styles.json"
DEFAULT_SITE_DIR = ROOT / "docs"


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_webp(source: Path, output: Path, size: tuple[int, int]) -> None:
    with Image.open(source) as image:
        converted = ImageOps.fit(
            image.convert("RGB"),
            size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        converted.save(output, "WEBP", quality=86, method=6, exif=b"")


def build_gallery(
    registry_path: Path,
    source_dir: Path,
    site_dir: Path,
    default_preview: Path | None,
) -> list[dict[str, object]]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    styles = sorted(
        registry["styles"].items(),
        key=lambda item: item[1]["reference_anchor"]["order"],
    )
    expected_count = int(registry["expected_style_count"])
    if len(styles) != expected_count:
        raise ValueError(f"expected {expected_count} styles, found {len(styles)}")

    assets_dir = site_dir / "assets" / "styles"
    assets_dir.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, object]] = []

    for style_id, style in styles:
        anchor = style["reference_anchor"]
        source = source_dir / anchor["source_file"]
        if not source.is_file():
            raise FileNotFoundError(f"missing reference image: {source}")
        actual_hash = sha256(source)
        if actual_hash != anchor["sha256"]:
            raise ValueError(
                f"reference hash mismatch for {source.name}: "
                f"expected {anchor['sha256']}, got {actual_hash}"
            )

        order = int(anchor["order"])
        image_name = f"{order:02d}-{slugify(style_id)}.webp"
        save_webp(source, assets_dir / image_name, (750, 1000))
        items.append(
            {
                "order": order,
                "style_id": style_id,
                "name": style["name"],
                "description": style["description"],
                "image": f"assets/styles/{image_name}",
                "base_color": anchor["observed_base"],
                "categories": style["category"],
                "material": style["background_material"]["primary"],
                "lighting": style["lighting"]["recommended_preset"],
                "shadow": style["shadow"]["recommended_preset"],
                "best_for": style["best_for"],
                "command": f"把这张图片做成票根，使用第{order}种，其他按默认。",
            }
        )

    if default_preview is not None:
        if not default_preview.is_file():
            raise FileNotFoundError(f"missing default preview: {default_preview}")
        save_webp(
            default_preview,
            site_dir / "assets" / "default-subtle-texture.webp",
            (585, 780),
        )

    payload = {
        "version": registry["version"],
        "reference_set": registry["reference_set"]["name"],
        "style_count": len(items),
        "defaults": {
            "palette_mode": "adaptive",
            "background": "photo-main-colour-fine-matte-paper",
            "texture_range": "base ±2",
            "subject_preservation": "strict",
        },
        "styles": items,
    }
    pretty_payload = json.dumps(payload, ensure_ascii=False, indent=2)
    (site_dir / "style-data.json").write_text(pretty_payload + "\n", encoding="utf-8")
    (site_dir / "style-data.js").write_text(
        "window.STYLE_GALLERY_DATA = " + pretty_payload + ";\n",
        encoding="utf-8",
    )
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--site-dir", type=Path, default=DEFAULT_SITE_DIR)
    parser.add_argument("--default-preview", type=Path)
    args = parser.parse_args()

    items = build_gallery(
        args.registry.resolve(),
        args.source_dir.resolve(),
        args.site_dir.resolve(),
        args.default_preview.resolve() if args.default_preview else None,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "style_count": len(items),
                "site_dir": str(args.site_dir.resolve()),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
