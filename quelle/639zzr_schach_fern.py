#@ MoveEye – Teil 639zzr: Schach zu zweit mit je einem Handy (Vermittlung auf dem Pi). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Idee 14 (Besitzer): two phones play one game of chess (games/schach/, mode «Zwei Handys»). The Pi only relays:
#   * one phone creates a game and gets a short code (4 characters, no 0/O, 1/I/L, 2/Z, 5/S, 6/G, 8/B), the second joins
#     with the code (typed or from the QR code: URL + code, never a token); more people with the code watch (read-only)
#   * the Pi keeps only start position + UCI move list per game (plus seats, an open request and the «hints on» note)
#   * every move is checked HERE with the full rules (own small move generator below, no extra package): whose turn, legal
#     move, the right move number; a broken or hostile page cannot spoil the game. Game end (mate, stalemate, threefold
#     repetition, 50 moves, too little material) is computed the same way as chess.js in the game (tests compare both)
#   * each seat has a secret token (only its SHA-256 stays on the Pi); the phone keeps it in localStorage and comes back
#     after sleep / reload with code + token. Transport: long polling (one GET waits up to 15 s for a change), the page
#     falls back to short polling by itself. No WebSocket, no WebRTC, no internet service: Wi-Fi and Tailscale both work.
# Where (same origin as the game page, so no CORS):
#   * games port (own origin, own Wi-Fi only): /schachfern/<op>     - only these addresses, nothing else of MoveEye
#   * main port, logged in with the right «games»: /schachfern/<op> (role_guard, 040)
#   * guests of «Spiele freigeben»: /p/<room key>/schachfern/<op>   (only while the game corner is open)
#   * /spiele (own Wi-Fi, when the games port does not run): /spiele/schachfern/<op>
# Who may create / join: whoever may open the game corner today (no new right). At most SF_GRENZEN["spiele"] games;
# a game ends after 24 h without activity, a finished game is kept 30 minutes (rematch), then removed.
# ----------------------------------------------------------------------------
SF_START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
SF_ABC = "ACDEFHJKMNPQRTUVWXY3479"                  # easy to read, say and type (no 0/O, 1/I/L, 2/Z, 5/S, 6/G, 8/B)
SF_GRENZEN = {"spiele": 10, "frist": 24 * 3600, "nach_ende": 1800, "posts": (12, 10.0), "neu_ip": (8, 600.0),
              "falsch_ip": (15, 300.0), "warten": 15.0, "warter": 40, "online": 25.0, "idle_weg": 600.0}
SF = {"spiele": {}, "cond": threading.Condition(), "ip": {}, "geladen": False, "warter": 0}
SF_DATEI = "schach_fern.json"
SF_OPS_POST = ("neu", "beitreten", "zug", "aktion")
SF_OPS_GET = ("info", "zustand", "qr")
PERM_GET["games"] = tuple(PERM_GET.get("games", ())) + ("/schachfern/",)
PERM_POST["games"] = set(PERM_POST.get("games", ())) | {"/schachfern/" + o for o in SF_OPS_POST}


# ---- rules (0x88 board; mirrors chess.js 1.4 for move generation and draw rules) --------------------------------------------------
_SF_N = (33, 31, 18, 14, -14, -18, -31, -33)
_SF_K = (1, -1, 16, -16, 15, 17, -15, -17)
_SF_B = (15, 17, -15, -17)
_SF_R = (1, -1, 16, -16)


def _sf_sq(name):
    return (int(name[1]) - 1) * 16 + "abcdefgh".index(name[0])


def _sf_name(s):
    return "abcdefgh"[s & 7] + str((s >> 4) + 1)


def sf_fen_lesen(fen):
    """FEN -> position dict {b: [128], w: 'w'/'b', c: castling, ep: square or -1, h: halfmoves, f: fullmove}; ValueError if bad"""
    t = str(fen or "").split()
    if len(t) != 6:
        raise ValueError("fen")
    rows = t[0].split("/")
    if len(rows) != 8:
        raise ValueError("fen rows")
    b = [None] * 128
    for i, row in enumerate(rows):
        r, f = 7 - i, 0
        for ch in row:
            if ch.isdigit():
                f += int(ch)
            elif ch in "pnbrqkPNBRQK":
                if f > 7:
                    raise ValueError("fen row")
                b[r * 16 + f] = ch; f += 1
            else:
                raise ValueError("fen piece")
        if f != 8:
            raise ValueError("fen row")
    if b.count("K") != 1 or b.count("k") != 1 or t[1] not in ("w", "b") or not re.fullmatch(r"-|K?Q?k?q?", t[2]) or not re.fullmatch(r"-|[a-h][36]", t[3]):
        raise ValueError("fen fields")
    return {"b": b, "w": t[1], "c": "" if t[2] == "-" else t[2], "ep": -1 if t[3] == "-" else _sf_sq(t[3]), "h": int(t[4]), "f": max(1, int(t[5]))}


