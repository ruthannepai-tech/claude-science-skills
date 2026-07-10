---
name: molecular-video-blender-modal
description: >
  Generate a cell-scale / schematic biology animation in Blender and render it on
  Modal cloud GPU into an MP4. Use this whenever the user wants a scientific
  animation of things bigger than single atoms — T-cells, receptors, membranes,
  nanoparticles, signaling, mechanism-of-action cartoons — or wants to turn a
  "video idea", a paper, or existing project artifacts (PDBs, platform specs,
  figures) into a rendered movie. Trigger on requests like "animate how our
  nanoparticle induces tolerance", "make a Blender movie of the three T-cell
  fates", "render this mechanism from our paper as a video", "I have a scene idea
  and some structures, build the animation", or "render my .blend on GPU / on
  Modal". Also use it for the render half alone: encoding a Blender scene to MP4
  on cloud GPU. For pure atomic-structure spins/montages (cartoon renders of a
  PDB) prefer protein-video-chimerax; this skill is for schematic/cell-scale
  scenes and for GPU rendering via Modal.
---

# Molecular video (Blender + Modal GPU)

Build a cell-scale or schematic biology animation in Blender and render it on
Modal cloud GPU. Two halves, either of which the user may want:

1. **Scene building** — translate a video idea / paper / project artifacts into a
   Blender scene: cells, receptors, membranes, nanoparticles, molecules
   (via the Molecular Nodes addon), keyframed motion, labels, camera, lighting.
2. **GPU rendering** — render the finished `.blend` to an MP4 on Modal, because a
   420-frame Cycles animation is far too slow on a laptop.

Read the half the user needs. If they hand you a finished `.blend` and just want
it rendered, jump to **Rendering on Modal**.

## Establish the scope first

- **The idea / source.** A free-text scene description, a paper (mechanism to
  visualize), or existing project artifacts. Pull real parameters from artifacts
  when available: `host.artifacts(search=...)` for platform specs, PDBs, prior
  scenes. Ground the biology in the source rather than inventing it.
- **Scale and style.** Cell-scale schematic (spheres = cells, cones = receptors,
  studded spheres = nanoparticles) vs. atomic detail (imported molecules). Mixed
  scenes are common (a cell with a real pMHC docking onto it).
- **The beats.** What changes over the timeline — fly-in, docking, a cell
  changing size/color to show a fate, labels fading in. Map beats to frame ranges
  (e.g. 30 fps, 420 frames = 14 s).
- **Reproducibility caveat.** A scene built through manual Blender Console steps
  (molecule import, per-chain styling, constraints) is NOT reproducible from a
  `.py` script alone — the authoritative artifact is the **saved `.blend`**, which
  is self-contained. Always render from the `.blend`, and save it as an artifact.

## Scene-building gotchas (Blender 4.4+ / 5.x)

These are real failures from building scenes in Blender 5.x. The Python API
changed in ways that break older tutorials.

- **F-curves moved off Action (5.0+).** `action.fcurves` no longer exists
  (slotted/layered Actions). Use
  `bpy_extras.anim_utils.action_get_channelbag_for_slot(action, obj.animation_data.action_slot).fcurves`.
  Keep a version-safe accessor: legacy `hasattr(action,"fcurves")` for ≤4.3, else
  the channelbag path.
- **World background node lookup by name is fragile.** `world.node_tree.nodes["Background"]`
  raises KeyError on worlds without that exact node name. Find it by type:
  `next(n for n in nt.nodes if n.type == 'BACKGROUND')`, creating one if absent.
- **Node instance group access.** On a node INSTANCE the referenced group is
  `.node_tree`, not `.node_group` (`.node_group` is only correct on the modifier).
- **Parent objects that must move together.** A receptor placed on a cell surface
  won't follow the cell's scale/position animation unless parented:
  `rec.parent = cell; rec.matrix_parent_inverse = cell.matrix_world.inverted()`
  (keep-transform parenting). Set the timeline to frame 1 (rest state) BEFORE
  baking `matrix_parent_inverse`, or the offset bakes against a scaled state.
- **Follow-but-not-scale.** To make object B follow object A's position but keep
  its own size (e.g. a nanoparticle riding a shrinking cell), use a Copy Location
  constraint (not Child Of), influence keyframed 0→1 with CONSTANT interpolation
  at the dock frame.
- **Molecular Nodes per-chain styling.** The MN import popup sets ONE style. For
  per-chain styling (cartoon on A/B, sticks on a peptide chain P) you must branch
  the geometry node tree: source geometry → per-style Style node gated by a chain
  selection → Join Geometry. Chain identity is a stock integer attribute
  `chain_id` (unique letters sorted alphabetically → 0,1,2…), so you can build the
  selection from stock nodes (Named Attribute `chain_id` + Compare + Boolean OR)
  without MN's Select Chain node.
- **Text label overlap.** Center-aligned single-line labels under closely-spaced
  objects collide. Break long labels onto two lines (`body="LINE1\nLINE2"`,
  `align_y='CENTER'`, tighten `space_line`) so each label's width shrinks to its
  longest word.

## Rendering on Modal

The scene is built; now render it fast on cloud GPU. This is the workflow proven
out for a 420-frame 1080p Cycles animation.

### Build (or reuse) the Blender image

