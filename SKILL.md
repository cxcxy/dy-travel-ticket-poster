---
name: dy-travel-ticket-poster
description: Convert user-supplied photos into reference-locked 3:4 travel, coffee, or movie ticket posters, and apply a reusable V2 background style system to existing tickets, cards, posters, photos, or products. Supports 20 material-aware style IDs, lighting and shadow presets, style strength, strict subject preservation, diverse style recommendations, photo-derived solid-color fallback, original-pixel photo panels, neutral titles, dates, serials, and barcodes. Use when the user asks to "套旅行票根模板", "做成票根海报", "改成这种旅行票格式", change only a card/poster background, requests a named material such as 洞石/和纸/亚麻/微水泥, asks for multiple differentiated background options, references style_id, or continues a prior ticket-poster batch.
---

# DY 旅行票根海报

把照片转换成干净的票根海报，或只为既有票根、卡片、海报、照片和产品更换高级背景。默认使用简体中文，保持主体真实，不伪造地点和身份信息。

## 先判断工作模式

- **票根构建模式**：用户要把原始照片做成票根。输出 `1170 × 1560`、`3:4`、无透明通道 PNG；使用锁定几何和原始照片像素回填。
- **背景换装模式**：用户已经提供票根、卡片、海报或产品主体，只要求背景风格。保持原画布、主体比例、人物、文字、日期、条形码和版式；除非用户明确要求，不强制改成旅行票根或 `3:4`。

两个模式都必须排除手机状态栏、通知、播放器、进度条、水印和额外文案。

## 执行前读取

1. 票根构建模式完整读取 [references/style-spec.md](references/style-spec.md)。
2. 实际生成或编辑图片时完整读取 [references/prompt-template.md](references/prompt-template.md)。
3. 用户指定背景风格、描述背景氛围或要求多套方案时，使用 [scripts/background_style_system.py](scripts/background_style_system.py) 读取并解析 [references/background-styles.json](references/background-styles.json)；不要手写或猜测注册表字段。
4. 加载并遵循当前环境的 `imagegen` Skill。它负责栅格图片生成与编辑；本 Skill 负责结构、主体保护、确定性合成和验收。

## 背景风格系统 V2

### 调用结构

```yaml
background:
  style_id: travertine_luxury
  strength: balanced
lighting:
  preset: soft_daylight
shadow:
  preset: premium_float
subject_preservation:
  mode: strict
temperature_shift: 0
```

- `strength` 支持 `subtle`、`balanced`、`strong` 或 `0..1`；默认 `balanced`。脚本会按当前风格的安全区间裁剪有效强度。
- 光线支持 `soft_daylight`、`afternoon_sun`、`diffused_window`、`gallery_light`、`center_spotlight`、`overcast_soft`。
- 阴影支持 `flat`、`subtle_float`、`premium_float`、`architectural`；风格模式默认采用该风格推荐值。
- `subject_preservation` 默认并必须优先使用 `strict`。只有用户明确要求主体与背景融合时才允许 `balanced` 或 `creative`。
- 无 `style_id` 且用户没有提出背景风格要求时，沿用逐图取色的低饱和纯色背景，不自动套米色材质。

### 解析与推荐

显式 ID 直接解析：

```bash
python3 scripts/background_style_system.py resolve \
  --style-id travertine_luxury \
  --strength balanced \
  --lighting soft_daylight \
  --shadow premium_float \
  --preservation strict
```

用户只描述“更高级、更暖”之类意图时，先取 3 个推荐，选择与题材最匹配且不压主体的一项；用户要求多套方案时返回指定数量，不重复近似米色：

```bash
python3 scripts/background_style_system.py recommend \
  --context "高级、温暖的旅行票根" --count 10
```

需要生图提示词时运行：

```bash
python3 scripts/background_style_system.py prompt \
  --style-id travertine_luxury \
  --strength balanced \
  --lighting soft_daylight \
  --shadow premium_float \
  --preservation strict
```

不要让用户记住风格 ID。用户说中文风格名、材质、用途或氛围时，用推荐器解析；只有多个候选同样合理且会改变主要视觉方向时才请求选择。

## 主体保护与背景生成

1. 用 `view_image` 检查所有输入；读取像素尺寸和可用的本地 EXIF/文件日期。不要把 GPS 或私人元数据上传第三方。
2. 在 `strict` 模式下，禁止修改人物、人脸、姿势、动物、产品、建筑、车辆、文字、日期、条形码、票根比例和现有版式。
3. 背景优化只作用于材质、纹理、光线、阴影、纵深、色彩和氛围。保持低饱和、低对比、克制纹理；禁止霓虹、重渐变、强光晕、过强 HDR、塑料感、过量颗粒和喧闹装饰。
4. 对票根构建模式，优先生成一张**无主体、无票根、无文字**的 `1170 × 1560` 背景底图，再确定性合成票根。不要让生成模型重画最终照片区。
5. 对背景换装模式，若存在透明主体、遮罩或可精确分离的卡片，优先确定性合成；否则使用图片编辑并重复严格主体保护约束，编辑后逐字、逐物核对。
6. 主体与背景必须有足够明度差。纹理、窗影、斑驳和聚光不得穿过主体正文、人脸、条形码或重要边缘。

