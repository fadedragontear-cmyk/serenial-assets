#!/usr/bin/env python3
"""Register existing character frames to the centers declared in character.json."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

try:
    from .character_sprite_pipeline import (
        DIRECTIONS,
        FRAME_SIZE,
        SAFE_BOUNDS,
        SpriteValidationError,
        load_spec,
    )
except ImportError:  # Direct `python tools/register_character_frames.py` execution.
    from character_sprite_pipeline import (
        DIRECTIONS,
        FRAME_SIZE,
        SAFE_BOUNDS,
        SpriteValidationError,
        load_spec,
    )


def register_frame(image: Image.Image, target_center_x: float) -> tuple[Image.Image, int]:
    if image.mode != "RGBA" or image.size != FRAME_SIZE:
        raise SpriteValidationError(
            f"registration requires a {FRAME_SIZE[0]}x{FRAME_SIZE[1]} RGBA source frame"
        )
    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        raise SpriteValidationError("cannot register a fully transparent character frame")
    left, _top, right, _bottom = bounds
    current_center_x = (left + right - 1) / 2
    offset_x = round(target_center_x - current_center_x)
    if offset_x == 0:
        return image.copy(), 0

    shifted_bounds = (left + offset_x, bounds[1], right + offset_x, bounds[3])
    if (
        shifted_bounds[0] < SAFE_BOUNDS["left"]
        or shifted_bounds[2] - 1 > SAFE_BOUNDS["right"]
    ):
        raise SpriteValidationError(
            f"registration shift {offset_x:+d}px would cross horizontal safe bounds"
        )
    output = Image.new("RGBA", FRAME_SIZE)
    output.alpha_composite(image, (offset_x, 0))
    if output.getchannel("A").getbbox() != shifted_bounds:
        raise SpriteValidationError("registration unexpectedly clipped visible pixels")
    return output, offset_x


def process(spec_path: Path, *, write: bool) -> int:
    spec = load_spec(spec_path)
    if spec.registration_center_x is None:
        raise SpriteValidationError(
            f"{spec_path}: character.json has no registration.visible_bounds_center_x"
        )

    changed = 0
    for animation in spec.animations:
        for direction in (item for item in DIRECTIONS if item not in spec.mirrored_from):
            directory = spec.directory / "frames" / animation.name / direction
            paths = sorted(directory.glob("*.png"))
            if len(paths) != animation.frames:
                raise SpriteValidationError(
                    f"{directory}: expected {animation.frames} numbered PNG frames"
                )
            target = spec.registration_center_x[direction]
            for path in paths:
                with Image.open(path) as opened:
                    source = opened.copy()
                registered, offset_x = register_frame(source, target)
                if abs(offset_x) > spec.registration_tolerance:
                    changed += 1
                    if write:
                        registered.save(path, format="PNG", compress_level=9)
                    print(f"{'shifted' if write else 'needs'} {path}: {offset_x:+d}px")

        for target, source_direction in spec.mirrored_from.items():
            target_directory = spec.directory / "frames" / animation.name / target
            source_directory = spec.directory / "frames" / animation.name / source_direction
            for index in range(animation.frames):
                target_path = target_directory / f"{index:03d}.png"
                source_path = source_directory / f"{index:03d}.png"
                with Image.open(source_path) as opened:
                    expected = opened.convert("RGBA").transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                _registered, expected_offset = register_frame(
                    expected,
                    spec.registration_center_x[target],
                )
                if abs(expected_offset) > spec.registration_tolerance:
                    raise SpriteValidationError(
                        f"{target_path}: mirrored source misses declared registration by "
                        f"{expected_offset:+d}px"
                    )
                with Image.open(target_path) as opened:
                    current = opened.convert("RGBA")
                if current.tobytes() == expected.tobytes():
                    continue
                changed += 1
                if write:
                    expected.save(target_path, format="PNG", compress_level=9)
                print(
                    f"{'mirrored' if write else 'needs mirror'} {target_path} "
                    f"from {source_path}"
                )

    if changed and not write:
        raise SpriteValidationError(
            f"{spec_path}: {changed} frame(s) require horizontal registration"
        )
    print(f"character frame registration: {changed} frame(s) {'updated' if write else 'valid'}")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--write", action="store_true", help="rewrite misregistered source frames")
    args = parser.parse_args()
    try:
        process(args.spec, write=args.write)
    except SpriteValidationError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
