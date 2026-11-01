#@ Motion Watch – Teil 360: Ordner des früheren Basis-Simulators (sim_dir), SMS über einen LTE-Stick. 3.23: der alte Python-Simulator «MoveEye Sim · Basis» (SIM_ZIP_B64, Installieren / Starten auf dem Pi) ist entfernt. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# 3.23 (Daniel 01.11.2026): «MoveEye Sim · Basis» (the old Python simulator, SIM_ZIP_B64, install / start / stop on the Pi) is
# removed - MoveEye Sim · 3D is the simulator. An old installation in sim_dir() stays on the disk (nothing is deleted).
def sim_dir():
    return os.path.join(DATA_DIR, "simulator")


def sens_has_pir():
    return CFG["sens_on"] and any(x["kind"] == "pir" and x["src"] for x in CFG["sensors"])


def eco_fps_now():
    f = max(1.0, float(CFG["eco_fps"]))
    return 1.0 if CFG["eco_pir"] and sens_has_pir() else f


def sms_numbers():
    return [n for n in re.split(r"[,; ]+", CFG["sms_numbers"]) if _PHONE_RE.match(n)][:5]


def _sms_mmcli(num, text):
    exe = shutil.which("mmcli")
    if not exe:
        return False, "mmcli missing (sudo apt install modemmanager)"
    rc, out, err = _run([exe, "-L"], 15)
    m = re.search(r"/Modem/(\d+)", out or "")
    if not m:
        return False, "no modem found (stick plugged in? mmcli -L)"
    safe = text.replace("'", "’").replace("\\", "/")
    for pre in ([], ["sudo", "-n"]):
        rc, out, err = _run(pre + [exe, "-m", m.group(1), f"--messaging-create-sms=text='{safe}',number='{num}'"], 20)
        sm = re.search(r"/SMS/(\d+)", out or "")
        if rc == 0 and sm:
            rc2, out2, err2 = _run(pre + [exe, "-s", sm.group(1), "--send"], 60)
            if rc2 == 0:
                return True, ""
            err = err2 or out2
    return False, ("mmcli: " + (err or out or "error").strip())[:160]


def _sms_at(num, text):
    import termios
    port = CFG["sms_port"].strip() or "/dev/ttyUSB2"
    if not os.path.exists(port):
        return False, f"{port} not found"
    try:
        fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    except OSError as e:
        return False, f"{port}: {e.strerror} (in use by ModemManager?)"
    try:
        a = termios.tcgetattr(fd)
        a[4] = a[5] = termios.B115200; a[2] |= termios.CLOCAL | termios.CREAD; a[3] = 0; a[1] = 0; a[0] = 0
        termios.tcsetattr(fd, termios.TCSANOW, a)

        def cmd(b, wait=2.0, until=(b"OK", b"ERROR", b">")):
            os.write(fd, b)
            buf = b""; end = time.time() + wait
            while time.time() < end:
                try:
                    c = os.read(fd, 256)
                    buf += c
                    if any(u in buf for u in until):
                        break
                except BlockingIOError:
                    time.sleep(0.05)
            return buf
        if b"OK" not in cmd(b"AT\r"):
            return False, "the modem does not answer (wrong port?)"
        cmd(b"AT+CMGF=1\r")
        cmd(b'AT+CSCS="GSM"\r')
        if b">" not in cmd(f'AT+CMGS="{num}"\r'.encode(), 5):
            return False, "the modem refuses the SMS"
        for a_, b_ in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ß", "ss"), ("–", "-"), ("’", "'"), ("«", '"'), ("»", '"')):
            text = text.replace(a_, b_)
        txt = text.encode("ascii", "replace")[:160]
        r = cmd(txt + b"\x1a", 60, (b"+CMGS", b"ERROR"))
        return (True, "") if b"+CMGS" in r else (False, "SMS not sent (credit / network?)")
    finally:
        os.close(fd)


def _sms_hilink(num, text):
    import http.cookiejar
    base = "http://" + (CFG["sms_hilink"].strip() or "192.168.8.1")
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    try:
        with op.open(base + "/api/webserver/SesTokInfo", timeout=8) as r:
            x = r.read().decode(errors="replace")
        ses = re.search(r"<SesInfo>(.*?)</SesInfo>", x); tok = re.search(r"<TokInfo>(.*?)</TokInfo>", x)
        if not tok:
            return False, "HiLink stick not found (address?)"
        from xml.sax.saxutils import escape
        body_ = (f"<?xml version='1.0' encoding='UTF-8'?><request><Index>-1</Index><Phones><Phone>{escape(num)}</Phone></Phones><Sca></Sca>"
                 f"<Content>{escape(text[:300])}</Content><Length>{len(text[:300])}</Length><Reserved>1</Reserved>"
                 f"<Date>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</Date></request>").encode()
        h = {"__RequestVerificationToken": tok.group(1), "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        if ses:
            h["Cookie"] = ses.group(1)
        with op.open(urllib.request.Request(base + "/api/sms/send-sms", data=body_, headers=h), timeout=20) as r:
            ans = r.read().decode(errors="replace")
        return (True, "") if "<response>OK</response>" in ans else (False, "HiLink: " + (re.search(r"<code>(\d+)</code>", ans).group(1) if "<code>" in ans else "error"))
    except Exception as e:
        return False, f"HiLink: {str(e)[:120]}"


def sms_send(text, force=False):
    """Send `text` to all numbers. force=True (test) ignores the limits."""
    nums = sms_numbers()
    if not nums:
        return False, "no phone number set"
    now = time.time()
    SMS["sent"] = [t for t in SMS["sent"] if now - t < 86400]
    if not force:
        if now - SMS["last"] < float(CFG["sms_pause"]) * 60:
            return False, "pause between two SMS"
        if len(SMS["sent"]) >= int(CFG["sms_day_max"]):
            return False, "daily limit reached"
    mode = CFG["sms_mode"]
    order = {"mmcli": [_sms_mmcli], "at": [_sms_at], "hilink": [_sms_hilink]}.get(mode, [_sms_mmcli, _sms_hilink, _sms_at])
    text = re.sub(r"\s+", " ", text).strip()[:300]
    errs = []
    ok_any = False
    for n in nums:
        ok = False
        for f in order:
            ok, err = f(n, text)
            if ok:
                break
            errs.append(err)
        ok_any = ok_any or ok
    SMS["last"] = now
    if ok_any:
        SMS["sent"].append(now)
    SMS["status"] = (f"✓ {datetime.now().strftime('%H:%M')}" if ok_any else "⚠ " + (errs[-1] if errs else "error"))[:160]
    log_event("web", ("SMS sent" if ok_any else "SMS failed: " + (errs[-1] if errs else "error"))[:200])
    return ok_any, "" if ok_any else (errs[-1] if errs else "error")

