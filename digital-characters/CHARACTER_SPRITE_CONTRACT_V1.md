# Serenial character sprite contract v1

Status: proposed production contract

This contract replaces code-drawn tavern avatars with original, editable, anime-influenced pixel art. It targets the clarity and expressive motion of polished 16-bit-era JRPGs without copying commercial characters, frames, palettes, or animation timing.

## Canonical cell

Every character and paper-doll layer uses `serenial-character-atlas-v2`:

- 96 x 96 transparent RGBA pixels per frame;
- ground anchor at x 48, y 84;
- safe visible bounds from x 4 through 91 and y 4 through 87;
- direction rows ordered down, left, right, up;
- nearest-neighbor rendering;
- explicit direction provenance in `character.json`; a reviewed mirror is allowed for a
  symmetric first-pass animation set, while intentionally handed hair, clothing, and
  accessories require original left/right art before approval;
- no baked checkerboard, matte, label, grid, shadow, glow, or background;
- unchanged transparent padding and anchor across all directions and actions.

Characters with wide directional features such as tails may declare a per-direction
`registration.visible_bounds_center_x` in `character.json`. This value is not a second
runtime origin: it is an automated source-frame registration gate chosen so the body
root remains on the canonical `(48, 84)` anchor while asymmetric tails and wings remain
clear of it. Every frame in that direction must retain the declared visible-bounds
center within the stated tolerance. Celdra uses `48 / 59 / 36 / 48` for
down / left / right / up respectively.

The visible character does not need to fill the cell. Humanoid body cores normally occupy about 26 to 40 x 66 pixels; hair, clothing, and accessories may widen that silhouette. Celdra's dragongirl form targets about 39 to 51 x 70 pixels because her wings and tail need more silhouette room. Non-humanoid actors may use more horizontal space while sharing the same cell and ground anchor.

## Required actions

| Action | Frames per direction | Playback |
| --- | ---: | ---: |
| idle | 4 | 4 fps |
| walk | 8 | 10 fps |
| run | 8 | 14 fps |

Planned actions include `interact`, `talk`, `use`, `sit`, `carry`, `emote`, `hurt`, and `celebrate`. New actions may use another frame count but retain the cell, direction order, and anchor.

## Source and generated layout

```text
digital-characters/
  CHARACTER_SPRITE_CONTRACT_V1.md
  templates/
    serenial-character-96x96-guide.png
  celdra-dragongirl/v1/
    character.json
    reference/
      cardinal-master.png
      notes.md
    frames/
      idle/down/000.png ...
      idle/left/000.png ...
      walk/down/000.png ...
      run/down/000.png ...
    runtime/
      sprite.json
      idle.png
      walk.png
      run.png
  celdra-dragon/v1/
    character.json
    reference/...
    frames/...
    runtime/...
  humanoid-v1/
    body/female-base-a/
      character.json
      reference/...
      frames/...
      runtime/...
```

Individual PNGs under `frames/` are the source of truth. Artists edit them directly. `python tools/character_sprite_pipeline.py --root digital-characters --write` validates and packs those sources into `runtime/`. Generated atlases are never edited directly.

Reviewed key-pose boards can be converted into editable source frames with
`tools/import_character_keypose_board.py`. The importer removes only edge-connected
reference mattes, preserves enclosed light costume pixels, normalizes the common scale
and anchor, discards accidental board-cell x offsets, and refuses to overwrite an
existing frame directory. Use `--silhouette-center-x` when importing an asymmetric
direction. Existing frames can be idempotently corrected from the manifest with
`python tools/register_character_frames.py path/to/character.json --write`. Generate
four-direction review GIFs from those corrected sources with
`python tools/render_character_previews.py path/to/character.json path/to/reference/previews`.

Use `--check` to verify committed runtime outputs without rewriting them. The GitHub Action runs the same checks on every character-asset pull request.

## Custom player appearances

Humanoid customization uses aligned paper-doll layers. Every selected layer supplies the same action, direction, frame count, cell, and anchor as its body.

Draw order is:

1. runtime shadow;
2. back accessory;
3. back hair;
4. body and skin;
5. lower outfit;
6. upper outfit;
7. front hair;
8. headwear;
9. front accessory or held item.

