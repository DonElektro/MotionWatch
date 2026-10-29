#@ MoveEye – Teil 066: Speicherkarte schonen: Schreibmenge pro Tag, Dateisystem-Fehler, Schreibschutz (Overlay). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Memory card protection (Daniel, 29.10.2026): on camp sites the power goes off without warning and a memory card that is
# written all day wears out. Here, without root rights and without extra writes worth mentioning:
#  * how much is written to the card per day (sectors written from /sys/block/<card>/stat, all partitions together;
#    the day totals go into <data>/sdcard_wear.json at most once an hour),
#  * file system errors (ext4 error counter in /sys/fs/ext4/<partition>/errors_count, and dmesg if it may be read),
#  * whether the root file system is protected (overlay = read-only card, changes in RAM) or was made read-only by errors,
#  * eMMC wear estimate (only eMMC has it: /sys/block/mmcblk*/device/life_time).
# The self-check (health_check, web and window) shows one traffic light «Memory card health» (145_selbstheilung.py adds it),
# the manual has the chapter «Memory card: fewer writes, read-only during the season» (607_uebersetzungen_robust.py).
# ----------------------------------------------------------------------------
SDCARD = {"t": 0.0, "dev": "", "base": "", "part": "", "last_sec": None, "boot": "", "days": {}, "first_t": 0.0, "today_mb": 0.0,
          "saved_t": 0.0, "ext4_err": None, "dmesg": None, "dmesg_t": 0.0, "dmesg_ok": None, "dmesg_last": "", "overlay": False,
          "root_ro": False, "life": None, "logged_err": 0, "busy": False}
SD_SAMPLE_S = 600                      # one look every 10 minutes (reading /sys costs nothing, nothing is written)
SD_SAVE_S = 3600                       # the day totals are written at most once an hour
SD_ERR_RX = re.compile(r"EXT4-fs (?:error|warning)|Buffer I/O error|I/O error, dev|blk_update_request: .*error|FAT-fs .*error"
                       r"|mmc\d+: .*(?:error|timeout|CRC)|Remounting filesystem read-only|EXT4-fs .*read-only", re.I)


def _sd_file():
    return os.path.join(DATA_DIR, "sdcard_wear.json")


def _sd_block_of(path):
    """(partition, whole device) of the block device a folder lives on, e.g. ('mmcblk0p2', 'mmcblk0'); ('', '') when it is
    not a block device (overlay, tmpfs, not Linux)"""
    try:
        st = os.stat(path)
        p = os.path.realpath("/sys/dev/block/%d:%d" % (os.major(st.st_dev), os.minor(st.st_dev)))
    except (OSError, AttributeError, ValueError):
        return "", ""
    if not os.path.isdir(p):
        return "", ""
    name = os.path.basename(p)
    if os.path.isfile(os.path.join(p, "partition")):
        return name, os.path.basename(os.path.dirname(p))
    return name, name


def _sd_find():
    """the card the program and the settings are on; with an overlay root the real card underneath (mmcblk0)"""
    part, base = _sd_block_of(DATA_DIR if os.path.isdir(DATA_DIR) else "/")
    if not base:
        part, base = _sd_block_of("/")
    if not base and os.path.isfile("/sys/block/mmcblk0/stat"):
        part, base = "", "mmcblk0"
    return part, base


def _sd_read_int(p):
    try:
        with open(p) as f:
            return int(f.read().split()[0], 0)
    except (OSError, ValueError, IndexError):
        return None


def _sd_sectors(base):
    """sectors (512 bytes) written to the whole device since the start of the computer"""
    try:
        with open(f"/sys/block/{base}/stat") as f:
            v = f.read().split()
        return int(v[6])
    except (OSError, ValueError, IndexError):
        return None


def _sd_mounts():
    """(root is an overlay, root is read-only although it should not be)"""
    ov = ro = False
    try:
        with open("/proc/mounts") as f:
            for ln in f:
                x = ln.split()
                if len(x) >= 4 and x[1] == "/":
                    ov = x[2] == "overlay" or ov
                    ro = (x[2] != "overlay" and "ro" in x[3].split(","))
    except OSError:
        pass
    try:
        with open("/proc/cmdline") as f:
            ov = ov or "overlayroot=tmpfs" in f.read()
    except OSError:
        pass
    return ov, ro


