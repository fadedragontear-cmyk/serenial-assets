# Serenial anime humanoid rig v2

Status: production target for new Tavern players, creator characters, and elders.

This rig replaces the small code-drawn patron fallback with an authored anime/JRPG character system. The existing `humanoid-v1/female-base-a` and Celdra packs remain usable while v2 modules are authored; v2 is additive rather than a destructive conversion.

## Visual target

The current visual target is the larger, detailed sprite language approved for the Tavern: readable anime faces and hair, substantial clothing detail, clean silhouettes, and a classic JRPG sense of proportion rather than tiny chibi patrons. The intended family is closer to the character readability associated with Chrono Trigger, Final Fantasy VI, Secret/Legend of Mana and modern HD-2D presentation such as Octopath, while remaining original Serenial art rather than reproducing another game's sprites.

- `192 x 192` RGBA source cells.
- Ground anchor: `(96, 172)` in every frame and every layer.
- Runtime target is approximately `112` logical pixels of visible character height in the 640x400 Tavern view, with a normal range of roughly `100–120` depending on hair/headwear.
- Character core should normally occupy about `120–145` source pixels vertically before exceptional hair/headwear.
- No chibi/minified patron fallback. If an optional module does not exist, omit that module and keep the authored base.
- Nearest-neighbor presentation at integer-friendly scales; no blurry CSS resizing.
- Transparent pixels must be genuinely transparent. White fringe, matte contamination, checker residue and background specks are production failures.

## Body baseline

The initial production system has exactly two authored base silhouettes:

1. `female-base-a`
2. `male-base-a`

Do not spend art or runtime complexity on a third body base yet. Additional silhouettes can be added later without changing the layer contract.

Hair, eyes, skin color, lineage details, outfits and accessories remain modular and are not restricted by body base unless a reviewed clipping rule requires it.

## Required animation baseline

The approved reference cadence is compact and expressive rather than padded with near-duplicate frames:

| Action | Frames | FPS | Ground contract |
| --- | ---: | ---: | --- |
| idle | 4 | 4 | planted |
| walk | 6 | 10 | ~1.55 world tiles / cycle |
| run | 6 | 14 | ~1.60 world tiles / cycle |

Walk frames `0` and `3` are opposite-foot contact poses. Passing/recovery information should read clearly around frames `1/4`; the remaining frames carry extension and weight transfer. Run uses stronger forward intent, longer reach, body compression/extension, and a readable lift/recovery phase.

The runtime animation clock advances from actual world distance, not wall-clock time. Authored feet therefore need to agree with the declared stride. Runtime code must not compensate for weak source animation by rocking, rotating, stretching or squashing the complete sprite as one rigid card.

Movement review must reject:

- feet visibly travelling backward while planted;
- identical walk and run silhouettes played at different speed;
- a torso that remains perfectly static while limbs move;
- the complete sprite being bobbed/tilted as a single rigid object;
- large root drift away from the shared ground anchor;
- hair, coats, capes, tails, or loose accessories moving before the body that drives them;
- up/down/side views that change body height or apparent character identity.

Secondary motion belongs in the art: hair tips, coat hems, scarves, tails and similar pieces should trail acceleration and settle after the body. The body itself should show weight transfer through hips, shoulders, knees and arm swing. This is the difference between a character that appears to travel and one that simply slides across the floor.

## Paper-doll layer order

Every module uses the exact same frame size, anchor, action, direction rows, frame count and timing as its rig:

1. `back_accessory`
2. `back_hair`
3. `body`
4. `skin_detail`
5. `eyes`
6. `lower_outfit`
7. `upper_outfit`
8. `lineage_detail`
9. `front_hair`
10. `headwear`
11. `front_accessory`

A complete player is therefore an appearance record plus reviewed module keys, not a one-off atlas. Fade, MegaHarv, Enigma/onestophiphop, Nadean25, Hero King Gilgamesh, Newf, Sage, Aiyaria, and future Tavern elders should all be assembled through this same layer system. Distinctive creator-specific pieces are modules/presets, not special renderer branches.

## Mirror compatibility

The game stores semantic selections such as body, lineage, hairstyle, outfit, accessory, skin color, hair color and eye color. Art modules map onto those stable values. Adding better art must not require rewriting a player's Supabase appearance row.

The current selectable body values are `female-base-a` and `male-base-a`. Older/unsupported body values should normalize to the reviewed default rather than creating a new renderer path.

## Color controls without destroying the art

Whole-sheet hue rotation is prohibited. It recolors outlines, highlights, skin, cloth and material shading together and makes authored art look cheap.

Free Mirror colors are supported through authored masks:

```text
module/
  runtime/
    idle.png
    walk.png
    run.png
    masks/
      skin-idle.png
      skin-walk.png
      skin-run.png
      hair-idle.png
      ...
```

A mask is an aligned transparent atlas for exactly one color channel. The client applies the chosen color to the mask, preserves authored shadow/highlight information, and composites the finished appearance once into an offscreen cache. Eyes use their own small mask so changing eye color never changes lashes, brows or skin.

The first assets do not need every mask. Missing masks leave the reviewed source palette intact.

## Directory shape

```text
digital-characters/humanoid-v2/
  rig.json
  README.md
  bodies/
    female-base-a/
    male-base-a/
  hair/
    layered-bob/
    long-tied/
    side-braid/
    windswept/
    short-crop/
    curly-crop/
  eyes/
    soft/
    bright/
    focused/
    round/
    angular/
  outfits/
    tavern-traveler/
    caretaker/
    wayfinder/
    guild-scholar/
  lineage/
    human/
    elf/
    dragontouched/
  accessories/
    hairpin/
    earrings/
    glasses/
    scarf/
  presets/
    creators/
    elders/
```

Each leaf can contain authored source frames plus packed runtime atlases. Shared modules should be preferred over duplicated creator-specific art. A creator preset may add unique hair, facial detail, hat, coat, jewelry or another characteristic piece when that feature is actually distinctive.

## Creator likeness workflow

Do not infer a creator's appearance from a username. Before authoring a named creator preset, collect current/relevant public reference images or references supplied by the creator/Fade and write a short visual brief. Record which features are identity-critical and which can use shared modules.

Production order:

1. approve one female and one male turnaround at final Tavern scale;
2. complete real 4-frame idle, 6-frame walk and 6-frame run cycles for both;
3. prove two hairstyles and two outfits on all four directions without clipping;
4. prove skin/hair/eye masks;
5. build Fade as the first creator preset;
6. add MegaHarv, Enigma, Nadean25 and Hero King Gilgamesh;
7. then expand Newf, Sage, Aiyaria and Tavern elders.

## Runtime performance

Layers are not redrawn independently every display frame forever. The client resolves a normalized appearance signature, loads immutable revision-pinned module atlases, composites the selected modules/masks into cached animation atlases, and reuses that composite until the appearance changes. This keeps the shared Tavern renderer cheap while preserving modular authoring.

Cloudflare serves only revision-pinned allowlisted assets. Missing modules must fail closed to the authored base and may never switch the player back to the retired small procedural avatar.