def sf_fen(p):
    rows = []
    for r in range(7, -1, -1):
        s, n = "", 0
        for f in range(8):
            x = p["b"][r * 16 + f]
            if x is None:
                n += 1
            else:
                s += (str(n) if n else "") + x; n = 0
        rows.append(s + (str(n) if n else ""))
    return f"{'/'.join(rows)} {p['w']} {p['c'] or '-'} {_sf_name(p['ep']) if p['ep'] >= 0 else '-'} {p['h']} {p['f']}"


def _sf_weiss(x):
    return x is not None and x.isupper()


def _sf_farbe(x):
    return None if x is None else ("w" if x.isupper() else "b")


def sf_angegriffen(b, s, von):
    """is square s attacked by the side «von» ('w'/'b')?"""
    up = von == "w"
    P, N, B, R, Q, K = ("PNBRQK" if up else "pnbrqk")
    for d in ((-15, -17) if up else (15, 17)):               # a white pawn attacks upwards: it stands below the square
        t = s + d
        if not t & 0x88 and b[t] == P:
            return True
    for d in _SF_N:
        t = s + d
        if not t & 0x88 and b[t] == N:
            return True
    for d in _SF_K:
        t = s + d
        if not t & 0x88 and b[t] == K:
            return True
    for dirs, a in ((_SF_B, (B, Q)), (_SF_R, (R, Q))):
        for d in dirs:
            t = s + d
            while not t & 0x88:
                if b[t] is not None:
                    if b[t] in a:
                        return True
                    break
                t += d
    return False


def _sf_koenig(b, c):
    k = "K" if c == "w" else "k"
    for s in range(128):
        if not s & 0x88 and b[s] == k:
            return s
    return -1


def sf_schach(p):
    return sf_angegriffen(p["b"], _sf_koenig(p["b"], p["w"]), "b" if p["w"] == "w" else "w")


def _sf_pseudo(p):
    b, c = p["b"], p["w"]
    them = "b" if c == "w" else "w"
    out = []
    for s in range(128):
        if s & 0x88 or b[s] is None or _sf_farbe(b[s]) != c:
            continue
        x = b[s].lower()
        if x == "p":
            fw, start, last = (16, 1, 7) if c == "w" else (-16, 6, 0)
            t = s + fw
            if not t & 0x88 and b[t] is None:
                if t >> 4 == last:
                    out += [(s, t, q) for q in "qrbn"]
                else:
                    out.append((s, t, ""))
                    t2 = t + fw
                    if s >> 4 == start and b[t2] is None:
                        out.append((s, t2, ""))
            for d in (fw - 1, fw + 1):
                t = s + d
                if t & 0x88:
                    continue
                if b[t] is not None and _sf_farbe(b[t]) == them:
                    out += [(s, t, q) for q in "qrbn"] if t >> 4 == last else [(s, t, "")]
                elif t == p["ep"]:
                    out.append((s, t, ""))
        elif x in "nk":
            for d in (_SF_N if x == "n" else _SF_K):
                t = s + d
                if not t & 0x88 and (b[t] is None or _sf_farbe(b[t]) == them):
                    out.append((s, t, ""))
        else:
            for d in ((_SF_B if x == "b" else _SF_R if x == "r" else _SF_K)):
                t = s + d
                while not t & 0x88:
                    if b[t] is None:
                        out.append((s, t, ""))
                    else:
                        if _sf_farbe(b[t]) == them:
                            out.append((s, t, ""))
                        break
                    t += d
    # castling (king and rook in place, empty between, king not in check and not passing an attacked square)
    ks, rank = (4, 0) if c == "w" else (116, 112)
    if b[ks] == ("K" if c == "w" else "k") and not sf_angegriffen(b, ks, them):
        R = "R" if c == "w" else "r"
        if ("K" if c == "w" else "k") in p["c"] and b[rank + 7] == R and b[ks + 1] is None and b[ks + 2] is None \
                and not sf_angegriffen(b, ks + 1, them) and not sf_angegriffen(b, ks + 2, them):
            out.append((ks, ks + 2, ""))
        if ("Q" if c == "w" else "q") in p["c"] and b[rank] == R and b[ks - 1] is None and b[ks - 2] is None and b[ks - 3] is None \
                and not sf_angegriffen(b, ks - 1, them) and not sf_angegriffen(b, ks - 2, them):
            out.append((ks, ks - 2, ""))
    return out


