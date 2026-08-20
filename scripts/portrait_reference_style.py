#!/usr/bin/env python3
"""Measured colour anchors for the portrait ticket reference."""

from __future__ import annotations

from palette_utils import RGB


PORTRAIT_REFERENCE_BACKGROUND: RGB = (146, 148, 110)  # #92946E
PORTRAIT_REFERENCE_TEXT: RGB = (27, 24, 17)  # #1B1811
PORTRAIT_REFERENCE_TICKET_CANDIDATES: tuple[tuple[str, str, RGB], ...] = (
    ("quiet-light", "参考暖象牙", (232, 222, 207)),  # #E8DECF
    ("editorial-mid", "旧纸暖米", (226, 214, 196)),  # #E2D6C4
    ("cinematic-deep", "复古羊皮", (217, 202, 181)),  # #D9CAB5
)
