# Hybrid asset completion status

Asset version: `2026.07.22.2`

- Canonical element count: 10
- Order-insensitive hybrid pairs: 45
- Previously represented pairs: 6
- Newly completed pairs: 39
- Total hybrid runtime packs: 50

## Bootstrap policy

The newly completed pairs reuse the validated `fire-ice/variant_01` image and sprite blobs. This preserves the exact image dimensions, transparency, animation layout, and current visual language while making every pair addressable immediately.

Each new manifest entry is marked:

```json
{"art_status":"bootstrap_shared","source_template":"hybrid_fire_ice_01"}
```

Replace these assets with pair-specific final art without changing paths, keys, dimensions, or sprite metadata.

## Newly completed pairs

- `fire-wind`
- `fire-water`
- `fire-earth`
- `fire-light`
- `fire-aether`
- `fire-neutral`
- `wind-water`
- `wind-earth`
- `wind-ice`
- `wind-light`
- `wind-aether`
- `wind-neutral`
- `water-earth`
- `water-ice`
- `water-storm`
- `water-light`
- `water-shadow`
- `water-aether`
- `water-neutral`
- `earth-ice`
- `earth-storm`
- `earth-light`
- `earth-shadow`
- `earth-aether`
- `earth-neutral`
- `ice-storm`
- `ice-light`
- `ice-shadow`
- `ice-aether`
- `ice-neutral`
- `storm-light`
- `storm-aether`
- `storm-neutral`
- `light-shadow`
- `light-aether`
- `light-neutral`
- `shadow-aether`
- `shadow-neutral`
- `aether-neutral`
