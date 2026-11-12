#@ MoveEye – Teil 545: Simulator-Updates: ein Besitzer (die Einstellung «Neue Versionen» des Simulators), MoveEye zeigt und stellt sie. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ---- 2.98.13: simulator updates have one owner - the simulator's own setting «Neue Versionen» (update_mode) -----------------
# MoveEye's switch «Update the simulator by itself» (sim_autoupd, web and window) shows and sets that setting through
# /control when the connected simulator has it; MoveEye then no longer presses «update_now» itself (300). For the Python
# simulator on the Pi (installed from inside MoveEye) the switch keeps working as before.
SIMUPD = {"t": 0.0, "mode": None, "synced": None}


def simupd_mode():
    """'off' | 'auto' | 'dev' of the connected simulator, None = it has no such setting (or not reachable)"""
    try:
        d = sim_control(None)
    except Exception:
        return None
    for c in d.get("controls") or []:
        if isinstance(c, dict) and c.get("id") == "update_mode":
            return str(c.get("value") or "off")
    return None


def simupd_push(on):
    """MoveEye's switch was changed: set the simulator's setting (keeps «dev» when it is already on)"""
    m = SIMUPD["mode"] if SIMUPD["mode"] is not None else simupd_mode()
    if m is None:
        return False
    want = ("dev" if m == "dev" else "auto") if on else "off"
    if want != m:
        try:
            sim_control({"action": "set", "id": "update_mode", "value": want})
        except Exception:
            return False
        log_event("sys", f"Simulator updates: {want} (set in MoveEye)")
    SIMUPD.update(mode=want, synced=bool(on), t=time.time())
    return True


def simupd_sync():
    """every 15 s while connected: whoever changed last wins - MoveEye's switch (web / window) or the simulator window"""
    if not sim_ready() or time.time() - SIMUPD["t"] < 15:
        return
    SIMUPD["t"] = time.time()
    m = simupd_mode()
    SIMUPD["mode"] = m
    if m is None:
        SIMUPD["synced"] = None
        return
    sim_on_ = m != "off"
    mine = bool(CFG.get("sim_autoupd", True))
    if SIMUPD["synced"] is None:                               # just connected: the simulator owns the setting
        SIMUPD["synced"] = sim_on_
        if mine != sim_on_:
            CFG["sim_autoupd"] = sim_on_; save_settings()
        return
    if mine != SIMUPD["synced"]:                               # changed in MoveEye (window) since the last look
        simupd_push(mine)
    elif sim_on_ != SIMUPD["synced"]:                          # changed in the simulator window
        SIMUPD["synced"] = sim_on_
        CFG["sim_autoupd"] = sim_on_; save_settings()


def sim_owns_updates():
    return SIMUPD.get("mode") is not None

# set_cfg (540) passes «sim_autoupd» changed on the web page to the simulator (_set_cfg_sim -> simupd_push)


# ---- Versionierung 3.0.0 (Besitzer 31.10.2026): MoveEye and the simulator share one number X.Y.Z from 3.0.0 («MoveEye 3.0.0» /
# «MoveEye Sim 3.0.0»). simulator3d/version.json keeps «version» = «3D-(X+2).Y.Z» for old simulators (they only compare that
# field: 3.0.0 would be older than 3D-4.82 for them) and has the real number in «ver». The self-test checks the order of the
# numbers and - in the repository (GitHub) - that version.json, SIM3D and APP_VERSION fit together.
# Drei Spuren (Besitzer 03.11.2026, bis zum Zusammenführen): MoveEye, the simulator and the case each have their own number and
# are released on their own. Instead of «the same number» each side names the OLDEST version of the other it works with:
# SIM_MIN here (MoveEye -> simulator, sent as «sim_min» in the state, 639zb) and MW_MIN in simulator3d/scripts/abgleich.gd
# (simulator -> MoveEye, sent as «mw_min» in /info, also in version.json). Raise it when the interface (schnittstelle.json)
# changes in a way the older side cannot follow. The version pair (639zb / abgleich.gd) only warns below the minimum.
SIM_MIN = "3.55.0"


