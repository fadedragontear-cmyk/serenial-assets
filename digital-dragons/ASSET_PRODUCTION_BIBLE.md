# Digital Dragon asset production bible

Asset version: `2026.07.25.1`

This document joins the mechanical progression bible, the runtime asset contract, and the art-direction documents into one production gate. It does not redefine mechanics.

## Readiness verdict

Asset production may proceed. The live game has stable breed keys, first-element hybrid affinity, level 1/30/50 Skill unlocks, five immutable Instincts per main breed, level-gated Command actions, cargo gathering and delivery, combat rewards, and a non-overlapping realtime world clock. Asset replacement is versioned and does not require a game-data migration.

| Area | Canon/live state | Asset consequence |
|---|---|---|
| Breed identity and stats | Canon and implemented | Elemental silhouettes and palettes can be refined without changing keys |
| Hybrid affinity | First listed/main element, implemented | Lead the design with the first element; integrate the second as anatomy/material/effect |
| Skills | Three per breed at levels 1, 30, 50 | Prepare three readable VFX families per breed; numbers remain UI text |
| Instincts | Five visible immutable instincts plus hidden low-HP safeguard | Use posture/emote tells, not separate dragon variants |
| Commands/gambits | Ten slots by level 100, actions level-gated | Icons must represent action intent and remain legible at Discord size |
| World movement | Autonomous roaming and explicit Explore are live | Terrain must communicate traversability and destination interest |
| Combat and cargo | Live | Entity/resource/treasure sprites may now be authored against stable states |
| Multi-stage authored objectives | TBD/content expansion | Do not block terrain or entity production; reserve overlay/icon space |
| Advanced enemy behavior visuals | TBD/content expansion | Start with neutral idle/hostile/defeated states and extend later |

## Runtime image contracts

- Portrait: 1024×1024 RGBA PNG.
- Profile and race: 512×512 RGBA PNG.
- Sprite cells: 32×32 RGBA, rows down/left/right/up.
- Idle and hurt: 4×4 cells.
- Walk, attack, cast, victory, defeat: 6×4 cells.
- World terrain: 32×32 cells, nearest-neighbor sampling, opaque base tile.
- Runtime keys and paths are immutable during refinement; replace files in place and bump `asset_version`.

## Dragon identity lock

Each dragon pack must preserve silhouette, horn count, eye color, chest marking, wing-finger structure, tail tip, palette anchors, and elemental material language across portrait, profile, race, and sprites.

Hybrids are one evolved species. The first/main element controls the dominant silhouette and affinity read. The second element changes anatomy, materials, markings, or effects; it is never presented as a selectable affinity and must not produce split-color symmetry.

## Review states

- `protected_reference`: approved reference identity; do not replace casually.
- `needs_consistency_review`: authored asset is live but needs a cross-format identity pass.
- `needs_manual_refinement`: procedural asset satisfies runtime contracts but is not final-quality approved.
- `first_import_review`: new asset family is integrated and ready for live visual review.

## Production order

1. World terrain atlas and Activity integration.
2. World entities: resources, treasure, enemies, bosses, lairs, markers.
3. Skill and combat VFX keyed to the three unlock tiers.
4. Main-element dragon consistency pass.
5. Hybrid manual refinement, portrait first, then profile/race, then sprites.
6. Discord-specific crops/icons after Activity assets establish the visual language.

## Acceptance checks

Reject assets with text, signatures, watermarks, franchise resemblance, cropped silhouette, concealed eyes/feet, accidental extra anatomy, inconsistent identity locks, broken sprite grids, blurry nearest-neighbor scaling, or terrain that hides roads, actors, objectives, or interaction states.