def sf_ziehe(p, m):
    """the position after move m = (from, to, promotion) - no legality check (see sf_legal)"""
    s, t, q = m
    b = p["b"][:]; c = p["w"]; x = b[s]; them = "b" if c == "w" else "w"
    cap = b[t] is not None
    rights = p["c"]
    if x.lower() == "p" and t == p["ep"] and not cap:            # en passant: the pawn beside goes
        b[t - 16 if c == "w" else t + 16] = None; cap = True
    b[t] = (q.upper() if c == "w" else q) if q else x; b[s] = None
    if x.lower() == "k":
        rights = rights.replace("K", "").replace("Q", "") if c == "w" else rights.replace("k", "").replace("q", "")
        if t - s == 2:
            b[s + 1] = b[s + 3]; b[s + 3] = None
        elif s - t == 2:
            b[s - 1] = b[s - 4]; b[s - 4] = None
    for sq, r in ((0, "Q"), (7, "K"), (112, "q"), (119, "k")):  # a rook moved away or was taken
        if s == sq or t == sq:
            rights = rights.replace(r, "")
    ep = -1
    if x.lower() == "p" and abs(t - s) == 32:                   # like chess.js: only when a pawn of the other side stands beside
        P = "p" if c == "w" else "P"
        if (not (t - 1) & 0x88 and b[t - 1] == P) or (not (t + 1) & 0x88 and b[t + 1] == P):
            ep = (s + t) // 2
    return {"b": b, "w": them, "c": rights, "ep": ep, "h": 0 if (x.lower() == "p" or cap) else p["h"] + 1,
            "f": p["f"] + (1 if c == "b" else 0)}


def sf_legal(p):
    """all legal moves as (from, to, promotion)"""
    c = p["w"]; them = "b" if c == "w" else "w"; out = []
    for m in _sf_pseudo(p):
        n = sf_ziehe(p, m)
        if not sf_angegriffen(n["b"], _sf_koenig(n["b"], c), them):
            out.append(m)
    return out


def sf_uci(m):
    return _sf_name(m[0]) + _sf_name(m[1]) + m[2]


def sf_schluessel(p):
    """key for the threefold repetition (board, side, castling, en passant square as chess.js counts it)"""
    return "".join(x or "." for i, x in enumerate(p["b"]) if not i & 0x88) + p["w"] + p["c"] + str(p["ep"])


def sf_material_fehlt(p):
    """too little material (exactly the rule of chess.js isInsufficientMaterial)"""
    n, cnt, farben = 0, {}, []
    for s in range(128):
        if s & 0x88 or p["b"][s] is None:
            continue
        x = p["b"][s].lower(); n += 1; cnt[x] = cnt.get(x, 0) + 1
        if x == "b":
            farben.append(((s >> 4) + (s & 7)) % 2)
    if n == 2:
        return True
    if n == 3 and (cnt.get("b") == 1 or cnt.get("n") == 1):
        return True
    if n == cnt.get("b", 0) + 2 and (sum(farben) == 0 or sum(farben) == len(farben)):
        return True
    return False


def sf_partie(start, zuege):
    """replay a game: (position, repetition counter, legal moves now); ValueError at the first move that is not allowed"""
    p = sf_fen_lesen(start)
    keys = {sf_schluessel(p): 1}
    leg = sf_legal(p)
    for u in zuege:
        m = next((m for m in leg if sf_uci(m) == u), None)
        if m is None:
            raise ValueError("illegal " + str(u)[:8])
        p = sf_ziehe(p, m)
        k = sf_schluessel(p); keys[k] = keys.get(k, 0) + 1
        leg = sf_legal(p)
    return p, keys, leg


def sf_ende_regeln(p, keys, leg):
    """end by the rules, in the order of partie.js: mate, stalemate, material, repetition, 50 moves"""
    if not leg:
        return {"art": "matt", "sieger": "b" if p["w"] == "w" else "w"} if sf_schach(p) else {"art": "patt", "sieger": None}
    if sf_material_fehlt(p):
        return {"art": "material", "sieger": None}
    if keys.get(sf_schluessel(p), 0) >= 3:
        return {"art": "wiederholung", "sieger": None}
    if p["h"] >= 100:
        return {"art": "50zuege", "sieger": None}
    return None


