from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from tools.character_sprite_pipeline import (
    SpriteValidationError,
    load_spec,
    process_pack,
)
from tools.import_character_keypose_board import normalize_board, write_frames
from tools.register_character_frames import register_frame


DIRECTIONS = ("down", "left", "right", "up")
ANIMATIONS = {"idle": (4, 4), "walk": (8, 10), "run": (8, 14)}
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CELDRA_REFERENCE = (
    REPOSITORY_ROOT
    / "digital-characters"
    / "celdra-dragongirl"
    / "v1"
    / "reference"
)
FEMALE_BASE_REFERENCE = (
    REPOSITORY_ROOT
    / "digital-characters"
    / "humanoid-v1"
    / "female-base-a"
    / "reference"
)


class CharacterSpritePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "digital-characters" / "test-model" / "v1"
        self.root.mkdir(parents=True)
        self.spec = self.root / "character.json"
        self.spec.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "contract_version": "serenial-character-atlas-v2",
                    "id": "test-model-v1",
                    "asset_kind": "character",
                    "frame_width": 96,
                    "frame_height": 96,
                    "anchor": {"x": 48, "y": 84},
                    "safe_bounds": {"left": 4, "top": 4, "right": 91, "bottom": 87},
                    "direction_rows": list(DIRECTIONS),
                    "render_filter": "nearest",
                    "animations": {
                        name: {"frames": frames, "fps": fps, "loop": True}
                        for name, (frames, fps) in ANIMATIONS.items()
                    },
                }
            ),
            encoding="utf-8",
        )
        for animation, (frames, _fps) in ANIMATIONS.items():
            for direction_index, direction in enumerate(DIRECTIONS):
                directory = self.root / "frames" / animation / direction
                directory.mkdir(parents=True)
                for frame_index in range(frames):
                    image = Image.new("RGBA", (96, 96))
                    draw = ImageDraw.Draw(image)
                    draw.rectangle(
                        (42 + frame_index % 2, 60 + direction_index, 53 + frame_index % 2, 84),
                        fill=(80, 160, 240, 255),
                    )
                    image.save(directory / f"{frame_index:03d}.png")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_builds_and_checks_runtime_outputs(self) -> None:
        process_pack(self.spec, write=True)
        process_pack(self.spec, write=False)
        with Image.open(self.root / "runtime" / "walk.png") as sheet:
            self.assertEqual(sheet.size, (768, 384))
            self.assertEqual(sheet.mode, "RGBA")
        metadata = json.loads((self.root / "runtime" / "sprite.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["anchor"], {"x": 48, "y": 84})
        self.assertEqual(metadata["animations"]["run"]["frames"], 8)

    def test_rejects_opaque_or_edge_filled_background(self) -> None:
        bad_frame = self.root / "frames" / "idle" / "down" / "000.png"
        Image.new("RGBA", (96, 96), (255, 255, 255, 255)).save(bad_frame)
        with self.assertRaisesRegex(SpriteValidationError, "cross safe bounds"):
            process_pack(self.spec, write=True)

    def test_rejects_missing_numbered_frame(self) -> None:
        (self.root / "frames" / "run" / "up" / "007.png").unlink()
        with self.assertRaisesRegex(SpriteValidationError, "frame sequence is invalid"):
            process_pack(self.spec, write=True)

    def test_rejects_non_rgba_source(self) -> None:
        bad_frame = self.root / "frames" / "walk" / "left" / "003.png"
        Image.new("RGB", (96, 96), (20, 30, 40)).save(bad_frame)
        with self.assertRaisesRegex(SpriteValidationError, "expected RGBA mode"):
            process_pack(self.spec, write=True)

    def test_rejects_partial_alpha(self) -> None:
        bad_frame = self.root / "frames" / "idle" / "right" / "002.png"
        image = Image.new("RGBA", (96, 96))
        image.putpixel((48, 84), (80, 160, 240, 128))
        image.save(bad_frame)
        with self.assertRaisesRegex(SpriteValidationError, "requires binary alpha"):
            process_pack(self.spec, write=True)

    def test_rejects_generated_color_noise(self) -> None:
        bad_frame = self.root / "frames" / "walk" / "up" / "004.png"
        image = Image.new("RGBA", (96, 96))
        for index in range(100):
            x = 10 + index % 20
            y = 10 + index // 20
            image.putpixel((x, y), (index, (index * 3) % 256, (index * 7) % 256, 255))
        image.save(bad_frame)
        with self.assertRaisesRegex(SpriteValidationError, "exceed the 96-color limit"):
            process_pack(self.spec, write=True)

    def test_check_detects_stale_generated_sheet(self) -> None:
        process_pack(self.spec, write=True)
        output = self.root / "runtime" / "idle.png"
        with Image.open(output) as opened:
            changed = opened.copy()
        changed.putpixel((0, 0), (255, 0, 255, 255))
        changed.save(output)
        with self.assertRaisesRegex(SpriteValidationError, "runtime sheet is stale"):
            process_pack(self.spec, write=False)

    def test_contract_requires_core_frame_counts(self) -> None:
        payload = json.loads(self.spec.read_text(encoding="utf-8"))
        payload["animations"]["walk"]["frames"] = 6
        self.spec.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(SpriteValidationError, "walk requires 8 frames"):
            load_spec(self.spec)

    def test_optional_registration_rejects_horizontal_frame_drift(self) -> None:
        payload = json.loads(self.spec.read_text(encoding="utf-8"))
        payload["registration"] = {
            "visible_bounds_center_x": {direction: 48 for direction in DIRECTIONS},
            "tolerance": 0.5,
        }
        self.spec.write_text(json.dumps(payload), encoding="utf-8")
        bad_frame = self.root / "frames" / "idle" / "down" / "000.png"
        image = Image.new("RGBA", (96, 96))
        ImageDraw.Draw(image).rectangle((30, 60, 41, 84), fill=(80, 160, 240, 255))
        image.save(bad_frame)
        with self.assertRaisesRegex(SpriteValidationError, "horizontal registration drift"):
            process_pack(self.spec, write=True)

    def test_registration_shift_is_lossless_and_idempotent(self) -> None:
        image = Image.new("RGBA", (96, 96))
        ImageDraw.Draw(image).rectangle((20, 40, 49, 84), fill=(80, 160, 240, 255))
        registered, offset = register_frame(image, 48)
        self.assertEqual(offset, 14)
        self.assertEqual(registered.getchannel("A").getbbox(), (34, 40, 64, 85))
        registered_again, next_offset = register_frame(registered, 48)
        self.assertEqual(next_offset, 0)
        self.assertEqual(registered.tobytes(), registered_again.tobytes())

    def test_reviewed_mirror_provenance_is_pixel_exact(self) -> None:
        payload = json.loads(self.spec.read_text(encoding="utf-8"))
        payload["direction_derivation"] = {"left": "reviewed-mirror-of-right-v1"}
        self.spec.write_text(json.dumps(payload), encoding="utf-8")
        for animation, (frames, _fps) in ANIMATIONS.items():
            for index in range(frames):
                right_path = self.root / "frames" / animation / "right" / f"{index:03d}.png"
                left_path = self.root / "frames" / animation / "left" / f"{index:03d}.png"
                with Image.open(right_path) as opened:
                    mirrored = opened.convert("RGBA").transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                mirrored.save(left_path)
        process_pack(self.spec, write=True)
        bad_path = self.root / "frames" / "idle" / "left" / "000.png"
        with Image.open(bad_path) as opened:
            bad = opened.convert("RGBA")
        bad.putpixel((30, 50), (255, 255, 255, 255))
        bad.save(bad_path)
        with self.assertRaisesRegex(SpriteValidationError, "must be the exact reviewed mirror"):
            process_pack(self.spec, write=True)


class CharacterReferenceTests(unittest.TestCase):
    def assert_transparent_png(
        self,
        root: Path,
        relative: str,
        size: tuple[int, int],
    ) -> Image.Image:
        path = root / relative
        self.assertTrue(path.is_file(), f"missing reference asset {path}")
        with Image.open(path) as opened:
            self.assertEqual(opened.format, "PNG")
            self.assertEqual(opened.mode, "RGBA")
            self.assertEqual(opened.size, size)
            self.assertEqual(opened.getpixel((0, 0))[3], 0)
            return opened.copy()

    def assert_normalized_cardinals(
        self,
        root: Path,
        directory: str,
        expected_height: int,
    ) -> dict[str, tuple[int, int, int, int]]:
        bounds: dict[str, tuple[int, int, int, int]] = {}
        for direction in DIRECTIONS:
            image = self.assert_transparent_png(
                root,
                f"{directory}/{direction}.png",
                (96, 96),
            )
            alpha = image.getchannel("A")
            alpha_values = {value for _count, value in alpha.getcolors(maxcolors=256) or []}
            self.assertEqual(alpha_values, {0, 255}, direction)
            bound = alpha.getbbox()
            self.assertIsNotNone(bound, direction)
            left, top, right, bottom = bound
            self.assertGreaterEqual(left, 4, direction)
            self.assertGreaterEqual(top, 4, direction)
            self.assertLessEqual(right - 1, 91, direction)
            self.assertEqual(bottom - 1, 84, direction)
            self.assertEqual(bottom - top, expected_height, direction)
            visible_colors = {
                color[:3]
                for _count, color in image.getcolors(maxcolors=96 * 96) or []
                if color[3] == 255
            }
            self.assertLessEqual(len(visible_colors), 64, direction)
            bounds[direction] = bound
        return bounds

    def test_cardinal_master_has_true_alpha_and_consistent_side_views(self) -> None:
        master = self.assert_transparent_png(
            CELDRA_REFERENCE,
            "celdra-dragongirl-cardinal-master-candidate-v2.png",
            (1254, 1254),
        )
        quadrants = {
            "down": (0, 0, 627, 627),
            "right": (627, 0, 1254, 627),
            "left": (0, 627, 627, 1254),
            "up": (627, 627, 1254, 1254),
        }
        bounds = {
            direction: master.crop(box).getchannel("A").getbbox()
            for direction, box in quadrants.items()
        }
        self.assertTrue(all(bound is not None for bound in bounds.values()))
        right_width = bounds["right"][2] - bounds["right"][0]
        left_width = bounds["left"][2] - bounds["left"][0]
        right_height = bounds["right"][3] - bounds["right"][1]
        left_height = bounds["left"][3] - bounds["left"][1]
        self.assertLessEqual(abs(right_width - left_width), 5)
        self.assertLessEqual(abs(right_height - left_height), 8)
        for direction, (left, top, right, bottom) in bounds.items():
            self.assertGreater(left, 0, direction)
            self.assertGreater(top, 0, direction)
            self.assertLess(right, 627, direction)
            self.assertLess(bottom, 627, direction)

    def test_celdra_normalized_cardinals_share_scale_and_anchor(self) -> None:
        self.assert_transparent_png(
            CELDRA_REFERENCE,
            "celdra-dragongirl-96-grid-preview-v2.png",
            (192, 192),
        )
        bounds = self.assert_normalized_cardinals(
            CELDRA_REFERENCE,
            "cardinal-96-v2",
            70,
        )
        left_width = bounds["left"][2] - bounds["left"][0]
        right_width = bounds["right"][2] - bounds["right"][0]
        self.assertLessEqual(abs(left_width - right_width), 1)

    def test_female_baseline_master_has_true_alpha_and_matching_profiles(self) -> None:
        master = self.assert_transparent_png(
            FEMALE_BASE_REFERENCE,
            "female-base-cardinal-candidate-v1.png",
            (1254, 1254),
        )
        right = master.crop((627, 0, 1254, 627)).getchannel("A").getbbox()
        left = master.crop((0, 627, 627, 1254)).getchannel("A").getbbox()
        self.assertIsNotNone(right)
        self.assertIsNotNone(left)
        self.assertLessEqual(abs((right[2] - right[0]) - (left[2] - left[0])), 2)
        self.assertLessEqual(abs((right[3] - right[1]) - (left[3] - left[1])), 3)

    def test_female_baseline_normalized_cardinals_share_scale_and_anchor(self) -> None:
        self.assert_transparent_png(
            FEMALE_BASE_REFERENCE,
            "female-base-96-grid-preview-v1.png",
            (192, 192),
        )
        bounds = self.assert_normalized_cardinals(
            FEMALE_BASE_REFERENCE,
            "cardinal-96-v1",
            66,
        )
        widths = [right - left for left, _top, right, _bottom in bounds.values()]
        self.assertLessEqual(max(widths) - min(widths), 1)


class CharacterKeyposeImporterTests(unittest.TestCase):
    def test_checker_import_keeps_enclosed_costume_lights_and_removes_neighbor_debris(self) -> None:
        board = Image.new("RGB", (200, 100), (248, 248, 248))
        draw = ImageDraw.Draw(board)
        for x in range(0, 200, 10):
            for y in range(0, 100, 10):
                if (x // 10 + y // 10) % 2:
                    draw.rectangle((x, y, x + 9, y + 9), fill=(255, 255, 255))
        draw.rectangle((28, 18, 72, 84), fill=(24, 30, 44))
        draw.rectangle((42, 35, 58, 55), fill=(245, 245, 240))
        draw.rectangle((96, 70, 99, 76), fill=(40, 90, 180))
        draw.rectangle((128, 18, 172, 84), fill=(24, 30, 44))
        draw.rectangle((142, 35, 158, 55), fill=(245, 245, 240))

        frames = normalize_board(board, columns=2, rows=1, background="checker")
        self.assertEqual(len(frames), 2)
        for frame in frames:
            self.assertEqual(frame.mode, "RGBA")
            self.assertEqual(frame.size, (96, 96))
            alpha_values = {value for _count, value in frame.getchannel("A").getcolors(maxcolors=256) or []}
            self.assertEqual(alpha_values.issubset({0, 255}), True)
            self.assertIsNotNone(frame.getchannel("A").getbbox())
        self.assertEqual(frames[0].getpixel((4, 84))[3], 0)

    def test_importer_refuses_to_overwrite_artist_frames(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "frames"
            frame = Image.new("RGBA", (96, 96))
            frame.putpixel((48, 84), (80, 160, 240, 255))
            write_frames([frame], output)
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                write_frames([frame], output)

    def test_importer_registers_shifted_board_cells_to_one_center(self) -> None:
        board = Image.new("RGB", (200, 100), (255, 0, 255))
        draw = ImageDraw.Draw(board)
        draw.rectangle((8, 20, 48, 88), fill=(24, 30, 44))
        draw.rectangle((148, 20, 188, 88), fill=(24, 30, 44))
        frames = normalize_board(
            board,
            columns=2,
            rows=1,
            background="magenta",
            silhouette_center_x=48,
        )
        centers = []
        for frame in frames:
            left, _top, right, _bottom = frame.getchannel("A").getbbox()
            centers.append((left + right - 1) / 2)
        self.assertLessEqual(max(centers) - min(centers), 0.5)
        self.assertTrue(all(abs(center - 48) <= 0.5 for center in centers))


if __name__ == "__main__":
    unittest.main()
