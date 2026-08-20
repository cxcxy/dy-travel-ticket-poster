#!/usr/bin/env python3
"""Suggest layout-aware editorial ticket-poster palettes."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from image_utils import open_prepared_source

from palette_utils import (
    RGB,
    contrast_ratio,
    delta_ok,
    file_sha256,
    hue_distance,
    oklch_to_rgb,
    rgb_to_hex,
    rgb_to_oklch,
)
from portrait_reference_style import (
    PORTRAIT_REFERENCE_BACKGROUND,
    PORTRAIT_REFERENCE_TEXT,
    PORTRAIT_REFERENCE_TICKET_CANDIDATES,
)
from ticket_layouts import LANDSCAPE, LAYOUT_IDS, PORTRAIT, get_layout


ANALYSIS_WIDTH = 128
TEXT_LIGHT = (244, 240, 229)
TEXT_DARK = (32, 35, 33)
PALETTE_TREATMENTS = ("auto", "photo-derived", "portrait-reference")


def resolve_palette_treatment(requested: str, layout_id: str) -> str:
    if requested not in PALETTE_TREATMENTS:
        raise ValueError(f"unknown palette treatment: {requested}")
    if requested != "auto":
        return requested
    return "portrait-reference" if layout_id == PORTRAIT else "photo-derived"


def _portrait_reference_result(
    source_path: Path,
    center_y: float,
    strip_neutral_borders: bool,
) -> dict:
    background = PORTRAIT_REFERENCE_BACKGROUND
    background_l, background_c, background_h = rgb_to_oklch(background)
    candidates: list[dict] = []
    for index, (candidate_id, label, stub) in enumerate(
        PORTRAIT_REFERENCE_TICKET_CANDIDATES
    ):
        separation = delta_ok(background, stub)
        text_contrast = contrast_ratio(PORTRAIT_REFERENCE_TEXT, stub)
        candidates.append(
            {
                "id": candidate_id,
                "label": label,
                "default_candidate": index == 0,
                "eligible": separation >= 0.10 and text_contrast >= 4.5,
                "background": rgb_to_hex(background),
                "stub": rgb_to_hex(stub),
                "text": rgb_to_hex(PORTRAIT_REFERENCE_TEXT),
                "metrics": {
                    "background_oklch": {
                        "l": round(background_l, 4),
                        "c": round(background_c, 4),
                        "h": round(background_h, 1),
                    },
                    "background_stub_delta_ok": round(separation, 4),
                    "text_contrast": round(text_contrast, 2),
                },
                "provenance": {
                    "background_source": rgb_to_hex(background),
                    "background_source_role": "portrait-reference-linen",
                    "background_source_coverage": 1.0,
                    "background_source_edge_coverage": 1.0,
                    "stub_source": rgb_to_hex(stub),
                    "stub_source_role": "portrait-reference-ticket-paper",
                    "stub_source_coverage": 1.0,
                    "text_source": rgb_to_hex(PORTRAIT_REFERENCE_TEXT),
                    "text_source_role": "portrait-reference-ink",
                },
                "warnings": [],
            }
        )
    return {
        "source": str(source_path.resolve()),
        "source_sha256": file_sha256(source_path),
        "photo_center_y": center_y,
        "strip_neutral_borders": strip_neutral_borders,
        "layout": PORTRAIT,
        "palette_treatment": "portrait-reference",
        "analysis_crop": {
            "width": get_layout(PORTRAIT).photo_w,
            "height": get_layout(PORTRAIT).photo_h,
        },
        "selection_rule": (
            "quiet-light matches the supplied portrait reference; review the two "
            "warmer paper variants only when the photograph benefits from them."
        ),
        "candidates": candidates,
    }


def _fit_source(
    source_path: Path,
    center_y: float,
    strip_neutral_borders: bool = True,
    layout_id: str = LANDSCAPE,
) -> Image.Image:
    source = open_prepared_source(source_path, strip_neutral_borders)
    layout = get_layout(layout_id)
    return ImageOps.fit(
        source,
        (layout.photo_w, layout.photo_h),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, center_y),
    )


def _extract_clusters(photo: Image.Image, color_count: int) -> list[dict]:
    analysis_h = max(32, round(ANALYSIS_WIDTH * photo.height / photo.width))
    analysis = photo.resize((ANALYSIS_WIDTH, analysis_h), Image.Resampling.LANCZOS)
    quantized = analysis.quantize(
        colors=color_count,
        method=Image.Quantize.MEDIANCUT,
    ).convert("RGB")
    all_counts = Counter(quantized.getdata())
    width, height = quantized.size
    border_x = max(1, round(width * 0.16))
    border_y = max(1, round(height * 0.16))
    edge_pixels = [
        quantized.getpixel((x_pos, y_pos))
        for y_pos in range(height)
        for x_pos in range(width)
        if (
            x_pos < border_x
            or x_pos >= width - border_x
            or y_pos < border_y
            or y_pos >= height - border_y
        )
    ]
    edge_counts = Counter(edge_pixels)
    total = width * height
    edge_total = len(edge_pixels)

    clusters: list[dict] = []
    for color, count in all_counts.most_common():
        l_value, chroma, hue = rgb_to_oklch(color)
        coverage = count / total
        edge_coverage = edge_counts[color] / edge_total
        if coverage < 0.015 or l_value < 0.16 or l_value > 0.94:
            continue
        skin_like = 20.0 <= hue <= 70.0 and 0.42 <= l_value <= 0.86 and 0.025 <= chroma <= 0.17
        clusters.append(
            {
                "rgb": color,
                "hex": rgb_to_hex(color),
                "coverage": coverage,
                "edge_coverage": edge_coverage,
                "l": l_value,
                "c": chroma,
                "h": hue,
                "skin_like": skin_like,
            }
        )

    if not clusters:
        color = all_counts.most_common(1)[0][0]
        l_value, chroma, hue = rgb_to_oklch(color)
        clusters.append(
            {
                "rgb": color,
                "hex": rgb_to_hex(color),
                "coverage": 1.0,
                "edge_coverage": 1.0,
                "l": l_value,
                "c": chroma,
                "h": hue,
                "skin_like": False,
            }
        )

    max_coverage = max(cluster["coverage"] for cluster in clusters)
    max_edge = max(cluster["edge_coverage"] for cluster in clusters) or 1.0
    for cluster in clusters:
        neutral_stability = 1.0 - min(cluster["c"] / 0.18, 1.0)
        score = (
            0.45 * cluster["coverage"] / max_coverage
            + 0.35 * cluster["edge_coverage"] / max_edge
            + 0.20 * neutral_stability
        )
        # Skin, hair and clothing are not reliable full-canvas sources. A
        # skin-like cluster remains eligible only when it is also present at
        # the crop edge, where it is more likely to be wood, stone or sand.
        if cluster["skin_like"] and cluster["edge_coverage"] < cluster["coverage"] * 0.55:
            score *= 0.55
        cluster["background_score"] = score
    return clusters


def _distinct_background_sources(clusters: list[dict], count: int = 3) -> list[dict]:
    ranked = sorted(clusters, key=lambda item: item["background_score"], reverse=True)
    selected: list[dict] = []
    for cluster in ranked:
        if all(
            delta_ok(cluster["rgb"], prior["rgb"]) >= 0.045
            or hue_distance(cluster["h"], prior["h"]) >= 28.0
            for prior in selected
        ):
            selected.append(cluster)
        if len(selected) == count:
            break
    for cluster in ranked:
        if len(selected) == count:
            break
        if cluster not in selected:
            selected.append(cluster)
    while len(selected) < count:
        selected.append(ranked[len(selected) % len(ranked)])
    return selected


def _background_from_source(source: dict, target_l: float, chroma_cap: float) -> RGB:
    target_c = min(chroma_cap, source["c"] * 0.72)
    if source["c"] >= 0.012:
        target_c = max(0.018, target_c)
    return oklch_to_rgb(target_l, target_c, source["h"])


def _ensure_text_contrast(stub: RGB) -> tuple[RGB, RGB, float]:
    text = max((TEXT_LIGHT, TEXT_DARK), key=lambda candidate: contrast_ratio(candidate, stub))
    ratio = contrast_ratio(text, stub)
    if ratio >= 5.0:
        return stub, text, ratio

    l_value, chroma, hue = rgb_to_oklch(stub)
    direction = -1.0 if text == TEXT_LIGHT else 1.0
    for _ in range(24):
        l_value = max(0.18, min(0.88, l_value + direction * 0.012))
        adjusted = oklch_to_rgb(l_value, chroma, hue)
        ratio = contrast_ratio(text, adjusted)
        if ratio >= 5.0:
            return adjusted, text, ratio
    return stub, text, contrast_ratio(text, stub)


def _select_stub(background: RGB, clusters: list[dict], background_source: dict) -> tuple[RGB, RGB, dict, float, float]:
    background_l, _, background_h = rgb_to_oklch(background)
    max_coverage = max(cluster["coverage"] for cluster in clusters)
    options: list[tuple[float, RGB, RGB, dict, float, float]] = []
    target_lightnesses = (0.34, 0.82) if background_l >= 0.62 else (0.82, 0.30)

    for source in clusters:
        for target_l in target_lightnesses:
            target_c = min(0.16, source["c"] * 0.94)
            if source["c"] >= 0.02:
                target_c = max(0.028, target_c)
            raw_stub = oklch_to_rgb(target_l, target_c, source["h"])
            stub, text, text_contrast = _ensure_text_contrast(raw_stub)
            separation = delta_ok(background, stub)
            hue_gap = hue_distance(background_h, source["h"])
            separation_score = max(0.0, 1.0 - abs(separation - 0.25) / 0.25)
            salience = min(source["c"] / 0.16, 1.0)
            score = (
                0.30 * salience
                + 0.25 * source["coverage"] / max_coverage
                + 0.25 * separation_score
                + 0.20 * min(source["c"] / 0.12, 1.0)
            )
            if source is background_source and len(clusters) > 1:
                score *= 0.78
            if separation < 0.10:
                score *= 0.20
            if separation > 0.50:
                score *= 0.65
            if separation < 0.15 and hue_gap < 45.0:
                score *= 0.65
            options.append((score, stub, text, source, separation, text_contrast))

    _, stub, text, source, separation, text_contrast = max(options, key=lambda item: item[0])
    return stub, text, source, separation, text_contrast


def suggest_palettes(
    source_path: Path,
    center_y: float = 0.5,
    color_count: int = 8,
    strip_neutral_borders: bool = True,
    layout_id: str = LANDSCAPE,
    palette_treatment: str = "auto",
) -> dict:
    treatment = resolve_palette_treatment(palette_treatment, layout_id)
    if treatment == "portrait-reference":
        if layout_id != PORTRAIT:
            raise ValueError("portrait-reference palette requires layout=portrait")
        return _portrait_reference_result(
            source_path,
            center_y,
            strip_neutral_borders,
        )

    layout = get_layout(layout_id)
    photo = _fit_source(source_path, center_y, strip_neutral_borders, layout_id)
    clusters = _extract_clusters(photo, color_count)
    background_sources = _distinct_background_sources(clusters)
    # Keep the first two candidates comparable in lightness but distinct in
    # mood. The middle candidate uses the most chromatic credible environment
    # source so it does not collapse into a second generic grey/beige option.
    narrative_source = max(
        clusters,
        key=lambda cluster: cluster["background_score"]
        * (0.50 + min(cluster["c"] / 0.09, 1.0)),
    )
    if narrative_source not in background_sources[:2]:
        background_sources[1] = narrative_source
    styles = (
        ("quiet-light", "安静亮调", 0.74, 0.055),
        ("editorial-mid", "编辑中调", 0.68, 0.075),
        ("cinematic-deep", "电影深调", 0.56, 0.090),
    )

    candidates: list[dict] = []
    for index, (candidate_id, label, target_l, chroma_cap) in enumerate(styles):
        background_source = background_sources[index]
        background = _background_from_source(background_source, target_l, chroma_cap)
        stub, text, stub_source, separation, text_contrast = _select_stub(
            background, clusters, background_source
        )
        background_l, background_c, background_h = rgb_to_oklch(background)
        warnings: list[str] = []
        if background_source["skin_like"]:
            warnings.append("背景来源色接近肤色/木色范围，交付前必须目视确认它来自环境。")
        if not 0.64 <= background_l <= 0.78 or not 0.02 <= background_c <= 0.08:
            warnings.append("该方案位于默认高级感软区间之外，只在叙事情绪明确时采用。")
        if separation < 0.14:
            warnings.append("背景与信息联分离度偏弱，优先改选另一套方案。")
        if text_contrast < 5.0:
            warnings.append("文字对比未达到生成目标 5:1。")
        candidates.append(
            {
                "id": candidate_id,
                "label": label,
                "default_candidate": index == 0,
                "eligible": separation >= 0.10 and text_contrast >= 4.5,
                "background": rgb_to_hex(background),
                "stub": rgb_to_hex(stub),
                "text": rgb_to_hex(text),
                "metrics": {
                    "background_oklch": {
                        "l": round(background_l, 4),
                        "c": round(background_c, 4),
                        "h": round(background_h, 1),
                    },
                    "background_stub_delta_ok": round(separation, 4),
                    "text_contrast": round(text_contrast, 2),
                },
                "provenance": {
                    "background_source": background_source["hex"],
                    "background_source_coverage": round(background_source["coverage"], 4),
                    "background_source_edge_coverage": round(
                        background_source["edge_coverage"], 4
                    ),
                    "stub_source": stub_source["hex"],
                    "stub_source_coverage": round(stub_source["coverage"], 4),
                },
                "warnings": warnings,
            }
        )

    return {
        "source": str(source_path.resolve()),
        "source_sha256": file_sha256(source_path),
        "photo_center_y": center_y,
        "strip_neutral_borders": strip_neutral_borders,
        "layout": layout_id,
        "palette_treatment": "photo-derived",
        "analysis_crop": {"width": layout.photo_w, "height": layout.photo_h},
        "selection_rule": "Visual-review all three candidates; quiet-light is only the default, not an automatic winner.",
        "candidates": candidates,
    }


def _load_preview_font(size: int, bold: bool = False):
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_preview(source_path: Path, center_y: float, result: dict, output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"preview already exists: {output_path}")
    canvas = Image.new("RGB", (1120, 1150), (238, 235, 229))
    draw = ImageDraw.Draw(canvas)
    title_font = _load_preview_font(28, bold=True)
    body_font = _load_preview_font(18)
    small_font = _load_preview_font(15)
    treatment = str(result.get("palette_treatment", "photo-derived"))
    preview_title = (
        "PORTRAIT REFERENCE PALETTE REVIEW"
        if treatment == "portrait-reference"
        else "PHOTO-DERIVED PALETTE REVIEW"
    )
    draw.text((34, 28), preview_title, fill=(31, 33, 32), font=title_font)
    draw.text(
        (34, 68),
        "Choose by subject separation, scene mood and canvas/stub hierarchy.",
        fill=(83, 82, 78),
        font=body_font,
    )

    photo = _fit_source(
        source_path,
        center_y,
        bool(result.get("strip_neutral_borders", True)),
        str(result.get("layout", LANDSCAPE)),
    )
    source_preview = ImageOps.fit(photo, (330, 216), method=Image.Resampling.LANCZOS)
    canvas.paste(source_preview, (34, 118))
    layout = get_layout(str(result.get("layout", LANDSCAPE)))
    draw.text(
        (34, 350),
        f"FINAL {layout.photo_w} × {layout.photo_h} CROP · {layout.id.upper()}",
        fill=(31, 33, 32),
        font=small_font,
    )
    draw.multiline_text(
        (34, 395),
        "Review all three.\nAvoid skin/hair-derived beige,\nmuddy middle tones and\nbatch-default colors.",
        fill=(83, 82, 78),
        font=body_font,
        spacing=8,
    )

    if layout.id == LANDSCAPE:
        ticket_h = 250
        ticket_w = round(ticket_h * layout.ticket_w / layout.ticket_h)
    else:
        ticket_h = 250
        ticket_w = round(ticket_h * layout.ticket_w / layout.ticket_h)
    ticket_photo_w = round(ticket_w * layout.photo_w / layout.ticket_w)
    ticket_photo_h = round(ticket_h * layout.photo_h / layout.ticket_h)
    ticket_stub_w = ticket_w - ticket_photo_w
    photo_thumb = ImageOps.fit(
        photo,
        (ticket_photo_w, ticket_photo_h),
        method=Image.Resampling.LANCZOS,
    )
    for index, candidate in enumerate(result["candidates"]):
        y_pos = 112 + index * 342
        background = tuple(int(candidate["background"][offset : offset + 2], 16) for offset in (1, 3, 5))
        stub = tuple(int(candidate["stub"][offset : offset + 2], 16) for offset in (1, 3, 5))
        text_color = tuple(int(candidate["text"][offset : offset + 2], 16) for offset in (1, 3, 5))
        draw.rounded_rectangle((398, y_pos, 1082, y_pos + 318), radius=14, fill=background)
        label_color = max(
            (TEXT_LIGHT, TEXT_DARK),
            key=lambda candidate_color: contrast_ratio(candidate_color, background),
        )
        draw.text(
            (414, y_pos + 13),
            f"{candidate['id'].upper()}  BG {candidate['background']}  STUB {candidate['stub']}  "
            f"TEXT {candidate['text']}  DELTA {candidate['metrics']['background_stub_delta_ok']:.3f}  "
            f"CR {candidate['metrics']['text_contrast']:.2f}",
            fill=label_color,
            font=small_font,
        )
        ticket_x = 480 if layout.id == LANDSCAPE else 680
        ticket_y = y_pos + 52
        draw.rounded_rectangle(
            (ticket_x, ticket_y, ticket_x + ticket_w, ticket_y + ticket_h),
            radius=8,
            fill=stub,
        )
        if layout.id == LANDSCAPE:
            canvas.paste(photo_thumb, (ticket_x, ticket_y))
            stub_text_x = ticket_x + ticket_photo_w + 18
            draw.text((stub_text_x, ticket_y + 28), "TRAVEL", fill=text_color, font=_load_preview_font(22, bold=True))
            draw.text((stub_text_x, ticket_y + 92), "2026 - 08", fill=text_color, font=small_font)
            draw.text((stub_text_x, ticket_y + 143), "NO.19427", fill=text_color, font=small_font)
            draw.text((stub_text_x, ticket_y + 176), "E5R8K3M2", fill=text_color, font=small_font)
        else:
            photo_x = ticket_x + round(ticket_w * layout.photo_x / layout.ticket_w)
            photo_y = ticket_y + round(ticket_h * layout.photo_y / layout.ticket_h)
            canvas.paste(photo_thumb, (photo_x, photo_y))
            divider_y = ticket_y + round(ticket_h * layout.divider_position / layout.ticket_h)
            draw.line((ticket_x + 8, divider_y, ticket_x + ticket_w - 8, divider_y), fill=background, width=2)
            draw.text((ticket_x + 12, divider_y + 8), "NO.19427", fill=text_color, font=small_font)
            draw.text((ticket_x + ticket_w - 72, divider_y + 8), "TRAVEL", fill=text_color, font=_load_preview_font(13, bold=True))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", compress_level=6)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--photo-center-y", type=float, default=0.5)
    parser.add_argument("--colors", type=int, default=8)
    parser.add_argument("--layout", choices=LAYOUT_IDS, default=LANDSCAPE)
    parser.add_argument(
        "--palette-treatment",
        choices=PALETTE_TREATMENTS,
        default="auto",
        help="auto uses the measured reference palette for portrait and photo-derived colours for landscape",
    )
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument(
        "--keep-neutral-borders",
        action="store_true",
        help="Preserve intentional solid white/black framing at the photo edge",
    )
    args = parser.parse_args()
    if not 0.0 <= args.photo_center_y <= 1.0:
        parser.error("--photo-center-y must be between 0 and 1")
    if not 6 <= args.colors <= 12:
        parser.error("--colors must be between 6 and 12")
    if not args.input.is_file():
        parser.error(f"input does not exist: {args.input}")
    if args.output_json and args.output_json.exists():
        raise FileExistsError(f"JSON output already exists: {args.output_json}")
    if args.preview and args.preview.exists():
        raise FileExistsError(f"preview already exists: {args.preview}")

    result = suggest_palettes(
        args.input,
        args.photo_center_y,
        args.colors,
        not args.keep_neutral_borders,
        args.layout,
        args.palette_treatment,
    )
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(serialized + "\n", encoding="utf-8")
    if args.preview:
        render_preview(args.input, args.photo_center_y, result, args.preview)
    print(serialized)


if __name__ == "__main__":
    main()
