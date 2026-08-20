from __future__ import annotations

import colorsys
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_reference_layout import (  # noqa: E402
    CANVAS_SIZE,
    PHOTO_W,
    TICKET_H,
    TICKET_W,
    TICKET_X,
    TICKET_Y,
    normalize,
)
from build_ticket_batch import build_ticket  # noqa: E402
from adapt_background_plate import adapt_plate, derive_theme_color  # noqa: E402
from build_subtle_texture_background import (  # noqa: E402
    MAX_LIGHTNESS,
    MAX_SATURATION,
    MIN_LIGHTNESS,
    MIN_SATURATION,
    PORTRAIT_REFERENCE_COLOR,
    build_portrait_reference_background,
    build_subtle_background,
    resolve_background_treatment,
    supporting_color,
)


class StyledBackgroundCompositeTests(unittest.TestCase):
    def test_auto_background_routes_portrait_to_reference_linen(self) -> None:
        self.assertEqual(
            resolve_background_treatment("auto", "portrait", "adaptive", None),
            "portrait-reference-linen",
        )
        self.assertEqual(
            resolve_background_treatment("auto", "landscape", "adaptive", None),
            "photo-matte",
        )
        self.assertEqual(
            resolve_background_treatment(
                "auto",
                "portrait",
                "adaptive",
                (80, 100, 120),
            ),
            "photo-matte",
        )
        self.assertEqual(
            resolve_background_treatment(
                "photo-matte",
                "portrait",
                "adaptive",
                None,
            ),
            "photo-matte",
        )

    def test_portrait_reference_linen_is_deterministic_and_textured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.png"
            second = root / "second.png"
            build_portrait_reference_background(first, seed=40817)
            build_portrait_reference_background(second, seed=40817)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with Image.open(first) as background:
                self.assertEqual(background.mode, "RGB")
                self.assertEqual(background.size, CANVAS_SIZE)
                top_left = background.crop((0, 0, 180, 180))
                bottom_right = background.crop(
                    (CANVAS_SIZE[0] - 180, CANVAS_SIZE[1] - 180, *CANVAS_SIZE)
                )
                top_mean = sum(pixel[0] for pixel in top_left.getdata()) / (
                    top_left.width * top_left.height
                )
                bottom_mean = sum(pixel[0] for pixel in bottom_right.getdata()) / (
                    bottom_right.width * bottom_right.height
                )
                top_right = background.crop(
                    (CANVAS_SIZE[0] - 180, 0, CANVAS_SIZE[0], 180)
                )
                right_mean = sum(pixel[0] for pixel in top_right.getdata()) / (
                    top_right.width * top_right.height
                )
                self.assertGreater(top_mean, bottom_mean + 28)
                self.assertGreater(top_mean, right_mean + 18)
                for minimum, maximum in background.getextrema():
                    self.assertGreater(maximum, minimum)
                    self.assertLessEqual(maximum - minimum, 96)
                center = background.crop((500, 700, 670, 860))
                self.assertGreater(len(set(center.getdata())), 8)
                center_luma = center.convert("L")
                horizontal_difference = ImageChops.difference(
                    center_luma.crop((0, 0, center.width - 1, center.height)),
                    center_luma.crop((1, 0, center.width, center.height)),
                )
                vertical_difference = ImageChops.difference(
                    center_luma.crop((0, 0, center.width, center.height - 1)),
                    center_luma.crop((0, 1, center.width, center.height)),
                )
                self.assertGreater(ImageStat.Stat(horizontal_difference).mean[0], 4.0)
                self.assertGreater(ImageStat.Stat(vertical_difference).mean[0], 6.0)
                self.assertGreater(ImageStat.Stat(center_luma).stddev[0], 8.0)
            self.assertEqual(PORTRAIT_REFERENCE_COLOR, (146, 148, 110))

    def test_default_background_retains_photo_hue_with_softened_saturation(self) -> None:
        source = (22, 103, 195)
        selected = supporting_color(source)
        source_hue, _source_lightness, source_saturation = colorsys.rgb_to_hls(
            *(channel / 255 for channel in source)
        )
        hue, lightness, saturation = colorsys.rgb_to_hls(
            *(channel / 255 for channel in selected)
        )

        self.assertAlmostEqual(hue, source_hue, places=2)
        self.assertGreater(saturation, MIN_SATURATION - 0.01)
        self.assertLessEqual(saturation, MAX_SATURATION + 0.01)
        self.assertLess(saturation, source_saturation)
        self.assertGreaterEqual(lightness, MIN_LIGHTNESS - 0.01)
        self.assertLessEqual(lightness, MAX_LIGHTNESS + 0.01)

    def test_default_background_is_deterministic_near_solid_with_subtle_texture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.png"
            second = root / "second.png"
            build_subtle_background(first, (108, 141, 156), seed=40817, texture_strength=2)
            build_subtle_background(second, (108, 141, 156), seed=40817, texture_strength=2)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            with Image.open(first) as background:
                self.assertEqual(background.mode, "RGB")
                self.assertEqual(background.size, CANVAS_SIZE)
                for minimum, maximum in background.getextrema():
                    self.assertGreater(maximum, minimum)
                    self.assertLessEqual(maximum - minimum, 8)

    def test_batch_adapts_background_per_photo_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = root / "material.png"
            red_background = root / "red-background.png"
            green_background = root / "green-background.png"
            red_photo = root / "red.png"
            green_photo = root / "green.png"
            Image.new("RGB", CANVAS_SIZE, (209, 158, 103)).save(material)
            Image.new("RGB", (1200, 900), (210, 32, 28)).save(red_photo)
            Image.new("RGB", (1200, 900), (24, 180, 70)).save(green_photo)
            red_theme, _ = derive_theme_color([red_photo], [0.5], "adaptive")
            green_theme, _ = derive_theme_color([green_photo], [0.5], "adaptive")
            adapt_plate(material, red_background, red_theme)
            adapt_plate(material, green_background, green_theme)

            base = {
                "style_id": "ivory_travertine_diagonal",
                "title_lines": ["BATCH", "TEST"],
                "date": "2026 - 08",
                "number": "NO.12345",
                "code": "A1B2C3D4",
                "stub_color": "#543719",
                "shadow_preset": "architectural",
            }
            first = build_ticket(
                {
                    **base,
                    "source": str(red_photo),
                    "filename": "red-ticket.png",
                    "background_image": str(red_background),
                },
                root,
            )
            second = build_ticket(
                {
                    **base,
                    "source": str(green_photo),
                    "filename": "green-ticket.png",
                    "background_image": str(green_background),
                },
                root,
            )
            first_image = Image.open(first).convert("RGB")
            second_image = Image.open(second).convert("RGB")

            self.assertNotEqual(
                first_image.crop((0, 0, CANVAS_SIZE[0], 350)).tobytes(),
                second_image.crop((0, 0, CANVAS_SIZE[0], 350)).tobytes(),
            )
            photo_point = (TICKET_X + PHOTO_W // 2, TICKET_Y + TICKET_H // 2)
            self.assertEqual(first_image.getpixel(photo_point), (210, 32, 28))
            self.assertEqual(second_image.getpixel(photo_point), (24, 180, 70))

    def test_unified_theme_color_produces_one_reusable_background(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = root / "material.png"
            red_photo = root / "red.png"
            blue_photo = root / "blue.png"
            first = root / "first.png"
            second = root / "second.png"
            Image.new("RGB", CANVAS_SIZE, (209, 158, 103)).save(material)
            Image.new("RGB", (900, 900), (190, 70, 55)).save(red_photo)
            Image.new("RGB", (900, 900), (70, 120, 170)).save(blue_photo)
            unified, extracted = derive_theme_color(
                [red_photo, blue_photo],
                [0.5],
                "unified",
            )
            self.assertIn(unified, extracted)
            adapt_plate(material, first, unified)
            adapt_plate(material, second, unified)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_legacy_solid_background_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "generated.png"
            source_photo = root / "photo.png"
            output = root / "output.png"
            Image.new("RGB", (TICKET_W, TICKET_H), (40, 70, 90)).save(generated)
            Image.new("RGB", (900, 900), (12, 210, 44)).save(source_photo)
            normalize(
                generated,
                output,
                (0, 0, TICKET_W, TICKET_H),
                PHOTO_W,
                source_photo,
                0.5,
                (135, 159, 171),
            )
            result = Image.open(output).convert("RGB")
            self.assertEqual(result.getpixel((0, 0)), (135, 159, 171))

    def test_background_plate_and_source_photo_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "generated.png"
            source_photo = root / "photo.png"
            background = root / "background.png"
            output = root / "output.png"

            ticket_preview = Image.new("RGB", (TICKET_W, TICKET_H), (40, 70, 90))
            ticket_preview.save(generated)
            Image.new("RGB", (1200, 900), (12, 210, 44)).save(source_photo)
            Image.new("RGB", CANVAS_SIZE, (191, 173, 151)).save(background)

            normalize(
                generated,
                output,
                (0, 0, TICKET_W, TICKET_H),
                PHOTO_W,
                source_photo,
                0.5,
                None,
                background_image_path=background,
                shadow_preset="premium_float",
            )

            result = Image.open(output).convert("RGB")
            self.assertEqual(result.size, CANVAS_SIZE)
            self.assertEqual(result.getpixel((0, 0)), (191, 173, 151))
            self.assertEqual(
                result.getpixel((TICKET_X + PHOTO_W // 2, TICKET_Y + TICKET_H // 2)),
                (12, 210, 44),
            )

    def test_background_plate_rejects_wrong_size(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "generated.png"
            source_photo = root / "photo.png"
            background = root / "background.png"
            Image.new("RGB", (TICKET_W, TICKET_H), (10, 10, 10)).save(generated)
            Image.new("RGB", (100, 100), (20, 20, 20)).save(source_photo)
            Image.new("RGB", (100, 100), (30, 30, 30)).save(background)
            with self.assertRaisesRegex(ValueError, "exactly"):
                normalize(
                    generated,
                    root / "out.png",
                    (0, 0, TICKET_W, TICKET_H),
                    PHOTO_W,
                    source_photo,
                    0.5,
                    None,
                    background_image_path=background,
                )


if __name__ == "__main__":
    unittest.main()
