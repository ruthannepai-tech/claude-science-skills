# Claude Science Skills

Reusable [Claude Science](https://claude.ai) skills for producing scientific
animations of molecular and cellular biology.

## Skills

### `protein-video-chimerax`
Turn one or more protein/peptide structure files (PDB/mmCIF) plus a "video idea"
into a **ChimeraX movie script** (`.cxc`) that records a presentation-quality MP4.
Handles multi-structure montages, per-chain / per-ligand coloring, in-place spins,
2D labels, and the ChimeraX API gotchas that commonly break movie scripts.

Best for **atomic-resolution structure rendering** — cartoon/surface/stick renders,
spins, and montages of actual PDB structures. Runs in ChimeraX on the desktop.

### `molecular-video-blender-modal`
Build a **cell-scale / schematic biology animation** in Blender (cells, receptors,
membranes, nanoparticles, imported molecules via Molecular Nodes, keyframed motion,
labels, camera) and **render it on Modal cloud GPU** to an MP4. Encodes the
scene-building fixes for Blender 5.x and a proven parallel GPU-render pipeline,
including the one-time OPTIX-compile timing insight and the per-frame filename
pitfall that silently wastes renders.

Best for **cell-scale / mechanism-of-action** scenes and for GPU-rendering any
Blender `.blend`. Ships `scripts/render_range.py` (contiguous-range renderer with
GPU fallback, even-dimension presets, and correct per-frame output naming).

## Using a skill

Each skill is a directory with a `SKILL.md` (and optional `scripts/`). Drop it
into your Claude Science skills directory, or point your agent at it. The
`description` field in each `SKILL.md` frontmatter controls when the skill
triggers.

## Provenance

Both skills were distilled from a real project: rendering an antigen-specific
tolerance ("three T-cell fates") animation for an eosinophilic esophagitis
therapeutic-design effort. The gotchas documented here are the ones that actually
came up.
