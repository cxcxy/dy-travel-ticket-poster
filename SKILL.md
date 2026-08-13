---
name: dy-travel-ticket-poster
description: Convert one or more user-supplied PNG/JPG photos into premium 3:4 travel-ticket posters with deterministic source-pixel crops, exact typography and barcodes, reference-locked 55px/58px margins, a single square perforation, palette-aware shadows, and three visually reviewed photo-derived background palettes. Use when the user asks to "套旅行票根模板", "做成票根海报", "改成这种旅行票格式", wants more accurate or more premium ticket-poster output, asks to improve background-color aesthetics, continues a prior ticket batch, or supplies travel/lifestyle photos for this treatment.
---

# DY 旅行票根海报

把单张或批量照片转换为准确、克制、有现代编辑感的旅行票根海报。标准路径使用本地脚本确定性完成原图裁切、背景、信息联、文字、条码、虚线、缺口和阴影；不要让图片模型猜这些可精确构建的层。

## 质量合同

- 默认使用简体中文沟通；用户明确要求其他语言时再切换。
- 每张输入独立输出一张 `1170 × 1560`、严格 `3:4`、RGB、无透明通道的 PNG。
- 保留人物身份、动物、产品、建筑、车辆、招牌、文字和关键动作。照片面板必须直接来自本次确认的可见像素源，只进行 EXIF 方向修正、透明区域安全铺底、明确外框条清理、等比例裁切和 Lanczos 下采样；不重绘语义内容。
- 锁定票根主体 `x=55, y=501, width=1057, height=507`，形成 `55px / 58px` 左右外边距；照片区为 `774 × 507`，信息联为 `283 × 507`。
- 标题使用粗体；日期、编号和 8 位序列码使用独立的细窄等宽轻字重字体。装饰条形码的所有竖条必须统一为 `43px` 高，顶部与底部各自齐平，不得参差。
- 每张图先生成三套照片派生配色并目视选择。不得把“低饱和”误当作唯一高级感，也不得跨图片套用通用米色、灰绿或蓝色。
- 标准路径不调用图片生成工具。只有裁切必然切掉关键主体、确实需要扩展无语义环境时，才加载 `imagegen` Skill 并使用例外提示词。

## 执行前读取

1. 完整读取 [references/style-spec.md](references/style-spec.md)，锁定几何、排版和内容边界。
2. 完整读取 [references/palette-system.md](references/palette-system.md)，执行背景、信息联与文字的候选生成和审美筛选。
3. 只有需要无语义环境扩展时，才完整读取 [references/prompt-template.md](references/prompt-template.md) 并加载当前环境的 `imagegen` Skill。

## 标准工作流

### 1. 检查输入与裁切

1. 对每张本地输入运行 `view_image`，读取像素尺寸和可用的本地 EXIF/文件日期。不要把 GPS 或私人元数据发送给第三方。
2. 确定 `photo-center-y`。先保住人脸、手部、动作、动物、车辆、产品、建筑和招牌，再保留说明环境的证据；禁止拉伸。默认清除照片边缘连续、近乎纯色的白/黑装裱条；若该边框是作品内容，在候选、渲染和验证三步都传 `--keep-neutral-borders`。
3. 若 `774:507` 裁切可以保住关键内容，继续标准路径。若无论如何都会切掉关键主体，转到“例外扩展”，不要直接生成整张票根。

### 2. 先选颜色，再出图

为每张照片使用独立文件名运行：

```bash
python3 scripts/suggest_palette.py \
  --input source.jpg \
  --photo-center-y 0.5 \
  --output-json source-palette.json \
  --preview source-palette-review.png
```

配色 JSON 会记录源文件绝对路径、SHA-256、`photo-center-y` 和边框处理方式；渲染与验证不匹配时必须失败，防止批量任务串用其他照片或旧版本原图的颜色。

同时用 `view_image` 查看原图和配色预览，逐套比较 `quiet-light`、`editorial-mid`、`cinematic-deep`。按以下顺序选择：

1. 背景是否退到主体之后。
2. 来源色是否属于天空、水面、墙面、道路、木材、植被或石材，而不是皮肤、头发、白边或偶然高光。
3. 信息联是否与画布清楚分离，又与照片属于同一色彩世界。
4. 留白是否干净，避免泥灰中间调、塑料亮色和廉价品牌宣传感。
5. 强色是否有明确叙事依据；同批图片是否误用了相同默认色。

三套都不合格时，调整裁切或排除错误来源后重新运行。不要凭空写一个“看起来高级”的 HEX。

### 3. 生成准确票面信息

- 用户给出标题、日期或文字时逐字采用并核对。
- 地点不能可靠确认时，不猜城市；使用 `COFFEE`、`KOALA`、`OLD TOWN`、`DESERT` 等中性场景词。
- 日期优先级为用户指定值、`DateTimeOriginal`、文件创建日期、当前年月，格式固定为 `YYYY - MM`。
- 自动英文场景词使用大写；中文标题保留中文。标题只使用一到两行。
- `NO.` 后使用 5 位数字；下一行使用 8 位大写字母数字。两者和条形码只承担装饰作用。

### 4. 确定性渲染

优先使用已目视选中的 JSON 候选：

