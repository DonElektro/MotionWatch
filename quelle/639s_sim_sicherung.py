#@ MoveEye – Teil 639s: Sicherung des Simulators – Eintrag «Simulator» in Sicherung (Backup): ZIP vom Simulator abholen, ablegen, herunterladen, «Simulator wiederherstellen» (nur der Besitzer). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket «Sicherung im Simulator» (Daniel 01.11.2026). Der Simulator macht die Sicherung selbst (simulator3d/scripts/sicherung.gd,
# System → Sicherung): ZIP mit manifest.json (Version, Datum, Prüfsummen), ohne Zugangsdaten. Hier der Teil von MoveEye:
#   * «In die MoveEye-Sicherung senden» im Simulator = Auftrag mw_cmd «sim_sicherung» (350). MoveEye holt das ZIP selbst über
#     /control {"action": "sicherung", "do": "get", "name"} (der Simulator nimmt das nur vom verbundenen MoveEye / diesem PC an,
#     net.gd dangerous) und meldet {"do": "ack"}. So braucht der Simulator keine Anmeldedaten von MoveEye.
#   * Ablage: DATA_DIR/sim_sicherung/MoveEyeSim_Sicherung_<datum>_<zeit>_v<version>[_vorher].zip (0600, die neuesten
#     SIMSICH_KEEP bleiben) und - wenn die Sicherung auf einen Ordner / WebDAV eingestellt ist - zusätzlich dorthin
#     (backup_copy, 060; Telegram nimmt keine ZIP-Dateien).
#   * Einstellungen → Schutz → Sicherung (Web bkExtras 530, Fenster 570): Eintrag «Simulator» mit ⬇ und «Simulator
#     wiederherstellen». Nur der Besitzer (Administrator, nicht im Bedienermodus, kein App-Schlüssel). MoveEye schickt das ZIP
#     über /control {"do": "restore", "confirm": true, "zip_b64"}; der Simulator sichert vorher den jetzigen Stand
#     (…_vorher.zip, kommt als vorher_b64 zurück und wird hier als eigener Eintrag abgelegt = rückgängig machen) und startet neu.
# ----------------------------------------------------------------------------
_SIMSICH_RE = re.compile(r"^MoveEyeSim_Sicherung_\d{4}-\d\d-\d\d_\d\d-\d\d-\d\d_v[0-9A-Za-z.\-]{1,24}(_vorher)?\.zip$")
SIMSICH_MAX = 100 * 1024 * 1024          # = sicherung.gd MAX_MW
SIMSICH_KEEP = 10
SIMSICH = {"status": "", "t": 0.0, "busy": False}


def simsich_dir():
    return os.path.join(DATA_DIR, "sim_sicherung")


