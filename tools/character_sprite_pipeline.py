#!/usr/bin/env python3
"""Validate and pack Serenial character source frames into runtime atlases."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


CONTRACT_VERSION = "serenial-character-atlas-v2"
FRAME_SIZE = (96, 96)
ANCHOR = {"x": 48, "y": 84}
SAFE_BOUNDS = {"left": 4, "top": 4, "right": 91, "bottom": 87}
DIRECTIONS = ("down", "left", "right", "up")
CORE_ANIMATIONS = {"idle": 4, "walk": 8, "run": 8}
MAX_VISIBLE_COLORS = 96
ASSET_KEY = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class SpriteValidationError(ValueError):
    """Raised when a character pack violates the production contract."""


@dataclass(frozen=True)
class Animation:
    name: str
    frames: int
    fps: float
    loop: bool


@dataclass(frozen=True)
class CharacterSpec:
    source: Path
    asset_id: str
    asset_kind: str
    animations: tuple[Animation, ...]
    registration_center_x: dict[str, float] | None
    registration_tolerance: float
    mirrored_from: dict[str, str]

    @property
    def directory(self) -> Path:
        return self.source.parent

    @property
    def runtime_directory(self) -> Path:
        return self.directory / "runtime"


def _expect_equal(payload: dict[str, Any], key: str, expected: Any, source: Path) -> None:
    if payload.get(key) != expected:
        raise SpriteValidationError(
            f"{source}: {key} must be {expected!r}; got {payload.get(key)!r}"
        )


def load_spec(source: Path) -> CharacterSpec:
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpriteValidationError(f"{source}: unable to read character.json: {exc}") from exc

    if not isinstance(payload, dict):
        raise SpriteValidationError(f"{source}: root value must be an object")

    _expect_equal(payload, "schema_version", 1, source)
    _expect_equal(payload, "contract_version", CONTRACT_VERSION, source)
    _expect_equal(payload, "frame_width", FRAME_SIZE[0], source)
    _expect_equal(payload, "frame_height", FRAME_SIZE[1], source)
    _expect_equal(payload, "anchor", ANCHOR, source)
    _expect_equal(payload, "safe_bounds", SAFE_BOUNDS, source)
    _expect_equal(payload, "direction_rows", list(DIRECTIONS), source)
    _expect_equal(payload, "render_filter", "nearest", source)

    asset_id = payload.get("id")
    if not isinstance(asset_id, str) or not ASSET_KEY.fullmatch(asset_id):
        raise SpriteValidationError(f"{source}: id must match {ASSET_KEY.pattern}")

    asset_kind = payload.get("asset_kind", "character")
    if asset_kind not in {"character", "layer"}:
        raise SpriteValidationError(f"{source}: asset_kind must be 'character' or 'layer'")

    raw_animations = payload.get("animations")
    if not isinstance(raw_animations, dict) or not raw_animations:
        raise SpriteValidationError(f"{source}: animations must be a non-empty object")

    animations: list[Animation] = []
    for name, raw in raw_animations.items():
        if not isinstance(name, str) or not ASSET_KEY.fullmatch(name):
            raise SpriteValidationError(f"{source}: unsafe animation name {name!r}")
        if not isinstance(raw, dict):
            raise SpriteValidationError(f"{source}: animation {name!r} must be an object")
        frames = raw.get("frames")
        fps = raw.get("fps")
        loop = raw.get("loop")
        if not isinstance(frames, int) or isinstance(frames, bool) or not 1 <= frames <= 32:
            raise SpriteValidationError(f"{source}: {name}.frames must be an integer from 1 to 32")
        if not isinstance(fps, (int, float)) or isinstance(fps, bool) or not 0 < fps <= 30:
            raise SpriteValidationError(f"{source}: {name}.fps must be a number above 0 and at most 30")
        if not isinstance(loop, bool):
            raise SpriteValidationError(f"{source}: {name}.loop must be true or false")
        animations.append(Animation(name=name, frames=frames, fps=float(fps), loop=loop))

    animation_map = {animation.name: animation for animation in animations}
    for name, expected_frames in CORE_ANIMATIONS.items():
        animation = animation_map.get(name)
        if animation is None:
            raise SpriteValidationError(f"{source}: required animation {name!r} is missing")
        if animation.frames != expected_frames:
            raise SpriteValidationError(
                f"{source}: {name} requires {expected_frames} frames; got {animation.frames}"
            )

    registration_center_x: dict[str, float] | None = None
    registration_tolerance = 0.5
    raw_registration = payload.get("registration")
    if raw_registration is not None:
        if not isinstance(raw_registration, dict):
            raise SpriteValidationError(f"{source}: registration must be an object")
        raw_centers = raw_registration.get("visible_bounds_center_x")
        if not isinstance(raw_centers, dict) or set(raw_centers) != set(DIRECTIONS):
            raise SpriteValidationError(
                f"{source}: registration.visible_bounds_center_x must define exactly "
                + ", ".join(DIRECTIONS)
            )
        registration_center_x = {}
        for direction in DIRECTIONS:
            center = raw_centers[direction]
            if (
                not isinstance(center, (int, float))
                or isinstance(center, bool)
                or not SAFE_BOUNDS["left"] <= center <= SAFE_BOUNDS["right"]
            ):
                raise SpriteValidationError(
                    f"{source}: registration center for {direction} must be inside safe bounds"
                )
            registration_center_x[direction] = float(center)
        tolerance = raw_registration.get("tolerance", registration_tolerance)
        if (
            not isinstance(tolerance, (int, float))
            or isinstance(tolerance, bool)
            or not 0 <= tolerance <= 2
        ):
            raise SpriteValidationError(
                f"{source}: registration.tolerance must be a number from 0 through 2"
            )
        registration_tolerance = float(tolerance)

    mirrored_from: dict[str, str] = {}
    raw_derivations = payload.get("direction_derivation", {})
    if not isinstance(raw_derivations, dict):
        raise SpriteValidationError(f"{source}: direction_derivation must be an object")
    for target, provenance in raw_derivations.items():
        if target not in DIRECTIONS or not isinstance(provenance, str):
            raise SpriteValidationError(f"{source}: invalid direction derivation entry")
        match = re.fullmatch(
            r"reviewed-mirror-of-(down|left|right|up)(?:-[a-z0-9._-]+)?",
            provenance,
        )
        if match:
            source_direction = match.group(1)
            if source_direction == target:
                raise SpriteValidationError(f"{source}: a direction cannot mirror itself")
            mirrored_from[target] = source_direction

    return CharacterSpec(
        source=source,
        asset_id=asset_id,
        asset_kind=asset_kind,
        animations=tuple(animations),
        registration_center_x=registration_center_x,
        registration_tolerance=registration_tolerance,
        mirrored_from=mirrored_from,
    )


def _frame_paths(spec: CharacterSpec, animation: Animation, direction: str) -> list[Path]:
    directory = spec.directory / "frames" / animation.name / direction
    expected = [directory / f"{index:03d}.png" for index in range(animation.frames)]
    actual = sorted(directory.glob("*.png")) if directory.is_dir() else []
    if actual != expected:
        missing = [str(path.relative_to(spec.directory)) for path in expected if path not in actual]
        extra = [str(path.relative_to(spec.directory)) for path in actual if path not in expected]
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        raise SpriteValidationError(
            f"{spec.source}: {animation.name}/{direction} frame sequence is invalid: "
            + "; ".join(details or ["directory is missing"])
        )
    return expected


def _validated_frame(
    path: Path,
    *,
    allow_empty: bool,
    expected_center_x: float | None = None,
    registration_tolerance: float = 0.5,
) -> Image.Image:
    try:
        with Image.open(path) as opened:
            if opened.format != "PNG":
                raise SpriteValidationError(f"{path}: source frame must be a PNG")
            if opened.size != FRAME_SIZE:
                raise SpriteValidationError(
                    f"{path}: expected {FRAME_SIZE[0]}x{FRAME_SIZE[1]}, got {opened.width}x{opened.height}"
                )
            if opened.mode != "RGBA":
                raise SpriteValidationError(f"{path}: expected RGBA mode, got {opened.mode}")
            frame = opened.copy()
    except SpriteValidationError:
        raise
    except (OSError, ValueError) as exc:
        raise SpriteValidationError(f"{path}: unreadable PNG: {exc}") from exc

    alpha = frame.getchannel("A")
    alpha_values = {value for count, value in alpha.getcolors(maxcolors=256) or [] if count}
    if not alpha_values.issubset({0, 255}):
        raise SpriteValidationError(
            f"{path}: production pixel art requires binary alpha; found partial transparency"
        )

    visible_colors = {
        pixel[:3]
        for _count, pixel in frame.getcolors(maxcolors=FRAME_SIZE[0] * FRAME_SIZE[1]) or []
        if pixel[3] == 255
    }
    if len(visible_colors) > MAX_VISIBLE_COLORS:
        raise SpriteValidationError(
            f"{path}: {len(visible_colors)} visible colors exceed the {MAX_VISIBLE_COLORS}-color limit"
        )

    alpha_bounds = alpha.getbbox()
    if alpha_bounds is None:
        if allow_empty:
            return frame
        raise SpriteValidationError(f"{path}: character frame is fully transparent")

    left, top, right_exclusive, bottom_exclusive = alpha_bounds
    if (
        left < SAFE_BOUNDS["left"]
        or top < SAFE_BOUNDS["top"]
        or right_exclusive - 1 > SAFE_BOUNDS["right"]
        or bottom_exclusive - 1 > SAFE_BOUNDS["bottom"]
    ):
        raise SpriteValidationError(
            f"{path}: visible bounds {alpha_bounds} cross safe bounds "
            f"({SAFE_BOUNDS['left']}, {SAFE_BOUNDS['top']}, "
            f"{SAFE_BOUNDS['right'] + 1}, {SAFE_BOUNDS['bottom'] + 1})"
        )
    if expected_center_x is not None:
        visible_center_x = (left + right_exclusive - 1) / 2
        if abs(visible_center_x - expected_center_x) > registration_tolerance:
            raise SpriteValidationError(
                f"{path}: horizontal registration drift; visible center {visible_center_x:g} "
                f"must remain within {registration_tolerance:g}px of {expected_center_x:g}"
            )
    return frame


def build_animation_sheet(spec: CharacterSpec, animation: Animation) -> Image.Image:
    frames_by_direction: dict[str, list[Image.Image]] = {}
    for row, direction in enumerate(DIRECTIONS):
        frames_by_direction[direction] = []
        for column, path in enumerate(_frame_paths(spec, animation, direction)):
            expected_center_x = (
                spec.registration_center_x.get(direction)
                if spec.registration_center_x is not None
                else None
            )
            frame = _validated_frame(
                path,
                allow_empty=spec.asset_kind == "layer",
                expected_center_x=expected_center_x,
                registration_tolerance=spec.registration_tolerance,
            )
            frames_by_direction[direction].append(frame)

    for target, source_direction in spec.mirrored_from.items():
        for index, (target_frame, source_frame) in enumerate(
            zip(frames_by_direction[target], frames_by_direction[source_direction], strict=True)
        ):
            expected = source_frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if target_frame.tobytes() != expected.tobytes():
                raise SpriteValidationError(
                    f"{spec.source}: {animation.name}/{target}/{index:03d}.png must be the exact "
                    f"reviewed mirror of {animation.name}/{source_direction}/{index:03d}.png"
                )

    sheet = Image.new("RGBA", (FRAME_SIZE[0] * animation.frames, FRAME_SIZE[1] * len(DIRECTIONS)))
    for row, direction in enumerate(DIRECTIONS):
        for column, frame in enumerate(frames_by_direction[direction]):
            sheet.alpha_composite(frame, (column * FRAME_SIZE[0], row * FRAME_SIZE[1]))
    return sheet


def runtime_metadata(spec: CharacterSpec) -> dict[str, Any]:
    metadata = {
        "schema_version": 1,
        "contract_version": CONTRACT_VERSION,
        "id": spec.asset_id,
        "asset_kind": spec.asset_kind,
        "frame_width": FRAME_SIZE[0],
        "frame_height": FRAME_SIZE[1],
        "anchor": ANCHOR,
        "safe_bounds": SAFE_BOUNDS,
        "direction_rows": list(DIRECTIONS),
        "render_filter": "nearest",
        "animations": {
            animation.name: {
                "file": f"{animation.name}.png",
                "frames": animation.frames,
                "fps": animation.fps,
                "loop": animation.loop,
            }
            for animation in spec.animations
        },
    }
    if spec.registration_center_x is not None:
        metadata["registration"] = {
            "visible_bounds_center_x": {
                direction: spec.registration_center_x[direction]
                for direction in DIRECTIONS
            },
            "tolerance": spec.registration_tolerance,
        }
    if spec.mirrored_from:
        metadata["mirrored_from"] = spec.mirrored_from
    return metadata


def _compare_sheet(expected: Image.Image, output: Path) -> None:
    if not output.is_file():
        raise SpriteValidationError(f"{output}: generated runtime sheet is missing")
    try:
        with Image.open(output) as opened:
            actual = opened.convert("RGBA")
            if actual.size != expected.size or actual.tobytes() != expected.tobytes():
                raise SpriteValidationError(f"{output}: runtime sheet is stale; rebuild it")
    except SpriteValidationError:
        raise
    except OSError as exc:
        raise SpriteValidationError(f"{output}: unreadable runtime sheet: {exc}") from exc


def _compare_metadata(expected: dict[str, Any], output: Path) -> None:
    if not output.is_file():
        raise SpriteValidationError(f"{output}: generated runtime metadata is missing")
    try:
        actual = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpriteValidationError(f"{output}: unreadable runtime metadata: {exc}") from exc
    if actual != expected:
        raise SpriteValidationError(f"{output}: runtime metadata is stale; rebuild it")


def process_pack(spec_path: Path, *, write: bool) -> None:
    spec = load_spec(spec_path)
    sheets = {animation.name: build_animation_sheet(spec, animation) for animation in spec.animations}
    metadata = runtime_metadata(spec)

    if write:
        spec.runtime_directory.mkdir(parents=True, exist_ok=True)
        for name, sheet in sheets.items():
            sheet.save(spec.runtime_directory / f"{name}.png", format="PNG", compress_level=9)
        (spec.runtime_directory / "sprite.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return

    for name, sheet in sheets.items():
        _compare_sheet(sheet, spec.runtime_directory / f"{name}.png")
    _compare_metadata(metadata, spec.runtime_directory / "sprite.json")


def process_root(root: Path, *, write: bool) -> int:
    specs = sorted(path for path in root.rglob("character.json") if "runtime" not in path.parts)
    errors: list[str] = []
    for spec in specs:
        try:
            process_pack(spec, write=write)
            print(f"{'built' if write else 'checked'} {spec.relative_to(root)}")
        except SpriteValidationError as exc:
            errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"character sprite pipeline: {len(specs)} pack(s) {'built' if write else 'valid'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("digital-characters"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write generated runtime atlases")
    mode.add_argument("--check", action="store_true", help="validate sources and generated outputs")
    args = parser.parse_args()
    return process_root(args.root, write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
