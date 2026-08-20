#!/usr/bin/env python3
"""Validate source fidelity, palette facts and canonical ticket geometry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from PIL import Image, ImageChops, ImageDraw, ImageOps

from image_utils import open_prepared_source

from normalize_reference_layout import (
    CANVAS_SIZE,
    PERFORATION_COLOR,
    PERFORATION_DASH_H,
    PERFORATION_GAP,
    PERFORATION_GUARD_W,
    PERFORATION_W,
    PHOTO_W,
    TICKET_H,
    TICKET_W,
    TICKET_X,
    TICKET_Y,
    apply_ticket_shadow,
    build_background,
    draw_single_perforation,
    load_background_image,
    make_ticket_mask,
)
from palette_utils import (
    RGB,
    contrast_ratio,
    delta_ok,
    file_sha256,
    load_palette_candidate,
    parse_hex_color,
    rgb_to_hex,
    rgb_to_oklch,
)
from render_ticket_poster import build_portrait_ticket_base, build_stub
from ticket_layouts import (
    LANDSCAPE,
    LAYOUT_IDS,
    PORTRAIT,
    draw_portrait_perforation,
    get_layout,
    make_portrait_ticket_mask,
)


def _validate_background(
    output: Image.Image,
    expected_color: RGB,
    layout_id: str,
    shadow_preset: str | None = None,
) -> None:
    layout = get_layout(layout_id)
    ticket_mask = (
        make_ticket_mask()
        if layout_id == LANDSCAPE
        else make_portrait_ticket_mask(layout)
    )
    expected = build_background(expected_color)
    apply_ticket_shadow(
        expected,
        ticket_mask,
        expected_color,
        shadow_preset,
        ticket_position=(layout.ticket_x, layout.ticket_y),
    )
    difference = ImageChops.difference(output, expected)
    # Ticket pixels may contain the photograph, stub and type. Every pixel
    # outside that exact silhouette must equal the canonical flat canvas plus
    # palette-aware shadow, including the narrow left/right gutters.
    difference.paste((0, 0, 0), (layout.ticket_x, layout.ticket_y), ticket_mask)
    if difference.getbbox() is not None:
        raise ValueError(
            "canvas background or shadow differs from the expected solid-color construction "
            f"{rgb_to_hex(expected_color)}"
        )


def _validate_background_image(
    output: Image.Image,
    expected_path: Path,
    layout_id: str,
    shadow_preset: str | None,
) -> RGB:
    layout = get_layout(layout_id)
    ticket_mask = (
        make_ticket_mask()
        if layout_id == LANDSCAPE
        else make_portrait_ticket_mask(layout)
    )
    expected = load_background_image(expected_path)
    canvas_color = expected.getpixel((0, 0))
    apply_ticket_shadow(
        expected,
        ticket_mask,
        canvas_color,
        shadow_preset,
        (layout.ticket_x, layout.ticket_y),
    )
    difference = ImageChops.difference(output, expected)
    difference.paste((0, 0, 0), (layout.ticket_x, layout.ticket_y), ticket_mask)
    if difference.getbbox() is not None:
        raise ValueError(
            "canvas background or shadow differs from the expected background image"
        )
    return canvas_color


def _validate_stub_exact(
    output: Image.Image,
    metadata: dict,
    stub: RGB,
    text: RGB,
    perforation: RGB,
    requested_font: Path | None = None,
    requested_body_font: Path | None = None,
    expected_title: str | None = None,
    expected_title_lines: list[str] | None = None,
    expected_date: str | None = None,
    expected_number: str | None = None,
    expected_code: str | None = None,
    layout_id: str = LANDSCAPE,
) -> None:
    required = (
        "dy_ticket_title",
        "dy_ticket_title_lines",
        "dy_ticket_date",
        "dy_ticket_number",
        "dy_ticket_code",
        "dy_ticket_title_font_sha256",
        "dy_ticket_body_font_sha256",
    )
    missing = [key for key in required if key not in metadata]
    if missing:
        raise ValueError(
            f"missing exact-stub renderer metadata: {', '.join(missing)}"
        )
    recorded_title_lines = json.loads(metadata["dy_ticket_title_lines"])
    if not isinstance(recorded_title_lines, list) or not all(
        isinstance(line, str) for line in recorded_title_lines
    ):
        raise ValueError("invalid exact-stub title-line metadata")
    title_lines = (
        expected_title_lines
        if expected_title_lines is not None
        else recorded_title_lines or None
    )
    title = (
        expected_title
        if expected_title is not None
        else metadata["dy_ticket_title"] or None
    )
    date = expected_date or metadata["dy_ticket_date"]
    number = expected_number or metadata["dy_ticket_number"]
    code = expected_code or metadata["dy_ticket_code"]

    # Locate the exact title and body font files by their embedded hashes.
    # They are independent typographic roles and must both be reproducible.
    from render_ticket_poster import (
        BOLD_FONT_CANDIDATES,
        CJK_FONT_CANDIDATES,
        HEAVY_FONT_CANDIDATES,
        LIGHT_MONO_FONT_CANDIDATES,
    )

    available = []
    for candidate in (
        *HEAVY_FONT_CANDIDATES,
        *BOLD_FONT_CANDIDATES,
        *CJK_FONT_CANDIDATES,
        *LIGHT_MONO_FONT_CANDIDATES,
    ):
        path = Path(candidate)
        if path.is_file() and path not in available:
            available.append(path)
    for requested in (requested_font, requested_body_font):
        if requested is not None:
            if not requested.is_file():
                raise ValueError(f"validation font does not exist: {requested}")
            if requested not in available:
                available.append(requested)
    if requested_font is not None and file_sha256(requested_font) != metadata[
        "dy_ticket_title_font_sha256"
    ]:
        raise ValueError("validation title font does not match recorded title font")
    if requested_body_font is not None and file_sha256(requested_body_font) != metadata[
        "dy_ticket_body_font_sha256"
    ]:
        raise ValueError("validation body font does not match recorded body font")
    hash_to_path = {file_sha256(path): path for path in available}
    title_font_path = hash_to_path.get(metadata["dy_ticket_title_font_sha256"])
    body_font_path = hash_to_path.get(metadata["dy_ticket_body_font_sha256"])
    if title_font_path is None or body_font_path is None:
        raise ValueError(
            "cannot reconstruct the exact stub because its recorded font file is unavailable"
        )
    layout = get_layout(layout_id)
    if layout_id == LANDSCAPE:
        expected_stub, identity = build_stub(
            title,
            title_lines,
            date,
            number,
            code,
            stub,
            text,
            title_font_path,
            body_font_path,
        )
    else:
        expected_ticket, identity = build_portrait_ticket_base(
            title,
            title_lines,
            date,
            number,
            code,
            stub,
            text,
            title_font_path,
            body_font_path,
        )
    if identity["title_font_sha256"] != metadata["dy_ticket_title_font_sha256"]:
        raise ValueError("title font identity changed during exact-stub reconstruction")
    if identity["body_font_sha256"] != metadata["dy_ticket_body_font_sha256"]:
        raise ValueError("body font identity changed during exact-stub reconstruction")
    if identity["title_font_name"] != metadata["dy_ticket_title_font_name"]:
        raise ValueError("title font name does not match its recorded file identity")
    if identity["body_font_name"] != metadata["dy_ticket_body_font_name"]:
        raise ValueError("body font name does not match its recorded file identity")

    if layout_id == LANDSCAPE:
        expected_ticket = Image.new("RGB", (TICKET_W, TICKET_H), stub)
        expected_ticket.paste(expected_stub, (PHOTO_W, 0))
        draw_single_perforation(expected_ticket, perforation)
        expected_stub = expected_ticket.crop((PHOTO_W, 0, TICKET_W, TICKET_H))
        actual_stub = output.crop(
            (
                TICKET_X + PHOTO_W,
                TICKET_Y,
                TICKET_X + TICKET_W,
                TICKET_Y + TICKET_H,
            )
        )
        ticket_mask = make_ticket_mask().crop((PHOTO_W, 0, TICKET_W, TICKET_H))
    else:
        draw_portrait_perforation(expected_ticket, perforation, layout)
        actual_stub = output.crop(
            (
                layout.ticket_x,
                layout.ticket_y,
                layout.ticket_x + layout.ticket_w,
                layout.ticket_y + layout.ticket_h,
            )
        )
        expected_stub = expected_ticket
        ticket_mask = make_portrait_ticket_mask(layout)
        # The photograph is validated independently against source pixels.
        ImageDraw.Draw(ticket_mask).rectangle(
            (
                layout.photo_x,
                layout.photo_y,
                layout.photo_x + layout.photo_w - 1,
                layout.photo_y + layout.photo_h - 1,
            ),
            fill=0,
        )
    # Every visible stub pixel, including the perforation and edge pixels, must
    # be byte-for-byte identical to deterministic reconstruction.
    difference = ImageChops.difference(actual_stub, expected_stub)
    zero = Image.new("RGB", difference.size, (0, 0, 0))
    checked = Image.composite(difference, zero, ticket_mask)
    if checked.getbbox() is not None:
        raise ValueError("information stub does not match exact deterministic reconstruction")


def _validate_renderer_metadata(
    metadata: dict,
    source_path: Path,
    photo_center_y: float,
    background: RGB | None,
    stub: RGB | None,
    text: RGB | None,
    strip_neutral_borders: bool,
    expected_title: str | None,
    expected_title_lines: list[str] | None,
    expected_date: str,
    expected_number: str,
    expected_code: str,
    layout_id: str,
    expected_background_image: Path | None,
    shadow_preset: str | None,
) -> None:
    required = {
        "dy_ticket_renderer",
        "dy_ticket_source_sha256",
        "dy_ticket_photo_center_y",
        "dy_ticket_title_font_name",
        "dy_ticket_title_font_sha256",
        "dy_ticket_body_font_name",
        "dy_ticket_body_font_sha256",
        "dy_ticket_title",
        "dy_ticket_title_lines",
        "dy_ticket_date",
        "dy_ticket_number",
        "dy_ticket_code",
    }
    missing = sorted(required.difference(metadata))
    if missing:
        raise ValueError(f"missing deterministic renderer metadata: {', '.join(missing)}")
    if metadata["dy_ticket_renderer"] not in {"1", "2"}:
        raise ValueError("unsupported deterministic renderer metadata version")
    recorded_layout = metadata.get("dy_ticket_layout", LANDSCAPE)
    if recorded_layout != layout_id:
        raise ValueError("embedded layout does not match --layout")
    if metadata["dy_ticket_renderer"] == "2" and "dy_ticket_layout" not in metadata:
        raise ValueError("renderer metadata version 2 requires an embedded layout")
    if metadata["dy_ticket_renderer"] == "2":
        for key in (
            "dy_ticket_background_source",
            "dy_ticket_background_image_sha256",
            "dy_ticket_shadow_preset",
        ):
            if key not in metadata:
                raise ValueError(f"renderer metadata version 2 requires {key}")
    expected_background_source = "image" if expected_background_image else "color"
    if metadata.get("dy_ticket_background_source", "color") != expected_background_source:
        raise ValueError("embedded background source does not match validation input")
    if expected_background_image is not None:
        if metadata.get("dy_ticket_background_image_sha256") != file_sha256(
            expected_background_image
        ):
            raise ValueError("embedded background image hash does not match validation input")
    recorded_shadow = metadata.get("dy_ticket_shadow_preset", "default")
    if recorded_shadow != (shadow_preset or "default"):
        raise ValueError("embedded shadow preset does not match validation input")
    if metadata["dy_ticket_source_sha256"] != file_sha256(source_path):
        raise ValueError("embedded source hash does not match --photo-source")
    if abs(float(metadata["dy_ticket_photo_center_y"]) - photo_center_y) > 1e-9:
        raise ValueError("embedded crop center does not match --photo-center-y")
    expected_strip = "1" if strip_neutral_borders else "0"
    if metadata.get("dy_ticket_strip_neutral_borders") != expected_strip:
        raise ValueError("embedded border handling does not match validation input")
    for label, expected in (
        ("background", background),
        ("stub", stub),
        ("text", text),
    ):
        if expected is None:
            continue
        key = f"dy_ticket_{label}"
        if metadata.get(key) != rgb_to_hex(expected):
            raise ValueError(f"embedded {label} color does not match validation input")
    for key in ("dy_ticket_title_font_sha256", "dy_ticket_body_font_sha256"):
        value = metadata[key]
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError(f"invalid embedded font identity: {key}")
    try:
        recorded_title_lines = json.loads(metadata["dy_ticket_title_lines"])
    except json.JSONDecodeError as error:
        raise ValueError("invalid embedded title-line metadata") from error
    if not isinstance(recorded_title_lines, list) or not all(
        isinstance(line, str) for line in recorded_title_lines
    ):
        raise ValueError("invalid embedded title-line metadata")
    if expected_title_lines is not None:
        if metadata["dy_ticket_title"] or recorded_title_lines != expected_title_lines:
            raise ValueError("embedded title lines do not match the external text contract")
    elif (
        metadata["dy_ticket_title"] != expected_title
        or recorded_title_lines
    ):
        raise ValueError("embedded title does not match the external text contract")
    for label, expected in (
        ("date", expected_date),
        ("number", expected_number),
        ("code", expected_code),
    ):
        if metadata[f"dy_ticket_{label}"] != expected:
            raise ValueError(
                f"embedded {label} does not match the external text contract"
            )


def _normalize_external_text_contract(
    expected_title: str | None,
    expected_title_lines: list[str] | None,
    expected_date: str | None,
    expected_number: str | None,
    expected_code: str | None,
) -> tuple[str | None, list[str] | None, str, str, str]:
    if (expected_title is None) == (expected_title_lines is None):
        raise ValueError(
            "strict validation requires exactly one of expected title or expected title lines"
        )
    if expected_title is not None and not expected_title.strip():
        raise ValueError("expected title must not be empty")
    if expected_title_lines is not None:
        if not 1 <= len(expected_title_lines) <= 2 or any(
            not line.strip() for line in expected_title_lines
        ):
            raise ValueError("expected title lines must contain one or two non-empty values")
    if expected_date is None or not re.fullmatch(r"\d{4} - \d{2}", expected_date):
        raise ValueError('strict validation requires expected date as "YYYY - MM"')
    if expected_number is None:
        raise ValueError("strict validation requires an expected ticket number")
    normalized_number = expected_number.upper()
    if re.fullmatch(r"\d{5}", normalized_number):
        normalized_number = f"NO.{normalized_number}"
    if not re.fullmatch(r"NO\.\d{5}", normalized_number):
        raise ValueError("expected number must be five digits or NO. followed by five digits")
    if expected_code is None:
        raise ValueError("strict validation requires an expected ticket code")
    normalized_code = expected_code.upper()
    if not re.fullmatch(r"[A-Z0-9]{8}", normalized_code):
        raise ValueError("expected code must contain exactly eight letters or digits")
    return (
        expected_title,
        expected_title_lines,
        expected_date,
        normalized_number,
        normalized_code,
    )


def _validate_palette(
    background: RGB | None,
    stub: RGB | None,
    text: RGB | None,
    palette_mode: str,
) -> list[str]:
    warnings: list[str] = []
    if background is not None:
        lightness, chroma, _ = rgb_to_oklch(background)
        if palette_mode == "adaptive":
            if lightness < 0.45 or lightness > 0.88 or chroma > 0.16:
                raise ValueError(
                    "adaptive background falls outside the supported narrative color limits "
                    f"(OKLCH L={lightness:.3f}, C={chroma:.3f})"
                )
            if not (0.64 <= lightness <= 0.78 and 0.02 <= chroma <= 0.08):
                warnings.append(
                    "background is outside the preferred editorial soft range "
                    f"(OKLCH L={lightness:.3f}, C={chroma:.3f}); visual approval is required"
                )
    if background is not None and stub is not None:
        separation = delta_ok(background, stub)
        if separation < 0.10:
            raise ValueError(
                f"canvas and stub are too similar (Delta OK={separation:.3f}; minimum 0.10)"
            )
        if separation < 0.14:
            warnings.append(
                f"canvas/stub separation is below the preferred 0.14 (Delta OK={separation:.3f})"
            )
        if separation > 0.50:
            warnings.append(
                f"canvas/stub separation exceeds the preferred 0.50 (Delta OK={separation:.3f})"
            )
    if stub is not None and text is not None:
        ratio = contrast_ratio(stub, text)
        if ratio < 4.5:
            raise ValueError(
                f"stub text contrast is {ratio:.2f}:1; small text requires at least 4.5:1"
            )
        if ratio < 5.0:
            warnings.append(
                f"stub text contrast passes at {ratio:.2f}:1 but is below the 5:1 production target"
            )
    return warnings


def validate(
    output_path: Path,
    source_path: Path,
    photo_center_y: float,
    expected_background: RGB | None = None,
    expected_stub: RGB | None = None,
    expected_text: RGB | None = None,
    expected_perforation: RGB | None = None,
    palette_mode: str = "adaptive",
    require_renderer_metadata: bool = False,
    strip_neutral_borders: bool = True,
    font_path: Path | None = None,
    expected_title: str | None = None,
    expected_title_lines: list[str] | None = None,
    expected_date: str | None = None,
    expected_number: str | None = None,
    expected_code: str | None = None,
    body_font_path: Path | None = None,
    layout_id: str = LANDSCAPE,
    expected_background_image: Path | None = None,
    shadow_preset: str | None = None,
) -> list[str]:
    layout = get_layout(layout_id)
    with Image.open(output_path) as opened:
        if opened.format != "PNG" or output_path.suffix.lower() != ".png":
            raise ValueError("final output must be a PNG file with a .png extension")
        if "A" in opened.getbands() or "transparency" in opened.info:
            raise ValueError("final PNG must not contain an alpha or transparency channel")
        if opened.mode != "RGB":
            raise ValueError(f"final PNG must use RGB mode, got {opened.mode}")
        renderer_metadata = dict(opened.info)
        output = opened.convert("RGB")
    if output.size != CANVAS_SIZE:
        raise ValueError(f"expected {CANVAS_SIZE}, got {output.size}")
    strict_text_contract = None
    if require_renderer_metadata:
        if expected_background_image is None and any(
            color is None for color in (expected_background, expected_stub, expected_text)
        ):
            raise ValueError("strict validation requires background, stub and text colors")
        if expected_background_image is not None and (
            expected_stub is None or expected_text is None
        ):
            raise ValueError("strict validation requires stub and text colors")
        strict_text_contract = _normalize_external_text_contract(
            expected_title,
            expected_title_lines,
            expected_date,
            expected_number,
            expected_code,
        )
    if expected_background is not None and expected_background_image is not None:
        raise ValueError("validate against only one background color or background image")
    if expected_background_image is not None:
        expected_background = _validate_background_image(
            output,
            expected_background_image,
            layout_id,
            shadow_preset,
        )
    elif expected_background is not None:
        _validate_background(output, expected_background, layout_id, shadow_preset)
    if require_renderer_metadata:
        assert strict_text_contract is not None
        _validate_renderer_metadata(
            renderer_metadata,
            source_path,
            photo_center_y,
            expected_background,
            expected_stub,
            expected_text,
            strip_neutral_borders,
            *strict_text_contract,
            layout_id,
            expected_background_image,
            shadow_preset,
        )

    source = open_prepared_source(source_path, strip_neutral_borders)
    expected = ImageOps.fit(
        source,
        (layout.photo_w, layout.photo_h),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, photo_center_y),
    )
    actual = output.crop(
        (
            layout.ticket_x + layout.photo_x,
            layout.ticket_y + layout.photo_y,
            layout.ticket_x + layout.photo_x + layout.photo_w,
            layout.ticket_y + layout.photo_y + layout.photo_h,
        )
    )
    safe_expected = expected.crop(
        (16, 16, layout.photo_w - 16, layout.photo_h - 16)
    )
    safe_actual = actual.crop(
        (16, 16, layout.photo_w - 16, layout.photo_h - 16)
    )
    if ImageChops.difference(safe_expected, safe_actual).getbbox() is not None:
        raise ValueError("photo panel does not match the aspect-preserving source crop")

    perforation_color = expected_perforation or expected_background or PERFORATION_COLOR
    if layout_id == LANDSCAPE:
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
            if should_be_dash and any(pixel != perforation_color for pixel in row):
                raise ValueError(f"perforation dash mismatch at local y={local_y}")
            if not should_be_dash and all(pixel == perforation_color for pixel in row):
                raise ValueError(f"unexpected perforation color in gap at local y={local_y}")

        top_row = [output.getpixel((x, TICKET_Y)) for x in range(x1, x2)]
        if any(pixel != perforation_color for pixel in top_row):
            raise ValueError("top perforation dash must start flush and square at ticket y=0")

        guard_x1 = x2
        guard_x2 = split_x + PERFORATION_GUARD_W
        guard = output.crop((guard_x1, TICKET_Y, guard_x2, TICKET_Y + TICKET_H))
        extrema = guard.getextrema()
        if any(low != high for low, high in extrema):
            raise ValueError(
                "stub guard band is not flat; possible second perforation or seam"
            )
        if expected_stub is not None:
            expected_extrema = tuple(
                value for channel in expected_stub for value in (channel, channel)
            )
            flattened_extrema = tuple(value for channel in extrema for value in channel)
            if flattened_extrema != expected_extrema:
                raise ValueError(
                    "stub guard band does not match expected color "
                    f"{rgb_to_hex(expected_stub)}"
                )
        text_region_box = (
            split_x + PERFORATION_GUARD_W + 4,
            TICKET_Y,
            TICKET_X + TICKET_W,
            TICKET_Y + TICKET_H,
        )
    else:
        expected_line = Image.new("RGB", (layout.ticket_w, layout.ticket_h), expected_stub or (0, 0, 0))
        draw_portrait_perforation(expected_line, perforation_color, layout)
        actual_ticket = output.crop(
            (
                layout.ticket_x,
                layout.ticket_y,
                layout.ticket_x + layout.ticket_w,
                layout.ticket_y + layout.ticket_h,
            )
        )
        band_y1 = layout.divider_position - 2
        band_y2 = layout.divider_position + 2
        expected_band = expected_line.crop((0, band_y1, layout.ticket_w, band_y2))
        actual_band = actual_ticket.crop((0, band_y1, layout.ticket_w, band_y2))
        band_mask = make_portrait_ticket_mask(layout).crop(
            (0, band_y1, layout.ticket_w, band_y2)
        )
        difference = ImageChops.difference(actual_band, expected_band)
        checked = Image.composite(
            difference,
            Image.new("RGB", difference.size, (0, 0, 0)),
            band_mask,
        )
        if checked.getbbox() is not None:
            raise ValueError("portrait perforation does not match the deterministic horizontal divider")
        text_region_box = (
            layout.ticket_x,
            layout.ticket_y + layout.divider_position + 20,
            layout.ticket_x + layout.ticket_w,
            layout.ticket_y + layout.ticket_h,
        )
    if expected_text is not None:
        text_region = output.crop(text_region_box)
        exact_text_pixels = sum(
            1 for pixel in text_region.getdata() if pixel == expected_text
        )
        if exact_text_pixels < 50:
            raise ValueError(
                "expected text color is not present in the information stub: "
                f"{rgb_to_hex(expected_text)}"
            )
    if expected_stub is not None and expected_text is not None:
        strict_title = strict_text_contract[0] if strict_text_contract else None
        strict_title_lines = strict_text_contract[1] if strict_text_contract else None
        strict_date = strict_text_contract[2] if strict_text_contract else None
        strict_number = strict_text_contract[3] if strict_text_contract else None
        strict_code = strict_text_contract[4] if strict_text_contract else None
        _validate_stub_exact(
            output,
            renderer_metadata,
            expected_stub,
            expected_text,
            perforation_color,
            font_path,
            body_font_path,
            strict_title,
            strict_title_lines,
            strict_date,
            strict_number,
            strict_code,
            layout_id,
        )

    return _validate_palette(
        expected_background,
        expected_stub,
        expected_text,
        palette_mode,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--photo-source", type=Path, required=True)
    parser.add_argument("--photo-center-y", type=float, default=0.5)
    parser.add_argument("--layout", choices=LAYOUT_IDS, default=LANDSCAPE)
    parser.add_argument("--expected-background-color", type=parse_hex_color)
    parser.add_argument("--expected-background-image", type=Path)
    parser.add_argument("--shadow-preset")
    parser.add_argument("--expected-stub-color", type=parse_hex_color)
    parser.add_argument("--expected-text-color", type=parse_hex_color)
    parser.add_argument("--expected-perforation-color", type=parse_hex_color)
    parser.add_argument("--palette-json", type=Path)
    parser.add_argument("--palette-candidate", default="quiet-light")
    parser.add_argument(
        "--palette-mode",
        choices=("adaptive", "user-specified"),
        default="adaptive",
    )
    parser.add_argument("--require-renderer-metadata", action="store_true")
    parser.add_argument("--font", type=Path)
    parser.add_argument("--body-font", type=Path)
    expected_title_group = parser.add_mutually_exclusive_group()
    expected_title_group.add_argument("--expected-title")
    expected_title_group.add_argument(
        "--expected-title-line",
        action="append",
        dest="expected_title_lines",
    )
    parser.add_argument("--expected-date")
    parser.add_argument("--expected-number")
    parser.add_argument("--expected-code")
    parser.add_argument(
        "--keep-neutral-borders",
        action="store_true",
        help="Preserve intentional solid white/black framing at the photo edge",
    )
    args = parser.parse_args()
    if not 0.0 <= args.photo_center_y <= 1.0:
        parser.error("--photo-center-y must be between 0 and 1")
    expected_background = args.expected_background_color
    expected_stub = args.expected_stub_color
    expected_text = args.expected_text_color
    if args.palette_json:
        palette_background, palette_stub, palette_text = load_palette_candidate(
            args.palette_json,
            args.palette_candidate,
            args.photo_source,
            args.photo_center_y,
            not args.keep_neutral_borders,
            args.layout,
        )
        if args.expected_background_image is None:
            expected_background = expected_background or palette_background
        expected_stub = expected_stub or palette_stub
        expected_text = expected_text or palette_text
    warnings = validate(
        output_path=args.output,
        source_path=args.photo_source,
        photo_center_y=args.photo_center_y,
        expected_background=expected_background,
        expected_stub=expected_stub,
        expected_text=expected_text,
        expected_perforation=args.expected_perforation_color,
        palette_mode=args.palette_mode,
        require_renderer_metadata=args.require_renderer_metadata,
        strip_neutral_borders=not args.keep_neutral_borders,
        font_path=args.font,
        expected_title=args.expected_title,
        expected_title_lines=args.expected_title_lines,
        expected_date=args.expected_date,
        expected_number=args.expected_number,
        expected_code=args.expected_code,
        body_font_path=args.body_font,
        layout_id=args.layout,
        expected_background_image=args.expected_background_image,
        shadow_preset=args.shadow_preset,
    )
    for warning in warnings:
        print(f"WARN: {warning}")
    print(f"PASS: {args.output}")


if __name__ == "__main__":
    main()
