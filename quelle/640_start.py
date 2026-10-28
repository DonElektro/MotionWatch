#@ Motion Watch – Teil 640: Start: Befehlszeile, Selbsttest, Programmstart. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", type=int, default=None, help="USB camera number (same as --source usb:N)")
    ap.add_argument("--source", default=None, help="video source: auto | usb:N | pi:N | rtsp://... | http://... (saved in the settings)")
    ap.add_argument("--web", action="store_true", help="(default now) start the web page / stream immediately")
    ap.add_argument("--no-web", action="store_true", help="do not start the web page / stream (it can be switched on in the window)")
    ap.add_argument("--headless", action="store_true", help="no desktop window, web page only (implies --web)")
    ap.add_argument("--port", type=int, default=None, help="web port (default 5000)")
    ap.add_argument("--web-password", default="", help="protect the web page with this password")
    ap.add_argument("--notify-url", default=None, help="webhook / ntfy URL called when a person is detected")
    ap.add_argument("--bind", default="0.0.0.0", help="address the web page listens on (127.0.0.1 = this computer only; use with a VPN / reverse proxy)")
    ap.add_argument("--https", action="store_true", help="serve the web page over HTTPS (self-signed certificate is created if --cert/--key are missing)")
    ap.add_argument("--cert", default="", help="certificate file (PEM) for --https")
    ap.add_argument("--key", default="", help="private key file (PEM) for --https")
    ap.add_argument("--boot", action="store_true", help="(used by the autostart) started at boot: switch the own Wi-Fi on")
    ap.add_argument("--config", default="", help="folder for settings / log / certificate (default ~/.config/motionwatch)")
    ap.add_argument("--allow-wifi", action="store_true", help="allow this user to manage Wi-Fi, the own hotspot and the clock (run once with sudo) and exit")
    ap.add_argument("--print-service", action="store_true", help="print a systemd unit file for autostart and exit")
    ap.add_argument("--install-service", action="store_true", help="install + enable the systemd service (run with sudo) and exit")
    ap.add_argument("--make-manifest", metavar="FOLDER", help="write FOLDER/versions.json for the update function and exit")
    ap.add_argument("--sign-key", default="", metavar="FILE", help="with --make-manifest: sign the versions with the secret key in FILE")
    ap.add_argument("--base-url", default="", help="with --make-manifest: web address of the folder (e.g. https://raw.githubusercontent.com/<user>/<repo>/main)")
    ap.add_argument("--self-test", nargs="?", const="", default=None, metavar="FOLDER",
                    help="quick checks without camera (with FOLDER: also the signatures in FOLDER/versions.json) and exit")
    ap.add_argument("--helper", action="store_true", help="also work as AI helper for a Raspberry Pi in the network (port 5057, pairing code)")
    ap.add_argument("--demo", action="store_true", help="demo: drawn scene with a person / animals walking by, own settings folder, no changes to the computer")
    ap.add_argument("--paused-until", type=float, default=None, help=argparse.SUPPRESS)   # used by "pause the program"
    a = ap.parse_args()
    if a.make_manifest:
        sys.exit(make_manifest(a.make_manifest, a.base_url, a.sign_key))
    if a.self_test is not None:
        sys.exit(self_test(a.self_test))
    if a.allow_wifi:
        sys.exit(allow_wifi())
    if a.print_service:
        print(service_text()); sys.exit(0)
    if a.install_service:
        sys.exit(install_service())
    WEB_OPTS.update(bind=a.bind, https=a.https or bool(a.cert and a.key), cert=a.cert, key=a.key)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))          # systemd stop -> finish the recording, save the settings
    if a.demo:
        DEMO["on"] = True
        set_data_dir(a.config or os.path.join(tempfile.gettempdir(), "motionwatch-demo"))
    else:
        set_data_dir(a.config or DATA_DIR)
    took = prepare_settings_file() if not a.demo else ""
    threading.Thread(target=clock_guard_loop, daemon=True, name="clockguard").start()
    threading.Thread(target=outbox_loop, daemon=True, name="outbox").start()
    threading.Thread(target=guard_watch_loop, daemon=True, name="guardwatch").start()
    load_settings()
    if STATE.get("settings_restored"):
        log_event("sys", "The settings file was damaged (kept as " + os.path.basename(STATE["settings_restored"]) + ") - "
                  + ("the backup copy was used" if STATE.get("settings_from_backup") else "no usable backup: default settings!"))
    testopt_load()
    threading.Thread(target=testopt_nightly_loop, daemon=True, name="testnight").start()
    if not a.demo and not a.helper:
        threading.Thread(target=tunnel_start, daemon=True).start()   # 2.95.54: simulators behind a firewall connect out to here
    if (a.helper or CFG.get("helper_serve")) and not a.demo:
        if a.helper and not CFG.get("helper_serve"):
            CFG["helper_serve"] = True; save_settings()
        helper_server_start()
    if not CFG.get("sim_autostart_v2"):                    # 2.95.26: the Pi outside does not switch to a PC simulator by itself
        CFG["sim_autostart_v2"] = True
        if _is_pi():
            CFG["sim_autostart"] = False
        save_settings()
    if took:
        log_event("sys", took); print(took)
    print(f"Settings: {SETTINGS_FILE}")
    if a.port:
        CFG["web_port"] = a.port
    CFG["web_password"] = a.web_password
    if a.notify_url is not None:
        CFG["notify_url"] = a.notify_url
    if DEMO["on"]:
        CFG.update(source="demo", setup_done=True, record_dir=os.path.join(DATA_DIR, "recordings"), notify_on=False, update_auto=False,
                   update_install=False, hotspot_on=False, mqtt_on=False, backup_type="off", fleet=[], ai_enabled=True, diary_on=True,
                   device_name=CFG["device_name"] or "Demo")
        a.source = None; a.cam = None
        print("DEMO MODE - settings in " + DATA_DIR)
    if not DEMO["on"] and not instance_lock(CFG["web_port"]):          # only one MoveEye at a time
        if a.boot or not instance_takeover(CFG["web_port"], not a.headless):
            sys.exit(0)
    start_guard()                                     # after an update: go back if the new version keeps crashing
    run_guard_start()                                 # did the whole Pi go off last time? two short runs -> safe start
    if a.paused_until and a.paused_until > time.time():
        run_paused(a.paused_until, _base_args())          # comes back by itself (execv), never returns
    if not a.headless and not GUI_OK:
        print(f"Desktop window not available ({GUI_ERR}) - running headless with the web page instead.")
        print("   To get the window:  sudo apt install python3-pil.imagetk python3-tk")
        a.headless = True
    if a.source:
        if SRC_RE.match(a.source):
            CFG["source"] = a.source
        elif _url_ok(a.source):
            known = next((x for x in CFG["ip_sources"] if x["url"] == a.source), None)
            if known is None:
                _ok, _err, _sid = source_add("Command line camera", a.source)
                CFG["source"] = "url:" + _sid
            else:
                CFG["source"] = "url:" + known["id"]
        else:
            ap.error("--source must be auto, usb:N, pi:N or an rtsp:// / http:// URL")
    elif a.cam is not None:
        CFG["source"] = f"usb:{a.cam}"
    if not DEMO["on"]:
        storage_apply(start=True)                                   # recordings on the chosen SSD / USB drive (if there)
    LOOPREC = LoopRecorder()
    threading.Thread(target=rtsp_watch, daemon=True, name="rtsp-watch").start()
    WATCH = MotionWatch()
    if DEMO["on"]:
        CFG["ai_enabled"] = True
    threading.Thread(target=watchdog_loop, daemon=True, name="watchdog").start()
    WEB = WebStream(WATCH)
    arm_tick()
    if DEMO["on"]:
        threading.Timer(3.0, lambda: arm(0)).start()                  # the demo starts armed
    else:
        NetAuto()
    if a.boot and CFG["net_mode"] == "hotspot" and not DEMO["on"]:                    # started by the autostart: own Wi-Fi on
        boot_hotspot()
    elif a.boot and CFG["net_mode"] == "client" and CFG["hotspot_on"]:
        CFG["hotspot_on"] = False
    elif CFG["hotspot_on"] and not a.boot:                         # e.g. camping: the own Wi-Fi comes back after a restart
        hotspot_switch_later(True, 3.0)
    try:
        if not DEMO["on"]:
            autostart_follow_version(); autostart_check_boot(); autostart_refresh()
    except Exception:
        pass
    if not a.no_web or a.headless:                                 # the web page is on from the start (1.6.3)
        CFG["web_stream"] = True
        WEB.start()
    threading.Thread(target=WATCH.run, daemon=True).start()
    apply_theme()
    ip = local_ip()
    print(f"MoveEye {APP_VERSION} started" + (f" - web page on {page_address(ip) if ip else 'http://<ip>:' + str(CFG['web_port']) + '/'}" if CFG["web_stream"] else ""))
    if CFG["web_stream"] and not web_pw_active():
        print("   Note: the web page has no password - anybody in this network can open it. Start with --web-password SECRET")
    if a.headless:
        if CFG["desktop_notice"] and not DEMO["on"]:      # started in the background: tell the person at the Pi
            desktop_notice(tr("MoveEye is running"),
                           tr("Started in the background.") + (" " + tr("Page") + ": " + page_address(ip) if ip and CFG["web_stream"] else ""),
                           wait=300 if a.boot else 30)
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass
    else:
        App(WATCH, WEB).run()
