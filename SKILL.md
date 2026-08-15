---
name: dy-travel-ticket-poster
description: Convert user-supplied photos into reference-locked 3:4 travel, coffee, or movie ticket posters, and apply a configurable 12-style gallery-derived background system to existing tickets, cards, posters, photos, or products. Defaults to a photo-adaptive near-solid background with very subtle tactile texture, supports optional batch-wide unified color families, explicit reference-anchored material and light styles, strict subject preservation, deterministic original-pixel crops, separate title/body typography, uniform-height barcodes, neutral titles, dates, and serials. Use when the user asks to "套旅行票根模板", "做成票根海报", "改成这种旅行票格式", match one of the 12 supplied gallery backgrounds, change only a card/poster background, requests materials such as 洞石/和纸/亚麻/灰泥, asks for multiple differentiated background options, references style_id, or continues a prior ticket-poster batch.
---

# DY 旅行票根海报

把照片转换成干净的票根海报，或只为既有票根、卡片、海报、照片和产品更换高级背景。默认使用简体中文，保持主体真实，不伪造地点和身份信息。

## 先判断工作模式

- **票根构建模式**：用户要把原始照片做成票根。输出 `1170 × 1560`、`3:4`、无透明通道 PNG；使用锁定几何和原始照片像素回填。
- **背景换装模式**：用户已经提供票根、卡片、海报或产品主体，只要求背景风格。保持原画布、主体比例、人物、文字、日期、条形码和版式；除非用户明确要求，不强制改成旅行票根或 `3:4`。

两个模式都必须排除手机状态栏、通知、播放器、进度条、水印和额外文案。

## 质量合同

- 票根构建必须使用本地确定性脚本完成裁切、背景合成、信息联、文字、条码、虚线、缺口与阴影；不得让图片模型拼写最终文字或重画照片区。
- 标题使用独立的粗体字体；日期、编号和 8 位序列码使用细窄等宽正文字体。两种字体的名称与文件 SHA-256 写入最终 PNG 元数据。
- 装饰条形码的所有竖条固定为完整 `43px` 高，顶部和底部各自齐平，只改变条宽和间距。
- 配色必须来自当前照片最终裁切并保留来源记录。先按 [references/palette-system.md](references/palette-system.md) 生成候选并目视选择，再把选中的画布色用于默认轻质感背景或显式风格适配。
- 严格验收必须同时检查原图像素、外部票面文字合同、标题/正文字体身份、等高条码、唯一方角虚线、画布/信息联层级和文字对比；不能只相信 PNG 自报元数据。

## 执行前读取

1. 票根构建模式完整读取 [references/style-spec.md](references/style-spec.md) 与 [references/palette-system.md](references/palette-system.md)。
2. 实际需要图片生成或编辑时完整读取 [references/prompt-template.md](references/prompt-template.md)。
3. 用户指定背景风格、描述背景氛围或要求多套方案时，使用 [scripts/background_style_system.py](scripts/background_style_system.py) 读取并解析默认的 [references/gallery-12-background-styles.json](references/gallery-12-background-styles.json)；不要手写或猜测注册表字段。通用 20 风格基线保留在 [references/background-styles.json](references/background-styles.json)，只有用户明确要求旧风格时才用 `--registry` 切换。
4. 只有显式风格需要生成材质母版，或裁切确实需要扩展无语义环境时，才加载并遵循当前环境的 `imagegen` Skill。默认轻质感纯色背景使用本地确定性脚本，不上传照片也不调用生图模型。

## 图集锁定的 12 风格系统

### 调用结构

```yaml
background:
  style_id: ivory_travertine_diagonal
  strength: balanced
palette:
  mode: adaptive
  theme_color: null
lighting:
  preset: stone_diagonal
shadow:
  preset: architectural
subject_preservation:
  mode: strict
temperature_shift: 0
```