def sf_perft(p, d):
    if d == 0:
        return 1
    return sum(sf_perft(sf_ziehe(p, m), d - 1) for m in sf_legal(p)) if d > 1 else len(sf_legal(p))


# ---- the games (memory + small file; tokens only as SHA-256) ------------------------------------------------------------------------
def _sf_hash(t):
    return hashlib.sha256(str(t).encode()).hexdigest()


def _sf_datei():
    return os.path.join(DATA_DIR, SF_DATEI)


def _sf_speichern():
    try:
        keep = ("code", "nr", "erstellt", "t", "startFen", "zuege", "ende", "sitze", "anfrage", "hilfe", "t_ende")
        d = {"v": 1, "spiele": {k: {x: G[x] for x in keep if x in G} for k, G in SF["spiele"].items()}}
        tmp = _sf_datei() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, _sf_datei())
    except (OSError, TypeError, ValueError):
        pass


def _sf_laden():
    if SF["geladen"]:
        return
    SF["geladen"] = True
    try:
        with open(_sf_datei(), encoding="utf-8") as f:
            d = json.load(f)
        for k, G in (d.get("spiele") or {}).items():
            if not (isinstance(G, dict) and re.fullmatch("[%s]{4}" % SF_ABC, str(k))):
                continue
            G["code"] = k
            G["seq"] = secrets.randbelow(10 ** 9)
            G["posts"] = {"w": [], "b": []}; G["zs"] = {}
            if _sf_neu_rechnen(G):
                SF["spiele"][k] = G
    except (OSError, ValueError, TypeError, AttributeError):
        pass


def _sf_neu_rechnen(G):
    """position, repetitions and legal moves from start + moves (False: the stored game is broken)"""
    try:
        G["_p"], G["_k"], G["_l"] = sf_partie(G.get("startFen") or SF_START, list(G.get("zuege") or []))
        return True
    except (ValueError, TypeError, KeyError, IndexError):
        return False


def _sf_bump(G, speichern=True):
    G["seq"] = (G.get("seq", 0) + 1) % 10 ** 9
    G["t"] = time.time()
    if speichern:
        _sf_speichern()
    SF["cond"].notify_all()


def _sf_aufraeumen(now=None):
    """remove games idle for 24 h, finished games after 30 minutes"""
    now = now or time.time(); weg = []
    for k, G in SF["spiele"].items():
        if now - G.get("t", 0) > SF_GRENZEN["frist"] or (G.get("ende") and now - G.get("t_ende", now) > SF_GRENZEN["nach_ende"]):
            weg.append(k)
    for k in weg:
        SF["spiele"].pop(k, None)
    if weg:
        _sf_speichern(); SF["cond"].notify_all()
    return weg


def _sf_grenze(liste, n, s, now):
    liste[:] = [x for x in liste if now - x < s]
    if len(liste) >= n:
        return False
    liste.append(now)
    return True


def _sf_ip_ok(ip, art, now, zaehlen=True):
    n, s = SF_GRENZEN[art]
    L = SF["ip"].setdefault(art + "|" + str(ip), [])
    L[:] = [x for x in L if now - x < s]
    if len(L) >= n:
        return False
    if zaehlen:
        L.append(now)
    if len(SF["ip"]) > 2000:
        SF["ip"] = {k: v for k, v in SF["ip"].items() if v and now - v[-1] < 900}
    return True


def _sf_sitz(G, token):
    """'w' / 'b' for a valid token, '' for none, None for a wrong one"""
    if not token:
        return ""
    h = _sf_hash(token)
    import hmac
    for c in ("w", "b"):
        if G["sitze"][c].get("h") and hmac.compare_digest(G["sitze"][c]["h"], h):
            return c
    return None


def _sf_status(G):
    return "ende" if G.get("ende") else "laeuft" if G["sitze"]["w"].get("h") and G["sitze"]["b"].get("h") else "warte"


def sf_sicht(G, sitz, now=None):
    """what one phone (or a spectator) sees - never a token"""
    now = now or time.time()
    p = G["_p"]
    G["zs"] = {k: v for k, v in G.get("zs", {}).items() if now - v < SF_GRENZEN["online"]}
    return {"ok": True, "code": G["code"], "nr": G["nr"], "seq": G["seq"], "startFen": G["startFen"], "zuege": list(G["zuege"]),
            "fen": sf_fen(p), "amZug": p["w"], "ende": G.get("ende"), "sitz": sitz or "zuschauer", "status": _sf_status(G),
            "sitze": {c: {"da": bool(G["sitze"][c].get("h")), "online": bool(G["sitze"][c].get("h")) and now - G["sitze"][c].get("t", 0) < SF_GRENZEN["online"]}
                      for c in ("w", "b")},
            "anfrage": G.get("anfrage"), "hilfe": G.get("hilfe"), "zuschauer": len(G["zs"])}


