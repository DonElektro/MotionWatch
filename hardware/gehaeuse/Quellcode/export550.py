"""5.5.0: Schutzschale 31 vorne, 32 hinten und 33 Stopfen exportieren -> STL (+ .npz) AUSSERHALB des Repositorys (Ordner GEH_STL,
Standard <tmp>/gehaeuse_out550) und als einzelne 3MF nach Druckdateien/v5-3/MoveEye_v5-3_<Teil>.3mf (Format wie export540.py).
Gedreht für den Druck: 31 und 33 mit der Stirnseite auf dem Bett, 32 mit der Rückseite auf dem Bett.
python3 export550.py [vorne hinten stopfen]   (ca. 10–20 min)      python3 export550.py --nur-stl   (ohne 3MF)
Alle übrigen Teile bleiben genau wie v5.3 / 5.4.0 (Druckdateien/v5-3/)."""
import os, sys, time, tempfile, numpy as np
import schale550 as s
from export import mesh, orient, write_stl
from decimate import cluster_qem_manifold

HIER = os.path.dirname(os.path.abspath(__file__))
DD = os.environ.get("GEH_DRUCKDATEIEN") or os.path.join(HIER, "..", "Druckdateien")
OUT = os.environ.get("GEH_STL") or os.path.join(tempfile.gettempdir(), "gehaeuse_out550")
JOBS = {"vorne": ("31_Schutzschale_vorne", s.part_vorne, 0.3, [0, -90, 0], 1),       # Stirnseite unten
        "hinten": ("32_Schutzschale_hinten", s.part_hinten, 0.3, [0, 90, 0], 1),     # Rückseite unten
        "stopfen": ("33_Schutzschale_Stopfen", s.part_stopfen, 0.2, [0, -90, 0], 1)}  # Platte unten

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    wahl = [a for a in sys.argv[1:] if a in JOBS] or list(JOBS)
    for key in wahl:
        name, fn, h, rot, cnt = JOBS[key]
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
        print(f"  -> {os.path.relpath(out, HIER)}: {nf} Dreiecke, {' × '.join('%.2f' % x for x in e)} mm, {os.path.getsize(out) // 1024} KB", flush=True)
