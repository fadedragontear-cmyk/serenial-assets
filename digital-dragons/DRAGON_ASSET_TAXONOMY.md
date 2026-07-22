# Dragon asset taxonomy v2

The asset identity is mechanical and intentionally boring:

- `element_<element>_<variant>`
- `hybrid_<element>_<element>_<variant>`
- `celdra`

Elements use the canonical order Fire, Wind, Water, Earth, Ice, Storm, Light, Shadow, Aether, Neutral. A hybrid pair is order-insensitive; both `shadow/storm` and `storm/shadow` resolve to `hybrid_storm_shadow_XX`.

The complete taxonomy contains 45 unique two-element pairs. Every pair now has at least one `variant_01` runtime directory. Existing historical hybrids keep their current variants; newly completed pairs are marked `art_status: bootstrap_shared` in the manifest until pair-specific final illustrations replace the shared template.

Old roster names remain only in `legacy_dragon_aliases` during migration. They are not directory names, current type names, or future creation keys. The aliases may be removed after production reports no old asset keys.

Celdra is protected at `dragons/unique/celdra/` and cannot be selected as a normal elemental, hybrid, starter, egg, or fallback asset.
