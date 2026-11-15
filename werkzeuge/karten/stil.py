#!/usr/bin/env python3
"""MoveEye: the four map styles of the offline map (part 639zzq) from the Protomaps style «light» (paket.py --web).

  style.json            Standard hell   (Protomaps «light», unchanged)
  style_dark.json       Standard dunkel (the same layers, colours chosen by hand for the dark pages of MoveEye)
  style_topo.json       Topo hell       (Standard + relief, contour lines, rock / glacier / forest like the Swiss maps,
                                         hiking paths yellow / red / blue from OpenStreetMap, peaks with height)
  style_topo_dark.json  Topo dunkel

Only pure Python on the style JSON (no node, no network): the same input gives the same bytes. The sources «topo»
(vector: layers «contour» and «wege») and «relief» (raster-dem, terrarium) carry placeholders like «protomaps»; MoveEye
puts its own addresses in (KQ_HEAD_JS, part 639zzq).

  python3 -I werkzeuge/karten/stil.py style.json OUTDIR       # writes the four files (for a look at them)
"""
import copy
import json
import re
import sys

# ---- colours ---------------------------------------------------------------------------------------------------------------------
# Topo light: the paper and the colours of the Swiss national maps (forest green, rock grey, glacier blue, brown contours)
HELL = {
    "paper": "#f6f4ee", "water": "#a9d3f0", "water_line": "#3f8fd2", "water_text": "#2b6cb0",
    "forest": "#c8dfaa", "wood": "#c8dfaa", "scrub": "#dce9c4", "grass": "#eef2de", "park": "#d7e7c2", "glacier": "#e8f3fb",
    "glacier_line": "#77acd8", "rock": "#e6e2db", "sand": "#efe8cf", "urban": "#ece8e0", "military": "#e4e1da",
    "building": "#77726b", "casing": "#bdb6aa", "road": "#ffffff", "road_minor": "#fbfaf7", "highway": "#f6d58a",
    "highway_casing": "#c49a3c", "rail": "#3b3b3b", "boundary": "#a0619d",
    "contour": "#b48b55", "contour_index": "#a57a45", "contour_glacier": "#5e9fd6", "contour_text": "#97703f",
    "contour_text_glacier": "#3b7fc0", "cliff": "#5a564f", "path": "#8c7d6a",
    "weg1": "#e3a800", "weg2": "#d83a22", "weg3": "#2b63d0", "weg_casing": "#ffffff", "weg1_casing": "#7a5c00",
    "text": "#3a352d", "text_minor": "#6b6457", "halo": "#f6f4ee", "peak": "#3d3528",
    "shadow": "#465472", "highlight": "#fffdf6", "accent": "#7a6c58", "relief": 0.42,
}
# Topo dark: chosen by hand (not mapped automatically) - dark slate, muted green / grey, glaciers in a cool blue, the hiking
# colours bright enough for the night
DUNKEL = {
    "paper": "#1d2125", "water": "#1c3a54", "water_line": "#3d7fb8", "water_text": "#8cc0ea",
    "forest": "#22322a", "wood": "#22322a", "scrub": "#26302a", "grass": "#21272a", "park": "#24302a", "glacier": "#2a3b4a",
    "glacier_line": "#5b8fbd", "rock": "#2c2c2d", "sand": "#2e2b24", "urban": "#24272b", "military": "#25272a",
    "building": "#4b5058", "casing": "#121518", "road": "#3d434b", "road_minor": "#363b42", "highway": "#6c5a37",
    "highway_casing": "#121518", "rail": "#8b9097", "boundary": "#a77aa4",
    "contour": "#8a6e4e", "contour_index": "#9d7d58", "contour_glacier": "#5b90c2", "contour_text": "#b2946f",
    "contour_text_glacier": "#86b6e2", "cliff": "#a59f95", "path": "#7d746a",
    "weg1": "#f2c230", "weg2": "#ff6b55", "weg3": "#6ea8ff", "weg_casing": "#15181b", "weg1_casing": "#15181b",
    "text": "#dfe3e8", "text_minor": "#a9b0b8", "halo": "#16191c", "peak": "#e6dccb",
    "shadow": "#000000", "highlight": "rgba(160,176,198,0.30)", "accent": "rgba(0,0,0,0.25)", "relief": 0.45,
}
# Standard dark: the Protomaps layers with dark colours (layer id -> paint)
STD_DUNKEL = {
    "background": {"background-color": "#16191c"}, "earth": {"fill-color": "#1f2327"},
    "landuse_urban_green": {"fill-color": "#22302a"}, "landuse_hospital": {"fill-color": "#2b2526"},
    "landuse_industrial": {"fill-color": "#22272c"}, "landuse_school": {"fill-color": "#28262a"},
    "landuse_beach": {"fill-color": "#2c2a24"}, "landuse_zoo": {"fill-color": "#232b2b"},
    "landuse_aerodrome": {"fill-color": "#25272b"}, "landuse_runway": {"fill-color": "#33363b"},
    "roads_runway": {"line-color": "#33363b"}, "roads_taxiway": {"line-color": "#33363b"},
    "water": {"fill-color": "#1c3a54"}, "water_stream": {"line-color": "#2f6796"}, "water_river": {"line-color": "#2f6796"},
    "landuse_pedestrian": {"fill-color": "#25282c"}, "landuse_pier": {"fill-color": "#2b2e33"},
    "buildings": {"fill-color": "#3a3f46"}, "roads_rail": {"line-color": "#6f757d"},
    "boundaries_country": {"line-color": "#7d6a86"}, "boundaries": {"line-color": "#5c5463"},
}