def _sf_neues_spiel(farbe, now):
    while True:
        code = "".join(secrets.choice(SF_ABC) for _ in range(4))
        if code not in SF["spiele"]:
            break
    if farbe not in ("w", "b"):
        farbe = secrets.choice("wb")
    tok = secrets.token_urlsafe(18)
    G = {"code": code, "nr": 1, "erstellt": now, "t": now, "startFen": SF_START, "zuege": [], "ende": None,
         "sitze": {"w": {}, "b": {}}, "anfrage": None, "hilfe": {"w": {}, "b": {}}, "seq": secrets.randbelow(10 ** 9),
         "posts": {"w": [], "b": []}, "zs": {}}
    G["sitze"][farbe] = {"h": _sf_hash(tok), "t": now}
    _sf_neu_rechnen(G)
    return G, tok, farbe


def _sf_platz_machen(now):
    """room for one more game: finished games first, then the longest idle one (at least 10 minutes idle)"""
    if len(SF["spiele"]) < SF_GRENZEN["spiele"]:
        return True
    ende = sorted((G["t"], k) for k, G in SF["spiele"].items() if G.get("ende"))
    idle = sorted((G["t"], k) for k, G in SF["spiele"].items() if now - G["t"] > SF_GRENZEN["idle_weg"])
    for _t, k in ende + idle:
        SF["spiele"].pop(k, None)
        if len(SF["spiele"]) < SF_GRENZEN["spiele"]:
            return True
    return False


def _sf_zurueck(G, von):
    """take back so that «von» is to move again (its own last move, and the reply after it)"""
    n = len(G["zuege"]); p = G["_p"]
    k = 1 if p["w"] != von else 2
    if n < k:
        return False
    G["zuege"] = G["zuege"][:n - k]
    _sf_neu_rechnen(G)
    return True


def _sf_eigene_zuege(G, c):
    start_w = G["startFen"].split()[1] == "w"
    return sum(1 for i in range(len(G["zuege"])) if ("w" if (i % 2 == 0) == start_w else "b") == c)


def _sf_ausfuehren(G, art, von, now):
    """an accepted request"""
    if art == "remis":
        G["ende"] = {"art": "einigung", "sieger": None}; G["t_ende"] = now
    elif art == "zurueck":
        _sf_zurueck(G, von)
    elif art == "revanche":                                      # new game, same code, colours swapped
        G["sitze"] = {"w": G["sitze"]["b"], "b": G["sitze"]["w"]}
        G["hilfe"] = {"w": dict(G["hilfe"].get("b") or {}, tipps=0), "b": dict(G["hilfe"].get("w") or {}, tipps=0)}
        G["nr"] += 1; G["zuege"] = []; G["ende"] = None; G.pop("t_ende", None); G["startFen"] = SF_START
        _sf_neu_rechnen(G)
    G["anfrage"] = None


