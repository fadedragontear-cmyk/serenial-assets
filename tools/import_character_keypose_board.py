#!/usr/bin/env python3
"""Import a reviewed key-pose board into editable Serenial sprite frames.

This tool is intentionally separate from the production atlas packer. Generated
boards are reference material; the 96x96 PNGs written here become artist-owned
source frames and must still pass the normal character sprite pipeline.
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image


FRAME_SIZE = 96
ANCHOR_X = 48
ANCHOR_Y = 84
TARGET_VISIBLE_HEIGHT = 70
MAX_VISIBLE_WIDTH = 84


def _background_candidate(pixel: tuple[int, int, int], mode: str) -> bool:
    red, green, blue = pixel
    if mode == "magenta":
        return red >= 190 and blue >= 150 and green <= 135 and min(red, blue) - green >= 70
    # Generated checkerboards are almost neutral whites. A lower threshold also
    # catches their antialiased fringe, but connectivity protects enclosed ivory
    # clothing pixels from being removed.
    return min(red, green, blue) >= 170 and max(red, green, blue) - min(red, green, blue) <= 30


def remove_connected_background(image: Image.Image, mode: str) -> Image.Image:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    seen = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def add(x: int, y: int) -> None:
        index = y * width + x
        if seen[index] or not _background_candidate(pixels[x, y], mode):
            return
        seen[index] = 1
        queue.append((x, y))

    for x in range(width):
        add(x, 0)
        add(x, height - 1)
    for y in range(height):
        add(0, y)
        add(width - 1, y)

    while queue:
        x, y = queue.popleft()
        if x:
            add(x - 1, y)
        if x + 1 < width:
            add(x + 1, y)
        if y:
            add(x, y - 1)
        if y + 1 < height:
            add(x, y + 1)

    output = rgb.convert("RGBA")
    alpha = Image.new("L", (width, height), 255)
    alpha.frombytes(bytes(0 if value else 255 for value in seen))
    output.putalpha(alpha)
    return output


def keep_largest_visible_component(image: Image.Image) -> Image.Image:
    """Remove disconnected pixels inherited from a neighboring board cell."""
    alpha = image.getchannel("A")
    width, height = alpha.size
    pixels = alpha.load()
    visited = bytearray(width * height)
    largest: list[tuple[int, int]] = []

    for y in range(height):
        for x in range(width):
            offset = y * width + x
            if visited[offset] or not pixels[x, y]:
                continue
            visited[offset] = 1
            queue = [(x, y)]
            component: list[tuple[int, int]] = []
            while queue:
                current_x, current_y = queue.pop()
                component.append((current_x, current_y))
                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (0 <= next_x < width and 0 <= next_y < height):
                        continue
                    next_offset = next_y * width + next_x
                    if visited[next_offset] or not pixels[next_x, next_y]:
                        continue
                    visited[next_offset] = 1
                    queue.append((next_x, next_y))
            if len(component) > len(largest):
                largest = component

    if not largest:
        return image
    cleaned_alpha = Image.new("L", (width, height), 0)
    cleaned_pixels = cleaned_alpha.load()
    for x, y in largest:
        cleaned_pixels[x, y] = 255
    output = image.copy()
    output.putalpha(cleaned_alpha)
    return output


def _cell_box(width: int, height: int, columns: int, rows: int, index: int) -> tuple[int, int, int, int]:
    column = index % columns
    row = index // columns
    return (
        round(column * width / columns),
        round(row * height / rows),
        round((column + 1) * width / columns),
        round((row + 1) * height / rows),
    )


def _quantize_rgba(image: Image.Image, colors: int = 64) -> Image.Image:
    alpha = image.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
    rgb = image.convert("RGB").quantize(
        colors=colors,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    ).convert("RGBA")
    rgb.putalpha(alpha)
    return rgb


def normalize_board(
    board: Image.Image,
    *,
    columns: int,
    rows: int,
    background: str,
    silhouette_center_x: int = ANCHOR_X,
) -> list[Image.Image]:
    cells: list[Image.Image] = []
    bounds: list[tuple[int, int, int, int]] = []
    for index in range(columns * rows):
        cell = board.crop(_cell_box(board.width, board.height, columns, rows, index))
        cell = keep_largest_visible_component(remove_connected_background(cell, background))
        bound = cell.getchannel("A").getbbox()
        if bound is None:
            raise ValueError(f"cell {index} has no visible sprite after background removal")
        cells.append(cell)
        bounds.append(bound)

    widest = max(right - left for left, _top, right, _bottom in bounds)
    tallest = max(bottom - top for _left, top, _right, bottom in bounds)
    scale = min(TARGET_VISIBLE_HEIGHT / tallest, MAX_VISIBLE_WIDTH / widest)

    row_ground: list[int] = []
    for row in range(rows):
        row_bounds = bounds[row * columns : (row + 1) * columns]
        row_ground.append(max(bound[3] for bound in row_bounds))

    normalized: list[Image.Image] = []
    for index, (cell, bound) in enumerate(zip(cells, bounds, strict=True)):
        left, top, right, bottom = bound
        sprite = cell.crop(bound)
        target_width = max(1, round(sprite.width * scale))
        target_height = max(1, round(sprite.height * scale))
        sprite = sprite.resize((target_width, target_height), Image.Resampling.LANCZOS)
        sprite = _quantize_rgba(sprite)

        # Generated cells often place the same pose at slightly different x
        # positions. Preserving that board offset causes visible atlas jitter.
        # Register the resized silhouette to an explicit frame-space center.
        destination_x = round(silhouette_center_x - (target_width - 1) / 2)
        ground_offset = round((bottom - row_ground[index // columns]) * scale)
        destination_bottom = ANCHOR_Y + 1 + ground_offset
        destination_y = destination_bottom - target_height

        frame = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE))
        frame.alpha_composite(sprite, (destination_x, destination_y))
        normalized.append(frame)
    return normalized


def write_frames(
    frames: list[Image.Image],
    output: Path,
    *,
    mirror_output: Path | None = None,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    if list(output.glob("*.png")):
        raise ValueError(f"refusing to overwrite existing PNG frames in {output}")
    if mirror_output is not None:
        mirror_output.mkdir(parents=True, exist_ok=True)
        if list(mirror_output.glob("*.png")):
            raise ValueError(f"refusing to overwrite existing PNG frames in {mirror_output}")

    for index, frame in enumerate(frames):
        frame.save(output / f"{index:03d}.png", format="PNG", compress_level=9)
        if mirror_output is not None:
            mirrored = frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            mirrored.save(mirror_output / f"{index:03d}.png", format="PNG", compress_level=9)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--columns", type=int, required=True)
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--background", choices=("checker", "magenta"), default="checker")
    parser.add_argument(
        "--silhouette-center-x",
        type=int,
        default=ANCHOR_X,
        help="frame-space center for visible bounds (Celdra side views use 60 left / 36 right)",
    )
    parser.add_argument("--mirror-output", type=Path)
    args = parser.parse_args()
    if args.columns < 1 or args.rows < 1:
        parser.error("columns and rows must be positive")

    with Image.open(args.board) as opened:
        board = opened.convert("RGBA")
    frames = normalize_board(
        board,
        columns=args.columns,
        rows=args.rows,
        background=args.background,
        silhouette_center_x=args.silhouette_center_x,
    )
    write_frames(frames, args.output, mirror_output=args.mirror_output)
    print(f"imported {len(frames)} frame(s) into {args.output}")
    if args.mirror_output:
        print(f"wrote reviewed mirrored direction into {args.mirror_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
