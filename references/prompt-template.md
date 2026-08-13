# 例外图片编辑提示词

标准旅行票根不得依赖图片模型生成几何、文字、条码或背景色；这些层统一由 `render_ticket_poster.py` 确定性完成。只有最终 `774 × 507` 裁切必然切掉关键主体，且无法用 `photo-center-y` 解决时，才读取并使用本文件扩展无语义环境。

## 使用边界

- 图片模型只输出一张扩展后的自然照片，不生成票根、背景画布、信息联、标题、日期、编号、条码、虚线、缺口或阴影。
- 原图是唯一语义来源。不得改变人物身份、五官、发型、眼镜、服装、姿势、手部、动物、车辆、产品、建筑、招牌、Logo、文字、数量、光线方向或关键动作。
- 只在原图边缘补充可重复、无身份含义的天空、水面、墙面、地面、植被虚化或其他环境连续区域。
- 不允许新增人物、动物、商品、车辆、建筑细节、门窗、文字、标识、道路设施或可识别物体。
- 输出仍是中间照片；最终必须重新经过取色、确定性渲染和完整验证。

## 无语义环境扩展模板

把方括号内容替换为当前照片的真实信息：

```text
Use case: constrained outpainting of non-semantic scenery only.
Image 1 is the only source image and the only semantic authority.

Goal:
Create enough natural horizontal breathing room for a later 774 x 507 crop (about 1.53:1). Extend only the outer environment where the source currently lacks room.

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

## 冲突优先级

当任何指令发生冲突时，按以下顺序处理：

1. 原图人物和语义内容不变。
2. 不新增可识别内容。
3. 边缘连续、透视和光线匹配。
4. 为横向裁切提供足够空间。

“看起来更漂亮”不得凌驾于前两项。若扩展会改变主体，放弃扩展并向用户说明裁切限制。

## 定向修正

只允许一次针对单一边缘连续性问题的修正：

```text
Image 1 is the edit target. Change only [name the exact non-semantic edge continuity problem]. Keep every original pixel containing a person, animal, product, vehicle, building, sign, logo, text or meaningful object unchanged. Do not add or remove anything else.
```

若一次修正后仍改变主体或出现新物体，丢弃该分支，不得继续 edit-on-edit。回到原图调整裁切，或向用户说明无法在不造假的前提下同时保留全部内容。

## 扩展后的验收

- 同时用 `view_image` 对比原图和扩展图，逐项核对锁定主体、数量、动作、招牌和文字。
- 明确记录哪些边缘是生成区域；交付时说明发生了无语义环境扩展。
- 使用扩展图作为 `render_ticket_poster.py --photo-source` 和验证器的像素源，同时保留原图路径作为审计依据。
- 只要主体、建筑、商品或文字发生改变，就不得把扩展图作为最终照片源。
