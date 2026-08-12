# DY Travel Ticket Poster

English | [简体中文](README.zh-CN.md)

Turn one photo or a batch of photos into a consistent series of travel-ticket posters. The Skill keeps the recognizable subject and scene from the source image, then builds a centered ticket with an adaptive color palette, a perforated information stub, neutral scene naming, a date, a serial number, and a decorative barcode.

The final deliverable for each photo is a clean `1170 × 1560` PNG in a `3:4` aspect ratio. Phone UI, notifications, player controls, and watermarks are excluded from the poster.

## Install for different agents

This repository is private. First, make sure your GitHub account has access to it and authenticate GitHub CLI:

```bash
gh auth login
```

Then choose the installation method for the agent you use. You do not need to install the Skill into every directory.

### Codex

```bash
mkdir -p ~/.codex/skills
gh repo clone cxcxy/dy-travel-ticket-poster ~/.codex/skills/dy-travel-ticket-poster
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
gh repo clone cxcxy/dy-travel-ticket-poster ~/.claude/skills/dy-travel-ticket-poster
```

### Cursor

```bash
mkdir -p ~/.cursor/skills
gh repo clone cxcxy/dy-travel-ticket-poster ~/.cursor/skills/dy-travel-ticket-poster
```

### Gemini CLI

```bash
mkdir -p ~/.gemini/skills
gh repo clone cxcxy/dy-travel-ticket-poster ~/.gemini/skills/dy-travel-ticket-poster
```

### GitHub Copilot

```bash
mkdir -p ~/.copilot/skills
gh repo clone cxcxy/dy-travel-ticket-poster ~/.copilot/skills/dy-travel-ticket-poster
```

### Other Agent Skills-compatible agents

If an agent supports the shared personal Skills directory, install the repository under `~/.agents/skills`. Clients such as Codex, Cursor, Gemini CLI, and GitHub Copilot that discover this shared directory can use the same installation.

```bash
mkdir -p ~/.agents/skills
gh repo clone cxcxy/dy-travel-ticket-poster ~/.agents/skills/dy-travel-ticket-poster
```

Restart or refresh the relevant agent after installation so it rescans its Skills. Installing this Skill provides the workflow and visual specification only; the agent must also have an image-generation or image-editing tool available. Codex can use the `imagegen` Skill directly, while other agents need an equivalent capability.

## What the Skill handles

- Preserves recognizable people, animals, products, buildings, vehicles, and actions
- Selects a crop that keeps the main subject and enough environmental context
- Adapts the background and ticket-stub colors to each photograph
- Uses user-provided titles and dates when available
- Falls back to a neutral scene title when the location cannot be verified
- Creates a five-digit serial, an eight-character decorative code, and a decorative barcode
- Processes batch inputs as separate posters while keeping one visual system
- Normalizes approved outputs to `1170 × 1560` PNG without overwriting the source

## Visual system

The poster uses a restrained, repeatable layout.

- Canvas ratio is `3:4`
- The ticket is centered and occupies about `90.4%` of the canvas width
- The ticket height is about `27.2%` of the canvas height
- The photo panel occupies about `74.7%` of the ticket width
- The information stub occupies about `25.3%`
- Rounded corners, a vertical perforation, a semicircular notch, a soft shadow, and bold condensed text stay consistent across the series
- The palette changes with the source photo while the hierarchy remains fixed

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

For each input, the workflow inspects the photo, chooses a safe crop, prepares the ticket metadata, performs the raster edit with the installed `imagegen` Skill or an equivalent image tool, checks the result, and normalizes the approved output with [scripts/normalize_output.sh](scripts/normalize_output.sh).

## Metadata behavior

- A title, location, or date supplied by the user takes priority
- If no reliable location is available, the Skill uses a neutral scene word such as `COFFEE`, `KOALA`, `OLD TOWN`, or `DESERT`
- The date priority is user input, local `DateTimeOriginal`, local file date, then the current year and month
- GPS and private metadata stay local and are not included in the generation request
- The serial code and barcode are visual elements and are not guaranteed to be scannable

## Requirements

- An Agent Skills environment that supports `SKILL.md`
- An image-generation or image-editing tool; `imagegen` is recommended for Codex
- ImageMagick for final normalization
- Local access to the input photos

The normalizer can be run directly after visual approval.

```bash
bash scripts/normalize_output.sh generated-image.png final-ticket.png
```

## Reference cases

The following examples show the supplied source photo beside the generated travel-ticket poster. Documentation previews are resized and stripped of metadata. The working output remains a `1170 × 1560` PNG.

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
├── references/prompt-template.md
├── references/style-spec.md
└── scripts/normalize_output.sh
```

## Content boundaries

The Skill does not invent a city when the image cannot support one. It also avoids adding new people, animals, products, vehicles, buildings, logos, or other identity-bearing details. Any background extension is limited to non-semantic scenery and should be disclosed with the delivery.
