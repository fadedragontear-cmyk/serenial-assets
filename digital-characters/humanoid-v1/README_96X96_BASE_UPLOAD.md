# Serenial Tavern 96×96 base-character upload slots

This is the active **base-character motion test** format for the Grand Hall / Tavern.

For this phase, use only the two bald body bases:

- `female-base-a`
- `male-base-a`

Do not add separate hair, eye, shirt, pants, shoe, lineage, or accessory layers yet. Those come after both body bases are loading, facing, walking, and running correctly.

## Runtime files

Each body uses exactly these three PNG files inside its `runtime/` folder:

| File | Cell size | Grid | Final sheet size | Rows |
| --- | --- | --- | --- | --- |
| `idle.png` | 96×96 | 4 columns × 4 rows | 384×384 | down, left, right, up |
| `walk.png` | 96×96 | 8 columns × 4 rows | 768×384 | down, left, right, up |
| `run.png` | 96×96 | 8 columns × 4 rows | 768×384 | down, left, right, up |

Shared runtime contract:

- RGBA PNG with genuine transparency.
- Every frame is exactly 96×96.
- Ground anchor is `(48, 84)` in every frame.
- Direction row order is `down`, `left`, `right`, `up`.
- Keep the character centered around the shared anchor; do not shift the whole character between frames.
- Nearest-neighbor rendering is expected.
- `idle`: 4 frames at 4 FPS.
- `walk`: 8 frames at 10 FPS.
- `run`: 8 frames at 14 FPS.

## Female upload path

Replace the existing body sheets here:

```text
digital-characters/humanoid-v1/female-base-a/runtime/idle.png
digital-characters/humanoid-v1/female-base-a/runtime/walk.png
digital-characters/humanoid-v1/female-base-a/runtime/run.png
```

Do not rename `sprite.json`.

## Male upload path

Upload the matching male sheets here using the exact same filenames:

```text
digital-characters/humanoid-v1/male-base-a/runtime/idle.png
digital-characters/humanoid-v1/male-base-a/runtime/walk.png
digital-characters/humanoid-v1/male-base-a/runtime/run.png
```

The male `character.json` and `runtime/sprite.json` are already prepared for the same 96×96 contract.

## Current goal

The acceptance test for this stage is deliberately narrow:

1. Female body loads.
2. Male body loads.
3. Each faces down/left/right/up correctly.
4. Idle cycles without position drift.
5. Walk cycles without obvious foot sliding or frame jumps.
6. Run cycles without obvious foot sliding or frame jumps.
7. Switching Female/Male changes the actual body sheet.

Only after that passes should hair and eye layers be added.