- `strength` 支持 `subtle`、`balanced`、`strong` 或 `0..1`；默认 `balanced`。脚本会按当前风格的安全区间裁剪有效强度。
- 光线既保留 6 个通用预设，也提供与图集对应的侧光、柔窗影、中心柔光、电影衰减、树影、纸张柔光、纵向柔影、建筑斜光、石灰墙漫射、洞石斜光、顶光和左上聚光预设。
- 阴影支持 `flat`、`subtle_float`、`premium_float`、`architectural`；风格模式默认采用该风格推荐值。
- `subject_preservation` 默认并必须优先使用 `strict`。只有用户明确要求主体与背景融合时才允许 `balanced` 或 `creative`。
- `palette.mode` 默认是 `adaptive`：用户没有指定背景色时，从每张照片最终票根裁切区域提取独立主题色，风格只锁定材质、纹理、光型和阴影，不强制注册表色相。
- 只有用户明确要求“统一色系”“全部同色”或给出统一色值时，才使用 `palette.mode=unified`。可直接采用用户色值，也可从整组照片共同提取一套代表色；同一风格本身不等于统一色系。
- 无 `style_id` 且用户没有提出背景风格要求时，默认使用逐图取色的低饱和“近似纯色 + 极轻微单色纹理”背景，不自动加入明显树影、窗影、聚光、渐变或大块斑驳。

12 个默认风格按用户图集顺序固定为：

1. `warm_linen_side_light` 暖灰亚麻侧光
2. `ivory_paper_window_veil` 象牙艺术纸柔窗影
3. `sand_center_glow` 沙岩中心柔光
4. `mushroom_cinematic_vignette` 蘑菇灰电影墙
5. `caramel_dappled_sun` 焦糖树影墙
6. `natural_washi_halo` 天然和纸柔光
7. `greige_stucco_soft_beams` 暖灰灰泥柔影
8. `ivory_stucco_window_beam` 象牙灰泥窗光
9. `cream_limewash_diffusion` 奶油石灰墙漫射
10. `ivory_travertine_diagonal` 象牙洞石斜光
11. `cotton_paper_top_glow` 棉纸顶光
12. `caramel_mineral_spotlight` 焦糖矿物聚光

注册表用参考图文件名、SHA-256、实测背景中值色和视觉签名锁定来源关系。生成时只迁移背景身份，不复制图集里的咖啡照片、人物、文字、编号或条形码。

维护或替换参考图集时先验证来源锚点：

```bash
python3 scripts/validate_gallery_references.py --source-dir "/absolute/path/to/gallery"
```

哈希、尺寸或安全背景区中值色任一不一致时停止，不要静默把新图片解释成旧风格。

### 用户选择一种风格后制作票根

把“附件 + 一个风格选择”作为最简调用契约。风格选择可以是序号、中文名或 `style_id`，例如 `第10种`、`象牙洞石斜光`、`ivory_travertine_diagonal`，三者必须解析到同一个配置。

- 单张图片：输出一张独立票根 PNG。
- 一组图片：默认把同一风格、强度、光线和阴影锁定到整组，但背景色按每张照片的主题色独立适配，逐张生成独立票根 PNG；不要把多张照片拼在一张海报里，也不要为每张随机换风格。
- 整组中允许背景主题色、照片裁切、标题、日期、编号、装饰码和信息联配色按各自素材调整；票根几何、材质、纹理、光型、阴影与所选风格身份保持不变。
- 用户明确要求统一色系时，整组改用同一个主题色和同一张适配后的背景底图；统一色系不是默认值。
- 用户明确为不同图片指定不同风格时才逐张覆盖；没有逐张覆盖时，第一处风格选择作用于整组。
- 用户只说“用 12 风格做票根”但没有选择具体一项时，列出序号与中文名等待选择，或按用户要求先推荐 3 项；不要静默随机选择。
- 用户只说“做票根”且没有提到 12 风格时，使用逐图主题色的轻质感纯色默认模式。

推荐的自然语言调用：

```text
把这张图片做成票根，使用第10种，其他按默认。
```

```text
把这一组图片分别做成票根，全部使用焦糖树影墙，颜色按各自图片主题色，强度 balanced。

把这一组图片分别做成票根，全部使用焦糖树影墙，并统一为灰蓝色系。
```

### 解析与推荐

序号、中文名或显式 ID 都先解析成规范 `style_id`：

