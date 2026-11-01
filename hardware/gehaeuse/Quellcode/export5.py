import time, sys, numpy as np
import v5, pantilt as pt
from export import mesh, orient, write_stl, write_3mf
from decimate import cluster_qem_manifold

JOBS = {  # name: (fn, h, rot, count)
    "01_Unterteil": (v5.part_tub, 0.3, [0, 0, 0], 1),
    "02_Deckel_mit_Laufring": (v5.part_lid, 0.3, [0, 0, 0], 1),
    "03_Drehteller": (pt.part_turntable, 0.2, [180, 0, 0], 1),
    "04_Gabel_mit_Arm1": (v5.part_yoke, 0.2, [0, 0, 0], 1),
    "05_Arm2_Lagerseite": (v5.part_arm2, 0.2, [-90, 0, 0], 1),
    "06_Kamerakopf": (pt.part_head, 0.2, [-90, 0, 0], 1),
    "07_Seitendeckel": (pt.part_sidecover, 0.2, [90, 0, 0], 1),
    "08_Lampenhalter_2x": (v5.part_lamp, 0.2, [0, -90, 0], 2),
    "09_Zwischenboden": (v5.part_shelf, 0.25, [0, 0, 0], 1),
    "10_HDMI_Stopfen": (v5.part_hdmi_plug, 0.2, [0, 0, 0], 1),
    "11_Fuss_4x": (v5.part_feet, 0.2, [0, 0, 0], 4),
}
if __name__ == "__main__":
    sel = sys.argv[1:]
    for name, (fn, h, rot, cnt) in JOBS.items():
        if sel and name[:2] not in sel:
            continue
        t0 = time.time()
        node = fn()
        v, f = mesh(node, h)
        v, f, nbad = cluster_qem_manifold(v, f, 0.6 if h <= 0.25 else 0.7)
        err = np.abs(node.sdf(v)).max()
        v, f = orient(v, f, rot)
        write_stl(f"out51/{name}.stl", v, f)
        np.savez_compressed(f"out51/{name}.npz", v=v, f=f)
        ext = v.max(0) - v.min(0)
        print(f"{name}: {len(f)} Dreiecke, maxErr {err:.3f}, offen {nbad}, {ext.round(1)} mm, {time.time() - t0:.0f}s", flush=True)
