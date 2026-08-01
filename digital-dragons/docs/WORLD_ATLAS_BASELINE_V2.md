# Dragon World Atlas Baseline Refresh

The merged terrain and entity atlases remain on their established public v1 paths. This publication adds the missing terrain metadata and bumps the root asset version so Celdra no longer reuses the pre-refresh cached files.

The entity atlas contract is 256×64 with 16 transparent 32×32 cells. It is an indexed-color PNG with a `tRNS` transparency chunk rather than a full RGBA PNG; viewers that render transparency against black can therefore make the background appear opaque even though transparent pixels are encoded. The terrain atlas contract is an indexed-color 320×256 PNG with 80 32×32 cells.

After merge, redeploy Celdra-Cloud or clear `/tmp/celdra-digital-dragons`, then hard-refresh the Activity. The asset version for this refresh is `2026.08.01.1`.
