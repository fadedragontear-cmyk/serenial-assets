# Image Generation Guide — Dragon World Hatchlings

## Use this guide as the governing instruction

Give the image-generation assistant this file, the approved element reference images, and `DRAGON_SPRITE_CONTRACT_V2.md` before requesting production art.

The assistant must treat approved references as authoritative. It must not redesign the dragon between frames, directions, animations, or output types.

## Production objective

Create one coherent hatchling asset pack for each ordinary element:

- Fire;
- Water;
- Wind;
- Earth;
- Ice;
- Storm;
- Light;
- Shadow;
- Aether;
- Neutral.

Each pack represents the **Whelp evolution stage, levels 1–9**. It must feel young without becoming a plush toy, mascot, chibi caricature, or generic baby dragon.

The required visual standard is polished fantasy game art with clear anatomy, controlled detail, readable elemental identity, and strong consistency across all assets.

## Non-negotiable technical rules

1. Runtime sprites use true transparent RGBA backgrounds.
2. Source cells are 128×128 pixels.
3. Direction rows are down, left, right, up.
4. Ground or hover anchor is `(64, 104)` in every frame.
5. No horn, toe, wing, tail, fin, ear, crest, particle, or defeated limb may touch the crop boundary.
6. Maintain at least 8 transparent pixels around ordinary poses and 4 pixels around extreme poses.
7. Do not include shadows, terrain, labels, borders, grid lines, health bars, selection rings, UI, or text.
8. Do not bake a checkerboard or green background into runtime files.
9. Optional green-background copies are review exports only.
10. Keep the exact same individual dragon in every image.

## Required outputs per element

### High-resolution identity art

- `portrait.png`: 1024×1024 transparent portrait or full-body hero image;
- `profile.png`: 512×512 transparent inspection/profile image;
- `race.png`: 512×512 transparent side-facing race presentation;
- `model_sheet.png`: production reference showing front, left, right, rear, three-quarter, wing treatment, head close-up, tail tip, foot/claw construction, palette swatches, and elemental markings.

### Active world sheets

- `idle.png`: 512×512, 4 frames × 4 directions;
- `walk.png`: 768×512, 6 frames × 4 directions;
- `attack.png`: 768×512, 6 frames × 4 directions;
- `cast.png`: 768×512, 6 frames × 4 directions;
- `hurt.png`: 512×512, 4 frames × 4 directions;
- `victory.png`: 768×512, 6 frames × 4 directions;
- `defeat.png`: 768×512, 6 frames × 4 directions.

### Reserved animation sources

Prepare key poses or full sheets when feasible:

- gather;
- carry idle;
- carry travel;
- deposit;
- rest;
- guard;
- takeoff;
- flight;
- land;
- hatch sequence.

These may remain source/reference assets until the runtime state-machine pass activates them.

## Recommended workflow

### Phase 1 — Lock the dragon

Generate and approve one high-resolution model sheet before requesting animation frames.

The model sheet must settle:

- body plan;
- exact proportions;
- skull and muzzle;
- eye placement and color;
- horn count and geometry;
- ear, frill, or fin geometry;
- wing construction;
- limb length and joint placement;
- feet and claw count;
- tail length and tip;
- scale pattern;
- elemental markings;
- primary, secondary, highlight, shadow, eye, horn, and effect colors.

Do not proceed while any of these remain ambiguous.

### Phase 2 — Lock four neutral directions

Create one neutral idle pose in each direction. Compare them side by side.

Reject the set if:

- the head changes size;
- horn count changes;
- markings swap sides;
- wing size changes;
- tail length changes;
- legs change thickness;
- the dragon appears older or younger in one direction;
- up-facing anatomy becomes a different character;
- the top of the head, horns, or toes are cropped.

### Phase 3 — Produce key poses, not uncontrolled full sheets

For best quality, generate each important pose as an individual transparent image using the approved model sheet and previous approved pose as references. Assemble the exact grid deterministically afterward.

A full contact sheet may be generated for exploration, but it is not final until every cell is individually checked, aligned, cropped, and placed into the required grid.

### Phase 4 — Animate by controlled deltas

Each consecutive frame should change only what motion requires. Preserve all identity traits.

Good frame-to-frame changes:

- chest rise;
- head tilt;
- foot placement;
- wing beat;
- tail follow-through;
- controlled elemental pulse;
- recoil;
- weight shift.

Bad frame-to-frame changes:

- new horns;
- missing claws;
- different eye color;
- different face;
- changing scale pattern;
- random accessories;
- changing wing membrane shape;
- inconsistent lighting direction;
- anatomy melting into elemental effects.

### Phase 5 — Assemble and validate

Use a deterministic compositor or image editor to:

- resize each approved frame without distortion;
- center on the shared anchor;
- preserve transparent margins;
- place cells into exact rows and columns;
- export lossless RGBA PNG;
- verify dimensions and alpha;
- generate one-times-size and close-camera previews.

