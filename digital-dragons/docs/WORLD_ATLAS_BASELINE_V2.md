# Dragon World Atlas Baseline Refresh

The merged terrain and entity atlases remain on their established public v1 paths. This publication adds the missing terrain metadata and bumps the root asset version so Celdra no longer reuses the pre-refresh cached files.

The entity atlas contract is 256×64 RGBA with 16 transparent 32×32 cells. The terrain atlas contract is 320×256 with 80 32×32 cells.

After merge, redeploy Celdra-Cloud or clear `/tmp/celdra-digital-dragons`, then hard-refresh the Activity.
