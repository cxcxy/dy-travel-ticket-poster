#!/usr/bin/env python3
"""Validate source fidelity, palette facts and canonical ticket geometry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from PIL import Image, ImageChops, ImageOps

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
from render_ticket_poster import build_stub


def _validate_background(output: Image.Image, expected_color: RGB) -> None:
    ticket_mask = make_ticket_mask()
    expected = build_background(expected_color)
    apply_ticket_shadow(expected, ticket_mask, expected_color)
    difference = ImageChops.difference(output, expected)
    # Ticket pixels may contain the photograph, stub and type. Every pixel
    # outside that exact silhouette must equal the canonical flat canvas plus
    # palette-aware shadow, including the narrow left/right gutters.
    difference.paste((0, 0, 0), (TICKET_X, TICKET_Y), ticket_mask)
    if difference.getbbox() is not None:
        raise ValueError(
            "canvas background or shadow differs from the expected solid-color construction "
            f"{rgb_to_hex(expected_color)}"
        )


def _validate_stub_exact(
    output: Image.Image,
    metadata: dict,
    stub: RGB,
    text: RGB,
    perforation: RGB,
    requested_font: Path | None = None,
    expected_title: str | None = None,
    expected_title_lines: list[str] | None = None,
    expected_date: str | None = None,
    expected_number: str | None = None,
    expected_code: str | None = None,
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
        else recorded_title_lines
    )
    title = (
        expected_title
        if expected_title is not None
        else metadata["dy_ticket_title"] or None
    )
    date = expected_date or metadata["dy_ticket_date"]
    number = expected_number or metadata["dy_ticket_number"]
    code = expected_code or metadata["dy_ticket_code"]

    # Locate the exact font files by their embedded hashes. The renderer uses a
    # single explicit font when --font is passed; otherwise it may use separate
    # title/body fonts. Exact reconstruction therefore requires both files.
    from render_ticket_poster import (
        BOLD_FONT_CANDIDATES,
        CJK_FONT_CANDIDATES,
        HEAVY_FONT_CANDIDATES,
    )

    available = []
    for candidate in (*HEAVY_FONT_CANDIDATES, *BOLD_FONT_CANDIDATES, *CJK_FONT_CANDIDATES):
        path = Path(candidate)
        if path.is_file() and path not in available:
            available.append(path)
    hash_to_path = {file_sha256(path): path for path in available}
    if requested_font is not None:
        if not requested_font.is_file():
            raise ValueError(f"validation font does not exist: {requested_font}")
        requested_hash = file_sha256(requested_font)
        title_font_path = (
            requested_font
            if requested_hash == metadata["dy_ticket_title_font_sha256"]
            else None
        )
        body_font_path = (
            requested_font
            if requested_hash == metadata["dy_ticket_body_font_sha256"]
            else None
        )
    else:
        title_font_path = hash_to_path.get(metadata["dy_ticket_title_font_sha256"])
        body_font_path = hash_to_path.get(metadata["dy_ticket_body_font_sha256"])
    if title_font_path is None or body_font_path is None:
        raise ValueError(
            "cannot reconstruct the exact stub because its recorded font file is unavailable"
        )
    if title_font_path != body_font_path:
        # build_stub accepts one explicit font. Reconstruct with its normal
        # deterministic selection, after verifying the selected files match.
        expected_stub, identity = build_stub(
            title,
            title_lines,
            date,
            number,
            code,
            stub,
            text,
            None,
        )
    else:
        expected_stub, identity = build_stub(
            title,
            title_lines,
            date,
            number,
            code,
            stub,
            text,
            title_font_path,
        )
    if identity["title_font_sha256"] != metadata["dy_ticket_title_font_sha256"]:
        raise ValueError("title font identity changed during exact-stub reconstruction")
    if identity["body_font_sha256"] != metadata["dy_ticket_body_font_sha256"]:
        raise ValueError("body font identity changed during exact-stub reconstruction")
    if identity["title_font_name"] != metadata["dy_ticket_title_font_name"]:
        raise ValueError("title font name does not match its recorded file identity")
    if identity["body_font_name"] != metadata["dy_ticket_body_font_name"]:
        raise ValueError("body font name does not match its recorded file identity")

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
    # Every visible stub pixel, including the perforation and edge pixels, must
    # be byte-for-byte identical to deterministic reconstruction.
    ticket_mask = make_ticket_mask().crop((PHOTO_W, 0, TICKET_W, TICKET_H))
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
    if metadata["dy_ticket_renderer"] != "1":
        raise ValueError("unsupported deterministic renderer metadata version")
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
) -> list[str]:
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
        if any(
            color is None
            for color in (expected_background, expected_stub, expected_text)
        ):
            raise ValueError(
                "strict validation requires background, stub and text colors"
            )
        strict_text_contract = _normalize_external_text_contract(
            expected_title,
            expected_title_lines,
            expected_date,
            expected_number,
            expected_code,
        )
    if expected_background is not None:
        _validate_background(output, expected_background)
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
        )

    source = open_prepared_source(source_path, strip_neutral_borders)
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
    perforation_color = expected_perforation or expected_background or PERFORATION_COLOR
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
    if expected_text is not None:
        text_region = output.crop(
            (
                split_x + PERFORATION_GUARD_W + 4,
                TICKET_Y,
                TICKET_X + TICKET_W,
                TICKET_Y + TICKET_H,
            )
        )
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
            strict_title,
            strict_title_lines,
            strict_date,
            strict_number,
            strict_code,
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
    parser.add_argument("--expected-background-color", type=parse_hex_color)
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
        )
        expected_background = expected_background or palette_background
        expected_stub = expected_stub or palette_stub
        expected_text = expected_text or palette_text
    warnings = validate(
        args.output,
        args.photo_source,
        args.photo_center_y,
        expected_background,
        expected_stub,
        expected_text,
        args.expected_perforation_color,
        args.palette_mode,
        args.require_renderer_metadata,
        not args.keep_neutral_borders,
        args.font,
        args.expected_title,
        args.expected_title_lines,
        args.expected_date,
        args.expected_number,
        args.expected_code,
    )
    for warning in warnings:
        print(f"WARN: {warning}")
    print(f"PASS: {args.output}")


if __name__ == "__main__":
    main()
