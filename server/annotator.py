"""Draw detection boxes + a guidance banner onto a copy of the photo."""
from __future__ import annotations

from typing import List

from PIL import Image, ImageDraw, ImageFont

from server.perception import Detection

_BANNER_HEIGHT = 60


def annotate(src_path: str, dst_path: str, detections: List[Detection], banner_text: str) -> None:
    img = Image.open(src_path).convert("RGB")
    w, h = img.size

    canvas = Image.new("RGB", (w, h + _BANNER_HEIGHT), color=(20, 20, 20))
    canvas.paste(img, (0, 0))
    draw = ImageDraw.Draw(canvas)

    for d in detections:
        x1, y1, x2, y2 = d.box
        draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 0), width=3)
        draw.text((x1 + 4, max(0, y1 - 14)), f"{d.label} {d.score:.2f}", fill=(0, 255, 0))

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((10, h + 8), banner_text[:200], fill=(255, 255, 255), font=font)

    canvas.save(dst_path, "JPEG", quality=85)