Appearance records store reviewed asset keys and curated palette keys. Whole-sheet hue rotation is not allowed because it damages skin, outlines, highlights, and material separation. A later mask-based recoloring pass may reduce duplicated palette sheets.

The first supported player body key is `female-base-a`: a clearly adult female baseline with a compact, neutral animation silhouette. It is the default body for the first customization vertical slice. Future body keys are additive choices; they do not replace or silently remap `female-base-a`. Hair and clothing remain independent aligned layers rather than being baked into the body identity.

The runtime composites selected layers once into an offscreen cache keyed by the normalized appearance record. Movement draws the cached result rather than redrawing every layer for every actor on every frame.

Celdra's primary tavern actor is the fixed unique adult female model `celdra-dragongirl-v1`, not a generic humanoid paper doll. Curated Celdra costumes may replace only clothing layers. Her face, blue hair, crystal horns and scale accents, wings, tail, proportions, palette, and anchor remain identity-locked.

The small crystalline dragon is a separate `celdra-dragon-v1` model. A future transformation switches complete actor models at a controlled state boundary; one animation never mixes humanoid and quadruped frames.

## Celdra identity lock

Every approved `celdra-dragongirl-v1` frame preserves:

- an adult female blue-haired dragongirl and Serenial Tavern caretaker;
- shoulder-length layered ice-blue and cobalt hair with long side locks and one narrow tied lock or braid;
- large sapphire-to-cyan eyes and a readable anime expression;
- two small translucent blue crystalline horn/crest pieces;
- compact cobalt-framed wings with lavender-purple membranes;
- one ice-blue tail with a compact crystalline tip;
- restrained ice-blue scale accents at the outer forearms and cheek/temple area;
- practical high-collar indigo and ivory caretaker clothing with a tailored waist, split long tunic panels over opaque leggings, muted-gold trim, and flat brown travel boots;
- one consistent scale, anatomy, palette, outfit construction, wing size, horn pair, and tail length in all directions.

`celdra-dragon-v1` preserves the separate small ice-blue and white crystalline dragon form, blue eyes, crest, tail tip, and compact purple wings.

The four neutral masters receive an overlay review before animation. Side views may reveal different details, but body length, stance, crest scale, and ground contact must remain consistent.

## Production sequence

1. Approve the identity reference and palette.
2. Draw four neutral masters on the 96 x 96 guide.
3. Overlay and correct those masters until scale and anatomy match.
4. Complete and approve `idle/down` from the current female Celdra master.
5. Extend idle to left, right, and up.
6. Complete walk one direction at a time, then run.
7. Hand-correct every generated or interpolated frame at 1x zoom.
8. Run the packer and commit both source frames and generated outputs.
9. Review at 1x, 2x, and actual Discord Activity scale.
10. Pin the approved asset commit in the Cloudflare proxy before runtime activation.

Image generation may assist with identity references and major key poses. It may not independently regenerate every animation frame from text. Each pose uses the approved master and neighboring approved frames as references; reviewed pixel art remains authoritative.

## Automated rejection gates

The pipeline rejects:

- a source frame that is not a 96 x 96 RGBA PNG;
- partial alpha instead of fully transparent or fully opaque source pixels;
- more than 96 visible RGB colors in one production frame;
- visible pixels outside the safe bounds;
- a missing, extra, or non-contiguous numbered frame;
- a missing required direction or action;
- a paper-doll layer whose action frame count differs;
- an unsafe asset or animation key;
- a stale generated sheet or metadata file;
- horizontal registration drift for a character that declares registration centers;
- a sheet with the wrong dimensions;
- an opaque background or baked checkerboard touching the frame edge.

Visual review is still required for silhouette consistency, motion arcs, expressions, costume clipping, directional correctness, and palette readability.

## Manual editing

Open an individual source PNG in Aseprite, Krita, GIMP, or another pixel editor. Use a 96 x 96 canvas, nearest-neighbor tools, and the supplied guide as a separate reference layer. Hide the guide before exporting the frame as RGBA PNG. Do not resize with smoothing.

After editing, run the packer. This keeps every correction small and reviewable instead of making one giant atlas the only editable source.

## Runtime approval boundary

The existence of a reference image or candidate folder never activates it. The first `signal-and-salt` integration must retain the procedural avatar as a loading/error fallback, load only revision-pinned allowlisted assets, never block movement while art downloads, and change no movement authority, persistence, or game-state behavior.