Image generation should create the art. It should not be trusted to guarantee exact pixel dimensions, identical cell spacing, or file naming without verification.

## Master prompt template

Replace bracketed fields. Attach the approved model sheet and prior approved frames as image references.

```text
Create production-quality game art for Serenial Dragon World.

SUBJECT
The exact same [ELEMENT] dragon hatchling shown in the attached approved reference sheet. This is the Whelp evolution stage, levels 1–9. Preserve the established skull, muzzle, eyes, horns, ears/fins, wings, limbs, claws, tail, markings, palette, apparent age, and body mass exactly.

BODY PLAN
[BODY PLAN REQUIREMENTS]

POSE AND DIRECTION
[ANIMATION NAME], frame [FRAME NUMBER] of [FRAME COUNT], facing [DOWN / LEFT / RIGHT / UP].
[MOTION DESCRIPTION FOR THIS FRAME]

CAMERA AND PRESENTATION
Orthographic three-quarter game-sprite camera consistent with the attached references. No perspective drift between frames. The dragon must remain centered over the same projected ground or hover anchor. Show complete anatomy with generous transparent safety space around horns, ears, toes, wing tips, fins, tail tip, elemental crest, and effects.

ART DIRECTION
Polished fantasy strategy-RPG creature art. Clean silhouette, deliberate anatomy, controlled texture, crisp readable forms, restrained detail at sprite scale, consistent upper-left lighting, coherent shadows painted on the body only, no cast shadow beneath the dragon. Elemental effects support the anatomy rather than covering it.

OUTPUT
One isolated dragon pose on a true transparent RGBA background. No terrain, no floor, no shadow ellipse, no border, no frame, no text, no labels, no UI, no checkerboard, no green screen. Do not crop any part of the dragon. Do not alter the character design.
```

## Universal negative instruction

Append this to every production request:

```text
Do not redesign the dragon. Do not change horn count, eye color, markings, scale pattern, wing structure, limb proportions, claw count, tail length, tail tip, age, body mass, or palette. No chibi exaggeration, plush-toy styling, mascot proportions, human clothing, saddle, rider, jewelry, armor, random accessories, background scenery, floor, cast shadow, border, text, frame numbers, grid lines, checkerboard, white matte, black matte, green spill, clipped horns, clipped toes, clipped wings, clipped tail, duplicate limbs, fused claws, broken joints, melted anatomy, inconsistent direction, or mirrored asymmetric markings.
```

## Animation directions

### Idle — 4 frames

The idle loop should be subtle and seamless.

1. neutral alert pose;
2. slight inhale, chest and shoulders rise;
3. gentle head, tail, fin, or wing adjustment;
4. return toward neutral without becoming identical too early.

Elemental motion should be restrained:

- ember pulse;
- water ripple;
- feather or membrane lift;
- dust mote;
- frost shimmer;
- small static arc;
- soft radiance;
- shadow wisp;
- aether mote;
- no effect for Neutral unless extremely subtle.

### Travel — 6 frames

Use the element's body plan rather than forcing every dragon into a terrestrial walk.

- grounded: complete footfall cycle with believable weight transfer;
- serpentine Water: body wave, fin stroke, and forward glide centered over the anchor;
- airborne Wind: wing beat and body lift cycle; never depict it jogging on the ground;
- floating Light, Shadow, and Aether: controlled hover propulsion with directional lean;
- Neutral: readable young-dragon walk or short bounding gait.

The loop must return cleanly from frame 6 to frame 1.

### Attack — 6 frames

1. anticipation;
2. wind-up;
3. forward commitment;
4. impact pose;
5. recoil or follow-through;
6. recovery toward idle.

Keep the impact readable without extending anatomy beyond the safe area. Physical elemental accents may appear at impact but must not replace the body.

### Cast — 6 frames

1. focus;
2. gather energy;
3. build elemental shape;
4. release point;
5. residual energy;
6. recovery.

Keep a consistent release origin near the mouth, horns, claws, chest, tail, or wing focus defined by the model sheet. Do not move the origin randomly between directions.

### Hurt — 4 frames

1. contact reaction;
2. strongest recoil;
3. guarded recovery;
4. return toward idle.

No gore. Do not permanently alter anatomy or markings.

### Victory — 6 frames

Show recognizable personality while preserving the shared anchor. Avoid huge jumps that leave the cell. The final frame must transition back to the first if looped.

### Defeat — 6 frames

1. loss of balance;
2. collapse begins;
3. body lowers;
4. settled body;
5. subtle final movement;
6. stable hold-safe final pose.

The final body must fit completely inside the cell with adequate tail, wing, horn, and foot margins.

## Element briefs

### Fire — grounded

A compact, athletic quadruped with a forceful stance, ember or flame crest, warm internal glow, and dark heat-resistant accents. Fire must look hot but controlled. Avoid covering the face or silhouette in flame. The hatchling should be energetic rather than monstrous.

