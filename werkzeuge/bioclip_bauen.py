#!/usr/bin/env python3
"""BioCLIP-Dateien für «🌿 Bestimmen» im Datentausch (MoveEye Teil 639zzd) bauen – läuft im Workflow «BioCLIP»
(.github/workflows/bioclip.yml) auf einem GitHub-Rechner, nie auf dem Pi und nie beim Integrator (Hugging Face ist von dort
nicht erreichbar, torch ist zu gross).

  python3 werkzeuge/bioclip_bauen.py --aus DIR [--rev HF-COMMIT] [--pflanzen 3500 --tiere 6500 --pilze 1500]

Ergebnis in DIR (alles auch im Protokoll / in der Zusammenfassung des Laufs):
  bioclip-1-bild-int8.onnx   Bild-Teil (ViT-B/16) von BioCLIP 1 als ONNX, Gewichte int8 (dynamisch quantisiert)
  bioclip-1-bild-fp32.onnx   dasselbe in voller Genauigkeit (Rückfall, wenn int8 nicht reicht)
  bioclip-1-arten.npy        Text-Einbettungen der Auswahl (float16, N × 512, normiert) – fertig gerechnet, der Pi braucht den
                             Text-Teil nie
  bioclip-1-arten.json       zu jeder Zeile die Taxonomie (7 Stufen wie TreeOfLife / pybioclip) + Namen (de/fr/it/en, Wikidata
                             CC0) + logit_scale, Vorverarbeitung, Quellen
  pruefung.json              Messung: torch ↔ ONNX (fp32 / int8), Treffer auf echten Fotos (iNaturalist), Zeit pro Bild
  pins.txt                   Grösse + sha256 jeder Datei (für BIO_FILES in Teil 639zzd)

Auswahl der Arten (Entscheid Besitzer: alles – Pflanzen, Tiere, Pilze, Insekten):
  * die in der Schweiz am häufigsten gemeldeten Arten (GBIF.org, Fundmeldungen Land CH, je Reich die obersten N), dazu die
    häufigsten aus Deutschland, Österreich und Liechtenstein (Mitteleuropa), dazu Haustiere, Nutztiere, Garten- und
    Kulturpflanzen (Liste EXTRA unten);
  * nur Arten, die BioCLIP selbst kennt (txt_emb_species.json aus imageomics/bioclip, TreeOfLife-10M): dann sind die
    Einbettungen genau die von pybioclip (txt_emb_species: nur die 7 Stufen der Taxonomie als Text, 80 Vorlagen gemittelt -
    die Gegenprobe im Lauf misst das nach: Kosinus 1.000 für «taxonomic», 0.99 mit Trivialname).
  * Höhere Stufen (Gattung, Familie, Ordnung, Klasse) entstehen auf dem Pi durch Zusammenzählen (wie pybioclip «rank»).
Namen: Wikidata (CC0) – Eigenschaft «Trivialname» (P1843), sonst die Bezeichnung, wenn sie nicht nur der lateinische Name ist.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "MoveEye-bioclip-build/1 (github.com/DonElektro/MotionWatch)"}
HF_REPO = "imageomics/bioclip"
HF_DEMO = "imageomics/bioclip-demo"                # Space: txt_emb_species.npy / .json (wie pybioclip)
RANKS = ("kingdom", "phylum", "class", "order", "family", "genus", "species")
LANGS = ("de", "fr", "it", "en")
GBIF_KINGDOM = {"Plantae": 6, "Animalia": 1, "Fungi": 5}
LAENDER = (("CH", 1.0), ("LI", 1.0), ("DE", 0.35), ("AT", 0.35))     # Gewicht: die Schweiz zuerst

# Haustiere, Nutztiere, Garten-, Zimmer- und Kulturpflanzen (oft wenig gemeldet, aber oft fotografiert)
EXTRA = """
Felis catus; Canis familiaris; Canis lupus; Oryctolagus cuniculus; Cavia porcellus; Mesocricetus auratus; Rattus norvegicus;
Mus musculus; Melopsittacus undulatus; Nymphicus hollandicus; Serinus canaria; Carassius auratus; Equus caballus; Equus asinus;
Bos taurus; Ovis aries; Capra hircus; Sus scrofa; Gallus gallus; Anas platyrhynchos; Anser anser; Meleagris gallopavo;
Columba livia; Lama glama; Vicugna pacos; Apis mellifera; Bombyx mori; Testudo hermanni; Pogona vitticeps;
Solanum lycopersicum; Solanum tuberosum; Capsicum annuum; Cucumis sativus; Cucurbita pepo; Cucurbita maxima; Daucus carota;
Brassica oleracea; Brassica napus; Brassica rapa; Lactuca sativa; Spinacia oleracea; Beta vulgaris; Allium cepa; Allium sativum;
Allium porrum; Allium schoenoprasum; Phaseolus vulgaris; Pisum sativum; Vicia faba; Zea mays; Triticum aestivum; Hordeum vulgare;
Secale cereale; Avena sativa; Helianthus annuus; Fragaria ananassa; Rubus idaeus; Ribes rubrum; Ribes nigrum; Ribes uva-crispa;
Vaccinium corymbosum; Malus domestica; Pyrus communis; Prunus avium; Prunus cerasus; Prunus domestica; Prunus persica;
Prunus armeniaca; Juglans regia; Corylus avellana; Castanea sativa; Vitis vinifera; Ficus carica; Olea europaea; Citrus limon;
Ocimum basilicum; Petroselinum crispum; Salvia officinalis; Salvia rosmarinus; Thymus vulgaris; Mentha spicata; Mentha piperita;
Origanum vulgare; Lavandula angustifolia; Anethum graveolens; Coriandrum sativum; Levisticum officinale; Rheum rhabarbarum;
Rosa canina; Rosa gallica; Tulipa gesneriana; Narcissus pseudonarcissus; Hyacinthus orientalis; Crocus vernus; Iris germanica;
Paeonia lactiflora; Dahlia pinnata; Tagetes erecta; Calendula officinalis; Petunia hybrida; Pelargonium zonale; Begonia semperflorens;
Impatiens walleriana; Viola tricolor; Viola wittrockiana; Hydrangea macrophylla; Buxus sempervirens; Thuja occidentalis;
Prunus laurocerasus; Forsythia suspensa; Syringa vulgaris; Philadelphus coronarius; Buddleja davidii; Rhododendron ponticum;
Hibiscus syriacus; Clematis vitalba; Wisteria sinensis; Hedera helix; Lonicera periclymenum; Lilium candidum; Hemerocallis fulva;
Echinacea purpurea; Rudbeckia hirta; Cosmos bipinnatus; Zinnia elegans; Antirrhinum majus; Digitalis purpurea; Lupinus polyphyllus;
Alcea rosea; Monstera deliciosa; Ficus benjamina; Ficus elastica; Epipremnum aureum; Spathiphyllum wallisii; Dracaena trifasciata;
Chlorophytum comosum; Aloe vera; Phalaenopsis amabilis; Euphorbia pulcherrima; Schlumbergera truncata; Crassula ovata;
Zamioculcas zamiifolia; Kalanchoe blossfeldiana; Cyclamen persicum; Saintpaulia ionantha; Hippeastrum puniceum
"""

# Testbilder für die echte Prüfung (Fotos «research grade» mit freier Lizenz von iNaturalist, nur im Lauf, nie verteilt)
PRUEF_ARTEN = (
    "Taraxacum officinale", "Bellis perennis", "Leucanthemum vulgare", "Papaver rhoeas", "Trifolium pratense", "Urtica dioica",
    "Fagus sylvatica", "Picea abies", "Galanthus nivalis", "Digitalis purpurea", "Solanum lycopersicum", "Helianthus annuus",
    "Vulpes vulpes", "Capreolus capreolus", "Erinaceus europaeus", "Sciurus vulgaris", "Meles meles", "Felis catus",
    "Canis familiaris", "Turdus merula", "Erithacus rubecula", "Parus major", "Pica pica", "Ardea cinerea", "Bufo bufo",
    "Salamandra salamandra", "Coccinella septempunctata", "Aglais io", "Vanessa atalanta", "Apis mellifera", "Bombus terrestris",
    "Pyrrhocoris apterus", "Lucanus cervus", "Araneus diadematus", "Helix pomatia", "Amanita muscaria", "Boletus edulis",
    "Cantharellus cibarius", "Fomes fomentarius", "Lycoperdon perlatum")


def get(url, data=None, headers=None, timeout=60, tries=5):
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=data, headers=dict(UA, **(headers or {})))
            with urllib.request.urlopen(r, timeout=timeout) as f:
                return f.read()
        except Exception as e:                                  # GBIF / Wikidata: kurz warten und nochmals
            if i == tries - 1:
                raise
            print("  … nochmals (%s): %s" % (e.__class__.__name__, url[:120]), flush=True)
            time.sleep(3 * (i + 1))


def getj(url, **k):
    return json.loads(get(url, **k).decode("utf-8"))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---- 1. BioCLIP von Hugging Face (feste Revision) ---------------------------------------------------------------------------
def hf_holen(rev, ziel, demo_rev=""):
    """Gewichte aus imageomics/bioclip (Modell, MIT), die fertigen Arten-Einbettungen von pybioclip aus dem Space
    imageomics/bioclip-demo (dort holt sie auch pybioclip: txt_emb_species.npy / .json) - beide mit fester Revision"""
    from huggingface_hub import HfApi, hf_hub_download
    api = HfApi()
    info = api.model_info(HF_REPO, revision=rev or None, files_metadata=True)
    rev = info.sha
    files = {s.rfilename: s.size for s in info.siblings}
    print("Hugging Face %s @ %s, Lizenz %s" % (HF_REPO, rev, (info.card_data or {}).get("license") if info.card_data else "?"))
    for n, s in sorted(files.items()):
        print("  %-40s %s" % (n, s))
    w = next((n for n in ("open_clip_model.safetensors", "open_clip_pytorch_model.bin") if n in files), None)
    if not w or "open_clip_config.json" not in files:
        sys.exit("keine open_clip-Gewichte im Repository")
    out = {n: hf_hub_download(HF_REPO, n, revision=rev, cache_dir=ziel) for n in ("open_clip_config.json", w)}
    sp = api.space_info(HF_DEMO, revision=demo_rev or None, files_metadata=True)
    demo_rev = sp.sha
    sfiles = {s.rfilename: s.size for s in sp.siblings}
    print("Hugging Face Space %s @ %s, Lizenz %s" % (HF_DEMO, demo_rev, (sp.card_data or {}).get("license") if sp.card_data else "?"))
    for n, s in sorted(sfiles.items()):
        if n.endswith((".npy", ".json", ".py", ".md", ".txt")):
            print("  %-40s %s" % (n, s))
    for n in ("txt_emb_species.npy", "txt_emb_species.json"):
        cand = [x for x in sfiles if x == n or x.endswith("/" + n)]
        if not cand:
            sys.exit("fehlt im Space: " + n)
        out[n] = hf_hub_download(HF_DEMO, cand[0], revision=demo_rev, repo_type="space", cache_dir=ziel)
    return rev, demo_rev, out, w


def txt_emb(model, tok, texte):
    """wie pybioclip get_txt_emb: jede der 80 OpenAI-Vorlagen, normiert, gemittelt, wieder normiert"""
    import torch
    from open_clip.zero_shot_metadata import OPENAI_IMAGENET_TEMPLATES as TPL
    out = []
    with torch.no_grad():
        for t in texte:
            e = model.encode_text(tok([f(t) for f in TPL]))
            e = torch.nn.functional.normalize(e, dim=-1).mean(dim=0)
            out.append((e / e.norm()).numpy())
    return out


def modell_laden(paths, wname):
    import open_clip
    cfg = json.load(open(paths["open_clip_config.json"]))
    mc, pc = cfg["model_cfg"], cfg.get("preprocess_cfg", {})
    print("model_cfg:", json.dumps(mc)[:300]); print("preprocess_cfg:", pc)
    model, _, pre = open_clip.create_model_and_transforms("ViT-B-16", pretrained=paths[wname], **{
        k: v for k, v in (("image_mean", pc.get("mean")), ("image_std", pc.get("std"))) if v})
    model.eval()
    print("Vorverarbeitung (torch):", pre)
    return model, pre, pc


# ---- 2. Auswahl: GBIF-Fundmeldungen, Schnittmenge mit TreeOfLife --------------------------------------------------------------
def gbif_top(land, reich, n):
    out, off = [], 0
    while len(out) < n:
        lim = min(1000, n - len(out))
        j = getj("https://api.gbif.org/v1/occurrence/search?" + urllib.parse.urlencode(
            {"country": land, "kingdomKey": GBIF_KINGDOM[reich], "facet": "speciesKey", "facetLimit": lim, "facetOffset": off, "limit": 0}))
        c = (j.get("facets") or [{}])[0].get("counts") or []
        out += [(int(x["name"]), int(x["count"])) for x in c]
        if len(c) < lim:
            break
        off += lim
    return out


def gbif_name(key):
    try:
        j = getj("https://api.gbif.org/v1/species/%d" % key, timeout=30)
    except Exception:
        return key, None
    n = j.get("canonicalName") or ""
    return key, n if j.get("rank") == "SPECIES" and re.fullmatch(r"[A-Z][a-z-]+ [a-z-]+", n) else None


def auswahl(n_reich):
    score, reich_of = {}, {}
    for land, w in LAENDER:
        for reich, n in n_reich.items():
            m = n if land == "CH" else max(200, int(n * 0.3))
            lst = gbif_top(land, reich, m)
            print("GBIF %s %s: %d Arten" % (land, reich, len(lst)), flush=True)
            for rank_, (k, c) in enumerate(lst):
                score[k] = score.get(k, 0.0) + w * (1.0 - rank_ / max(1, len(lst)))
                reich_of[k] = reich
    keys = sorted(score, key=lambda k: -score[k])
    names = {}
    with cf.ThreadPoolExecutor(16) as ex:
        for k, n in ex.map(gbif_name, keys):
            if n:
                names[k] = n
    order = []
    seen = set()
    for k in keys:
        n = names.get(k)
        if n and n not in seen:
            seen.add(n); order.append((n, reich_of[k], score[k]))
    return order


def tol_index(names_json):
    """«Gattung art» -> Zeilen in txt_emb_species (TreeOfLife-Taxonomie, Reihenfolge wie pybioclip)"""
    T = json.load(open(names_json))
    idx = {}
    for i, e in enumerate(T):
        tax = e[0] if isinstance(e, (list, tuple)) and e and isinstance(e[0], (list, tuple)) else e
        if not isinstance(tax, (list, tuple)) or len(tax) < 7:
            continue
        g, s = str(tax[5] or ""), str(tax[6] or "")
        if g and s:
            idx.setdefault((g + " " + s).strip(), []).append(i)
    print("TreeOfLife: %d Einträge, %d Binomiale" % (len(T), len(idx)))
    print("  Beispiel:", T[0])
    return T, idx


# ---- 3. Namen aus Wikidata (CC0) ----------------------------------------------------------------------------------------------
def wikidata(names):
    out = {}
    lst = sorted(set(names))
    for i in range(0, len(lst), 150):
        part = lst[i:i + 150]
        vals = " ".join('"%s"' % n.replace('"', "") for n in part)
        q = ("SELECT ?name ?l ?src ?txt WHERE { VALUES ?name { %s } ?it wdt:P225 ?name . "
             "{ ?it wdt:P1843 ?txt . BIND(\"c\" AS ?src) } UNION { ?it rdfs:label ?txt . BIND(\"l\" AS ?src) } "
             "BIND(LANG(?txt) AS ?l) FILTER(?l IN (\"de\",\"de-ch\",\"fr\",\"it\",\"en\",\"en-gb\")) }" % vals)
        try:
            j = getj("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}), timeout=120)
        except Exception as e:
            print("  Wikidata Teil %d: %s" % (i, e)); continue
        for b in j["results"]["bindings"]:
            n, L, src, t = b["name"]["value"], b["l"]["value"][:2], b["src"]["value"], b["txt"]["value"].strip()
            if not t or t.lower() == n.lower() or n.lower() in t.lower() or len(t) > 60:
                continue
            d = out.setdefault(n, {})
            cur = d.get(L)
            # Trivialname (P1843) vor Bezeichnung; in Deutsch «de» vor «de-ch»; sonst der kürzere
            k = (0 if src == "c" else 1, 0 if b["l"]["value"] in ("de", "fr", "it", "en") else 1, len(t))
            if cur is None or k < cur[1]:
                d[L] = (t, k)
        time.sleep(0.6)
        if i % 1500 == 0:
            print("  Wikidata %d / %d" % (i, len(lst)), flush=True)
    return {n: {L: v[0][:1].upper() + v[0][1:] if L == "de" else v[0] for L, v in d.items()} for n, d in out.items()}


# ---- 4. ONNX ------------------------------------------------------------------------------------------------------------------
def onnx_export(model, ziel):
    import torch
    from onnxruntime.quantization import QuantType, quantize_dynamic

    class Bild(torch.nn.Module):
        def __init__(self, v):
            super().__init__(); self.v = v

        def forward(self, image):
            return self.v(image)
    fp32 = os.path.join(ziel, "bioclip-1-bild-fp32.onnx")
    int8 = os.path.join(ziel, "bioclip-1-bild-int8.onnx")
    from torch.onnx import utils as onnx_utils               # der klassische TorchScript-Export (ohne onnxscript)
    onnx_utils.export(Bild(model.visual), torch.randn(1, 3, 224, 224), fp32, input_names=["image"], output_names=["emb"],
                      dynamic_axes={"image": {0: "n"}, "emb": {0: "n"}}, opset_version=17, do_constant_folding=True)
    # nur MatMul / Gemm: ConvInteger (der eine Patch-Conv) hat in onnxruntime für die CPU keinen Kern
    quantize_dynamic(fp32, int8, weight_type=QuantType.QInt8, per_channel=True, op_types_to_quantize=["MatMul", "Gemm"])
    import numpy as np
    import onnxruntime as ort
    x = np.random.RandomState(1).normal(size=(1, 3, 224, 224)).astype(np.float32)
    with torch.no_grad():
        ref = Bild(model.visual)(torch.from_numpy(x)).numpy()[0]
    for p in (fp32, int8):                                   # gleich laden und rechnen: ein Fehler zeigt sich hier
        e = ort.InferenceSession(p, providers=["CPUExecutionProvider"]).run(None, {"image": x})[0][0]
        print("  %s: Kosinus zu torch %.5f" % (os.path.basename(p), float(e @ ref / np.linalg.norm(e) / np.linalg.norm(ref))), flush=True)
    return fp32, int8


def cv2_vor(img_bgr, size, mean, std, interp):
    """genau wie BIOCLIP_WORKER in Teil 639zzd: kürzere Seite auf 224, Mitte ausschneiden, RGB, normieren"""
    import cv2
    import numpy as np
    h, w = img_bgr.shape[:2]
    s = size / float(min(h, w))
    nw, nh = max(size, round(w * s)), max(size, round(h * s))
    im = cv2.resize(img_bgr, (nw, nh), interpolation=interp)
    y, x = (nh - size) // 2, (nw - size) // 2
    im = im[y:y + size, x:x + size, ::-1].astype(np.float32) / 255.0
    im = (im - np.array(mean, np.float32)) / np.array(std, np.float32)
    return im.transpose(2, 0, 1)[None].copy()


def inat_fotos(art, n=2):
    q = urllib.parse.urlencode({"taxon_name": art, "quality_grade": "research", "photos": "true", "per_page": 12,
                                "photo_license": "cc0,cc-by", "order_by": "votes", "locale": "en"})
    try:
        j = getj("https://api.inaturalist.org/v1/observations?" + q, timeout=60)
    except Exception as e:
        print("  iNaturalist %s: %s" % (art, e)); return []
    out = []
    for o in j.get("results") or []:
        if ((o.get("taxon") or {}).get("name") or "") != art:
            continue
        for ph in o.get("photos") or []:
            u = (ph.get("url") or "").replace("square", "medium")
            if u:
                out.append(u); break
        if len(out) >= n:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aus", required=True)
    ap.add_argument("--rev", default="")
    ap.add_argument("--demo-rev", default="")
    ap.add_argument("--pflanzen", type=int, default=3500)
    ap.add_argument("--tiere", type=int, default=6500)
    ap.add_argument("--pilze", type=int, default=1500)
    ap.add_argument("--fotos", type=int, default=2, help="echte Fotos pro Prüf-Art (0 = keine Prüfung mit Fotos)")
    a = ap.parse_args()
    import numpy as np
    import torch
    torch.set_num_threads(4)
    os.makedirs(a.aus, exist_ok=True)
    cache = os.path.join(os.path.dirname(os.path.abspath(a.aus)), "hf_cache")
    t0 = time.time()
    rev, demo_rev, paths, wname = hf_holen(a.rev, cache, a.demo_rev)
    model, pre, pc = modell_laden(paths, wname)
    scale = float(model.logit_scale.exp().item())
    print("logit_scale.exp() = %.4f" % scale)
    fp32, int8 = onnx_export(model, a.aus)                    # zuerst: ein Fehler hier zeigt sich nach Minuten
    print("ONNX: fp32 %d Bytes, int8 %d Bytes" % (os.path.getsize(fp32), os.path.getsize(int8)), flush=True)

    # Text-Einbettungen von BioCLIP (pybioclip-Format) und die Auswahl
    E = np.load(paths["txt_emb_species.npy"], mmap_mode="r")
    print("txt_emb_species.npy:", E.shape, E.dtype)
    T, idx = tol_index(paths["txt_emb_species.json"])
    by_col = E.shape[0] == 512 and E.shape[1] == len(T)
    if not by_col and not (E.shape[1] == 512 and E.shape[0] == len(T)):
        sys.exit("unerwartete Form der Einbettungen %s für %d Namen" % (E.shape, len(T)))
    order = auswahl({"Plantae": a.pflanzen, "Animalia": a.tiere, "Fungi": a.pilze})
    extra = [x.strip() for x in EXTRA.replace("\n", " ").split(";") if x.strip()]
    rows, picked, miss = [], [], []
    for n in extra + [o[0] for o in order]:
        if n in picked:
            continue
        r = idx.get(n)
        if not r:
            miss.append(n); continue
        picked.append(n); rows.append(r[0])
    print("Auswahl: %d Arten (GBIF-Kandidaten %d, Zusatz %d, ohne BioCLIP-Eintrag %d, z. B. %s)"
          % (len(picked), len(order), len(extra), len(miss), ", ".join(miss[:12])))
    M = np.asarray(E[:, rows].T if by_col else E[rows], dtype=np.float32)
    M /= np.linalg.norm(M, axis=1, keepdims=True)
    taxa = []
    for r in rows:
        e = T[r]
        tax = list(e[0] if isinstance(e[0], (list, tuple)) else e)[:7]
        taxa.append([str(x or "") for x in tax])
    # Gegenprobe: dieselben Einbettungen mit dem Text-Teil selbst rechnen (Format wie pybioclip) – und so die Zusatz-Arten
    # ergänzen, die TreeOfLife nicht kennt (Taxonomie dann vom GBIF-Backbone, englischer Name von Wikidata)
    import open_clip
    tok = open_clip.get_tokenizer("ViT-B-16")
    fmts = {"taxonomic + common": lambda tx, c: " ".join(tx) + (" with common name " + c if c else ""),
            "taxonomic": lambda tx, c: " ".join(tx), "common": lambda tx, c: c or " ".join(tx)}
    probe = [n for n in ("Vulpes vulpes", "Taraxacum officinale", "Turdus merula", "Amanita muscaria", "Apis mellifera",
                         "Felis catus", "Fagus sylvatica", "Coccinella septempunctata") if n in idx]
    best, best_c = "taxonomic + common", -1.0
    fmt_cos = {}
    for fn, f in fmts.items():
        cs = []
        for n in probe:
            e = T[idx[n][0]]
            tx, com = [str(x or "") for x in e[0]][:7], str(e[1] or "") if len(e) > 1 else ""
            v = txt_emb(model, tok, [f(tx, com)])[0]
            d = np.asarray(E[:, idx[n][0]] if by_col else E[idx[n][0]], dtype=np.float32)
            cs.append(float(v @ (d / np.linalg.norm(d))))
        fmt_cos[fn] = round(sum(cs) / max(1, len(cs)), 4)
        if fmt_cos[fn] > best_c:
            best, best_c = fn, fmt_cos[fn]
    print("Gegenprobe Text-Format (Kosinus zu den pybioclip-Einbettungen):", fmt_cos, "->", best)
    add = [n for n in miss if n in extra]
    own = []
    if add and best_c > 0.98:
        en = wikidata(add)
        for n in add:
            try:
                j = getj("https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": n, "strict": "true"}))
            except Exception:
                continue
            if j.get("rank") != "SPECIES" or j.get("matchType") not in ("EXACT",) or not all(j.get(k) for k in RANKS[:6]):
                continue
            tx = [j[k] for k in RANKS[:6]] + [n.split(" ", 1)[1]]
            own.append((n, tx, (en.get(n) or {}).get("en", "")))
        vecs = txt_emb(model, tok, [fmts[best](tx, c) for _n, tx, c in own])
        for (n, tx, c), v in zip(own, vecs):
            picked.append(n); taxa.append(tx)
        if own:
            M = np.vstack([M, np.asarray(vecs, dtype=np.float32)])
    print("Zusatz-Arten selbst gerechnet (nicht in TreeOfLife): %d %s" % (len(own), ", ".join(n for n, _t, _c in own[:20])))
    higher = set()
    for t in taxa:
        higher.update(x for x in t[:6] if x)
    print("Namen aus Wikidata: %d Arten + %d höhere Stufen …" % (len(picked), len(higher)), flush=True)
    names = wikidata(picked + sorted(higher))
    nde = sum(1 for n in picked if "de" in names.get(n, {}))
    print("deutsche Namen: %d von %d Arten (%.0f %%)" % (nde, len(picked), 100.0 * nde / max(1, len(picked))))
    np.save(os.path.join(a.aus, "bioclip-1-arten.npy"), M.astype(np.float16))
    meta = {"format": 1, "model": "BioCLIP 1 (imageomics/bioclip, ViT-B/16, MIT)", "hf_rev": rev, "demo_rev": demo_rev,
            "text_format": best, "text_format_cos": fmt_cos, "own": [n for n, _t, _c in own], "logit_scale": round(scale, 4),
            "ranks": list(RANKS), "size": 224, "mean": list(pc.get("mean") or (0.48145466, 0.4578275, 0.40821073)),
            "std": list(pc.get("std") or (0.26862954, 0.26130258, 0.27577711)), "n": len(taxa), "taxa": taxa,
            "names": {k: v for k, v in names.items() if v},
            "built": time.strftime("%Y-%m-%d"),
            "sources": {"model": "BioCLIP (Stevens et al., CVPR 2024), huggingface.co/imageomics/bioclip, MIT",
                        "embeddings": "txt_emb_species.npy/.json as used by pybioclip (Space imageomics/bioclip-demo, TreeOfLife-10M taxonomy); extra species computed with the BioCLIP text encoder, taxonomy GBIF Backbone (CC BY 4.0)",
                        "selection": "most reported species in CH/LI (and DE/AT) after occurrence counts on GBIF.org, plus pets, farm animals, garden and crop plants",
                        "names": "Wikidata (CC0), taxon common name P1843 / labels"}}
    with open(os.path.join(a.aus, "bioclip-1-arten.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))

    # Prüfung
    import cv2
    import onnxruntime as ort
    from PIL import Image
    so = ort.SessionOptions(); so.intra_op_num_threads = 4
    S = {k: ort.InferenceSession(p, so, providers=["CPUExecutionProvider"]) for k, p in (("fp32", fp32), ("int8", int8))}
    imgs = []
    tmpd = os.path.join(os.path.dirname(os.path.abspath(a.aus)), "fotos")
    os.makedirs(tmpd, exist_ok=True)
    if a.fotos:
        for art in PRUEF_ARTEN:
            for j_, u in enumerate(inat_fotos(art, a.fotos)):
                try:
                    p = os.path.join(tmpd, "%s_%d.jpg" % (art.replace(" ", "_"), j_))
                    open(p, "wb").write(get(u, timeout=60))
                    imgs.append((art, p))
                except Exception as e:
                    print("  Foto %s: %s" % (art, e))
            time.sleep(1.1)                                     # iNaturalist: höchstens ~1 Anfrage pro Sekunde
    print("Prüf-Fotos: %d" % len(imgs))
    sel_idx = {n: i for i, n in enumerate(picked)}
    res = {"n_img": len(imgs), "cos": {}, "top1": {}, "top3": {}, "agree_int8_fp32": 0, "ms": {}, "fehlt_in_auswahl": []}
    hit = {k: [0, 0] for k in ("torch", "fp32_area", "fp32_cubic", "int8_area")}
    cos = {k: [] for k in ("fp32_area", "fp32_cubic", "int8_area", "torch_vs_onnx_same_input")}
    agree = 0
    zeilen = []
    for art, p in imgs:
        if art not in sel_idx:
            res["fehlt_in_auswahl"].append(art)
        pil = Image.open(p).convert("RGB")
        with torch.no_grad():
            x = pre(pil).unsqueeze(0)
            et = model.encode_image(x).numpy()[0]
        e_same = S["fp32"].run(None, {"image": x.numpy()})[0][0]
        bgr = cv2.imread(p, cv2.IMREAD_COLOR)
        embs = {"torch": et,
                "fp32_area": S["fp32"].run(None, {"image": cv2_vor(bgr, 224, meta["mean"], meta["std"], cv2.INTER_AREA)})[0][0],
                "fp32_cubic": S["fp32"].run(None, {"image": cv2_vor(bgr, 224, meta["mean"], meta["std"], cv2.INTER_CUBIC)})[0][0],
                "int8_area": S["int8"].run(None, {"image": cv2_vor(bgr, 224, meta["mean"], meta["std"], cv2.INTER_AREA)})[0][0]}
        nt = et / np.linalg.norm(et)
        cos["torch_vs_onnx_same_input"].append(float(nt @ (e_same / np.linalg.norm(e_same))))
        tops = {}
        for k, e in embs.items():
            e = e / np.linalg.norm(e)
            if k != "torch":
                cos[k].append(float(nt @ e))
            lg = scale * (M @ e)
            pr = np.exp(lg - lg.max()); pr /= pr.sum()
            top = list(np.argsort(-pr)[:3])
            tops[k] = top
            hit[k][0] += int(picked[top[0]] == art); hit[k][1] += int(art in [picked[i] for i in top])
        agree += int(tops["int8_area"][0] == tops["fp32_area"][0])
        zeilen.append("%-28s torch: %-28s int8: %-28s %s" % (art, picked[tops["torch"][0]], picked[tops["int8_area"][0]],
                                                              "✓" if picked[tops["int8_area"][0]] == art else ""))
    print("\n".join(zeilen))
    n = max(1, len(imgs))
    res["cos"] = {k: (round(min(v), 4) if v else None, round(sum(v) / max(1, len(v)), 4) if v else None) for k, v in cos.items()}
    res["top1"] = {k: round(v[0] / n, 3) for k, v in hit.items()}
    res["top3"] = {k: round(v[1] / n, 3) for k, v in hit.items()}
    res["agree_int8_fp32"] = round(agree / n, 3)
    # Zeit pro Bild (dieser Rechner; der Pi 5 ist etwa 3–5 × langsamer)
    x = cv2_vor(np.full((480, 640, 3), 120, np.uint8), 224, meta["mean"], meta["std"], cv2.INTER_AREA)
    for k, p in (("fp32", fp32), ("int8", int8)):
        for th in (2, 4):
            so2 = ort.SessionOptions(); so2.intra_op_num_threads = th; so2.inter_op_num_threads = 1
            t1 = time.time(); s2 = ort.InferenceSession(p, so2, providers=["CPUExecutionProvider"]); tl = time.time() - t1
            s2.run(None, {"image": x})
            t1 = time.time()
            for _ in range(5):
                s2.run(None, {"image": x})
            res["ms"]["%s_%dthreads" % (k, th)] = {"load_ms": int(tl * 1000), "run_ms": int((time.time() - t1) / 5 * 1000)}
    res["n_arten"] = len(picked); res["n_de"] = nde; res["hf_rev"] = rev; res["demo_rev"] = demo_rev; res["text_format_cos"] = fmt_cos; res["sekunden"] = int(time.time() - t0)
    with open(os.path.join(a.aus, "pruefung.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    pins = []
    for fn in ("bioclip-1-bild-int8.onnx", "bioclip-1-bild-fp32.onnx", "bioclip-1-arten.npy", "bioclip-1-arten.json"):
        p = os.path.join(a.aus, fn)
        pins.append("PIN %s size=%d sha256=%s" % (fn, os.path.getsize(p), sha256(p)))
    open(os.path.join(a.aus, "pins.txt"), "w").write("\n".join(pins) + "\n")
    print("\n".join(pins))


if __name__ == "__main__":
    main()
