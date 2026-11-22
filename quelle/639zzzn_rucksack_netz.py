#@ MoveEye – Teil 639zzzn: «Digitaler Rucksack» im Netzwerk – Freigabe «rucksack» über SMB (Samba) für Windows, Mac und iPhone: Schalter nur für den Admin (ab Werk aus), eigenes Passwort, Samba auf Wunsch einmal installieren, eigene Datei /etc/samba/moveeye.conf, Abgleich Netzwerk ↔ Rucksack mit den Regeln des Rucksacks. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Auftrag des Besitzers (14.11.2026): den Digitalen Rucksack im Netzwerk freigeben (SMB), lesen und schreiben.
#   * Schalter «Im Netzwerk freigeben (Windows/Mac/iPhone)» in Einstellungen → System → Digitaler Rucksack, nur der Admin
#     (Web: Rolle admin und kein App-Schlüssel; Benutzer mit «Einstellungen» kommen nicht an tausch_smb: USER_SETTINGS_DENY).
#     Ab Werk aus. Fehlt Samba, fragt die Seite zuerst «Samba wird einmal installiert (ca. 10 MB). Weiter?».
#   * Benutzername fest «rucksack» (ein Systembenutzer ohne Anmeldung, ohne Heimordner), eigenes Passwort: der Admin setzt,
#     ändert oder löscht es. MoveEye speichert es NIE: es geht nur über stdin an «smbpasswd -s» (Samba hält den Hash in seiner
#     root-Datenbank) und liegt bis dahin höchstens 10 Min. im Speicher (wenn Samba zuerst installiert wird). Nicht in Protokoll,
#     Einstellungen, Export, Push oder Status; gesetzt wird es nur über die sichere Seite (https), wie die anderen Passwörter (574).
#   * Rechte für die System-Schritte: derselbe Weg wie Piper/espeak-ng (639zzb), Dienst-Datei (140) und Ausschalten (400):
#     als root direkt, sonst «sudo -n» (geht nur, wenn sudo kein Passwort will – der erste Benutzer von Raspberry Pi OS). Keine
#     neue sudo-Regel. Will sudo ein Passwort, zeigt die Seite die genauen Befehle zum Kopieren (SMB["cmds"]).
#   * Warum eine eigene Datei statt «usershare»: usershares können weder ein eigenes Passwort / einen Benutzer anlegen (smbpasswd
#     braucht root) noch SMB2+, Netz-Bindung und «kein Gast» festlegen (das sind globale Werte). Darum /etc/samba/moveeye.conf,
#     am Ende von smb.conf eingebunden (eine Zeile, vorher eine Kopie smb.conf.vor-moveeye). Inhalt: [global] SMB2 als
#     Minimum, nur Port 445, kein Gast (map to guest = never, restrict anonymous = 2), keine Drucker (auch [printers] / [print$]
#     der Debian-Vorlage abgeschaltet), nur die privaten IPv4-Adressen der LAN-/WLAN-Schnittstellen (bind interfaces only; nicht
#     Tailscale, Docker, LTE), dazu hosts allow nur private Netze; [rucksack]: valid users = rucksack, force user = Besitzer des
#     Rucksack-Ordners (nie root), versteckte Dateien weg (veto /.*/ + hide dot files), Programme per Endung abgewiesen (veto,
#     wie tausch_block_exec), keine Verknüpfungen nach aussen, max disk size = Platz des Rucksacks, Verschlüsselung erwünscht.
#     Aus = die Datei wird leer (nur ein Kommentar), Konto «rucksack» gesperrt, Samba neu geladen; hat MoveEye smbd selbst
#     gestartet, wird es wieder gestoppt. Samba bleibt installiert.
#   * Der Ordner: der Rucksack speichert Dateien als Nummern (f/<id>.bin + .json, 639zzc), das darf das Netz nicht sehen. Die
#     Freigabe zeigt darum <Rucksack>/netz mit «Für alle» als lesbare Namen (Ordner = eine Ebene) – als feste Verknüpfungen
#     (hardlink) auf dieselben Daten, kein doppelter Platz. Private Dateien («Meine Dateien») und Chats sind nicht im Netz.
#     Abgleich (smb_sync, alle 10 s und beim Öffnen der Rucksack-Seite): neue Dateien aus dem Netz werden übernommen, sobald sie
#     5 s ruhen (Namen bereinigt, Programme / zu gross / Rucksack voll / zu wenig frei → gelöscht, mit Grund auf der Seite und im
#     Protokoll), umbenannt / verschoben / gelöscht im Netz = im Rucksack auch, neue Ordner = Rucksack-Ordner; im Browser
#     Hochgeladenes erscheint im Netz, Gelöschtes verschwindet. Nur auf einem Speicher mit festen Verknüpfungen (Karte, ext4) –
#     FAT / exFAT-Sticks: Fehler mit Grund.
#   * Nicht durchsetzbar über SMB (ehrlich in der Anleitung und auf der Seite): Grösse pro Datei, Platz und «2 GB frei» gelten
#     erst nach dem Schreiben (die Datei wird dann gelöscht); eine im Netz direkt geänderte Datei bekommt keine Version im
#     Rucksack; die ersten Bytes (Programm-Kennung) prüft erst der Abgleich.
# Tests: werkzeuge/rucksack_smb_test.py (falsche Samba-/sudo-Schicht; mit --e2e echtes smbd + smbclient, falls installiert).
# ----------------------------------------------------------------------------
for _k, _v in {"tausch_smb": False, "tausch_smb_st": {}}.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.update({"tausch_smb", "tausch_smb_st"})
LOCK_DENY_PATHS.add("/api/tausch/smb")                    # operator mode (390)

# Programmtext in der ZIP (Hauptdatei kleiner, 22.11.2026; Muster 639zzzzk / 639zzzzm): ab Zeile 63 steht der Teil in EINEM
# Literal SMB_PY - bauen.py legt es in die Zusatz-ZIP (über ZD_SHA256 mit signiert), zd_exec führt es hier aus (Zeilennummern wie
# in dieser Datei). Keine Start-, Schutz-, Alarm-, Update- oder Reparatur-Funktion: ohne ZIP fehlt der Teil einfach. Was ohne
# ZIP gelten muss (Einstellungen, Sperrlisten), steht oben ausserhalb des Literals.


if "zd_exec" not in globals():                              # only without 639zzzzk (Blinki defines it first)
    # wraps: zd_exec
    def zd_exec(src, name):
        """run the program text of a part that bauen.py moved into the data zip (same as 639zzzzk): src comes from _zd (Teil
        012), i.e. only from a zip whose SHA-256 matched ZD_SHA256 of this signed program. Real file name for compile +
        linecache (tracebacks show the lines of the part). Only for functions outside start, protection, alarm, update, repair."""
        if not src:
            return False
        import linecache
        linecache.cache[name] = (len(src), None, src.splitlines(True), name)
        exec(compile(src, name, "exec"), globals())
        return True


