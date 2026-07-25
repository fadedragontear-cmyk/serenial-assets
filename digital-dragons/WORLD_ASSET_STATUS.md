# World asset status

Asset version: `2026.07.25.1`

## Imported

| Runtime key | Contract | Coverage | Status |
|---|---|---|---|
| `serenial_terrain_v1` | 320×256 PNG atlas; 32×32 cells | 20 terrain families × 4 variants | First import review |

Terrain families: `ocean`, `coast`, `river`, `lair`, `road`, `grass`, `forest`, `earth`, `water`, `mountain`, `windstream`, `lava`, `cliff`, `icefield`, `stormfield`, `lightfield`, `shadowfen`, `aetherfield`, `neutralfield`, `ruins`.

The atlas is terrain-major then variant. Cell index is `terrain_index * 4 + variant`; columns are 10. Variant selection must be stable for a world seed and coordinate so tiles do not shimmer between refreshes.

## Still queued

1. Resource-node and treasure sprites.
2. Enemy and boss state sprites.
3. Lair and destination overlays.
4. Skill and combat VFX.
5. Weather/ambient overlays.

These are asset-content tasks, not blockers in the mechanical model.