TOPO_ATTR = "© swisstopo"


def _layer(s, lid):
    for i, l in enumerate(s["layers"]):
        if l["id"] == lid:
            return i, l
    return None, None


def _parse(c):
    m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", c)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(x * 2 for x in h)
        return [int(h[i:i + 2], 16) for i in (0, 2, 4)], 1.0
    m = re.fullmatch(r"rgba?\(([^)]*)\)", c)
    if m:
        p = [float(x) for x in m.group(1).split(",")]
        return [int(v) for v in p[:3]], (p[3] if len(p) > 3 else 1.0)
    return None


def _hex(rgb, a=1.0):
    r, g, b = (max(0, min(255, int(round(v)))) for v in rgb)
    return "#%02x%02x%02x" % (r, g, b) if a >= 0.999 else "rgba(%d,%d,%d,%.2f)" % (r, g, b, a)


def _dark_of(c, kind):
    """a colour of the light style for the dark one (only for what the tables do not name): luminance turned around,
    a little of the hue kept"""
    p = _parse(c) if isinstance(c, str) else None
    if not p:
        return c
    (r, g, b), a = p
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    if kind == "text":
        t = 0.62 + 0.30 * (1 - lum)
        return _hex([0.55 * 255 * t + 0.45 * v * t for v in (r, g, b)], a)
    if kind == "halo":
        return "#16191c"
    t = 0.10 + 0.22 * (1 - lum) + 0.10 * lum
    return _hex([35 + (v - 128) * 0.18 + 60 * t for v in (r, g, b)], a)


def _walk(v, kind):
    if isinstance(v, str):
        return _dark_of(v, kind)
    if isinstance(v, list):
        return [_walk(x, kind) for x in v]
    return v


def _darken_rest(s, done):
    """every colour the tables did not set: text light, halos dark, fills and lines dark"""
    for l in s["layers"]:
        p = l.get("paint") or {}
        for k in list(p):
            if not k.endswith("color") or (l["id"], k) in done:
                continue
            kind = "text" if k in ("text-color", "icon-color") else "halo" if k.endswith("halo-color") else "fill"
            p[k] = _walk(p[k], kind)


def standard_dunkel(light):
    s = copy.deepcopy(light)
    s["name"] = "MoveEye Offline-Karte Schweiz (Standard dunkel)"
    s["sprite"] = "{SPRITE}dark"
    done = set()
    for lid, paint in STD_DUNKEL.items():
        _, l = _layer(s, lid)
        if l:
            l.setdefault("paint", {}).update(copy.deepcopy(paint))
            done |= {(lid, k) for k in paint}
    _, l = _layer(s, "landuse_park")
    if l:
        l["paint"]["fill-color"] = _kind_colors({"forest": "#22322a", "wood": "#22322a", "scrub": "#26302a", "grass": "#24302a",
                                                 "park": "#24302a", "glacier": "#2a3b4a", "sand": "#2e2b24", "military": "#25272a"}, "#1f2327")
        done.add(("landuse_park", "fill-color"))
    for l in s["layers"]:                                   # roads: dark grey, casings darker
        if l["type"] == "line" and l.get("source-layer") == "roads" and l["id"] not in ("roads_rail",):
            col = "#121518" if "casing" in l["id"] else "#5b5240" if "highway" in l["id"] and "casing" not in l["id"] else \
                "#40464e" if "major" in l["id"] else "#33383f"
            l["paint"]["line-color"] = col
            done.add((l["id"], "line-color"))
    _darken_rest(s, done)
    return s