def _sd_dmesg():
    """number of storage errors in the kernel messages, the last one; None = dmesg may not be read (no root)"""
    if not shutil.which("dmesg"):
        return None, ""
    try:
        r = subprocess.run(["dmesg"], capture_output=True, text=True, timeout=4)
    except (OSError, subprocess.SubprocessError):
        return None, ""
    if r.returncode != 0 or not r.stdout:
        return None, ""
    hits = [ln.strip() for ln in r.stdout.splitlines() if SD_ERR_RX.search(ln)]
    return len(hits), (hits[-1][-160:] if hits else "")


def _sd_boot_id():
    try:
        with open("/proc/sys/kernel/random/boot_id") as f:
            return f.read().strip()
    except OSError:
        return ""


def _sd_load():
    try:
        with open(_sd_file()) as f:
            d = json.load(f)
        if isinstance(d, dict):
            SDCARD["days"] = {k: float(v) for k, v in (d.get("days") or {}).items() if isinstance(v, (int, float))}
            if d.get("boot") == SDCARD["boot"] and isinstance(d.get("sec"), int):
                SDCARD["last_sec"] = d["sec"]           # same start of the computer: go on counting from there
            SDCARD["first_t"] = float(d.get("first") or 0.0)
    except (OSError, ValueError, TypeError):
        pass


def _sd_save():
    days = dict(sorted(SDCARD["days"].items())[-21:])
    SDCARD["days"] = days
    try:
        tmp = _sd_file() + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"days": {k: round(v, 1) for k, v in days.items()}, "boot": SDCARD["boot"], "sec": SDCARD["last_sec"],
                       "first": SDCARD["first_t"]}, f)
        os.replace(tmp, _sd_file())
        SDCARD["saved_t"] = time.time()
    except OSError:
        pass


def sdcard_tick(force=False):
    """one look (every 10 minutes from the health thread of 145, and when the self-check is opened for the first time)"""
    now = time.time()
    if SDCARD["busy"] or (not force and now - SDCARD["t"] < SD_SAMPLE_S):
        return
    SDCARD["busy"] = True
    try:
        first = not SDCARD["t"]
        SDCARD["t"] = now
        if first:
            SDCARD["part"], SDCARD["base"] = _sd_find()
            SDCARD["boot"] = _sd_boot_id()
            _sd_load()
            if not SDCARD["first_t"]:
                SDCARD["first_t"] = now
            b = SDCARD["base"]
            if b:
                for nm in ("life_time", "pre_eol_info"):
                    v = None
                    try:
                        with open(f"/sys/block/{b}/device/{nm}") as f:
                            v = f.read().split()
                    except OSError:
                        pass
                    if v and nm == "life_time":
                        try:
                            SDCARD["life"] = max(int(x, 16) for x in v)   # 0x01 = 0-10 % used … 0x0B = worn out
                        except ValueError:
                            pass
        SDCARD["overlay"], SDCARD["root_ro"] = _sd_mounts()
        b = SDCARD["base"]
        if b:
            sec = _sd_sectors(b)
            if sec is not None:
                last = SDCARD["last_sec"]
                add = (sec - last) if (last is not None and sec >= last) else (0 if last is None else sec)
                SDCARD["last_sec"] = sec
                day = datetime.now().strftime("%Y-%m-%d")
                SDCARD["days"][day] = SDCARD["days"].get(day, 0.0) + add * 512 / 1e6
                SDCARD["today_mb"] = SDCARD["days"][day]
            part = SDCARD["part"] or b
            SDCARD["ext4_err"] = _sd_read_int(f"/sys/fs/ext4/{part}/errors_count")
        if force or now - SDCARD["dmesg_t"] > 1800:
            SDCARD["dmesg_t"] = now
            n, last_ = _sd_dmesg()
            SDCARD["dmesg_ok"] = n is not None
            SDCARD["dmesg"] = n
            SDCARD["dmesg_last"] = last_
        errs = int(SDCARD["ext4_err"] or 0) + int(SDCARD["dmesg"] or 0)
        if errs > SDCARD["logged_err"]:
            SDCARD["logged_err"] = errs
            log_event("sys", f"Memory card: {errs} file system / read error(s) found" + (f" - {SDCARD['dmesg_last']}" if SDCARD["dmesg_last"] else ""))
        if b and (now - SDCARD["saved_t"] > SD_SAVE_S or len(SDCARD["days"]) and max(SDCARD["days"]) != datetime.now().strftime("%Y-%m-%d")):
            _sd_save()
    except Exception as e:
        print(f"memory card check: {e}")
    finally:
        SDCARD["busy"] = False


