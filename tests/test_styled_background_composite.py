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


class StyledBackgroundCompositeTests(unittest.TestCase):
    def test_batch_reuses_one_background_plate_but_keeps_distinct_photos(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            background = root / "background.png"
            red_photo = root / "red.png"
            green_photo = root / "green.png"
            Image.new("RGB", CANVAS_SIZE, (219, 207, 189)).save(background)
            Image.new("RGB", (1200, 900), (210, 32, 28)).save(red_photo)
            Image.new("RGB", (1200, 900), (24, 180, 70)).save(green_photo)

            base = {
                "style_id": "ivory_travertine_diagonal",
                "title_lines": ["BATCH", "TEST"],
                "date": "2026 - 08",
                "number": "NO.12345",
                "code": "A1B2C3D4",
                "stub_color": "#543719",
                "background_image": str(background),
                "shadow_preset": "architectural",
            }
            first = build_ticket(
                {**base, "source": str(red_photo), "filename": "red-ticket.png"},
                root,
            )
            second = build_ticket(
                {**base, "source": str(green_photo), "filename": "green-ticket.png"},
                root,
            )
            first_image = Image.open(first).convert("RGB")
            second_image = Image.open(second).convert("RGB")

            self.assertEqual(
                first_image.crop((0, 0, CANVAS_SIZE[0], 350)).tobytes(),
                second_image.crop((0, 0, CANVAS_SIZE[0], 350)).tobytes(),
            )
            photo_point = (TICKET_X + PHOTO_W // 2, TICKET_Y + TICKET_H // 2)
            self.assertEqual(first_image.getpixel(photo_point), (210, 32, 28))
            self.assertEqual(second_image.getpixel(photo_point), (24, 180, 70))

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
