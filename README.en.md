# DY Travel Ticket Poster

English | [简体中文](README.md) | [Live 12-style preview](https://cxcxy.github.io/dy-travel-ticket-poster/)

Turn one photo or a group of photos into travel-ticket posters. Upload your images, tell the Skill which style you want, and it will handle the layout for you.

## Reference cases

Here are a few examples. The left column is the original photo and the right column is the ticket poster.

| Case | Original | Ticket poster |
| --- | --- | --- |
| Coffee counter | <img src="assets/cases/coffee-original.jpg" width="240" alt="Original coffee counter photo"> | <img src="assets/cases/coffee-ticket.jpg" width="240" alt="Coffee counter ticket poster"> |
| Koala encounter | <img src="assets/cases/koala-original.jpg" width="240" alt="Original koala portrait"> | <img src="assets/cases/koala-ticket.png" width="240" alt="Koala ticket poster"> |
| Heritage architecture | <img src="assets/cases/heritage-original.jpg" width="240" alt="Original heritage architecture photo"> | <img src="assets/cases/heritage-ticket.jpg" width="240" alt="Heritage architecture ticket poster"> |
| Open-air theater | <img src="assets/cases/theater-original.jpg" width="240" alt="Original open-air theater photo"> | <img src="assets/cases/theater-ticket.jpg" width="240" alt="Open-air theater ticket poster"> |
| Boutique interior | <img src="assets/cases/boutique-original.jpg" width="240" alt="Original boutique photo"> | <img src="assets/cases/boutique-ticket.jpg" width="240" alt="Boutique ticket poster"> |
| Old town street | <img src="assets/cases/old-town-original.jpg" width="240" alt="Original old town street photo"> | <img src="assets/cases/old-town-ticket.jpg" width="240" alt="Old town street ticket poster"> |
| Café table | <img src="assets/cases/cafe-original.jpg" width="240" alt="Original café table photo"> | <img src="assets/cases/cafe-ticket.jpg" width="240" alt="Café table ticket poster"> |
| Desert drive | <img src="assets/cases/desert-original.jpg" width="240" alt="Original desert drive photo"> | <img src="assets/cases/desert-ticket.jpg" width="240" alt="Desert drive ticket poster"> |
| Waterfront photographer | <img src="assets/cases/waterfront-original.jpg" width="240" alt="Original waterfront photo"> | <img src="assets/cases/waterfront-ticket.jpg" width="240" alt="Waterfront ticket poster"> |
| Lakeside view | <img src="assets/cases/lakeside-original.jpg" width="240" alt="Original lakeside photo"> | <img src="assets/cases/lakeside-ticket.jpg" width="240" alt="Lakeside ticket poster"> |
| Gold house | <img src="assets/cases/gold-house-original.jpg" width="240" alt="Original yellow house photo"> | <img src="assets/cases/gold-house-ticket.jpg" width="240" alt="Gold house ticket poster"> |

## What it can do

- Turn one photo into one ticket poster
- Turn a group of photos into a matching set
- Keep the important people, animals, buildings, vehicles, and objects in your photos
- Add a title, date, number, and ticket information
- Choose a background that matches the photo, or request one shared color
- Keep the original image proportion without stretching or distortion

## How to use it

### 1. Prepare your photos

Upload one or more clear PNG or JPG photos. Travel scenes, people, animals, buildings, cafés, and everyday moments all work well.

### 2. Call the Skill

In Codex, type:

```text
Use $dy-travel-ticket-poster to turn this image into a travel ticket poster.
```

If Codex already shows `dy-travel-ticket-poster`, you do not need to install it again. If it is not visible, install the Skill first and start a new task.

The simplest way to install it is to send this repository link to Codex:

```text
Please install this Skill: https://github.com/cxcxy/dy-travel-ticket-poster
```

### 3. Choose a style

Open the [12-style preview](https://cxcxy.github.io/dy-travel-ticket-poster/). Then tell the Skill the number or the Chinese name you like.

For example:

```text
Use style 10.
```

Or:

```text
Use “象牙洞石斜光”.
```

You can also say:

```text
Use the default style.
```

### 4. Process several photos

Send several images together and say:

```text
Turn this group of photos into separate ticket posters, all using style 10.
```

Each photo becomes its own poster. They will not be merged into a collage.

### 5. Ask for changes

You can keep refining the result in plain language:

```text
Change the background to style 2 and keep everything else the same.
```

```text
Change the title to WATERFRONT and the date to 2026 - 08.
```

## The 12 styles

| No. | Chinese name | Overall feeling |
| --- | --- | --- |
| 01 | 暖灰亚麻侧光 | Warm, soft, textile-like |
| 02 | 象牙艺术纸柔窗影 | Bright, clean, art-paper feel |
| 03 | 沙岩中心柔光 | Natural, warm, brighter in the center |
| 04 | 蘑菇灰电影墙 | Quiet, mature, cinematic |
| 05 | 焦糖树影墙 | Warm, sunny, leafy shadows |
| 06 | 天然和纸柔光 | Light, calm, handmade paper |
| 07 | 暖灰灰泥柔影 | Soft, with subtle wall depth |
| 08 | 象牙灰泥窗光 | Bright, with architectural window light |
| 09 | 奶油石灰墙漫射 | Creamy, soft, natural |
| 10 | 象牙洞石斜光 | Bright, premium, diagonal light |
| 11 | 棉纸顶光 | Clean, even, cotton-paper feel |
| 12 | 焦糖矿物聚光 | Deep warm tone, focused atmosphere |

## What happens by default

- Without a style request, the background follows the main colors in each photo.
- The default background is close to a solid color with a very light texture.
- In a batch, each photo gets its own matching color by default.
- To use one color family for all photos, say “use one shared blue-gray color family”.
- If you do not provide a title, place, or date, the Skill uses simple neutral wording instead of guessing.

## Ready-to-copy examples

```text
Use $dy-travel-ticket-poster to turn this image into a ticket poster with style 5.
```

```text
Use $dy-travel-ticket-poster to turn this group of photos into separate posters, all using style 10 and one shared blue-gray color family.
```

```text
Use $dy-travel-ticket-poster and recommend 3 styles that fit this photo before making the poster.
```

## If you are not sure what to say

You only need to provide:

1. The photo or photos
2. A style number, a style name, or “default”
3. Any title, date, or shared color you want

For example:

```text
Use this travel photo with style 8. Set the title to OLD TOWN and the date to 2026 - 08.
```

## 2026-08-15 update

- Added 12 selectable background styles.
- The default background now follows the colors in the photo.
- Added support for single-photo and batch creation.
- Added an online preview page so you can compare styles before choosing one.
