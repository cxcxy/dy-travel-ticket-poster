# DY 旅行票根海报

[English](README.en.md) | 简体中文 | [在线预览 12 种风格](https://cxcxy.github.io/dy-travel-ticket-poster/)

把一张照片或一组照片，变成好看的旅行票根海报。你只需要上传图片，默认就能直接制作；只有想换一种感觉时，再选择其他风格。

## 参考案例

先看看它可以做出什么效果。左边是原图，右边是生成的票根。

| 案例 | 原图 | 票根效果 |
| --- | --- | --- |
| 咖啡吧台 | <img src="assets/cases/coffee-original.jpg" width="240" alt="咖啡吧台原图"> | <img src="assets/cases/coffee-ticket.jpg" width="240" alt="咖啡吧台票根"> |
| 考拉合影 | <img src="assets/cases/koala-original.jpg" width="240" alt="考拉合影原图"> | <img src="assets/cases/koala-ticket.png" width="240" alt="考拉合影票根"> |
| 历史建筑 | <img src="assets/cases/heritage-original.jpg" width="240" alt="历史建筑原图"> | <img src="assets/cases/heritage-ticket.jpg" width="240" alt="历史建筑票根"> |
| 露天剧场 | <img src="assets/cases/theater-original.jpg" width="240" alt="露天剧场原图"> | <img src="assets/cases/theater-ticket.jpg" width="240" alt="露天剧场票根"> |
| 精品店陈列 | <img src="assets/cases/boutique-original.jpg" width="240" alt="精品店原图"> | <img src="assets/cases/boutique-ticket.jpg" width="240" alt="精品店票根"> |
| 老城街道 | <img src="assets/cases/old-town-original.jpg" width="240" alt="老城街道原图"> | <img src="assets/cases/old-town-ticket.jpg" width="240" alt="老城街道票根"> |
| 咖啡与甜点 | <img src="assets/cases/cafe-original.jpg" width="240" alt="咖啡与甜点原图"> | <img src="assets/cases/cafe-ticket.jpg" width="240" alt="咖啡与甜点票根"> |
| 沙漠行车 | <img src="assets/cases/desert-original.jpg" width="240" alt="沙漠行车原图"> | <img src="assets/cases/desert-ticket.jpg" width="240" alt="沙漠行车票根"> |
| 水岸摄影 | <img src="assets/cases/waterfront-original.jpg" width="240" alt="水岸摄影原图"> | <img src="assets/cases/waterfront-ticket.jpg" width="240" alt="水岸摄影票根"> |
| 湖边远眺 | <img src="assets/cases/lakeside-original.jpg" width="240" alt="湖边远眺原图"> | <img src="assets/cases/lakeside-ticket.jpg" width="240" alt="湖边远眺票根"> |
| 黄色住宅 | <img src="assets/cases/gold-house-original.jpg" width="240" alt="黄色住宅原图"> | <img src="assets/cases/gold-house-ticket.jpg" width="240" alt="黄色住宅票根"> |

## 能做什么

- 把单张照片做成一张票根海报
- 把一组照片分别做成一组统一风格的票根
- 保留照片中的人物、动物、建筑、车辆和主要内容
- 自动安排标题、日期、编号和票根信息
- 默认根据照片的颜色搭配背景，也可以指定统一的颜色
- 图片会保持完整比例，不拉伸、不变形

## 小白使用方法

### 第一步：安装 Skill

最简单的安装说法是：

```text
请安装这个 Skill：https://github.com/cxcxy/dy-travel-ticket-poster
```

这个 Skill 不只给 Codex 用。它使用通用的 `SKILL.md` 格式，下面这些 Agent 都可以使用：

#### 可以直接识别 Skill 的工具

| 工具 | 怎么安装 | 安装后怎么调用 |
| --- | --- | --- |
| Codex | 在对话里发送本仓库链接，并说“请安装这个 Skill” | 直接说“把这张图片做成旅行票根” |
| Claude Code | 把仓库文件夹放到 `~/.claude/skills/dy-travel-ticket-poster/` | 输入 `/dy-travel-ticket-poster`，也可以直接描述需求 |
| Gemini CLI | 执行 `gemini skills install https://github.com/cxcxy/dy-travel-ticket-poster` | 输入 `/skills list` 检查，再描述需求 |
| Kimi Code | 把仓库文件夹放到 `~/.kimi-code/skills/dy-travel-ticket-poster/` | 输入 `/skill:dy-travel-ticket-poster`，再描述需求 |
| 腾讯云 CodeBuddy | 在项目的 `.codebuddy/skills/dy-travel-ticket-poster/` 中放入 `SKILL.md` | 新建任务后直接描述需求 |

#### 其他常见 Agent 工具

下面这些工具也可以使用这个 Skill，但通常需要把仓库里的 `SKILL.md` 复制到它们的“项目规则 / 自定义指令 / Skills”位置，再开始对话：

| 工具 | 类型 |
| --- | --- |
| Cursor | 海外常用编程 Agent |
| Windsurf | 海外常用编程 Agent |
| Cline、Roo Code | VS Code Agent 插件 |
| GitHub Copilot、Copilot CLI | GitHub Agent |
| Trae | 字节跳动 Agent |
| 通义灵码、MarsCode | 国产编程 Agent |
| CodeGeeX、GLM 编程工具 | 国产编程 Agent |
| 百度 Comate | 国产编程 Agent |
| Coze（扣子） | 国产 Agent 平台 |
| 豆包 | 国产 AI 助手 |

这些工具的菜单名称可能会随版本变化。如果没有“安装 Skill”按钮，就把 `SKILL.md` 内容复制到项目规则里，或者在对话中说：

```text
请读取这个仓库里的 SKILL.md，并按照里面的要求把这张图片做成旅行票根。
```

安装后如果工具没有马上识别，请关闭并重新打开当前任务。

### 第二步：准备图片

上传一张或多张清晰的 PNG、JPG 照片。照片里可以是旅行风景、人物、动物、建筑、咖啡店或任何你想做成票根的内容。

### 第三步：直接制作，想换再选风格

最简单的方式是不选择风格，直接说：

```text
按默认风格制作。
```

默认风格就是这个 Skill 的基础效果，会根据照片颜色搭配轻质感背景。

只有想换一种感觉时，才打开[12 种风格预览](https://cxcxy.github.io/dy-travel-ticket-poster/)，再告诉我序号或中文名。

例如：

```text
使用第10种风格。
```

也可以说：

```text
使用“象牙洞石斜光”。
```

### 第四步：一次处理多张图片

把多张图片一起发来，不指定风格就会全部使用默认风格：

```text
把这组图片分别做成票根。
```

想让它们使用其他风格时，再补充风格：

```text
把这组图片分别做成票根，全部使用第10种风格。
```

每张图片会得到一张单独的票根，不会拼成一张大图。

### 第五步：查看并修改

如果你想换一种感觉，直接继续说：

```text
背景换成第2种，其他保持不变。
```

如果想换标题或日期，也可以直接说：

```text
标题改成 WATERFRONT，日期改成 2026 - 08。
```

## 想换感觉时，再从 12 种风格里选

| 序号 | 中文名 | 大致感觉 |
| --- | --- | --- |
| 01 | 暖灰亚麻侧光 | 温暖、柔和、像布料墙面 |
| 02 | 象牙艺术纸柔窗影 | 明亮、干净、像艺术纸 |
| 03 | 沙岩中心柔光 | 自然、温暖、中心更亮 |
| 04 | 蘑菇灰电影墙 | 低调、成熟、电影感 |
| 05 | 焦糖树影墙 | 温暖、有阳光和树影 |
| 06 | 天然和纸柔光 | 轻盈、安静、纸张质感 |
| 07 | 暖灰灰泥柔影 | 柔和、有墙面层次 |
| 08 | 象牙灰泥窗光 | 明亮、有建筑窗光 |
| 09 | 奶油石灰墙漫射 | 奶油色、柔和、自然 |
| 10 | 象牙洞石斜光 | 明亮、高级、有斜向光线 |
| 11 | 棉纸顶光 | 干净、均匀、像棉纸 |
| 12 | 焦糖矿物聚光 | 深暖色、聚焦、氛围感强 |

## 默认怎么处理

- 不指定风格时，会根据每张照片的主要颜色安排背景。
- 默认背景是接近纯色的轻微质感，不会突然出现复杂图案。
- 一组图片默认每张单独配色，让每张票根都更贴合自己的照片。
- 想让一组图片使用同一种颜色时，直接说“统一为灰蓝色系”或你喜欢的颜色。
- 如果你没有提供标题、地点或日期，Skill 会使用简单、中性的文字，不会随意猜测城市。

## 你可以直接复制的说法

```text
使用 $dy-travel-ticket-poster，把这张图做成票根。
```

```text
使用 $dy-travel-ticket-poster，把这张图做成票根，使用第5种风格。
```

```text
使用 $dy-travel-ticket-poster，把这组图片分别做成票根，统一使用第10种，并统一为灰蓝色系。
```

```text
使用 $dy-travel-ticket-poster，先给我推荐 3 种适合这张照片的风格，我选好后再制作。
```

## 不知道怎么说时

你不需要记住任何专业名称。直接告诉我这三件事就够了：

1. 上传哪一张或哪一组照片
2. 如果想换风格，再告诉我序号或中文名；不说就是默认风格
3. 是否需要指定标题、日期或统一颜色

例如：

```text
这是我的旅行照片，请用第8种风格做成票根，标题写 OLD TOWN，日期写 2026 - 08。
```

## 2026-08-15 更新

- 新增 12 种可以直接选择的背景风格。
- 默认背景改为根据照片颜色生成的轻质感纯色。
- 支持单张图片和多张图片批量制作。
- 新增在线风格预览页，可以先看效果再选择。
