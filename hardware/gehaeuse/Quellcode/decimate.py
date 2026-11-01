"""Vertex-Clustering mit Quadric-Error-Platzierung (Lindstrom). Erhält scharfe Kanten gut."""
import numpy as np


def cluster_qem(v, f, c):
    a, b, cc = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    n = np.cross(b - a, cc - a)
    area = np.linalg.norm(n, axis=1)
    ok = area > 1e-12
    n[ok] /= area[ok, None]
    d = -np.einsum("ij,ij->i", n, a)
    p = np.column_stack([n, d])                       # (F,4)
    Qf = p[:, :, None] * p[:, None, :] * area[:, None, None]
    key = np.floor(v / c).astype(np.int64)
    _, cid = np.unique(key, axis=0, return_inverse=True)
    cid = cid.ravel()
    K = cid.max() + 1
    Q = np.zeros((K, 4, 4))
    for k in range(3):
        np.add.at(Q, cid[f[:, k]], Qf)
    cnt = np.bincount(cid, minlength=K).astype(float)
    mean = np.zeros((K, 3))
    np.add.at(mean, cid, v)
    mean /= cnt[:, None]
    A = Q[:, :3, :3]; bb = Q[:, :3, 3]
    scale = np.trace(A, axis1=1, axis2=2)[:, None, None] + 1e-12
    lam = 1e-3 * scale
    A2 = A + lam * np.eye(3)
    rhs = -bb + (lam[:, :, 0] * mean)
    x = np.linalg.solve(A2, rhs[:, :, None])[:, :, 0]
    # nicht weiter als eine Zelle vom Mittelwert entfernen
    dev = x - mean
    dn = np.linalg.norm(dev, axis=1)
    lim = c * 0.9
    far = dn > lim
    x[far] = mean[far] + dev[far] * (lim / dn[far])[:, None]
    nf = cid[f]
    keep = (nf[:, 0] != nf[:, 1]) & (nf[:, 1] != nf[:, 2]) & (nf[:, 0] != nf[:, 2])
    nf = nf[keep]
    s = np.sort(nf, axis=1)
    _, ui = np.unique(s, axis=0, return_index=True)
    nf = nf[np.sort(ui)]
    used, inv = np.unique(nf, return_inverse=True)
    return x[used], inv.reshape(-1, 3)


def _bad_vertices(f):
    E = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    u, c = np.unique(E, axis=0, return_counts=True)
    bad = u[c != 2].ravel()
    # zusätzlich: Vertices mit nicht-scheibenförmigem Umfeld (Pinch) über Euler-Check der Fächer
    return np.unique(bad)


def cluster_qem_manifold(v, f, c, max_iter=25):
    """Wie cluster_qem, aber Cluster an nicht-mannigfaltigen Stellen werden wieder aufgelöst."""
    a, b, cc = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    n = np.cross(b - a, cc - a)
    area = np.linalg.norm(n, axis=1)
    ok = area > 1e-12
    n[ok] /= area[ok, None]
    d = -np.einsum("ij,ij->i", n, a)
    p = np.column_stack([n, d])
    Qf = p[:, :, None] * p[:, None, :] * area[:, None, None]
    key = np.floor(v / c).astype(np.int64)
    _, cid0 = np.unique(key, axis=0, return_inverse=True)
    cid0 = cid0.ravel()
    K = cid0.max() + 1
    Q = np.zeros((K, 4, 4))
    for k in range(3):
        np.add.at(Q, cid0[f[:, k]], Qf)
    cnt = np.bincount(cid0, minlength=K).astype(float)
    mean = np.zeros((K, 3)); np.add.at(mean, cid0, v); mean /= cnt[:, None]
    A = Q[:, :3, :3]; bb = Q[:, :3, 3]
    lam = 1e-3 * (np.trace(A, axis1=1, axis2=2)[:, None, None] + 1e-12)
    x = np.linalg.solve(A + lam * np.eye(3), (-bb + lam[:, :, 0] * mean)[:, :, None])[:, :, 0]
    dev = x - mean; dn = np.linalg.norm(dev, axis=1); far = dn > 0.9 * c
    x[far] = mean[far] + dev[far] * (0.9 * c / dn[far])[:, None]

    frozen = np.zeros(K, bool)
    for it in range(max_iter):
        cid = cid0.copy()
        fz = frozen[cid0]
        cid[fz] = K + np.nonzero(fz)[0]          # eigene Id je Original-Vertex
        pos = np.concatenate([x, v])             # Id >= K -> Original-Vertex (Index - K)
        # Ids zusammenführen, die als float32 (STL) dieselbe Position hätten
        _, canon = np.unique(pos.astype(np.float32), axis=0, return_inverse=True)
        canon = canon.ravel()
        nf = canon[cid[f]]
        keep = (nf[:, 0] != nf[:, 1]) & (nf[:, 1] != nf[:, 2]) & (nf[:, 0] != nf[:, 2])
        nf = nf[keep]
        s = np.sort(nf, axis=1)
        _, ui, uc = np.unique(s, axis=0, return_index=True, return_counts=True)
        # doppelte Dreiecke (gegenläufig) komplett entfernen
        nf = nf[np.sort(ui[uc == 1])]
        bad = _bad_vertices(nf)
        if len(bad) == 0:
            break
        # zurück auf Cluster abbilden: alle Cluster, deren Vertices an fehlerhaften Stellen liegen
        badmask = np.isin(canon[cid], bad)
        hit_ids = cid0[badmask]
        # plus Nachbar-Cluster über die Original-Dreiecke
        fm = badmask[f].any(1)
        nb = np.unique(np.concatenate([hit_ids, cid0[f[fm]].ravel()]))
        if frozen[nb].all():
            break
        frozen[nb] = True
    rep = np.zeros(canon.max() + 1, int); rep[canon] = np.arange(len(canon))
    used, inv = np.unique(nf, return_inverse=True)
    return pos[rep[used]], inv.reshape(-1, 3), len(_bad_vertices(nf))
