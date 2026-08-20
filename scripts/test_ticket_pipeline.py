#!/usr/bin/env python3
"""Regression tests for palette selection, rendering and output validation."""

from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

from normalize_reference_layout import normalize
from palette_utils import load_palette_candidate, parse_hex_color
from recolor_existing_poster import recolor
from render_ticket_poster import _body_font_path, _font_path, render
from suggest_palette import suggest_palettes
from ticket_layouts import PORTRAIT, get_layout
from validate_ticket_output import validate


class TicketPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source.png"
        image = Image.new("RGB", (1400, 1000), (143, 166, 176))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 360, 1000), fill=(75, 100, 79))
        draw.rectangle((360, 180, 1050, 920), fill=(188, 135, 104))
        draw.rectangle((1050, 0, 1400, 1000), fill=(53, 74, 83))
        draw.ellipse((560, 270, 850, 740), fill=(225, 204, 180))
        image.save(self.source, format="PNG")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _render(self) -> tuple[Path, tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
        palette = suggest_palettes(self.source)["candidates"][0]
        background = parse_hex_color(palette["background"])
        stub = parse_hex_color(palette["stub"])
        text = parse_hex_color(palette["text"])
        output = self.root / "ticket.png"
        render(
            self.source,
            output,
            "OLD TOWN",
            None,
            "2026 - 08",
            "NO.19427",
            "E5R8K3M2",
            background,
            stub,
            text,
            0.5,
        )
        return output, background, stub, text

    def _render_portrait(self) -> tuple[Path, tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
        palette = suggest_palettes(self.source, layout_id=PORTRAIT)["candidates"][0]
        background = parse_hex_color(palette["background"])
        stub = parse_hex_color(palette["stub"])
        text = parse_hex_color(palette["text"])
        output = self.root / "portrait-ticket.png"
        render(
            self.source,
            output,
            "OLD TOWN",
            None,
            "2026 - 08",
            "NO.19427",
            "E5R8K3M2",
            background,
            stub,
            text,
            0.5,
            layout_id=PORTRAIT,
        )
        return output, background, stub, text

    def _mutate_renderer_png(
        self,
        source_path: Path,
        destination_path: Path,
        mutate,
    ) -> None:
        """Preserve renderer metadata so corruption tests exercise exact pixels."""
        with Image.open(source_path) as opened:
            image = opened.convert("RGB")
            metadata = {
                key: value
                for key, value in opened.info.items()
                if isinstance(value, str)
            }
        mutate(image)
        png_info = PngImagePlugin.PngInfo()
        for key, value in metadata.items():
            png_info.add_text(key, value)
        image.save(destination_path, format="PNG", pnginfo=png_info)

    def test_palette_candidates_have_provenance_and_readable_text(self) -> None:
        result = suggest_palettes(self.source)
        self.assertEqual(len(result["candidates"]), 3)
        self.assertEqual(len(result["source_sha256"]), 64)
        for candidate in result["candidates"]:
            self.assertIn("background_source", candidate["provenance"])
            self.assertGreaterEqual(candidate["metrics"]["text_contrast"], 5.0)
            self.assertGreaterEqual(
                candidate["metrics"]["background_stub_delta_ok"], 0.10
            )

    def test_portrait_default_palette_matches_reference_relationship(self) -> None:
        result = suggest_palettes(self.source, layout_id=PORTRAIT)
        candidate = result["candidates"][0]
        self.assertEqual(result["palette_treatment"], "portrait-reference")
        self.assertEqual(candidate["background"], "#92946E")
        self.assertEqual(candidate["stub"], "#E8DECF")
        self.assertEqual(candidate["text"], "#1B1811")
        self.assertEqual(
            candidate["provenance"]["stub_source_role"],
            "portrait-reference-ticket-paper",
        )

    def test_portrait_can_explicitly_use_photo_derived_palette(self) -> None:
        result = suggest_palettes(
            self.source,
            layout_id=PORTRAIT,
            palette_treatment="photo-derived",
        )
        self.assertEqual(result["palette_treatment"], "photo-derived")
        self.assertNotEqual(result["candidates"][0]["stub"], "#E8DECF")

    def test_deterministic_render_passes_full_validation(self) -> None:
        output, background, stub, text = self._render()
        warnings = validate(
            output,
            self.source,
            0.5,
            background,
            stub,
            text,
            background,
            "adaptive",
            True,
            expected_title="OLD TOWN",
            expected_date="2026 - 08",
            expected_number="NO.19427",
            expected_code="E5R8K3M2",
        )
        self.assertIsInstance(warnings, list)

    def test_portrait_layout_passes_full_validation(self) -> None:
        output, background, stub, text = self._render_portrait()
        warnings = validate(
            output,
            self.source,
            0.5,
            background,
            stub,
            text,
            background,
            "adaptive",
            True,
            expected_title="OLD TOWN",
            expected_date="2026 - 08",
            expected_number="NO.19427",
            expected_code="E5R8K3M2",
            layout_id=PORTRAIT,
        )
        with Image.open(output) as opened:
            self.assertEqual(opened.info["dy_ticket_layout"], PORTRAIT)
        self.assertIsInstance(warnings, list)

    def test_portrait_layout_accepts_a_background_image(self) -> None:
        palette = suggest_palettes(self.source, layout_id=PORTRAIT)["candidates"][0]
        background = parse_hex_color(palette["background"])
        stub = parse_hex_color(palette["stub"])
        text = parse_hex_color(palette["text"])
        background_path = self.root / "portrait-background.png"
        plate = Image.new("RGB", (1170, 1560), background)
        ImageDraw.Draw(plate).rectangle((0, 0, 1169, 6), fill=tuple(min(255, value + 2) for value in background))
        plate.save(background_path)
        output = self.root / "portrait-image-background.png"
        render(
            self.source,
            output,
            "OLD TOWN",
            None,
            "2026 - 08",
            "NO.19427",
            "E5R8K3M2",
            None,
            stub,
            text,
            0.5,
            background_image_path=background_path,
            layout_id=PORTRAIT,
        )
        warnings = validate(
            output,
            self.source,
            0.5,
            expected_stub=stub,
            expected_text=text,
            expected_perforation=plate.getpixel((0, 0)),
            require_renderer_metadata=True,
            expected_title="OLD TOWN",
            expected_date="2026 - 08",
            expected_number="NO.19427",
            expected_code="E5R8K3M2",
            layout_id=PORTRAIT,
            expected_background_image=background_path,
        )
        self.assertIsInstance(warnings, list)

    def test_portrait_palette_provenance_is_layout_locked(self) -> None:
        result = suggest_palettes(self.source, layout_id=PORTRAIT)
        palette_path = self.root / "portrait-palette.json"
        palette_path.write_text(json.dumps(result), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "layout mismatch"):
            load_palette_candidate(
                palette_path,
                "quiet-light",
                self.source,
                0.5,
                True,
                "landscape",
            )

    def test_portrait_barcode_bars_are_uniform_height(self) -> None:
        output, _, _, text = self._render_portrait()
        layout = get_layout(PORTRAIT)
        with Image.open(output) as opened:
            rendered = opened.convert("RGB")
        barcode_left = layout.ticket_x + 66
        barcode_top = layout.ticket_y + 1012
        barcode_height = 88
        barcode_width = layout.ticket_w - 132
        observed_heights = set()
        for x_pos in range(barcode_left, barcode_left + barcode_width):
            text_rows = [
                y_pos
                for y_pos in range(barcode_top, barcode_top + barcode_height)
                if rendered.getpixel((x_pos, y_pos)) == text
            ]
            if text_rows:
                observed_heights.add(max(text_rows) - min(text_rows) + 1)
        self.assertEqual(observed_heights, {barcode_height})

    def test_body_copy_uses_a_separate_light_mono_font(self) -> None:
        output, _, _, _ = self._render()
        with Image.open(output) as opened:
            metadata = dict(opened.info)
        self.assertNotEqual(
            metadata["dy_ticket_title_font_sha256"],
            metadata["dy_ticket_body_font_sha256"],
        )
        body_font = ImageFont.truetype(_body_font_path(None), 27)
        self.assertEqual(body_font.getlength("1"), body_font.getlength("W"))

    def test_strict_validation_rejects_the_wrong_body_font(self) -> None:
        output, background, stub, text = self._render()
        with self.assertRaisesRegex(ValueError, "validation body font"):
            validate(
                output,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
                True,
                expected_title="OLD TOWN",
                expected_date="2026 - 08",
                expected_number="NO.19427",
                expected_code="E5R8K3M2",
                body_font_path=Path(_font_path(None, heavy=True)),
            )

    def test_rendered_barcode_bars_are_uniform_height(self) -> None:
        output, _, _, text = self._render()
        with Image.open(output) as opened:
            rendered = opened.convert("RGB")

        # Geometry is part of the public poster specification: the ticket starts
        # at (55, 501), while the barcode starts at local (822, 420) and is 43px
        # high within a 192px-wide area.
        barcode_left = 55 + 822
        barcode_top = 501 + 420
        barcode_height = 43
        barcode_width = 192
        observed_heights = set()
        for x_pos in range(barcode_left, barcode_left + barcode_width):
            text_rows = [
                y_pos
                for y_pos in range(barcode_top, barcode_top + barcode_height)
                if rendered.getpixel((x_pos, y_pos)) == text
            ]
            if text_rows:
                observed_heights.add(max(text_rows) - min(text_rows) + 1)

        self.assertEqual(observed_heights, {barcode_height})

    def test_strict_validation_requires_external_palette_and_text_contracts(self) -> None:
        output, background, stub, text = self._render()
        contract = {
            "expected_title": "OLD TOWN",
            "expected_date": "2026 - 08",
            "expected_number": "NO.19427",
            "expected_code": "E5R8K3M2",
        }
        with self.assertRaisesRegex(ValueError, "background, stub and text"):
            validate(
                output,
                self.source,
                0.5,
                background,
                None,
                None,
                background,
                "adaptive",
                True,
                **contract,
            )
        with self.assertRaisesRegex(ValueError, "expected title"):
            validate(
                output,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
                True,
            )
        with self.assertRaisesRegex(ValueError, "external text contract"):
            validate(
                output,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
                True,
                expected_title="ALTERED",
                expected_date="2026 - 08",
                expected_number="NO.19427",
                expected_code="E5R8K3M2",
            )

    def test_normalizer_runs_on_supported_pillow(self) -> None:
        rendered, background, stub, text = self._render()
        normalized = self.root / "normalized.png"
        normalize(
            rendered,
            normalized,
            (55, 501, 1112, 1008),
            829,
            self.source,
            0.5,
            background,
            background,
        )
        validate(
            normalized,
            self.source,
            0.5,
            background,
            stub,
            text,
            background,
            "adaptive",
        )

    def test_wrong_background_pixel_fails(self) -> None:
        output, background, stub, text = self._render()
        with Image.open(output) as opened:
            invalid = opened.convert("RGB")
        invalid.putpixel((0, 0), (255, 0, 0))
        invalid_path = self.root / "wrong-background.png"
        invalid.save(invalid_path, format="PNG")
        with self.assertRaisesRegex(ValueError, "background"):
            validate(
                invalid_path,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
            )

    def test_recolor_rebuilds_background_shadow_and_perforation(self) -> None:
        output, _, stub, text = self._render()
        recolored = self.root / "ticket-recolored.png"
        new_background = (30, 40, 50)
        recolor(output, recolored, new_background)
        warnings = validate(
            recolored,
            self.source,
            0.5,
            new_background,
            stub,
            text,
            new_background,
            "user-specified",
            True,
            expected_title="OLD TOWN",
            expected_date="2026 - 08",
            expected_number="NO.19427",
            expected_code="E5R8K3M2",
        )
        self.assertIsInstance(warnings, list)

    def test_portrait_recolor_preserves_layout_and_rebuilds_divider(self) -> None:
        output, _, stub, text = self._render_portrait()
        recolored = self.root / "portrait-recolored.png"
        new_background = (132, 148, 158)
        recolor(output, recolored, new_background)
        warnings = validate(
            recolored,
            self.source,
            0.5,
            new_background,
            stub,
            text,
            new_background,
            "user-specified",
            True,
            expected_title="OLD TOWN",
            expected_date="2026 - 08",
            expected_number="NO.19427",
            expected_code="E5R8K3M2",
            layout_id=PORTRAIT,
        )
        self.assertIsInstance(warnings, list)

    def test_central_canvas_gutter_corruption_fails(self) -> None:
        output, background, stub, text = self._render()
        with Image.open(output) as opened:
            invalid = opened.convert("RGB")
        invalid.putpixel((0, 720), (255, 0, 255))
        invalid_path = self.root / "wrong-gutter.png"
        invalid.save(invalid_path, format="PNG")
        with self.assertRaisesRegex(ValueError, "canvas background"):
            validate(
                invalid_path,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
            )

    def test_stub_color_patch_fails(self) -> None:
        output, background, stub, text = self._render()
        invalid_path = self.root / "wrong-stub.png"
        self._mutate_renderer_png(
            output,
            invalid_path,
            lambda image: ImageDraw.Draw(image).rectangle(
                (900, 700, 930, 730), fill=(0, 255, 0)
            ),
        )
        with self.assertRaisesRegex(ValueError, "information stub"):
            validate(
                invalid_path,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
            )

    def test_stub_mid_tone_patch_fails(self) -> None:
        output, background, stub, text = self._render()
        midpoint = tuple((left + right) // 2 for left, right in zip(stub, text))
        invalid_path = self.root / "wrong-stub-mid-tone.png"
        self._mutate_renderer_png(
            output,
            invalid_path,
            lambda image: ImageDraw.Draw(image).rectangle(
                (1010, 780, 1040, 810), fill=midpoint
            ),
        )
        with self.assertRaisesRegex(ValueError, "information stub"):
            validate(
                invalid_path,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
            )

    def test_stub_outer_visible_edge_patch_fails(self) -> None:
        output, background, stub, text = self._render()
        invalid_path = self.root / "wrong-stub-edge.png"
        self._mutate_renderer_png(
            output,
            invalid_path,
            lambda image: ImageDraw.Draw(image).rectangle(
                (1080, 560, 1090, 570), fill=(0, 255, 0)
            ),
        )
        with self.assertRaisesRegex(ValueError, "information stub"):
            validate(
                invalid_path,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
            )

    def test_alpha_channel_fails(self) -> None:
        output, background, stub, text = self._render()
        with Image.open(output) as opened:
            invalid = opened.convert("RGBA")
        invalid_path = self.root / "alpha.png"
        invalid.save(invalid_path, format="PNG")
        with self.assertRaisesRegex(ValueError, "alpha"):
            validate(
                invalid_path,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
            )

    def test_non_png_fails(self) -> None:
        output, background, stub, text = self._render()
        with Image.open(output) as opened:
            invalid = opened.convert("RGB")
        invalid_path = self.root / "ticket.bmp"
        invalid.save(invalid_path, format="BMP")
        with self.assertRaisesRegex(ValueError, "PNG"):
            validate(
                invalid_path,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
            )

    def test_palette_mode_png_fails_rgb_contract(self) -> None:
        output, background, stub, text = self._render()
        with Image.open(output) as opened:
            invalid = opened.convert("P", palette=Image.Palette.ADAPTIVE, colors=64)
        invalid_path = self.root / "palette-mode.png"
        invalid.save(invalid_path, format="PNG")
        with self.assertRaisesRegex(ValueError, "RGB mode"):
            validate(
                invalid_path,
                self.source,
                0.5,
                background,
                stub,
                text,
                background,
                "adaptive",
            )

    def test_low_contrast_palette_fails(self) -> None:
        _, background, stub, _ = self._render()
        output = self.root / "low-contrast.png"
        render(
            self.source,
            output,
            "DESERT",
            None,
            "2026 - 08",
            "NO.19427",
            "E5R8K3M2",
            background,
            stub,
            stub,
            0.5,
        )
        with self.assertRaisesRegex(ValueError, "contrast"):
            validate(
                output,
                self.source,
                0.5,
                background,
                stub,
                stub,
                background,
                "adaptive",
            )

    def test_user_palette_still_requires_canvas_stub_separation(self) -> None:
        background = (140, 140, 140)
        text = (20, 20, 20)
        output = self.root / "same-colors.png"
        render(
            self.source,
            output,
            "DESERT",
            None,
            "2026 - 08",
            "NO.19427",
            "E5R8K3M2",
            background,
            background,
            text,
            0.5,
        )
        with self.assertRaisesRegex(ValueError, "too similar"):
            validate(
                output,
                self.source,
                0.5,
                background,
                background,
                text,
                background,
                "user-specified",
            )

    def test_palette_provenance_rejects_other_source_or_crop(self) -> None:
        result = suggest_palettes(self.source)
        palette_path = self.root / "palette.json"
        palette_path.write_text(json.dumps(result), encoding="utf-8")
        other = self.root / "other.png"
        Image.new("RGB", (500, 500), (20, 40, 60)).save(other)
        with self.assertRaisesRegex(ValueError, "provenance"):
            load_palette_candidate(palette_path, "quiet-light", other, 0.5)
        with self.assertRaisesRegex(ValueError, "crop mismatch"):
            load_palette_candidate(palette_path, "quiet-light", self.source, 0.6)
        Image.new("RGB", (1400, 1000), (1, 2, 3)).save(self.source)
        with self.assertRaisesRegex(ValueError, "content changed"):
            load_palette_candidate(palette_path, "quiet-light", self.source, 0.5)

    def test_transparent_hidden_rgb_does_not_leak(self) -> None:
        transparent = self.root / "transparent.png"
        image = Image.new("RGBA", (800, 600), (255, 0, 255, 0))
        ImageDraw.Draw(image).rectangle((160, 80, 640, 520), fill=(35, 95, 145, 255))
        image.save(transparent)
        result = suggest_palettes(transparent)
        sources = {
            candidate["provenance"]["background_source"]
            for candidate in result["candidates"]
        }
        self.assertNotIn("#FF00FF", sources)
        output = self.root / "transparent-ticket.png"
        candidate = result["candidates"][0]
        render(
            transparent,
            output,
            "WATER",
            None,
            "2026 - 08",
            "NO.19427",
            "E5R8K3M2",
            parse_hex_color(candidate["background"]),
            parse_hex_color(candidate["stub"]),
            parse_hex_color(candidate["text"]),
            0.5,
        )
        with Image.open(output) as rendered:
            photo = rendered.convert("RGB").crop((55, 501, 55 + 774, 501 + 507))
        self.assertNotIn((255, 0, 255), set(photo.getdata()))


if __name__ == "__main__":
    unittest.main()
