#!/usr/bin/env python3
"""Audit elemental hatchling sprite packs for runtime contract and visual crop risks.

Contract errors fail the command. Visual-risk findings are warnings so existing legacy
art can remain reviewable while new candidates are improved incrementally.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ELEMENTS = ["fire", "water", "earth", "storm", "ice", "wind", "shadow", "light", "aether", "neutral"]
EXPECTED = {
    "idle": 4,
    "walk": 6,
    "attack": 6,
    "cast": 6,
    "hurt": 4,
    "victory": 6,
    "defeat": 6,
}
EXPECTED_ROWS = ["down", "left", "right", "up"]


@dataclass
class Finding:
    level: str
    element: str
    animation: str
    code: str
    message: str
    row: int | None = None
    frame: int | None = None


def has_alpha(image: Image.Image) -> bool:
    return image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info)


def alpha_channel(image: Image.Image) -> Image.Image:
    return image.convert("RGBA").getchannel("A")


def frame_edge_risk(alpha: Image.Image, margin: int = 2) -> tuple[bool, list[str]]:
    width, height = alpha.size
    if width <= margin * 2 or height <= margin * 2:
        return True, ["frame-too-small"]
    edges = {
        "left": alpha.crop((0, 0, margin, height)),
        "right": alpha.crop((width - margin, 0, width, height)),
        "top": alpha.crop((0, 0, width, margin)),
        "bottom": alpha.crop((0, height - margin, width, height)),
    }
    touched = [name for name, band in edges.items() if band.getbbox() is not None]
    return bool(touched), touched


def audit_pack(element: str) -> list[Finding]:
    findings: list[Finding] = []
    base = ROOT / "digital-dragons" / "dragons" / "elemental" / element / "hatchling_01" / "sprites_v2"
    meta_path = base / "sprite.json"
    if not meta_path.exists():
        return [Finding("error", element, "pack", "missing-metadata", f"Missing {meta_path.relative_to(ROOT)}")]

    try:
        meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [Finding("error", element, "pack", "invalid-metadata", f"Unable to parse sprite.json: {exc}")]

    frame_width = int(meta.get("frame_width") or 0)
    frame_height = int(meta.get("frame_height") or 0)
    if frame_width <= 0 or frame_height <= 0:
        findings.append(Finding("error", element, "pack", "invalid-frame-size", "frame_width/frame_height must be positive integers"))
        return findings

    rows = meta.get("direction_rows")
    if rows != EXPECTED_ROWS:
        findings.append(Finding("error", element, "pack", "direction-order", f"direction_rows must be {EXPECTED_ROWS}, got {rows!r}"))

    animations = meta.get("animations") or {}
    for animation, expected_frames in EXPECTED.items():
        config = animations.get(animation)
        if not isinstance(config, dict):
            findings.append(Finding("error", element, animation, "missing-animation", "Animation is missing from sprite.json"))
            continue
        frames = int(config.get("frames") or 0)
        if frames != expected_frames:
            findings.append(Finding("error", element, animation, "frame-count", f"Expected {expected_frames} frames, metadata declares {frames}"))
        filename = str(config.get("file") or f"{animation}.png")
        path = base / filename
        if not path.exists():
            findings.append(Finding("error", element, animation, "missing-file", f"Missing {path.relative_to(ROOT)}"))
            continue

        try:
            image = Image.open(path)
            image.load()
        except Exception as exc:
            findings.append(Finding("error", element, animation, "invalid-image", f"Unable to read PNG: {exc}"))
            continue

        expected_size = (frame_width * frames, frame_height * len(EXPECTED_ROWS))
        if image.size != expected_size:
            findings.append(Finding("error", element, animation, "sheet-size", f"Expected {expected_size[0]}x{expected_size[1]}, got {image.width}x{image.height}"))
            continue
        if not has_alpha(image):
            findings.append(Finding("error", element, animation, "missing-alpha", f"{filename} has no transparency channel"))

        alpha = alpha_channel(image)
        for row in range(len(EXPECTED_ROWS)):
            for frame in range(frames):
                box = (frame * frame_width, row * frame_height, (frame + 1) * frame_width, (row + 1) * frame_height)
                cell = alpha.crop(box)
                bbox = cell.getbbox()
                if bbox is None:
                    findings.append(Finding("error", element, animation, "empty-frame", "Frame has no visible pixels", row=row, frame=frame))
                    continue
                touches, edges = frame_edge_risk(cell, margin=2)
                if touches:
                    findings.append(Finding("warning", element, animation, "edge-crop-risk", f"Visible pixels touch the 2px safety margin: {', '.join(edges)}", row=row, frame=frame))
                visible_width = bbox[2] - bbox[0]
                visible_height = bbox[3] - bbox[1]
                if visible_width / frame_width > .94 or visible_height / frame_height > .94:
                    findings.append(Finding("warning", element, animation, "tight-occupancy", f"Visible bounds {visible_width}x{visible_height} occupy >94% of the frame", row=row, frame=frame))

        corners = [alpha.getpixel((0, 0)), alpha.getpixel((image.width - 1, 0)), alpha.getpixel((0, image.height - 1)), alpha.getpixel((image.width - 1, image.height - 1))]
        if any(value > 0 for value in corners):
            findings.append(Finding("warning", element, animation, "sheet-corner-alpha", "One or more sheet corners are non-transparent; check for matte/background leakage"))

    art_status = str(meta.get("art_status") or "")
    if "placeholder" in art_status or art_status in {"legacy", "legacy_authored"}:
        findings.append(Finding("warning", element, "pack", "legacy-status", f"sprite.json art_status is {art_status!r}"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", dest="json_path", help="Optional path for machine-readable report")
    parser.add_argument("--elements", nargs="*", choices=ELEMENTS, default=ELEMENTS)
    args = parser.parse_args()

    findings = [finding for element in args.elements for finding in audit_pack(element)]
    errors = [row for row in findings if row.level == "error"]
    warnings = [row for row in findings if row.level == "warning"]

    print(f"Hatchling sprite audit: {len(args.elements)} elements, {len(errors)} errors, {len(warnings)} warnings")
    for row in findings:
        location = f"{row.element}/{row.animation}"
        if row.row is not None and row.frame is not None:
            location += f" row={row.row} frame={row.frame}"
        print(f"[{row.level.upper()}] {location} {row.code}: {row.message}")

    if args.json_path:
        destination = Path(args.json_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({
            "schema_version": 1,
            "elements": args.elements,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "findings": [asdict(row) for row in findings],
        }, indent=2) + "\n", encoding="utf-8")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
