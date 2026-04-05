from __future__ import annotations

import os
import textwrap
from typing import Any, Mapping

from PIL import Image, ImageDraw, ImageFont

_FONT_DIR = os.path.join("inputs", "font", "Be_Vietnam_Pro")

# Slide highlight (vd 1920×3440): khối bullet trong khung trắng
HIGHLIGHT_BULLET_START_RATIO = 0.5
# Lề ngang cho khối chữ căn trái (tỉ lệ theo chiều rộng ảnh)
HIGHLIGHT_TEXT_MARGIN_RATIO = 0.15
_DESIGN_WIDTH = 1920
_HIGHLIGHT_FONT_PT = 62
_GAP_BETWEEN_BULLETS_PT = 48
# Vị trí dọc dòng đầu ("HỌC SINH"): nhân với chiều cao ảnh (0 = mép trên, 1 = mép dưới).
# Giảm giá trị → đẩy cả khối chữ lên cao; tăng → đẩy xuống thấp.
TEXT_BLOCK_START_RATIO = 0.6


def load_image(image_path):
    return Image.open(image_path)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    """Trả về (width, height) của khung chữ."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered(
    draw: ImageDraw.ImageDraw,
    image_width: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> int:
    """
    Vẽ một dòng căn giữa ngang; trả về y tiếp theo (dưới dòng vừa vẽ).
    """
    w, h = _text_size(draw, text, font)
    x = (image_width - w) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return y + h


def _draw_left(
    draw: ImageDraw.ImageDraw,
    x_left: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> int:
    """Vẽ một dòng căn trái tại ``x_left``; trả về y tiếp theo."""
    _, h = _text_size(draw, text, font)
    draw.text((x_left, y), text, font=font, fill=fill)
    return y + h


def add_information_to_intro_image(image, name, class_name, teacher, tutor, save_path):
    parts = name.split()
    name = " ".join(word.capitalize() for word in parts)
    draw = ImageDraw.Draw(image)
    w = image.width
    # Màu nâu đậm (khớp thẻ mẫu), nền sáng
    fill_main = "#3d2f24"
    fill_muted = "#4a3d32"

    font_header = ImageFont.truetype(
        os.path.join(_FONT_DIR, "BeVietnamPro-Medium.ttf"), 40
    )
    font_name = ImageFont.truetype(
        os.path.join(_FONT_DIR, "BeVietnamPro-SemiBold.ttf"), 80
    )
    font_body = ImageFont.truetype(
        os.path.join(_FONT_DIR, "BeVietnamPro-Regular.ttf"), 40
    )

    gap_small = 20
    gap_medium = 40

    lop = f"Lớp: {class_name}"
    gvcn = f"GVCN: {teacher}"
    gia_su = f"Gia sư: {tutor}"

    y = int(image.height * TEXT_BLOCK_START_RATIO)

    y = _draw_centered(draw, w, y, "HỌC SINH", font_header, fill_muted)
    y += gap_small

    y = _draw_centered(draw, w, y, name, font_name, fill_main)
    y += gap_medium

    y = _draw_centered(draw, w, y, lop, font_body, fill_main)
    y += gap_small

    y = _draw_centered(draw, w, y, gvcn, font_body, fill_main)
    y += gap_small

    # _draw_centered(draw, w, y, gia_su, font_body, fill_main)

    image.save(save_path)
    return image


def add_highlight_bullets_to_image(
    image: Image.Image,
    highlight_row: Mapping[str, Any] | None,
    save_path: str,
) -> Image.Image:
    """
    Vẽ 3 bullet từ ``highlight_1_title`` … ``highlight_3_title``, căn trái trong lề.

    ``highlight_row`` là một dict (một phần tử của mảng JSON từ ``convert_d2t``).
    """
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    draw = ImageDraw.Draw(image)
    iw, ih = image.width, image.height
    scale = iw / _DESIGN_WIDTH
    font_size = max(40, round(_HIGHLIGHT_FONT_PT * scale))
    gap_between_bullets = max(22, round(_GAP_BETWEEN_BULLETS_PT * scale))
    line_gap = max(10, round(14 * scale))

    margin_x = max(40, int(iw * HIGHLIGHT_TEXT_MARGIN_RATIO))
    content_w_px = iw - 2 * margin_x

    font = ImageFont.truetype(
        os.path.join(_FONT_DIR, "BeVietnamPro-SemiBold.ttf"), font_size
    )
    fill = "#3d2f24"

    max_chars = max(18, int(content_w_px / (font_size * 0.55)))

    keys = ("highlight_1_title", "highlight_2_title", "highlight_3_title")
    y = int(ih * HIGHLIGHT_BULLET_START_RATIO)

    for bi, key in enumerate(keys):
        raw = ""
        if highlight_row:
            val = highlight_row.get(key)
            if val is not None:
                raw = str(val).strip()
        if not raw:
            raw = "—"

        wrapped = textwrap.wrap(raw, width=max_chars) or ["—"]
        for li, line in enumerate(wrapped):
            text_line = f"• {line}" if li == 0 else f"  {line}"
            y = _draw_left(draw, margin_x, y, text_line, font, fill)
            if li < len(wrapped) - 1:
                y += line_gap

        if bi < len(keys) - 1:
            y += gap_between_bullets

    image.save(save_path)
    return image