def versionen_selftest():
    order = ["2.98.113", "2.98.114", "3.0.0", "3.0.1", "3.1.0", "3.1.1", "3.10.0", "4.0.0"]
    for a, b in zip(order, order[1:]):
        assert _vkey(a) < _vkey(b), f"MoveEye {a} < {b}"
        assert VFILE_RE.match("webcam_bewegung_%s.py" % b.replace(".", "_")) and VER_RE.match(b), f"file name / number {b}"
    sims = ["3D-4.82", "3D-4.83", "3.0.0", "3.0.1", "3.1.0", "3.10.0", "4.0.0"]
    for a, b in zip(sims, sims[1:]):
        assert sim_vkey(a) < sim_vkey(b), f"simulator {a} < {b}"
    assert sim_vkey("3D-5.0.0") == sim_vkey("3.0.0") == sim_vkey("MoveEye Sim 3.0.0") == (3, 0, 0), "bridge 3D-5.0.0 = 3.0.0"
    assert sim_vlegacy("3.0.0") == "3D-5.0.0" and sim_vlegacy("3.10.2") == "3D-5.10.2" and sim_vlegacy("3D-4.82") == "3D-4.82"
    assert VER_RE.match(SIM_MIN) and sim_vkey(SIM_MIN) <= sim_vkey(SIM3D_EMBED["version"]), f"SIM_MIN {SIM_MIN} newer than the own simulator"
    p = os.path.join(HERE, "simulator3d", "version.json")
    if not os.path.isfile(p):
        return None                                               # on the Pi: no repository next to the program
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    ver, old = str(d.get("ver") or ""), str(d.get("version") or "")
    assert old.startswith("3D-"), f"version.json «version» must stay «3D-…» for old simulators (is {old!r})"
    if ver:
        assert old == sim_vlegacy(ver), f"version.json: «version» {old} must be {sim_vlegacy(ver)} (= {ver} for old simulators)"
        # 3 tracks (Besitzer 03.11.2026): each part has its own number - the simulator of this MoveEye may be older than the
        # one in the repository (a release of the simulator alone), never newer
        assert sim_vkey(SIM3D_EMBED["version"]) <= sim_vkey(ver), f"SIM3D {SIM3D_EMBED['version']} newer than version.json {ver}"
        assert sim_vkey(SIM_MIN) <= sim_vkey(ver), f"MoveEye needs simulator {SIM_MIN}, version.json has {ver}"
        mm = str(d.get("mw_min") or "")
        assert not mm or (VER_RE.match(mm) and _vkey(mm) <= _vkey(APP_VERSION)), f"the simulator {ver} needs MoveEye {mm} (this is {APP_VERSION})"
    return f"MoveEye {APP_VERSION} · Sim {ver or old} (old simulators read {old}) · needs Sim ≥ {SIM_MIN}" + (
        f", Sim needs MoveEye ≥ {d.get('mw_min')}" if d.get("mw_min") else "")


SELFTEST_EXTRA.append(("Version numbers: order, file names, bridge for old simulators, minimum of the other track (3 tracks)", versionen_selftest))


