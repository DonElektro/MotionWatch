#!/usr/bin/env python3
"""Sim-Texte: die sichtbaren deutschen Texte des 3D-Simulators für die Übersetzung sammeln (Sprachen Phase 1, 30.10.2026).

Liest simulator3d/scripts/*.gd, findet die Texte, die man im Simulator sieht (Beschriftungen von add_control, Label- und
Button-Texte, tooltip_text, start_info, Karten, Assistent, Hilfe …) und schreibt simulator3d/i18n/texte.json:

    {"Deutscher Text": {"en": "…", "fr": "…", "it": "…", "rm": "…"}, …}

(ein Eintrag kann zusätzlich "?": "warum unsicher" haben). Mehrmals laufen lassen ist harmlos: vorhandene Übersetzungen
bleiben, neue Texte kommen leer dazu, nicht mehr gefundene bleiben stehen (werden gemeldet; --aufraeumen entfernt sie).
Daneben entsteht simulator3d/i18n/abdeckung.txt: wie viele Texte, pro Datei, wie viele übersetzt, und welche Texte
zusammengesetzt werden («dynamisch» – die muss Phase 2 von Hand in T.t(...) mit %s / {name} umbauen).

    python3 werkzeuge/sim_texte.py                 # sammeln, texte.json + abdeckung.txt schreiben
    python3 werkzeuge/sim_texte.py --pruefen       # nur prüfen: Exit 1, wenn texte.json nicht aktuell ist oder Lücken hat
    python3 werkzeuge/sim_texte.py --mw-tabellen   # leere Übersetzungen aus den MoveEye-Tabellen (DE / TRX) füllen
    python3 werkzeuge/sim_texte.py --liste         # alle gefundenen Texte mit Datei:Zeile ausgeben

Nicht gesammelt: neu_data.gd (Versionshinweise, bleiben deutsch), print / Fehlermeldungen fürs Log, Kennungen (ids,
Schlüssel, Gruppen, Knotennamen), Pfade, JSON-Schlüssel, Shader und HTML/JS der Handy-Seiten (eigene Zählung im Bericht).
"""
import argparse
import collections
import glob
import json
import os
import re
import signal
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(ROOT, "simulator3d")
SCRIPTS = os.path.join(SIM, "scripts")
OUT = os.path.join(SIM, "i18n", "texte.json")
REPORT = os.path.join(SIM, "i18n", "abdeckung.txt")
LANGS = ("en", "fr", "it", "rm")
SKIP_FILES = {"neu_data.gd", "i18n.gd"}

# short German words that appear as pieces of composed texts (an / aus …) - kept, marked «dynamisch»
DE_SHORT = {"an", "aus", "ein", "und", "oder", "von", "bis", "mit", "ohne", "nein", "ja", "keine", "kein", "zu", "offen",
            "läuft", "fertig", "nie", "immer", "heute", "gestern", "jetzt"}
DE_WORDS = set("""der die das den dem des und oder nicht ist sind ein eine einen einem einer kein keine mit für von zu zum zur auf
im in an aus bei nach vor über unter wird werden wurde hat haben kann können muss soll noch schon nur auch wenn dann als wie
was wer wo hier jetzt alle alles neu neue neuer bitte du dich dir dein deine ihr sie es er man sich bis ohne gegen ab mehr
weniger aus an läuft gestartet gestoppt fertig leer voll zeigt zeigen spiel szene kamera kopf licht wetter""".split())
EN_WORDS = set("""the and not is are of to for with without from this that be been was were has have can cannot could
unknown error failed missing invalid yes off at by its if then else only all any none true false please
should must will would than which what when where who you your we our they their there here new old ok value""".split())
UNITS = {"km", "h", "m", "s", "cm", "mm", "hpa", "db", "fps", "px", "mb", "gb", "kb", "ms", "mah", "kmh", "x", "v", "w",
         "kw", "wh", "lux", "lx", "mhz", "ghz", "dbm", "ip", "id", "nr", "min", "sek", "std", "fov"}