def _kind_colors(m, other):
    """fill colour per «kind» of the Protomaps layer landuse"""
    groups = {"forest": ["forest", "national_park", "nature_reserve", "protected_area"], "wood": ["wood"], "scrub": ["scrub", "heath"],
              "grass": ["grass", "grassland", "meadow", "golf_course"], "park": ["park", "cemetery", "garden"], "glacier": ["glacier"],
              "sand": ["sand", "beach"], "military": ["military", "naval_base", "airfield"]}
    ex = ["match", ["get", "kind"]]
    for g, kinds in groups.items():
        if g in m:
            ex += [kinds, m[g]]
    return ex + [other]


def topo(light, dunkel=False):
    """Standard (light) + relief, contour lines, landcover, cliffs, hiking paths and peaks; dunkel=True: the dark one"""
    P = DUNKEL if dunkel else HELL
    s = standard_dunkel(light) if dunkel else copy.deepcopy(light)
    s["name"] = "MoveEye Offline-Karte Schweiz (Topo %s)" % ("dunkel" if dunkel else "hell")
    s["sources"]["topo"] = {"type": "vector", "tiles": ["{TOPO}"], "minzoom": 11, "maxzoom": 14, "attribution": "{ATTR}"}
    s["sources"]["relief"] = {"type": "raster-dem", "tiles": ["{RELIEF}"], "tileSize": 256, "encoding": "terrarium", "minzoom": 8,
                              "maxzoom": 13, "attribution": "{ATTR}"}
    L = s["layers"]

    def paint(lid, **kw):
        _, l = _layer(s, lid)
        if l:
            l.setdefault("paint", {}).update({k.replace("_", "-"): v for k, v in kw.items()})
    paint("background", background_color=P["paper"])
    paint("earth", fill_color=P["paper"])
    paint("water", fill_color=P["water"])
    paint("water_stream", line_color=P["water_line"])
    paint("water_river", line_color=P["water_line"])
    paint("landuse_urban_green", fill_color=P["park"])
    for lid in ("landuse_hospital", "landuse_industrial", "landuse_school", "landuse_zoo", "landuse_aerodrome", "landuse_pedestrian"):
        paint(lid, fill_color=P["urban"])
    paint("buildings", fill_color=P["building"], fill_opacity=0.9)
    paint("roads_rail", line_color=P["rail"])
    paint("boundaries_country", line_color=P["boundary"])
    paint("boundaries", line_color=P["boundary"])
    # landcover like the Swiss maps: forest green, glacier light blue with a blue edge, meadows paper-white
    _, lp = _layer(s, "landuse_park")
    if lp:
        lp["paint"]["fill-color"] = _kind_colors(P, P["paper"])
        lp["paint"]["fill-opacity"] = ["interpolate", ["linear"], ["zoom"], 6, 0, 9, 1]
        lp["filter"] = ["in", "kind", "national_park", "park", "cemetery", "protected_area", "nature_reserve", "forest", "golf_course",
                        "wood", "scrub", "heath", "grassland", "grass", "meadow", "glacier", "sand", "military", "naval_base", "airfield", "garden"]
    i_park, _ = _layer(s, "landuse_park")
    extra = [
        {"id": "topo_rock", "type": "fill", "source": "protomaps", "source-layer": "landuse",
         "filter": ["in", "kind", "bare_rock", "rock", "scree", "shingle"], "paint": {"fill-color": P["rock"]}},
        {"id": "topo_glacier_edge", "type": "line", "source": "protomaps", "source-layer": "landuse", "minzoom": 10,
         "filter": ["==", "kind", "glacier"], "paint": {"line-color": P["glacier_line"], "line-width": ["interpolate", ["linear"], ["zoom"], 10, 0.4, 15, 1.2]}},
    ]
    L[i_park + 1:i_park + 1] = extra
    # roads: on the paper the white roads need a visible edge
    for l in L:
        if l["type"] == "line" and l.get("source-layer") == "roads" and l["id"] != "roads_rail" and not dunkel:
            if "casing" in l["id"]:
                l["paint"]["line-color"] = P["highway_casing"] if "highway" in l["id"] else P["casing"]
            elif "highway" in l["id"]:
                l["paint"]["line-color"] = P["highway"]
            elif l["id"] in ("roads_minor", "roads_minor_service", "roads_bridges_minor"):
                l["paint"]["line-color"] = P["road_minor"]
    # relief + contour lines + cliffs below the roads (like on paper)
    i_ped, _ = _layer(s, "landuse_pedestrian")
    relief = {"id": "topo_relief", "type": "hillshade", "source": "relief", "maxzoom": 18,
              "paint": {"hillshade-method": "igor", "hillshade-exaggeration": P["relief"], "hillshade-illumination-direction": 315,
                        "hillshade-illumination-anchor": "map", "hillshade-shadow-color": P["shadow"],
                        "hillshade-highlight-color": P["highlight"], "hillshade-accent-color": P["accent"]}}
    # equidistance like the Swiss maps: 100 m from z11, 50 m from z12, 20 m from z13, 10 m from z14
    vis = ["any", [">=", ["get", "lvl"], 100], ["all", [">=", ["zoom"], 12], [">=", ["get", "lvl"], 50]],
           ["all", [">=", ["zoom"], 13], [">=", ["get", "lvl"], 20]], [">=", ["zoom"], 14]]
    gl = ["==", ["get", "gl"], 1]
    hk = {"id": "topo_hk", "type": "line", "source": "topo", "source-layer": "contour", "minzoom": 11, "filter": vis,
          "layout": {"line-join": "round"},
          "paint": {"line-color": ["case", gl, P["contour_glacier"], [">=", ["get", "lvl"], 100], P["contour_index"], P["contour"]],
                    "line-opacity": 0.75 if dunkel else 0.9,
                    "line-width": ["interpolate", ["linear"], ["zoom"], 11, ["case", [">=", ["get", "lvl"], 100], 0.55, 0.3],
                                   14, ["case", [">=", ["get", "lvl"], 100], 1.0, 0.45], 17, ["case", [">=", ["get", "lvl"], 100], 1.6, 0.8]]}}
    cliff = {"id": "topo_cliff", "type": "line", "source": "protomaps", "source-layer": "earth", "filter": ["==", "kind", "cliff"],
             "minzoom": 12, "paint": {"line-color": P["cliff"], "line-width": ["interpolate", ["linear"], ["zoom"], 12, 0.6, 16, 1.6]}}
    L[i_ped:i_ped] = [relief, hk, cliff]
    # paths that are not hiking paths: thin, dashed, brown-grey
    _, ro = _layer(s, "roads_other")
    if ro:
        ro["paint"] = {"line-color": P["path"], "line-dasharray": [3, 2],
                       "line-width": ["interpolate", ["linear"], ["zoom"], 12, 0.4, 14, 0.8, 17, 1.6]}
        ro["minzoom"] = 13
    # hiking paths from OpenStreetMap (not the official network): g 1 yellow (Wanderweg), 2 red (Bergwanderweg), 3 blue (Alpinwanderweg)
    g = ["get", "g"]
    w_w = ["interpolate", ["linear"], ["zoom"], 12, 1.1, 14, 1.8, 17, 3.2]
    w_c = ["interpolate", ["linear"], ["zoom"], 12, 2.3, 14, 3.4, 17, 5.4]
    wege = [
        {"id": "topo_wege_casing", "type": "line", "source": "topo", "source-layer": "wege", "minzoom": 12,
         "layout": {"line-join": "round", "line-cap": "round"},
         "paint": {"line-color": ["case", ["==", g, 1], P["weg1_casing"], P["weg_casing"]], "line-width": w_c,
                   "line-opacity": ["case", ["==", g, 1], 0.55, 0.85]}},
        {"id": "topo_wege_1", "type": "line", "source": "topo", "source-layer": "wege", "minzoom": 12, "filter": ["==", g, 1],
         "layout": {"line-join": "round", "line-cap": "round"}, "paint": {"line-color": P["weg1"], "line-width": w_w}},
        {"id": "topo_wege_23", "type": "line", "source": "topo", "source-layer": "wege", "minzoom": 12, "filter": [">=", g, 2],
         "layout": {"line-join": "round"},
         "paint": {"line-color": ["case", ["==", g, 3], P["weg3"], P["weg2"]], "line-width": w_w, "line-dasharray": [2.4, 1.2]}},
    ]
    i_rail, _ = _layer(s, "roads_rail")
    L[i_rail:i_rail] = wege
    # labels: contour heights along the lines, peaks with their height
    lab = {"id": "topo_hk_label", "type": "symbol", "source": "topo", "source-layer": "contour", "minzoom": 13.5,
           "filter": ["any", [">=", ["get", "lvl"], 100], ["all", [">=", ["zoom"], 15], [">=", ["get", "lvl"], 50]]],
           "layout": {"symbol-placement": "line", "text-field": ["to-string", ["get", "ele"]], "text-font": ["Noto Sans Regular"],
                      "text-size": 10, "symbol-spacing": 340, "text-max-angle": 25, "text-padding": 4},
           "paint": {"text-color": ["case", gl, P["contour_text_glacier"], P["contour_text"]], "text-halo-color": P["halo"],
                     "text-halo-width": 1.4}}
    peaks = ["peak", "volcano", "saddle"]
    peak = {"id": "topo_peaks", "type": "symbol", "source": "protomaps", "source-layer": "pois", "minzoom": 11,
            "filter": ["in", ["get", "kind"], ["literal", peaks]],
            "layout": {"text-field": ["case", ["has", "elevation"],
                                      ["concat", ["get", "name"], "\n", ["to-string", ["round", ["get", "elevation"]]]], ["get", "name"]],
                       "text-font": ["Noto Sans Medium"], "text-size": 11.5, "text-anchor": "top", "text-offset": [0, 0.3],
                       "text-max-width": 8, "icon-image": "", "symbol-sort-key": ["-", 0, ["coalesce", ["get", "elevation"], 0]]},
            "paint": {"text-color": P["peak"], "text-halo-color": P["halo"], "text-halo-width": 1.5}}
    i_pois, pois = _layer(s, "pois")
    if pois:
        pois["filter"] = ["all", pois["filter"], ["!", ["in", ["get", "kind"], ["literal", peaks]]]]
        L[i_pois:i_pois] = [lab, peak]
    for l in L:                                             # label halos on the paper
        p = l.get("paint") or {}
        if l["type"] == "symbol" and "text-halo-color" in p and l["id"] not in ("topo_hk_label", "topo_peaks") and not dunkel:
            if l["id"].startswith("water"):
                continue
            p["text-halo-color"] = P["halo"]
    if not dunkel:
        for lid in ("water_waterway_label", "water_label_lakes", "water_label_ocean"):
            paint(lid, text_color=P["water_text"], text_halo_color=P["halo"])
    return s


