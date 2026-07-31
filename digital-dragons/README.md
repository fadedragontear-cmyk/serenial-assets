# Digital Dragon runtime assets

Asset version: `2026.07.25.2`

Dragon art follows the Digital Dragon Universe taxonomy instead of the retired named roster.

## Production guides

- [Dragon Sprite Contract v2](DRAGON_SPRITE_CONTRACT_V2.md): exact high-resolution cell grids, directions, anchors, safe margins, active animations, evolution stages, body plans, transparency rules, and QA gates.
- [Image Generation Hatchling Guide](IMAGE_GENERATION_HATCHLING_GUIDE.md): copy-ready prompting instructions, negative constraints, animation motion plans, element morphology, hatch-flow production, and deterministic sheet assembly.
- [Sprite v2 metadata template](templates/sprite-v2.example.json): schema-ready metadata for new packs.
- [Evolution visual registry](visual-stages.json): stage-aware keys with canonical-asset fallback until each requested pack is registered.

These documents are authoritative for the current hatchling production pass.

## Runtime structure

- `dragons/elemental/<element>/variant_XX/` for ordinary elemental variants.
- `dragons/hybrids/<element-pair>/variant_XX/` for hybrid variants.
- `dragons/unique/celdra/` for Celdra alone.
- Every existing runtime pack contains portrait, profile, race, seven animation sheets, and sprite metadata.
- Personal dragon names belong to owned dragons in the database; they never determine asset paths.

The manifest temporarily retains explicit aliases for retired asset keys so an older deployed Celdra can survive the coordinated database/code migration. No legacy-named dragon directories remain.

## Image contract

Shared identity art remains:

- `portrait.png`: 1024×1024 RGBA PNG.
- `profile.png` and `race.png`: 512×512 RGBA PNG.

Legacy sprite packs remain valid with 32×32 cells. Contract-v2 packs should use 128×128 source cells and may use other documented square source sizes from 64 through 256 pixels.

All world sheets retain the exact row order:

1. down;
2. left;
3. right;
4. up.

Active frame counts remain:

- `idle` and `hurt`: 4 columns × 4 rows;
- `walk`, `attack`, `cast`, `victory`, and `defeat`: 6 columns × 4 rows.

New high-resolution packs must follow the anchor and clipping requirements in `DRAGON_SPRITE_CONTRACT_V2.md`. Larger source cells improve quality and safety padding; they do not change the one-tile gameplay footprint.

Celdra's art is intentionally never used as an elemental or hybrid fallback.

## Evolution visuals

Visual stages follow shared progression:

- Whelp: levels 1–9;
- Drake: levels 10–29;
- Mature: levels 30–49;
- Adult: levels 50–69;
- Elder: level 70+.

`visual-stages.json` reserves ordinary Whelp keys for all ten elements. A requested stage activates only after its key exists in `manifest.json`; otherwise Dragon World retains the canonical species asset as a deliberate placeholder.

Unique dragons and hybrids require explicit overrides and do not inherit ordinary elemental stage art automatically.

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
