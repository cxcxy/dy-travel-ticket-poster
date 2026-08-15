#!/usr/bin/env python3
"""Resolve, recommend, validate, and compile background styles into prompts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = (
    Path(__file__).resolve().parent.parent
    / "references"
    / "gallery-12-background-styles.json"
)
REQUIRED_STYLE_FIELDS = (
    "name",
    "category",
    "description",
    "background_material.primary",
    "background_material.secondary",
    "background_material.realism",
    "color_system.base",
    "color_system.secondary",
    "color_system.highlight",
    "color_system.temperature",
    "color_system.saturation",
    "texture.type",
    "texture.scale",
    "texture.density",
    "texture.strength",
    "lighting.recommended_preset",
    "shadow.recommended_preset",
    "depth.level",
    "depth.technique",
    "grain.type",
    "grain.strength",
    "atmosphere.keywords",
    "composition_relation.subject_contrast",
    "composition_relation.visual_priority",
    "intensity.default",
    "intensity.min",
    "intensity.max",
    "best_for",
    "avoid",
    "prompt_fragment",
)
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def nested_get(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(path)
        current = current[part]
    return current


def validate_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    styles = registry.get("styles")
    if not isinstance(styles, dict):
        return ["styles must be an object"]
    expected_count = registry.get("expected_style_count", 20)
    if not isinstance(expected_count, int) or expected_count < 1:
        errors.append("expected_style_count must be a positive integer")
    elif len(styles) != expected_count:
        errors.append(f"expected exactly {expected_count} styles, found {len(styles)}")

    for preset_group in (
        "strength_presets",
        "lighting_presets",
        "shadow_presets",
        "subject_preservation_modes",
    ):
        if not isinstance(registry.get(preset_group), dict) or not registry[preset_group]:
            errors.append(f"{preset_group} must be a non-empty object")

    lighting = registry.get("lighting_presets", {})
    shadows = registry.get("shadow_presets", {})
    for preset_id, preset in lighting.items():
        for field in ("direction", "softness", "intensity", "temperature"):
            if field not in preset:
                errors.append(f"lighting_presets.{preset_id}: missing {field}")
        for field in ("softness", "intensity"):
            value = preset.get(field)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                errors.append(
                    f"lighting_presets.{preset_id}.{field} must be between 0 and 1"
                )
    for preset_id, preset in shadows.items():
        for field in ("distance", "blur", "opacity"):
            if not isinstance(preset.get(field), (int, float)):
                errors.append(f"shadow_presets.{preset_id}.{field} must be numeric")
        opacity = preset.get("opacity")
        if isinstance(opacity, (int, float)) and not 0 <= opacity <= 1:
            errors.append(f"shadow_presets.{preset_id}.opacity must be between 0 and 1")
    reference_orders: list[int] = []
    reference_hashes: list[str] = []
    requires_reference_anchor = isinstance(registry.get("reference_set"), dict)
    for style_id, style in styles.items():
        if not re.fullmatch(r"[a-z0-9_]+", style_id):
            errors.append(f"{style_id}: style_id must use lowercase letters, digits, underscores")
        for field in REQUIRED_STYLE_FIELDS:
            try:
                nested_get(style, field)
            except KeyError:
                errors.append(f"{style_id}: missing {field}")
        for field in ("base", "secondary", "highlight"):
            color = style.get("color_system", {}).get(field)
            if not isinstance(color, str) or not HEX_COLOR.fullmatch(color):
                errors.append(f"{style_id}: invalid color_system.{field}: {color!r}")
        intensity = style.get("intensity", {})
        minimum = intensity.get("min")
        default = intensity.get("default")
        maximum = intensity.get("max")
        if not all(isinstance(item, (int, float)) for item in (minimum, default, maximum)):
            errors.append(f"{style_id}: intensity values must be numeric")
        elif not 0 <= minimum <= default <= maximum <= 1:
            errors.append(f"{style_id}: expected 0 <= min <= default <= max <= 1")
        if style.get("lighting", {}).get("recommended_preset") not in lighting:
            errors.append(f"{style_id}: unknown recommended lighting preset")
        if style.get("shadow", {}).get("recommended_preset") not in shadows:
            errors.append(f"{style_id}: unknown recommended shadow preset")
        if requires_reference_anchor:
            anchor = style.get("reference_anchor")
            if not isinstance(anchor, dict):
                errors.append(f"{style_id}: missing reference_anchor")
            else:
                order = anchor.get("order")
                source_file = anchor.get("source_file")
                source_hash = anchor.get("sha256")
                observed_base = anchor.get("observed_base")
                visual_signature = anchor.get("visual_signature")
                if not isinstance(order, int):
                    errors.append(f"{style_id}: reference_anchor.order must be an integer")
                else:
                    reference_orders.append(order)
                if not isinstance(source_file, str) or not source_file.strip():
                    errors.append(f"{style_id}: reference_anchor.source_file is required")
                if not isinstance(source_hash, str) or not SHA256.fullmatch(source_hash):
                    errors.append(f"{style_id}: reference_anchor.sha256 must be lowercase SHA-256")
                else:
                    reference_hashes.append(source_hash)
                if not isinstance(observed_base, str) or not HEX_COLOR.fullmatch(observed_base):
                    errors.append(f"{style_id}: invalid reference_anchor.observed_base")
                if not isinstance(visual_signature, str) or not visual_signature.strip():
                    errors.append(f"{style_id}: reference_anchor.visual_signature is required")

    if requires_reference_anchor:
        expected_orders = list(range(1, len(styles) + 1))
        if sorted(reference_orders) != expected_orders:
            errors.append(
                f"reference_anchor.order must be unique and cover 1..{len(styles)}"
            )
        if len(reference_hashes) != len(set(reference_hashes)):
            errors.append("reference_anchor.sha256 values must be unique")

    known = set(styles)
    for index, route in enumerate(registry.get("routing", [])):
        for style_id in route.get("styles", []):
            if style_id not in known:
                errors.append(f"routing[{index}]: unknown style {style_id}")
    diverse_order = registry.get("diverse_default_order", [])
    for style_id in diverse_order:
        if style_id not in known:
            errors.append(f"diverse_default_order: unknown style {style_id}")
    if len(diverse_order) != len(styles) or set(diverse_order) != known:
        errors.append("diverse_default_order must contain every style exactly once")
    return errors


def _strength_value(registry: dict[str, Any], style: dict[str, Any], value: str | float) -> tuple[float, float]:
    if isinstance(value, str) and value in registry["strength_presets"]:
        requested = float(registry["strength_presets"][value])
    else:
        try:
            requested = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"unknown strength {value!r}; use subtle, balanced, strong, or 0..1") from exc
    if not 0 <= requested <= 1:
        raise ValueError("strength must be between 0 and 1")
    limits = style["intensity"]
    effective = min(float(limits["max"]), max(float(limits["min"]), requested))
    return requested, effective


def resolve_style(
    registry: dict[str, Any],
    style_id: str,
    strength: str | float = "balanced",
    lighting: str | None = None,
    shadow: str | None = None,
    preservation: str = "strict",
    temperature_shift: int = 0,
) -> dict[str, Any]:
    if style_id not in registry["styles"]:
        suggestions = recommend_styles(registry, style_id, 3)
        names = ", ".join(item["style_id"] for item in suggestions)
        raise ValueError(f"unknown style_id {style_id!r}; nearby recommendations: {names}")
    style = registry["styles"][style_id]
    requested, effective = _strength_value(registry, style, strength)
    lighting_id = lighting or style["lighting"]["recommended_preset"]
    shadow_id = shadow or style["shadow"]["recommended_preset"]
    if lighting_id not in registry["lighting_presets"]:
        raise ValueError(f"unknown lighting preset: {lighting_id}")
    if shadow_id not in registry["shadow_presets"]:
        raise ValueError(f"unknown shadow preset: {shadow_id}")
    if preservation not in registry["subject_preservation_modes"]:
        raise ValueError(f"unknown subject preservation mode: {preservation}")
    if not -100 <= temperature_shift <= 100:
        raise ValueError("temperature_shift must be between -100 and 100")
    return {
        "style_id": style_id,
        "style": style,
        "strength": {"requested": requested, "effective": effective},
        "lighting": {"preset": lighting_id, **registry["lighting_presets"][lighting_id]},
        "shadow": {"preset": shadow_id, **registry["shadow_presets"][shadow_id]},
        "subject_preservation": {
            "mode": preservation,
            "instruction": registry["subject_preservation_modes"][preservation],
        },
        "temperature_shift": temperature_shift,
    }


def _profile(style: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        style["background_material"]["primary"],
        style["category"][0],
        style["color_system"]["temperature"],
        style["lighting"]["recommended_preset"],
        style["depth"]["level"],
    )


def _distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return sum(a != b for a, b in zip(_profile(left), _profile(right))) / 5.0


def recommend_styles(registry: dict[str, Any], context: str, count: int = 10) -> list[dict[str, Any]]:
    styles = registry["styles"]
    count = max(1, min(count, len(styles)))
    lowered = context.casefold()
    relevance = {style_id: 0.0 for style_id in styles}
    matched_routes: list[list[str]] = []
    for route in registry.get("routing", []):
        if any(keyword.casefold() in lowered for keyword in route["keywords"]):
            matched_routes.append(route["styles"])
            for rank, style_id in enumerate(route["styles"]):
                relevance[style_id] += 8.0 - rank

    for style_id, style in styles.items():
        searchable = " ".join(
            [style_id, style["name"], style["description"]]
            + style["category"]
            + style["best_for"]
            + style["atmosphere"]["keywords"]
        ).casefold()
        for token in re.findall(r"[\w\-]+", lowered):
            if len(token) >= 2 and token in searchable:
                relevance[style_id] += 1.0

    base_order = []
    for route in matched_routes:
        base_order.extend(route)
    base_order.extend(registry["diverse_default_order"])
    base_order.extend(styles)
    order_index: dict[str, int] = {}
    for style_id in base_order:
        order_index.setdefault(style_id, len(order_index))

    if not any(relevance.values()):
        # The curated order intentionally spans textile, paper, stone, plaster,
        # suede, cement, washi, satin, light-shadow, and parchment families.
        selected = registry["diverse_default_order"][:count]
    else:
        selected = []
        remaining = set(styles)
        while remaining and len(selected) < count:
            def score(style_id: str) -> tuple[float, float, int]:
                diversity = 1.0 if not selected else min(
                    _distance(styles[style_id], styles[chosen]) for chosen in selected
                )
                return (
                    relevance[style_id] * 3.0 + diversity * 4.0,
                    relevance[style_id],
                    -order_index[style_id],
                )

            chosen = max(remaining, key=score)
            selected.append(chosen)
            remaining.remove(chosen)

    return [
        {
            "style_id": style_id,
            "name": styles[style_id]["name"],
            "material": styles[style_id]["background_material"]["primary"],
            "lighting": styles[style_id]["lighting"]["recommended_preset"],
            "temperature": styles[style_id]["color_system"]["temperature"],
            "depth": styles[style_id]["depth"]["level"],
            "reason": "matched context" if relevance[style_id] else "selected for visual diversity",
        }
        for style_id in selected
    ]


def compile_prompt(resolved: dict[str, Any], registry: dict[str, Any]) -> str:
    style = resolved["style"]
    material = style["background_material"]
    colors = style["color_system"]
    texture = style["texture"]
    lighting = resolved["lighting"]
    shadow = resolved["shadow"]
    atmosphere = ", ".join(style["atmosphere"]["keywords"])
    avoid = ", ".join(style["avoid"])
    negative = ", ".join(registry["negative_prompt"])
    light_pattern = lighting.get("pattern", "natural low-contrast illumination")
    safe_zone = lighting.get("safe_zone", "keep the subject-safe region restrained")
    anchor = style.get("reference_anchor")
    reference_identity = ""
    if isinstance(anchor, dict):
        reference_identity = f"""[REFERENCE-LOCKED STYLE IDENTITY]
