#!/usr/bin/env python3
"""Shared geometry for the deterministic ticket-poster layouts."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw


LANDSCAPE = "landscape"
PORTRAIT = "portrait"
LAYOUT_IDS = (LANDSCAPE, PORTRAIT)


@dataclass(frozen=True)
class TicketLayout:
    id: str
    ticket_box: tuple[int, int, int, int]
    photo_box: tuple[int, int, int, int]
    divider_axis: str
    divider_position: int

    @property
    def ticket_x(self) -> int:
        return self.ticket_box[0]

    @property
    def ticket_y(self) -> int:
        return self.ticket_box[1]

    @property
    def ticket_w(self) -> int:
        return self.ticket_box[2]

    @property
    def ticket_h(self) -> int:
        return self.ticket_box[3]

    @property
    def photo_x(self) -> int:
        return self.photo_box[0]

    @property
    def photo_y(self) -> int:
        return self.photo_box[1]

    @property
    def photo_w(self) -> int:
        return self.photo_box[2]

    @property
    def photo_h(self) -> int:
        return self.photo_box[3]


LAYOUTS = {
    LANDSCAPE: TicketLayout(
        id=LANDSCAPE,
        ticket_box=(55, 501, 1057, 507),
        photo_box=(0, 0, 774, 507),
        divider_axis="vertical",
        divider_position=774,
    ),
    PORTRAIT: TicketLayout(
        id=PORTRAIT,
        ticket_box=(305, 190, 560, 1180),
        photo_box=(44, 80, 472, 748),
        divider_axis="horizontal",
        divider_position=884,
    ),
}


def get_layout(layout_id: str) -> TicketLayout:
    try:
        return LAYOUTS[layout_id]
    except KeyError as error:
        raise ValueError(
            f"unknown ticket layout {layout_id!r}; choose from {', '.join(LAYOUT_IDS)}"
        ) from error


def make_portrait_ticket_mask(layout: TicketLayout | None = None) -> Image.Image:
    """Build the scalloped portrait keepsake silhouette from the reference."""
    layout = layout or get_layout(PORTRAIT)
    mask = Image.new("L", (layout.ticket_w, layout.ticket_h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        (0, 0, layout.ticket_w - 1, layout.ticket_h - 1),
        radius=34,
        fill=255,
    )

    # Small repeated edge bites echo a printed admission ticket. The larger
    # centered bites and the two divider notches establish the hierarchy seen
    # in the supplied portrait reference without copying its background.
    small_radius = 9
    excluded_center = 54
    for x_pos in range(52, layout.ticket_w - 51, 44):
        if abs(x_pos - layout.ticket_w // 2) < excluded_center:
            continue
        draw.ellipse(
            (x_pos - small_radius, -small_radius, x_pos + small_radius, small_radius),
            fill=0,
        )
        draw.ellipse(
            (
                x_pos - small_radius,
                layout.ticket_h - small_radius,
                x_pos + small_radius,
                layout.ticket_h + small_radius,
            ),
            fill=0,
        )

    center_radius = 31
    center_x = layout.ticket_w // 2
    draw.ellipse(
        (center_x - center_radius, -center_radius, center_x + center_radius, center_radius),
        fill=0,
    )
    draw.ellipse(
        (
            center_x - center_radius,
            layout.ticket_h - center_radius,
            center_x + center_radius,
            layout.ticket_h + center_radius,
        ),
        fill=0,
    )

    side_radius = 18
    divider_y = layout.divider_position
    draw.ellipse(
        (-side_radius, divider_y - side_radius, side_radius, divider_y + side_radius),
        fill=0,
    )
    draw.ellipse(
        (
            layout.ticket_w - side_radius,
            divider_y - side_radius,
            layout.ticket_w + side_radius,
            divider_y + side_radius,
        ),
        fill=0,
    )
    return mask


def draw_portrait_perforation(
    ticket: Image.Image,
    color: tuple[int, int, int],
    layout: TicketLayout | None = None,
) -> None:
    """Draw the portrait layout's one square-ended horizontal tear line."""
    layout = layout or get_layout(PORTRAIT)
    draw = ImageDraw.Draw(ticket)
    line_h = 4
    dash_w = 22
    gap = 14
    y1 = layout.divider_position - line_h // 2
    y2 = y1 + line_h - 1
    for dash_x in range(0, layout.ticket_w, dash_w + gap):
        draw.rectangle(
            (dash_x, y1, min(dash_x + dash_w - 1, layout.ticket_w - 1), y2),
            fill=color,
        )


def portrait_photo_mask(layout: TicketLayout | None = None) -> Image.Image:
    layout = layout or get_layout(PORTRAIT)
    mask = Image.new("L", (layout.photo_w, layout.photo_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, layout.photo_w - 1, layout.photo_h - 1),
        radius=31,
        fill=255,
    )
    return mask
