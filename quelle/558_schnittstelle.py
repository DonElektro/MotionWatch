#@ MoveEye – Teil 558: eine Feldliste MoveEye ↔ 3D-Simulator (simulator3d/schnittstelle.json) und ihre Prüfung im Selbsttest (Aufräumen 2, Daniel 30.10.2026). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Die Liste simulator3d/schnittstelle.json nennt jedes Feld, das die beiden austauschen: die Antwort des Simulators auf
# /state («world_reply», main.gd + power.gd + net.gd), den Zustand von MoveEye («state», sim_state 290 + Hüllen), /info
# und die /control-Aktionen, die MoveEye braucht. Der Selbsttest meldet:
#   * ein Feld wird gesendet, steht aber nicht in der Liste (oder umgekehrt),
#   * ein Feld wird gesendet, aber die andere Seite liest es nie (unbenutzt),
#   * MoveEye liest ein Feld der Antwort, das der Simulator gar nicht sendet,
#   * MoveEye schickt eine /control-Aktion, die der Simulator nicht kennt.
# Ein neues Feld: eine Zeile in schnittstelle.json (ein Ort). Holt main.gd world_reply ein weiteres Teil-Wörterbuch
# (r.merge(x.reply())), dann hier in IFACE_GD_REPLY eintragen. Der Simulator prüft dieselbe Liste beim Start
# (scripts/schnittstelle.gd, Zeile «Schnittstelle: …» im Log).
# ----------------------------------------------------------------------------
IFACE_GD_REPLY = [("main.gd", "world_reply"), ("power.gd", "reply")]     # (file, function) whose dict keys are the answer


def _gd_func(text, name):
    m = re.search(r"\nfunc " + re.escape(name) + r"\(.*?(?=\nfunc |\Z)", text, re.S)
    return m.group(0) if m else ""


def _gd_top_keys(body, var="r|d|rep"):
    """the keys of the dictionary literals right after «var x := {» or «return {» (depth 1 only) plus «r["k"] = …»"""
    keys, stack, i, n = [], [], 0, len(body)
    while i < n:
        c = body[i]
        if c == "#":
            j = body.find("\n", i)
            i = n if j < 0 else j
            continue
        if c in "\"'":
            j = i + 1
            while j < n and body[j] != c:
                j += 2 if body[j] == "\\" else 1
            s, k = body[i + 1:j], j + 1
            while k < n and body[k] in " \t":
                k += 1
            if stack == ["{v"] and k < n and body[k] == ":" and re.fullmatch(r"\w+", s):
                keys.append(s)
            i = j + 1
            continue
        if c in "{[(":
            stack.append("{v" if c == "{" and re.search(r"(var \w+\s*:?=|return)\s*$", body[max(0, i - 60):i]) else c)
        elif c in "}])" and stack:
            stack.pop()
        i += 1
    keys += re.findall(r"\b(?:" + var + r')\["(\w+)"\]\s*=', body)
    return list(dict.fromkeys(keys))


