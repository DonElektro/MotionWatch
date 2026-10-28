import math, json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
F = TTFont('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf')
gs = F.getGlyphSet(); cmap = F.getBestCmap(); upm = F['head'].unitsPerEm
def text_path(s, x, base, size):
    sc = size / upm; out = []; cx = x
    for ch in s:
        g = cmap[ord(ch)]; pen = SVGPathPen(gs)
        tp = TransformPen(pen, (sc, 0, 0, -sc, cx, base))
        gs[g].draw(tp); out.append(pen.getCommands()); cx += gs[g].width * sc
    return " ".join(out), cx - x
def adv(s, size):
    return sum(gs[cmap[ord(c)]].width for c in s) * size / upm
def fan(cx, cy, r, a0, a1):
    p = lambda a: (cx + r*math.cos(math.radians(a)), cy + r*math.sin(math.radians(a)))
    x0, y0 = p(a0); x1, y1 = p(a1)
    return f"M{cx:.1f} {cy:.1f} L{x0:.1f} {y0:.1f} A{r} {r} 0 0 1 {x1:.1f} {y1:.1f} Z"
def walker(x, y, s, c):
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({s})" fill="{c}" stroke="{c}" stroke-linecap="round"><circle cx="1" cy="-15" r="5" stroke="none"/>'
            f'<path d="M0 -9 L-1 3" stroke-width="7"/><path d="M-1 3 L-6 13 M-1 3 L5 12" stroke-width="3.5" fill="none"/><path d="M0 -6 L-6 0 M0 -6 L6 -1" stroke-width="3" fill="none"/></g>')
def corners(x0, y0, x1, y1, c, w, l):
    return (f'<g fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"><path d="M{x0:.1f} {y0+l:.1f} V{y0:.1f} H{x0+l:.1f} '
            f'M{x1-l:.1f} {y0:.1f} H{x1:.1f} V{y0+l:.1f} M{x1:.1f} {y1-l:.1f} V{y1:.1f} H{x1-l:.1f} M{x0+l:.1f} {y1:.1f} H{x0:.1f} V{y1-l:.1f}"/></g>')
GRAD = ('<defs><linearGradient id="{id}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ff9f43" stop-opacity=".95"/>'
        '<stop offset="1" stop-color="#ff9f43" stop-opacity=".12"/></linearGradient></defs>')
def eye(ox, oy, r, size, ring, pup):
    return f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r:.1f}" fill="none" stroke="{ring}" stroke-width="{size*0.13:.1f}"/><circle cx="{ox:.1f}" cy="{oy:.1f}" r="{r*0.42:.1f}" fill="{pup}"/>'

def w6(txt_col="var(--txt,#e8eef5)"):
    size = 72; x = 4; base = 150
    pm, wm = text_path("M", x, base, size); wo = adv("o", size)
    ox = x + wm + wo/2; oy = base - size*0.27; r = size*0.255
    pv, wv = text_path("ve", x + wm + wo, base, size)
    pe, we = text_path("Eye", x + wm + wo + wv, base, size)
    W = x + wm + wo + wv + we + 4
    s = GRAD.format(id="mwfw6") + f'<path d="{fan(ox, oy, 95, -124, -56)}" fill="url(#mwfw6)"/>' + walker(ox+3, oy-55, 1.0, "#e8590c") \
        + corners(ox-14, oy-80, ox+19, oy-34, "currentColor", 2.5, 6) \
        + f'<path d="{pm} {pv}" fill="currentColor"/>' + eye(ox, oy, r, size, "#ff9f43", "currentColor") + f'<path d="{pe}" fill="#ff9f43"/>'
    top = oy - 100
    return f'<svg class="wm6" viewBox="0 {top:.0f} {W:.0f} {base - top + 16:.0f}" role="img" aria-label="MoveEye">{s}</svg>'
def w1():
    size = 74; x = 4; base = 200
    pm, wm = text_path("M", x, base, size); wo = adv("o", size)
    ox = x + wm + wo/2; oy = base - size*0.27; r = size*0.255
    pv, wv = text_path("ve", x + wm + wo, base, size)
    wmove = wm + wo + wv
    pe, we = text_path("Eye", x + (wmove - adv("Eye", size))/2, 278, size)
    s = GRAD.format(id="mwfw1") + f'<path d="{fan(ox, oy, 150, -128, -52)}" fill="url(#mwfw1)"/>' + walker(ox+18, oy-90, 1.6, "#e8590c") \
        + corners(ox-6, oy-125, ox+42, oy-58, "currentColor", 3, 8) + f'<path d="{pm} {pv} {pe}" fill="currentColor"/>' + eye(ox, oy, r, size, "#ff9f43", "currentColor")
    top = oy - 153
    return f'<svg class="wm1" viewBox="0 {top:.0f} {wmove + 8:.0f} {300 - top:.0f}" role="img" aria-label="MoveEye">{s}</svg>'
json.dump({"w6": w6(), "w1": w1()}, open('/tmp/claude-0/wm/wm.json', 'w'))
open('/tmp/claude-0/wm/test.html', 'w').write('<html><body style="background:#0a0e14;color:#e8eef5;padding:20px">' + '<div style="height:44px">' + w6().replace('<svg', '<svg style="height:44px"') + '</div><br><div style="height:64px">' + w1().replace('<svg', '<svg style="height:64px"') + '</div><br><div style="background:#fff;color:#18212d;padding:8px"><div style="height:44px">' + w6().replace('<svg', '<svg style="height:44px"') + '</div></div></body></html>')
print(len(w6()), len(w1()))