# code just before the string (stripped) that makes it an id / key / path, not a text
BEFORE_SKIP = re.compile(r"""(==|!=|\bin|\.get|\.has|\bhas|get_node|get_node_or_null|has_node|find_child|\$|has_method|\.call|
    \.callv|call_deferred|\.connect|emit_signal|add_to_group|is_in_group|get_nodes_in_group|remove_from_group|\.set|\.get_meta|
    \.set_meta|has_meta|\.find|\.rfind|begins_with|ends_with|\.replace|\.split|\.rsplit|load|preload|ResourceLoader\.exists|
    file_exists|dir_exists|FileAccess\.open|DirAccess\.open|\.open|\.erase|\.contains|\.count|\.trim_prefix|\.trim_suffix|
    is_action_pressed|is_action_just_pressed|is_action_released|get_action_strength|get_axis|get_vector|is_action|
    add_theme_\w+_override|get_theme_\w+|has_theme_\w+|remove_theme_\w+_override|set_shader_parameter|get_shader_parameter|
    \.name\s*=|\bname\s*=|tkey\s*=|\bmatch|play|\.animation\s*=|OS\.\w+|ProjectSettings\.\w+|Engine\.\w+|ClassDB\.\w+|
    \.is_class|JSON\.\w+|\.queue_free|get_setting|set_setting|Marshalls\.\w+|\.substr|request|_send|_ws_send|http_get|_get|
    \.has_signal|add_user_signal|tween_property|tween_method|\.bind|\.rpc|\.rpc_id|create_timer|instantiate|
    action_add_event|InputMap\.\w+|keys|\.lstrip|\.rstrip|\.strip_edges|\.format_ignore)\s*\(?\s*$""", re.X)