Gallery order: {anchor['order']:02d}. Visual signature: {anchor['visual_signature']}.
Use the reference only for background material, light pattern, tonal falloff and spatial depth. Never copy its photograph, people, text, codes or ticket content.

"""
    return f"""[SUBJECT PRESERVATION]
{resolved['subject_preservation']['instruction']}

{reference_identity}[BACKGROUND MATERIAL]
{material['primary']}; secondary material: {material['secondary']}; realism: {material['realism']}.
{style['prompt_fragment']}.

[COLOR]
Base {colors['base']}; secondary {colors['secondary']}; highlight {colors['highlight']}.
Temperature: {colors['temperature']}; saturation: {colors['saturation']}; temperature shift: {resolved['temperature_shift']:+d}.

[TEXTURE]
{texture['type']}; scale: {texture['scale']}; density: {texture['density']}; native strength: {texture['strength']:.2f}.
Overall style intensity: {resolved['strength']['effective']:.2f} (requested {resolved['strength']['requested']:.2f}).

[LIGHT]
Preset {lighting['preset']}; direction: {lighting['direction']}; softness: {lighting['softness']:.2f}; intensity: {lighting['intensity']:.2f}; temperature: {lighting['temperature']}.
Pattern: {light_pattern}. Ticket-safe behavior: {safe_zone}.

