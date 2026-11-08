"""5.3.1: Adapter 28 (altes UPS HAT) exportieren -> out531/28_Adapter_UPS_HAT_alt.stl (+ .npz) und als einzelne 3MF nach
Druckdateien/v5-3/MoveEye_v5-3_28_Adapter_UPS_HAT_alt.3mf (Format wie gehaeuse_bauen.py --druck53).
python3 export531.py            (ca. 1–2 min)      python3 export531.py --nur-stl   (ohne 3MF)
Alle übrigen Teile bleiben genau wie v5.3 (Druckdateien/v5-3/)."""
import os, sys, time, numpy as np
import upsalt531
from export import mesh, orient, write_stl
from decimate import cluster_qem_manifold

HIER = os.path.dirname(os.path.abspath(__file__))
DD = os.environ.get("GEH_DRUCKDATEIEN") or os.path.join(HIER, "..", "Druckdateien")
JOBS = {"28_Adapter_UPS_HAT_alt": (upsalt531.part_adapter, 0.2, [0, 0, 0], 1)}   # Rahmen unten wie eingebaut

if __name__ == "__main__":
    os.makedirs("out531", exist_ok=True)
    for name, (fn, h, rot, cnt) in JOBS.items():
        t0 = time.time()
        node = fn()
        v, f = mesh(node, h)
        v, f, nbad = cluster_qem_manifold(v, f, 0.6)
        err = np.abs(node.sdf(v)).max()
        v, f = orient(v, f, rot)
        write_stl(f"out531/{name}.stl", v, f)
        np.savez_compressed(f"out531/{name}.npz", v=v, f=f)
        ext = v.max(0) - v.min(0)
        print(f"{name}: {len(f)} Dreiecke, maxErr {err:.3f}, offen {nbad}, {ext.round(2)} mm, {time.time() - t0:.0f}s", flush=True)
        if "--nur-stl" in sys.argv:
            continue
        sys.path.insert(0, os.path.join(HIER, "..", "..", "..", "werkzeuge"))
        import gehaeuse_bauen as gb
        tri = gb.lies_stl(f"out531/{name}.stl")
        out = os.path.join(DD, "v5-3", "MoveEye_v5-3_" + name + ".3mf")
        nf, e = gb.schreibe_3mf_teil(out, name, tri, cnt)
        print(f"  -> {os.path.relpath(out, HIER)}: {nf} Dreiecke, {' × '.join('%.2f' % x for x in e)} mm, {os.path.getsize(out) // 1024} KB")