def alle(light):
    """{name in the web package: style} - the four styles"""
    return {"style.json": light, "style_dark.json": standard_dunkel(light), "style_topo.json": topo(light), "style_topo_dark.json": topo(light, True)}


def pruefen(styles):
    """the checks of karten_test.py / paket.py (raises AssertionError): sources, layers, no colour left light in dark"""
    for n, s in styles.items():
        ids = [l["id"] for l in s["layers"]]
        assert len(ids) == len(set(ids)), n + ": layer ids twice"
        assert s["sources"]["protomaps"]["tiles"] == ["{TILES}"], n
        for l in s["layers"]:
            if "source" in l:
                assert l["source"] in s["sources"], (n, l["id"])
        if "topo" in n:
            assert {"topo", "relief"} <= set(s["sources"]), n
            assert {"topo_relief", "topo_hk", "topo_hk_label", "topo_wege_1", "topo_wege_23", "topo_peaks"} <= set(ids), n
            assert s["sources"]["relief"]["encoding"] == "terrarium" and s["sources"]["topo"]["tiles"] == ["{TOPO}"], n
        else:
            assert "topo" not in s["sources"] and "relief" not in s["sources"], n
        if "dark" in n:
            assert s["sprite"] == "{SPRITE}dark", n
            bg = s["layers"][0]["paint"]["background-color"]
            assert sum(_parse(bg)[0]) < 120, (n, bg)
            for l in s["layers"]:
                if l["type"] in ("fill", "background"):
                    for k, v in (l.get("paint") or {}).items():
                        if k.endswith("color"):
                            for c in re.findall(r"#[0-9a-fA-F]{6}", json.dumps(v)):
                                assert sum(_parse(c)[0]) < 300, (n, l["id"], c)
    return True


if __name__ == "__main__":
    light = json.load(open(sys.argv[1], encoding="utf-8"))
    st = alle(light)
    pruefen(st)
    for n, s in st.items():
        with open("%s/%s" % (sys.argv[2], n), "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    print("ok", {n: len(s["layers"]) for n, s in st.items()})