def sf_api(op, method, args, d, ip="?", warten=True):
    """the relay: (HTTP status, dict) or (status, (bytes, mime)). Same for every address (games port, main port, guests)."""
    now = time.time()
    args = args or {}; d = d if isinstance(d, dict) else {}
    if (method == "POST") != (op in SF_OPS_POST) or op not in SF_OPS_POST + SF_OPS_GET:
        return 404, {"ok": False, "fehler": "unbekannt"}
    src = d if method == "POST" else args
    code = re.sub(r"[^A-Z0-9]", "", str(src.get("code") or "").upper())[:8]
    token = str(src.get("token") or "")[:64]
    with SF["cond"]:
        _sf_laden(); _sf_aufraeumen(now)
        if op == "info":
            return 200, {"ok": True, "offen": len(SF["spiele"]), "max": SF_GRENZEN["spiele"]}
        if op == "neu":
            if not _sf_ip_ok(ip, "neu_ip", now):
                return 429, {"ok": False, "fehler": "zu_oft"}
            if not _sf_platz_machen(now):
                return 429, {"ok": False, "fehler": "voll"}
            G, tok, farbe = _sf_neues_spiel(str(d.get("farbe") or ""), now)
            SF["spiele"][G["code"]] = G
            _sf_bump(G)
            return 200, dict(sf_sicht(G, farbe, now), token=tok)
        if not _sf_ip_ok(ip, "falsch_ip", now, zaehlen=False):     # guessing codes: after too many wrong ones this address waits
            return 429, {"ok": False, "fehler": "zu_oft"}
        G = SF["spiele"].get(code)
        if G is None:
            _sf_ip_ok(ip, "falsch_ip", now)
            return 404, {"ok": False, "fehler": "weg"}
        sitz = _sf_sitz(G, token)
        if sitz is None:
            _sf_ip_ok(ip, "falsch_ip", now)
            return 403, {"ok": False, "fehler": "token"}
        if op == "qr":
            u = str(args.get("u") or "")
            from urllib.parse import urlsplit
            try:
                x = urlsplit(u)
            except ValueError:
                x = None
            if not (x and x.scheme in ("http", "https") and x.netloc and "@" not in x.netloc and not x.query and not x.fragment and len(u) < 300
                    and re.fullmatch(r"(/p/[A-Za-z0-9_\-]{1,64}|/spiele)?/(g|games)/schach/(index\.html)?", x.path)):
                return 400, {"ok": False, "fehler": "adresse"}
            return 200, (qr_svg(sf_qr_text(u, G["code"])).encode("utf-8"), "image/svg+xml")
        if op == "beitreten":
            if not sitz:
                frei = [c for c in ("w", "b") if not G["sitze"][c].get("h")]
                if frei and not G.get("ende"):
                    tok = secrets.token_urlsafe(18)
                    G["sitze"][frei[0]] = {"h": _sf_hash(tok), "t": now}
                    _sf_bump(G)
                    return 200, dict(sf_sicht(G, frei[0], now), token=tok)
                G.setdefault("zs", {})[_sf_hash(ip)[:12]] = now
                return 200, dict(sf_sicht(G, "", now), token="")
            G["sitze"][sitz]["t"] = now
            return 200, dict(sf_sicht(G, sitz, now), token=token)
        if op == "zustand":
            if sitz:
                G["sitze"][sitz]["t"] = now
            else:
                G.setdefault("zs", {})[_sf_hash(ip)[:12]] = now
            try:
                seq = int(args.get("seq", -1))
            except (TypeError, ValueError):
                seq = -1
            if warten and str(args.get("warte") or "") == "1" and seq == G["seq"] and SF["warter"] < SF_GRENZEN["warter"]:
                end = now + SF_GRENZEN["warten"]; SF["warter"] += 1
                try:
                    while G["seq"] == seq and time.time() < end and SF["spiele"].get(code) is G:
                        SF["cond"].wait(min(1.0, end - time.time()))
                finally:
                    SF["warter"] -= 1
                if SF["spiele"].get(code) is not G:
                    return 404, {"ok": False, "fehler": "weg"}
                sitz = _sf_sitz(G, token) or ""                        # a rematch while waiting swaps the colours
                if sitz:
                    G["sitze"][sitz]["t"] = time.time()
            return 200, sf_sicht(G, sitz)
        # ---- moves and actions: only a seat ----
        if not sitz:
            return 403, {"ok": False, "fehler": "zuschauer"}
        G["sitze"][sitz]["t"] = now
        n_, s_ = SF_GRENZEN["posts"]
        if not _sf_grenze(G.setdefault("posts", {}).setdefault(sitz, []), n_, s_, now):
            return 429, {"ok": False, "fehler": "zu_oft", "v": sf_sicht(G, sitz, now)}
        if op == "zug":
            uci = str(d.get("uci") or "")
            try:
                n = int(d.get("n", -1))
            except (TypeError, ValueError):
                n = -1
            if n == len(G["zuege"]) - 1 and n >= 0 and G["zuege"][n] == uci and G["_p"]["w"] != sitz:
                return 200, sf_sicht(G, sitz, now)                       # the same move again (answer lost on the way): fine
            fehler = ("ende" if G.get("ende") else "warte" if _sf_status(G) != "laeuft" else "nicht_dran" if G["_p"]["w"] != sitz
                      else "nicht_synchron" if n != len(G["zuege"]) else "")
            if not fehler:
                m = next((m for m in G["_l"] if sf_uci(m) == uci), None) if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", uci) else None
                if m is None:
                    fehler = "illegal"
            if fehler:
                return 409, {"ok": False, "fehler": fehler, "v": sf_sicht(G, sitz, now)}
            G["_p"] = sf_ziehe(G["_p"], m); G["zuege"].append(uci)
            k = sf_schluessel(G["_p"]); G["_k"][k] = G["_k"].get(k, 0) + 1
            G["_l"] = sf_legal(G["_p"])
            G["anfrage"] = None                                          # a move answers an open offer with «no»
            e = sf_ende_regeln(G["_p"], G["_k"], G["_l"])
            if e:
                G["ende"] = e; G["t_ende"] = now
            _sf_bump(G)
            return 200, sf_sicht(G, sitz, now)
        art = str(d.get("art") or "")
        ander = "b" if sitz == "w" else "w"
        A = G.get("anfrage")
        fehler = ""
        if art == "hilfe":                                            # «hints on» note for both (fairness)
            h = G["hilfe"].setdefault(sitz, {})
            for k_ in ("lern", "balken"):
                if isinstance(d.get(k_), bool):
                    h[k_] = d[k_]
            if d.get("tipp") is True:
                h["tipps"] = min(999, int(h.get("tipps") or 0) + 1)
        elif art == "aufgeben":
            if G.get("ende") or _sf_status(G) != "laeuft":
                fehler = "ende" if G.get("ende") else "warte"
            else:
                G["ende"] = {"art": "aufgabe", "sieger": ander}; G["t_ende"] = now; G["anfrage"] = None
        elif art == "abbrechen":                                      # the waiting game (nobody joined yet) goes away
            if G["sitze"][ander].get("h"):
                fehler = "laeuft"
            else:
                SF["spiele"].pop(code, None); _sf_speichern(); SF["cond"].notify_all()
                return 200, {"ok": True, "weg": True}
        elif art in ("remis", "zurueck", "revanche"):
            ok_ = (not G.get("ende") and _sf_status(G) == "laeuft") if art != "revanche" else bool(G.get("ende")) and G["sitze"][ander].get("h")
            if art == "zurueck" and ok_:
                ok_ = _sf_eigene_zuege(G, sitz) > 0
            if not ok_:
                fehler = "geht_nicht"
            elif A and A.get("von") == ander and A.get("art") == art:  # both want the same: done
                _sf_ausfuehren(G, art, ander, now)
            elif A and A.get("von") == ander:
                fehler = "offen"
            else:
                G["anfrage"] = {"art": art, "von": sitz, "nr": len(G["zuege"])}
        elif art == "annehmen":
            if not A or A.get("von") != ander or (A["art"] != "revanche" and (G.get("ende") or A.get("nr") != len(G["zuege"]))):
                fehler = "keine"
            else:
                _sf_ausfuehren(G, A["art"], ander, now)
        elif art in ("ablehnen", "zurueckziehen"):
            if A and A.get("von") == (ander if art == "ablehnen" else sitz):
                G["anfrage"] = None
        else:
            return 400, {"ok": False, "fehler": "unbekannt"}
        if fehler:
            return 409, {"ok": False, "fehler": fehler, "v": sf_sicht(G, sitz, now)}
        _sf_bump(G)
        return 200, sf_sicht(G, _sf_sitz(G, token) or "", now)          # after a rematch the seat has the other colour


