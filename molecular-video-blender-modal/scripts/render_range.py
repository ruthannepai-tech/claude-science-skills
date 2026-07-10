import bpy, sys, os, time

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
blend      = argv[0]
frame_a    = int(argv[1])
frame_b    = int(argv[2])
out_dir    = argv[3]
res_pct    = int(argv[4]) if len(argv) > 4 else 100   # resolution_percentage
samples    = int(argv[5]) if len(argv) > 5 else 0     # 0 = keep scene value
os.makedirs(out_dir, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene

# GPU
prefs = bpy.context.preferences.addons["cycles"].preferences
chosen = None
for backend in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = backend; prefs.get_devices()
        if [d for d in prefs.devices if d.type == backend]:
            for d in prefs.devices: d.use = (d.type == backend)
            chosen = backend; break
    except Exception as e:
        print(f"[gpu] {backend}: {e}")
scene.cycles.device = "GPU" if chosen else "CPU"

scene.render.resolution_percentage = 100
if res_pct == 67:                 # "720p" preset -> exact even dims for H.264
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
else:
    scene.render.resolution_percentage = res_pct
    # force even dimensions (yuv420p requires even width/height)
    scene.render.resolution_x -= scene.render.resolution_x % 2
    scene.render.resolution_y -= scene.render.resolution_y % 2
if samples > 0:
    scene.cycles.samples = samples
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode  = "RGB"   # video has no alpha; smaller files

rx = int(scene.render.resolution_x * res_pct / 100)
ry = int(scene.render.resolution_y * res_pct / 100)
print(f"[cfg] backend={chosen} {rx}x{ry} samples={scene.cycles.samples} "
      f"frames {frame_a}-{frame_b} -> {out_dir}")

t0 = time.time()
for f in range(frame_a, frame_b + 1):
    ft = time.time()
    scene.frame_set(f)
    # set an explicit per-frame filepath — render(write_still) writes the
    # literal filepath and does NOT auto-insert the frame number.
    scene.render.filepath = os.path.join(out_dir, f"frame_{f:04d}")
    bpy.ops.render.render(write_still=True)
    print(f"[frame] {f} {time.time()-ft:.1f}s", flush=True)
dt = time.time() - t0
n = frame_b - frame_a + 1
print(f"=== DONE {n} frames in {dt:.1f}s ({dt/n:.1f}s/frame) "
      f"-> 420 ~= {dt/n*420/60:.0f} min single-GPU ===")
