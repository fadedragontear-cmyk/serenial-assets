# Female player baseline A reference

This folder establishes `female-base-a`, the first supported body key for `serenial-humanoid-v1`. It is a clearly adult female player baseline, separate from Celdra's unique dragongirl model.

## Candidate files

- `female-base-cardinal-candidate-v1.png` — cleaned high-resolution four-direction turnaround with true RGBA transparency.
- `cardinal-96-v1/*.png` — normalized gameplay-scale direction references.
- `female-base-96-grid-preview-v1.png` — all four normalized directions in one review grid.
- `character.example.json` — the required frame, anchor, direction, and animation metadata for the future body-layer pack.

## Production lock

- 96 x 96 RGBA cells with binary alpha;
- 66-pixel visible height in all four directions;
- y=84 ground contact and production safe bounds;
- authored down, left, right, and up views;
- compact adult female anime/JRPG presentation through face, hair, and practical clothing construction;
- ordinary humanoid design with no Celdra-specific horns, wings, scales, tail, markings, or palette lock;
- body, hair, upper outfit, lower outfit, footwear, and accessories separated into aligned layers before runtime use.

The combined turnaround is an approval and alignment reference. It is not permission to bake the shown hair and clothing into the production body layer. The current reductions use at most 64 visible RGB colors and are intended for manual 1x cleanup before animation.
