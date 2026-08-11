#!/usr/bin/env python3
"""Build a compact visual review sheet from elemental hatchling idle sprites."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS = ["fire", "water", "earth", "storm", "ice", "wind", "shadow", "light", "aether", "neutral"]
DIRECTIONS = ["down", "left", "right", "up"]
CELL = 64
SCALE = 2
PANEL_W = 300
PANEL_H = 330
COLS = 5
ROWS = 2


def font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def checker(size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", size, (28, 31, 38, 255))
    draw = ImageDraw.Draw(image)
    step = 16
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if (x // step + y // step) % 2:
                draw.rectangle((x, y, x + step - 1, y + step - 1), fill=(40, 44, 52, 255))
    return image


def first_direction_frames(path: Path) -> list[Image.Image]:
    source = Image.open(path).convert("RGBA")
    result = []
    for row in range(4):
        frame = source.crop((0, row * CELL, CELL, (row + 1) * CELL))
        result.append(frame.resize((CELL * SCALE, CELL * SCALE), Image.Resampling.LANCZOS))
    return result


def main() -> None:
    sheet = Image.new("RGBA", (COLS * PANEL_W, ROWS * PANEL_H), (13, 17, 24, 255))
    title_font = font(24)
    label_font = font(15)
    for index, element in enumerate(ELEMENTS):
        col, row = index % COLS, index // COLS
        ox, oy = col * PANEL_W, row * PANEL_H
        panel = checker((PANEL_W - 12, PANEL_H - 12))
        pd = ImageDraw.Draw(panel)
        idle = ROOT / "digital-dragons" / "dragons" / "elemental" / element / "hatchling_01" / "sprites_v2" / "idle.png"
        frames = first_direction_frames(idle)
        positions = [(12, 55), (148, 55), (12, 190), (148, 190)]
        for direction, frame, (x, y) in zip(DIRECTIONS, frames, positions):
            panel.alpha_composite(frame, (x, y))
            pd.text((x + 4, y + 106), direction.upper(), font=label_font, fill=(225, 229, 235, 255))
        pd.rectangle((0, 0, panel.width - 1, panel.height - 1), outline=(99, 108, 126, 255), width=2)
        pd.text((12, 12), element.upper(), font=title_font, fill=(248, 231, 178, 255))
        sheet.alpha_composite(panel, (ox + 6, oy + 6))
    output = ROOT / "hatchling-idle-review-sheet.png"
    sheet.save(output, optimize=True)
    print(output.relative_to(ROOT))


if __name__ == "__main__":
    main()
