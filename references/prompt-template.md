# 图片编辑提示词模板

标准票根不得依赖图片模型生成几何、文字、条码或背景色；这些层统一由 `render_ticket_poster.py` 或 `build_ticket_batch.py` 确定性完成。每张照片单独处理，先判断使用默认“照片主色 + 细腻哑光纸纹”背景还是显式图集风格背景；不要把两套背景要求同时写进一条提示词。

## A. 无语义环境扩展

只有最终 `774 × 507` 裁切必然切掉关键主体，且无法用 `photo-center-y` 解决时，才使用图片模型扩展无语义环境。模型只输出自然照片，不生成票根、背景画布、信息联、标题、日期、编号、条码、虚线、缺口或阴影。

```text
Use case: constrained outpainting of non-semantic scenery only.
Image 1 is the only source image and the only semantic authority.

Locked source content:
[List the exact people, faces, hands, animals, products, vehicles, buildings, signs, text, actions and relationships that must remain pixel-faithful and unchanged.]

Permitted extension zones:
[State the exact edges that may be extended and name only the non-semantic material present there, such as plain sky, distant water, blank wall, ground, soft foliage or shallow-depth-of-field background.]

Hard constraints:
- Do not repaint, retouch, beautify, relight, recolor or restyle any existing source content.
- Do not change identity, anatomy, pose, gaze, clothing, object count, geometry, texture, sign, logo or readable text.
- Do not invent people, animals, products, vehicles, architecture, windows, doors, furniture, props, roads, labels or landmarks.
- Match the existing perspective, lens character, depth of field, grain, exposure, white balance and edge continuity.
- Add no ticket, poster canvas, typography, barcode, perforation, notch, frame, watermark, phone UI or decorative travel icon.
- Output one clean expanded photograph only.
```

同时用 `view_image` 对比原图和扩展图，记录生成边缘。只要主体、建筑、商品或文字发生改变，就丢弃扩展图，不得继续 edit-on-edit。

## B. 默认照片主色细腻哑光纸纹背景

用户没有指定 `style_id`、材质、光影或背景氛围时，不调用生图模型。直接从最终照片裁切提取环境主色，并确定性生成克制柔和的主色细腻哑光纸纹背景：

```bash
python3 scripts/build_subtle_texture_background.py \
  --source-photo original-photo.png \
  --photo-center-y 0.5 \
  --palette-mode adaptive \
  --texture-strength 2 \
  --output subtle-solid-background-1170x1560.png
```

默认保留照片主色色相，把饱和度收至原色约 `72%`，并以亮度约 `±2` 的哑光细纸纹提供触感；远看必须是一整块克制柔和的主色。禁止渐变、暗角、树影、窗影、聚光、明显纸纤维、石材纹路、颗粒团块和可识别图案。用户明确要求“纯色 / 无纹理”时才不用本步骤；用户明确要求统一色系时，使用 `--palette-mode unified --theme-color '#RRGGBB'`，整组复用同一背景。

合成时将结果作为批量清单中的 `background_image` 交给 `build_ticket_batch.py`。旧版 `normalize_reference_layout.py --background-image` 只用于迁移既有票根。

## C. 图集锁定背景底图

先从最终照片裁切在本地提取主题色，再运行 `scripts/background_style_system.py prompt ... --palette-mode adaptive --theme-color '#RRGGBB'`，从默认的 `gallery-12-background-styles.json` 得到带参考视觉签名的完整 Prompt。用户明确要求统一色系时改用 `--palette-mode unified`，整组传入同一个色值。随后在末尾追加下面的输出约束。此请求只生成背景，不上传私人照片，也不让模型接触主体。参考图只用于提炼材质、光型、明暗衰减与纵深；禁止复制图集里的照片、人物、文字、编号和条形码。

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
python3 scripts/adapt_background_plate.py \
  --plate generated-material-plate-1170x1560.png \
  --source-photo original-photo.png \
  --photo-center-y 0.5 \
  --palette-mode adaptive \
  --output adaptive-background-1170x1560.png
```

默认每张照片分别运行一次，得到各自主题色背景。只有用户明确要求统一色系时，才用 `--palette-mode unified --theme-color '#RRGGBB'` 生成一张整组复用的背景。

```bash
python3 scripts/build_ticket_batch.py \
  --manifest ticket-batch.json \
  --output-dir output
```

## D. 既有卡片 / 海报只换背景

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

默认照片主色细腻纸纹背景修正：

```text
Change only the full-canvas background to the restrained main-color family sampled from Image 1. Preserve the photo-derived hue; lower saturation to about 72% of its source value, bounded to a calm usable range, and keep the surface matte. Add only very subtle low-contrast fine paper tooth (about ±2 brightness): no gradient, vignette, directional light, window shadow, leaf shadow, spotlight, visible grain cluster, pattern, gloss, or reflection. Preserve the ticket, photo, crop, text and shadow exactly.
```

风格背景修正：重新运行风格编译器，降低 `strength` 或更换光线/阴影预设，只重新生成背景底图，再确定性合成；不要重生成主体。

文字修正时逐字符写明，例如：

```text
Replace the code with exactly "E5R8K3M2" — eight characters: E, 5, R, 8, K, 3, M, 2.
```