def simsich_list():
    """the stored backups of the simulator, newest first: [{name, kb, when, vorher, ver}]"""
    try:
        names = sorted((n for n in os.listdir(simsich_dir()) if _SIMSICH_RE.match(n)), key=lambda n: n[21:40], reverse=True)
    except OSError:
        names = []
    out = []
    for n in names[:SIMSICH_KEEP + 10]:
        try:
            out.append({"name": n, "kb": max(1, os.path.getsize(os.path.join(simsich_dir(), n)) // 1024),
                        "when": datetime.strptime(n[21:40], "%Y-%m-%d_%H-%M-%S").strftime("%d.%m.%Y %H:%M"),
                        "vorher": n.endswith("_vorher.zip"), "ver": n[42:].split("_")[0].removesuffix(".zip")})
        except (OSError, ValueError):
            pass
    return out


def simsich_path(name):
    n = os.path.basename(str(name or ""))
    p = os.path.join(simsich_dir(), n)
    return p if _SIMSICH_RE.match(n) and os.path.isfile(p) else None


def simsich_check(data):
    """is it a backup of the simulator? (ZIP with manifest.json app «MoveEye Sim») -> (ok, err, manifest)"""
    import io, zipfile
    if not data or len(data) > SIMSICH_MAX:
        return False, "backup empty or bigger than 100 MB", None
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            m = json.loads(z.read("manifest.json").decode("utf-8"))
            bad = z.testzip()
            if bad is None and isinstance(m, dict) and isinstance(m.get("files"), dict):   # the checksums of sicherung.gd
                import hashlib
                have = set(z.namelist())
                for rel, inf in m["files"].items():
                    if not isinstance(inf, dict) or rel not in have or \
                            hashlib.sha256(z.read(rel)).hexdigest() != str(inf.get("sha256") or ""):
                        bad = rel
                        break
    except (zipfile.BadZipFile, KeyError, ValueError, OSError, RuntimeError, EOFError):
        return False, "not a backup of the simulator (or damaged)", None
    if not isinstance(m, dict) or m.get("app") != "MoveEye Sim" or m.get("art") != "sicherung" or not isinstance(m.get("files"), dict) or bad is not None:
        return False, "not a backup of the simulator (or damaged)", None
    return True, "", m


def _simsich_prune():
    keep = [x["name"] for x in simsich_list()[:SIMSICH_KEEP]]
    try:
        for n in os.listdir(simsich_dir()):
            if _SIMSICH_RE.match(n) and n not in keep:
                os.remove(os.path.join(simsich_dir(), n))
    except OSError:
        pass


def simsich_store(name, data, src="simulator"):
    """put one backup into the store (and to the backup folder / WebDAV if set) -> (ok, err)"""
    n = os.path.basename(str(name or ""))
    if not _SIMSICH_RE.match(n):
        return False, "bad file name"
    ok, err, m = simsich_check(data)
    if not ok:
        return False, err
    d = simsich_dir()
    try:
        os.makedirs(d, exist_ok=True)
        os.chmod(d, 0o700)
        p = os.path.join(d, n)
        with open(p + ".part", "wb") as f:
            f.write(data)
        os.chmod(p + ".part", 0o600)
        os.replace(p + ".part", p)
    except OSError as e:
        return False, f"could not write the backup: {e}"
    _simsich_prune()
    SIMSICH.update(status=f"✓ {datetime.now().strftime('%H:%M')} {n}", t=time.time())
    log_event("sys", f"Simulator backup stored ({src}): {n}, {len(data) // 1024} kB, {int((m or {}).get('n') or 0)} files")
    if CFG.get("backup_type") in ("folder", "webdav"):        # the backup of MoveEye: also there (Telegram takes no ZIP)
        def cp():
            ok_, err_ = backup_copy(p, {"kind": "simulator"})
            if not ok_:
                log_event("sys", f"Simulator backup: copy to the backup ({CFG.get('backup_type')}) failed: {err_}"[:220])
        threading.Thread(target=cp, daemon=True, name="simsichcopy").start()
    return True, ""


def _simsich_post(d, timeout=120.0):
    req = urllib.request.Request(sim_base() + "/control", data=json.dumps(d).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "MotionWatch"})
    with _SIM_OPENER.open(req, timeout=timeout) as r:
        return json.loads(r.read())


def simsich_fetch(cmd):
    """mw_cmd «sim_sicherung» (350): fetch the ZIP from the simulator, store it, say «ack»"""
    import base64, hashlib
    name = str((cmd or {}).get("name") or "")[:120]
    ok, err = False, "bad file name"
    if _SIMSICH_RE.match(name):
        try:
            r = _simsich_post({"action": "sicherung", "do": "get", "name": name})
            data = base64.b64decode(str(r.get("zip_b64") or ""), validate=True) if r.get("ok") else b""
            if not r.get("ok"):
                ok, err = False, str(r.get("error") or "the simulator refused")[:120]
            elif hashlib.sha256(data).hexdigest() != str(r.get("sha256") or ""):
                ok, err = False, "the backup arrived damaged"
            else:
                ok, err = simsich_store(name, data, "simulator")
        except (OSError, ValueError, urllib.error.URLError) as e:
            ok, err = False, f"simulator not reachable: {e}"[:160]
    if not ok:
        SIMSICH.update(status="⚠ " + err, t=time.time())
        log_event("sys", f"Simulator backup not stored: {err}"[:220])
    try:
        _simsich_post({"action": "sicherung", "do": "ack", "name": name, "ok": ok, "error": tr_err(err, "de") if err else ""}, 10.0)
    except Exception:
        pass
    return ok, err


