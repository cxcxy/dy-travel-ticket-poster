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
- One horizontal ticket exactly centered.
- Ticket about 90.4% of canvas width and 27.2% of canvas height.
- About 75% quiet negative space.
- Ticket aspect ratio about 2.49:1.
- Left photo panel exactly 74.7%; right information stub exactly 25.3%.
- Small rounded corners, restrained soft shadow below-right, short rectangular vertical perforation dashes, and one centered semicircular inward notch on the far-right edge.
- No border.

Photo invariants and crop:
[Describe the exact people, animals, products, vehicles, buildings, actions and relationships that must remain unchanged.]
Use only Image 1 for the photo panel. Crop intelligently to a wide 1.86:1 frame without stretching. Preserve photographic realism, identity, object count, lighting and textures. Do not invent new semantic content.

Palette:
[Muted background color derived from the photo]; [related information-stub color]; [high-contrast text color]. Keep the source photo natural.

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
```

## 定向修正模板

当首轮只出现一个问题时，不重写整份创意要求，使用定向编辑：

```text
Image 1 is the edit target. Change only [the exact problem]. Keep the canvas, ticket position, source photograph, subject identity, crop, colors, shadow, perforation, notch, all other text and barcode unchanged. Do not add or remove anything else.
```

文字修正时逐字符写明，例如：

```text
Replace the code with exactly "E5R8K3M2" — eight characters: E, 5, R, 8, K, 3, M, 2.
```
