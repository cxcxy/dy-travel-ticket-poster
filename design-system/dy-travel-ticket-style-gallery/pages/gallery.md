# Gallery Page Override

This page follows `../MASTER.md`, with the following project-specific overrides.

## Product intent

- The adaptive default-mode hero is the page opening and the only `h1`.
- The 12-style selector follows the hero immediately, before update notes or usage content.
- Favor large, readable previews over forcing all 12 styles into one viewport.
- Selecting a style opens progressive detail; cards do not repeat long descriptions.

## Visual system

- Preserve the established warm-paper brand palette instead of replacing it with neutral white.
- Use local system sans-serif fonts to avoid a render-blocking web-font dependency.
- Use one blue interaction accent, near-black text, subtle paper borders, and restrained elevation.
- Preview images are complete `3:4` assets: `height:auto`, `aspect-ratio:3/4`, `object-fit:contain`; never crop, stretch, or scale them on hover.

## Taste Skill direction

- Design read: a portfolio-style gallery for travel-photo creators, combining real ticket outputs, warm paper surfaces, and restrained cobalt interaction.
- Dials: `DESIGN_VARIANCE=5`, `MOTION_INTENSITY=4`, `VISUAL_DENSITY=7`.
- Treat this as a targeted evolution: preserve the page order, navigation anchors, 15-ticket carousel, and three-column 12-style grid.
- Keep one page-level eyebrow in the hero; avoid repeating version labels or decorative section labels.
- Place carousel controls on the image but keep the active title and counter in a dedicated caption below it.
- Present the update notes as one featured statement plus three supporting rows instead of four interchangeable cards.
- Keep the usage panel in the warm-paper visual system; a dark code surface is allowed, but the entire section must not flip to a black theme.
- This site intentionally emulates a light print artifact, so `color-scheme: light` is the documented exception to Taste's general dark-mode default.

## Responsive grid

- Desktop, tablet, and supported phone portrait widths: 3 columns.
- The 12 styles flow naturally into 4 rows; do not add a viewport-height minimum below the grid.
- Every image tile remains at least `44 × 44px`; filter and icon buttons use a `44px` minimum target.
- No page-level horizontal overflow. The filter row may scroll locally only when its labels cannot fit.

## Interaction

- The hero preview is a 15-item carousel containing the approved ticket outputs supplied in `/Users/mac1/Desktop/票根skill/未命名文件夹/`; website derivatives live in `docs/assets/carousel/` and must not mutate the source PNGs.
- Carousel slides preserve the complete `3:4` image with `object-fit:contain`; controls include previous, next, pause/play, a live position counter, and left/right keyboard navigation.
- Auto-play pauses on hover, keyboard focus, page invisibility, explicit pause, and `prefers-reduced-motion`.
- Filters expose `aria-pressed` and announce the visible result count.
- The native dialog supports a visible close action, previous/next controls, `Escape`, and left/right arrow keys.
- Style-card copy icons and the dialog copy action copy the Chinese style name only; prompt-copy controls elsewhere keep their original full command behavior.
- All icon-only actions use consistent outline SVGs with descriptive labels.
- Micro-interactions use `180–200ms` transitions and respect `prefers-reduced-motion`.