```bash
python3 scripts/background_style_system.py resolve \
  --style-id "第10种" \
  --strength balanced \
  --lighting stone_diagonal \
  --shadow architectural \
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
  --style-id ivory_travertine_diagonal \
  --strength balanced \
  --palette-mode adaptive \
  --theme-color '#8FA6AD' \
  --lighting stone_diagonal \
  --shadow architectural \
  --preservation strict
```

不要让用户记住风格 ID。用户说中文风格名、材质、用途或氛围时，用推荐器解析；只有多个候选同样合理且会改变主要视觉方向时才请求选择。

## 主体保护与背景生成

1. 用 `view_image` 检查所有输入；读取像素尺寸和可用的本地 EXIF/文件日期。不要把 GPS 或私人元数据上传第三方。
2. 在 `strict` 模式下，禁止修改人物、人脸、姿势、动物、产品、建筑、车辆、文字、日期、条形码、票根比例和现有版式。
3. 背景优化只作用于材质、纹理、光线、阴影、纵深、色彩和氛围。默认模式必须保持低饱和、低对比和近似纯色，纹理仅提供轻微触感；禁止霓虹、重渐变、强光晕、过强 HDR、塑料感、过量颗粒和喧闹装饰。
4. 对票根构建模式，无显式风格时直接使用 [scripts/build_subtle_texture_background.py](scripts/build_subtle_texture_background.py) 确定性生成 `1170 × 1560` 轻质感纯色背景，不调用生图模型。显式选择 12 风格时，才先生成一张**无主体、无票根、无文字**的材质母版，再用 [scripts/adapt_background_plate.py](scripts/adapt_background_plate.py) 适配主题色。不要让生成模型重画最终照片区。
5. 对背景换装模式，若存在透明主体、遮罩或可精确分离的卡片，优先确定性合成；否则使用图片编辑并重复严格主体保护约束，编辑后逐字、逐物核对。
6. 主体与背景必须有足够明度差。纹理、窗影、斑驳和聚光不得穿过主体正文、人脸、条形码或重要边缘。

## 票根构建工作流

1. 锁定票根主体 `x=55, y=501, width=1057, height=507`；左外边距 `55px`、右外边距 `58px`。照片区 `774 × 507px`，信息联 `283 × 507px`。
2. 为照片确定裁切焦点，先保住人脸、动作、动物、车辆、产品或建筑主体，再保留环境证据。禁止拉伸和 JPEG 中间转码。
3. 生成信息：优先采用用户指定标题、地点和日期；无法可靠判断地点时使用 `COFFEE`、`KOALA`、`OLD TOWN`、`DESERT` 等中性场景词。日期依次采用用户指定、`DateTimeOriginal`、文件日期、当前年月，格式 `YYYY - MM`。装饰编号使用 `NO.` 加 5 位数字和 8 位大写字母数字。
4. 使用 `scripts/suggest_palette.py` 为每张最终裁切生成 `quiet-light / editorial-mid / cinematic-deep` 三套可追溯候选，结合 `view_image` 逐张目视选择。默认背景以选中画布色为主题，优先约束在 HSL 饱和度 `6–20%`、明度 `58–62%`，但不得牺牲画布/信息联层级与文字对比。
5. 无显式风格时运行 `build_subtle_texture_background.py --palette-mode adaptive --source-photo <photo> --photo-center-y <crop>`。显式风格时按 [references/prompt-template.md](references/prompt-template.md) 生成无主体材质母版，再运行 `adapt_background_plate.py`；只有统一色系模式才使用 `--palette-mode unified` 和共同色值或整组素材。批量任务逐张处理，不把多张输入拼为一张交付图。
6. 使用 [scripts/build_ticket_batch.py](scripts/build_ticket_batch.py) 或 [scripts/render_ticket_poster.py](scripts/render_ticket_poster.py) 从原图确定性构建最终票根。批量清单可为每项提供 `background` 或 `background_image`，二者必须且只能提供一个；风格背景还可提供 `shadow_preset`。渲染器负责独立标题/正文字体、等高条码、唯一方角虚线、缺口、主题色阴影和元数据。
7. [scripts/normalize_reference_layout.py](scripts/normalize_reference_layout.py) 只用于迁移旧生成式票根或回填已有票根的原始照片像素；始终传入 `--photo-source`。它兼容 `--background-color`、`--background-image`、`--shadow-preset`、`--perforation-color` 和边框保留选项，但不能替代新图的确定性文字合同。
8. 只有旧版完全纯色背景错误时，使用 [scripts/recolor_existing_poster.py](scripts/recolor_existing_poster.py)。新默认背景应重新运行 `build_subtle_texture_background.py`，不要用完全纯色覆盖掉轻微质感。
9. 用 `view_image` 检查最终 PNG，并运行 [scripts/validate_ticket_output.py](scripts/validate_ticket_output.py)；严格模式传入外部标题、日期、编号、代码、标题字体和正文字体合同，验证源照片像素、背景层级、文字对比、字体身份、等高条码、唯一虚线与顶部方角首段。

