# Digital Dragon runtime assets

Asset version: `2026.07.22.1`

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