```bash
python3 scripts/render_ticket_poster.py \
  --photo-source source.jpg \
  --photo-center-y 0.5 \
  --output old-town-ticket.png \
  --title "OLD TOWN" \
  --date "2026 - 08" \
  --number 19427 \
  --code E5R8K3M2 \
  --palette-json source-palette.json \
  --palette-candidate editorial-mid \
  --font "/absolute/path/to/pinned-bold-font.ttf" \
  --body-font "/absolute/path/to/pinned-light-mono-font.ttf"
```

需要固定换行时，使用一到两次 `--title-line` 替代 `--title`。用户明确指定颜色时，直接传入 `--background-color`、`--stub-color`、`--text-color`；仍须满足文字对比和画布/信息联层级。同一批次分别固定传入粗体标题字体 `--font` 与细窄等宽正文字体 `--body-font`；未传时脚本会为两种层级各自选择可用字体，并把名称与文件 SHA-256 永久写入 PNG 和命令输出，方便复现与审计。不得退回生成模型拼写文字。

脚本始终拒绝覆盖已有输出。使用可读、版本化的新文件名；不要覆盖唯一原图、配色 JSON 或已确认成品。

### 5. 双重验收

先用 `view_image` 目视检查：

- 主体、裁切、身份、数量、动作、招牌和原图文字无变化。
- 背景安静但不灰脏；信息联与背景有清楚层级；文字舒展、没有挤入缺口。
- 日期、编号和序列码呈细窄等宽轻字重；条形码所有竖条等高、上下齐平，没有阶梯状顶部。
- 画面只有一个水平票根、一条方角虚线和一个右侧半圆缺口。
- 双层阴影落地、连续、克制；没有发光、描边或第二张卡片。
- 没有飞机、地图、指南针、邮戳、护照章、QR 码、价格、额外微缩字、手机 UI 或水印。

再运行确定性验证：

```bash
python3 scripts/validate_ticket_output.py \
  --output old-town-ticket.png \
  --photo-source source.jpg \
  --photo-center-y 0.5 \
  --palette-json source-palette.json \
  --palette-candidate editorial-mid \
  --palette-mode adaptive \
  --font "/absolute/path/to/pinned-bold-font.ttf" \
  --body-font "/absolute/path/to/pinned-light-mono-font.ttf" \
  --expected-title "OLD TOWN" \
  --expected-date "2026 - 08" \
  --expected-number 19427 \
  --expected-code E5R8K3M2 \
  --require-renderer-metadata
```

验证命令里的外部标题、日期、编号、代码必须与渲染参数逐字对应；渲染使用 `--title-line` 时，验证也改为一到两次 `--expected-title-line`。严格模式拒绝缺少任一背景/信息联/文字色或票面文字合同，不能只相信 PNG 自报元数据。

验证器硬检查 PNG/RGB、尺寸、源文件哈希与裁切配方、外部票面文字合同、标题/正文字体身份、等高条形码、原图像素回归、画布和阴影全部外露像素、信息联逐像素重建、唯一虚线、顶部方角首段、透明通道、背景/信息联最低分离度和文字对比。`WARN` 代表超出默认审美软区间，必须结合预览目视确认；任何错误都禁止交付。

用户指定背景色时改用精确 `--expected-background-color`、`--expected-stub-color`、`--expected-text-color` 和 `--palette-mode user-specified`。

## 例外与修复

- **裁切必然损失关键主体**：读取 `prompt-template.md`，只扩展无语义环境。扩展后重新运行取色和确定性渲染，并在交付中标明扩展区域。验证器的 `--photo-source` 使用确认后的扩展图，同时保留原图作目视审计。
- **背景选色普通、灰脏或抢主体**：不要重跑图片模型。改选另一套已有候选；三套都失败时重新取色，再次完整验收。
- **只有外部背景色需要更换**：运行 `recolor_existing_poster.py` 输出新文件。它会同时重建与新背景协调的虚线和双层阴影。
- **旧生成式海报的几何、原图回填或第二条虚线错误**：可用 `normalize_reference_layout.py --photo-source <原图> --background-color <HEX>` 生成迁移预览，但旧图没有可信的票面文字与字体合同，不能冒充严格验收成品。确认标题、日期、编号、代码后，必须回到 `render_ticket_poster.py` 从原图重建并通过严格验证；迁移脚本不是新图默认路径。
- **文字、条码或几何错误**：回到 `render_ticket_poster.py` 修正参数。不得对成品进行连续生成式编辑。
- **任何修复发生后**：旧验收立即失效，重新执行完整目视检查和验证器，不只检查改动项。

## 批量一致性

- 并行生成候选和渲染可以提速，但每张照片必须拥有独立 JSON、预览、标题、裁切、背景、信息联和验收记录。
- 只固定画布、几何、排版层级、缺口、唯一虚线和阴影系统；不要固定每张照片的色相。
- 若连续图片得到完全相同或非常接近的背景，逐张确认来源。真实场景相近可以保留；无法证明来源时重新取色。
- 一张通过不代表整批通过。所有最终 PNG 都通过双重验收后才可交付。

## 完成标准

仅当每张输入都拥有独立成品、绝对路径和所选配色记录，且最终 PNG 为 `1170 × 1560` RGB、照片像素可回归、背景为选定纯色、画布/信息联层级清楚、文字对比合格、票根几何锁定、只有一条方角虚线、阴影自然、没有多余内容，并通过目视检查与验证器时，任务才完成。
