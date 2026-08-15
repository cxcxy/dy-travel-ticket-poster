from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


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
from build_subtle_texture_background import build_subtle_background  # noqa: E402


class StyledBackgroundCompositeTests(unittest.TestCase):
    def test_default_background_is_deterministic_near_solid_with_subtle_texture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.png"
            second = root / "second.png"
            build_subtle_background(first, (108, 141, 156), seed=40817, texture_strength=3)
            build_subtle_background(second, (108, 141, 156), seed=40817, texture_strength=3)

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
                background,
                "premium_float",
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
                    background,
                )


if __name__ == "__main__":
    unittest.main()
