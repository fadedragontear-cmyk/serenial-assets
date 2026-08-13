#!/usr/bin/env python3
"""Render four-direction animated QA previews from character source frames."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

try:
    from .character_sprite_pipeline import DIRECTIONS, FRAME_SIZE, load_spec
except ImportError:  # Direct `python tools/render_character_previews.py` execution.
    from character_sprite_pipeline import DIRECTIONS, FRAME_SIZE, load_spec


PREVIEW_SCALE = 2
BACKGROUND = (20, 15, 17, 255)
GRID = (55, 42, 43, 255)
QUADRANTS = {
    "down": (0, 0),
    "left": (FRAME_SIZE[0], 0),
    "right": (0, FRAME_SIZE[1]),
    "up": FRAME_SIZE,
}


def render(spec_path: Path, output_directory: Path) -> None:
    spec = load_spec(spec_path)
    output_directory.mkdir(parents=True, exist_ok=True)
    for animation in spec.animations:
        frames: list[Image.Image] = []
        for index in range(animation.frames):
            canvas = Image.new("RGBA", (FRAME_SIZE[0] * 2, FRAME_SIZE[1] * 2), BACKGROUND)
            for direction in DIRECTIONS:
                path = spec.directory / "frames" / animation.name / direction / f"{index:03d}.png"
                with Image.open(path) as opened:
                    canvas.alpha_composite(opened.convert("RGBA"), QUADRANTS[direction])
            draw = ImageDraw.Draw(canvas)
            draw.line((FRAME_SIZE[0], 0, FRAME_SIZE[0], canvas.height), fill=GRID)
            draw.line((0, FRAME_SIZE[1], canvas.width, FRAME_SIZE[1]), fill=GRID)
            frames.append(
                canvas.resize(
                    (canvas.width * PREVIEW_SCALE, canvas.height * PREVIEW_SCALE),
                    Image.Resampling.NEAREST,
                ).convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
            )
        output = output_directory / f"{animation.name}-all-directions-v1.gif"
        frames[0].save(
            output,
            save_all=True,
            append_images=frames[1:],
            duration=round(1000 / animation.fps),
            loop=0,
            disposal=2,
            optimize=False,
        )
        print(f"rendered {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    render(args.spec, args.output_directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