def sim_manifest_selftest():
    """3 tracks: a correctly signed «sim» block of versions.json is taken, a changed / unsigned / foreign one is not - with a
    TEST key made here (never the signing key; the public key is swapped only during this test)"""
    import hashlib
    keep = ({k: SIM3D[k] for k in SIM3D_EMBED}, {k: SIM3D_LINUX[k] for k in SIM3D_LINUX_EMBED}, dict(SIMMAN))
    g = globals()
    real = g["UPDATE_PUBKEY"]
    try:
        if not _ED:
            _ED.extend(_ed25519_impl())
        seed = hashlib.sha256(b"MoveEye self-test key - not the signing key").digest()
        a, b, c = sim_vkey(SIM3D_EMBED["version"])
        nv = "%d.%d.%d" % (a, b, c + 1)
        sha = hashlib.sha256(b"fake simulator zip").hexdigest()

        def blk(v=nv, fn=SIM3D["file"], sh=sha, key=seed, lx=False):
            e = {"ver": v, "file": fn, "size": 18, "sha256": sh, "sig": _ED[1](key, _sig_msg(v, fn, sh)).hex()}
            r = {"ver": v, "win": e}
            if lx:
                fl = SIM3D_LINUX["file"]
                r["linux"] = {"ver": v, "file": fl, "size": 19, "sha256": sh, "sig": _ED[1](key, _sig_msg(v, fl, sh)).hex()}
            return r

        def back():
            SIM3D.update(SIM3D_EMBED); SIM3D_LINUX.update(SIM3D_LINUX_EMBED)
        g["UPDATE_PUBKEY"] = _ED[0](seed).hex()                    # sig_ok (380) checks against this - the test key
        assert sim_manifest_take(blk(lx=True), save=False) == ["win", "linux"], "signed entries not taken"
        assert SIM3D["version"] == nv and SIM3D["sha256"] == sha and SIM3D["size"] == 18 and SIM3D_LINUX["size"] == 19, "values"
        assert sim3d_path().endswith("_" + nv + ".zip"), "cache name of the new simulator"
        back()
        bad = {"changed checksum": dict(blk(), win=dict(blk()["win"], sha256=hashlib.sha256(b"other").hexdigest())),
               "changed number": dict(blk(), win=dict(blk()["win"], ver="%d.%d.%d" % (a, b, c + 2))),
               "unsigned": dict(blk(), win={k: v for k, v in blk()["win"].items() if k != "sig"}),
               "broken signature": dict(blk(), win=dict(blk()["win"], sig="00" * 64)),
               "other key": blk(key=hashlib.sha256(b"another key").digest()),
               "other file": blk(fn="simulator3d/anders.zip"),
               "program file name": blk(fn="webcam_bewegung_9_9_9.py"),
               "not a dict": "x"}
        if c > 0:
            bad["older simulator"] = blk(v="%d.%d.%d" % (a, b, c - 1))
        for what, x in bad.items():
            assert not sim_manifest_take(x, save=False), f"{what} taken"
            assert SIM3D["sha256"] == SIM3D_EMBED["sha256"] and SIM3D["version"] == SIM3D_EMBED["version"], f"{what}: values changed"
        # Simulator-Anhang (300): a newer package as Release asset under «anhang» - taken with its address; anything that is
        # not exactly «signed + own file name + the address that follows from the number» leaves the repository package
        nv2 = "%d.%d.%d" % (a, b, c + 2)
        fa = SIM3D_ANHANG["win"][0]

        def ah(v=nv2, fn=fa, key=seed, url=None, sig=True):
            e = {"ver": v, "file": fn, "size": 20, "sha256": sha, "url": sim_anhang_url("win", v) if url is None else url}
            if sig:
                e["sig"] = _ED[1](key, _sig_msg(v, fn, sha)).hex()
            return dict(blk(), anhang={"ver": v, "win": e})
        back()
        assert sim_manifest_take(ah(), save=False) == ["win"], "signed asset entry not taken"
        assert SIM3D["version"] == nv2 and SIM3D["size"] == 20 and SIM3D["url"] == sim_anhang_url("win", nv2), "asset values"
        assert SIM3D["url"].startswith(SIM3D_ANHANG_BASE + "sim-" + nv2 + "/") and SIM3D_LINUX["url"] == "", "asset address"
        assert not sim_manifest_take(blk(), save=False) and SIM3D["version"] == nv2, "went back from the asset to an older package"
        bad_a = {"other host": ah(url="https://example.org/sim-%s/%s" % (nv2, SIM3D_ANHANG["win"][1])),
                 "address of an other number": ah(url=sim_anhang_url("win", nv)),
                 "no address": ah(url=""),
                 "repository file name": ah(fn=SIM3D["file"]),
                 "unsigned": ah(sig=False),
                 "other key": dict(blk(), anhang=ah(key=hashlib.sha256(b"another key").digest())["anhang"]),
                 "not a dict": dict(blk(), anhang="x")}
        for what, x in bad_a.items():
            back()
            assert sim_manifest_take(x, save=False) == ["win"] and SIM3D["version"] == nv and SIM3D["url"] == "", f"asset {what}: not the repository package"
        back()
        moved = dict(blk(), win=ah()["anhang"]["win"])             # an asset entry at the place of the repository package
        assert not sim_manifest_take(moved, save=False) and SIM3D["version"] == SIM3D_EMBED["version"], "asset entry taken as repository package"
        back()
        assert sim_manifest_take(ah(v=nv), save=False) == ["win"] and SIM3D["url"] == "", "same number: the repository package wins"
        back()
        g["UPDATE_PUBKEY"] = real
        assert not sim_manifest_take(blk(), save=False), "test key accepted with the real public key"
        assert not sim_manifest_take(ah(), save=False) and SIM3D["url"] == "", "asset with the test key accepted with the real public key"
    finally:
        g["UPDATE_PUBKEY"] = real
        SIM3D.update(keep[0]); SIM3D_LINUX.update(keep[1]); SIMMAN.clear(); SIMMAN.update(keep[2])
    return "signed «sim» entry taken; changed, unsigned, other key / file, older refused; asset entry («anhang») only signed with its own address (test key)"


SELFTEST_EXTRA.append(("Simulator checksums from the signed versions.json (3 tracks, 300)", sim_manifest_selftest))