SMB_PY = r'''

SMB_USER = "rucksack"                                     # the user name of the share (shown on the page)
SMB_SHARE = "rucksack"
SMB_DIR = "netz"                                          # <Rucksack>/netz = the shared folder
SMB_QUIET = 5.0                                           # s: a new file from the network must rest this long
SMB_PW_KEEP = 600.0                                       # s: a password waiting for the installation of Samba (memory only)
SMB = {"etc": "/etc/samba", "lock": threading.RLock(), "sync": threading.Lock(), "busy": "", "err": "", "cmds": [], "pw": None,
       "want": None, "pend": {}, "rej": deque(maxlen=8), "run": False, "root": None, "S": None, "t_sync": 0.0, "t_lan": 0.0,
       "lan": None, "active": (0.0, False), "conf": ""}
_SMB_NET = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16")
_SMB_SKIP_IF = re.compile(r"^(lo|docker|br-|veth|virbr|lxc|tailscale|zt|wg|tun|tap|ppp|wwan|usb)")
_SMB_DENIED = re.compile(r"password is required|terminal is required|not in the sudoers|may not run sudo|no sudo", re.I)


def smb_sys(cmd, inp=None, timeout=60, root=True):
    """(rc, text) of a system command. root=True: as root directly, otherwise «sudo -n» (never a password question). The Samba
    password only ever goes through inp (stdin), never into cmd, a log line or a file."""
    pre = ["sudo", "-n"] if root and not _is_root() else []
    if pre and not shutil.which("sudo"):
        return 127, "no sudo"
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive", APT_LISTCHANGES_FRONTEND="none", LC_ALL="C")
    kw = {"input": inp} if inp is not None else {"stdin": subprocess.DEVNULL}
    try:
        r = subprocess.run(pre + cmd, capture_output=True, text=True, timeout=timeout, env=env, **kw)
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        return -9, "timeout"
    except OSError as e:
        return 127, str(e)


def smb_have():
    return bool(shutil.which("smbd") or os.path.exists("/usr/sbin/smbd"))


def smb_lan(now=None):
    """[(interface, "ip/prefix")]: private IPv4 networks of real LAN / Wi-Fi interfaces (cached 60 s)"""
    now = time.time() if now is None else now
    if SMB["lan"] is not None and now - SMB["t_lan"] < 60:
        return SMB["lan"]
    import ipaddress
    nets = [ipaddress.ip_network(n) for n in _SMB_NET]
    _rc, out = smb_sys(["ip", "-o", "-4", "addr", "show"], root=False, timeout=10)
    res = []
    for m in re.finditer(r"^\d+:\s+(\S+)\s+inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)", out, re.M):
        nm = m.group(1).split("@")[0]
        try:
            a = ipaddress.ip_address(m.group(2))
        except ValueError:
            continue
        if not _SMB_SKIP_IF.match(nm) and any(a in n for n in nets) and (nm, f"{a}/{m.group(3)}") not in res:
            res.append((nm, f"{a}/{m.group(3)}"))
    SMB.update(lan=res, t_lan=now)
    return res


def smb_unix_user():
    """the Linux user that owns the Rucksack (Samba writes as this user) - never root"""
    import pwd
    root = tausch_root()[0]
    try:
        uid = os.stat(root).st_uid if root and os.path.isdir(root) else os.getuid()
        return pwd.getpwuid(uid).pw_name if uid else ""
    except (KeyError, OSError):
        return ""


def smb_conf(path, user, lan, quota_mb, veto_ext):
    """the text of /etc/samba/moveeye.conf for the share (on)"""
    ifs = " ".join(["127.0.0.1/8"] + [x[1] for x in lan])
    veto = "/.*/" + "".join(f"*.{e}/" for e in sorted(veto_ext))
    return "\n".join([
        "# MoveEye: Digitaler Rucksack im Netzwerk - written by MoveEye, do not change by hand (switch: Settings -> Digital backpack)",
        "[global]", "   server min protocol = SMB2", "   smb ports = 445", f"   interfaces = {ifs}", "   bind interfaces only = yes",
        "   map to guest = never", "   restrict anonymous = 2", "   usershare allow guests = no", "   load printers = no",
        "   printing = bsd", "   printcap name = /dev/null", "   disable spoolss = yes", f"   max disk size = {int(quota_mb)}",
        "[printers]", "   available = no", "[print$]", "   available = no",
        f"[{SMB_SHARE}]", "   comment = MoveEye", f"   path = {path}", f"   valid users = {SMB_USER}", f"   force user = {user}",
        "   read only = no", "   guest ok = no", "   browseable = yes",
        "   hosts allow = 127.0.0.1 10. 172.16.0.0/255.240.0.0 192.168. 169.254.", "   hosts deny = ALL",
        "   hide dot files = yes", f"   veto files = {veto}", "   delete veto files = yes",
        "   follow symlinks = no", "   wide links = no", "   create mask = 0640", "   directory mask = 0750",
        "   server smb encrypt = desired", ""])


SMB_CONF_OFF = "# MoveEye: Digitaler Rucksack im Netzwerk - off (no share)\n"


def smb_wanted():
    """(conf text, "" or english reason) for the switch as it is"""
    if not (CFG.get("tausch_smb") and CFG.get("tausch_on", True)):
        return SMB_CONF_OFF, ""
    root, _k, prob = tausch_root()
    if not root or prob == "missing":
        return "", "the storage (USB stick / SSD) is not there"
    if prob == "ro":
        return "", "the memory card is write-protected"
    lan = smb_lan()
    if not lan:
        return "", "no home network found (Wi-Fi / LAN)"
    user = smb_unix_user()
    path = os.path.join(root, SMB_DIR)
    if not user or not re.match(r"^[a-z_][a-z0-9_.-]{0,31}$", user):
        return "", "the folder of the backpack belongs to root - start MoveEye as a normal user"
    if not re.match(r"^/[A-Za-z0-9_ ./+@-]+$", path):
        return "", "the path of the backpack has unusual signs"
    ext = TZ_BLOCK_EXT if CFG.get("tausch_block_exec", True) else ()
    return smb_conf(path, user, lan, tausch_limits()["total"] // TZ_MB, [e for e in ext if re.match(r"^[a-z0-9-]+$", e)]), ""


def _smb_links_ok(root):
    """can this storage hold two names for one file (hardlink)? FAT / exFAT cannot"""
    a, b = os.path.join(root, "up", ".smb_link_test"), os.path.join(root, SMB_DIR, ".smb_link_test")
    try:
        os.makedirs(os.path.dirname(b), exist_ok=True)
        open(a, "wb").close()
        if os.path.exists(b):
            os.remove(b)
        os.link(a, b)
        return True
    except OSError:
        return False
    finally:
        for p in (a, b):
            try:
                os.remove(p)
            except OSError:
                pass


def _smb_step(cmd, why, inp=None, timeout=60):
    """one root step: "" or the english reason (no rights -> the reason that shows the commands)"""
    rc, out = smb_sys(cmd, inp, timeout)
    if rc == 0:
        return ""
    if _SMB_DENIED.search(out) or rc == 127 and "sudo" in out:
        return "no rights"
    return f"{why}: {(out.splitlines() or ['?'])[-1][:120] if rc != -9 else 'timeout'}"


def smb_install():
    """apt-get install samba (once, after the confirmation on the page) -> "" or the english reason"""
    if smb_have():
        return ""
    apt = shutil.which("apt-get")
    if not apt:
        return "no apt-get on this system"
    inst = [apt, "install", "-y", "--no-install-recommends", "-o", "Dpkg::Options::=--force-confold", "samba"]
    rc, out = smb_sys(inst, timeout=900)
    if rc != 0 and re.search(r"Unable to locate package|has no installation candidate|404\s+Not Found|Failed to fetch", out):
        if smb_sys([apt, "update"], timeout=600)[0] == 0:
            rc, out = smb_sys(inst, timeout=900)
    if rc == 0 and smb_have():
        log_event("sys", "Digital backpack: Samba installed (apt) for the network share")
        st = dict(CFG.get("tausch_smb_st") or {}, mine=True)
        CFG["tausch_smb_st"] = st
        save_settings()
        return ""
    low = out.lower()
    if _SMB_DENIED.search(out):
        return "no rights"
    if rc == -9:
        return "apt took too long - try again later"
    if "could not get lock" in low or "dpkg frontend lock" in low:
        return "apt is busy right now (another installation or update) - try again in a few minutes"
    if "temporary failure resolving" in low or "could not resolve" in low or "failed to fetch" in low:
        return "no internet for apt - try again with internet"
    return "apt: " + ((out.splitlines() or ["?"])[-1][:120])


def smb_write_conf(text):
    """our include file + once the include line in smb.conf -> "" or the english reason"""
    d = os.path.join(DATA_DIR, "samba")
    os.makedirs(d, exist_ok=True)
    mine = os.path.join(d, "moveeye.conf")                 # also the source of the commands to copy (no secret inside)
    with open(mine, "w", encoding="utf-8") as f:
        f.write(text)
    etc = SMB["etc"]
    dst = os.path.join(etc, "moveeye.conf")
    if text != SMB_CONF_OFF and shutil.which("testparm"):
        rc, out = smb_sys(["testparm", "-s", "--suppress-prompt", mine], root=False, timeout=30)
        if rc != 0:
            return "Samba refused the settings: " + ((out.splitlines() or ["?"])[-1][:120])
    try:
        with open(dst, encoding="utf-8") as f:
            same = f.read() == text
    except OSError:
        same = False
    if not same:
        e = _smb_step(["install", "-m", "644", "-o", "root", "-g", "root", mine, dst], "install")
        if e:
            return e
    main = os.path.join(etc, "smb.conf")
    try:
        with open(main, encoding="utf-8") as f:
            cur = f.read()
    except OSError:
        cur = ""
    line = f"include = {dst}"
    if not re.search(r"^\s*include\s*=\s*" + re.escape(dst) + r"\s*$", cur, re.M):
        tmp = os.path.join(d, "smb.conf.neu")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(cur.rstrip("\n") + ("\n" if cur else "") + "\n# MoveEye (Digitaler Rucksack im Netzwerk)\n" + line + "\n")
        if cur:
            _smb_step(["cp", "-n", main, main + ".vor-moveeye"], "cp")
        e = _smb_step(["install", "-m", "644", "-o", "root", "-g", "root", tmp, main], "install")
        try:
            os.remove(tmp)
        except OSError:
            pass
        if e:
            return e
    return ""


def smb_user_ok():
    """the system user «rucksack» (no login, no home) - "" or the english reason"""
    import pwd
    try:
        u = pwd.getpwnam(SMB_USER)
        if u.pw_uid >= 1000 or not u.pw_shell.endswith(("nologin", "false")):
            return f"a user «{SMB_USER}» exists already and is not the one of MoveEye"
        return ""
    except KeyError:
        return _smb_step(["useradd", "--system", "--no-create-home", "--home-dir", "/nonexistent", "--shell", "/usr/sbin/nologin",
                          "--user-group", SMB_USER], "useradd")


def smb_pw_store(pw):
    """the password into Samba's own database (stdin only) -> "" or the english reason"""
    e = smb_user_ok() or _smb_step(["smbpasswd", "-s", "-a", SMB_USER], "smbpasswd", inp=f"{pw}\n{pw}\n", timeout=30)
    if not e and not CFG.get("tausch_smb"):
        _smb_step(["smbpasswd", "-d", SMB_USER], "smbpasswd")     # set while off: the account stays locked
    if not e:
        CFG["tausch_smb_st"] = dict(CFG.get("tausch_smb_st") or {}, pw=int(time.time()))
        save_settings()
        log_event("sys", "Digital backpack: password of the network share set")
    return e


def smb_pw_check(pw):
    pw = str(pw or "")
    if len(pw) < 8:
        return "at least 8 signs"
    if len(pw) > 64 or any(c in pw for c in "\r\n\x00"):
        return "at most 64 signs, no line breaks"
    return ""


def smb_service(on):
    """smbd (and nmbd) on and reload / off -> "" or the english reason"""
    st = dict(CFG.get("tausch_smb_st") or {})
    rc, out = smb_sys(["systemctl", "is-active", "smbd"], root=False, timeout=15)
    running = rc == 0 and out.strip() == "active"
    if on:
        if running:
            return _smb_step(["systemctl", "reload", "smbd"], "systemctl reload smbd", timeout=60)
        e = _smb_step(["systemctl", "enable", "--now", "smbd"], "systemctl enable smbd", timeout=90)
        if not e:
            smb_sys(["systemctl", "enable", "--now", "nmbd"], timeout=90)   # the name \\<pi> for Windows; without it the address works
            st["started"] = True
            CFG["tausch_smb_st"] = st
            save_settings()
        return e
    if not running:
        return ""
    if st.get("started") or st.get("mine"):
        e = _smb_step(["systemctl", "disable", "--now", "smbd"], "systemctl disable smbd", timeout=90)
        smb_sys(["systemctl", "disable", "--now", "nmbd"], timeout=90)
        st.pop("started", None)
        CFG["tausch_smb_st"] = st
        save_settings()
        return e
    return _smb_step(["systemctl", "reload", "smbd"], "systemctl reload smbd", timeout=60)


def smb_cmds(on):
    """the exact commands for a terminal when MoveEye has no rights (sudo wants a password)"""
    mine = os.path.join(DATA_DIR, "samba", "moveeye.conf")
    dst = os.path.join(SMB["etc"], "moveeye.conf")
    inc = f"include = {dst}"
    if not on:
        return [f"sudo install -m 644 '{mine}' {dst}", f"sudo smbpasswd -d {SMB_USER}", "sudo systemctl reload smbd"]
    return ["sudo apt install -y --no-install-recommends samba",
            f"id {SMB_USER} || sudo useradd --system --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin --user-group {SMB_USER}",
            f"sudo install -m 644 '{mine}' {dst}",
            f"grep -qx '{inc}' {SMB['etc']}/smb.conf || echo '{inc}' | sudo tee -a {SMB['etc']}/smb.conf",
            f"sudo smbpasswd -a {SMB_USER}", f"sudo smbpasswd -e {SMB_USER}",
            "sudo systemctl enable --now smbd nmbd", "sudo systemctl reload smbd"]


def smb_apply(why=""):
    """bring Samba to the state of the switch -> "" or the english reason (also in SMB["err"])"""
    with SMB["lock"]:
        on = bool(CFG.get("tausch_smb") and CFG.get("tausch_on", True))
        SMB["cmds"] = []
        text, err = smb_wanted()
        if not err and on and not smb_have():
            err = "Samba is not installed"
        if not err and on:
            root = _tz_load()
            if root is None or not _smb_links_ok(root):
                err = "this storage cannot link files (FAT / exFAT) - use the memory card or a drive with ext4"
        if not err and on and SMB["pw"] and time.time() - SMB["pw"][1] < SMB_PW_KEEP:
            err = smb_pw_store(SMB["pw"][0])
            if not err:
                SMB["pw"] = None
        if not err and on and not (CFG.get("tausch_smb_st") or {}).get("pw"):
            err = "no password set"
        if not err and (on or smb_have() and os.path.exists(os.path.join(SMB["etc"], "moveeye.conf"))):
            if on:
                err = smb_user_ok()
            if not err:
                err = smb_write_conf(text)
            if not err:
                if on:
                    err = _smb_step(["smbpasswd", "-e", SMB_USER], "smbpasswd")
                elif os.path.exists(os.path.join(SMB["etc"], "moveeye.conf")):
                    smb_sys(["smbpasswd", "-d", SMB_USER], timeout=30)
            if not err:
                err = smb_service(on)
        if err == "no rights":
            SMB["cmds"] = smb_cmds(on)
        SMB.update(err=err, active=(0.0, False), conf=text if not err else "")
        if why:
            log_event("sys", f"Digital backpack: network share {'on' if on else 'off'} ({why})" + (f" - not done: {err}" if err else ""))
        if on and not err:
            smb_worker_start()
        return err


def smb_active():
    """is the share really there now? (switch on, our file in /etc, smbd runs) - cached 10 s"""
    t, v = SMB["active"]
    if time.time() - t < 10:
        return v
    v = False
    if CFG.get("tausch_smb") and not SMB["err"] and smb_have():
        try:
            with open(os.path.join(SMB["etc"], "moveeye.conf"), encoding="utf-8") as f:
                mine = f.read()
        except OSError:
            mine = ""
        rc, out = smb_sys(["systemctl", "is-active", "smbd"], root=False, timeout=15)
        v = f"[{SMB_SHARE}]" in mine and rc == 0 and out.strip() == "active"
    SMB["active"] = (time.time(), v)
    return v


def smb_status(lang=None):
    """for the page: never the password, only whether one is set"""
    st = CFG.get("tausch_smb_st") or {}
    on = bool(CFG.get("tausch_smb"))
    lan = smb_lan() if on or SMB["busy"] else []
    ip = lan[0][1].split("/")[0] if lan else (local_ip() or "<IP>")
    host = re.sub(r"[^A-Za-z0-9-]", "", socket.gethostname() or "") or "raspberrypi"
    if SMB["busy"]:
        state, why = "busy", tr(SMB["busy"], lang)
    elif not on:
        state, why = "off", ""
    elif SMB["err"]:
        e = SMB["err"]
        state, why = "err", (tr("MoveEye has no rights for this (sudo asks for a password) - run the commands below once in a terminal.", lang)
                             if e == "no rights" else smb_tr(e, lang))
    elif not CFG.get("tausch_on", True):
        state, why = "err", tr("The digital backpack is switched off.", lang)
    elif smb_active():
        state, why = "on", ""
    else:
        state, why = "err", tr("Samba does not run", lang)
    return {"ok": True, "on": on, "state": state, "why": why, "have": smb_have(), "pw": bool(st.get("pw")),
            "pw_wait": bool(SMB["pw"]), "user": SMB_USER, "share": SMB_SHARE, "win": f"\\\\{host}\\{SMB_SHARE}", "win_ip": f"\\\\{ip}\\{SMB_SHARE}",
            "mac": f"smb://{ip}/{SMB_SHARE}", "mac_name": f"smb://{host}.local/{SMB_SHARE}", "cmds": list(SMB["cmds"]),
            "rej": [{"t": t, "name": n, "why": smb_tr(w, lang)} for t, n, w in SMB["rej"]], "need_install": SMB.get("want") is not None and not smb_have()}


def smb_tr(e, lang=None):
    """«reason: detail» -> translated reason + detail"""
    a, s, b = str(e).partition(": ")
    return tr(a, lang) + (s + b if s else "")


def smb_bg(label, fn):
    """one root job at a time in the background (the page asks again while «busy»)"""
    with SMB["lock"]:
        if SMB["busy"]:
            return False
        SMB["busy"] = label

    def run():
        try:
            fn()
        except Exception as e:                                 # never leave the page «busy» for ever
            SMB["err"] = f"error: {e.__class__.__name__}"
            log_event("sys", f"Digital backpack: network share: {e.__class__.__name__}")
        finally:
            SMB["busy"] = ""
    threading.Thread(target=run, daemon=True, name="rucksack-smb").start()
    return True


def smb_action(d, lang=None):
    """POST /api/tausch/smb: on / off / install / pw / pw_del -> (ok, english error)"""
    a = str(d.get("action") or "")
    pw = d.get("password")
    if SMB["busy"] and a != "cancel":
        return False, "busy - try again"
    if pw is not None and str(pw) != "":
        e = smb_pw_check(pw)
        if e:
            return False, e
    if a == "on":
        if not CFG.get("tausch_on", True):
            return False, "The digital backpack is switched off."
        if not pw and not (CFG.get("tausch_smb_st") or {}).get("pw") and not SMB["pw"]:
            return False, "Set a password first."
        if pw:
            SMB["pw"] = (str(pw), time.time())
        if not smb_have():
            SMB["want"] = True                                     # the page shows the confirmation step
            return True, ""
        CFG["tausch_smb"] = True
        save_settings()
        smb_bg("switching on …", lambda: smb_apply("switched on"))
        return True, ""
    if a == "install":
        if SMB.get("want") is None and not CFG.get("tausch_smb"):
            return False, "Switch it on first."
        SMB["want"] = None

        def job():
            SMB["busy"] = "installing Samba …"
            e = smb_install()
            if e:
                SMB["err"] = e
                if e == "no rights":
                    SMB["cmds"] = smb_cmds(True)
                CFG["tausch_smb"] = True                           # the switch stays on: the status says what is missing
                save_settings()
                log_event("sys", "Digital backpack: Samba not installed: " + e)
                return
            CFG["tausch_smb"] = True
            save_settings()
            SMB["busy"] = "switching on …"
            smb_apply("switched on")
        smb_bg("installing Samba …", job)
        return True, ""
    if a == "cancel":
        SMB.update(want=None, pw=None)
        return True, ""
    if a == "off":
        SMB.update(want=None, pw=None)
        CFG["tausch_smb"] = False
        save_settings()
        smb_bg("switching off …", lambda: smb_apply("switched off"))
        return True, ""
    if a == "pw":
        if not pw:
            return False, "at least 8 signs"
        if not smb_have():
            SMB["pw"] = (str(pw), time.time())
            SMB["want"] = True
            return True, ""
        SMB["pw"] = None

        def job():
            e = smb_pw_store(str(pw))
            SMB["err"] = e if e else ("" if SMB["err"] == "no password set" else SMB["err"])
            if e == "no rights":
                SMB["cmds"] = smb_cmds(True)
            elif not e and CFG.get("tausch_smb"):
                smb_apply("password changed")
        smb_bg("saving the password …", job)
        return True, ""
    if a == "pw_del":
        SMB["pw"] = None

        def job():
            if smb_have():
                e = _smb_step(["smbpasswd", "-x", SMB_USER], "smbpasswd")
                if e and not re.search(r"Failed to find entry|does not exist|Failed to delete", e):
                    SMB["err"] = e
                    return
            CFG["tausch_smb_st"] = {k: v for k, v in (CFG.get("tausch_smb_st") or {}).items() if k != "pw"}
            save_settings()
            log_event("sys", "Digital backpack: password of the network share deleted")
            if CFG.get("tausch_smb"):
                SMB["err"] = "no password set"
        smb_bg("deleting the password …", job)
        return True, ""
    return False, "unknown action"


# ---- the folder <Rucksack>/netz  <->  the Rucksack («Für alle») ----------------------------------------------------------------
SMB_WHO = {"key": "admin", "name": "Netzwerk", "admin": True, "perms": set(TZ_PERMS), "is_admin": True}


def _smb_state_path(root):
    return os.path.join(root, "netz.json")                   # beside the shared folder, not in it


def _smb_reject(path, rel, why):
    try:
        os.remove(path)
    except OSError:
        pass
    SMB["rej"].appendleft((int(time.time()), rel[-80:], why))
    log_event("web", f"Digital backpack: «{rel[-80:]}» from the network not taken: {why}")


def _smb_drop(root, fid):
    """a file deleted over the network: out of the Rucksack (like tausch_delete, without the limits of a person)"""
    m = TZ["files"].pop(fid, None)
    for p in (os.path.join(root, "f", fid + ".bin"), os.path.join(root, "f", fid + ".json"), os.path.join(root, "t", fid + ".jpg"),
              os.path.join(root, "t", fid + "_p.jpg")):
        try:
            os.remove(p)
        except OSError:
            pass
    shutil.rmtree(os.path.join(root, "h", fid), ignore_errors=True)
    TZ["chats"].pop(fid, None)
    if m:
        log_event("web", f"Digital backpack: «{m['name']}» deleted over the network")


def _smb_folder(root, name):
    """a folder name from the network -> the Rucksack folder (made if needed) or None"""
    n, _why = tausch_clean_name(name, folder=True)
    if n is None or n != name:
        return None
    if not any(x["name"] == n for x in TZ["folders"]):
        if len(TZ["folders"]) >= TZ_MAX_FOLDERS:
            return None
        TZ["folders"].append({"name": n, "by": "admin", "by_name": SMB_WHO["name"], "t": int(time.time())})
        TZ["folders"].sort(key=lambda x: x["name"].lower())
        _tz_folders_save(root)
        log_event("web", f"Digital backpack: folder «{n}» made over the network")
    return n


def _smb_import(root, nd, rel, st, S):
    """a new, resting file from the network -> into the Rucksack (the rules of an upload) or deleted with a reason"""
    path = os.path.join(nd, rel)
    folder, base = rel.split("/", 1) if "/" in rel else ("", rel)
    name, why = tausch_clean_name(base)
    if name is None:
        return _smb_reject(path, rel, why)
    if tausch_ext(name) == "chat":
        return _smb_reject(path, rel, "Chats are made with «New chat».")
    if tausch_blocked(name):
        return _smb_reject(path, rel, "Programs and scripts are not accepted")
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError:
        return
    if tausch_magic_exec(head):
        return _smb_reject(path, rel, "This file is a program or script - not accepted.")
    lim = tausch_limits()
    used, res = tausch_usage()
    if st.st_size > lim["file"]:
        return _smb_reject(path, rel, "too big for one file: " + tausch_fmt(lim["file"], "en"))
    if len(TZ["files"]) >= TZ_MAX_FILES:
        return _smb_reject(path, rel, "Too many files - delete old ones first.")
    if used + res + st.st_size > lim["total"]:
        return _smb_reject(path, rel, "The digital backpack is full")
    if tausch_disk_free(root) < lim["min_free"]:
        return _smb_reject(path, rel, "Not enough free space on the storage")
    if folder and folder not in {x["name"] for x in TZ["folders"]}:
        return
    name = _tz_unique(name, "all", folder, "admin")
    rel2 = (folder + "/" if folder else "") + name
    if rel2 != rel:
        if os.path.exists(os.path.join(nd, rel2)):
            return
        try:
            os.rename(path, os.path.join(nd, rel2))
        except OSError:
            return
        path = os.path.join(nd, rel2)
    fid = secrets.token_hex(8)
    while fid in TZ["files"]:
        fid = secrets.token_hex(8)
    mime, kind, risky = tausch_type(name)
    m = {"id": fid, "name": name, "area": "all", "folder": folder, "owner": "admin", "owner_name": SMB_WHO["name"], "size": st.st_size,
         "t": int(time.time()), "kind": kind, "thumb": None if kind in ("image", "video", "pdf") and not risky else False}
    try:
        os.link(path, os.path.join(root, "f", fid + ".bin"))
        _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
    except OSError as e:
        SMB["err"] = f"The storage cannot be written to.: {e.__class__.__name__}"
        return
    TZ["files"][fid] = m
    S["files"][rel2] = [fid, st.st_ino]
    log_event("web", f"Digital backpack: «{name}» came over the network ({tausch_fmt(st.st_size, 'de')}, Für alle" + (f" / {folder})" if folder else ")"))
    if m["thumb"] is None:
        tausch_thumb_queue(fid)
    return fid


def smb_sync(now=None):
    """one pass of the comparison (see the top of this part) -> number of changes"""
    if not (CFG.get("tausch_smb") and CFG.get("tausch_on", True)) or not SMB["sync"].acquire(timeout=5):
        return 0
    try:
        root = _tz_load()
        if root is None:
            return 0
        now = time.time() if now is None else now
        nd = os.path.join(root, SMB_DIR)
        with TZ["lock"]:
            if SMB["root"] != root or SMB["S"] is None:
                try:
                    with open(_smb_state_path(root), encoding="utf-8") as f:
                        S = json.load(f)
                    assert isinstance(S.get("files"), dict) and isinstance(S.get("dirs"), list)
                except (OSError, ValueError, AssertionError, AttributeError):
                    S = {"files": {}, "dirs": []}
                SMB.update(root=root, S=S, pend={})
            S = SMB["S"]
            if not os.path.isdir(nd):                            # the folder is gone (new storage, removed by hand): never delete
                os.makedirs(nd, exist_ok=True)                   # anything because of that - start again
                S = SMB["S"] = {"files": {}, "dirs": []}
            n = _smb_pass(root, nd, S, now)
            if n:
                SMB["S"] = S
                _tz_write_json(_smb_state_path(root), S)
            SMB["t_sync"] = now
            return n
    finally:
        SMB["sync"].release()


def _smb_scan(nd, now):
    """{rel: stat} of the files (one folder level), set of folders; deeper folders and links go away when they rest"""
    seen, dirs = {}, set()
    for e in os.scandir(nd):
        if e.name.startswith("."):
            continue
        try:
            if e.is_symlink():
                continue
            if e.is_dir():
                dirs.add(e.name)
                for x in os.scandir(e.path):
                    if x.name.startswith(".") or x.is_symlink():
                        continue
                    if x.is_dir():
                        if now - x.stat().st_mtime > 60:
                            shutil.rmtree(x.path, ignore_errors=True)
                            SMB["rej"].appendleft((int(now), f"{e.name}/{x.name}/", "only one folder level"))
                    elif x.is_file():
                        seen[f"{e.name}/{x.name}"] = x.stat()
            elif e.is_file():
                seen[e.name] = e.stat()
        except OSError:
            continue
    return seen, dirs


def _smb_pass(root, nd, S, now):
    seen, dirs = _smb_scan(nd, now)
    files = TZ["files"]
    bino = {}
    for fid, m in files.items():
        if m["area"] == "all" and m.get("kind") != "chat":
            try:
                bino[fid] = os.stat(os.path.join(root, "f", fid + ".bin")).st_ino
            except OSError:
                pass
    by_ino = {v: k for k, v in bino.items()}
    inos = {st.st_ino for st in seen.values()}
    n = 0
    # 1. the links of the last pass
    for rel, (fid, ino) in list(S["files"].items()):
        st = seen.get(rel)
        p = os.path.join(nd, rel)
        if st is not None and st.st_ino == ino:
            if fid in bino and bino[fid] == ino:
                continue
            try:                                               # deleted / replaced in the browser (a saved text is a new file)
                os.remove(p)
                if fid in bino:
                    os.link(os.path.join(root, "f", fid + ".bin"), p)
                    S["files"][rel] = [fid, bino[fid]]
                    seen[rel] = os.stat(p)
                else:
                    S["files"].pop(rel)
                    seen.pop(rel)
            except OSError:
                pass
            n += 1
            continue
        S["files"].pop(rel)
        n += 1
        if fid in bino and bino[fid] == ino and ino not in inos:  # gone over the network (not moved: the data is nowhere else)
            _smb_drop(root, fid)
            bino.pop(fid, None)
            by_ino.pop(ino, None)
    # 2. folders
    have = {x["name"] for x in TZ["folders"]}
    for name in sorted(dirs - have):
        if name in S["dirs"]:                                  # deleted in the browser
            try:
                os.rmdir(os.path.join(nd, name))
                dirs.discard(name)
                n += 1
                continue
            except OSError:
                pass
        if _smb_folder(root, name):
            n += 1
    for name in sorted(have - dirs):
        inside = [m for m in files.values() if m["area"] == "all" and m.get("folder") == name]
        if name in S["dirs"] and not inside:                   # deleted over the network
            TZ["folders"] = [x for x in TZ["folders"] if x["name"] != name]
            _tz_folders_save(root)
            log_event("web", f"Digital backpack: folder «{name}» deleted over the network")
        else:
            os.makedirs(os.path.join(nd, name), exist_ok=True)
            dirs.add(name)
        n += 1
    # 3. what is in the folder
    linked = set()
    for rel, st in sorted(seen.items()):
        fid = by_ino.get(st.st_ino)
        if fid:
            linked.add(fid)
            m = files[fid]
            folder, base = rel.split("/", 1) if "/" in rel else ("", rel)
            if S["files"].get(rel, [None])[0] != fid:          # renamed / moved over the network
                nm, _w = tausch_clean_name(base)
                if nm and (not folder or folder in {x["name"] for x in TZ["folders"]}):
                    nm = nm if (nm, folder) == (m["name"], m.get("folder", "")) else _tz_unique(nm, "all", folder, m["owner"])
                    if nm != base and not os.path.exists(os.path.join(nd, folder, nm)):
                        try:
                            os.rename(os.path.join(nd, rel), os.path.join(nd, folder, nm))   # a clean name: taken in the next pass
                        except OSError:
                            pass
                    elif nm == base:
                        m.update(name=nm, folder=folder)
                        _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
                        S["files"] = {k: v for k, v in S["files"].items() if v[0] != fid}
                        S["files"][rel] = [fid, st.st_ino]
                        n += 1
            if st.st_size != m["size"]:                        # changed right in the folder
                try:
                    with open(os.path.join(nd, rel), "rb") as f:
                        bad = tausch_magic_exec(f.read(16))
                except OSError:
                    bad = False
                if bad:
                    _smb_reject(os.path.join(nd, rel), rel, "This file is a program or script - not accepted.")
                    _smb_drop(root, fid)
                    S["files"].pop(rel, None)
                else:
                    m.update(size=st.st_size, t=int(now), ver=int(m.get("ver") or 1) + 1, ed_name=SMB_WHO["name"], ed_t=int(now))
                    if m.get("thumb") is not False:
                        m["thumb"] = None
                        tausch_thumb_queue(fid)
                    _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
                n += 1
            continue
        sig = (st.st_size, st.st_mtime_ns, st.st_ino)
        if SMB["pend"].get(rel) != sig or now - st.st_mtime < SMB_QUIET:
            SMB["pend"][rel] = sig                             # still being written: next pass
            continue
        SMB["pend"].pop(rel, None)
        fid = _smb_import(root, nd, rel, st, S)
        if fid:
            linked.add(fid)
        n += 1
    for k in [k for k in SMB["pend"] if k not in seen]:
        SMB["pend"].pop(k, None)
    # 4. new in the Rucksack (browser) -> into the folder
    taken = {r.lower() for r in seen}
    for fid in bino:
        if fid in linked or fid not in files:
            continue
        m = files[fid]
        folder = m.get("folder", "")
        rel = (folder + "/" if folder else "") + m["name"]
        if rel.lower() in taken or folder and folder not in dirs:
            continue
        try:
            os.link(os.path.join(root, "f", fid + ".bin"), os.path.join(nd, rel))
            S["files"][rel] = [fid, bino[fid]]
            taken.add(rel.lower())
            n += 1
        except OSError:
            pass
    S["dirs"] = sorted(dirs)
    return n


def smb_worker_start():
    with SMB["lock"]:
        if SMB["run"]:
            return
        SMB["run"] = True
    threading.Thread(target=_smb_worker, daemon=True, name="rucksack-smb-sync").start()


def _smb_worker():
    """every 10 s the comparison; every minute: the home network changed (new address, hotspot) -> the file again"""
    last = None
    try:
        while CFG.get("tausch_smb"):
            time.sleep(10)
            if SMB["busy"]:
                continue
            if not CFG.get("tausch_on", True):
                if SMB["conf"] and SMB["conf"] != SMB_CONF_OFF:
                    smb_apply("the digital backpack was switched off")
                continue
            try:
                if time.time() - SMB["t_lan"] > 60:
                    lan = smb_lan()
                    if last is not None and lan != last or SMB["conf"] and smb_wanted()[0] not in ("", SMB["conf"]):
                        smb_apply("network changed")
                    last = lan
                if not SMB["err"]:
                    smb_sync()
            except Exception as e:
                log_event("sys", f"Digital backpack: network comparison: {e.__class__.__name__}: {e}"[:160])
                time.sleep(30)
    finally:
        SMB["run"] = False


_smb_tausch_list_before = tausch_list


def tausch_list(who, area="all", folder="", lang=None):   # + 639zzzn: open page = compare first (no waiting for the next pass)
    if CFG.get("tausch_smb") and not SMB["err"] and time.time() - SMB["t_sync"] > 2:
        try:
            smb_sync()
        except Exception as e:
            log_event("sys", f"Digital backpack: network comparison: {e.__class__.__name__}"[:160])
    return _smb_tausch_list_before(who, area, folder, lang)


# ---- web: GET/POST /api/tausch/smb (only the administrator) -----------------------------------------------------------------------
_smalltv_routes_639zzzn = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzzn
    _smalltv_routes_639zzzn(app, reply, body)
    from flask import request, g

    @app.route("/api/tausch/smb", methods=["GET", "POST"])
    def api_tausch_smb():
        d = body() if request.method == "POST" else {}
        L = norm_lang(request.args.get("lang") or d.get("lang") or CFG.get("lang"))
        if getattr(g, "role", "admin") != "admin" or getattr(g, "appkey", None):
            return reply({"ok": False, "error": tr("only the administrator", L)}, 403)
        if request.method == "POST":
            if d.get("password") and seclogin_plain(request):
                url = seclogin_url(request).split("/api/")[0] + "/"
                return reply({"ok": False, "error": tr("For your safety a password can only be set over the secure page", L) + ": " + url,
                              "https": url}, 403)
            ok, err = smb_action(d, L)
            if not ok:
                return reply(dict(smb_status(L), ok=False, error=tr(err, L)), 400)
        return reply(smb_status(L))

    if CFG.get("tausch_smb"):                              # after a start: the network may be another one, then the comparison
        smb_bg("switching on …", lambda: smb_apply("start"))


# ---- the settings card (530 Settings → Digital backpack) ---------------------------------------------------------------------------
SMB_PANEL_JS = r"""
<script>
(function () {
  try { const D = /*SMBDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const T = x => (typeof t === "function" ? t(x) : x);
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  const copy = txt => { try { navigator.clipboard.writeText(txt).then(() => { if (typeof toast === "function") toast("✓ " + T("Copied")); }, () => prompt(T("Copy"), txt)); } catch (e) { prompt(T("Copy"), txt); } };
  window.smbPanel = function (d) {
    const bx = E("div", "auxbox smb-card"); bx.id = "smb-card"; bx.hidden = true; d.appendChild(bx);
    let timer = null, msg = "";
    const load = async () => { let r = null; try { r = await fetch("/api/tausch/smb?lang=" + L(), {cache: "no-store"}); } catch (e) { return; }
      if (r.status === 403) { bx.hidden = true; return; } let j = null; try { j = await r.json(); } catch (e) { return; } paint(j); };
    const act = async (a, x) => { const j = await post("/api/tausch/smb", Object.assign({action: a, lang: L()}, x || {})); msg = j.ok ? "" : (j.error || "error");
      if (j.state) paint(j); else load(); return j; };
    function line(label, val) { const r = E("div", "row smb-l"); r.style.cssText = "gap:8px;align-items:center;margin-top:6px";
      const a = E("span", "mut", label); a.style.minWidth = "92px"; const c = E("code", "", val); c.style.cssText = "flex:1;word-break:break-all;font-size:13px";
      const b = E("button", "sec", "⧉"); b.type = "button"; b.title = T("Copy"); b.style.cssText = "padding:4px 10px"; b.onclick = () => copy(val);
      r.append(a, c, b); return r; }
    function paint(j) {
      bx.hidden = false; bx.textContent = ""; clearTimeout(timer);
      const h = E("div", "", "🖧 " + T("Network share")); h.style.cssText = "font-weight:700;margin:12px 0 4px"; bx.appendChild(h);
      const row = E("label", "row tg"), cb = E("input"); cb.type = "checkbox"; cb.className = "sw"; cb.id = "smb-on"; cb.checked = !!j.on || !!j.need_install;
      cb.disabled = j.state === "busy"; row.append(E("span", "", T("Share in the network (Windows/Mac/iPhone)")), cb); bx.appendChild(row);
      const pin = E("input"); pin.type = "password"; pin.autocomplete = "new-password"; pin.placeholder = T("Password for the network (at least 8 signs)");
      pin.style.cssText = "width:100%;margin-top:6px;box-sizing:border-box"; pin.id = "smb-pw";
      cb.onchange = () => { if (!cb.checked) { act("off"); return; }
        if (!j.pw && !j.pw_wait && pin.value.length < 8) { cb.checked = false; msg = T("Set a password first."); paint(j); setTimeout(() => { const p = document.getElementById("smb-pw"); if (p) p.focus(); }, 50); return; }
        act("on", pin.value ? {password: pin.value} : {}); };
      const S = {on: ["", "● " + T("active")], off: ["mut", "○ " + T("off")], err: ["err", "⚠ " + T("Error")], busy: ["mut", "⏳ " + T("working …")]}[j.state] || ["mut", j.state];
      const st = E("div", S[0], S[1] + (j.why ? " – " + j.why : "")); st.id = "smb-state"; st.style.marginTop = "4px"; if (j.state === "on") st.style.color = "#3fb950"; bx.appendChild(st);
      if (msg) { const m = E("div", "err", "⚠ " + msg); m.style.marginTop = "4px"; bx.appendChild(m); }
      if (j.need_install) {
        const c = E("div", "sens-card"); c.id = "smb-confirm"; c.style.marginTop = "8px";
        c.append(E("div", "", T("Samba is installed once (about 10 MB). Continue?")));
        const r = E("div", "row"); r.style.cssText = "gap:8px;margin-top:8px"; const ok = E("button", "", T("Continue")), no = E("button", "sec", T("Cancel"));
        ok.type = no.type = "button"; ok.id = "smb-go"; ok.onclick = () => act("install"); no.onclick = () => act("cancel"); r.append(ok, no); c.append(r); bx.appendChild(c);
      }
      bx.appendChild(line(T("User name"), j.user));
      const pr = E("div", ""); pr.style.marginTop = "8px";
      if (j.pw) {
        pr.append(E("div", "mut", "🔑 " + T("Password") + ": " + T("set") + " " + T("(never shown again)")));
        const r = E("div", "row"); r.style.cssText = "gap:8px;margin-top:6px"; const ch = E("button", "sec", T("Change password")), dl = E("button", "red", T("Delete password"));
        ch.type = dl.type = "button";
        ch.onclick = () => { r.replaceWith(pin, sv); pin.focus(); };
        dl.onclick = () => { if (confirm(T("Delete the password? Nobody can connect over the network until a new one is set."))) act("pw_del"); };
        r.append(ch, dl); pr.appendChild(r);
      } else { pr.append(E("div", "mut", "🔑 " + T("Password") + ": " + (j.pw_wait ? T("waiting for Samba") : T("not set"))), pin); }
      const sv = E("button", "", T("Set password")); sv.type = "button"; sv.style.marginTop = "6px";
      sv.onclick = async () => { if (pin.value.length < 8) { msg = T("at least 8 signs"); paint(j); return; } const v = pin.value; pin.value = ""; await act("pw", {password: v}); };
      if (!j.pw) pr.appendChild(sv); bx.appendChild(pr);
      const how = E("div", ""); how.style.cssText = "margin-top:10px" + (j.state === "on" ? "" : ";opacity:.6");
      how.append(E("div", "", T("How to connect") + ":"), line("Windows", j.win), line("Mac / iPhone", j.mac), E("div", "mut", T("If the name is not found:") + " " + j.win_ip + " · " + j.mac_name));
      how.lastChild.style.cssText = "font-size:12px;margin-top:4px;word-break:break-all"; bx.appendChild(how);
      if ((j.cmds || []).length) { const c = E("div", "sens-card"); c.style.marginTop = "8px"; c.append(E("div", "", T("Once in a terminal on the Pi:")));
        const pre = E("pre", "", j.cmds.join("\n")); pre.style.cssText = "white-space:pre-wrap;word-break:break-all;font-size:12px;margin:6px 0"; const b = E("button", "sec", "⧉ " + T("Copy")); b.type = "button";
        b.onclick = () => copy(j.cmds.join("\n")); c.append(pre, b); bx.appendChild(c); }
      if ((j.rej || []).length) { const c = E("div", "mut", T("Not taken from the network:")); c.style.marginTop = "8px"; bx.appendChild(c);
        j.rej.forEach(x => { const r = E("div", "mut", "· " + x.name + " – " + x.why); r.style.fontSize = "12px"; bx.appendChild(r); }); }
      const nt = E("div", "mut", T("smb-note")); nt.style.cssText = "font-size:12px;margin-top:8px"; bx.appendChild(nt);
      if (j.state === "busy") timer = setTimeout(load, 1500);
    }
    load(); d.addEventListener("toggle", () => { if (d.open) load(); });
  };
})();
</script>
"""
_smb_hook = 'if (sec.id === "Developer") devExtras(d);'
if _smb_hook in WEB_PAGE and "smbPanel" not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_smb_hook, _smb_hook + '\n    if (sec.id === ' + json.dumps(_TZS) + ' && window.smbPanel) smbPanel(d);', 1)
    WEB_PAGE = WEB_PAGE.replace("</body>", SMB_PANEL_JS + "</body>", 1)

# english key: (de, fr, it, rm)
_HX_SMB = {
    "Network share": ("Netzwerk-Freigabe", "Partage réseau", "Condivisione in rete", "Partiziun en la rait"),
    "Share in the network (Windows/Mac/iPhone)": ("Im Netzwerk freigeben (Windows/Mac/iPhone)", "Partager sur le réseau (Windows/Mac/iPhone)",
                                                  "Condividi in rete (Windows/Mac/iPhone)", "Parter en la rait (Windows/Mac/iPhone)"),
    "Password for the network (at least 8 signs)": ("Passwort fürs Netzwerk (mindestens 8 Zeichen)", "Mot de passe pour le réseau (au moins 8 caractères)",
                                                    "Password per la rete (almeno 8 caratteri)", "Pled-clav per la rait (almain 8 caracters)"),
    "Set a password first.": ("Zuerst ein Passwort setzen.", "Définis d’abord un mot de passe.", "Imposta prima una password.", "Fixescha l’emprim in pled-clav."),
    "active": ("aktiv", "actif", "attivo", "activ"),
    "Error": ("Fehler", "Erreur", "Errore", "Errur"),
    "working …": ("arbeitet …", "en cours …", "in corso …", "lavura …"),
    "Samba is installed once (about 10 MB). Continue?": ("Samba wird einmal installiert (ca. 10 MB). Weiter?", "Samba sera installé une fois (env. 10 Mo). Continuer ?",
                                                         "Samba viene installato una volta (circa 10 MB). Continuare?", "Samba vegn installà ina giada (ca. 10 MB). Vinavant?"),
    "Continue": ("Weiter", "Continuer", "Continua", "Vinavant"),
    "User name": ("Benutzername", "Nom d’utilisateur", "Nome utente", "Num d’utilisader"),
    "Password": ("Passwort", "Mot de passe", "Password", "Pled-clav"),
    "(never shown again)": ("(wird nie mehr angezeigt)", "(n’est plus jamais affiché)", "(non viene più mostrata)", "(na vegn mai pli mussà)"),
    "Change password": ("Passwort ändern", "Changer le mot de passe", "Cambia password", "Midar il pled-clav"),
    "Delete password": ("Passwort löschen", "Supprimer le mot de passe", "Elimina password", "Stizzar il pled-clav"),
    "Delete the password? Nobody can connect over the network until a new one is set.": (
        "Passwort löschen? Bis ein neues gesetzt ist, kann sich niemand übers Netzwerk verbinden.",
        "Supprimer le mot de passe ? Personne ne pourra se connecter par le réseau tant qu’un nouveau n’est pas défini.",
        "Eliminare la password? Nessuno potrà collegarsi dalla rete finché non ne viene impostata una nuova.",
        "Stizzar il pled-clav? Nagin na po sa colliar sur la rait fin ch’in nov è fixà."),
    "waiting for Samba": ("wartet auf Samba", "attend Samba", "in attesa di Samba", "spetga sin Samba"),
    "not set": ("nicht gesetzt", "non défini", "non impostata", "betg fixà"),
    "Set password": ("Passwort setzen", "Définir le mot de passe", "Imposta password", "Fixar il pled-clav"),
    "How to connect": ("So verbindest du dich", "Comment se connecter", "Come collegarsi", "Uschia ta colliasch ti"),
    "If the name is not found:": ("Wird der Name nicht gefunden:", "Si le nom n’est pas trouvé :", "Se il nome non viene trovato:", "Sch’il num na vegn betg chattà:"),
    "Once in a terminal on the Pi:": ("Einmal im Terminal auf dem Pi:", "Une fois dans un terminal sur le Pi :", "Una volta in un terminale sul Pi:",
                                      "Ina giada en in terminal sin il Pi:"),
    "Not taken from the network:": ("Aus dem Netzwerk nicht übernommen:", "Non repris du réseau :", "Non ripreso dalla rete:", "Betg surpiglià da la rait:"),
    "smb-note": ("Was über das Netzwerk kommt, übernimmt MoveEye nach ein paar Sekunden in «Für alle» (Ordner: eine Ebene). Programme, zu grosse Dateien "
                 "oder ein voller Rucksack: die Datei wird danach wieder gelöscht – Samba kann Grösse und Inhalt nicht schon beim Schreiben prüfen. "
                 "«Meine Dateien» und Chats sind nicht im Netzwerk.",
                 "Ce qui arrive par le réseau est repris par MoveEye après quelques secondes dans «Pour tous» (dossiers : un niveau). Programmes, fichiers "
                 "trop grands ou sac plein : le fichier est ensuite supprimé – Samba ne peut pas vérifier taille et contenu pendant l’écriture. "
                 "«Mes fichiers» et les chats ne sont pas sur le réseau.",
                 "Ciò che arriva dalla rete viene ripreso da MoveEye dopo qualche secondo in «Per tutti» (cartelle: un livello). Programmi, file troppo "
                 "grandi o zaino pieno: il file viene poi eliminato – Samba non può controllare dimensione e contenuto durante la scrittura. "
                 "«I miei file» e le chat non sono in rete.",
                 "Quai che vegn sur la rait surpiglia MoveEye suenter in pèr secundas en «Per tuts» (ordinaturs: in nivel). Programs, datotecas memia "
                 "grondas u in satgados plain: la datoteca vegn suenter stizzada – Samba na po betg controllar grondezza e cuntegn durant scriver. "
                 "«Mias datotecas» e chats n’èn betg en la rait."),
    "only the administrator": ("nur der Admin", "seulement l’administrateur", "solo l’amministratore", "mo l’administratur"),
    "MoveEye has no rights for this (sudo asks for a password) - run the commands below once in a terminal.": (
        "MoveEye hat dafür keine Rechte (sudo will ein Passwort) – die Befehle unten einmal im Terminal ausführen.",
        "MoveEye n’a pas les droits pour cela (sudo demande un mot de passe) – exécute une fois les commandes ci-dessous dans un terminal.",
        "MoveEye non ha i diritti per questo (sudo chiede una password) – esegui una volta i comandi qui sotto in un terminale.",
        "MoveEye n’ha betg ils dretgs per quai (sudo dumonda in pled-clav) – exequescha ina giada ils cumonds sutvart en in terminal."),
    "Samba does not run": ("Samba läuft nicht", "Samba ne tourne pas", "Samba non è in esecuzione", "Samba na funcziuna betg"),
    "Samba is not installed": ("Samba ist nicht installiert", "Samba n’est pas installé", "Samba non è installato", "Samba n’è betg installà"),
    "no password set": ("kein Passwort gesetzt", "aucun mot de passe défini", "nessuna password impostata", "nagin pled-clav fixà"),
    "no home network found (Wi-Fi / LAN)": ("kein Heimnetz gefunden (WLAN / LAN)", "aucun réseau domestique trouvé (Wi-Fi / LAN)",
                                            "nessuna rete di casa trovata (Wi-Fi / LAN)", "nagina rait da chasa chattada (WLAN / LAN)"),
    "the storage (USB stick / SSD) is not there": ("der Speicher (USB-Stick / SSD) fehlt", "le stockage (clé USB / SSD) est absent",
                                                   "la memoria (chiavetta USB / SSD) manca", "la memoria (stick USB / SSD) manca"),
    "the memory card is write-protected": ("die Speicherkarte ist schreibgeschützt", "la carte mémoire est protégée en écriture",
                                           "la scheda di memoria è protetta da scrittura", "la carta da memoria è protegida cunter scriver"),
    "the folder of the backpack belongs to root - start MoveEye as a normal user": (
        "der Ordner des Rucksacks gehört root – MoveEye als normaler Benutzer starten", "le dossier du sac appartient à root – démarre MoveEye comme utilisateur normal",
        "la cartella dello zaino appartiene a root – avvia MoveEye come utente normale", "l’ordinatur dal satgados tutga a root – avra MoveEye sco utilisader normal"),
    "the path of the backpack has unusual signs": ("der Pfad des Rucksacks hat ungewöhnliche Zeichen", "le chemin du sac contient des caractères inhabituels",
                                                   "il percorso dello zaino ha caratteri insoliti", "la via dal satgados ha caracters nunusitads"),
    "this storage cannot link files (FAT / exFAT) - use the memory card or a drive with ext4": (
        "dieser Speicher kann keine Verknüpfungen (FAT / exFAT) – Speicherkarte oder ein Laufwerk mit ext4 nehmen",
        "ce stockage ne sait pas lier des fichiers (FAT / exFAT) – utilise la carte mémoire ou un disque en ext4",
        "questa memoria non può collegare file (FAT / exFAT) – usa la scheda di memoria o un disco con ext4",
        "questa memoria na po betg colliar datotecas (FAT / exFAT) – piglia la carta da memoria u in disc cun ext4"),
    "a user «rucksack» exists already and is not the one of MoveEye": ("einen Benutzer «rucksack» gibt es schon, er ist nicht der von MoveEye",
        "un utilisateur «rucksack» existe déjà et n’est pas celui de MoveEye", "esiste già un utente «rucksack» che non è quello di MoveEye",
        "in utilisader «rucksack» exista gia e n’è betg quel da MoveEye"),
    "Samba refused the settings": ("Samba lehnt die Einstellungen ab", "Samba refuse les réglages", "Samba rifiuta le impostazioni", "Samba refusa las configuraziuns"),
    "no apt-get on this system": ("kein apt-get auf diesem System", "pas d’apt-get sur ce système", "nessun apt-get su questo sistema", "nagin apt-get sin quest sistem"),
    "apt took too long - try again later": ("apt brauchte zu lange – später nochmals versuchen", "apt a pris trop de temps – réessaie plus tard",
                                            "apt ha impiegato troppo – riprova più tardi", "apt ha duvrà memia ditg – emprova pli tard anc ina giada"),
    "apt is busy right now (another installation or update) - try again in a few minutes": (
        "apt ist gerade beschäftigt (andere Installation oder Update) – in ein paar Minuten nochmals versuchen",
        "apt est occupé (autre installation ou mise à jour) – réessaie dans quelques minutes",
        "apt è occupato (altra installazione o aggiornamento) – riprova tra qualche minuto",
        "apt è occupà (autra installaziun u actualisaziun) – emprova en in pèr minutas anc ina giada"),
    "no internet for apt - try again with internet": ("kein Internet für apt – mit Internet nochmals versuchen", "pas d’internet pour apt – réessaie avec internet",
                                                      "niente internet per apt – riprova con internet", "nagin internet per apt – emprova cun internet anc ina giada"),
    "installing Samba …": ("installiere Samba …", "installation de Samba …", "installazione di Samba …", "installescha Samba …"),
    "switching on …": ("schalte ein …", "activation …", "attivazione …", "activescha …"),
    "switching off …": ("schalte aus …", "désactivation …", "disattivazione …", "deactivescha …"),
    "saving the password …": ("speichere das Passwort …", "enregistrement du mot de passe …", "salvataggio della password …", "memorisescha il pled-clav …"),
    "deleting the password …": ("lösche das Passwort …", "suppression du mot de passe …", "eliminazione della password …", "stizza il pled-clav …"),
    "at least 8 signs": ("mindestens 8 Zeichen", "au moins 8 caractères", "almeno 8 caratteri", "almain 8 caracters"),
    "at most 64 signs, no line breaks": ("höchstens 64 Zeichen, keine Zeilenumbrüche", "au plus 64 caractères, sans retour à la ligne",
                                         "al massimo 64 caratteri, senza a capo", "maximalmain 64 caracters, nagins sigls da lingia"),
    "Switch it on first.": ("Zuerst einschalten.", "Active-le d’abord.", "Prima attivalo.", "L’emprim activar."),
    "Programs and scripts are not accepted": ("Programme und Skripte werden nicht angenommen", "Les programmes et scripts ne sont pas acceptés",
                                              "Programmi e script non sono accettati", "Programs e scripts na vegnan betg acceptads"),
    "Too many files - delete old ones first.": ("Zu viele Dateien – zuerst alte löschen.", "Trop de fichiers – supprime d’abord les anciens.",
                                                "Troppi file – elimina prima quelli vecchi.", "Memia bleras datotecas – l’emprim stizzar las veglias."),
    "The digital backpack is full": ("Der Digitale Rucksack ist voll", "Le sac à dos numérique est plein", "Lo zaino digitale è pieno", "Il satgados digital è plain"),
    "Not enough free space on the storage": ("Zu wenig freier Platz auf dem Speicher", "Pas assez d’espace libre sur le stockage",
                                             "Spazio libero insufficiente sulla memoria", "Memia pauc plaz liber sin la memoria"),
    "The digital backpack is switched off.": ("Der Digitale Rucksack ist ausgeschaltet.", "Le sac à dos numérique est désactivé.",
                                              "Lo zaino digitale è disattivato.", "Il satgados digital è deactivà."),
    "too big for one file": ("zu gross für eine Datei", "trop grand pour un fichier", "troppo grande per un file", "memia grond per ina datoteca"),
    "only one folder level": ("nur eine Ordner-Ebene", "un seul niveau de dossiers", "un solo livello di cartelle", "mo in nivel d’ordinaturs"),
    "Network share: set up in the browser": ("Netzwerk-Freigabe: im Browser einrichten", "Partage réseau : à configurer dans le navigateur",
                                             "Condivisione in rete: da impostare nel browser", "Partiziun en la rait: endrizzar en il navigatur"),
}
for _k, _v in _HX_SMB.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
WEB_PAGE = WEB_PAGE.replace("/*SMBDE*/{}", json.dumps({_k: DE.get(_k, _v[0]) for _k, _v in _HX_SMB.items()}, ensure_ascii=False), 1)

# ---- the manual: one point in the section «Digitaler Rucksack» (639zzc) ----------------------------------------------------------
SMB_HELP_HTML = r"""
de|<li><b>🖧 Im Netzwerk</b> (nur der Admin, ab Werk aus): Einstellungen → Digitaler Rucksack → «Im Netzwerk freigeben». Windows: <code>\\&lt;Pi-Name&gt;\rucksack</code>, Mac / iPhone (Dateien → Mit Server verbinden): <code>smb://&lt;Pi-Adresse&gt;/rucksack</code>, Benutzer <code>rucksack</code> mit eigenem Passwort. Nur «Für alle», nur im Heimnetz; Programme, zu grosse Dateien und ein voller Rucksack werden nach dem Schreiben wieder gelöscht.</li>
en|<li><b>🖧 In the network</b> (administrator only, off by default): Settings → Digital backpack → «Share in the network». Windows: <code>\\&lt;pi-name&gt;\rucksack</code>, Mac / iPhone (Files → Connect to server): <code>smb://&lt;pi-address&gt;/rucksack</code>, user <code>rucksack</code> with its own password. Only «For everyone», only in the home network; programs, too big files and a full backpack are deleted again after writing.</li>
fr|<li><b>🖧 Sur le réseau</b> (administrateur seulement, désactivé par défaut) : Réglages → Sac à dos numérique → «Partager sur le réseau». Windows : <code>\\&lt;nom-du-pi&gt;\rucksack</code>, Mac / iPhone : <code>smb://&lt;adresse-du-pi&gt;/rucksack</code>, utilisateur <code>rucksack</code> avec son propre mot de passe. Seulement «Pour tous», seulement dans le réseau domestique.</li>
it|<li><b>🖧 In rete</b> (solo l’amministratore, disattivato di fabbrica): Impostazioni → Zaino digitale → «Condividi in rete». Windows: <code>\\&lt;nome-pi&gt;\rucksack</code>, Mac / iPhone: <code>smb://&lt;indirizzo-pi&gt;/rucksack</code>, utente <code>rucksack</code> con la sua password. Solo «Per tutti», solo nella rete di casa.</li>
rm|<li><b>🖧 En la rait</b> (mo l’administratur, deactivà da fabrica): Configuraziuns → Satgados digital → «Parter en la rait». Windows: <code>\\&lt;num-dal-pi&gt;\rucksack</code>, Mac / iPhone: <code>smb://&lt;adressa-dal-pi&gt;/rucksack</code>, utilisader <code>rucksack</code> cun agen pled-clav. Mo «Per tuts», mo en la rait da chasa.</li>
"""
_HELP_SMB = dict(x.split("|", 1) for x in SMB_HELP_HTML.strip().split("\n") if "|" in x)


def _help_smb(doc, lang):
    i = doc.find('<section id="tausch"')
    j = doc.find("</ul></section>", i)
    return doc if i < 0 or j < 0 or "🖧" in doc[i:j] or lang not in _HELP_SMB else doc[:j] + _HELP_SMB[lang] + doc[j:]


_hp_en_smb = HELP_PAGE.find('<div lang="en">')
if _hp_en_smb > 0:
    HELP_PAGE = _help_smb(HELP_PAGE[:_hp_en_smb], "de") + _help_smb(HELP_PAGE[_hp_en_smb:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_smb(HELP_X[_L], _L)

# ---- window: a line with the state and a button to the page (the setup itself is in the browser) -------------------------------
if GUI_OK:
    _smb_tk_build_section_before = App._build_section

    def _smb_tk_build_section(self, sec, sbody, settings_parent=None):
        _smb_tk_build_section_before(self, sec, sbody, settings_parent)
        if sec != "File exchange" or CFG.get("lock_on"):
            return
        try:
            s = smb_status()
            ttk.Label(sbody, text="🖧 " + tr("Network share") + ": " + {"on": tr("active"), "off": tr("off"), "busy": tr("working …")}.get(
                s["state"], tr("Error") + " – " + s["why"]) + (f"  ·  {s['win']}" if s["on"] else ""), style="Mut.TLabel", wraplength=330,
                justify="left").pack(anchor="w", pady=(8, 0))
            ttk.Button(sbody, text=tr("Network share: set up in the browser"), command=lambda: self._open_page("/settings")).pack(fill="x", pady=(4, 0))
        except Exception as e:
            log_event("sys", f"Window: network share: {e}"[:160])

    # wraps: App._build_section
    App._build_section = _smb_tk_build_section


# ---- self-test (only for --self-test) ----------------------------------------------------------------------------------------------
def rucksack_smb_selftest():
    c = smb_conf("/home/nutzer/.config/motionwatch/tausch/netz", "nutzer", [("wlan0", "192.168.1.20/24")], 5120, ["exe", "sh"])
    for want in ("server min protocol = SMB2", "map to guest = never", "guest ok = no", f"valid users = {SMB_USER}", "bind interfaces only = yes",
                 "interfaces = 127.0.0.1/8 192.168.1.20/24", "hide dot files = yes", "veto files = /.*/*.exe/*.sh/", "max disk size = 5120",
                 "force user = nutzer", "wide links = no", "[print$]\n   available = no"):
        assert want in c, f"conf without «{want}»"
    assert c.count("[rucksack]") == 1 and "guest ok = yes" not in c and "SMB1" not in c
    assert "[rucksack]" not in SMB_CONF_OFF and CFG.get("tausch_smb") is not None and DEFAULTS["tausch_smb"] is False
    assert "tausch_smb" in USER_SETTINGS_DENY and "smbPanel(d)" in WEB_PAGE and "/*SMBDE*/" not in WEB_PAGE
    for k in _HX_SMB:
        assert all(TRX[L].get(k) for L in ("fr", "it", "rm")) and DE.get(k), f"text without translation: {k}"
    assert smb_pw_check("kurz") and smb_pw_check("a\nbcdefghi") and not smb_pw_check("lang-genug-1")
    st = smb_status("de")
    assert st["user"] == SMB_USER and st["win"].endswith("\\rucksack") and st["mac"].startswith("smb://")
    return "SMB2+, no guest, one user, LAN only, dot files hidden; off by default, admin only; 5 languages"


SELFTEST_EXTRA.append(("Digital backpack in the network: Samba file, rules, texts (639zzzn)", rucksack_smb_selftest))
'''
zd_exec(SMB_PY and "\n" * 61 + SMB_PY, "639zzzn_rucksack_netz.py")   # line 1 of SMB_PY = line 62: the line numbers are those of this file