def sf_qr_text(u, code):
    """the text of the QR code: the address of the game page + the game code - never a token or password"""
    return u + "?fern=" + code


def sf_ip(remote, fwd=""):
    ip = remote or "?"
    if ip in ("127.0.0.1", "::1") and fwd:
        ip = fwd.split(",")[0].strip()[:45] or ip
    return ip


# ---- games port (own origin, own Wi-Fi): /schachfern/<op> - only these addresses (340: GAMESRV_API) ------------------------------
def sf_spieleport(h, method, path):
    from urllib.parse import urlsplit, parse_qs
    op = path[len("/schachfern/"):]
    hdr = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    if method == "POST":
        o = h.headers.get("Origin")                                  # a page of another web site may not post here
        if o is not None:
            try:
                ok_ = urlsplit(o).netloc.lower() == (h.headers.get("Host") or "").lower()
            except ValueError:
                ok_ = False
            if not ok_:
                return _sf_antwort(h, 403, {"ok": False, "fehler": "fremd"}, hdr)
        try:
            n = int(h.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if not 0 <= n <= 4096:
            return _sf_antwort(h, 413, {"ok": False, "fehler": "gross"}, hdr)
        try:
            d = json.loads(h.rfile.read(n) or b"{}")
        except ValueError:
            d = {}
        args = {}
    else:
        d = {}
        args = {k: v[0] for k, v in parse_qs(urlsplit(h.path).query).items()}
    try:
        st, out = sf_api(op, method, args, d, h.client_address[0])
    except Exception as e:                                           # never a broken connection for the phone
        log_event("web", f"Schach (zwei Handys): {e.__class__.__name__}")
        st, out = 500, {"ok": False, "fehler": "fehler"}
    return _sf_antwort(h, st, out, hdr)


def _sf_antwort(h, st, out, hdr):
    if isinstance(out, tuple):
        data, ct = out
        hdr = dict(hdr, **{"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox"})
    else:
        data, ct = json.dumps(out).encode("utf-8"), "application/json"
    try:
        h.send_response(st)
        h.send_header("Content-Type", ct + ("; charset=utf-8" if ct == "application/json" else ""))
        for k, v in hdr.items():
            h.send_header(k, v)
        h.send_header("Content-Length", str(len(data)))
        h.end_headers(); h.wfile.write(data)
    except (BrokenPipeError, ConnectionResetError):
        pass


GAMESRV_API["/schachfern/"] = sf_spieleport


# ---- main port: logged in (right «games»), guests of «Spiele freigeben», /spiele (own Wi-Fi) ---------------------------------------
_smalltv_routes_639zzr = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzr
    _smalltv_routes_639zzr(app, reply, body)
    from flask import Response, request
    import hmac

    def run(op):
        d = (request.get_json(force=True, silent=True) or {}) if request.method == "POST" else {}
        if request.method == "POST" and (request.content_length or 0) > 4096:
            return Response(json.dumps({"ok": False, "fehler": "gross"}), 413, mimetype="application/json")
        st, out = sf_api(op, request.method, request.args.to_dict(), d, sf_ip(request.remote_addr, request.headers.get("X-Forwarded-For", "")))
        if isinstance(out, tuple):
            return Response(out[0], st, mimetype=out[1], headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
                                                                  "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox"})
        return Response(json.dumps(out), st, mimetype="application/json", headers={"Cache-Control": "no-store"})

    zu = lambda: Response(json.dumps({"ok": False, "fehler": "zu"}), 404, mimetype="application/json", headers={"Cache-Control": "no-store"})

    @app.route("/schachfern/<op>", methods=["GET", "POST"])
    def schachfern_login(op):                     # login + right «games» (auth / role_guard, 550)
        return run(op)

    @app.route("/p/<key>/schachfern/<op>", methods=["GET", "POST"])
    def schachfern_gast(key, op):                 # guests: only while «Spiele freigeben» is on, with the room key
        if not (party_on() and hmac.compare_digest(str(PARTY.get("key") or ""), key)):
            return zu()
        return run(op)

    @app.route("/spiele/schachfern/<op>", methods=["GET", "POST"])
    def schachfern_spiele(op):                    # like /spiele: only from the own Wi-Fi
        if not lan_guest_ip(request.remote_addr, request.headers.get("X-Forwarded-For", "") or request.headers.get("Forwarded", "")):
            return zu()
        return run(op)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def sf_selftest():
    p = sf_fen_lesen(SF_START)
    assert sf_fen(p) == SF_START and sf_perft(p, 2) == 400, "rules: start position"
    kiwi = sf_fen_lesen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
    assert len(sf_legal(kiwi)) == 48 and sf_perft(kiwi, 2) == 2039, "rules: castling, en passant, promotion (Kiwipete)"
    pp, kk, ll = sf_partie(SF_START, ["f2f3", "e7e5", "g2g4", "d8h4"])
    assert sf_ende_regeln(pp, kk, ll) == {"art": "matt", "sieger": "b"}, "rules: fool's mate"
    try:
        sf_partie(SF_START, ["e2e5"]); assert False, "illegal move accepted"
    except ValueError:
        pass
    assert sf_material_fehlt(sf_fen_lesen("8/8/8/8/8/8/5k2/4KB2 w - - 0 1")) and not sf_material_fehlt(sf_fen_lesen("8/8/8/8/8/8/5k2/4KR2 w - - 0 1"))
    assert "/schachfern/zug" in PERM_POST["games"] and role_allows("kid", "/schachfern/zustand", "GET", {}) and role_allows("kid", "/schachfern/zug", "POST", {})
    assert not role_allows("custom", "/schachfern/zug", "POST", {}, set()) and not role_allows("custom", "/schachfern/zustand", "GET", {}, set())
    assert sf_qr_text("http://pi:5003/g/schach/", "ACDE") == "http://pi:5003/g/schach/?fern=ACDE" and GAMESRV_API.get("/schachfern/") is sf_spieleport
    return "chess for two phones: rules (perft start 400, Kiwipete 2039, mate), rights «games», games port address only /schachfern/"


SELFTEST_EXTRA.append(("Chess for two phones: relay and rules (639zzr)", sf_selftest))
