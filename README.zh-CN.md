# DY 旅行票根海报

[English](README.md) | 简体中文

把单张照片或一批照片做成风格统一的旅行票根海报。Skill 会保留原图中可辨认的人物、动物、建筑、车辆、产品和动作，再根据照片颜色制作居中的票根、撕票信息联、场景标题、日期、编号和装饰性条形码。

每张照片最终交付一张 `1170 × 1560`、`3:4`、无透明通道的 PNG。成品中不会保留手机状态栏、通知、播放器控件和水印。

## 安装

### 直接让 Codex 安装（推荐）

把下面这句话直接发给 Codex：

```text
请帮我安装这个 Skill：https://github.com/cxcxy/dy-travel-ticket-poster，并在安装完成后检查 Codex 是否能够识别它。
```

### Codex 手动安装

```bash
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git
cd dy-travel-ticket-poster
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R . "${CODEX_HOME:-$HOME/.codex}/skills/dy-travel-ticket-poster"
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.claude/skills/dy-travel-ticket-poster
```

### Cursor

```bash
mkdir -p ~/.cursor/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.cursor/skills/dy-travel-ticket-poster
```

### Gemini CLI

```bash
mkdir -p ~/.gemini/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.gemini/skills/dy-travel-ticket-poster
```

### GitHub Copilot

```bash
mkdir -p ~/.copilot/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.copilot/skills/dy-travel-ticket-poster
```

### 其他兼容 Agent Skills 的 Agent

如果 Agent 支持通用的个人 Skills 目录，可以安装到 `~/.agents/skills`。Codex、Cursor、Gemini CLI 和 GitHub Copilot 等支持该共享目录的客户端，也可以通过这种方式共用一份安装。

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/cxcxy/dy-travel-ticket-poster.git ~/.agents/skills/dy-travel-ticket-poster
```

手动安装完成后，重新启动或刷新对应 Agent，让它重新扫描 Skills。安装本 Skill 只会提供工作流和版式规范；Agent 还需要具备可用的图片生成或图片编辑工具。Codex 可直接配合 `imagegen` Skill，其他 Agent 需要提供等效能力。

## 能做什么

- 保留原图中的人物身份、动物、产品、建筑、车辆和关键动作
- 在主体完整的前提下保留足够的环境信息
- 根据每张照片调整海报背景和信息联配色
- 优先采用用户给出的标题、地点和日期
- 地点无法可靠确认时，改用中性场景词
- 自动生成五位编号、八位装饰码和装饰性条形码
- 批量处理时每张照片独立出图，同时保持统一版式
- 将通过检查的成品归一化为 `1170 × 1560` PNG，并保留原始文件

## 视觉系统

整套海报使用固定、克制、可重复的布局。

- 画布比例为 `3:4`
- 票根水平居中，宽度约占画布的 `90.4%`
- 票根高度约占画布的 `27.2%`
- 照片区约占票根宽度的 `74.7%`
- 信息联约占票根宽度的 `25.3%`
- 圆角、竖向撕票线、半圆缺口、轻阴影和粗体窄字保持一致
- 配色随照片变化，信息层级和版式保持不变

完整的版式参数见 [references/style-spec.md](references/style-spec.md)。

## 使用方法

附上一张或多张本地 PNG、JPG 照片，然后让当前 Agent 使用这个 Skill。

```text
使用 $dy-travel-ticket-poster，把这些照片做成统一的 3:4 旅行票根海报。
```

也可以直接指定标题和日期。

```text
使用 $dy-travel-ticket-poster 处理这张照片，标题用 WATERFRONT，日期用 2026 - 08。
```

工作流会逐张检查照片，选择安全的裁切区域，整理票根信息，调用当前环境的 `imagegen` Skill 或等效图片工具完成栅格编辑，目视检查结果，再通过 [scripts/normalize_output.sh](scripts/normalize_output.sh) 输出标准尺寸成品。

## 信息生成规则

- 用户提供的标题、地点和日期拥有最高优先级
- 没有可靠地点信息时，使用 `COFFEE`、`KOALA`、`OLD TOWN`、`DESERT` 这类中性场景词
- 日期依次采用用户指定值、本地 `DateTimeOriginal`、本地文件日期、当前年月
- GPS 和私人元数据只在本地读取，不会写入图片生成请求
- 编号、装饰码和条形码只承担视觉作用，不保证能够扫描

## 环境要求

- 支持 `SKILL.md` 的 Agent Skills 环境
- 可用的图片生成或图片编辑工具；Codex 推荐使用 `imagegen` Skill
- 本地安装 ImageMagick，用于最终尺寸归一化
- 本地可以访问需要处理的原始照片

成品通过目视检查后，可以单独运行归一化脚本。

```bash
bash scripts/normalize_output.sh generated-image.png final-ticket.png
```

## 参考案例

下面展示本次提供的原始照片和对应票根成品。文档预览图已统一缩小并移除元数据，实际工作流输出仍为 `1170 × 1560` PNG。

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
    <td><img src="assets/cases/koala-ticket.jpg" width="360" alt="考拉合影票根海报"></td>
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
├── references/prompt-template.md
├── references/style-spec.md
└── scripts/normalize_output.sh
```

## 内容边界

画面无法证明具体城市时，Skill 不会猜测地点。制作过程中也不会新增人物、动物、商品、车辆、建筑、标识或其他带有身份信息的细节。确实需要扩展背景时，只处理没有语义的环境区域，并在交付说明中标出。
