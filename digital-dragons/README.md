# Digital Dragon runtime assets

Asset version: `2026.07.25.2`

Dragon art now follows the Digital Dragon Universe taxonomy instead of the retired named roster.

## Runtime structure

- `dragons/elemental/<element>/variant_XX/` for ordinary elemental variants.
- `dragons/hybrids/<element-pair>/variant_XX/` for hybrid variants.
- `dragons/unique/celdra/` for Celdra alone.
- Every runtime pack contains portrait, profile, race, seven 32×32 sprite sheets, and sprite metadata.
- Personal dragon names belong to owned dragons in the database; they never determine asset paths.

The manifest temporarily retains explicit aliases for retired asset keys so an older deployed Celdra can survive the coordinated database/code migration. No legacy-named dragon directories remain.

## Image contract

- `portrait.png`: 1024×1024 RGBA PNG.
- `profile.png` and `race.png`: 512×512 RGBA PNG.
- Sprite cells: 32×32 RGBA PNG in down, left, right, up rows.
- `idle` and `hurt`: 4 columns × 4 rows.
- `walk`, `attack`, `cast`, `victory`, and `defeat`: 6 columns × 4 rows.

Celdra's art is intentionally never used as an elemental or hybrid fallback.

## Hybrid art coverage

All 45 canonical two-element pairs have runtime packs. The 39 coverage-expansion packs are runtime-valid procedural V2 assets and are queued for manual identity refinement; six historical packs are queued for consistency review. Exact-duplicate and image-contract checks pass.

## Prompt sidecars

Every canonical hybrid `variant_01` directory includes `prompt.json`. The aggregate prompt library is `hybrid-prompt-library.json`; it records identity locks, palette, negative prompts, and portrait/profile/race/sprite prompts for future manual or model-assisted revisions.


## World terrain

`world_tiles.serenial_terrain_v1` is the first versioned world atlas: 20 terrain families, four stable variants each, and 32×32 nearest-neighbor cells. The atlas supplies the Activity base terrain; roads, lairs, resources, actors, fog, and labels stay separate so mechanics remain readable.

## Art approval language

`art_status` records provenance and runtime fitness. `review_status` records whether a human art pass is still expected. “Production procedural” means contract-valid and shippable as an interim asset, not final visual approval.

## World entities

`world_entities.serenial_entities_v1` is the first versioned overlay atlas for the shared world and guild HUD. Its 16 transparent 32×32 cells cover the guild crest, all ten elemental resources, treasure, boss relics, blueprints, enemies, and bosses. Entity overlays remain separate from terrain so future art can be replaced without changing simulation coordinates.