### Water — serpentine

A long-bodied aquatic dragon with a distinctly serpentine silhouette, fins or webbed structures, smooth directional curves, and controlled water accents. Curve the body through the square; never squash it horizontally to imitate a quadruped. Preserve a clear head, neck, torso flow, tail, and fin placement. Travel should read as swimming or gliding even over abstract world terrain.

### Wind — airborne

A light flying hatchling with large functional wings, aerodynamic proportions, feather, membrane, or sail details, and a stable hovering center. It should look airborne in idle and travel states. Do not place it in a normal four-legged walk cycle. Keep wing tips well inside the safe area at maximum extension.

### Earth — grounded

A broad, heavy hatchling with stone plating, mineral ridges, thick limbs, and a low center of mass. Preserve softness and flexibility at joints so it remains alive rather than a rock statue. Dust and small pebbles may accent motion but cannot hide foot placement.

### Ice — grounded

A nimble hatchling with crystalline growths, cool translucent accents, and sharp but controlled silhouette points. Ice spikes must remain consistent and inside the safe area. Avoid pure white overexposure; maintain blue-gray shadow structure.

### Storm — grounded

An athletic hatchling with charged crests, conductive horn or scale structures, and restrained arcs. Lightning should emphasize action beats, not randomly redraw the outline. Avoid confusing Storm with Wind; Storm is power and charge, not primarily flight.

### Light — floating

A luminous hatchling with elegant, clean forms and soft radiance. Preserve visible edges and internal value contrast. Do not wash the body into white. Halo-like effects must remain secondary and compact.

### Shadow — floating

A dark hatchling with readable layered values, violet, blue, or muted spectral accents, and controlled shadow wisps. Do not use featureless black. Eyes, muzzle, limbs, wings, and tail must remain readable on transparent and dark terrain previews.

### Aether — floating

An arcane hatchling with cosmic, crystalline, runic, or extradimensional motifs. Keep the anatomy stable and let a small number of motes or internal gradients carry the supernatural identity. Avoid excessive galaxy texture and particle clutter.

### Neutral — generalist

A classic young dragon with balanced anatomy and no dominant elemental mutation. Use strong shape language, appealing but not toy-like proportions, and restrained natural coloration. Neutral must look intentional rather than unfinished.

## Direction-specific requirements

### Down

The face, chest, forelimbs, and front silhouette are primary. Keep horns and ears separated. Both feet or the projected hover center must align symmetrically unless the pose intentionally shifts weight.

### Left

Show true left-facing anatomy. Preserve asymmetric markings on the correct side. Keep muzzle, horns, wing layering, and tail overlap readable.

### Right

Do not automatically mirror Left when the dragon has asymmetric markings, horns, scars, fin placement, equipment, or effects. Produce a true right-facing reference when needed.

### Up

The back of the head, shoulders, wings, spine, tail, and rear feet must remain recognizable. Do not hide or crop the head. The up-facing row must not become a headless rear silhouette. Keep horn and ear tops fully within the cell.

## Hatch sequence guidance

Hatching is a separate, larger UI sequence rather than a world-tile animation.

Recommended transparent frames or key images:

1. intact element-themed egg;
2. first cracks and internal light;
3. shell displacement and silhouette visible;
4. hatchling emerging;
5. fully revealed hatchling with shell fragments;
6. settled introduction pose.

The hatchling must match the Whelp model sheet exactly. Do not create a different baby form solely for the hatch animation.

Deliver both:

- transparent runtime frames;
- green-background review copies.

Do not use green copies at runtime.

## Race asset guidance

The race asset is side-facing presentation art, not a crop from the portrait. Preserve the same Whelp design while emphasizing forward motion, readable limbs or wing beat, and a clean silhouette against the racing interface.

The race asset must remain separate from the four-direction world sheets.

## Generation request sequence

Use this order for each element:

1. model sheet;
2. corrected model sheet after review;
3. four neutral directional poses;
4. idle key frames;
5. travel key frames;
6. attack key frames;
7. cast key frames;
8. hurt, victory, and defeat key frames;
9. deterministic sheet assembly;
10. portrait, profile, and race art reconciled to the final model;
11. hatch sequence;
12. reserved gather, carry, deposit, and rest poses.

Do not generate ten elements in one giant contact sheet. Produce and approve one element at a time, then use the approved technical template for the next element.

## Final self-check the image assistant must perform

Before claiming completion, explicitly verify:

- exact same dragon identity in every frame;
- exact required direction order;
- exact frame count;
- complete anatomy in every cell;
- no clipped horns, toes, wings, fins, tail, or head;
- stable anchor;
- true transparency;
- no matte or fringe;
- no labels or grid lines in runtime PNGs;
- correct body plan for the element;
- readable one-times-size silhouette;
- separate transparent and green review outputs;
- filenames and dimensions match the contract.

If any item cannot be verified, label the output as a concept or source frame rather than a runtime-ready asset.