## 裁切与批量规则

- 照片面板按约 `1.53:1` 直接从原图使用 Lanczos 等比例裁切缩放，不拉伸、不重绘、不经过有损中间文件。
- 普通裁切会切掉关键主体时，只允许对无语义背景做最小扩展，并在交付说明标出；不得生成新人物、动物、商品、车辆、建筑或标识。
- 票根批量固定画布、几何、照片/信息联比例、外轮廓圆角、唯一方角撕票线、缺口和文字层级。
- 未指定颜色时，无论是否选定风格，每张照片都独立取主题色；整组选定同一风格时只锁定材质、纹理、强度、光线、阴影和风格身份，不复用同一张最终背景底图。
- 用户明确要求统一色系时，才锁定一套主题色并复用同一张适配后的背景底图；若用户没有给色值，可从整组最终裁切共同提取代表色。
- 多风格方案必须优先拉开材质、光线、纹理、温度和纵深差异，而不是随机生成相近米色。
- 每张单独验收；一张通过不代表整批通过。

## 失败处理

- **人脸、物体、文字或条形码改变**：结果作废，回到 `strict`，优先使用背景底图加确定性合成。
- **原图被压扁、重绘或有损压缩**：禁止交付生成图中的照片区；用 `normalize_reference_layout.py --photo-source` 回填，并与同参数 `ImageOps.fit` 结果做像素回归。
- **两条虚线**：清除信息联左缘 `20px` 内旧分隔，只保留一条宽 `7px` 的方角矩形虚线；第一段从票根顶部开始。
- **材质太明显或抢主体**：先降为 `subtle`，再降低光线或阴影；不要通过模糊主体解决。
- **默认背景出现明显图案、光斑或渐变**：结果作废，重新运行 `build_subtle_texture_background.py`；默认只允许近似纯色和不可辨识的细微单色纹理。
- **风格变成廉价 AI 效果**：按注册表 `avoid` 和全局负向词重做；检查渐变、光晕、HDR、颗粒、塑料感和饱和度。
- **窗影或纹理压住文字/人脸**：只移动或减弱背景光影，不移动主体。
- **风格 ID 不存在**：运行推荐器给出相近候选，不静默回退到任意米色。
- **背景底图尺寸错误**：重新生成或归一化为精确 `1170 × 1560`，不要在合成时拉伸。
- **地点不明**：使用中性场景词，不虚构城市。

## 完成标准

票根构建模式仅在以下条件全部成立后完成：独立成品为 `1170 × 1560`；左右边距符合锁定值；照片面板可回归原始文件等比例裁切；全高只有一条方角虚线；标题使用粗体且正文使用独立细窄等宽字体；条形码全部竖条等高；双层阴影连续自然；外部票面文字合同逐字通过；未指定颜色时背景可追溯到当前照片主题色，统一色系仅在用户明确要求时启用；无显式风格时背景呈近似纯色且只有极轻微单色质感，显式风格时符合指定 `style_id`；没有 UI 或水印。

背景换装模式仅在主体内容、人物、文字、日期、条形码、比例和版式逐项不变，背景风格、强度、光线与阴影符合解析配置，主体仍为第一视觉层级，输出尺寸与用户要求一致，并已提供绝对路径后完成。