## 票根构建工作流

1. 锁定票根主体 `x=55, y=501, width=1057, height=507`；左外边距 `55px`、右外边距 `58px`。照片区 `774 × 507px`，信息联 `283 × 507px`。
2. 为照片确定裁切焦点，先保住人脸、动作、动物、车辆、产品或建筑主体，再保留环境证据。禁止拉伸和 JPEG 中间转码。
3. 生成信息：优先采用用户指定标题、地点和日期；无法可靠判断地点时使用 `COFFEE`、`KOALA`、`OLD TOWN`、`DESERT` 等中性场景词。日期依次采用用户指定、`DateTimeOriginal`、文件日期、当前年月，格式 `YYYY - MM`。装饰编号使用 `NO.` 加 5 位数字和 8 位大写字母数字。
4. 无背景风格要求时，为每张图提取独立的画布色、信息联色和文字色；画布为 HSL 饱和度 `6–20%`、明度 `58–62%` 的单一纯色。显式风格模式只替换外部画布，信息联仍优先与当前照片协调。
5. 按 [references/prompt-template.md](references/prompt-template.md) 生成票根预览和风格背景底图。批量任务逐张处理，不把多张输入拼为一张交付图。
6. 使用 [scripts/normalize_reference_layout.py](scripts/normalize_reference_layout.py) 重建版式，并始终传入 `--photo-source`：
   - 纯色背景用 `--background-color '#RRGGBB'`。
   - 风格背景用 `--background-image <1170x1560-background.png>` 和对应 `--shadow-preset`。
   - 脚本会回填原图像素、清除旧分隔痕迹、只重绘一条方角虚线并重建双层阴影。
7. 只有外部纯色背景错误时，使用 [scripts/recolor_existing_poster.py](scripts/recolor_existing_poster.py)。它不用于生成材质背景。
8. 使用 [scripts/normalize_output.sh](scripts/normalize_output.sh) 安全归一化最终尺寸；输出新文件，不覆盖唯一源图或已确认成品。
9. 用 `view_image` 检查最终 PNG，用 `sips` 或 `magick identify` 核对尺寸，并运行 [scripts/validate_ticket_output.py](scripts/validate_ticket_output.py) 验证源照片像素回归、唯一虚线和顶部方角首段。

## 裁切与批量规则

- 照片面板按约 `1.53:1` 直接从原图使用 Lanczos 等比例裁切缩放，不拉伸、不重绘、不经过有损中间文件。
- 普通裁切会切掉关键主体时，只允许对无语义背景做最小扩展，并在交付说明标出；不得生成新人物、动物、商品、车辆、建筑或标识。
- 票根批量固定画布、几何、照片/信息联比例、外轮廓圆角、唯一方角撕票线、缺口和文字层级。
- 未指定风格时，每张照片独立取色；指定同一 `style_id` 时，锁定风格身份但仍需根据照片调整主体对比和信息联配色。
- 多风格方案必须优先拉开材质、光线、纹理、温度和纵深差异，而不是随机生成相近米色。
- 每张单独验收；一张通过不代表整批通过。

## 失败处理

- **人脸、物体、文字或条形码改变**：结果作废，回到 `strict`，优先使用背景底图加确定性合成。
- **原图被压扁、重绘或有损压缩**：禁止交付生成图中的照片区；用 `normalize_reference_layout.py --photo-source` 回填，并与同参数 `ImageOps.fit` 结果做像素回归。
- **两条虚线**：清除信息联左缘 `20px` 内旧分隔，只保留一条宽 `7px` 的方角矩形虚线；第一段从票根顶部开始。
- **材质太明显或抢主体**：先降为 `subtle`，再降低光线或阴影；不要通过模糊主体解决。
- **风格变成廉价 AI 效果**：按注册表 `avoid` 和全局负向词重做；检查渐变、光晕、HDR、颗粒、塑料感和饱和度。
- **窗影或纹理压住文字/人脸**：只移动或减弱背景光影，不移动主体。
- **风格 ID 不存在**：运行推荐器给出相近候选，不静默回退到任意米色。
- **背景底图尺寸错误**：重新生成或归一化为精确 `1170 × 1560`，不要在合成时拉伸。
- **地点不明**：使用中性场景词，不虚构城市。

## 完成标准

票根构建模式仅在以下条件全部成立后完成：独立成品为 `1170 × 1560`；左右边距符合锁定值；照片面板可回归原始文件等比例裁切；全高只有一条方角虚线；双层阴影连续自然；文字可读；票根结构完整；背景符合指定 `style_id` 或逐图纯色回退；没有 UI 或水印。

背景换装模式仅在主体内容、人物、文字、日期、条形码、比例和版式逐项不变，背景风格、强度、光线与阴影符合解析配置，主体仍为第一视觉层级，输出尺寸与用户要求一致，并已提供绝对路径后完成。
