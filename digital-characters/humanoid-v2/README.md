# Serenial anime humanoid rig v2

Status: production target for new Tavern players, creator characters, and elders.

This rig replaces the small code-drawn patron fallback with a larger authored anime/JRPG character system. The existing `humanoid-v1/female-base-a` and Celdra packs remain usable while v2 modules are authored; v2 is additive rather than a destructive conversion.

## Visual target

- Adult anime/JRPG proportions with a readable face, hair silhouette, hands, footwear, and clothing at the live Tavern scale.
- `192 x 192` RGBA source cells. Runtime may display the visible character at roughly `128–144` logical pixels tall in the 640x400 Tavern view.
- Ground anchor: `(96, 172)` in every frame and every layer.
- Character core should normally occupy about `120–145` source pixels vertically before exceptional hair/headwear.
- No chibi/minified patron fallback. If an optional module does not exist, omit that module and keep the authored base.
- Nearest-neighbor presentation at integer-friendly scales; no blurry CSS resizing.

## Required animation baseline

| Action | Frames | FPS | Ground contract |
| --- | ---: | ---: | --- |
| idle | 4 | 4 | planted |
| walk | 8 | 10 | ~1.55 world tiles / cycle |
| run | 8 | 14 | ~1.60 world tiles / cycle |

Walk frames `0` and `4` are opposite-foot contact poses; `2` and `6` are passing poses. Run uses stronger forward intent, longer reach, body compression/extension, and a readable airborne/recovery phase. The runtime animation clock is advanced from actual world distance, not wall-clock time, so authored feet must match the declared stride instead of compensating with sliding.

Movement review must reject:

- feet visibly travelling backward while planted;
- identical walk and run silhouettes played at different speed;
- a torso that remains perfectly static while limbs move;
- large root drift away from the shared ground anchor;
- hair, coats, capes, tails, or loose accessories moving before the body that drives them;
- up/down/side views that change body height or apparent character identity.

Secondary motion should trail the root action by a small amount: hair tips, coat hems, scarves, tails, and similar pieces follow acceleration and settle after the body. This is authored into their layer frames; runtime bob/lean is only a temporary aid for placeholder sheets.

## Paper-doll layer order

Every module uses the exact same frame size, anchor, action, direction rows, frame count, and timing as its rig:

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

The game already stores semantic selections such as body, lineage, hairstyle, outfit, accessory, skin color, hair color, and eye color. Art modules map onto those stable values. Adding better art must not require rewriting a player's Supabase appearance row.

Body silhouettes are visual choices, not gender/identity restrictions. Skin color is independent of fantasy lineage. Any reviewed outfit/hair/accessory that physically fits the rig may be combined unless a specific clipping rule says otherwise.

## Color sliders without destroying the art

Whole-sheet hue rotation is prohibited. It recolors outlines, highlights, skin, cloth, and material shading together and makes authored art look cheap.

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

A mask is an aligned transparent atlas for exactly one color channel. The client applies the chosen color to the mask, blends it with preserved authored shadow/highlight information, and composites the finished appearance once into an offscreen cache. Eyes use their own small mask so changing eye color never changes lashes, brows, or skin.

The first assets do not need every mask. Missing masks leave the reviewed source palette intact.

## Directory shape

```text
digital-characters/humanoid-v2/
  rig.json
  README.md
  bodies/
    female-base-a/
    male-base-a/
    androgynous-base-a/
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

Each leaf can contain authored source frames plus packed runtime atlases. Shared modules should be preferred over duplicated creator-specific art. A creator preset may add a unique hair, facial detail, hat, coat, jewelry item, etc. when that feature is actually distinctive.

## Creator likeness workflow

Do not infer a creator's appearance from a username. Before authoring a named creator preset, collect current/relevant public reference images or references supplied by the creator/Fade and write a short visual brief. Record which features are identity-critical and which can use shared modules. Avoid silently turning a creator's handle or theme into a physical trait.

Production order:

1. approve a neutral female, male, and androgynous body turnaround;
2. complete one real walk and run cycle on each body;
3. prove two hairstyles and two outfits on all four directions without clipping;
4. prove skin/hair/eye masks;
5. build Fade as the first creator preset;
6. add MegaHarv, Enigma, Nadean25, Hero King Gilgamesh;
7. then expand Newf, Sage, Aiyaria and Tavern elders.

## Runtime performance

Layers are not redrawn independently every display frame forever. The client resolves a normalized appearance signature, loads immutable revision-pinned module atlases, composites the selected modules/masks into cached animation atlases, and reuses that composite until the appearance changes. This keeps the shared Tavern renderer cheap while preserving modular authoring.

Cloudflare serves only revision-pinned allowlisted assets. Missing modules must fail closed to the authored base and may never switch the player back to the retired small procedural avatar.