[SHADOW]
Preset {shadow['preset']}; distance: {shadow['distance']}; blur: {shadow['blur']}; opacity: {shadow['opacity']:.2f}.

[DEPTH AND ATMOSPHERE]
Depth: {style['depth']['level']}; technique: {style['depth']['technique']}.
Atmosphere: {atmosphere}. Subject remains the first visual priority.

[QUALITY]
premium editorial styling, realistic materials, subtle tactile detail, controlled contrast, natural shadows, high-end graphic design presentation.

[NEGATIVE]
{negative}; avoid style-specific failures: {avoid}.
"""


def dump_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")
    subparsers.add_parser("list")

    recommend = subparsers.add_parser("recommend")
    recommend.add_argument("--context", required=True)
    recommend.add_argument("--count", type=int, default=10)

    for command in ("resolve", "prompt"):
        child = subparsers.add_parser(command)
        child.add_argument("--style-id", required=True)
        child.add_argument("--strength", default="balanced")
        child.add_argument("--lighting")
        child.add_argument("--shadow")
        child.add_argument("--preservation", default="strict")
        child.add_argument("--temperature-shift", type=int, default=0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    registry = load_registry(args.registry)
    errors = validate_registry(registry)
    if errors:
        dump_json({"status": "error", "errors": errors})
        raise SystemExit(1)
    if args.command == "validate":
        dump_json({
            "status": "ok",
            "version": registry["version"],
            "style_count": len(registry["styles"]),
            "reference_set": registry.get("reference_set", {}).get("name"),
        })
    elif args.command == "list":
        dump_json([
            {
                "style_id": style_id,
                "name": style["name"],
                "category": style["category"],
                "reference_order": style.get("reference_anchor", {}).get("order"),
            }
            for style_id, style in registry["styles"].items()
        ])
    elif args.command == "recommend":
        dump_json(recommend_styles(registry, args.context, args.count))
    else:
        try:
            resolved = resolve_style(
                registry,
                args.style_id,
                args.strength,
                args.lighting,
                args.shadow,
                args.preservation,
                args.temperature_shift,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(2) from exc
        if args.command == "resolve":
            dump_json(resolved)
        else:
            print(compile_prompt(resolved, registry))


if __name__ == "__main__":
    main()
