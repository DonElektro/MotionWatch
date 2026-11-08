#!/usr/bin/env python3
"""Artinfos für «🌿 Bestimmen» (MoveEye Teil 639zzd) bauen – läuft im Workflow «BioCLIP-Infos» (.github/workflows/bioclip_info.yml)
auf einem GitHub-Rechner (Wikipedia / Wikidata sind beim Integrator nicht erreichbar). Nichts wird erfunden, übersetzt oder von
einem Sprachmodell geschrieben: alle Texte sind wörtliche Ausschnitte aus Wikipedia, alle Fakten Werte aus Wikidata.

  python3 werkzeuge/bioclip_info_bauen.py --arten bioclip-1-arten.json --aus DIR [--nur "Allium ursinum,Taxus baccata"]

Ergebnis in DIR:
  bioclip-info-1.sqlite   Tabelle info(sci, z): z = zlib(JSON) pro Art; Tabelle meta(k, v) mit Quellen, Regeln, Zahlen
  abdeckung.json          wie viele Arten einen deutschen / englischen Text, ein «giftig» / «essbar» haben
  stichprobe.txt          die Karten der Stichprobe (STICH) – der Lauf schlägt fehl, wenn eine davon nicht stimmt
  pins.txt                Grösse + sha256

Quellen (Entscheid Besitzer):
  * Deutsche Wikipedia: die Einleitung, gekürzt auf ganze Sätze (etwa 400–600 Zeichen), Lizenz CC BY-SA 4.0, Autoren = die
    Versionsgeschichte (Link pro Eintrag). Fehlt ein deutscher Artikel: die englische Einleitung, markiert «(englisch)».
  * Wikidata (CC0): Wuchshöhe (P2048), Rote Liste IUCN (P141), Lebensraum (P2974), Speisepilz-Eigenschaft (P789),
    Eigenschaft (P1552, nur «giftig»).
Regeln «giftig» / «essbar» (vorsichtig – nur ausdrückliche Sätze, sonst nichts), siehe REGELN unten und im Kopf von Teil 639zzd.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
import zlib

UA = {"User-Agent": "MoveEye-bioclip-info/1 (github.com/DonElektro/MotionWatch; species cards, offline)"}
WD = "https://query.wikidata.org/sparql"
API = {"de": "https://de.wikipedia.org/w/api.php", "en": "https://en.wikipedia.org/w/api.php"}
LEAD_MIN, LEAD_MAX = 400, 600

REGELN = """\
giftig: (1) ein Satz im deutschen Artikel sagt es aus: «giftig» als Aussage («ist / sind (sehr / stark / tödlich) giftig»,
  «giftig für …»), «giftigste», «Giftpflanze», «Giftpilz», «Giftschlange», «giftige Pflanze / Pilz / Art»; der Satz enthält
  keine Verneinung («nicht giftig», «ungiftig», «kein Gift»), kein «verwechseln / Verwechslung / Doppelgänger / ähnlich» und
  keinen deutschen Namen einer anderen Art der Liste; oder (2) Wikidata P789 «poisonous / deadly» oder P1552 «poisonous».
essbar: nur Pflanzen und Pilze; ein Satz im deutschen Artikel: «essbar», «Speisepilz», «Wildgemüse», «als Salat / Gemüse /
  Gewürz / Tee … verwendet / gegessen», «werden … gegessen», «zu Marmelade / Konfitüre / Saft / Gelee / Pesto verarbeitet»;
  ohne Verneinung («nicht essbar», «ungenießbar», «kein Speisepilz»), ohne ein Wort zu «giftig» im selben Satz, ohne
  Verwechslung, ohne Namen einer anderen Art. Ist die Art «giftig», wird «essbar» nie gezeigt (unklar = nichts).
  MoveEye zeigt «essbar» immer nur mit der Warnung (Verwechslungsgefahr, Tox Info Suisse 145).
