# DY Travel Ticket Poster

English | [简体中文](README.zh-CN.md)

Turn one photo or a batch of photos into a consistent series of travel-ticket posters. The Skill keeps the recognizable subject and scene from the source image, then builds a centered ticket with an adaptive color palette, a perforated information stub, neutral scene naming, a date, a serial number, and a decorative barcode.

The final deliverable for each photo is a clean `1170 × 1560` PNG in a `3:4` aspect ratio. Phone UI, notifications, player controls, and watermarks are excluded from the poster.

## Install

### Ask Codex to install it (recommended)

Send this sentence directly to Codex:

```text
Please install this Skill from https://github.com/cxcxy/dy-travel-ticket-poster and verify that Codex can discover it after installation.
```

### Manual installation for Codex

```bash
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git
cd dy-travel-ticket-poster
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R . "${CODEX_HOME:-$HOME/.codex}/skills/dy-travel-ticket-poster"
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.claude/skills/dy-travel-ticket-poster
```

### Cursor

```bash
mkdir -p ~/.cursor/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.cursor/skills/dy-travel-ticket-poster
```

### Gemini CLI

```bash
mkdir -p ~/.gemini/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.gemini/skills/dy-travel-ticket-poster
```

### GitHub Copilot

```bash
mkdir -p ~/.copilot/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.copilot/skills/dy-travel-ticket-poster
```

### Other Agent Skills-compatible agents

If an agent supports the shared personal Skills directory, install the repository under `~/.agents/skills`. Clients such as Codex, Cursor, Gemini CLI, and GitHub Copilot that discover this shared directory can use the same installation.

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.agents/skills/dy-travel-ticket-poster
```

After a manual installation, restart or refresh the relevant agent so it rescans its Skills. The standard poster path is deterministic and needs local Python, Pillow, and a bold font. Image generation or editing is required only when an essential subject cannot survive the crop and non-semantic scenery must be extended; Codex can use `imagegen` for that exception.

## What the Skill handles

- Preserves recognizable people, animals, products, buildings, vehicles, and actions
- Selects a crop that keeps the main subject and enough environmental context
- Produces three palettes from the final crop for visual review before choosing the canvas, stub, and text colors
- Uses deterministic scripts for source pixels, typography, barcode, geometry, perforation, notch, and shadow
- Uses user-provided titles and dates when available
- Falls back to a neutral scene title when the location cannot be verified
- Creates a five-digit serial, an eight-character decorative code, and a decorative barcode
- Processes batch inputs as separate posters while keeping one visual system
- Outputs approved work as `1170 × 1560` RGB PNG without overwriting the source

## Visual system

The poster uses a restrained, repeatable layout.

- Canvas ratio is `3:4`
- The ticket is centered and occupies about `90.4%` of the canvas width
- The ticket height is about `32.5%` of the canvas height
- The photo panel occupies about `73.2%` of the ticket width
- The information stub occupies about `26.8%`
- Small rounded corners, one square-ended perforation, a semicircular notch, a two-stage shadow, and bold typography stay consistent
- Three environment-derived palette candidates are reviewed per photo while the hierarchy remains fixed

Full construction details are in [references/style-spec.md](references/style-spec.md).

## Use

Attach one or more local PNG or JPG photos, then ask your agent to use the Skill.

```text
Use $dy-travel-ticket-poster to convert these photos into clean 3:4 travel-ticket posters.
```

You can also provide explicit metadata.

```text
Use $dy-travel-ticket-poster for this photo. Title it WATERFRONT and use 2026 - 08.
```

For each input, the workflow inspects the photo and final crop, uses [scripts/suggest_palette.py](scripts/suggest_palette.py) to create three traceable palette previews, visually selects one, builds the poster deterministically with [scripts/render_ticket_poster.py](scripts/render_ticket_poster.py), and checks source pixels, solid background, color hierarchy, text contrast, and ticket structure with [scripts/validate_ticket_output.py](scripts/validate_ticket_output.py). `imagegen` is used only when a crop would otherwise lose essential content and non-semantic scenery must be extended.

## Metadata behavior

- A title, location, or date supplied by the user takes priority
- If no reliable location is available, the Skill uses a neutral scene word such as `COFFEE`, `KOALA`, `OLD TOWN`, or `DESERT`
- The date priority is user input, local `DateTimeOriginal`, local file date, then the current year and month
- GPS and private metadata stay local and are not included in the generation request
- The serial code and barcode are visual elements and are not guaranteed to be scannable

## Requirements

- An Agent Skills environment that supports `SKILL.md`
- Python 3.10+, the Pillow version declared in `requirements.txt`, and an available bold TTF/OTF/TTC font; pin one font per batch, while output PNGs retain font names and SHA-256 identities for validation
- An image-generation or image-editing tool only for exceptional non-semantic scenery extension; Codex can use `imagegen`
- ImageMagick only for the legacy-output normalization path
- Local access to the input photos

Generate palette candidates and a review sheet first:

```bash
python3 scripts/suggest_palette.py --input source.jpg --output-json palette.json --preview palette-review.png
```

See [SKILL.md](SKILL.md) for the complete render and validation commands.

## Reference cases

The following source images and early visual cases illustrate photo-derived color direction. They are not pixel-level goldens for the new validator; current `1170 × 1560` RGB PNG output follows `SKILL.md`, the visual specification, and the validation scripts.

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
    <td><img src="assets/cases/koala-ticket.jpg" width="360" alt="Koala portrait converted into a travel-ticket poster"></td>
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
</table>

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
├── references/
│   ├── palette-system.md
│   ├── prompt-template.md
│   └── style-spec.md
├── scripts/
│   ├── suggest_palette.py
│   ├── render_ticket_poster.py
│   ├── validate_ticket_output.py
│   └── normalize_reference_layout.py
└── requirements.txt
```

## Content boundaries

The Skill does not invent a city when the image cannot support one. It also avoids adding new people, animals, products, vehicles, buildings, logos, or other identity-bearing details. Any background extension is limited to non-semantic scenery and should be disclosed with the delivery.
