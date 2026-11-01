"""v5.2: geänderte und neue Teile exportieren -> out52/*.stl (+ .npz).  Einzelne: python3 export52.py 01 06 12
Namen mit «_v52», wo ein Teil von v5.1 ersetzt wird (01_Unterteil_v52 statt 01_Unterteil)."""
import time, sys, os, numpy as np
import v52
from export import mesh, orient, write_stl
from decimate import cluster_qem_manifold

JOBS = {  # name: (fn, h, rot, count)
    "01_Unterteil_v52": (v52.part_tub, 0.3, [0, 0, 0], 1),
    "06_Kamerakopf_v52": (v52.part_head, 0.2, [-90, 0, 0], 1),
    "10_Stopfen_HDMI_USB_v52": (v52.part_service_plug, 0.2, [0, 0, 0], 1),
    "12_Blindstopfen_Weitwinkel": (v52.blind_wide, 0.1, [0, -90, 0], 1),
    "13_Stopfen_IR_LED": (v52.blind_ir, 0.08, [0, 0, 0], 1),
    "14_Diffusor_Status_LED": (v52.part_diffuser, 0.1, [0, 0, 0], 1),
    "15_Pupillenring": (v52.part_pupil, 0.06, [0, 0, 0], 1),
    "16_Stopfen_SD_v52": (v52.part_sd_plug, 0.1, [0, 0, 0], 1),
    "13_Entwicklungs_Sockel": (v52.part_sockel, 0.3, [0, 0, 0], 1),
    "17_Blindstopfen_Reserve": (v52.part_res_plug, 0.1, [0, 0, 0], 1),
}
if __name__ == "__main__":
    os.makedirs("out52", exist_ok=True)
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
        write_stl(f"out52/{name}.stl", v, f)
        np.savez_compressed(f"out52/{name}.npz", v=v, f=f)
        ext = v.max(0) - v.min(0)
        print(f"{name}: {len(f)} Dreiecke, maxErr {err:.3f}, offen {nbad}, {ext.round(2)} mm, {time.time() - t0:.0f}s", flush=True)
