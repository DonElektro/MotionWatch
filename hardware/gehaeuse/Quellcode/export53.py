"""v5.3: geänderte und neue Teile exportieren -> out53/*.stl (+ .npz).  Einzelne: python3 export53.py 01 25
Namen mit «_v53», wo ein Teil von v5.2 ersetzt wird (01_Unterteil_v53 statt 01_Unterteil_v52, 02_Deckel_v53 statt
02_Deckel_mit_Laufring). Alle übrigen Teile sind gleich wie v5.2 (Druckdateien/v5-2/)."""
import time, sys, os, numpy as np
import v53
from export import mesh, orient, write_stl
from decimate import cluster_qem_manifold

JOBS = {  # name: (fn, h, rot, count)
    "25_Halter_Wand_Baum": (v53.part_holder, 0.3, [0, 0, 0], 1),
    "26_Akkuklappe": (v53.part_hatch, 0.2, [0, 0, 0], 1),
    "27_Luftkanal": (v53.part_duct, 0.15, [180, 0, 0], 1),
    "02_Deckel_v53": (v53.part_lid, 0.3, [0, 0, 0], 1),
    "01_Unterteil_v53": (v53.part_tub, 0.3, [0, 0, 0], 1),
}
if __name__ == "__main__":
    os.makedirs("out53", exist_ok=True)
    sel = sys.argv[1:]
    for name, (fn, h, rot, cnt) in JOBS.items():
        if sel and name[:2] not in sel:
            continue
        t0 = time.time()
        node = fn()
        v, f = mesh(node, h)
        v, f, nbad = cluster_qem_manifold(v, f, 0.6 if h <= 0.25 else 0.7) if h >= 0.2 else cluster_qem_manifold(v, f, 0.6 * h / 0.2)
        err = np.abs(node.sdf(v)).max()
        v, f = orient(v, f, rot)
        write_stl(f"out53/{name}.stl", v, f)
        np.savez_compressed(f"out53/{name}.npz", v=v, f=f)
        ext = v.max(0) - v.min(0)
        print(f"{name}: {len(f)} Dreiecke, maxErr {err:.3f}, offen {nbad}, {ext.round(2)} mm, {time.time() - t0:.0f}s", flush=True)