DEBUG_CALL = re.compile(r"\b(print|printerr|prints|printraw|print_debug|push_warning|push_error|assert|_log|log_line|_dbg|debug)\s*\(")
HTML_RE = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*[\s>/]|function\s*\(|=>|document\.|\{\s*margin|;\s*\}|var\(--|getElementById")
SHADER_RE = re.compile(r"\b(uniform|varying|shader_type|render_mode|vec[234]|void\s+\w+\()")
PATH_RE = re.compile(r"^(res|user|https?|wss?|file)://|^[\w.\-]+/[\w.\-/]*$|\.(png|jpe?g|json|gd|tscn|tres|glb|gltf|ogg|wav|mp3|txt|zip|exe|cfg|html|js|css|svg|py|sh|md|csv|webp|bin|pck|bmp|tga|obj)$", re.I)
TECH_RE = re.compile(r"^(Authorization|Accept|User-Agent|Content-Type|Content-Length|Connection|Cache-Control|Location|Host|X-[\w-]+):|"
                     r"^[a-z]+/[\w.+-]+(;|$)|HTTP/1\.[01]|\n[a-z]+: [a-z.]|\$\w|Start-Process|Write-Output|Get-CimInstance|\\d|^\[out:|^\{\"|^--\w|\s--\w|"
                     r"^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|Bad Request|Not Found|Forbidden|Unauthorized|Internal Server Error|Method Not Allowed)$")
# technical words that look like text (key names, Godot classes, device ids, file dialog filters …)
TECH_WORDS = {"Backspace", "Enter", "Tab", "Escape", "Delete", "Hidden", "TRACE", "CONNECT", "COMPUTERNAME", "HOSTNAME",
              "Button", "Label", "VScrollBar", "DTM2", "COMB", "DTM25", "SmallTV-Ultra", "Ultra-V9.0.40", "MoveEye-Simulator",
              "webcam_bewegung_*.py ; MoveEye", "*.py ; Python", "|sprint"}
ID_RE = re.compile(r"^[a-z0-9_.\-:/#+%]*$")
CLASSNAME_RE = re.compile(r"^[A-Z][A-Za-z0-9]*(2D|3D|Container|Button|Label|Rect|Edit|Box|Panel|Slider|Instance|Mesh|Material|Texture|Light|Shape|Body|Player|Popup|Dialog|Timer|Tween|Node|Viewport|Camera)$")


def decode(raw):
    """GDScript string escapes -> the real text"""
    out, i = [], 0
    while i < len(raw):
        c = raw[i]
        if c == "\\" and i + 1 < len(raw):
            n = raw[i + 1]
            if n == "u" and re.match(r"[0-9a-fA-F]{4}", raw[i + 2:i + 6]):
                out.append(chr(int(raw[i + 2:i + 6], 16))); i += 6; continue
            out.append({"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'"}.get(n, "\\" + n)); i += 2; continue
        out.append(c); i += 1
    return "".join(out)


def strings_of(src):
    """yield (value, line, triple, prefix, code_before_on_line, code_after_on_line, whole_line) for every literal"""
    lits = []                                 # (start, end, raw, triple, prefix)
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "#":
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if c in "\"'":
            prefix = src[i - 1] if i > 0 and src[i - 1] in "&^" else ""
            if src.startswith(c * 3, i):
                j = src.find(c * 3, i + 3)
                j = n - 3 if j < 0 else j
                lits.append((i, j + 3, src[i + 3:j], True, prefix)); i = j + 3; continue
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            lits.append((i, j + 1, src[i + 1:j], False, prefix)); i = j + 1; continue
        i += 1
    # code with the strings blanked (for the context)
    blank = list(src)
    for s, e, *_ in lits:
        for k in range(s, min(e, n)):
            if blank[k] != "\n":
                blank[k] = "_" if s < k < e - 1 else '"'
    blank = "".join(blank)
    line_starts = [0] + [m.end() for m in re.finditer("\n", src)]
    import bisect
    for s, e, raw, triple, prefix in lits:
        ln = bisect.bisect_right(line_starts, s)
        ls = line_starts[ln - 1]
        le = src.find("\n", e); le = n if le < 0 else le
        yield decode(raw), ln, triple, prefix, blank[ls:s], blank[e:le], blank[ls:le]


def letters(s):
    return re.sub(r"[^A-Za-zÀ-ÿ]", "", s)


def classify(v, triple, prefix, before, after, line):
    """'' = a UI text, else why not (for --warum)"""
    if triple:
        return "doc"
    if prefix:
        return "stringname"
    t = v.strip()
    if len(letters(t)) < 2:
        return "keine Wörter"
    if DEBUG_CALL.search(line[:len(before)]) or "SCRIPT ERROR" in v:
        return "log"
    if HTML_RE.search(v):
        return "html"
    if SHADER_RE.search(v):
        return "shader"
    uikey = (" " in v.strip() or re.search(r"[äöüÄÖÜ]", v)) and re.match(r"^[A-ZÄÖÜ]", v.strip())
    if re.match(r"^\s*:", after) and not uikey:
        return "schlüssel"                     # dict key / match branch (a German text as key stays: group names …)
    b = before.rstrip()
    if BEFORE_SKIP.search(b):
        return "kennung"
    if b.endswith("[") and not re.search(r"[=(,\[]\s*\[$", b) and re.search(r"[\w\])]\[$", b):
        return "index"
    if t in TECH_WORDS or re.fullmatch(r"\*[0-9a-fA-F]{6}|-[A-Z]\w+|[a-z]+[A-Z]\w*|\w+=.*|MWTUN\d.*|import .*", t) \
            or t.startswith(("Mozilla/", "advfirewall", "kind: ", "ort:")) or TECH_RE.search(t) or (" " not in t and ("_" in t or "\\" in t or re.search(r"[A-Za-z0-9]\.[A-Za-z]", t) or t[:1] in "/?")):
        return "technisch"
    if PATH_RE.search(t) and " " not in t:
        return "pfad"
    if ID_RE.match(t) and t.lower() not in DE_SHORT:
        return "kennung"
    if " " not in t and CLASSNAME_RE.match(t):
        return "klasse"
    if re.fullmatch(r"[A-Z][a-z]+[A-Z]\w*", t) and " " not in t:  # CamelCase identifiers
        return "kennung"
    words = re.findall(r"[A-Za-zÀ-ÿ]+", t.lower())
    if not [w for w in words if len(w) >= 2 and w not in UNITS] and not any(w in DE_SHORT for w in words):
        return "einheit"
    de = sum(w in DE_WORDS for w in words) + 2 * len(re.findall(r"[äöüÄÖÜ]", t))
    en = sum(w in EN_WORDS for w in words)
    if en > de and en >= 1:
        return "englisch"
    if re.fullmatch(r"[a-z][a-z0-9_]*(\s+[a-z0-9_]+)*", t) and de == 0 and t.lower() not in DE_SHORT:
        return "kennung"
    return ""


def is_dynamic(v, before, after):
    b, a = before.rstrip(), after.lstrip()
    if b.endswith("+") or a.startswith("+") or b.endswith("+=") or a.startswith("+="):
        return True
    if v != v.strip() or v.strip().lower() in DE_SHORT:
        return True
    return False


def scene_names():
    """scenes.gd: German scene name -> English (const LIST + const EN, the names MoveEye already shows)"""
    src = open(os.path.join(SCRIPTS, "scenes.gd"), encoding="utf-8").read()
    lst = dict(re.findall(r'\["(\w+)", "([^"]+)"\]', src.split("const EN", 1)[0]))
    m = re.search(r"const EN := \{(.*?)\}", src, re.S)
    en = dict(re.findall(r'"(\w+)": "([^"]+)"', m.group(1))) if m else {}
    return {lst[k]: en[k] for k in lst if k in en}


def collect():
    found = collections.OrderedDict()        # text -> [(file, line, dynamic)]
    en_names = set(scene_names().values())
    skipped = collections.Counter()
    html = collections.Counter()
    for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.gd"))):
        fn = os.path.basename(path)
        if fn in SKIP_FILES:
            continue
        src = open(path, encoding="utf-8").read()
        for v, ln, triple, prefix, before, after, line in strings_of(src):
            why = classify(v, triple, prefix, before, after, line)
            if not why and fn == "scenes.gd" and v in en_names:
                why = "englisch"
            if why == "html":
                html[fn] += 1
            if why:
                skipped[why] += 1
                continue
            found.setdefault(v, []).append((fn, ln, is_dynamic(v, before, after)))
    return found, skipped, html


def load_existing():
    if not os.path.exists(OUT):
        return {}
    with open(OUT, encoding="utf-8") as f:
        d = json.load(f)
    return {k: v for k, v in d.items() if not k.startswith("_")}


def mw_tables():
    """German -> {en, fr, it, rm} from MoveEye (the newest built file webcam_bewegung_*.py, loaded as a module)"""
    import importlib.util
    files = sorted(glob.glob(os.path.join(ROOT, "webcam_bewegung_*.py")),
                   key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    if not files:
        return {}
    sys.argv = [files[-1]]
    spec = importlib.util.spec_from_file_location("mw_tx", files[-1])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = {}
    for en, de in m.DE.items():
        if not isinstance(de, str) or not isinstance(en, str):
            continue
        row = {"en": en}
        for L in ("fr", "it", "rm"):
            x = m.TRX.get(L, {}).get(en)
            if isinstance(x, str):
                row[L] = x
        if len(row) == 4:
            out.setdefault(de, row)
    return out


def write_json(d):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    body = {"_hinweis": "Übersetzungen des 3D-Simulators: Schlüssel = deutscher Text wie im Code, Werte en/fr/it/rm "
                        "(leer = noch offen, «?» = unsicher). Erzeugt und nachgeführt mit werkzeuge/sim_texte.py; "
                        "gelesen von scripts/i18n.gd (T.t). Fallback: rm -> de, fr/it -> en -> de."}
    for k in sorted(d, key=lambda s: (s.lower(), s)):
        row = d[k]
        body[k] = {L: row.get(L, "") for L in LANGS}
        if row.get("?"):
            body[k]["?"] = row["?"]
    txt = json.dumps(body, ensure_ascii=False, indent=1) + "\n"
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if txt != old:
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(txt)
    return txt != old


def report(found, d, skipped, html, obsolete):
    per_file = collections.OrderedDict()
    dyn = collections.OrderedDict()
    for v, occ in found.items():
        for fn, ln, dy in occ:
            pf = per_file.setdefault(fn, {"n": set(), "dyn": 0})
            pf["n"].add(v)
            if dy:
                pf["dyn"] += 1
                dyn.setdefault(fn, []).append((ln, v))
    filled = {L: sum(1 for v in found if (d.get(v) or {}).get(L)) for L in LANGS}
    unsure = [v for v in found if (d.get(v) or {}).get("?")]
    L = ["Abdeckung der Simulator-Texte (erzeugt von werkzeuge/sim_texte.py – nicht von Hand ändern)", "",
         f"Texte gesamt: {len(found)} (Stellen: {sum(len(o) for o in found.values())})",
         "Übersetzt: " + ", ".join(f"{k} {filled[k]}" for k in LANGS),
         f"Unsicher markiert: {len(unsure)}",
         f"Dynamisch (zusammengesetzt, Phase 2 von Hand umbauen): {sum(len(x) for x in dyn.values())} Stellen",
         f"Nicht mehr im Code (noch in texte.json): {len(obsolete)}",
         f"HTML/JS-Texte der Handy-Seiten (nicht gesammelt): {sum(html.values())} Stellen in " + ", ".join(f"{k} {v}" for k, v in html.most_common()),
         "Übersprungen (Grund: Anzahl): " + ", ".join(f"{k} {v}" for k, v in skipped.most_common()), "",
         "Pro Datei (Texte / davon dynamische Stellen):"]
    for fn, pf in sorted(per_file.items(), key=lambda x: -len(x[1]["n"])):
        L.append(f"  {fn:<22} {len(pf['n']):>5}  {pf['dyn']:>4}")
    L += ["", "Unsicher:"] + [f"  {v!r}: {(d.get(v) or {}).get('?')}" for v in unsure]
    L += ["", "Dynamische Stellen (Datei:Zeile Text) – in Phase 2 zu einer Vorlage mit %s / {name} machen:"]
    for fn, items in dyn.items():
        for ln, v in sorted(items):
            L.append(f"  {fn}:{ln}  {v!r}")
    txt = "\n".join(L) + "\n"
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(txt)
    return filled, unsure, dyn


def main():
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)      # «| head» without a traceback
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pruefen", action="store_true", help="nur prüfen (Exit 1 bei neuen Texten oder Lücken)")
    ap.add_argument("--aufraeumen", action="store_true", help="Texte entfernen, die nicht mehr im Code stehen")
    ap.add_argument("--mw-tabellen", action="store_true", help="leere Übersetzungen aus den MoveEye-Tabellen füllen")
    ap.add_argument("--liste", action="store_true", help="alle Texte mit Datei:Zeile ausgeben")
    ap.add_argument("--warum", metavar="TEXT", help="zeigen, warum ein Text (nicht) gesammelt wird")
    a = ap.parse_args()
    found, skipped, html = collect()
    if a.warum:
        for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.gd"))):
            src = open(path, encoding="utf-8").read()
            for v, ln, triple, prefix, before, after, line in strings_of(src):
                if a.warum in v:
                    print(f"{os.path.basename(path)}:{ln}: {classify(v, triple, prefix, before, after, line) or 'TEXT'}: {v!r}")
        return 0
    if a.liste:
        for v, occ in found.items():
            print(f"{occ[0][0]}:{occ[0][1]}{' +' + str(len(occ) - 1) if len(occ) > 1 else ''}{' [dyn]' if any(o[2] for o in occ) else ''}  {v!r}")
        return 0
    d = load_existing()
    new = [v for v in found if v not in d]
    obsolete = [v for v in d if v not in found]
    if a.pruefen:
        gaps = [v for v in found if v in d and not all(d[v].get(L) for L in LANGS)]
        print(f"Sim-Texte: {len(found)} Texte, {len(new)} neu, {len(gaps)} mit Lücken, {len(obsolete)} nicht mehr im Code")
        return 1 if new or gaps else 0
    for v in new:
        d[v] = {L: "" for L in LANGS}
    if a.aufraeumen:
        for v in obsolete:
            d.pop(v, None)
    took = 0
    for de, en in scene_names().items():          # the English scene names of scenes.gd (MoveEye shows the same)
        if de in d and not d[de].get("en"):
            d[de]["en"] = en
    if a.mw_tabellen:
        mw = mw_tables()
        for v in found:
            row = mw.get(v)
            if row:
                for L in LANGS:
                    if not d[v].get(L) and row.get(L):
                        d[v][L] = row[L]; took += 1
    changed = write_json(d)
    filled, unsure, dyn = report(found, d, skipped, html, [] if a.aufraeumen else obsolete)
    print(f"Sim-Texte: {len(found)} Texte ({len(new)} neu, {len(obsolete)} nicht mehr im Code"
          f"{' – entfernt' if a.aufraeumen and obsolete else ''}), übersetzt " + ", ".join(f"{k} {filled[k]}" for k in LANGS)
          + f", unsicher {len(unsure)}, dynamische Stellen {sum(len(x) for x in dyn.values())}"
          + (f", aus MoveEye übernommen {took}" if a.mw_tabellen else "")
          + (" – texte.json geschrieben" if changed else " – texte.json unverändert"))
    for v in new[:40]:
        print("  neu:", repr(v))
    if len(new) > 40:
        print(f"  … und {len(new) - 40} weitere neue")
    for v in obsolete[:20]:
        print("  nicht mehr im Code:", repr(v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
