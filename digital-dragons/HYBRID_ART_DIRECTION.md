# Hybrid art direction and prompt workflow

## Production target

Hybrid dragons must read as a single evolved species, not two recolored halves. Each pair needs a locked silhouette, horn count, eye color, chest marking, wing-finger structure, and tail tip that remain consistent across portrait, profile, race, and sprites.

## Runtime image contract

- Portrait: 1024×1024 RGBA PNG.
- Profile and race: 512×512 RGBA PNG.
- Sprite cells: 32×32 RGBA, rows down/left/right/up.
- Idle and hurt: 4×4 cells.
- Walk, attack, cast, victory, defeat: 6×4 cells.

## Future generation workflow

1. Open the pair's `prompt.json` and use `master_prompt` plus the relevant asset prompt.
2. Generate the portrait first. Treat it as the identity reference for all later outputs.
3. Generate profile and race with the portrait supplied as a character reference where the tool supports it.
4. Build sprites from the approved profile silhouette, preserving palette and unique anatomy.
5. Replace files in place without changing runtime keys. Run the asset audit before merge.

## Rejection criteria

Reject outputs with split-color symmetry, generic recolors, inconsistent horn/wing/tail anatomy, missing feet, concealed eyes, cropped silhouette, text, signatures, watermarks, franchise resemblance, or sprite cells that break the required grid.
