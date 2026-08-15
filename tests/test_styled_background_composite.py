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


class StyledBackgroundCompositeTests(unittest.TestCase):
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
