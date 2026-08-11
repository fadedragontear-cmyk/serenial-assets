# Digital Dragons — Hatchling Art Direction (August 2026)

## Purpose

This file turns the hand-edited hatchling idle work into the visual reference for the next production pass. The goal is to stop treating every animation sheet as an isolated art problem.

The runtime contract stays stable. Art can be replaced one animation family at a time without changing Dragon World code.

## Current visual reference

The strongest reference set is the manually revised `sprites_v2/idle.png` work committed after the baseline batch.

### Revised reference idles

- Light — `dragons/elemental/light/hatchling_01/sprites_v2/idle.png`
- Water — `dragons/elemental/water/hatchling_01/sprites_v2/idle.png`
- Ice — `dragons/elemental/ice/hatchling_01/sprites_v2/idle.png`
- Shadow — `dragons/elemental/shadow/hatchling_01/sprites_v2/idle.png`
- Wind — `dragons/elemental/wind/hatchling_01/sprites_v2/idle.png`
- Earth — `dragons/elemental/earth/hatchling_01/sprites_v2/idle.png`
- Storm — `dragons/elemental/storm/hatchling_01/sprites_v2/idle.png`

These were individually replaced on 2026-08-04 and should be treated as the clearest current statement of the desired hatchling look.

### Secondary reference

- Fire — `dragons/elemental/fire/hatchling_01/sprites_v2/idle.png`

Fire was manually replaced/reorganized on 2026-08-03 and remains useful, but the August 4 set should take precedence when resolving style conflicts.

### Still needs a dedicated idle style pass

- Aether — current idle is still the 2026-08-01 baseline batch.
- Neutral — current idle is still the 2026-08-01 baseline batch.

Do not automatically promote Aether or Neutral as style references until visually reviewed.

## Target visual language

The revised idles should guide future production:

- painterly/chunky JRPG creature rendering rather than tiny generic pixel-dragon shorthand;
- readable hatchling silhouette at gameplay scale;
- large expressive head/face and strong element identity;
- clean body contour with no accidental cloud/smoke noise around the silhouette;
- deliberate highlight and shadow grouping instead of grain/noise texture;
- saturated elemental color without clipping detail;
- consistent apparent scale between directions and animation families;
- feet, horns, wing tips, tails and ears must stay inside the frame padding;
- transparent background only in runtime art;
- no baked shadow unless the pack metadata explicitly requires one;
- no camera zoom changes between frames;
- no identity drift between idle, walk, attack, cast, hurt, victory and defeat.

## Runtime animation contract

Every production hatchling should ultimately provide:

| Animation | Directions | Frames | Goal |
|---|---:|---:|---|
| idle | 4 | 4 | breathing, blink, tiny tail/crest motion |
| walk | 4 | 6 | readable locomotion, no foot sliding |
| attack | 4 | 6 | physical strike / element-appropriate attack pose |
| cast | 4 | 6 | magical skill preparation/release |
| hurt | 4 | 4 | short readable impact reaction |
| victory | 4 | 6 | personality/reward beat |
| defeat | 4 | 6 | clear downed state, final frame safe to hold |

Direction row order remains:

1. down
2. left
3. right
4. up

Frame metadata, anchors and animation timing belong in `sprite.json`; gameplay code must not infer crop geometry from the artwork.

## Production order

### Phase A — finish the ten base hatchlings

1. Lock the August 4 idle references as the style target.
2. Bring Fire idle into the same polish level if needed.
3. Redesign/refine Aether idle to match the reference quality.
4. Refine Neutral idle.
5. For each base element, regenerate/restyle the remaining six animation families from that element's approved idle identity.
6. QA every sheet in the runtime viewer before marking it approved.

### Phase B — dual-element hatchlings

Do not solve hybrids by simple palette swapping.

Each hybrid should inherit:

- one primary body/silhouette idea;
- one secondary structural/detail influence;
- both elemental palettes/effects in controlled proportions;
- the same hatchling age/scale language as the elemental references.

The hybrid identity must remain readable when elemental VFX are removed. Effects should support the creature design, not hide it.

Production should prioritize combinations that already appear in the live dragon population, then fill the remaining pair matrix systematically.

### Phase C — transformations / later stages

Later forms should be derived from the approved hatchling identity rather than from older unrelated variant art.

For each transformation:

- preserve face/crest/horn/tail motifs that make the dragon recognizable;
- increase complexity and scale gradually;
- avoid turning every later form into the same generic adult dragon silhouette;
- keep the same direction/animation contract unless a new runtime contract is deliberately versioned.

## QA gate

A sheet is not production-ready until all of the following pass:

- transparent background is clean;
- no crop/cutoff in any frame;
- consistent body scale across all directions;
- correct row order;
- correct frame count;
- no unexpected matte/halo around transparency;
- no obvious generative grain/noise;
- no duplicated or missing limbs;
- no horn/toe/tail clipping;
- walk cycle does not visibly foot-slide;
- animation starts and ends in a pose compatible with idle when appropriate;
- attack/cast direction is readable from gameplay camera distance;
- defeat final frame can safely hold;
- visual identity matches the approved idle reference for that element.

## Asset status vocabulary

Use these labels in future manifests/review notes:

- `reference_idle` — manually reviewed idle currently defining the desired identity.
- `candidate` — new art awaiting runtime review.
- `approved` — passed visual/runtime QA.
- `legacy` — usable but not aligned with the current direction.
- `fallback` — intentionally temporary art used so the runtime does not break.
- `missing` — no viable production asset yet.

## Important rule

Do not overwrite a reviewed reference simply because a new generated sheet exists. New work should land as a candidate, be inspected in the real renderer, and only then replace the reference/runtime mapping.
