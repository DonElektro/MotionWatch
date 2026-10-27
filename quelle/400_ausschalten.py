#@ Motion Watch – Teil 400: Pi ausschalten / neu starten. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Power: shut down / restart the Raspberry Pi (web page + desktop window). The recording is finished and the settings are
#   saved first. Works as root, with the polkit rule of --allow-wifi or (Raspberry Pi OS) with sudo without a password.
# ----------------------------------------------------------------------------
POWER = {"pending": "", "msg": ""}


def _power_cmd(action):
    cmds = [["systemctl", action]]
    if not _is_root() and shutil.which("sudo"):
        cmds.append(["sudo", "-n", "systemctl", action])
    err = ""
    for c in cmds:
        rc, _out, e = _run(c, timeout=30)
        if rc == 0:
            return ""
        err = e or f"exit {rc}"
    return (f"no permission to {'shut down' if action == 'poweroff' else 'restart'} ({err[:120]}) - allow it once with: "
            f"sudo {sys.executable} {os.path.abspath(__file__)} --allow-wifi")


def power_action(action, delay=3.0, source="desktop"):
    """action: poweroff | reboot. The answer comes back at once, the Pi goes down after `delay` seconds."""
    if action not in ("poweroff", "reboot"):
        return False, "unknown action"
    if POWER["pending"]:
        return True, ""
    POWER["pending"] = action; POWER["msg"] = ""
    STATE["power"] = action
    log_event("sys", ("Shutting down the Pi" if action == "poweroff" else "Restarting the Pi") + f" ({source})")

    def work():
        time.sleep(delay)                                    # the page / window gets its answer first
        try:
            w = WATCH_REF["w"]
            end = time.time() + 10.0                         # the camera loop ends a running recording (POWER["pending"])
            while w is not None and w.writer is not None and time.time() < end:
                time.sleep(0.2)
            if AUDIO is not None:
                AUDIO.wait_mux(30.0)
            sound_stop()
            save_settings_now()
        except Exception as e:
            log_event("sys", f"Before shutdown: {e}"[:200])
        err = _power_cmd(action)
        if err:
            POWER["pending"] = ""; POWER["msg"] = err; STATE["power"] = ""
            log_event("sys", ("Shutdown failed: " if action == "poweroff" else "Restart failed: ") + err[:160])
    threading.Thread(target=work, daemon=True, name="power").start()
    return True, ""