def simsich_restore(name, who="web"):
    """send a stored backup to the simulator: it backs up its present state first (comes back -> own entry), then restarts"""
    import base64
    p = simsich_path(name)
    if not p:
        return False, "not found", ""
    if not CFG.get("sim_on") or not SIM.get("ok"):
        return False, "simulator not connected - switch the simulation on first", ""
    if SIMSICH["busy"]:
        return False, "busy", ""
    SIMSICH["busy"] = True
    try:
        with open(p, "rb") as f:
            data = f.read()
        r = _simsich_post({"action": "sicherung", "do": "restore", "confirm": True, "name": os.path.basename(p),
                           "zip_b64": base64.b64encode(data).decode("ascii")}, 180.0)
    except (OSError, ValueError, urllib.error.URLError) as e:
        return False, f"simulator not reachable: {e}"[:160], ""
    finally:
        SIMSICH["busy"] = False
    if not r.get("ok"):
        e = str(r.get("error") or "the simulator refused")
        return False, ("only the owner, from this PC or the connected MoveEye" if e == "nur_lokal" else e)[:200], ""
    before = str(r.get("vorher_name") or "")
    if r.get("vorher_b64") and _SIMSICH_RE.match(before):
        try:
            simsich_store(before, base64.b64decode(str(r["vorher_b64"])), "before restore")
        except ValueError:
            pass
    log_event("sys", f"Simulator restored from {os.path.basename(p)} ({who}); its state before: {before or '-'}")
    SIMSICH.update(status=f"✓ {datetime.now().strftime('%H:%M')} " + tr("Simulator restored - it restarts"), t=time.time())
    return True, "", before


def simsich_routes(app, reply, body):
    from flask import request, Response, send_file, g
    for p_ in ("/api/sim/sicherung",):
        LOCK_DENY_PATHS.add(p_); APPKEY_DENY_PATHS.add(p_)

    def owner():
        return getattr(g, "role", "admin") == "admin" and not getattr(g, "appkey", None) and not CFG.get("lock_on")

    @app.route("/api/sim/sicherung", methods=["GET", "POST"])
    def api_sim_sicherung():
        lang = norm_lang(request.args.get("lang") or CFG["lang"])
        if not owner():
            return reply({"ok": False, "error": tr("not allowed for your user", lang)}, 403)
        if request.method == "GET":
            return reply({"ok": True, "list": simsich_list(), "status": SIMSICH["status"], "sim": bool(CFG.get("sim_on") and SIM.get("ok")),
                          "busy": SIMSICH["busy"], "copy": CFG.get("backup_type") in ("folder", "webdav")})
        d = body(); lang = norm_lang(d.get("lang") or lang)
        a = d.get("action")
        if a == "restore":
            if d.get("confirm") is not True:
                return reply({"ok": False, "error": "only with \"confirm\": true"}, 400)
            ok, err, before = simsich_restore(d.get("name"), "web " + (request.remote_addr or "?"))
            return reply({"ok": ok, "error": tr_err(err, lang) if err else None, "before": before}, 200 if ok else 400)
        if a == "delete":
            p = simsich_path(d.get("name"))
            if not p:
                return reply({"ok": False, "error": tr_err("not found", lang)}, 404)
            try:
                os.remove(p)
            except OSError as e:
                return reply({"ok": False, "error": str(e)[:120]}, 500)
            log_event("sys", f"Simulator backup deleted: {os.path.basename(p)}")
            return reply({"ok": True})
        return reply({"ok": False, "error": "unknown action"}, 400)

    @app.route("/api/sim/sicherung/<name>")
    def api_sim_sicherung_file(name):
        if not owner():
            return Response("not allowed", 403)
        p = simsich_path(name)
        if not p:
            return Response("not found", 404)
        return send_file(p, mimetype="application/zip", as_attachment=True, download_name=os.path.basename(p), max_age=0)


