# DY 旅行票根海报

[English](README.en.md) | 简体中文

把单张照片或一批照片做成风格统一的旅行票根海报。Skill 会保留原图中可辨认的人物、动物、建筑、车辆、产品和动作，再根据照片颜色制作居中的票根、撕票信息联、场景标题、日期、编号和装饰性条形码。

每张照片最终交付一张 `1170 × 1560`、`3:4`、无透明通道的 PNG。成品中不会保留手机状态栏、通知、播放器控件和水印。

## 能做什么

- 保留原图中的人物身份、动物、产品、建筑、车辆和关键动作
- 最终照片面板直接使用原始文件像素做等比例裁切与高质量缩放，不使用生成模型重构图，不经过 JPEG 有损中间转码
- 在主体完整的前提下保留足够的环境信息
- 根据每张照片调整海报背景和信息联配色
- 优先采用用户给出的标题、地点和日期
- 地点无法可靠确认时，改用中性场景词
- 自动生成五位编号、八位装饰码和装饰性条形码
- 批量处理时每张照片独立出图，同时保持统一版式
- 使用确定性脚本从原图像素生成 `1170 × 1560` RGB PNG，并保留原始文件

## 视觉系统

整套海报使用固定、克制、可重复的布局。

- 画布比例为 `3:4`
- 票根主体名义坐标为 `x=55, y=501`，尺寸为 `1057 × 507px`
- 左右外边距锁定为参考图的 `55px / 58px`，宽度占画布的 `90.4%`
- 照片区约占票根宽度的 `73.2%`，信息联约占 `26.8%`
- 圆角、竖向撕票线、半圆缺口和轻阴影保持一致；标题使用粗体，日期、编号与序列码使用细窄等宽体
- 装饰条形码统一为 `43px` 等高竖条，只改变条宽和间距，不再出现参差顶部
- 照片与信息联之间始终只有一条方角矩形虚线；虚线首段从票根顶部开始，不使用圆角
- 使用接触阴影与环境阴影两层结构，让整张票根稳定落在背景上
- 画布使用由照片环境色派生的纯色背景；默认高级感软区间为 OKLCH `L=0.64–0.78, C=0.02–0.08`
- 配色随照片变化，信息层级和版式保持不变；批量任务不套统一默认背景色

完整的版式参数见 [references/style-spec.md](references/style-spec.md)。

## 安装与工具支持

这是一个遵循 Open Agent Skills 结构的公开仓库。安装前需确认当前 GitHub 账号已登录 GitHub CLI。

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

私有子模块必须确保 Codex Cloud 连接的 GitHub 账号也有读取权限。标准票根由本地 Python、Pillow，以及固定的粗体标题字体与细窄等宽正文字体确定性完成；只有裁切必然损失关键主体、需要扩展无语义环境时才需要图片生成/编辑能力。

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
| Image generation / `imagegen` | 仅在需要扩展无语义环境时使用 | 例外必需 |
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

工作流会逐张检查照片和最终裁切，使用 [scripts/suggest_palette.py](scripts/suggest_palette.py) 生成三套可追溯配色预览，目视选择后由 [scripts/render_ticket_poster.py](scripts/render_ticket_poster.py) 确定性合成，再通过 [scripts/validate_ticket_output.py](scripts/validate_ticket_output.py) 检查原图像素、纯色背景、颜色层级、文字对比和票根结构。只有裁切必然损失关键主体时，才调用 `imagegen` 扩展无语义环境。

## 信息生成规则

- 用户提供的标题、地点和日期拥有最高优先级
- 没有可靠地点信息时，使用 `COFFEE`、`KOALA`、`OLD TOWN`、`DESERT` 这类中性场景词
- 日期依次采用用户指定值、本地 `DateTimeOriginal`、本地文件日期、当前年月
- GPS 和私人元数据只在本地读取，不会写入图片生成请求
- 编号、装饰码和条形码只承担视觉作用，不保证能够扫描

## 环境要求

- 支持 `SKILL.md` 的 Agent Skills 环境
- Python 3.10+、`requirements.txt` 中声明的 Pillow，以及可用的粗体标题与细窄等宽正文 TTF/OTF/TTC 字体
- 只有扩展无语义环境的例外路径才需要 `imagegen`
- 本地可以访问需要处理的原始照片

先生成配色候选与预览：

```bash
python3 scripts/suggest_palette.py --input source.jpg --output-json palette.json --preview palette-review.png
```

完整渲染和严格验证命令见 [SKILL.md](SKILL.md)。严格模式需要从命令外部再次提供背景、信息联、文字、标题、日期、编号和代码，不能只相信 PNG 自报元数据。

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
├── requirements.txt
├── references/
│   ├── palette-system.md
│   ├── prompt-template.md
│   └── style-spec.md
├── scripts/
│   ├── build_before_after_showcase.py
│   ├── build_ticket_batch.py
│   ├── image_utils.py
│   ├── normalize_output.sh
│   ├── normalize_reference_layout.py
│   ├── palette_utils.py
│   ├── recolor_existing_poster.py
│   ├── render_ticket_poster.py
│   ├── suggest_palette.py
│   ├── test_ticket_pipeline.py
│   └── validate_ticket_output.py
└── README.en.md
```

## 内容边界

画面无法证明具体城市时，Skill 不会猜测地点。制作过程中也不会新增人物、动物、商品、车辆、建筑、标识或其他带有身份信息的细节。确实需要扩展背景时，只处理没有语义的环境区域，并在交付说明中标出。
