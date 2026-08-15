# DY 旅行票根海报

[English](README.en.md) | 简体中文 | [在线预览 12 种风格](https://cxcxy.github.io/dy-travel-ticket-poster/)

把单张照片或一批照片做成风格统一的旅行票根海报。Skill 会保留原图中可辨认的人物、动物、建筑、车辆、产品和动作，再根据照片颜色制作居中的票根、撕票信息联、场景标题、日期、编号和装饰性条形码。

每张照片最终交付一张 `1170 × 1560`、`3:4`、无透明通道的 PNG。成品中不会保留手机状态栏、通知、播放器控件和水印。

## 2026-08-15 更新

- 新增图集锁定的 12 种可配置背景风格，可使用序号、中文名或 `style_id` 选择。
- 未指定风格时，默认改为照片主题色驱动的“近似纯色 + 极轻微单色质感”背景；纹理严格限制在基色约 `±3`，不自动加入渐变、暗角、窗影、树影或聚光。
- 批量任务默认由每张照片独立提取主题色；只有明确要求“统一色系”时才共享同一颜色。
- 新增 [GitHub Pages 12 风格预览站](https://cxcxy.github.io/dy-travel-ticket-poster/)，支持材质筛选、放大查看和复制调用语句。
- 新增 [scripts/build_pages_gallery.py](scripts/build_pages_gallery.py)，可从锁定注册表和原始图集重新生成网页数据与轻量 WebP 预览，生成前会校验 12 张参考图的 SHA-256。

## 能做什么

- 保留原图中的人物身份、动物、产品、建筑、车辆和关键动作
- 最终照片面板直接使用原始文件像素做等比例裁切与高质量缩放，不使用生成模型重构图，不经过 JPEG 有损中间转码
- 在主体完整的前提下保留足够的环境信息
- 根据每张照片调整海报背景和信息联配色
- 可用图集锁定的 12 个 `style_id` 调用完整材质、色彩、纹理、光线、阴影和纵深系统
- 支持 `subtle / balanced / strong` 强度、通用与图集专用光线、4 种阴影和严格主体保护
- 用户不记得风格名时，可按题材与氛围推荐差异明显的多套背景
- 优先采用用户给出的标题、地点和日期
- 地点无法可靠确认时，改用中性场景词
- 自动生成五位编号、八位装饰码和装饰性条形码
- 批量处理时每张照片独立出图，同时保持统一版式
- 将通过检查的成品归一化为 `1170 × 1560` PNG，并保留原始文件

## 视觉系统

整套海报使用固定、克制、可重复的布局。

- 画布比例为 `3:4`
- 票根主体名义坐标为 `x=55, y=501`，尺寸为 `1057 × 507px`
- 左右外边距锁定为参考图的 `55px / 58px`，宽度占画布的 `90.4%`
- 照片区约占票根宽度的 `73.2%`，信息联约占 `26.8%`
- 圆角、竖向撕票线、半圆缺口、轻阴影和粗体窄字保持一致
- 照片与信息联之间始终只有一条方角矩形虚线；虚线首段从票根顶部开始，不使用圆角
- 使用接触阴影与环境阴影两层结构，让整张票根稳定落在背景上
- 未指定风格时，画布默认使用照片主题色驱动的“近似纯色 + 极轻微单色质感”背景，明度 `58–62%`、饱和度 `6–20%`；不出现明显光斑、渐变或图案
- 配色随照片变化，信息层级和版式保持不变；批量任务不套统一默认背景色

完整的版式参数见 [references/style-spec.md](references/style-spec.md)。

## 图集锁定的 12 种背景风格

显式指定风格后，Skill 会从 [references/gallery-12-background-styles.json](references/gallery-12-background-styles.json) 解析完整配置。12 种风格由用户提供的 12 张图集逐张提炼，并用原文件名、SHA-256、实测背景中值色与视觉签名锁定来源；只迁移背景材质、光型、明暗衰减和空间关系，不复制参考照片、人物、文字或编号。材质、光线和阴影彼此可组合；默认使用 `balanced` 强度和 `strict` 主体保护。颜色默认不锁死：未指定背景色时，每张照片从最终裁切提取自己的主题色；只有用户明确要求时才统一整组色系。未指定风格时使用逐图轻质感纯色背景，不调用生图模型。通用 20 风格基线继续保存在 [references/background-styles.json](references/background-styles.json)，可通过 `--registry` 显式调用。

| `style_id` | 中文名 | 主要材质 / 氛围 |
| --- | --- | --- |
| `warm_linen_side_light` | 暖灰亚麻侧光 | 亚麻墙布、右侧宽幅柔光 |
| `ivory_paper_window_veil` | 象牙艺术纸柔窗影 | 艺术纸、高明度柔斜影 |
| `sand_center_glow` | 沙岩中心柔光 | 沙色矿物墙、中心纵向柔光 |
| `mushroom_cinematic_vignette` | 蘑菇灰电影墙 | 暖灰矿物墙、成熟边缘衰减 |
| `caramel_dappled_sun` | 焦糖树影墙 | 焦糖石灰墙、虚化午后光斑 |
| `natural_washi_halo` | 天然和纸柔光 | 手工和纸、顶部中央漫射光 |
| `greige_stucco_soft_beams` | 暖灰灰泥柔影 | 灰泥墙、宽幅纵向柔影 |
| `ivory_stucco_window_beam` | 象牙灰泥窗光 | 象牙灰泥、建筑斜向窗光 |
| `cream_limewash_diffusion` | 奶油石灰墙漫射 | 石灰墙、宽阔不规则漫射 |
| `ivory_travertine_diagonal` | 象牙洞石斜光 | 明亮洞石、宽幅斜光 |
| `cotton_paper_top_glow` | 棉纸顶光 | 天然棉纸、对称顶光 |
| `caramel_mineral_spotlight` | 焦糖矿物聚光 | 深焦糖矿物墙、左上聚光 |

### 在线查看与维护预览网站

完整视觉卡片位于 [GitHub Pages 12 风格预览站](https://cxcxy.github.io/dy-travel-ticket-poster/)。网站源码保存在 [`docs/`](docs/)，部署工作流为 [`.github/workflows/pages.yml`](.github/workflows/pages.yml)。合并到 `main` 后，工作流会把 `docs/` 作为静态站点发布；仓库首次启用时，需要在 GitHub **Settings → Pages → Build and deployment** 中选择 **GitHub Actions**。

本地预览：

```bash
python3 -m http.server 8000 --directory docs
```

浏览器打开 `http://127.0.0.1:8000/`。参考图集发生变更时，先运行：

```bash
python3 scripts/build_pages_gallery.py \
  --source-dir "/absolute/path/to/gallery" \
  --default-preview "/absolute/path/to/default-ticket.png"
```

脚本只在 12 张来源文件全部通过注册表哈希校验后更新网页资产、`docs/style-data.json` 和可供本地直接打开的 `docs/style-data.js`。

最常见的使用方式就是：上传一张或一组照片，再选择上面的一种风格。可以说“第10种”、中文名或 `style_id`。单图输出一张票根；多图默认锁定同一风格、强度、光线和阴影，但背景颜色按每张照片主题色独立适配，逐张输出独立票根，不拼图、不随机换风格。只有明确说“统一色系”时才共用同一个背景色系。

```text
把这一组图片分别做成票根，全部使用第10种，其他按默认。
```

上面的“默认”表示每张图独立取主题色。需要统一颜色时可以说：

```text
把这一组图片分别做成票根，全部使用第10种，并统一为灰蓝色系。
```

直接调用：

```text
使用 $dy-travel-ticket-poster，把背景改成 ivory_travertine_diagonal，强度 balanced，使用 stone_diagonal 和 architectural；主体保护 strict。
```

也可以只描述意图：

```text
使用 $dy-travel-ticket-poster，给这张票根推荐 10 个材质差异明显的高级背景方案。
```

命令行可验证、解析、推荐或生成标准 Prompt：

```bash
python3 scripts/background_style_system.py validate
python3 scripts/background_style_system.py recommend --context "高级温暖的旅行票根" --count 10
python3 scripts/background_style_system.py prompt --style-id "第10种" --strength balanced --palette-mode adaptive --theme-color '#8FA6AD'
python3 scripts/adapt_background_plate.py --plate material.png --source-photo photo.jpg --palette-mode adaptive --output background.png
python3 scripts/build_subtle_texture_background.py --source-photo photo.jpg --palette-mode adaptive --output background.png
python3 scripts/validate_gallery_references.py --source-dir "/absolute/path/to/gallery"
```

## 安装与工具支持

这是一个遵循 Open Agent Skills 结构的私有仓库。安装前需确认当前 GitHub 账号拥有仓库访问权限，并已登录 GitHub CLI。

### Codex 桌面端、CLI 与 IDE 扩展

安装到用户级 Skills 目录：

```bash
mkdir -p "$HOME/.agents/skills"
gh repo clone cxcxy/dy-travel-ticket-poster "$HOME/.agents/skills/dy-travel-ticket-poster"
```

Codex 通常会自动发现新增 Skill；若没有出现，重新启动 Codex。使用时输入 `$dy-travel-ticket-poster`。

### Codex Cloud

Codex Cloud 任务需要从目标项目仓库读取这个 Skill。推荐把它作为子模块放在目标项目根目录的 `.agents/skills/` 中：

```bash
mkdir -p .agents/skills
git submodule add https://github.com/cxcxy/dy-travel-ticket-poster.git \
  .agents/skills/dy-travel-ticket-poster
git submodule update --init --recursive
```

私有子模块必须确保 Codex Cloud 连接的 GitHub 账号也有读取权限。云端环境还需要提供图片生成/编辑能力；若要运行归一化脚本，还需在环境中安装 ImageMagick。

### Claude Code 与其他 Agent Skills 工具

支持 Agent Skills 的工具可以把本仓库放进各自的 Skills 目录。以 Claude Code 的用户级目录为例：

```bash
mkdir -p "$HOME/.claude/skills"
gh repo clone cxcxy/dy-travel-ticket-poster "$HOME/.claude/skills/dy-travel-ticket-poster"
```

这些工具必须另外提供兼容的图片生成或图片编辑能力；仅能读取 `SKILL.md` 但不能编辑图片时，无法完成成片工作流。

### Codex Plugins 与常用配套工具

在 ChatGPT/Codex 桌面端打开 **Plugins** 安装；在 Codex CLI 中输入 `/plugins`。安装后新建任务再使用。以下工具不是全部必需：

| 工具或 Plugin | 用途 | 是否必需 |
| --- | --- | --- |
| Image generation / `imagegen` | 按票根视觉系统编辑并生成图片 | 必需 |
| GitHub | 维护 Skill 仓库、查看提交或协作修改 | 可选 |
| Google Drive / Box | 读取原始照片或保存交付图 | 可选 |
| Canva | 在成片后继续排版或人工微调 | 可选 |

Plugin 不会自动获得本地私人照片；仍需由用户明确选择或授权文件。没有对应 Plugin 时，直接使用本地文件即可。

参考：[Codex Skills 官方文档](https://learn.chatgpt.com/docs/build-skills) · [Codex Plugins 官方文档](https://learn.chatgpt.com/docs/plugins) · [Claude Code Skills 官方文档](https://code.claude.com/docs/en/skills)

## 使用方法

附上一张或多张本地 PNG、JPG 照片，然后让 Codex 使用这个 Skill。

```text
使用 $dy-travel-ticket-poster，把这些照片做成统一的 3:4 旅行票根海报。
```

也可以直接指定标题和日期。

```text
使用 $dy-travel-ticket-poster 处理这张照片，标题用 WATERFRONT，日期用 2026 - 08。
```

工作流会逐张检查照片，选择安全的裁切区域并整理票根信息。未指定风格时，[scripts/build_subtle_texture_background.py](scripts/build_subtle_texture_background.py) 直接生成主题色轻质感纯色背景，不调用生图模型；显式图集风格才调用 `imagegen` 生成无主体材质母版，再由 [scripts/adapt_background_plate.py](scripts/adapt_background_plate.py) 适配主题色。最后通过 [scripts/normalize_reference_layout.py](scripts/normalize_reference_layout.py) 回填原始照片像素和票根，目视检查并输出标准尺寸成品。

## 信息生成规则

- 用户提供的标题、地点和日期拥有最高优先级
- 没有可靠地点信息时，使用 `COFFEE`、`KOALA`、`OLD TOWN`、`DESERT` 这类中性场景词
- 日期依次采用用户指定值、本地 `DateTimeOriginal`、本地文件日期、当前年月
- GPS 和私人元数据只在本地读取，不会写入图片生成请求
- 编号、装饰码和条形码只承担视觉作用，不保证能够扫描

## 环境要求

- Codex 环境中可以使用 `imagegen` Skill
- 本地安装 ImageMagick，用于最终尺寸归一化
- 本地安装 Pillow，用于确定性版式重建和背景定向换色
- 本地可以访问需要处理的原始照片

成品通过目视检查后，可以单独运行归一化脚本。

```bash
bash scripts/normalize_output.sh generated-image.png final-ticket.png
```

## 参考案例

下面展示本次提供的原始照片和对应票根成品。文档页面会按合适宽度显示预览，实际工作流输出仍为 `1170 × 1560` PNG。

### 01 · 咖啡吧台

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/coffee-original.jpg" width="360" alt="咖啡吧台原图"></td>
    <td><img src="assets/cases/coffee-ticket.jpg" width="360" alt="咖啡吧台票根海报"></td>
  </tr>
</table>

### 02 · 考拉合影

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/koala-original.jpg" width="360" alt="考拉合影原图"></td>
    <td><img src="assets/cases/koala-ticket.png" width="360" alt="考拉合影票根海报"></td>
  </tr>
</table>

### 03 · 历史建筑

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/heritage-original.jpg" width="360" alt="历史建筑人物原图"></td>
    <td><img src="assets/cases/heritage-ticket.jpg" width="360" alt="历史建筑人物票根海报"></td>
  </tr>
</table>

### 04 · 露天剧场

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/theater-original.jpg" width="360" alt="露天剧场原图"></td>
    <td><img src="assets/cases/theater-ticket.jpg" width="360" alt="露天剧场票根海报"></td>
  </tr>
</table>

### 05 · 精品店陈列

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/boutique-original.jpg" width="360" alt="精品店陈列原图"></td>
    <td><img src="assets/cases/boutique-ticket.jpg" width="360" alt="精品店陈列票根海报"></td>
  </tr>
</table>

### 06 · 老城街道

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/old-town-original.jpg" width="360" alt="彩色老城街道原图"></td>
    <td><img src="assets/cases/old-town-ticket.jpg" width="360" alt="彩色老城街道票根海报"></td>
  </tr>
</table>

### 07 · 咖啡与甜点

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/cafe-original.jpg" width="360" alt="咖啡与甜点俯拍原图"></td>
    <td><img src="assets/cases/cafe-ticket.jpg" width="360" alt="咖啡与甜点票根海报"></td>
  </tr>
</table>

### 08 · 沙漠行车

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/desert-original.jpg" width="360" alt="沙漠红色车辆原图"></td>
    <td><img src="assets/cases/desert-ticket.jpg" width="360" alt="沙漠红色车辆票根海报"></td>
  </tr>
</table>

### 09 · 水岸摄影

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/waterfront-original.jpg" width="360" alt="水岸摄影人物原图"></td>
    <td><img src="assets/cases/waterfront-ticket.jpg" width="360" alt="水岸摄影人物票根海报"></td>
  </tr>
</table>

### 10 · 湖边远眺

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/lakeside-original.jpg" width="360" alt="湖边人物远眺原图"></td>
    <td><img src="assets/cases/lakeside-ticket.jpg" width="360" alt="湖边人物远眺票根海报"></td>
  </tr>
</table>

### 11 · 黄色住宅

<table>
  <tr><th>原图</th><th>生成的票根海报</th></tr>
  <tr>
    <td><img src="assets/cases/gold-house-original.jpg" width="360" alt="黄色住宅原图"></td>
    <td><img src="assets/cases/gold-house-ticket.jpg" width="360" alt="黄色住宅票根海报"></td>
  </tr>
</table>

## 仓库结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── assets/cases/
├── references/background-styles.json
├── references/gallery-12-background-styles.json
├── references/prompt-template.md
├── references/style-spec.md
├── scripts/background_style_system.py
├── scripts/adapt_background_plate.py
├── scripts/build_subtle_texture_background.py
├── scripts/build_before_after_showcase.py
├── scripts/build_ticket_batch.py
├── scripts/normalize_output.sh
├── scripts/normalize_reference_layout.py
├── scripts/recolor_existing_poster.py
├── scripts/validate_gallery_references.py
└── tests/
```

## 内容边界

画面无法证明具体城市时，Skill 不会猜测地点。制作过程中也不会新增人物、动物、商品、车辆、建筑、标识或其他带有身份信息的细节。确实需要扩展背景时，只处理没有语义的环境区域，并在交付说明中标出。
