# 图片编辑提示词模板

将方括号内容替换为当前照片的真实信息。每张照片单独使用一次。

```text
Use case: style-transfer.
Asset type: finished clean 3:4 portrait travel-ticket poster PNG.

Input images:
- Image 1 is the edit target and the only source photograph.
- Any additional image is a composition reference only. Do not copy its photograph, text, logo, watermark, phone UI, or identifying content.

Primary request:
Place Image 1 into a clean horizontal travel-ticket poster system.

Canvas and geometry:
- Strict 3:4 portrait composition.
- Final canvas is 1170 x 1560. Use one horizontal ticket body at x=55, y=501, width=1057, height=507.
- Lock the outer margins to the measured reference: 55 px left and 58 px right. Do not let either side drift or force them into a different symmetric layout.
- The ticket body occupies 90.4% of canvas width and 32.5% of canvas height, with an aspect ratio about 2.08:1.
- Optically center the complete ticket-and-shadow group; keep the ticket body itself about 26 px above the geometric canvas center.
- Left photo panel is 774 x 507, exactly 73.2% of ticket width; right information stub is 283 x 507, exactly 26.8%.
- Small rounded corners on the ticket outer silhouette only. Use exactly one vertical perforation divider at the photo/stub seam. Its dashes are square-ended rectangles, and the first dash begins flush at the ticket top with no rounded cap. Never add a second dotted line, bright seam, border, or divider shadow. Add a grounded two-stage shadow around the complete ticket: a tight contact shadow plus a wider, lighter ambient shadow, strongest below and subtle above. Add one centered semicircular inward notch on the far-right edge.
- No border.

Photo invariants and crop:
[Describe the exact people, animals, products, vehicles, buildings, actions and relationships that must remain unchanged.]
Use only Image 1 for the photo panel. Crop intelligently to a 774 x 507 frame, about 1.53:1, without stretching or recompressing. Preserve photographic realism, identity, object count, lighting and textures. Do not invent new semantic content. The final production step will replace this generated preview panel with original source pixels; therefore do not allow typography, divider artifacts, gradients, or shadows to spill into the photo.

Palette:
- Canvas background: [HEX], derived from a supporting hue actually present in Image 1, adjusted to a quiet solid color at HSL saturation 6-20% and lightness 58-62%.
- Information stub: [HEX], derived from a darker or more vivid secondary color actually present in Image 1.
- Text: [HEX], with at least 4.5:1 contrast for the date and codes.
- The full canvas background must be one flat, edge-to-edge solid color: no gradient, vignette, texture, paper grain, glow, or color blocks.
- The reference image controls geometry only. Do not copy its background color unless the user explicitly requests that exact color.
- Keep the source photo natural.

Typography and exact text:
Heavy uppercase geometric sans-serif, left aligned with generous padding. Render exactly these lines and no other text:
"[TITLE LINE 1]"
"[TITLE LINE 2]"
"[YYYY - MM]"
"[NO.12345]"
"[ABCDEFGH]"
Below the code, add one small decorative barcode made of varied vertical bars in the same text color.

Constraints:
Clean finished poster only. No mobile status bar, time, battery, Wi-Fi, notifications, player controls, progress bars, watermark, signature, logos, captions, outside frames, or extra text.
Preserve the reference-locked 55 px left / 58 px right margins and the photo-derived canvas color. Do not substitute a generic beige, gray-green, or blue batch background.
```

## 定向修正模板

当首轮只出现一个问题时，不重写整份创意要求，使用定向编辑：

```text
Image 1 is the edit target. Change only [the exact problem]. Keep the canvas, ticket position, source photograph, subject identity, crop, colors, shadow, perforation, notch, all other text and barcode unchanged. Do not add or remove anything else.
```

几何修正时使用：

```text
Change only the ticket geometry. Set the ticket body to x=55, y=501, width=1057, height=507 on the 1170 x 1560 canvas. Lock the outer margins to 55 px left and 58 px right. Preserve the current photo crop, palette, text, perforation, notch and shadow.
```

背景色修正时使用：

```text
Change only the full-canvas background to the specified solid color [HEX], sampled from and harmonized with Image 1 at HSL lightness 58-62% and saturation 6-20%. Use one flat edge-to-edge color with no gradient, texture, vignette or light patch. Preserve the ticket, photo, crop, text and shadow exactly.
```

文字修正时逐字符写明，例如：

```text
Replace the code with exactly "E5R8K3M2" — eight characters: E, 5, R, 8, K, 3, M, 2.
```
