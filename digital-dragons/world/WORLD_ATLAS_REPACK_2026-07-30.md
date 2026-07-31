# Dragon World Atlas Repack — 2026-07-30

## Outcome

The supplied terrain and entity images were presentation sheets rather than drop-in runtime atlases. They have been repacked into the existing Dragon World v1 contracts so the Activity does not require coordinate or simulation changes.

## Active runtime outputs

- `tiles/serenial_terrain_v1.png`: 320×256 PNG, 10 columns × 8 rows, 32×32 cells.
- `entities/serenial_entities_v1.png`: 256×64 transparent PNG, 8 columns × 2 rows, 32×32 cells.

The stable runtime keys and paths are retained. Existing terrain IDs, entity IDs, world coordinates, spawn behavior, fog, movement costs, and gameplay effects are unchanged.

## Terrain conversion

The supplied terrain image was a 12×6 presentation grid with unequal source-cell boundaries and a varying number of examples per family. It could not be sampled directly by the fixed runtime grid.

The active atlas is ordered exactly as required:

1. ocean
2. coast
3. river
4. lair
5. road
6. grass
7. forest
8. earth
9. water
10. mountain
11. windstream
12. lava
13. cliff
14. icefield
15. stormfield
16. lightfield
17. shadowfen
18. aetherfield
19. neutralfield
20. ruins

Each family occupies four consecutive cells. When the source provided at least four examples, four authored examples were retained. When it provided only three, the fourth cell was produced deterministically from the closest authored variant rather than inventing a new terrain identity. Source seams were removed before downsampling.

The internal detail was reduced for legibility and compression at the actual 32×32 runtime scale. The family ordering, cell count, and atlas dimensions remain identical to v1.

## Entity conversion

The supplied entity image visually used an 8×2 layout but did not match the active slot order. It also contained two herb-like icons and no separate boss-relic icon.

The repack restores this exact order:

1. guild crest
2. ember bloom
3. gale plume
4. tidal pearl
5. stoneheart ore
6. frost lotus
7. stormglass
8. sunshard
9. umbral morel
10. aether crystal
11. wayfarer herb
12. treasure cache
13. boss relic
14. blueprint
15. enemy
16. boss

The duplicate herb is not used in the active atlas. Slot 13 contains an interim boss relic assembled from the supplied aether-crystal and crowned-boss visual language. It should receive a dedicated authored replacement during the next entity-art pass, but it is distinct and runtime-safe now.

## Deployment

Because the public paths remain unchanged, merge this asset change and then redeploy Celdra-Cloud or clear its Digital Dragon asset cache. Existing browser sessions may require a hard refresh while the previous one-hour HTTP cache expires.

## QA checklist

- verify ocean, coast, river, and water appear in the correct world regions;
- verify lair tiles remain recognizable under dragon and selection overlays;
- verify all ten elemental resource icons match their HUD and world elements;
- verify treasure, boss relic, blueprint, enemy, and boss use distinct slots;
- inspect 6-, 14-, and 28-tile camera views;
- confirm procedural fallbacks still appear if an atlas request fails.
