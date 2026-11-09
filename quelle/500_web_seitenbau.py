#@ Motion Watch – Teil 500: Web: App-Symbol, Seiten zusammensetzen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
APP_ICON_LIST = [("moveeye", "MoveEye"), ("radar", "Radar"), ("radar2", "Radar, two rings"), ("cross", "Radar, gaps crosswise"), ("trail", "Radar with afterglow"),
                 ("rings4", "Four directions"), ("waves", "Lens with waves"),
                 ("light", "Light radar (green)"), ("night", "Night radar (orange beam)"), ("forest", "Forest with a find"), ("thermal", "Thermal picture"),
                 ("fov", "Field of view"), ("camp", "Tent watch"), ("shield", "Shield"), ("hits", "Radar with finds"),
                 ("classic", "Classic (orange)")]


def app_icon_id():
    ic = str(CFG.get("app_icon") or "moveeye")
    return ic if ic in dict(APP_ICON_LIST) else "moveeye"


def host_variant():
    """'ext' when the page was opened over Tailscale (100.x address or *.ts.net name), else 'int'. '' outside a request."""
    try:
        from flask import has_request_context, request
        if not has_request_context():
            return ""
        host = (request.host or "").rsplit(":", 1)[0].strip("[]") if not (request.host or "").startswith("[") else request.host[1:].split("]")[0]
    except Exception:
        return ""
    return "ext" if (is_remote_ip(host) or host.lower().endswith(".ts.net")) else "int"


def app_title(variant):
    return "MoveEye"          # 2.96.0: MoveEye (before: Motion Watch); one name and one icon for every address (since 2.3.0)


def app_icon_png(size, variant="", icon=None):
    """App icon (home screen, tab). From 2.95.23 one of several (setting «App icon»): the radar eye and its relatives are
    stored as 512 px PNG and scaled; «classic» is the old orange tile with the camera head, drawn here."""
    ic = icon if icon in dict(APP_ICON_LIST) else app_icon_id()
    key = (ic, size)
    if key in _ICONS:
        return _ICONS[key]
    if ic != "classic" and ic in APP_ICONS_PNG:
        import base64
        src = cv2.imdecode(np.frombuffer(base64.b64decode("".join(APP_ICONS_PNG[ic])), np.uint8), cv2.IMREAD_COLOR)
        if src is not None:
            im = cv2.resize(src, (size, size), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".png", im)
            _ICONS[key] = buf.tobytes() if ok else b""
            return _ICONS[key]
    n = 4 * size; k = n / 100.0
    top, bot = np.array((67, 159, 255), np.float32), np.array((12, 89, 232), np.float32)        # #ff9f43 -> #e8590c (BGR)
    g = np.linspace(0, 1, n, dtype=np.float32)[:, None, None]
    img = np.ascontiguousarray(np.repeat((top * (1 - g) + bot * g), n, axis=1).astype(np.uint8))
    W, B, L = (255, 255, 255), (20, 14, 10), (12, 89, 232)
    P = lambda x, y: (int(round((50 + x) * k)), int(round((46 + y) * k)))
    th = max(1, int(round(6 * k)))

    def line(pts):
        cv2.polylines(img, [np.array([P(*q) for q in pts], np.int32)], False, W, th, cv2.LINE_AA)
        for q in (pts[0], pts[-1]):
            cv2.circle(img, P(*q), th // 2, W, -1, cv2.LINE_AA)

    def quad(a, c, e, steps=12):
        return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * e[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * e[1])
                for t in [i / steps for i in range(steps + 1)]]
    line([(-26, -6), (-26, 10)] + quad((-26, 10), (-26, 20), (-16, 20)) + [(16, 20)] + quad((16, 20), (26, 20), (26, 10)) + [(26, -6)])   # fork
    line([(0, 20), (0, 30)]); line([(-14, 32), (14, 32)])                                                                                  # stand
    for r, col in ((19, W), (11, B), (6, L)):
        cv2.circle(img, P(0, 0), int(round(r * k)), col, -1, cv2.LINE_AA)
    cv2.circle(img, P(-3.5, -3.5), int(round(2.6 * k)), W, -1, cv2.LINE_AA)
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".png", img)
    _ICONS[key] = buf.tobytes() if ok else b""
    return _ICONS[key]


_APPLE_ICON_URI = {}


def apple_icon_href(variant=None):
    """3.69.1: the 180 px icon inline as data: URI for «Zum Home-Bildschirm». iOS fetches a linked apple-touch-icon in the
    background and silently refuses MoveEye's own (self-signed) certificate - then it shows a black letter. A few KB only:
    colours in steps of 8 (16 when still over 8 KB), PNG level 9. Cached per icon and host variant (not per request)."""
    v = host_variant() if variant is None else variant
    key = (app_icon_id(), v)
    if key not in _APPLE_ICON_URI:
        import base64
        raw = app_icon_png(180, v)
        out = raw
        im = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR) if raw else None
        if im is not None:
            for q in (8, 16):
                p = ((im.astype(np.int16) // q) * q + q // 2).clip(0, 255).astype(np.uint8)
                ok, buf = cv2.imencode(".png", p, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                if ok:
                    out = buf.tobytes()
                if len(out) <= 8000:
                    break
        _APPLE_ICON_URI[key] = ("data:image/png;base64," + base64.b64encode(out).decode()) if out else "/apple-touch-icon.png"
    return _APPLE_ICON_URI[key]


def apple_icon_link():
    """<link rel="apple-touch-icon"> with the inline icon - for pages that are not built by render_page (guest, games)"""
    return '<link rel="apple-touch-icon" href="' + apple_icon_href() + '">'


def apple_icon_selftest():
    import base64
    u = apple_icon_href("int")
    assert u.startswith("data:image/png;base64,") and apple_icon_href("int") is u, "inline and cached"
    raw = base64.b64decode(u.split(",", 1)[1])
    im = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    assert im is not None and im.shape[:2] == (180, 180) and len(u) < 12000, (len(u), None if im is None else im.shape)
    p = render_page("<html><head></head><body></body></html>", "live")
    assert '<link rel="apple-touch-icon" href="data:image/png;base64,' in p and 'href="/apple-touch-icon.png' not in p, "render_page: inline icon"
    return "180 px, %d bytes inline (data: URI, cached per icon and address)" % len(u)


SELFTEST_EXTRA.append(("Home-screen icon inline for iOS (500, 3.69.1)", apple_icon_selftest))


def app_manifest():
    v = host_variant(); name = app_title(v)
    return json.dumps({"name": name, "short_name": name, "start_url": "/", "scope": "/", "display": "standalone",
                       "background_color": "#e8590c" if app_icon_id() in ("classic", "moveeye") else "#0e1621", "theme_color": "#0b0f14", "lang": CFG["lang"],
                       # the name of the icon in the address: a new icon is a new address, so Android fetches it again
                       "icons": [{"src": "/icon-192.png?i=" + app_icon_id(), "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
                                 {"src": "/icon-512.png?i=" + app_icon_id(), "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]})


