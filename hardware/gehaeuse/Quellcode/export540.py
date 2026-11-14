"""5.4.0: 29 Transportsicherung (Haube) und 30 Drehsperre-Klammer exportieren -> STL (+ .npz) AUSSERHALB des Repositorys
(Ordner GEH_STL, Standard <tmp>/gehaeuse_out540) und als einzelne 3MF nach Druckdateien/v5-3/MoveEye_v5-3_<Teil>.3mf (Format wie
gehaeuse_bauen.py --druck53). Gedreht für den Druck: Haube umgedreht (Dach unten), Klammer wie eingebaut.
python3 export540.py            (ca. 5–10 min)      python3 export540.py --nur-stl   (ohne 3MF)
Alle übrigen Teile bleiben genau wie v5.3 (Druckdateien/v5-3/)."""
import os, sys, time, tempfile, numpy as np
import kappe540, klammer540
from export import mesh, orient, write_stl
from decimate import cluster_qem_manifold

HIER = os.path.dirname(os.path.abspath(__file__))
DD = os.environ.get("GEH_DRUCKDATEIEN") or os.path.join(HIER, "..", "Druckdateien")
OUT = os.environ.get("GEH_STL") or os.path.join(tempfile.gettempdir(), "gehaeuse_out540")
JOBS = {"29_Transportsicherung": (kappe540.part_kappe, 0.3, [180, 0, 0], 1),        # umgedreht: Dach unten
        "30_Drehsperre_Klammer": (klammer540.part_klammer, 0.2, [0, 0, 0], 1)}   # wie eingebaut

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, (fn, h, rot, cnt) in JOBS.items():
        t0 = time.time()
        node = fn()
        v, f = mesh(node, h)
        v, f, nbad = cluster_qem_manifold(v, f, 0.6)
        err = np.abs(node.sdf(v)).max()
        v, f = orient(v, f, rot)
        stl = os.path.join(OUT, name + ".stl")
        write_stl(stl, v, f)
        np.savez_compressed(os.path.join(OUT, name + ".npz"), v=v, f=f)
        ext = v.max(0) - v.min(0)
        print(f"{name}: {len(f)} Dreiecke, maxErr {err:.3f}, offen {nbad}, {ext.round(2)} mm, {time.time() - t0:.0f}s -> {stl}", flush=True)
        if "--nur-stl" in sys.argv:
            continue
        sys.path.insert(0, os.path.join(HIER, "..", "..", "..", "werkzeuge"))
        import gehaeuse_bauen as gb
        tri = gb.lies_stl(stl)
        out = os.path.join(DD, "v5-3", "MoveEye_v5-3_" + name + ".3mf")
        nf, e = gb.schreibe_3mf_teil(out, name, tri, cnt)
        print(f"  -> {os.path.relpath(out, HIER)}: {nf} Dreiecke, {' × '.join('%.2f' % x for x in e)} mm, {os.path.getsize(out) // 1024} KB")