A prebuilt image may already exist — check `compute_details` for a recorded
Blender image id before rebuilding. To build from scratch, in the
`compute_provider` (modal) kernel:

```python
import modal
BLENDER_URL = "https://download.blender.org/release/Blender5.1/blender-5.1.2-linux-x64.tar.xz"
img = (modal.Image.from_registry("nvidia/cuda:12.4.1-runtime-ubuntu22.04", add_python="3.11")
       .apt_install("curl","xz-utils","ffmpeg","libx11-6","libxrender1","libxi6",
                    "libxxf86vm1","libxfixes3","libxkbcommon0","libsm6","libice6",
                    "libgl1","libglu1-mesa","libegl1","libgomp1","libxext6")
       .run_commands(f"curl -L {BLENDER_URL} -o /tmp/b.tar.xz",
                     "mkdir -p /opt/blender && tar -xJf /tmp/b.tar.xz -C /opt/blender --strip-components=1",
                     "ln -s /opt/blender/blender /usr/local/bin/blender",
                     "rm /tmp/b.tar.xz"))
img.build(modal.App.lookup("blender-render", create_if_missing=True))
```

If the scene's molecules must render as atomic models (not just docked
placeholders), MN must be baked in AND enabled before the `.blend` loads:
`.run_commands("blender --online-mode --command extension sync",
"blender --online-mode --command extension install molecularnodes")`. Enabling
MN AFTER opening the file is too late — its node trees load as dead placeholders
and output empty geometry. If the user is fine with molecules shown as simple
shapes, skip MN entirely (faster).

### The critical timing fact — OPTIX compile is a one-time per-container cost

Cycles compiles the OPTIX/CUDA kernel on the FIRST render in a fresh container
(~440 s), then caches it; every subsequent frame in that container is fast
(~14 s/frame @720p, ~30 s/frame @1080p for a transparency/SSS-heavy scene).

**This is the single biggest gotcha.** Do NOT estimate full-render cost from
single-frame test jobs — each pays the compile once, so a single frame looks like
it takes 5 minutes when the real per-frame cost is seconds. Always measure timing
with a CONTIGUOUS multi-frame batch in one Blender process, and read the
steady-state (2nd frame onward), not the first.

### Parallel render pattern (shared Volume)

Split the frame range across a few WIDE containers so the compile amortizes.
4 containers × ~105 frames was the sweet spot for 420 frames.

1. Create a shared Modal Volume once (compute_provider kernel):
   `modal.Volume.from_name("render-frames", create_if_missing=True)`.
2. Fan out N `host.compute` jobs (repl tool), each mounting the volume at
   `/frames` (`provider_params.modal.volumes={'/frames':'render-frames'}`) and
   rendering its own contiguous sub-range into `/frames` via the bundled
   `scripts/render_range.py`. Submit all in one repl cell; loop
   `wait_for_notification` until all report success.
3. One final container (same volume mounted) ffmpeg-encodes
   `/frames/frame_%04d.png` → MP4, copies it to `./out/`, and harvests.

The bundled `scripts/render_range.py` handles GPU enable (OPTIX→CUDA→CPU
fallback), a "720p" preset with forced even dimensions (H.264 needs even
width/height), sample override, and per-frame output naming.

### FILENAME BUG that silently wastes a full render

`bpy.ops.render.render(write_still=True)` writes to the LITERAL
`scene.render.filepath` and does NOT auto-insert the frame number. If you set the
filepath once outside the loop, every frame (and every parallel container)
overwrites the same file — you get 1 frame after an hour. Set the filepath INSIDE
the per-frame loop: `scene.render.filepath = os.path.join(out_dir, f"frame_{f:04d}")`
(no extension — Blender appends the format's). Verify frames are accumulating in
the Volume early (10 min in) rather than trusting it for the full hour.

### Encode and harvest

```
ffmpeg -y -framerate 30 -i /frames/frame_%04d.png \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart \
  out/animation.mp4
```

`yuv420p` + even dimensions = universal playback; `+faststart` = streams before
fully downloaded; `crf 16` = high quality. Also copy a few sample stills
(start / mid / end frames) to `out/` for quick QC. `save_artifacts` the MP4,
the stills, and the `.blend`.

### Cost and cleanup

Parallelism changes wall-time, NOT cost — total GPU-hours (and $) are the same
whether 1 container or 30. Resolution is the reliable cost lever: 1080p→720p
keeps ~44% of the pixels (2.25× reduction, not 4×). Samples help less on
transparency/SSS-bound scenes than the usual rule of thumb — measure rather than
assume. A ~14 s 420-frame 1080p render is roughly 2 A100-hours.

When done: terminate every sandbox
(`modal.Sandbox.list(app_id=app.app_id)` → `sb.terminate()`), and delete the
frames Volume with the CLI (`modal volume delete <name> --yes` — the SDK has no
top-level `Volume.delete()` in current versions). If a submit fails with
"exceeded its spend limit", that's a hard stop on Modal's side — the user must
raise it at modal.com/settings/plan; nothing you close frees it.

## Delivering

Hand back: the MP4, a few QC stills, and the saved `.blend`. Note which molecules
(if any) render as simple shapes vs. atomic models, and any scene caveats. Offer
to record the image id + pattern in `compute_details` so the next render skips
the image build.
