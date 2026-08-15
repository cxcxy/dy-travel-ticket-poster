# DY Travel Ticket Poster

English | [简体中文](README.md) | [Live 12-style gallery](https://cxcxy.github.io/dy-travel-ticket-poster/)

Turn one photo or a batch of photos into a consistent series of travel-ticket posters. The Skill keeps the recognizable subject and scene from the source image, then builds a centered ticket with an adaptive color palette, a perforated information stub, neutral scene naming, a date, a serial number, and a decorative barcode.

The final deliverable for each photo is a clean `1170 × 1560` PNG in a `3:4` aspect ratio. Phone UI, notifications, player controls, and watermarks are excluded from the poster.

## 2026-08-15 update

- Added 12 gallery-locked configurable background styles addressable by order, Chinese display name, or canonical `style_id`.
- Changed the no-style default to a photo-derived near-solid background with extremely subtle monochrome tactile texture. The texture is held to roughly `base ±3`; gradients, vignettes, window shadows, leaf shadows, and spotlights are not added by default.
- Batch inputs now derive one theme hue per final photo crop. A shared color family is used only when explicitly requested.
- Added a [GitHub Pages gallery for all 12 styles](https://cxcxy.github.io/dy-travel-ticket-poster/) with material filters, full previews, and copyable invocation text.
- Added [scripts/build_pages_gallery.py](scripts/build_pages_gallery.py) to regenerate the site data and optimized WebP previews from the locked registry after validating all 12 source SHA-256 anchors.

## What the Skill handles

- Preserves recognizable people, animals, products, buildings, vehicles, and actions
- Builds the final photo panel directly from original source pixels with aspect-preserving cropping and high-quality resampling; never uses a model-reconstructed panel or a lossy JPEG intermediate
- Selects a crop that keeps the main subject and enough environmental context
- Adapts the background and ticket-stub colors to each photograph
- Resolves 12 gallery-locked `style_id` presets with color, texture, lighting, shadow, and depth
- Supports `subtle / balanced / strong` intensity, generic and gallery-specific lighting, four shadow presets, and strict subject preservation
- Recommends materially different options when the user asks for multiple backgrounds
- Uses user-provided titles and dates when available
- Falls back to a neutral scene title when the location cannot be verified
- Creates a five-digit serial, an eight-character decorative code, and a decorative barcode
- Processes batch inputs as separate posters while keeping one visual system
- Normalizes approved outputs to `1170 × 1560` PNG without overwriting the source

## Visual system

The poster uses a restrained, repeatable layout.

- Canvas ratio is `3:4`
- The nominal ticket body is `1057 × 507px` at `x=55, y=501`
- Outer margins are locked to the measured reference at `55px` left and `58px` right; ticket width is `90.4%` of the canvas
- The photo panel occupies about `73.2%` of the ticket width and the information stub about `26.8%`
- Rounded corners, a vertical perforation, a semicircular notch, a soft shadow, and bold condensed text stay consistent across the series
- Exactly one square-ended perforation divider is allowed, with its first dash flush at the ticket top
- A tight contact shadow plus a wider ambient shadow grounds the complete ticket
- With no explicit style request, the canvas uses a photo-derived near-solid color with imperceptible monochrome tactile texture, normally HSL lightness `58–62%` and saturation `6–20%`; no obvious light patch, gradient, or pattern is added
- The palette changes with each source photo while hierarchy and geometry remain fixed; a batch must not reuse one generic background color

Full construction details are in [references/style-spec.md](references/style-spec.md).

## Gallery-Locked 12-Style Background System

When a style is requested, the Skill resolves a complete material specification from [references/gallery-12-background-styles.json](references/gallery-12-background-styles.json). The 12 styles were distilled one-by-one from the user-supplied gallery and are anchored by source filename, SHA-256, measured background median, and a visual signature. Only background material, light pattern, tonal falloff, and spatial depth are transferred; the reference photograph, people, text, and codes are never copied. Material, lighting, and shadow remain independently composable. Color is adaptive by default: unless the user specifies a background color, every final photo crop supplies its own theme hue. A batch-wide color family is used only when explicitly requested. With no explicit style, the default is a deterministic photo-derived near-solid background with very subtle monochrome texture and no image-generation call. The generic 20-style baseline remains available in [references/background-styles.json](references/background-styles.json) through an explicit `--registry` override.

The 12 default IDs are:

```text
warm_linen_side_light          ivory_paper_window_veil
sand_center_glow               mushroom_cinematic_vignette
caramel_dappled_sun            natural_washi_halo
greige_stucco_soft_beams       ivory_stucco_window_beam
cream_limewash_diffusion       ivory_travertine_diagonal
cotton_paper_top_glow          caramel_mineral_spotlight
```

### Live gallery and site maintenance

The complete visual catalog is available in the [GitHub Pages 12-style gallery](https://cxcxy.github.io/dy-travel-ticket-poster/). Its static source is in [`docs/`](docs/) and the deployment workflow is [`.github/workflows/pages.yml`](.github/workflows/pages.yml). After the changes reach `main`, the workflow publishes `docs/`; on first setup, select **GitHub Actions** under **Settings → Pages → Build and deployment**.

Preview locally:

```bash
python3 -m http.server 8000 --directory docs
```

Then open `http://127.0.0.1:8000/`. Regenerate the gallery after changing the locked reference set:

```bash
python3 scripts/build_pages_gallery.py \
  --source-dir "/absolute/path/to/gallery" \
  --default-preview "/absolute/path/to/default-ticket.png"
```

The generator updates the website assets, `docs/style-data.json`, and the directly openable `docs/style-data.js` only after all 12 source files pass the registry hash checks.

The primary workflow is: attach one photo or a batch, then choose one of the 12 styles by gallery order, exact display name, or canonical `style_id`. A single input produces one ticket. A batch locks one style, intensity, lighting, and shadow across all inputs while adapting the final background hue to each photo by default. It exports one independent ticket per photo without making a collage or randomly changing styles. One shared background plate is used only when the user explicitly asks for a unified color family.

Example:

```text
Use $dy-travel-ticket-poster with ivory_travertine_diagonal, balanced strength, stone_diagonal, architectural shadow, and strict subject preservation.
```

The deterministic helper validates the registry, recommends diverse styles, resolves presets, and compiles the image prompt:

```bash
python3 scripts/background_style_system.py validate
python3 scripts/background_style_system.py recommend --context "premium warm travel ticket" --count 10
python3 scripts/background_style_system.py prompt --style-id "第10种" --strength balanced --palette-mode adaptive --theme-color '#8FA6AD'
python3 scripts/adapt_background_plate.py --plate material.png --source-photo photo.jpg --palette-mode adaptive --output background.png
python3 scripts/build_subtle_texture_background.py --source-photo photo.jpg --palette-mode adaptive --output background.png
python3 scripts/validate_gallery_references.py --source-dir "/absolute/path/to/gallery"
```

## Installation and tool support

This is a private repository that follows the Open Agent Skills structure. Make sure the current GitHub account can access it and that GitHub CLI is authenticated.

### Codex desktop, CLI, and IDE extension

Install it in the user-level Skills directory:

```bash
mkdir -p "$HOME/.agents/skills"
gh repo clone cxcxy/dy-travel-ticket-poster "$HOME/.agents/skills/dy-travel-ticket-poster"
```

Codex normally discovers new Skills automatically. Restart Codex if it does not appear, then invoke it with `$dy-travel-ticket-poster`.

### Codex Cloud

Codex Cloud needs the Skill inside the target project repository. The recommended setup is a submodule under `.agents/skills/` at the target repository root:

```bash
mkdir -p .agents/skills
git submodule add https://github.com/cxcxy/dy-travel-ticket-poster.git \
  .agents/skills/dy-travel-ticket-poster
git submodule update --init --recursive
```

For a private submodule, the GitHub account connected to Codex Cloud must also have read access. The cloud environment needs image-generation or image-editing capability, plus ImageMagick if the normalization script will run there.

### Claude Code and other Agent Skills tools

Tools that support Agent Skills can place this repository in their own Skills directory. For example, the Claude Code user-level location is:

```bash
mkdir -p "$HOME/.claude/skills"
gh repo clone cxcxy/dy-travel-ticket-poster "$HOME/.claude/skills/dy-travel-ticket-poster"
```

Those tools still need a compatible image-generation or image-editing capability. Reading `SKILL.md` alone is not enough to complete the poster workflow.

### Codex Plugins and common companion tools

Open **Plugins** in the ChatGPT/Codex desktop app, or enter `/plugins` in Codex CLI. Start a new task after installation. Not every item below is required:

| Tool or Plugin | Purpose | Required |
| --- | --- | --- |
| Image generation / `imagegen` | Edit and generate images using the ticket visual system | Yes |
| GitHub | Maintain the Skill repository and collaborate on changes | Optional |
| Google Drive / Box | Read source photos or save deliverables | Optional |
| Canva | Continue layout work or manual refinement after generation | Optional |

Plugins do not automatically receive private local photos. The user must explicitly select or authorize files. Local files remain sufficient when no companion Plugin is installed.

References: [Codex Skills documentation](https://learn.chatgpt.com/docs/build-skills) · [Codex Plugins documentation](https://learn.chatgpt.com/docs/plugins) · [Claude Code Skills documentation](https://code.claude.com/docs/en/skills)

## Use

Attach one or more local PNG or JPG photos, then ask Codex to use the Skill.

```text
Use $dy-travel-ticket-poster to convert these photos into clean 3:4 travel-ticket posters.
```

You can also provide explicit metadata.

```text
Use $dy-travel-ticket-poster for this photo. Title it WATERFRONT and use 2026 - 08.
```

For each input, the workflow inspects the photo, chooses a safe crop, and prepares the ticket metadata. With no explicit style, [scripts/build_subtle_texture_background.py](scripts/build_subtle_texture_background.py) creates the near-solid tactile background locally. Gallery style mode instead generates an empty material plate, and [scripts/adapt_background_plate.py](scripts/adapt_background_plate.py) applies the current photo's theme hue or an explicitly shared hue. [scripts/normalize_reference_layout.py](scripts/normalize_reference_layout.py) deterministically restores the original photo pixels and ticket before final review.

## Metadata behavior

- A title, location, or date supplied by the user takes priority
- If no reliable location is available, the Skill uses a neutral scene word such as `COFFEE`, `KOALA`, `OLD TOWN`, or `DESERT`
- The date priority is user input, local `DateTimeOriginal`, local file date, then the current year and month
- GPS and private metadata stay local and are not included in the generation request
- The serial code and barcode are visual elements and are not guaranteed to be scannable

## Requirements

- Codex with the `imagegen` Skill available
- ImageMagick for final normalization
- Pillow for deterministic layout rebuilding and targeted background recoloring
- Local access to the input photos

The normalizer can be run directly after visual approval.

```bash
bash scripts/normalize_output.sh generated-image.png final-ticket.png
```

## Reference cases

The following examples show the supplied source photo beside the generated travel-ticket poster. The documentation displays each preview at a suitable width, while the working output remains a `1170 × 1560` PNG.

### 01 · Coffee counter

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/coffee-original.jpg" width="360" alt="Original photo of a coffee counter"></td>
    <td><img src="assets/cases/coffee-ticket.jpg" width="360" alt="Coffee photo converted into a travel-ticket poster"></td>
  </tr>
</table>

### 02 · Koala encounter

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/koala-original.jpg" width="360" alt="Original portrait with a koala"></td>
    <td><img src="assets/cases/koala-ticket.png" width="360" alt="Koala portrait converted into a travel-ticket poster"></td>
  </tr>
</table>

### 03 · Heritage architecture

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/heritage-original.jpg" width="360" alt="Original portrait at a heritage building"></td>
    <td><img src="assets/cases/heritage-ticket.jpg" width="360" alt="Heritage portrait converted into a travel-ticket poster"></td>
  </tr>
</table>

### 04 · Open-air theater

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/theater-original.jpg" width="360" alt="Original photo of an open-air theater"></td>
    <td><img src="assets/cases/theater-ticket.jpg" width="360" alt="Theater photo converted into a travel-ticket poster"></td>
  </tr>
</table>

### 05 · Boutique interior

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/boutique-original.jpg" width="360" alt="Original photo of a boutique interior"></td>
    <td><img src="assets/cases/boutique-ticket.jpg" width="360" alt="Boutique interior converted into a travel-ticket poster"></td>
  </tr>
</table>

### 06 · Old town street

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/old-town-original.jpg" width="360" alt="Original photo of a colorful old town street"></td>
    <td><img src="assets/cases/old-town-ticket.jpg" width="360" alt="Old town street converted into a travel-ticket poster"></td>
  </tr>
</table>

### 07 · Café table

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/cafe-original.jpg" width="360" alt="Original overhead photo of coffee and cake"></td>
    <td><img src="assets/cases/cafe-ticket.jpg" width="360" alt="Cafe table photo converted into a travel-ticket poster"></td>
  </tr>
</table>

### 08 · Desert drive

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/desert-original.jpg" width="360" alt="Original photo of a red vehicle in the desert"></td>
    <td><img src="assets/cases/desert-ticket.jpg" width="360" alt="Desert vehicle photo converted into a travel-ticket poster"></td>
  </tr>
</table>

### 09 · Waterfront photographer

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/waterfront-original.jpg" width="360" alt="Original waterfront portrait with a camera"></td>
    <td><img src="assets/cases/waterfront-ticket.jpg" width="360" alt="Waterfront portrait converted into a travel-ticket poster"></td>
  </tr>
### 10 · Lakeside view

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/lakeside-original.jpg" width="360" alt="Original photo of a person sitting beside a lake"></td>
    <td><img src="assets/cases/lakeside-ticket.jpg" width="360" alt="Lakeside photo converted into a travel-ticket poster"></td>
  </tr>
</table>

### 11 · Gold house

<table>
  <tr><th>Original</th><th>Generated ticket poster</th></tr>
  <tr>
    <td><img src="assets/cases/gold-house-original.jpg" width="360" alt="Original photo of a yellow residential building"></td>
    <td><img src="assets/cases/gold-house-ticket.jpg" width="360" alt="Yellow building converted into a travel-ticket poster"></td>
  </tr>
</table>

## Repository layout

```text
.
├── SKILL.md
├── agents/openai.yaml
├── assets/cases/
├── references/background-styles.json
├── references/gallery-12-background-styles.json
├── references/prompt-template.md
├── references/style-spec.md
├── scripts/background_style_system.py
├── scripts/adapt_background_plate.py
├── scripts/build_subtle_texture_background.py
├── scripts/build_before_after_showcase.py
├── scripts/build_ticket_batch.py
├── scripts/normalize_output.sh
├── scripts/normalize_reference_layout.py
├── scripts/recolor_existing_poster.py
├── scripts/validate_gallery_references.py
└── tests/
```

## Content boundaries

The Skill does not invent a city when the image cannot support one. It also avoids adding new people, animals, products, vehicles, buildings, logos, or other identity-bearing details. Any background extension is limited to non-semantic scenery and should be disclosed with the delivery.
