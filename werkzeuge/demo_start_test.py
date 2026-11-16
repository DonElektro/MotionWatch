#!/usr/bin/env python3
"""Test für demo_start.py («Demo beim Host», Teil 639zzzzw) – ohne Netz, ohne Browser, mit einem Wegwerf-Schlüssel.

  1. Gleiche Signatur-Prüfung wie MoveEye: öffentlicher Schlüssel, Ed25519, Nachricht, Dateimuster = Teil 380.
  2. Echte Signatur: die neueste Datei in versions.json des Repositorys ist gültig signiert; verändert = ungültig.
  3. Auswahl im eigenen Ordner (Wegwerf-Schlüssel): neueste signierte + vollständige Version; verändert, unsigniert, ohne
     ZIP, falsche ZIP, ohne Host-Modus, Brücke = nie.
  4. Update (GitHub nachgestellt): holt Datei + ZIP nur in den eigenen Ordner, falsche Prüfsumme bleibt nicht liegen,
     nur https-Adressen von GitHub, alte Versionen aufgeräumt (höchstens 2), kein Update auf eine ältere / gleiche.
  5. Werkseinstellungen: nur demo_daten wird geleert; nächster Zeitpunkt 03:30 Schweizer Zeit.
  6. Echter Lauf: demo_start.py startet eine nachgemachte Version mit den richtigen Optionen und beendet sie auf SIGTERM.
python3 werkzeuge/demo_start_test.py
"""
import hashlib, importlib.util, json, os, re, shutil, signal, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL = []


def ok(cond, what):
    print(("  ok  " if cond else "  FEHLER  ") + what)
    if not cond:
        FAIL.append(what)