Verwechslung: Sätze mit «verwechseln / Verwechslung / Doppelgänger»: verlinkte Artikel (Wikipedia-Links) in diesem Satz.
"""

# Stichprobe (Besitzer): giftig / essbar - muss stimmen, sonst schlägt der Lauf fehl
STICH = {"Colchicum autumnale": "tox", "Convallaria majalis": "tox", "Taxus baccata": "tox", "Amanita muscaria": "tox",
         "Amanita phalloides": "tox", "Atropa belladonna": "tox",
         "Allium ursinum": "ed", "Taraxacum officinale": "ed", "Boletus edulis": "ed", "Rubus fruticosus": "ed"}

_ABK = ("z. B.", "u. a.", "d. h.", "v. a.", "s. o.", "s. u.", "o. Ä.", "u. Ä.", "bzw.", "ca.", "etc.", "sog.", "vgl.", "evtl.",
        "inkl.", "lat.", "griech.", "Nr.", "St.", "Dr.", "Prof.", "subsp.", "var.", "agg.", "spec.", "sp.", "ssp.", "u. U.", "z. T.")
NEG_TOX = re.compile(r"\b(nicht|kaum|wenig|un)\s*giftig|\bungiftig|\bkein(e|en|er)?\s+(Gift|giftig)|\bnicht\s+als\s+giftig", re.I)
TOX = re.compile(r"(\b(ist|sind|gilt|gelten|wirkt|wirken|werden|wird)\b[^.;]{0,40}\bgiftig\b|\bgiftig\s+(für|ist|sind)\b"
                 r"|\b(sehr|stark|hoch|tödlich|schwach|leicht|mäßig|gering)\s+giftig\b|\bgiftigsten?\b|\bGiftpflanze\w*|\bGiftpilz\w*"
                 r"|\bGiftschlange\w*|\bgiftige[nrs]?\s+(Pflanze|Pilz|Art|Zierpflanze|Gartenpflanze|Wildpflanze)\b)")
TOXWORD = re.compile(r"giftig|Gift|Vergiftung|toxisch", re.I)
VERW = re.compile(r"verwechs|Verwechs|Doppelgänger|zum Verwechseln", re.I)
NEG_ED = re.compile(r"\bnicht\s+(essbar|genießbar|zum\s+Verzehr|gegessen|verzehrt)|\bunessbar|\bungenießbar|\bkein(e|en)?\s+Speisepilz"
                    r"|\bnicht\s+geeignet|\bungeeignet", re.I)
ED = re.compile(r"\bessbar\w*|\bSpeisepilz\w*|\bWildgemüse\b|\bals\s+(Salat|Gemüse|Gewürz|Würze|Tee|Wildgemüse|Kompott|Speise\w*|"
                r"Nahrungsmittel|Küchenkraut)\b[^.;]{0,40}\b(verwendet|genutzt|gegessen|verzehrt|zubereitet|gebraucht)"
                r"|\bwerden\b[^.;]{0,50}\b(roh|gekocht|gegart|gebraten)?\s*gegessen\b|\bwird\b[^.;]{0,50}\bgegessen\b"
                r"|\bzu\s+(Marmelade|Konfitüre|Saft|Gelee|Pesto|Likör|Kompott|Mus)\w*\s+verarbeitet")


def get(url, data=None, timeout=90, tries=6):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(r, timeout=timeout) as f:
                return f.read()
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1) + (20 if "429" in str(e) else 0))


def getj(url, **k):
    return json.loads(get(url, **k).decode("utf-8"))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---- Wikidata: Artikel-Titel + Fakten ---------------------------------------------------------------------------------------
def wikidata(names):
    out = {}
    lst = sorted(set(names))
    for i in range(0, len(lst), 80):
        part = lst[i:i + 80]
        vals = " ".join('"%s"' % n.replace('"', "") for n in part)
        q = """SELECT ?name ?item ?rank ?de ?en (GROUP_CONCAT(DISTINCT ?iucnL; separator="|") AS ?iucn)
  (GROUP_CONCAT(DISTINCT ?edL; separator="|") AS ?ed) (GROUP_CONCAT(DISTINCT ?chL; separator="|") AS ?ch)
  (GROUP_CONCAT(DISTINCT ?habL; separator="|") AS ?hab) (GROUP_CONCAT(DISTINCT ?h; separator="|") AS ?hs) WHERE {
  VALUES ?name { %s } ?item wdt:P225 ?name .
  OPTIONAL { ?item wdt:P105 ?rank }
  OPTIONAL { ?de schema:about ?item ; schema:isPartOf <https://de.wikipedia.org/> }
  OPTIONAL { ?en schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  OPTIONAL { ?item wdt:P141 ?iu . ?iu rdfs:label ?iucnL FILTER(LANG(?iucnL) = "de") }
  OPTIONAL { ?item wdt:P789 ?e . ?e rdfs:label ?edL FILTER(LANG(?edL) = "en") }
  OPTIONAL { ?item wdt:P1552 ?c . ?c rdfs:label ?chL FILTER(LANG(?chL) = "en") }
  OPTIONAL { ?item wdt:P2974 ?hb . ?hb rdfs:label ?habL FILTER(LANG(?habL) = "de") }
  OPTIONAL { ?item p:P2048/psv:P2048 [ wikibase:quantityAmount ?ha ; wikibase:quantityUnit ?hu ] .
             ?hu rdfs:label ?hul FILTER(LANG(?hul) = "en") BIND(CONCAT(STR(?ha), " ", ?hul) AS ?h) }
} GROUP BY ?name ?item ?rank ?de ?en""" % vals
        try:
            j = getj(WD + "?" + urllib.parse.urlencode({"query": q, "format": "json"}), timeout=180)
        except Exception as e:
            print("  Wikidata Teil %d: %s" % (i, e), flush=True); continue
        for b in j["results"]["bindings"]:
            v = {k: x["value"] for k, x in b.items()}
            n = v["name"]
            tit = {L: urllib.parse.unquote(v[L].rsplit("/wiki/", 1)[1]).replace("_", " ") for L in ("de", "en") if v.get(L)}
            score = 2 * ("de" in tit) + 2 * v.get("rank", "").endswith("/Q7432") + ("en" in tit)
            cur = out.get(n)
            if cur and cur["score"] >= score:
                continue
            sp = lambda k: [x for x in (v.get(k) or "").split("|") if x]
            out[n] = {"score": score, "q": v["item"].rsplit("/", 1)[1], "tit": tit, "iucn": sp("iucn"), "ed": sp("ed"),
                      "ch": sp("ch"), "hab": sp("hab"), "h": sp("hs")}
        time.sleep(0.5)
        if i % 2000 == 0:
            print("  Wikidata %d / %d" % (i, len(lst)), flush=True)
    return out


# ---- Wikipedia --------------------------------------------------------------------------------------------------------------
def intros(L, titles):
    """Titel -> (Einleitung als Text, revid, endgültiger Titel) - 20 pro Anfrage"""
    out = {}
    lst = sorted(set(titles))
    for i in range(0, len(lst), 20):
        part = lst[i:i + 20]
        q = {"action": "query", "format": "json", "formatversion": "2", "prop": "extracts|info", "exintro": "1", "explaintext": "1",
             "exlimit": "20", "redirects": "1", "titles": "|".join(part), "maxlag": "5"}
        try:
            j = getj(API[L] + "?" + urllib.parse.urlencode(q))
        except Exception as e:
            print("  %s Einleitungen %d: %s" % (L, i, e), flush=True); continue
        qq = j.get("query") or {}
        back = {}
        for k in ("normalized", "redirects"):
            for r in qq.get(k) or []:
                back[r["to"]] = back.get(r["from"], r["from"])
        for p in qq.get("pages") or []:
            if p.get("missing") or not p.get("extract"):
                continue
            src = back.get(p["title"], p["title"])
            out[src] = (p["extract"], p.get("lastrevid"), p["title"])
        if i % 2000 == 0:
            print("  %s Einleitungen %d / %d" % (L, i, len(lst)), flush=True)
    return out


def volltext(title):
    """ganzer Artikel als Text (mit == Abschnitten ==) + verlinkte Artikel"""
    q = {"action": "query", "format": "json", "formatversion": "2", "prop": "extracts|links", "explaintext": "1",
         "exsectionformat": "wiki", "pllimit": "max", "plnamespace": "0", "redirects": "1", "titles": title, "maxlag": "5"}
    try:
        j = getj(API["de"] + "?" + urllib.parse.urlencode(q))
    except Exception:
        return title, "", []
    ps = (j.get("query") or {}).get("pages") or [{}]
    return title, ps[0].get("extract") or "", [x["title"] for x in ps[0].get("links") or []]


def saetze(text):
    for a in _ABK:
        text = text.replace(a, a.replace(".", "․"))
    out = []
    for para in text.split("\n"):
        para = para.strip()
        if not para or para.startswith("=="):
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ„«(])", para):
            s = s.replace("․", ".").strip()
            if s:
                out.append(s)
    return out


def kuerzen(text):
    """die Einleitung auf ganze Sätze, etwa LEAD_MIN-LEAD_MAX Zeichen"""
    ss, out = saetze(text), ""
    for s in ss:
        if len(out) + len(s) + 1 > LEAD_MAX:
            break
        out = (out + " " + s).strip()
        if len(out) >= LEAD_MIN:
            break
    if not out and ss:
        w = ss[0][:LEAD_MAX - 1]
        out = w[:w.rfind(" ")] + " …" if " " in w else w + "…"
    return out


def andere_namen(s, own, namen):
    """deutsche Namen anderer Arten der Liste im Satz (1- bis 3-Wort-Folgen)"""
    w = re.findall(r"[A-Za-zÄÖÜäöüß-]+", s)
    hits = set()
    for n in (1, 2, 3):
        for i in range(len(w) - n + 1):
            k = " ".join(w[i:i + n])
            if k in namen and k not in own:
                hits.add(k)
    return hits


def pruefen(text, own, namen, links, pflanze_pilz):
    tox, ed, look = [], [], []
    for s in saetze(text):
        if len(s) > 500:
            continue
        verw = bool(VERW.search(s))
        other = andere_namen(s, own, namen)
        if verw:
            for t in links:
                if t not in own and len(t) > 3 and re.search(r"(?<![A-Za-zÄÖÜäöüß])" + re.escape(t) + r"(?![a-zäöüß])", s):
                    look.append(t)
            continue
        if TOX.search(s) and not NEG_TOX.search(s) and not other:
            tox.append(s)
        elif pflanze_pilz and ED.search(s) and not NEG_ED.search(s) and not TOXWORD.search(s) and not other:
            ed.append(s)
    seen = set()
    look = [x for x in look if not (x in seen or seen.add(x))]
    return tox[:2], ed[:2], look[:6]


def hoehe(vals):
    best = None
    f = {"metre": 1.0, "centimetre": 0.01, "millimetre": 0.001}
    for v in vals:
        try:
            a, u = v.split(" ", 1)
            m = float(a) * f[u]
        except (ValueError, KeyError):
            continue
        best = m if best is None or m > best else best
    if best is None or best <= 0:
        return ""
    if best >= 1:
        return ("bis %.1f m" % best).replace(".0 m", " m").replace(".", ",")
    if best >= 0.01:
        return "bis %d cm" % round(best * 100)
    return ("bis %.1f mm" % (best * 1000)).replace(".0 mm", " mm").replace(".", ",")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arten", required=True)
    ap.add_argument("--aus", required=True)
    ap.add_argument("--nur", default="", help="nur diese Arten (Komma) - schneller Probelauf der Regeln")
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.aus, exist_ok=True)
    L = json.load(open(a.arten, encoding="utf-8"))
    taxa = {t[5] + " " + t[6]: t for t in L["taxa"]}
    names = L.get("names") or {}
    want = [x.strip() for x in a.nur.split(",") if x.strip()] or sorted(taxa)
    if a.nur:
        for x in list(STICH):
            if x not in want:
                want.append(x)
    print("Arten: %d (Liste %d)" % (len(want), len(taxa)), flush=True)
    W = wikidata(want)
    print("Wikidata: %d Treffer, %d mit de-Artikel, %d mit en-Artikel" % (len(W), sum("de" in w["tit"] for w in W.values()),
                                                                       sum("en" in w["tit"] for w in W.values())), flush=True)
    de_t = {n: w["tit"]["de"] for n, w in W.items() if "de" in w["tit"]}
    en_t = {n: w["tit"]["en"] for n, w in W.items() if "en" in w["tit"] and n not in de_t}
    I_de = intros("de", de_t.values())
    I_en = intros("en", en_t.values())
    print("Einleitungen: de %d, en %d" % (len(I_de), len(I_en)), flush=True)
    # alle deutschen Artnamen der Liste (für «andere Art im Satz») + die Titel der deutschen Artikel
    namen = set()
    for n in taxa:
        d = (names.get(n) or {}).get("de")
        if d and len(d) > 3:
            namen.add(d)
    for n, t in de_t.items():
        if len(t) > 3 and t != n:
            namen.add(t)
    full = {}
    with cf.ThreadPoolExecutor(6) as ex:
        for k, (tit, txt, links) in enumerate(ex.map(volltext, sorted(set(de_t.values())))):
            full[tit] = (txt, links)
            if k % 1000 == 0:
                print("  Volltexte %d / %d" % (k, len(de_t)), flush=True)
    rows, cov = {}, {"arten": len(want), "de": 0, "en": 0, "keiner": 0, "giftig": 0, "giftig_wd": 0, "essbar": 0, "verwechslung": 0,
                     "hoehe": 0, "iucn": 0, "lebensraum": 0}
    for n in want:
        t = taxa.get(n) or [""] * 7
        w = W.get(n) or {"tit": {}, "iucn": [], "ed": [], "ch": [], "hab": [], "h": [], "q": ""}
        e = {"q": w.get("q", "")}
        own = {n, t[5]}
        dn = (names.get(n) or {}).get("de")
        if dn:
            own.add(dn)
        if n in de_t and de_t[n] in I_de:
            x, rev, tit = I_de[de_t[n]]
            own.add(tit)
            e.update(l="de", t=tit, x=kuerzen(x), r=rev)
            txt, links = full.get(de_t[n], ("", []))
            tox, ed, look = pruefen(txt or x, own, namen, links, t[0] in ("Plantae", "Fungi"))
            if tox:
                e["tox"] = tox
            if ed and not tox:
                e["ed"] = ed
            if look:
                e["look"] = look
            cov["de"] += 1
        elif n in en_t and en_t[n] in I_en:
            x, rev, tit = I_en[en_t[n]]
            e.update(l="en", t=tit, x=kuerzen(x), r=rev)
            cov["en"] += 1
        else:
            cov["keiner"] += 1
        wd_tox = [x for x in w["ed"] + w["ch"] if re.search(r"poison|deadly|toxic", x, re.I)]
        if wd_tox:
            e["toxwd"] = wd_tox[:2]
            e.pop("ed", None)                                      # unklar = nichts zu «essbar»
        h = hoehe(w["h"])
        if h:
            e["h"] = h; cov["hoehe"] += 1
        if w["iucn"]:
            e["iucn"] = w["iucn"][0]; cov["iucn"] += 1
        if w["hab"]:
            e["hab"] = ", ".join(w["hab"][:4]); cov["lebensraum"] += 1
        cov["giftig"] += int(bool(e.get("tox") or e.get("toxwd")))
        cov["giftig_wd"] += int(bool(e.get("toxwd")))
        cov["essbar"] += int(bool(e.get("ed")))
        cov["verwechslung"] += int(bool(e.get("look")))
        rows[n] = e
    # Verwechslung: ☠️ für verlinkte Arten, die selbst «giftig» sind
    tox_titles = {r.get("t") for r in rows.values() if r.get("l") == "de" and (r.get("tox") or r.get("toxwd"))}
    for r in rows.values():
        if r.get("look"):
            r["look"] = [[x, int(x in tox_titles)] for x in r["look"]]
    db = os.path.join(a.aus, "bioclip-info-1.sqlite")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE info (sci TEXT PRIMARY KEY, z BLOB NOT NULL)")
    con.execute("CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT)")
    con.executemany("INSERT INTO info VALUES (?, ?)", [(n, zlib.compress(json.dumps(e, ensure_ascii=False, separators=(",", ":")).encode(), 9))
                                                        for n, e in sorted(rows.items())])
    meta = {"format": "1", "built": time.strftime("%Y-%m-%d"), "regeln": REGELN, "abdeckung": json.dumps(cov),
            "quellen": "Texte: Wikipedia (de, sonst en), CC BY-SA 4.0, Autoren: Versionsgeschichte des Artikels; Fakten: Wikidata (CC0)"}
    con.executemany("INSERT INTO meta VALUES (?, ?)", sorted(meta.items()))
    con.commit(); con.execute("VACUUM"); con.close()
    json.dump(cov, open(os.path.join(a.aus, "abdeckung.json"), "w"), indent=1)
    # Stichprobe
    lines, bad = [], []
    for n, kind in STICH.items():
        e = rows.get(n)
        if e is None:
            bad.append("%s fehlt in der Liste" % n); continue
        is_tox, is_ed = bool(e.get("tox") or e.get("toxwd")), bool(e.get("ed"))
        okk = is_tox if kind == "tox" else (is_ed and not is_tox)
        if not okk:
            bad.append("%s: erwartet %s, gefunden giftig=%s essbar=%s" % (n, kind, is_tox, is_ed))
        lines.append("=== %s (%s) – %s · erwartet %s · %s\n%s" % (n, (names.get(n) or {}).get("de", ""), e.get("t", "-"), kind,
                                                                 "OK" if okk else "FALSCH", json.dumps(e, ensure_ascii=False, indent=1)))
    if "Allium ursinum" in rows and not rows["Allium ursinum"].get("look"):
        bad.append("Bärlauch: keine Verwechslungs-Arten gefunden")
    open(os.path.join(a.aus, "stichprobe.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("Abdeckung:", json.dumps(cov))
    pin = "PIN bioclip-info-1.sqlite size=%d sha256=%s" % (os.path.getsize(db), sha256(db))
    open(os.path.join(a.aus, "pins.txt"), "w").write(pin + "\n")
    print(pin, "· %d s" % (time.time() - t0))
    if bad:
        print("\n".join("::error::Stichprobe: " + b for b in bad))
        sys.exit(1)


if __name__ == "__main__":
    main()
