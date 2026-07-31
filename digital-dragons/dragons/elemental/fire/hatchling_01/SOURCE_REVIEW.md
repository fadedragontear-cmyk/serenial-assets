# Fire Hatchling Canary Asset Review — Replacement Pass

## Outcome

The second supplied Fire Hatchling animation set is materially stronger than the first canary and replaces it as the active staged Fire Whelp sprite source.

The raw 1536×1024 uploads were still presentation/contact sheets rather than exact runtime atlases. They were repacked into a new versioned runtime directory instead of being committed unchanged.

## Source mapping

The seven supplied images were classified as:

1. Victory
2. Defeat
3. Hurt
4. Walk
5. Attack
6. Cast
7. Idle

## Active runtime contract

- compact source cell size: 48×48 for this staged canary;
- direction rows: Down, Left, Right, Up;
- Idle and Hurt: 4 frames × 4 rows;
- Walk, Attack, Cast, Victory, and Defeat: 6 frames × 4 rows;
- transparent RGBA output;
- linear filtering;
- ground anchor: `(24, 45)`.

The active staged path is now `hatchling_01/sprites_v2/`. The original `sprites/` canary remains in the repository only as rollback/reference material and is no longer selected by `visual-stages.json`.

A 128×128-cell master repack was also used for visual QA. The compact sheets are the runtime canary export; final production art should return to the 128×128 masters after manual shadow, direction, and animation cleanup.

## Repacking decisions

- Idle, Hurt, and Victory were generated as direction columns with motion progression across rows. Individual figures were component-cropped, normalized, and rearranged into directional runtime rows.
- Walk was remapped to Down, Left, Right, Up using the closest authored rows.
- Attack and Cast retain their four supplied rows and were normalized into exact cells.
- Cast supplied five frames per direction; frame six returns to the opening pose.
- Defeat supplied five frames per direction; frame six holds the final grounded pose.
- The supplied Defeat right-facing row was unreliable, so it is mirrored from the left-facing row.

## Remaining limitations

- Some Down movement/action poses remain three-quarter rather than perfectly frontal.
- Walk has more readable motion than the previous canary but still lacks strong foot articulation.
- Generated contact shadows remain baked into the artwork.
- Flame volume and brightness vary between Attack and Cast frames.
- Defeat Right is mirrored.
- The asset remains a runtime canary, not final approved production art.

## Approval status

- Character identity: improved and coherent
- Exact dimensions and frame counts: pass
- Direction-row contract: pass with documented approximations
- Transparency: pass
- Runtime replacement readiness: pass
- Final art approval: pending in-world inspection
