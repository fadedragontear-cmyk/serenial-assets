# Generated Source Master Policy

The image generator produces its strongest dragon art as 1536×1024 contact sheets and 1024×1024 presentation images. These dimensions are now treated as source masters rather than failed runtime sheets.

The game consumes normalized runtime atlases derived from those masters. Future upgrades should preserve the original high-resolution files, record crop/frame mappings, and rebuild runtime atlases without asking image generation to emit exact production grids.

The current 64×64-cell Whelp packs are baseline derivatives. They may be replaced in place after manual cleanup without changing stage keys or gameplay systems.
