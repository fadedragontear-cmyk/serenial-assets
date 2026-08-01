#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import lzma
import struct
import zlib
from pathlib import Path

ROOT = Path.cwd()
STAGE = ROOT / ".asset-publish"
ELEMENTS = ["fire", "water", "wind", "earth", "ice", "storm", "light", "shadow", "aether", "neutral"]
ANIMS = {
    "idle": (4, 4, True),
    "hurt": (4, 8, False),
    "walk": (6, 8, True),
    "attack": (6, 10, False),
    "cast": (6, 10, False),
    "victory": (6, 6, True),
    "defeat": (6, 6, False),
}
EXPECTED = {
    "idle": (256, 256),
    "hurt": (256, 256),
    "walk": (384, 256),
    "attack": (384, 256),
    "cast": (384, 256),
    "victory": (384, 256),
    "defeat": (384, 256),
}


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)


def write_rgba_png(path: Path, width: int, height: int, pixels: bytes) -> None:
    if len(pixels) != width * height * 4:
        raise ValueError(f"{path}: bad RGBA byte count")
    raw = b"".join(b"\x00" + pixels[y * width * 4 : (y + 1) * width * 4] for y in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def png_header(path: Path):
    body = path.read_bytes()
    if body[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not PNG")
    width, height, depth, color = struct.unpack(">IIBB", body[16:26])
    return width, height, depth, color, (b"tRNS" in body)


def load_pack():
    parts = sorted(STAGE.glob("hatchling_compact20_pack.b64.part*"))
    if not parts:
        raise RuntimeError("compact sprite pack chunks missing")
    packed = base64.b64decode("".join(part.read_text().strip() for part in parts), validate=True)
    expected = (STAGE / "hatchling_compact20_pack.sha256").read_text().strip()
    actual = hashlib.sha256(packed).hexdigest()
    if actual != expected:
        raise RuntimeError(f"pack checksum mismatch: {actual} != {expected}")
    payload = lzma.decompress(packed)
    if payload[:4] != b"SSP2":
        raise RuntimeError("bad compact sprite pack magic")
    header_length = struct.unpack(">I", payload[4:8])[0]
    header = json.loads(payload[8 : 8 + header_length])
    data = payload[8 + header_length :]
    if header.get("format") != "indexed24-20px-v1":
        raise RuntimeError("unexpected compact pack format")
    return header, data


def indexed_frame_to_rgba(indices: bytes, palette: list[int], sw: int = 20, sh: int = 20, dw: int = 64, dh: int = 64) -> bytes:
    colors = [tuple(palette[index : index + 3]) for index in range(0, len(palette), 3)]
    source = []
    for index in indices:
        red, green, blue = colors[index]
        source.append((red, green, blue, 0 if index == 0 else 255))

    output = bytearray(dw * dh * 4)
    for y in range(dh):
        sy = (y + 0.5) * sh / dh - 0.5
        y0 = max(0, min(sh - 1, int(sy)))
        y1 = min(sh - 1, y0 + 1)
        fy = max(0.0, min(1.0, sy - y0))
        for x in range(dw):
            sx = (x + 0.5) * sw / dw - 0.5
            x0 = max(0, min(sw - 1, int(sx)))
            x1 = min(sw - 1, x0 + 1)
            fx = max(0.0, min(1.0, sx - x0))
            samples = (
                (source[y0 * sw + x0], (1 - fx) * (1 - fy)),
                (source[y0 * sw + x1], fx * (1 - fy)),
                (source[y1 * sw + x0], (1 - fx) * fy),
                (source[y1 * sw + x1], fx * fy),
            )
            alpha = sum(color[3] * weight for color, weight in samples)
            position = (y * dw + x) * 4
            if alpha < 0.5:
                output[position : position + 4] = b"\x00\x00\x00\x00"
                continue
            red = sum(color[0] * color[3] * weight for color, weight in samples) / alpha
            green = sum(color[1] * color[3] * weight for color, weight in samples) / alpha
            blue = sum(color[2] * color[3] * weight for color, weight in samples) / alpha
            output[position : position + 4] = bytes(
                (
                    max(0, min(255, round(red))),
                    max(0, min(255, round(green))),
                    max(0, min(255, round(blue))),
                    max(0, min(255, round(alpha))),
                )
            )
    return bytes(output)


def expand_atlas(record: dict, pixels: bytes, palette: list[int]) -> bytes:
    source_width = source_height = 20
    target_width = target_height = 64
    columns = record["width"] // source_width
    rows = record["height"] // source_height
    if rows != 4 or record["out_width"] != columns * target_width or record["out_height"] != rows * target_height:
        raise RuntimeError(f"bad compact atlas record: {record}")

    output = bytearray(record["out_width"] * record["out_height"] * 4)
    for row in range(rows):
        for column in range(columns):
            frame = bytearray(source_width * source_height)
            for y in range(source_height):
                start = (row * source_height + y) * record["width"] + column * source_width
                frame[y * source_width : (y + 1) * source_width] = pixels[start : start + source_width]
            rgba = indexed_frame_to_rgba(bytes(frame), palette)
            for y in range(target_height):
                source_start = y * target_width * 4
                target_start = ((row * target_height + y) * record["out_width"] + column * target_width) * 4
                output[target_start : target_start + target_width * 4] = rgba[source_start : source_start + target_width * 4]
    return bytes(output)


def write_sprites() -> None:
    header, data = load_pack()
    if header.get("elements") != ELEMENTS:
        raise RuntimeError("element order mismatch")

    for record in header["files"]:
        element = record["element"]
        offset = record["offset"]
        length = record["length"]
        pixels = data[offset : offset + length]
        if len(pixels) != record["width"] * record["height"]:
            raise RuntimeError(f"bad compact data length: {record['path']}")
        rgba = expand_atlas(record, pixels, header["palettes"][element])
        write_rgba_png(ROOT / record["path"], record["out_width"], record["out_height"], rgba)

    for element in ELEMENTS:
        animations = {}
        for name, (frames, fps, loop) in ANIMS.items():
            animation = {"file": f"{name}.png", "frames": frames, "fps": fps, "loop": loop}
            if name in ("attack", "cast"):
                animation["event_frame"] = 3
            if name == "defeat":
                animation["hold_last_frame"] = True
            animations[name] = animation

        metadata = {
            "schema_version": 2,
            "contract_version": "serenial-sprite-source-v2",
            "frame_width": 64,
            "frame_height": 64,
            "direction_rows": ["down", "left", "right", "up"],
            "anchor": {"x": 32, "y": 60},
            "world_scale": 1.15,
            "render_filter": "linear",
            "pixel_art": False,
            "art_status": "baseline_placeholder_v1",
            "review_status": "runtime_baseline_manual_review_required",
            "known_limitations": [
                "generated placeholder art; anatomy and directional consistency need manual cleanup",
                "contact shadows are baked into several frames",
                "some motion cycles read as pose changes rather than fully articulated animation",
                "effect scale and lighting vary between action frames",
                "runtime atlases are compact derivatives of higher-resolution source work retained for later refinement",
            ],
            "animations": animations,
            "source_note": f"{element.title()} Hatchling baseline normalized for runtime use. Higher-resolution 1536x1024 and 1024x1024 generation masters should be retained as future source material.",
        }
        path = ROOT / f"digital-dragons/dragons/elemental/{element}/hatchling_01/sprites_v2/sprite.json"
        path.write_text(json.dumps(metadata, indent=2) + "\n")


def write_visual_stages() -> None:
    body_plans = {
        "fire": "grounded",
        "water": "serpentine",
        "wind": "airborne",
        "earth": "grounded",
        "ice": "grounded",
        "storm": "grounded",
        "light": "floating",
        "shadow": "floating",
        "aether": "floating",
        "neutral": "generalist",
    }
    staged_assets = {}
    for element in ELEMENTS:
        key = f"hatchling_{element}_01"
        presentation_base = f"dragons/elemental/{element}/variant_01"
        staged_assets[key] = {
            "portrait": f"{presentation_base}/portrait.png",
            "profile": f"{presentation_base}/profile.png",
            "race": f"{presentation_base}/race.png",
            "sprites": f"dragons/elemental/{element}/hatchling_01/sprites_v2/sprite.json",
            "kind": "elemental_stage",
            "elements": [element],
            "stage": "whelp",
            "display_label": f"{element.title()} Hatchling · Baseline 01",
            "art_status": "baseline_placeholder_v1",
            "review_status": "runtime_baseline_manual_review_required",
        }

    object_body = {
        "schema_version": 1,
        "contract_version": "serenial-dragon-visual-stages-v1",
        "description": "Evolution-aware visual keys. Baseline hatchling packs are staged for all ten ordinary elements; canonical art remains the fallback.",
        "stage_order": ["whelp", "drake", "mature", "adult", "elder"],
        "stage_levels": {
            "whelp": [1, 9],
            "drake": [10, 29],
            "mature": [30, 49],
            "adult": [50, 69],
            "elder": [70, None],
        },
        "body_plans": body_plans,
        "element_defaults": {element: {"whelp": f"hatchling_{element}_01"} for element in ELEMENTS},
        "staged_assets": staged_assets,
        "asset_overrides": {},
        "fallback_policy": {
            "missing_stage_asset": "canonical_species_asset",
            "missing_animation": "idle_then_element_token",
            "unique_dragons": "canonical_unless_explicit_override",
            "hybrids": "canonical_unless_explicit_override",
        },
    }
    (ROOT / "digital-dragons/visual-stages.json").write_text(json.dumps(object_body, indent=2) + "\n")


def write_terrain_metadata() -> None:
    terrains = [
        "ocean",
        "coast",
        "river",
        "lair",
        "road",
        "grass",
        "forest",
        "earth",
        "water",
        "mountain",
        "windstream",
        "lava",
        "cliff",
        "icefield",
        "stormfield",
        "lightfield",
        "shadowfen",
        "aetherfield",
        "neutralfield",
        "ruins",
    ]
    metadata = {
        "schema_version": 1,
        "asset_version": "2026.08.01.1",
        "runtime_key": "serenial_terrain_v1",
        "atlas": "serenial_terrain_v1.png",
        "pixel_art": False,
        "tile_width": 32,
        "tile_height": 32,
        "columns": 10,
        "rows": 8,
        "variants_per_terrain": 4,
        "layout": "terrain_major_then_variant",
        "terrains": {},
        "art_status": "baseline_authored_repack_v2",
        "review_status": "runtime_visual_review",
    }
    for terrain_index, name in enumerate(terrains):
        cells = []
        for variant in range(4):
            index = terrain_index * 4 + variant
            column = index % 10
            row = index // 10
            cells.append({"variant": variant, "column": column, "row": row, "x": column * 32, "y": row * 32})
        metadata["terrains"][name] = {"index": terrain_index, "cells": cells}
    path = ROOT / "digital-dragons/world/tiles/serenial_terrain_v1.json"
    path.write_text(json.dumps(metadata, indent=2) + "\n")


def update_manifest() -> None:
    path = ROOT / "digital-dragons/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["asset_version"] = "2026.08.01.1"
    if "world_tiles" in manifest and "serenial_terrain_v1" in manifest["world_tiles"]:
        manifest["world_tiles"]["serenial_terrain_v1"]["art_status"] = "baseline_v2_repacked"
        manifest["world_tiles"]["serenial_terrain_v1"]["review_status"] = "runtime_baseline_manual_review_required"
    if "world_entities" in manifest and "serenial_entities_v1" in manifest["world_entities"]:
        manifest["world_entities"]["serenial_entities_v1"]["art_status"] = "baseline_v2_transparent"
        manifest["world_entities"]["serenial_entities_v1"]["review_status"] = "runtime_baseline_manual_review_required"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def write_docs() -> None:
    docs = ROOT / "digital-dragons/docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "HATCHLING_BASELINE_V1.md").write_text(
        """# Elemental Hatchling Baseline V1

All ten ordinary elemental Whelps have staged animation packs: Fire, Water, Wind, Earth, Ice, Storm, Light, Shadow, Aether, and Neutral.

## Runtime contract

- 64×64 cells; rows Down, Left, Right, Up
- Idle/Hurt: 4 frames × 4 rows
- Walk/Attack/Cast/Victory/Defeat: 6 frames × 4 rows
- RGBA PNG with true transparency and linear filtering
- ground anchor `(32, 60)`
- canonical elemental portrait/profile/race art remains in use until matching hatchling presentation art is approved

## Status

These are technically valid baseline placeholders, not final art. Unique dragons, hybrids, and later evolution stages remain protected from ordinary Whelp substitution.
"""
    )
    (docs / "SOURCE_MASTER_POLICY.md").write_text(
        """# Generated Source Master Policy

The image generator produces its strongest dragon art as 1536×1024 contact sheets and 1024×1024 presentation images. These dimensions are now treated as source masters rather than failed runtime sheets.

The game consumes normalized runtime atlases derived from those masters. Future upgrades should preserve the original high-resolution files, record crop/frame mappings, and rebuild runtime atlases without asking image generation to emit exact production grids.

The current 64×64-cell Whelp packs are baseline derivatives. They may be replaced in place after manual cleanup without changing stage keys or gameplay systems.
"""
    )
    (docs / "WORLD_ATLAS_BASELINE_V2.md").write_text(
        """# Dragon World Atlas Baseline Refresh

The merged terrain and entity atlases remain on their established public v1 paths. This publication adds the missing terrain metadata and bumps the root asset version so Celdra no longer reuses the pre-refresh cached files.

The entity atlas contract is 256×64 RGBA with 16 transparent 32×32 cells. The terrain atlas contract is 320×256 with 80 32×32 cells.

After merge, redeploy Celdra-Cloud or clear `/tmp/celdra-digital-dragons`, then hard-refresh the Activity.
"""
    )


def validate() -> None:
    stages = json.loads((ROOT / "digital-dragons/visual-stages.json").read_text())
    for element in ELEMENTS:
        key = f"hatchling_{element}_01"
        if key not in stages["staged_assets"]:
            raise RuntimeError(f"missing {key}")
        base = ROOT / f"digital-dragons/dragons/elemental/{element}/hatchling_01/sprites_v2"
        metadata = json.loads((base / "sprite.json").read_text())
        if metadata["frame_width"] != 64 or metadata["direction_rows"] != ["down", "left", "right", "up"]:
            raise RuntimeError(f"{element}: bad sprite contract")
        for name, size in EXPECTED.items():
            actual = png_header(base / f"{name}.png")
            if actual[:2] != size or actual[2] != 8 or actual[3] != 6:
                raise RuntimeError(f"{element}/{name}: bad PNG {actual}")

    for path, size in [
        (ROOT / "digital-dragons/world/tiles/serenial_terrain_v1.png", (320, 256)),
        (ROOT / "digital-dragons/world/entities/serenial_entities_v1.png", (256, 64)),
    ]:
        actual = png_header(path)
        if actual[:2] != size:
            raise RuntimeError(f"{path}: wrong dimensions {actual[:2]}")
    print("validated ten elemental hatchling packs and world atlas contracts")


def main() -> None:
    write_sprites()
    write_visual_stages()
    write_terrain_metadata()
    update_manifest()
    write_docs()
    validate()


if __name__ == "__main__":
    main()
