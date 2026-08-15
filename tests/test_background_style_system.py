from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from background_style_system import (  # noqa: E402
    compile_prompt,
    load_registry,
    recommend_styles,
    resolve_style,
    validate_registry,
)
from build_style_contact_sheet import style_id_from_item  # noqa: E402


class BackgroundStyleSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry()

    def test_registry_has_twelve_reference_locked_styles(self) -> None:
        self.assertEqual(validate_registry(self.registry), [])
        self.assertEqual(len(self.registry["styles"]), 12)
        orders = {
            style["reference_anchor"]["order"]
            for style in self.registry["styles"].values()
        }
        self.assertEqual(orders, set(range(1, 13)))

    def test_legacy_twenty_style_registry_still_validates(self) -> None:
        legacy = load_registry(ROOT / "references" / "background-styles.json")
        self.assertEqual(validate_registry(legacy), [])
        self.assertEqual(len(legacy["styles"]), 20)

    def test_reference_travertine_compiles_with_strict_preservation(self) -> None:
        resolved = resolve_style(
            self.registry,
            "ivory_travertine_diagonal",
            strength="balanced",
            lighting="stone_diagonal",
            shadow="architectural",
        )
        prompt = compile_prompt(resolved, self.registry)
        self.assertIn("premium ivory travertine", prompt)
        self.assertIn("Keep original proportions, typography, people", prompt)
        self.assertIn("Gallery order: 10", prompt)
        self.assertIn("wide diagonal illumination", prompt)
        self.assertIn("no neon", prompt)

    def test_palette_defaults_to_photo_adaptive(self) -> None:
        resolved = resolve_style(self.registry, "第5种")
        self.assertEqual(resolved["palette"]["mode"], "adaptive")
        self.assertIsNone(resolved["palette"]["theme_color"])
        prompt = compile_prompt(resolved, self.registry)
        self.assertIn("Palette mode: adaptive", prompt)
        self.assertIn("do not force the registry hue", prompt)

    def test_unified_palette_keeps_explicit_theme_color(self) -> None:
        resolved = resolve_style(
            self.registry,
            "第5种",
            palette_mode="unified",
            theme_color="#8fa6ad",
        )
        self.assertEqual(resolved["palette"]["mode"], "unified")
        self.assertEqual(resolved["palette"]["theme_color"], "#8FA6AD")
        self.assertIn("Selected theme color: #8FA6AD", compile_prompt(resolved, self.registry))

    def test_named_strength_is_clamped_to_style_limits(self) -> None:
        resolved = resolve_style(self.registry, "ivory_paper_window_veil", strength="strong")
        self.assertEqual(resolved["strength"]["requested"], 0.75)
        self.assertEqual(resolved["strength"]["effective"], 0.6)

    def test_style_selector_accepts_order_chinese_name_and_id(self) -> None:
        selectors = (
            "第10种",
            "第十种",
            "象牙洞石斜光",
            "ivory_travertine_diagonal",
        )
        for selector in selectors:
            with self.subTest(selector=selector):
                resolved = resolve_style(self.registry, selector)
                self.assertEqual(resolved["style_id"], "ivory_travertine_diagonal")
                self.assertEqual(resolved["requested_style"], selector)

    def test_recommender_prefers_context_and_diversity(self) -> None:
        results = recommend_styles(self.registry, "给我 10 个高级旅行票根背景方案", 10)
        ids = [item["style_id"] for item in results]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        self.assertTrue({"ivory_travertine_diagonal", "ivory_paper_window_veil"}.intersection(ids))
        materials = {item["material"] for item in results}
        self.assertGreaterEqual(len(materials), 8)

    def test_generic_ten_options_use_curated_diverse_order(self) -> None:
        results = recommend_styles(self.registry, "给我10个背景方案", 10)
        self.assertEqual(
            [item["style_id"] for item in results],
            self.registry["diverse_default_order"][:10],
        )

    def test_contact_sheet_accepts_explicit_or_filename_style_id(self) -> None:
        explicit = {"filename": "preview.png", "style_id": "sand_center_glow"}
        derived = {"filename": "03-coffee-sand_center_glow.png"}
        self.assertEqual(style_id_from_item(explicit, self.registry), "sand_center_glow")
        self.assertEqual(style_id_from_item(derived, self.registry), "sand_center_glow")


if __name__ == "__main__":
    unittest.main()