def sdcard_rate():
    """MB per day: the average of the full days of before (up to 7), else what today brings so far, scaled to a day"""
    today = datetime.now().strftime("%Y-%m-%d")
    full = [v for k, v in sorted(SDCARD["days"].items()) if k != today][-7:]
    if full:
        return sum(full) / len(full), True
    t0 = max(SDCARD["first_t"], datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    span = time.time() - t0
    if span < 1200:
        return None, False
    return SDCARD.get("today_mb", 0.0) * 86400.0 / span, False


def sdcard_state():
    sdcard_tick()
    r, full = sdcard_rate()
    return {"dev": SDCARD["base"], "part": SDCARD["part"], "mb_day": round(r, 1) if r is not None else None, "days_known": full,
            "today_mb": round(SDCARD.get("today_mb", 0.0), 1), "ext4_errors": SDCARD["ext4_err"], "dmesg_errors": SDCARD["dmesg"],
            "dmesg_readable": SDCARD["dmesg_ok"], "dmesg_last": SDCARD["dmesg_last"], "overlay": SDCARD["overlay"],
            "root_ro": SDCARD["root_ro"], "emmc_life": SDCARD["life"], "free_mb": (STATE.get("disk") or {}).get("free_mb")}


def sdcard_health_item(L):
    """one traffic light for the self-check: {id, icon, title, level, text, tip, link}"""
    T = lambda x: tr(x, L)
    s = sdcard_state()
    if not s["dev"] and not s["overlay"]:
        return {"id": "sdwear", "icon": "🪪", "title": T("Memory card health"), "level": "off", "text": T("not measurable on this computer"), "tip": "",
                "link": "/help#sdcard"}
    parts, level, tip = [], "ok", ""
    if s["mb_day"] is not None:
        mb = s["mb_day"]
        parts.append(trf("≈ {n} written per day", L, n=(f"{mb / 1000:.1f} GB" if mb >= 1000 else f"{mb:.0f} MB")))
    else:
        parts.append(T("write volume: measuring (20 min)"))
    if s["free_mb"] is not None:
        parts.append(f"{s['free_mb'] / 1024:.1f} GB " + T("free"))
    errs = int(s["ext4_errors"] or 0) + int(s["dmesg_errors"] or 0)
    if errs:
        parts.append(trf("{n} file system error(s)", L, n=errs))
        level = "bad"
        tip = "The memory card reports errors: copy the recordings, check the card on a PC (or replace it) and use the read-only protection during the season."
    elif s["dmesg_readable"] is False and s["ext4_errors"] is None:
        parts.append(T("errors: not readable"))
    else:
        parts.append(T("no file system errors"))
    if s["root_ro"]:
        level = "bad"
        parts.append(T("read-only after errors"))
        tip = "The system switched the card to read-only (errors). Restart; if it happens again, replace the card."
    if s["overlay"]:
        parts.append(T("read-only protection on"))
        try:
            rd = rec_dir() if os.path.isdir(rec_dir()) else ""
        except Exception:
            rd = ""
        if rd and not _sd_block_of(rd)[1] and level == "ok":
            level = "warn"
            tip = ("Read-only protection is on: recordings and changed settings stay only in the memory (RAM) and are gone after a restart. "
                   "Put the recordings on a USB drive / SSD (Settings → Recording).")
    elif level == "ok" and s["mb_day"] is not None and s["mb_day"] > 5000:
        level = "warn"
        tip = "A lot is written to the card: put the recordings on a USB drive / SSD, switch off continuous recording, or use the read-only protection during the season."
    if s["emmc_life"] is not None and s["emmc_life"] >= 0x08 and level != "bad":
        level = "warn"
        parts.append(trf("worn {p} %", L, p=min(100, s["emmc_life"] * 10)))
        tip = "The memory chip is quite worn: plan a replacement."
    return {"id": "sdwear", "icon": "🪪", "title": T("Memory card health"), "level": level, "text": " · ".join(parts), "tip": T(tip) if tip else "",
            "link": "/help#sdcard"}
