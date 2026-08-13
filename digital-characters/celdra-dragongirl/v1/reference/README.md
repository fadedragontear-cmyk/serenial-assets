# Celdra dragongirl form v1 reference

This folder establishes Celdra's primary tavern actor: `celdra-dragongirl-v1`. It corrects the earlier assumption that the small crystalline dragon would be her main playable form.

## Production v1 files

- `../character.json` — the approved 96 x 96 runtime contract and animation timing.
- `../frames/` — 80 individually editable RGBA source frames: four directions x
  4 idle, 8 walk, and 8 run frames.
- `../runtime/idle.png`, `walk.png`, and `run.png` — generated atlases; do not edit
  these directly.
- `previews/*-all-directions-v1.gif` — nearest-neighbor visual proofs of every
  direction and required action.

The first left-facing animation set is an explicitly recorded, reviewed mirror of
the right-facing set. This keeps the first production loop coherent. A later hand
pass can restore fixed-side hair asymmetry without changing filenames, timing, or
runtime APIs.

## Reference files

- `celdra-dragongirl-cardinal-master-candidate-v2.png` — current high-resolution adult female four-direction identity master with true RGBA transparency.
- `cardinal-96-v2/*.png` — current four normalized 96 x 96 direction references, each with a 70-pixel visible height and y=84 ground contact.
- `celdra-dragongirl-96-grid-preview-v2.png` — the current four gameplay-scale direction references in one review grid.
- `tavern-scale-proof-v2.png` — the current front frame composited at its intended size on the tavern canvas.

The `*-v1` cardinal and idle files remain only as an audit trail for the superseded first design. They must not be promoted into `frames/` or used to produce new animation because their identity and costume predate the approved female design correction. The next `idle/down` pass starts from the v2 master.

The cardinal and idle candidates preserve the canonical source facts that Celdra is an AI dragongirl with blue hair and the caretaker of the Serenial Tavern. Her dragon traits are derived from the existing small crystalline dragon identity rather than from a commercial character.

## Identity lock

- adult female blue-haired dragongirl and tavern caretaker;
- shoulder-length layered hair with long side locks and a narrow tied lock;
- sapphire-to-cyan eyes;
- two small translucent blue crystal horn/crest pieces;
- compact cobalt-framed lavender-purple wings;
- ice-blue tail with crystalline blue tip;
- restrained forearm and cheek/temple scale accents;
- high-collar indigo and ivory caretaker tunic with split long panels over opaque leggings, muted-gold trim, and flat brown travel boots;
- one consistent face, hair mass, proportions, horns, wings, tail, clothing construction, palette, and ground anchor in every view.

The small dragon remains a separate `celdra-dragon-v1` alternate/companion model.

## QA status

The v2 master and normalized direction references have true binary transparency. All four gameplay views are exactly 70 visible pixels tall and end on y=84. The front, right, left, and back silhouettes are 51, 39, 39, and 49 pixels wide. Every visible pixel remains inside the production safe bounds and each normalized frame uses no more than 64 visible RGB colors.

The reference masters remain visual guidance rather than runtime inputs. The 80
PNGs in `../frames/` are now the editable source of truth. Every production frame
has binary transparency, stays inside the safe bounds, and uses at most 96 visible
colors; the runtime atlas is rebuilt and checked from those sources. The horizontal
silhouette registration is locked per direction so the body remains planted on the
same world origin instead of inheriting generated board-cell drift. The recorded
left-facing derivation is also verified as an exact mirror of the corrected right set.
