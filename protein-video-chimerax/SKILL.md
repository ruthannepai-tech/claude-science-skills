---
name: protein-video-chimerax
description: >
  Produce a ChimeraX movie script (.cxc) that renders a narrated animation of
  one or more protein/peptide structures (PDB/mmCIF/mol2) into an MP4. Use this
  whenever the user shares a structure file (or several) plus a "video idea" for
  showcasing it — e.g. "make a spinning movie of this pMHC complex", "animate my
  three allergen structures one at a time then together", "I want a rotating
  cartoon render of these PDBs for a talk", "turn these docked poses into a
  montage". Trigger even when the user doesn't say "ChimeraX" or ".cxc" — any
  request to turn protein structure files into a presentation-quality rotating /
  morphing / multi-structure video belongs here. For CELL-scale or schematic
  biology animations (T-cells, nanoparticles, membranes, abstract mechanism
  cartoons) use molecular-video-blender-modal instead; this skill is for
  atomic-resolution structure rendering in ChimeraX.
---

# Protein video (ChimeraX .cxc)

Turn one or more molecular structures into a presentation-quality MP4 by writing
a ChimeraX command script (`.cxc`). ChimeraX is the right tool when the subject
is the **actual atomic structure** — cartoon/surface/stick renders, spins,
morphs, per-chain or per-ligand coloring — as opposed to schematic cell biology
(that's the Blender skill).

The deliverable is a **`.cxc` script the user runs in ChimeraX** (`open
movie.cxc`), which records and encodes the MP4 in one pass. You are writing the
script, not rendering it yourself — ChimeraX runs on the user's machine.

## What to establish before writing the script

1. **The structure files** — names and what each contains. Ask for, or read, the
   chain composition: which chains are the "platform" (e.g. MHC, receptor, scaffold)
   and which is the "payload" (peptide, ligand, epitope). The payload is usually
   what the viewer should track, so it gets the saturated color; the platform stays
   neutral. If you can read the PDB, count atoms/residues per chain so your
   `color`/`select` specs are correct.
2. **The narrative / beats** — what happens in what order. A typical structure
   montage is a sequence of *beats*: focus on structure A (spin), then B, then
   show all together. Get the beat list from the user's "video idea".
3. **Style** — cartoon vs surface vs stick; background (dark reads best for
   talks); labels on/off. Default to crisp cartoon + payload sticks on a dark
   background unless told otherwise.
4. **Length / pace** — ChimeraX records at a fixed framerate (default 30 fps in
   the encode step). Spin speed is `turn <deg> <frames>`; a full turn in ~1.3 s
   is `turn y 9 40`. Keep each `wait N` equal to the frame count of the motion
   it follows, or the movie desyncs.

## Script skeleton

Write the script in these five sections, in order. This structure is load-bearing —
recording must wrap only the motion, and styling must precede recording.

```
# 1. LOAD
open structA.pdb          # becomes model #1
open structB.pdb          # #2
open structC.pdb          # #3

# 2. LAYOUT (only if showing multiple side by side)
move x -120 models #1     # space them so a final group shot never overlaps
move x  120 models #3     # note each model's post-move centroid for spin centers

# 3. STYLE (must come BEFORE recording)
hide atoms
show cartoon
color #1-3/A,B #aab8c4    # platform chains: one shared neutral
color #1/P orange         # payload chains: one saturated color each, so the
color #2/P teal           #   eye tracks the peptide, not the (identical) platform
color #3/P magenta
show #1-3/P atoms
style #1-3/P stick
set bgColor #0a0e14       # dark bg reads best; white labels on top
lighting soft
graphics silhouettes true
hide #2,3 models          # start with only the first subject visible

# 4. RECORD (wrap ONLY the animated beats)
movie record supersample 3
#   --- per beat: reveal -> reframe -> label -> spin ---
view #1 frames 15
2dlabels text "SUBJECT A" xpos 0.44 ypos 0.12 size 34 color white
wait 15
turn y 9 40 center <cx>,<cy>,<cz> models #1   # explicit centroid = spins in place
wait 40
#   (repeat for each beat; hide previous / show next between beats)

# 5. ENCODE
movie encode output my_movie.mp4 quality high framerate 30
```

## ChimeraX gotchas that will bite you

These are real failure modes — encode them into every script.

- **2D labels: create vs change.** ChimeraX is NOT old Chimera. There is no
  `2dlabels create/delete`. Use `2dlabels text "..."` to CREATE the first label,
  and `2dlabels all text "..."` to CHANGE it thereafter. To fade a label out:
  `2dlabels all visibility false frames 15`.
- **Spin in place needs an explicit center.** A bare `turn y 9 40` rotates about
  the global scene center, so any model not at the origin orbits instead of
  spinning. Give every spin `center <x>,<y>,<z> models #N` using that model's
  own centroid (original centroid + whatever x-offset you `move`d it). If you
  re-space the models, update the centers to match.
- **`wait` must match the motion.** `turn y 9 40` animates over 40 frames; the
  following `wait 40` holds the recording for exactly those frames. Mismatched
  waits desync labels and motion. Same rule for `view ... frames N` → `wait N`.
- **Don't color by B-factor unless it's real.** Many exported/predicted PDBs have
  an all-zero B-factor column; `color byattribute bfactor` or `color bfactor`
  then paints everything one color and looks broken. Color by chain/selection
  instead unless you've confirmed real B-factors.
- **Style choice on dark backgrounds.** Semi-transparent molecular surfaces turn
  muddy on dark backgrounds. Prefer opaque cartoon + payload sticks. If you want
  surface, use a light background or bump opacity.
- **Working directory.** `open structA.pdb` resolves relative to ChimeraX's cwd.
  Tell the user to run from the folder holding the PDBs, or write absolute paths
  into the `open` lines.
- **Model numbering is load order.** The first `open` is `#1`, second `#2`, etc.
  All later `color`/`move`/`turn`/`show` specs key off these numbers.

## Selection spec cheat-sheet

- `#1` — model 1; `#1-3` — models 1 through 3
- `#1/P` — chain P of model 1; `#1-3/A,B` — chains A and B of models 1–3
- `#1/P:5-20` — residues 5–20 of chain P; `#1/P@CA` — CA atoms
- `color`, `show`/`hide`, `style`, `select`, `transparency`, `turn`, `move`,
  `view` all accept these specs.

## Handing off to a cell-scale scene

If the user's larger project also has a Blender cell-scale animation (see
molecular-video-blender-modal), you can end the ChimeraX cut with a fade
(`2dlabels all visibility false frames 15; wait 15`) designed to cross-dissolve
into the first ~15 frames of the Blender scene's establishing camera — an
atomic→cellular transition. Mention this option when both scales are in play.

## Delivering

Write the `.cxc` to the workspace, `save_artifacts` it, and tell the user the
one command to run: `open my_movie.cxc` in ChimeraX (or
`chimerax --script my_movie.cxc` headless). Note that ChimeraX must be installed
locally — this skill produces the script, not the rendered MP4. If they want the
render done on cloud GPU instead, that's the Blender/Modal skill's territory;
ChimeraX movie recording is designed to run interactively on the desktop.
