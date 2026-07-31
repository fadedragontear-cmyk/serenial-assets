# Fire Hatchling Canary Asset Review

## Source classification

The ten supplied generation outputs were not named. They were classified as follows:

1. portrait hero art
2. profile side art
3. race/action art
4. directional turnaround reference
5. rest/settle reference; not used as an active runtime animation
6. idle-like directional sequence, reused as the interim Idle and Walk source
7. fire-breath Attack sequence
8. charged-flame Cast sequence
9. Victory sequence
10. Defeat sequence

No dedicated Hurt sequence was supplied.

## Runtime adjustments

The active canary pack was rebuilt into the exact sprite-v2 contract:

- 128×128 source cells;
- direction rows: down, left, right, up;
- Idle and Hurt: four frames;
- Walk, Attack, Cast, Victory, and Defeat: six frames;
- transparent RGBA output;
- linear filtering metadata.

The generated sheets did not provide reliable right-facing animation rows. Right-facing rows are therefore mirrored from the left-facing rows. This is acceptable for this symmetrical hatchling canary, but future dragons with asymmetric markings, equipment, injuries, or directional VFX require authored right-facing frames.

Walk was generated with almost no leg articulation. Small positional offsets were added only to make movement readable during runtime testing. It remains below final animation quality.

Hurt was absent. The canary Hurt sequence is synthesized from Idle poses using recoil, compression, and recovery transforms.

The source contact sheets also included baked contact shadows and frame-to-frame bleed. The canary sheets were cropped, centered, downsampled, and cleaned to remove the worst neighboring-frame fragments. Baked shadows remain and must be removed in final authored replacements.

## Approval status

- Runtime contract: pass
- Direction coverage: pass with mirrored Right
- Frame dimensions/counts: pass
- Transparency: pass
- Character identity: acceptable for canary
- Walk articulation: fail for final production
- Hurt authorship: placeholder only
- Baked shadow removal: required before final production
- Defeat Up direction: partially side-on during collapse
- Final art approval: not granted

This pack is intentionally marked `runtime_canary_only`. It exists to test the high-resolution renderer, evolution-stage selection, scaling, caching, and ordinary world readability before another generation pass.