def iface_list(base=None):
    base = base or os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(base, "simulator3d", "schnittstelle.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def iface_check(base=None):
    """(problems, counts) - compares simulator3d/schnittstelle.json with the sources of both sides; None without the folder"""
    import inspect
    base = base or os.path.dirname(os.path.abspath(__file__))
    L = iface_list(base)
    gdir = os.path.join(base, "simulator3d", "scripts")
    if L is None or not os.path.isdir(gdir):
        return None
    gd = {}
    for fn in os.listdir(gdir):
        if fn.endswith(".gd"):
            with open(os.path.join(gdir, fn), encoding="utf-8") as f:
                gd[fn] = f.read()
    own = zd_source()                                       # with the literals of the data zip (012)
    meta = L.get("_meta") or {}
    pyonly = set(L.get("_nur_python_simulator") or [])
    cond = set(L.get("_bedingt") or [])
    probs = []

    def cmp(sect, sent, where):
        lst = set((L.get(sect) or {}).keys())
        for k in sorted(set(sent) - lst):
            probs.append(f"{sect}: «{k}» is sent ({where}) but not in schnittstelle.json")
        for k in sorted(lst - set(sent) - cond):
            probs.append(f"{sect}: «{k}» is in schnittstelle.json but not sent ({where})")
        return lst

    # 1. the answer of the simulator (world_reply) - sent by the GDScript sources, read by MoveEye (350, 285, 552 …)
    wr = []
    for fn, func in IFACE_GD_REPLY:
        wr += _gd_top_keys(_gd_func(gd.get(fn, ""), func))
    wr += re.findall(r'\brep\["(\w+)"\]\s*=', _gd_func(gd.get("net.gd", ""), "_handle"))
    wl = cmp("world_reply", wr, "main.gd world_reply / power.gd reply / net.gd")
    rd = inspect.getsource(SimLink.tick)
    for nm, fn_ in list(globals().items()):
        if re.fullmatch(r"_?simvals_take(_\w+)?", nm) and callable(fn_):
            try:
                rd += inspect.getsource(fn_)
            except (OSError, TypeError):
                pass
    lits = set(re.findall(r'"(\w+)"', rd))
    for k in sorted(wl - set(meta.get("world_reply") or []) - lits):
        probs.append(f"world_reply: «{k}» is sent by the simulator but MoveEye never reads it (350 SimLink.tick / simvals_take)")
    reads = set(re.findall(r'\brep_?\.get\("(\w+)"', rd)) | set(re.findall(r'\brep_?\["(\w+)"\]', rd))
    for k in sorted(reads - wl - set(L.get("_optional_reply") or [])):
        probs.append(f"world_reply: MoveEye reads «{k}» but the simulator does not send it")
    # 2. the state of MoveEye (sim_state, part 290 + wrappers) - read by the GDScript sources
    st = list(sim_state().keys())
    sl = cmp("state", st, "sim_state")
    allgd = "\n".join(gd.values())
    gread = set(re.findall(r'(?:get|has)\("(\w+)"', allgd)) | set(re.findall(r'\["(\w+)"\]', allgd))
    for k in sorted(sl - set(meta.get("state") or []) - pyonly - gread):
        probs.append(f"state: «{k}» is sent by MoveEye but the 3D simulator never reads it")
    # 3. /info
    il = cmp("info", _gd_top_keys(_gd_func(gd.get("main.gd", ""), "info")), "main.gd info")
    for k in sorted(il - set(meta.get("info") or [])):
        if f'.get("{k}"' not in own and f'["{k}"]' not in own:
            probs.append(f"info: «{k}» is sent by the simulator but MoveEye never reads it")
    # 4. /control actions MoveEye sends: in the list and known by the simulator (main.gd _control)
    used = set(re.findall(r'sim_control\(\{"action":\s*"(\w+)"', own)) | set(re.findall(r'\bq_?\s*=\s*\{"action":\s*"(\w+)"', own))
    cb = _gd_func(gd.get("main.gd", ""), "_control")
    known = set(re.findall(r'\ba == "(\w+)"', cb))
    for g in re.findall(r"\ba in \[([^\]]*)\]", cb):
        known |= set(re.findall(r'"(\w+)"', g))
    cl = set((L.get("control") or {}).keys())
    for k in sorted(used - known):
        probs.append(f"control: MoveEye sends the action «{k}» but the simulator does not know it (main.gd _control)")
    for k in sorted(used - cl):
        probs.append(f"control: the action «{k}» is used by MoveEye but not in schnittstelle.json")
    for k in sorted(cl - used):
        probs.append(f"control: «{k}» is in schnittstelle.json but MoveEye does not use it")
    return probs, {"world_reply": len(wl), "state": len(sl), "info": len(il), "control": len(cl)}


def iface_selftest():
    r = iface_check()
    if r is None:
        return "simulator folder not here"
    probs, n = r
    assert not probs, f"{len(probs)} problems: " + " | ".join(probs[:12])
    return f"{n['world_reply']} answer fields, {n['state']} state fields, {n['info']} info fields, {n['control']} actions - same on both sides"


SELFTEST_EXTRA.append(("One field list MoveEye ↔ simulator (simulator3d/schnittstelle.json)", iface_selftest))


_sim_status_340 = sim_status


# wraps: sim_status
def sim_status():                                         # + 558: who steers the simulator (world_reply «leader»)
    r = _sim_status_340()
    r["leader"] = SIM.get("leader") or ""
    return r


_sim_stats_300 = sim_stats


# wraps: sim_stats
def sim_stats():                                          # + 558: the share of the simulator on its PC («sim_cpu_own»)
    r = _sim_stats_300()
    r["sim_cpu"] = SIM.get("sim_cpu") if r.get("pc_cpu") is not None else None
    return r
