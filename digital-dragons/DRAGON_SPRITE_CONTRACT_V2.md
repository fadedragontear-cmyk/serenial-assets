# Serenial Dragon Sprite Contract v2

## Runtime compatibility

Contract v2 is additive. Legacy 32×32 packs remain valid. New packs should use 128×128 source cells unless a production lead approves another square size.

Supported source-cell sizes:

- 32×32 legacy;
- 64×64;
- 96×96;
- 128×128 recommended;
- 160×160;
- 192×192;
- 256×256.

The logical world footprint remains one tile. Larger source cells provide detail and transparent safety padding; they do not make the dragon occupy more terrain.

## Required pack layout

```text
<asset-key>/
├── portrait.png
├── profile.png
├── race.png
└── sprites/
    ├── sprite.json
    ├── idle.png
    ├── walk.png
    ├── attack.png
    ├── cast.png
    ├── hurt.png
    ├── victory.png
    └── defeat.png
```

Reserved files may be added now for future activation:

```text
gather.png
carry_idle.png
carry_walk.png
deposit.png
rest.png
guard.png
takeoff.png
flight.png
land.png
hatch.png
```

## Direction rows

Every world animation sheet uses exactly four rows in this order:

1. down;
2. left;
3. right;
4. up.

Do not rotate or reorder rows between animations. Left and right may be independently authored; do not assume mirroring is acceptable for asymmetric markings, equipment, horns, injuries, or elemental effects.

## Active frame counts

| File | Columns | Rows | Recommended FPS | Loop |
|---|---:|---:|---:|---|
| idle.png | 4 | 4 | 4 | yes |
| walk.png | 6 | 4 | 8 | yes |
| attack.png | 6 | 4 | 10 | no |
| cast.png | 6 | 4 | 10 | no |
| hurt.png | 4 | 4 | 8 | no |
| victory.png | 6 | 4 | 6 | yes |
| defeat.png | 6 | 4 | 6 | no; hold-safe final frame |

For 128×128 cells, the expected PNG sizes are:

| File | Pixel dimensions |
|---|---:|
| idle.png | 512×512 |
| walk.png | 768×512 |
| attack.png | 768×512 |
| cast.png | 768×512 |
| hurt.png | 512×512 |
| victory.png | 768×512 |
| defeat.png | 768×512 |

## Anchor

For a 128×128 cell, use the shared anchor:

- horizontal center: `x = 64`;
- ground or hover center: `y = 104`.

Scale anchors proportionally for other cell sizes.

The contact point, projected center, or hover center must remain stable across all directions and frames. The Activity supplies the shadow and selection ring.

## Safe area

For ordinary poses, keep at least 8 transparent pixels between every visible pixel and the cell boundary. For attack, cast, victory, and defeat extremes, keep at least 4 pixels.

The following may never be clipped:

- horns;
- ears;
- toes and claws;
- wing tips;
- fins;
- tail tips;
- raised head;
- elemental crests;
- cast particles;
- defeated body extensions.

Do not crop artwork tightly and then stretch it into the cell. Compose the anatomy inside the shared safe area.

## Body plans

All body plans use the same cell and anchor contract.

| Element | Body plan | Required silhouette behavior |
|---|---|---|
| Fire | grounded | compact, forceful quadruped; readable ember crest |
| Water | serpentine | elongated aquatic body curved through the cell; never horizontally compressed |
| Wind | airborne | clearly flying or hovering; feet are not treated as the primary ground contact |
| Earth | grounded | broad, heavy, low center of mass; stone plating remains readable |
| Ice | grounded | nimble crystalline quadruped; spikes remain inside safe area |
| Storm | grounded | athletic, charged silhouette; electricity cannot replace readable anatomy |
| Light | floating | luminous but fully readable body; highlights must not erase edges |
| Shadow | floating | dark but separated from transparent background; silhouette cannot collapse into black |
| Aether | floating | arcane/cosmic features with stable anatomy and controlled particles |
| Neutral | generalist | classic young dragon silhouette without dominant elemental mutation |

## Transparency and review backgrounds

Runtime files must be true RGBA PNGs with transparent backgrounds.

Forbidden in runtime files:

- green screen;
- checkerboard baked into pixels;
- white matte;
- black matte;
- halo from automatic background removal;
- terrain;
- cast shadow;
- labels or frame numbers;
- grid lines.

A separate green-background review export may be delivered, but it must never be referenced by `manifest.json` or `sprite.json`.

## Visual consistency

A pack must maintain the same dragon identity across:

- portrait;
- profile;
- race art;
- every direction;
- every animation;
- every frame.

Lock these traits before animation production:

- skull shape;
- muzzle length;
- eye color and placement;
- horn count, shape, and angle;
- ear or fin shape;
- wing construction;
- limb proportions;
- tail length and tip;
- scale pattern;
- elemental markings;
- palette;
- age and apparent body mass.

Do not regenerate each frame from a text prompt alone. Use an approved reference sheet and prior approved frames as image references for every generation step.

## Evolution stages

Runtime stages are:

- whelp: levels 1–9;
- drake: levels 10–29;
- mature: levels 30–49;
- adult: levels 50–69;
- elder: level 70+.

New hatchlings use keys such as `hatchling_fire_01`. They become active only after:

1. the full pack exists;
2. the pack is registered in `manifest.json`;
3. `visual-stages.json` points the relevant stage to that key;
4. runtime QA passes.

Until then, Dragon World uses the canonical species sprite as the placeholder.

Unique dragons and hybrids require explicit stage mappings. They do not automatically inherit the ordinary elemental hatchling.

## sprite.json v2 template

```json
{
  "schema_version": 2,
  "contract_version": "serenial-sprite-source-v2",
  "frame_width": 128,
  "frame_height": 128,
  "anchor": {"x": 64, "y": 104},
  "body_plan": "grounded",
  "direction_rows": ["down", "left", "right", "up"],
  "render_filter": "linear",
  "animations": {
    "idle": {"file": "idle.png", "frames": 4, "fps": 4, "loop": true},
    "walk": {"file": "walk.png", "frames": 6, "fps": 8, "loop": true},
    "attack": {"file": "attack.png", "frames": 6, "fps": 10, "loop": false, "next": "idle"},
    "cast": {"file": "cast.png", "frames": 6, "fps": 10, "loop": false, "next": "idle"},
    "hurt": {"file": "hurt.png", "frames": 4, "fps": 8, "loop": false, "next": "idle"},
    "victory": {"file": "victory.png", "frames": 6, "fps": 6, "loop": true},
    "defeat": {"file": "defeat.png", "frames": 6, "fps": 6, "loop": false, "hold_last_frame": true}
  }
}
```

The runtime currently reads the PNG grid while preserving the metadata for the next animation-state-machine pass. Do not deviate from the active frame counts without a coordinated runtime change.

## Required QA previews

Every delivery must include review composites showing:

- all four idle directions;
- all four travel directions;
- the most extreme frame from attack, cast, victory, and defeat;
- transparent checkerboard preview;
- temporary green-background preview;
- one-times-size preview;
- close-camera preview;
- six-actor group preview on representative Dragon World terrain.

A technically valid sheet is not automatically visually approved.
