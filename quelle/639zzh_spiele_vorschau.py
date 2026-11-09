#@ MoveEye – Teil 639zzh: Vorschaubilder der Spiele-Kacheln vom Haupt-Server (gleicher Ursprung wie die Seite, auch über https). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 3.69.2: The pictures of the tiles (Kevlaschef, Quantum, FOTAQ …) pointed to the games port, which is plain http
# (games_url). A page opened over https (https://<pi>:5001) then loaded a mixed-content picture - Safari blocks it
# (or upgrades it to https, which the games port does not speak), onerror hides it: tiles without a picture.
# Now only the PICTURE comes from the main server, from the same origin as the page:
#   * /party/thumb/<dir>      admin tab Mehr → Spielecke (login; also the right «games»)
#   * /spiele/thumb/<dir>     /spiele (like /spiele itself: only from the home network)
#   * /p/<key>/thumb/<dir>    the players of the game evening (/p/<key>/, while it is open)
# Only thumb.svg / thumb.png of a game in games.json (or FOTAQ, 639zzg, from DATA_DIR/fotaq), at most 1 MB, exact
# MIME type, «nosniff» and a CSP with «sandbox» (an SVG opened directly runs no script on the MoveEye origin).
# The games themselves stay on the games port (own origin = isolated from MoveEye).
# ----------------------------------------------------------------------------
GAME_THUMBS = {"thumb.svg": "image/svg+xml", "thumb.png": "image/png"}
GAME_THUMB_MAX = 1 << 20
PERM_GET["games"] = tuple(PERM_GET.get("games", ())) + ("/party/thumb/",)


def game_thumb_file(game):
    """(path, mime) of the tile picture of an installed game, or None"""
    x = next((x for x in games_list() if x.get("dir") == game), None)
    ic = str((x or {}).get("icon") or "")
    if ic not in GAME_THUMBS:
        return None
    p_ = games_file(game, ic)
    try:
        if not p_ or os.path.getsize(p_) > GAME_THUMB_MAX:
            return None
    except OSError:
        return None
    return p_, GAME_THUMBS[ic]


def game_thumb_src(game, icon, base):
    """the src of a tile picture on the same origin (base: /party, /spiele or /p/<key>)"""
    return base + "/thumb/" + game if str(icon or "") in GAME_THUMBS else ""


# ---- /spiele: the server-built tiles (340) ------------------------------------------------------------------------------------------
_game_icon_639zzh = _game_icon


# wraps: _game_icon
def _game_icon(x, host=""):                                 # + 639zzh: the picture from /spiele/thumb/<dir> (same origin)
    from html import escape as _e
    src = game_thumb_src(x.get("dir", ""), x.get("icon"), "/spiele")
    if not src:                                             # an emoji as before; another file name: no http:// picture, the symbol
        return _game_icon_639zzh(x if "." not in str(x.get("icon") or "") else dict(x, icon="🎮"), host)
    return f'<img src="{_e(src, quote=True)}" alt="" loading="lazy" onerror="this.style.visibility=\'hidden\'">'


# ---- the JavaScript tiles: game evening (340 PARTY_PAGE) and admin tab (460) ---------------------------------------------------------
PARTY_PAGE = PARTY_PAGE.replace('<img src="${BASE}/g/${g.dir}/${g.icon}"', '<img src="${BASE}/thumb/${g.dir}"', 1)
TOOLS_PAGE = (TOOLS_PAGE.replace('im.src = "/games/" + x.dir + "/" + s_;', 'im.src = "/party/thumb/" + x.dir;', 1)
              .replace('im.src = "/games/fotaq/thumb.svg";', 'im.src = "/party/thumb/fotaq";', 1))


# ---- routes -------------------------------------------------------------------------------------------------------------------------
_smalltv_routes_639zzh = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzh
    _smalltv_routes_639zzh(app, reply, body)
    from flask import Response, request
    import hmac

    def send(game):
        r = game_thumb_file(game)
        h = {"X-Content-Type-Options": "nosniff", "Cache-Control": "max-age=3600",
             "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox"}
        if not r:
            return Response("not found", 404, mimetype="text/plain", headers=h)
        with open(r[0], "rb") as f:
            return Response(f.read(GAME_THUMB_MAX + 1), mimetype=r[1], headers=h)

    @app.route("/party/thumb/<game>")
    def game_thumb_admin(game):
        return send(game)

    @app.route("/spiele/thumb/<game>")
    def game_thumb_spiele(game):
        if not lan_guest_ip(request.remote_addr, request.headers.get("X-Forwarded-For", "") or request.headers.get("Forwarded", "")):
            return Response("not found", 404, mimetype="text/plain")
        return send(game)

    @app.route("/p/<key>/thumb/<game>")
    def game_thumb_party(key, game):
        if not (party_on() and hmac.compare_digest(str(PARTY.get("key") or ""), key)):
            return Response("closed", 404, mimetype="text/plain")
        return send(game)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def gthumb_selftest():
    assert '<img src="${BASE}/thumb/${g.dir}"' in PARTY_PAGE and "/g/${g.dir}/${g.icon}" not in PARTY_PAGE, "game evening: tiles from /p/<key>/thumb/"
    assert 'im.src = "/party/thumb/" + x.dir;' in TOOLS_PAGE and 'im.src = "/party/thumb/fotaq";' in TOOLS_PAGE, "admin tab: tiles from /party/thumb/"
    assert '"/games/" + x.dir + "/" + s_' not in TOOLS_PAGE and "/games/fotaq/thumb.svg" not in TOOLS_PAGE
    assert 'src="/spiele/thumb/qg-orbit"' in _game_icon({"dir": "qg-orbit", "icon": "thumb.svg"}, "pi:5001") and _game_icon({"dir": "x", "icon": "🎲"}) == "🎲"
    assert _game_icon({"dir": "x", "icon": "index.html"}, "pi:5001") == "🎮", "another file: the symbol, never the games port"
    assert game_thumb_src("x", "../../etc/passwd", "/spiele") == "" and game_thumb_src("x", "index.html", "/spiele") == ""
    assert role_allows("custom", "/party/thumb/qg-orbit", "GET", {}, {"games"}) and not role_allows("custom", "/party/thumb/qg-orbit", "GET", {}, set())
    return "tile pictures from the same origin (/party, /spiele, /p/<key>) - no http:// picture on an https page; only thumb.svg / thumb.png"


SELFTEST_EXTRA.append(("Game tiles: pictures from the same origin (639zzh, 3.69.2)", gthumb_selftest))
