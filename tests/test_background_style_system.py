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


class BackgroundStyleSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry()

    def test_registry_has_twenty_complete_styles(self) -> None:
        self.assertEqual(validate_registry(self.registry), [])
        self.assertEqual(len(self.registry["styles"]), 20)

    def test_travertine_compiles_with_strict_preservation(self) -> None:
        resolved = resolve_style(
            self.registry,
            "travertine_luxury",
            strength="balanced",
            lighting="soft_daylight",
            shadow="premium_float",
        )
        prompt = compile_prompt(resolved, self.registry)
        self.assertIn("premium light travertine", prompt)
        self.assertIn("Keep original proportions, typography, people", prompt)
        self.assertIn("no neon", prompt)

    def test_named_strength_is_clamped_to_style_limits(self) -> None:
        resolved = resolve_style(self.registry, "frosted_cream", strength="strong")
        self.assertEqual(resolved["strength"]["requested"], 0.75)
        self.assertEqual(resolved["strength"]["effective"], 0.55)

    def test_recommender_prefers_context_and_diversity(self) -> None:
        results = recommend_styles(self.registry, "给我 10 个高级旅行票根背景方案", 10)
        ids = [item["style_id"] for item in results]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        self.assertTrue({"travertine_luxury", "cream_art_paper"}.intersection(ids))
        materials = {item["material"] for item in results}
        self.assertGreaterEqual(len(materials), 8)

    def test_generic_ten_options_use_curated_diverse_order(self) -> None:
        results = recommend_styles(self.registry, "给我10个背景方案", 10)
        self.assertEqual(
            [item["style_id"] for item in results],
            self.registry["diverse_default_order"][:10],
        )


if __name__ == "__main__":
    unittest.main()