# ---- texts (DE / fr / it / rm; the key is the English text) ----
_HX_SIMSICH = {
    'Simulator': ('Simulator', 'Simulateur', 'Simulatore', 'Simulatur'),
    'Backups of the simulator: in the simulator System → Backup → «Send to the MoveEye backup». Restore = the simulator first backs up its present state (entry «before»), then it restarts.': (
        'Sicherungen des Simulators: im Simulator System → Sicherung → «In die MoveEye-Sicherung senden». Wiederherstellen = der Simulator sichert zuerst seinen jetzigen Stand (Eintrag «vorher»), dann startet er neu.',
        'Sauvegardes du simulateur : dans le simulateur Système → Sauvegarde → « Envoyer dans la sauvegarde MoveEye ». Restaurer = le simulateur sauvegarde d’abord son état actuel (entrée « avant »), puis il redémarre.',
        'Backup del simulatore: nel simulatore Sistema → Backup → «Invia al backup di MoveEye». Ripristinare = il simulatore salva prima il suo stato attuale (voce «prima»), poi si riavvia.',
        'Copias da segirezza dal simulatur: en il simulatur Sistem → Copia da segirezza → «Trametter en la copia da segirezza da MoveEye». Restaurar = il simulatur segira l’emprim ses stadi actual (inscripziun «avant»), lura s’avia el da nov.'),
    'No backup of the simulator yet.': ('Noch keine Sicherung des Simulators.', 'Pas encore de sauvegarde du simulateur.', 'Ancora nessun backup del simulatore.', 'Anc nagina copia da segirezza dal simulatur.'),
    'Restore simulator': ('Simulator wiederherstellen', 'Restaurer le simulateur', 'Ripristina il simulatore', 'Restaurar il simulatur'),
    'before': ('vorher', 'avant', 'prima', 'avant'),
    'Restore the simulator from this backup? Its present state is backed up first (you can undo it), then the simulator restarts.': (
        'Den Simulator aus dieser Sicherung wiederherstellen? Sein jetziger Stand wird vorher gesichert (rückgängig machen geht), dann startet der Simulator neu.',
        'Restaurer le simulateur depuis cette sauvegarde ? Son état actuel est d’abord sauvegardé (annulation possible), puis le simulateur redémarre.',
        'Ripristinare il simulatore da questo backup? Il suo stato attuale viene salvato prima (si può annullare), poi il simulatore si riavvia.',
        'Restaurar il simulatur ord questa copia da segirezza? Ses stadi actual vegn segirà avant (revocar è pussaivel), lura s’avia il simulatur da nov.'),
    'Delete this backup of the simulator?': ('Diese Sicherung des Simulators löschen?', 'Supprimer cette sauvegarde du simulateur ?', 'Eliminare questo backup del simulatore?', 'Stizzar questa copia da segirezza dal simulatur?'),
    'Simulator restored - it restarts': ('Simulator wiederhergestellt – er startet neu', 'Simulateur restauré – il redémarre', 'Simulatore ripristinato – si riavvia', 'Simulatur restaurà – el s’avia da nov'),
    'simulator not connected - switch the simulation on first': ('Simulator nicht verbunden – zuerst die Simulation einschalten', 'simulateur non connecté – activez d’abord la simulation', 'simulatore non connesso – attiva prima la simulazione', 'simulatur betg collià – l’emprim activar la simulaziun'),
    'only the owner, from this PC or the connected MoveEye': ('nur der Besitzer, von diesem PC oder vom verbundenen MoveEye', 'seulement le propriétaire, depuis ce PC ou le MoveEye connecté', 'solo il proprietario, da questo PC o dal MoveEye connesso', 'mo il proprietari, da quest PC u dal MoveEye collià'),
    'not a backup of the simulator (or damaged)': ('keine Sicherung des Simulators (oder beschädigt)', 'pas une sauvegarde du simulateur (ou endommagée)', 'non è un backup del simulatore (o è danneggiato)', 'nagina copia da segirezza dal simulatur (u donnegiada)'),
    'backup empty or bigger than 100 MB': ('Sicherung leer oder grösser als 100 MB', 'sauvegarde vide ou supérieure à 100 Mo', 'backup vuoto o più grande di 100 MB', 'copia da segirezza vida u pli gronda che 100 MB'),
    'the backup arrived damaged': ('die Sicherung kam beschädigt an', 'la sauvegarde est arrivée endommagée', 'il backup è arrivato danneggiato', 'la copia da segirezza è arrivada donnegiada'),
    'Also copied to the backup above (folder / WebDAV).': ('Wird auch in die Sicherung oben kopiert (Ordner / WebDAV).', 'Aussi copiée dans la sauvegarde ci-dessus (dossier / WebDAV).', 'Copiato anche nel backup sopra (cartella / WebDAV).', 'Vegn era copiada en la copia da segirezza survart (ordinatur / WebDAV).'),
}
for _k, _v in _HX_SIMSICH.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
