import time, zipfile, sys
import numpy as np
from skimage.measure import marching_cubes
import csg
from csg import rotm
import pantilt as pt
from decimate import cluster_qem, cluster_qem_manifold


def mesh(node, h):
    lo, hi = node.bbox()
    lo = lo - 2 * h; hi = hi + 2 * h
    n = np.ceil((hi - lo) / h).astype(int) + 1
    xs, ys, zs = [lo[i] + np.arange(n[i]) * h for i in range(3)]
    vol = np.empty(n, np.float32)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    XY = np.stack([X.ravel(), Y.ravel()], 1)
    for k, z in enumerate(zs):
        P = np.column_stack([XY, np.full(len(XY), z)])
        vol[:, :, k] = node.sdf(P).reshape(n[0], n[1])
    v, f, _, _ = marching_cubes(vol, 0.0, spacing=(h, h, h))
    v += lo
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    if np.einsum("ij,ij->i", a, np.cross(b, c)).sum() < 0:
        f = f[:, ::-1]
    return v, f


def orient(v, f, rot):
    v = v @ rotm(rot).T
    v[:, 2] -= v[:, 2].min()
    v[:, :2] -= (v[:, :2].min(0) + v[:, :2].max(0)) / 2
    return v, f


def write_stl(fn, v, f):
    tri = v[f].astype(np.float32)
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    arr = np.zeros(len(f), dt); arr["n"] = nrm; arr["v"] = tri
    with open(fn, "wb") as fh:
        fh.write(b"pantilt".ljust(80, b" ")); fh.write(np.uint32(len(f)).tobytes()); fh.write(arr.tobytes())


def write_3mf(fn, objs):
    parts = ['<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>']
    items = []
    for i, (name, v, f, off) in enumerate(objs, 1):
        vs = "".join(f'<vertex x="{x:.3f}" y="{y:.3f}" z="{z:.3f}"/>' for x, y, z in v)
        ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
        parts.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>{vs}</vertices>'
                     f'<triangles>{ts}</triangles></mesh></object>')
        items.append(f'<item objectid="{i}" transform="1 0 0 0 1 0 0 0 1 {off[0]:.2f} {off[1]:.2f} 0"/>')
    parts.append("</resources><build>" + "".join(items) + "</build></model>")
    with zipfile.ZipFile(fn, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", "".join(parts))


if __name__ == "__main__":
    jobs = [("1_Gehaeuse_Unterteil", pt.part_tub, 0.25, [0, 0, 0], (66, 45)),
            ("2_Deckel_mit_Laufring", pt.part_lid, 0.25, [0, 0, 0], (66, 130)),
            ("3_Drehteller", pt.part_turntable, 0.2, [180, 0, 0], (45, 215)),
            ("4_Gabel_mit_Arm1", pt.part_yoke, 0.2, [0, 0, 0], (215, 140)),
            ("5_Arm2_Lagerseite", pt.part_arm2, 0.2, [-90, 0, 0], (213, 45)),
            ("6_Kamerakopf", pt.part_head, 0.2, [-90, 0, 0], (160, 40)),
            ("7_Seitendeckel", pt.part_sidecover, 0.2, [90, 0, 0], (165, 105))]
    sel = sys.argv[1:]
    objs = []
    for name, fn, h, rot, off in jobs:
        if sel and name[0] not in sel:
            continue
        t0 = time.time()
        node = fn()
        v, f = mesh(node, h)
        v, f, nbad = cluster_qem_manifold(v, f, 0.6)
        err = np.abs(node.sdf(v)).max()
        v, f = orient(v, f, rot)
        write_stl(f"out41/{name}.stl", v, f)
        ext = v.max(0) - v.min(0)
        print(f"{name}: {len(f)} Dreiecke, maxErr {err:.3f}, offen {nbad}, {ext.round(1)} mm, {time.time() - t0:.0f}s", flush=True)
        objs.append((name, v, f, off))
        np.savez_compressed(f"out41/{name}.npz", v=v, f=f)
    if not sel:
        write_3mf("out41/PanTilt_v4-1_X2D_alle_Teile.3mf", objs)