def load(path, name="demo_start_t"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def func_src(text, name):
    m = re.search(r"^def %s\(.*?(?=^\S)" % re.escape(name), text, re.M | re.S)
    return m.group(0).rstrip() if m else ""


def fake_program(folder, ver, host=True, zip_ok=True, extra=""):
    v_ = ver.replace(".", "_")
    zn = f"moveeye_daten_{v_}.zip"
    zb = ("zip of " + ver).encode() * 50
    with open(os.path.join(folder, zn), "wb") as f:
        f.write(zb if zip_ok else zb + b"x")
    txt = (f'APP_VERSION = "{ver}"\nZD_FILE = "{zn}"\nZD_SHA256 = "{hashlib.sha256(zb).hexdigest()}"\n'
           + ('def _args(ap):\n    ap.add_argument("--host-modus")\ndef host_mode_start(a): pass\n' if host else "")
           + "import sys, time, json, os\n"
           + "if __name__ == '__main__':\n"
           + "    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'argv.json'), 'w').write(json.dumps(sys.argv[1:] + ['ENV=' + os.environ.get('MALLOC_ARENA_MAX', '')]))\n"
           + "    time.sleep(120)\n" + extra)
    fn = f"webcam_bewegung_{v_}.py"
    with open(os.path.join(folder, fn), "w") as f:
        f.write(txt)
    return fn, hashlib.sha256(txt.encode()).hexdigest()


def main():
    src = open(os.path.join(ROOT, "demo_start.py"), encoding="utf-8").read()
    p380 = open(os.path.join(ROOT, "quelle", "380_updates.py"), encoding="utf-8").read()
    print("1. gleiche Prüfung wie MoveEye (Teil 380)")
    k380 = re.search(r'^UPDATE_PUBKEY = "([0-9a-f]{64})"', p380, re.M).group(1)
    ds = load(os.path.join(ROOT, "demo_start.py"))
    ok(ds.UPDATE_PUBKEY == k380, "öffentlicher Schlüssel = UPDATE_PUBKEY (380)")
    for fn in ("_ed25519_impl", "_sig_msg", "sig_ok"):
        a, b = func_src(src, fn), func_src(p380, fn)
        ok(a and a == b, f"{fn} Wort für Wort wie in 380")
    m380 = re.search(r'^VFILE_RE = re\.compile\((r"[^"]+")\)', p380, re.M).group(1)
    ok(m380 in src, "Dateimuster VFILE_RE wie 380")
    ok("subprocess.Popen(child_cmd" in src and "shell=True" not in src and "os.system" not in src, "startet nur MoveEye selbst, keine Shell")
    ok(set(ds.GH_HOSTS) <= {"raw.githubusercontent.com", "objects.githubusercontent.com", "github.com"}, "nur Adressen von GitHub")
    ok(not ds._https_ok("http://raw.githubusercontent.com/x") and not ds._https_ok("https://evil.example/x")
       and not ds._https_ok("https://raw.githubusercontent.com.evil.example/x") and ds._https_ok("https://raw.githubusercontent.com/a/b"),
       "http / fremde Rechner abgelehnt")
    print("2. echte Signatur im Repository")
    try:
        man = json.load(open(os.path.join(ROOT, "versions.json"), encoding="utf-8"))
        ents = ds.signed_entries(man)
        ok(len(ents) >= 1, f"versions.json: {len(ents)} signierte Einträge")
        e = max(ents.values(), key=lambda x: ds.vkey(x["version"]))
        ok(ds.sig_ok(e["version"], e["file"], e["sha256"], e["sig"]), f"{e['version']}: Signatur gültig")
        ok(not ds.sig_ok(e["version"], e["file"], "0" * 64, e["sig"]), "andere Prüfsumme: ungültig")
        ok(not ds.sig_ok("9.9.9", e["file"], e["sha256"], e["sig"]), "andere Nummer: ungültig")
        if os.path.isfile(os.path.join(ROOT, e["file"])):
            same = ds.sha256_file(os.path.join(ROOT, e["file"]), ds.UPD_MAX_BYTES) == e["sha256"]
            print(f"  {'ok  ' if same else 'Hinweis:'} {e['file']}: Prüfsumme der Datei " + ("passt" if same else "anders (neu gebaut, noch nicht signiert)"))
    except (OSError, ValueError) as ex:
        ok(False, f"versions.json lesbar ({ex})")

    print("3. Auswahl im eigenen Ordner (Wegwerf-Schlüssel)")
    tmp = tempfile.mkdtemp(prefix="demostart_")
    try:
        pub, sign, _v = ds._ed25519_impl()
        seed = os.urandom(32); pk = pub(seed).hex()
        work = os.path.join(tmp, "host"); os.makedirs(work)
        shutil.copy(os.path.join(ROOT, "demo_start.py"), work)
        t = open(os.path.join(work, "demo_start.py"), encoding="utf-8").read().replace(k380, pk)
        open(os.path.join(work, "demo_start.py"), "w", encoding="utf-8").write(t)
        d = load(os.path.join(work, "demo_start.py"), "demo_start_w")

        def entry(ver, fn, sha, good=True, **kw):
            return dict({"version": ver, "file": fn, "sha256": sha, "sig": sign(seed, d._sig_msg(ver, fn, sha if good else "1" * 64)).hex()}, **kw)
        f1, s1 = fake_program(work, "5.1.0")
        f2, s2 = fake_program(work, "5.2.0")
        f3, s3 = fake_program(work, "5.3.0")                        # unsigned in the list
        f4, s4 = fake_program(work, "5.4.0", host=False)            # no host mode
        f5, s5 = fake_program(work, "5.5.0", zip_ok=False)          # wrong zip
        lst = {"versions": [entry("5.5.0", f5, s5), entry("5.4.0", f4, s4), entry("5.3.0", f3, s3, good=False),
                            entry("5.2.0", f2, s2), entry("5.1.0", f1, s1), entry("5.9.0", "webcam_bewegung_5_9_0.py", "a" * 64),
                            dict(entry("5.8.0", "webcam_bewegung_5_8_0.py", "b" * 64), bridge=True)]}
        json.dump(lst, open(d.MANIFEST_COPY, "w"))
        e, p = d.pick_local()
        ok(e is not None and e["version"] == "5.2.0", f"gewählt: {e and e['version']} (5.5 falsche ZIP, 5.4 ohne Host-Modus, 5.3 unsigniert, 5.9 fehlt)")
        ok("5.8.0" not in [x["version"] for x in d.signed_entries(lst).values()], "Brücke wird nie gewählt")
        with open(os.path.join(work, f2), "a") as f:
            f.write("# changed\n")
        e, p = d.pick_local()
        ok(e is not None and e["version"] == "5.1.0", "5.2.0 verändert -> 5.1.0")
        os.remove(os.path.join(work, "moveeye_daten_5_1_0.zip"))
        e, why = d.pick_local()
        ok(e is None and any("zip missing" in w for w in why), "ohne ZIP: keine Version")
        print("4. Update (GitHub nachgestellt)")
        for n in os.listdir(work):
            if n.startswith(("webcam_bewegung_", "moveeye_daten_")):
                os.remove(os.path.join(work, n))
        srv = os.path.join(tmp, "github"); os.makedirs(srv)
        fa, sa = fake_program(srv, "6.0.0"); fb, sb = fake_program(srv, "6.1.0"); fc, sc = fake_program(srv, "6.2.0")
        man = {"versions": [entry("6.2.0", fc, sc), entry("6.1.0", fb, sb), entry("6.0.0", fa, sa)]}
        base = d.MANIFEST_URL.rsplit("/", 1)[0] + "/"
        seen = []

        def fake_get(url, limit, dest=None, timeout=60):
            seen.append(url)
            if not d._https_ok(url):
                raise ValueError("only https addresses of GitHub")
            name = url.split("?")[0][len(base):]
            b = json.dumps(man).encode() if name == "versions.json" else open(os.path.join(srv, name), "rb").read()
            if len(b) > limit:
                raise ValueError("too big")
            if dest is None:
                return b
            open(dest, "wb").write(b)
            return len(b)
        d.http_get = fake_get
        for v_ in ("5_0_0", "5_0_1", "5_0_2"):
            fake_program(work, v_.replace("_", "."))
        v = d.update()
        ok(v == "6.2.0" and not d.verify(man["versions"][0]), "neueste signierte Version geholt und geprüft (Datei + ZIP)")
        ok(all(u.startswith(base) for u in seen), "nur von GitHub geholt")
        left = sorted(n for n in os.listdir(work) if n.startswith("webcam_bewegung_"))
        ok(left == ["webcam_bewegung_5_0_2.py", "webcam_bewegung_6_2_0.py"], f"aufgeräumt, höchstens 2 Versionen: {left}")
        ok(d.update("6.2.0") == "", "gleiche Version: kein Update")
        # a newer one with a wrong checksum on the server
        fd, sd = fake_program(srv, "6.3.0")
        man["versions"].insert(0, entry("6.3.0", fd, "c" * 64))
        try:
            d.update("6.2.0"); got = "ok"
        except ValueError as ex:
            got = str(ex)
        ok("checksum" in got and not os.path.exists(os.path.join(work, fd)), "falsche Prüfsumme: Fehler, nichts liegt im Ordner")
        ok(not [n for n in os.listdir(work) if n.endswith(".part")], "keine halben Dateien")
        man["versions"][0] = entry("6.3.0", fd, sd, good=False)
        ok(d.update("6.2.0") == "", "unsigniert: nie geholt")
        fe, se = fake_program(srv, "6.4.0", host=False)
        man["versions"].insert(0, entry("6.4.0", fe, se))
        ok(d.update("6.2.0") == "" and not os.path.exists(os.path.join(work, fe)), "ohne Host-Modus: nicht benutzt, gelöscht")
        man["versions"].pop(0)
        print("5. Werkseinstellungen, Zeitpunkt")
        os.makedirs(os.path.join(d.DATA, "recordings")); open(os.path.join(d.DATA, "recordings", "a.mp4"), "w").write("x")
        open(os.path.join(work, "bleibt.txt"), "w").write("x")
        d.reset_data()
        ok(os.listdir(d.DATA) == [] and os.path.exists(os.path.join(work, "bleibt.txt")), "nur demo_daten geleert")
        nr = d.next_reset()
        ok(0 < nr - time.time() <= 86400 + 3600, "nächstes Zurücksetzen innerhalb eines Tages")
        try:
            from zoneinfo import ZoneInfo
            from datetime import datetime
            t = datetime.fromtimestamp(nr, ZoneInfo("Europe/Zurich"))
            ok((t.hour, t.minute) == (3, 30), f"um 03:30 Schweizer Zeit ({t:%Y-%m-%d %H:%M %Z})")
        except Exception as ex:
            print(f"  (Zeitzonen-Daten fehlen: {ex})")
        cmd = d.child_cmd(os.path.join(work, fc))
        ok(cmd[2:] == ["--demo", "--headless", "--bind", "127.0.0.1", "--port", str(int(os.environ.get("PORT") or 5000)), "--host-modus",
                       "--url-prefix", "/demo", "--config", d.DATA], "Startoptionen: " + " ".join(cmd[2:]))
        print("6. echter Lauf (Prozess)")
        env = dict(os.environ, PORT="5099")
        pr = subprocess.Popen([sys.executable, os.path.join(work, "demo_start.py")], cwd=tmp, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        argv_p = os.path.join(work, "argv.json"); t0 = time.time()
        while time.time() - t0 < 30 and not os.path.exists(argv_p):
            time.sleep(0.2)
        argv = json.load(open(argv_p)) if os.path.exists(argv_p) else []
        ok("--host-modus" in argv and argv[argv.index("--port") + 1] == "5099" and argv[argv.index("--bind") + 1] == "127.0.0.1",
           f"gestartet mit {' '.join(argv)}")
        ok("ENV=2" in argv, "MoveEye läuft mit MALLOC_ARENA_MAX=2 (Speicher)")
        pr.send_signal(signal.SIGTERM)
        try:
            out, _ = pr.communicate(timeout=40)
        except subprocess.TimeoutExpired:
            pr.kill(); out, _ = pr.communicate()
        ok(pr.returncode == 0, f"SIGTERM: sauber beendet (Code {pr.returncode})")
        ok("6.2.0 - signature and data zip checked" in out, "Protokoll nennt die geprüfte Version")
        kids = subprocess.run(["pgrep", "-f", os.path.join(work, fc)], capture_output=True, text=True).stdout.strip()
        ok(not kids, "kein MoveEye bleibt übrig")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("FEHLER: " + "; ".join(FAIL) if FAIL else "demo_start: alles gut")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
