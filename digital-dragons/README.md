# Digital Dragon runtime assets

Asset version: `2026.07.20.1`

This directory follows Celdra's requested runtime structure exactly. All runtime filenames are lowercase ASCII with underscores.

## Included

- 11 functional item icons at 256×256.
- 53 seeded dragon directories with portrait, profile, race art, seven 32×32 sprite sheets, and sprite metadata.
- Persistent navigation/status UI.
- Modular equipment slots, tier frames, and ten element overlays.
- Racing background, lane, gate, finish, status, event, podium, reward, and ticket assets.
- Five-frame egg hatch sequence, horizontal hatch sheet, result badges, reveal rings, particles, fragments, and swirls.
- 42 Discord application emoji PNG files at 128×128, each named exactly as requested.
- Source reference sheets and recreation prompts.

## Important implementation note

The 32×32 sheets are bootstrap runtime sprites generated from each species' approved race illustration. They meet the exact sheet/cell/direction/metadata contract and are suitable for integration testing. A later hand-pixelled pass can replace them without changing paths or metadata.

The dragon race illustrations are the current approved species concepts. Portraits and profiles are generated from the same species art to maintain identity consistency.
