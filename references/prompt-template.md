# 图片编辑提示词模板

每张照片单独处理。先判断使用默认纯色背景还是 V2 风格背景；不要把两套背景要求同时写进一条提示词。

## A. 票根主体预览

将方括号内容替换为当前照片的真实信息。风格模式下，这张预览的外部背景只是临时占位，最终会被独立背景底图替换。

```text
Use case: style-transfer.
Asset type: clean 3:4 portrait travel, coffee, or movie ticket poster PNG.

Input images:
- Image 1 is the edit target and the only source photograph.
- Any additional image is a composition reference only. Do not copy its photograph, text, logo, watermark, phone UI, or identifying content.

[SUBJECT PRESERVATION — STRICT]
Preserve the original subject exactly. Do not redesign the ticket, card, photo, people, faces, products, vehicles, buildings or key actions. Keep original identity, object count, lighting, textures and relationships unchanged. Do not invent semantic content.

[CANVAS AND GEOMETRY]
- Strict 3:4 portrait composition, 1170 x 1560.
- One ticket at x=55, y=501, width=1057, height=507.
- Lock outer margins to 55 px left and 58 px right.
- Photo panel: 774 x 507, 73.2% of ticket width.
- Information stub: 283 x 507, 26.8% of ticket width.
- Small rounded corners on the ticket outer silhouette only.
- Exactly one vertical perforation divider at the seam. Use square-ended rectangle dashes; start the first dash flush at the ticket top. Never add a second dotted line, bright seam, border or divider shadow.
- Add one centered semicircular inward notch on the far-right edge.
- No border.

[PHOTO INVARIANTS AND CROP]
[Describe the exact people, animals, products, vehicles, buildings, actions and relationships that must remain unchanged.]
Use only Image 1 for the photo panel. Crop intelligently to 774 x 507, about 1.53:1, without stretching or recompressing. The production step will replace this preview panel with original source pixels; do not let typography, divider artifacts, gradients or shadows spill into the photo.

[INFORMATION STUB PALETTE]
- Stub: [HEX], derived from a darker or more vivid secondary color in Image 1.
- Text: [HEX], with at least 4.5:1 contrast for date and codes.
- Keep the source photograph natural.

[TEMPORARY OUTER BACKGROUND]
- Adaptive solid mode: use [HEX], derived from Image 1 at HSL saturation 6-20% and lightness 58-62%; one flat edge-to-edge color, no texture or gradient.
- V2 style mode: use a quiet flat placeholder only. Do not attempt the final material background in this pass.

[TYPOGRAPHY AND EXACT TEXT]
Heavy uppercase geometric sans-serif, left aligned with generous padding. Render exactly these lines and no other text:
"[TITLE LINE 1]"
"[TITLE LINE 2]"
"[YYYY - MM]"
"[NO.12345]"
"[ABCDEFGH]"
Below the code, add one small decorative barcode made of varied vertical bars in the same text color.

[CONSTRAINTS]
Clean finished poster only. No mobile status bar, time, battery, Wi-Fi, notifications, player controls, progress bars, watermark, signature, logos, captions, outside frames or extra text.
```

## B. V2 背景底图

先运行 `scripts/background_style_system.py prompt ...` 得到完整的风格 Prompt，再在末尾追加下面的输出约束。此请求只生成背景，不上传私人照片，也不让模型接触主体。

```text
[OUTPUT PLATE]
Create one background-only plate at exactly 1170 x 1560 pixels, portrait 3:4.
The entire canvas is an empty premium presentation surface.
Do not include any ticket, card, poster, photo, person, animal, product, vehicle, building, typography, number, barcode, logo, frame, watermark or UI.
Keep the center ticket-safe region readable and restrained.
Place material variation, window shadows, grain and lighting only in the background plane.
Do not create a fake card-shaped light patch, outline or second rectangle behind the future subject.
```

生成后用 `view_image` 检查底图：必须为空背景，尺寸精确，纹理和光影不在票根正文区域形成高对比干扰。随后运行：

```bash
python3 scripts/normalize_reference_layout.py \
  --input generated-ticket-preview.png \
  --output final-ticket.png \
  --bbox X1,Y1,X2,Y2 \
  --split-x SPLIT_X \
  --photo-source original-photo.png \
  --photo-center-y 0.5 \
  --background-image generated-background-1170x1560.png \
  --shadow-preset premium_float
```

## C. 既有卡片 / 海报只换背景

当用户提供的是已经设计好的票根、卡片、海报或产品主体，不套票根几何。使用风格编译 Prompt，并把下面的约束放在最前面：

```text
[SUBJECT PRESERVATION — STRICT]
Preserve the supplied subject exactly at pixel-faithful proportions.
Do not change, redraw, restyle, retype or replace any person, face, photo, product, card edge, typography, date, serial number, barcode, logo, layout or internal color.
Change only the background outside the supplied subject.
Keep the original canvas size and aspect ratio unless the user explicitly requests a new format.
Do not let texture, lighting or shadows cross over text, faces, barcodes or important subject edges.
```

有透明主体、精确遮罩或可稳定分离的卡片时，优先生成背景底图后确定性合成，不直接重画主体。

## 定向修正

只改一个问题时，使用局部指令，不重写已确认设计：

```text
Image 1 is the edit target. Change only [the exact problem]. Keep the canvas, subject, source photograph, identity, crop, typography, dates, barcode, layout, colors, shadow and all other elements unchanged. Do not add or remove anything else.
```

几何修正：

```text
Change only the ticket geometry. Set the ticket body to x=55, y=501, width=1057, height=507 on the 1170 x 1560 canvas. Lock the outer margins to 55 px left and 58 px right. Preserve the current photo crop, palette, text, perforation, notch and shadow.
```

纯色背景修正：

```text
Change only the full-canvas background to [HEX], sampled from Image 1 at HSL lightness 58-62% and saturation 6-20%. Use one flat edge-to-edge color with no gradient, texture, vignette or light patch. Preserve the ticket, photo, crop, text and shadow exactly.
```

风格背景修正：重新运行风格编译器，降低 `strength` 或更换光线/阴影预设，只重新生成背景底图，再确定性合成；不要重生成主体。

文字修正时逐字符写明，例如：

```text
Replace the code with exactly "E5R8K3M2" — eight characters: E, 5, R, 8, K, 3, M, 2.
```
