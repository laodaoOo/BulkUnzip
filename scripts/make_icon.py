"""生成 BulkUnzip 的应用图标（PNG + 多尺寸 ICO）。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SIZE = 1024

BACKGROUND_TOP = (74, 58, 102)
BACKGROUND_BOTTOM = (43, 36, 56)
BOX_FILL = (245, 241, 250)
BOX_EDGE = (43, 36, 56)
BOX_LID = (211, 194, 232)
BAR = (107, 78, 155)
BADGE = (94, 168, 92)


def _gradient(size: int) -> Image.Image:
    """竖直渐变的方形底图。"""
    canvas = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(canvas)
    for y in range(size):
        ratio = y / max(size - 1, 1)
        color = tuple(
            round(BACKGROUND_TOP[index] * (1 - ratio) + BACKGROUND_BOTTOM[index] * ratio)
            for index in range(3)
        )
        draw.line([(0, y), (size, y)], fill=color)
    return canvas


def _rounded_mask(size: int, radius: int) -> Image.Image:
    """圆角矩形遮罩，用于裁出应用图标的底。"""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def draw_icon(size: int = SIZE) -> Image.Image:
    """画一张图标：两个叠放的归档盒 + 解压箭头徽标。"""
    base = _gradient(size).convert("RGBA")
    base.putalpha(_rounded_mask(size, round(size * 0.22)))
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def scale(value: float) -> int:
        return round(value * size / 1024)

    edge = max(scale(10), 2)
    radius = scale(42)

    # 后面的盒子，制造“批量”的叠放感。
    back = [scale(345), scale(240), scale(810), scale(770)]
    draw.rounded_rectangle(
        back, radius=radius, fill=(196, 180, 222, 255), outline=BOX_EDGE, width=edge,
    )
    draw.rounded_rectangle(
        [scale(345), scale(240), scale(810), scale(382)],
        radius=radius, fill=BOX_LID, outline=BOX_EDGE, width=edge,
    )

    # 前面的盒子。
    front = [scale(200), scale(380), scale(690), scale(840)]
    draw.rounded_rectangle(front, radius=radius, fill=BOX_FILL, outline=BOX_EDGE, width=edge)
    draw.rounded_rectangle(
        [scale(200), scale(380), scale(690), scale(520)],
        radius=radius, fill=BOX_LID, outline=BOX_EDGE, width=edge,
    )
    # 盒盖与盒身的接缝、盒盖中缝。
    draw.line(
        [(scale(212), scale(520)), (scale(678), scale(520))],
        fill=BOX_EDGE, width=max(scale(6), 2),
    )
    draw.line(
        [(scale(445), scale(392)), (scale(445), scale(508))],
        fill=BOX_EDGE, width=max(scale(5), 2),
    )

    # 盒身里的三条“压缩包”。
    for offset, width_ratio in ((578, 0.72), (660, 0.72), (742, 0.52)):
        draw.rounded_rectangle(
            [scale(268), scale(offset), scale(268 + 360 * width_ratio), scale(offset + 46)],
            radius=scale(23), fill=BAR,
        )

    # 右下角的解压箭头徽标。
    cx, cy, r = scale(790), scale(790), scale(150)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BADGE, outline=BOX_EDGE, width=edge)
    arrow = [
        (cx, cy + scale(62)),
        (cx - scale(70), cy - scale(10)),
        (cx - scale(26), cy - scale(10)),
        (cx - scale(26), cy - scale(68)),
        (cx + scale(26), cy - scale(68)),
        (cx + scale(26), cy - scale(10)),
        (cx + scale(70), cy - scale(10)),
    ]
    draw.polygon(arrow, fill=(255, 255, 255))

    return Image.alpha_composite(base, layer)


def main() -> None:
    """导出 PNG 与 ICO。"""
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()
    icon.resize((512, 512), Image.LANCZOS).save(ASSETS / "app.png")
    icon.save(
        ASSETS / "app.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"wrote {ASSETS / 'app.png'} and {ASSETS / 'app.ico'}")


if __name__ == "__main__":
    main()
