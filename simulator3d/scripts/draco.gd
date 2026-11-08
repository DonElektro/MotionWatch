extends RefCounted
## Draco decoder in GDScript (from 3.65.0): unpacks the meshes of glTF with KHR_draco_mesh_compression, which Godot 4.3 cannot read.
## swisstopo has sent swissBUILDINGS3D like this since 2026 (Draco 2.2, edgebreaker with valence coding, positions quantized and
## predicted with parallelograms). Only what the simulator needs: the triangles and the positions; normals, colours and
## the batch ids in the same data are skipped (the simulator makes its own flat normals).
## Written after the published bitstream of Draco (google/draco, Apache 2.0): edgebreaker (standard + valence), the
## depth-first and the max-prediction-degree traversal, rANS, tagged / raw symbols, prediction difference, parallelogram,
## multi-parallelogram and constrained multi-parallelogram with the wrap transform, quantization.
## decode(bytes) -> {"ok": true, "pos": PackedVector3Array (per vertex), "tri": PackedInt32Array (3 vertex numbers per triangle),
##                   "pos_uid": Draco id of the positions, <uid>: [type, components, values, vertex -> value] of each decoded attribute}
##                  or {"ok": false, "err": "why"};  attribute(res, uid): the first component of an attribute per vertex (_BATCHID)

const INV := -1

var b: PackedByteArray
var p := 0
var err := ""


static func decode(bytes: PackedByteArray) -> Dictionary:
	var d = new()
	d.b = bytes
	var r: Dictionary = d._decode()
	if not r.get("ok", false) and not r.has("err"):
		r["err"] = d.err if d.err != "" else "Draco nicht lesbar"
	return r


# ---- reading -------------------------------------------------------------------------------------------------------
func u8() -> int:
	if p >= b.size():
		err = "Draco: Daten zu kurz"
		return 0
	p += 1
	return b[p - 1]


func i8() -> int:
	var v := u8()
	return v - 256 if v > 127 else v


func u16() -> int:
	var v := u8()
	return v | (u8() << 8)


func i32() -> int:
	if p + 4 > b.size():
		err = "Draco: Daten zu kurz"
		return 0
	var v := b.decode_s32(p)
	p += 4
	return v


func f32() -> float:
	if p + 4 > b.size():
		err = "Draco: Daten zu kurz"
		return 0.0
	var v := b.decode_float(p)
	p += 4
	return v


func var_u() -> int:
	var v := 0
	var sh := 0
	while sh < 64:
		var c := u8()
		v |= (c & 0x7f) << sh
		sh += 7
		if c & 0x80 == 0 or err != "":
			break
	return v


# bits, the lowest bit of each byte first: [start byte, bit offset]
func bits(st: Array, n: int) -> int:
	var v := 0
	for i in range(n):
		var at: int = st[0] + (st[1] >> 3)
		if at < b.size():
			v |= ((b[at] >> (st[1] & 7)) & 1) << i
		st[1] += 1
	return v


static func bits_end(st: Array) -> int:
	return st[0] + (st[1] + 7) / 8


# ---- rANS -----------------------------------------------------------------------------------------------------------
func _ans_init(start: int, n: int, lbase: int) -> Array:
	"""[state, offset] of an rANS stream of n bytes at start (empty on a fault)"""
	if n < 1 or start + n > b.size():
		return []
	var x: int = b[start + n - 1] >> 6
	var st := 0
	var off := 0
	if x == 0:
		off = n - 1
		st = b[start + n - 1] & 0x3f
	elif x == 1:
		if n < 2:
			return []
		off = n - 2
		st = (b[start + n - 2] | (b[start + n - 1] << 8)) & 0x3fff
	elif x == 2:
		if n < 3:
			return []
		off = n - 3
		st = (b[start + n - 3] | (b[start + n - 2] << 8) | (b[start + n - 1] << 16)) & 0x3fffff
	else:
		if n < 4 or lbase == 4096:
			return []
		off = n - 4
		st = (b[start + n - 4] | (b[start + n - 3] << 8) | (b[start + n - 2] << 16) | (b[start + n - 1] << 24)) & 0x3fffffff
	return [st + lbase, off]


func bit_dec() -> Dictionary:
	"""a binary rANS decoder (start faces, crease edges); reads its header and skips its data in the main buffer"""
	var p0 := u8()
	var n := var_u()
	var d := {"p0": p0, "start": p, "st": 4096, "off": 0}
	if n > 0:
		var a := _ans_init(p, n, 4096)
		if a.is_empty():
			err = "Draco: rANS-Bits kaputt"
			return d
		d["st"] = a[0]
		d["off"] = a[1]
	p += n
	return d


func bit_next(d: Dictionary) -> int:
	var st: int = d["st"]
	if st < 4096 and d["off"] > 0:
		d["off"] -= 1
		st = st * 256 + b[d["start"] + d["off"]]
	var quot := st / 256
	var rem := st % 256
	var q: int = 256 - d["p0"]
	var xn := quot * q
	var val := rem < q
	d["st"] = xn + rem if val else st - xn - q
	return 1 if val else 0


func sym_dec(ubits: int) -> Dictionary:
	"""a symbol rANS decoder: probability table, then the data"""
	var prec_bits := clampi((3 * ubits) / 2, 12, 20)
	var prec := 1 << prec_bits
	var ns := var_u()
	if ns > 1 << 20 or ns / 64 > b.size() - p:
		err = "Draco: zu viele Symbole"
		return {}
	var probs := PackedInt32Array()
	probs.resize(ns)
	var i := 0
	while i < ns and err == "":
		var dd := u8()
		var tok := dd & 3
		if tok == 3:
			i += (dd >> 2) + 1
			continue
		var pr := dd >> 2
		for k in range(tok):
			pr |= u8() << (8 * (k + 1) - 2)
		probs[i] = pr
		i += 1
	var cum := PackedInt32Array()
	cum.resize(ns)
	var lut := PackedInt32Array()
	lut.resize(prec)
	var c := 0
	for s in range(ns):
		cum[s] = c
		if c + probs[s] > prec:
			err = "Draco: rANS-Tabelle kaputt"
			return {}
		for j in range(c, c + probs[s]):
			lut[j] = s
		c += probs[s]
	if ns > 0 and c != prec:
		err = "Draco: rANS-Tabelle unvollständig"
		return {}
	var n := var_u()
	var d := {"prec": prec, "lbase": prec * 4, "probs": probs, "cum": cum, "lut": lut, "start": p, "st": 0, "off": 0}
	if n > b.size() - p:
		err = "Draco: rANS-Daten zu kurz"
		return {}
	var a := _ans_init(p, n, prec * 4)
	if a.is_empty():
		err = "Draco: rANS-Anfang kaputt"
		return {}
	d["st"] = a[0]
	d["off"] = a[1]
	p += n
	return d


func symbols(n: int, ncomp: int) -> PackedInt32Array:
	"""n values (tagged: a bit length per ncomp values, or raw: one rANS symbol each); the inner loops by hand (hot path)"""
	var out := PackedInt32Array()
	if n == 0:
		return out
	out.resize(n)
	var scheme := u8()
	if scheme != 0 and scheme != 1:
		err = "Draco: Symbol-Art %d" % scheme
		return out
	var mbl := 5
	if scheme == 1:
		mbl = u8()
		if mbl < 1 or mbl > 18:
			err = "Draco: Symbolbreite %d" % mbl
			return out
	var d := sym_dec(mbl)
	if err != "":
		return out
	var probs: PackedInt32Array = d["probs"]
	var cum: PackedInt32Array = d["cum"]
	var lut: PackedInt32Array = d["lut"]
	var prec: int = d["prec"]
	var pmask := prec - 1
	var pbits := 0
	while (1 << pbits) < prec:
		pbits += 1
	var lbase: int = d["lbase"]
	var start: int = d["start"]
	var st: int = d["st"]
	var off: int = d["off"]
	var bb := b
	if scheme == 1:
		for i in range(n):
			while st < lbase and off > 0:
				off -= 1
				st = st * 256 + bb[start + off]
			var r := st & pmask
			var sv: int = lut[r]
			st = (st >> pbits) * probs[sv] + r - cum[sv]
			out[i] = sv
		return out
	# tagged: the bit length from rANS, the values as raw bits (lowest first) after the rANS data
	var bitpos := p * 8
	var bsz := bb.size()
	var at := 0
	for i in range(0, n, ncomp):
		while st < lbase and off > 0:
			off -= 1
			st = st * 256 + bb[start + off]
		var r := st & pmask
		var bl: int = lut[r]
		st = (st >> pbits) * probs[bl] + r - cum[bl]
		for j in range(ncomp):
			var v := 0
			if bl > 0:
				var bi := bitpos >> 3
				var sh := bitpos & 7
				var need := (sh + bl + 7) >> 3
				var w := 0
				for k in range(need):
					if bi + k < bsz:
						w |= bb[bi + k] << (8 * k)
				v = (w >> sh) & ((1 << bl) - 1)
				bitpos += bl
			if at < n:
				out[at] = v
			at += 1
	p = (bitpos + 7) >> 3
	return out


# ---- the mesh ---------------------------------------------------------------------------------------------------------
var c2v := PackedInt32Array()                # corner -> vertex
var opp := PackedInt32Array()                # corner -> opposite corner
var vc := PackedInt32Array()                 # vertex -> left-most corner


static func nxt(c: int) -> int:
	return INV if c < 0 else (c - 2 if c % 3 == 2 else c + 1)


static func prv(c: int) -> int:
	return INV if c < 0 else (c + 2 if c % 3 == 0 else c - 1)


func vx(c: int) -> int:
	return INV if c < 0 else c2v[c]


func op(c: int) -> int:
	return INV if c < 0 else opp[c]


func swl(c: int) -> int:
	return nxt(op(nxt(c)))


func swr(c: int) -> int:
	return prv(op(prv(c)))


func setopp(a: int, c: int) -> void:
	opp[a] = c
	opp[c] = a


func newv() -> int:
	vc.append(INV)
	return vc.size() - 1


func _decode() -> Dictionary:
	if b.size() < 11 or b.slice(0, 5).get_string_from_ascii() != "DRACO":
		return {"ok": false, "err": "keine Draco-Daten"}
	p = 5
	var maj := u8()
	var mnr := u8()
	var etype := u8()
	var method := u8()
	var flags := u16()
	if maj != 2 or mnr != 2:
		return {"ok": false, "err": "Draco-Version %d.%d (nur 2.2)" % [maj, mnr]}
	if etype != 1:
		return {"ok": false, "err": "Draco: keine Dreiecke (Art %d)" % etype}
	if flags & 0x8000:
		return {"ok": false, "err": "Draco mit Metadaten"}
	if method != 1:
		return {"ok": false, "err": "Draco sequentiell (nur Edgebreaker)"}
	var tdt := u8()
	if tdt != 0 and tdt != 2:
		return {"ok": false, "err": "Draco-Edgebreaker Art %d" % tdt}
	var nev := var_u()
	var nf := var_u()
	var nad := u8()
	var nsym := var_u()
	var nsplit := var_u()
	if err != "" or nf > 4000000 or nsym > nf or nsplit > nsym or nev + nsplit > 3 * nf + 3:
		return {"ok": false, "err": "Draco: Kopf unplausibel"}
	c2v.resize(3 * nf)
	c2v.fill(INV)
	opp.resize(3 * nf)
	opp.fill(INV)
	vc = PackedInt32Array()
	# topology splits: [split symbol, source symbol, edge]
	var nts := var_u()
	if nts > nf:
		return {"ok": false, "err": "Draco: Teilungen unplausibel"}
	var splits := []
	var last := 0
	for i in range(nts):
		var src := var_u() + last
		var dl := var_u()
		if dl > src:
			return {"ok": false, "err": "Draco: Teilung kaputt"}
		splits.append([src - dl, src, 0])
		last = src
	if nts > 0:
		var bst := [p, 0]
		for t in splits:
			t[2] = bits(bst, 1) & 1
		p = bits_end(bst)
	# the traversal: symbols, start faces, attribute seams (skipped), valence contexts
	var sym_bits := [0, 0]
	if tdt == 0:
		var tsize := var_u()
		sym_bits = [p, 0]
		p += tsize
	var startdec := bit_dec()
	for i in range(nad):
		bit_dec()
	if err != "":
		return {"ok": false}
	var valence := PackedInt32Array()
	var ctx_syms := []
	var ctx_cnt := PackedInt32Array()
	var active := -1
	if tdt == 2:
		valence.resize(nev + nsplit)
		for i in range(6):
			var n := var_u()
			if n > nf:
				return {"ok": false, "err": "Draco: Valenz-Kontext unplausibel"}
			ctx_syms.append(symbols(n, 1) if n > 0 else PackedInt32Array())
			ctx_cnt.append(n)
			if err != "":
				return {"ok": false}
	var after_trav := p
	var topo := [0, 1, 3, 5, 7]                           # C, S, L, R, E
	# connectivity (the reverse of the encoder)
	var stack: Array[int] = []
	var tsac := {}
	var nfaces := 0
	var maxv := nev + nsplit
	for sid in range(nsym):
		var c := 3 * nfaces
		nfaces += 1
		var chk := false
		var s := 0
		if tdt == 0:
			s = bits(sym_bits, 1)
			if s != 0:
				s |= bits(sym_bits, 2) << 1
		elif active == -1:
			s = 7
		else:
			ctx_cnt[active] -= 1
			if ctx_cnt[active] < 0:
				return {"ok": false, "err": "Draco: Valenz-Symbole fehlen"}
			var si: int = ctx_syms[active][ctx_cnt[active]]
			if si < 0 or si > 4:
				return {"ok": false, "err": "Draco: Symbol kaputt"}
			s = topo[si]
		if s == 0:                                        # C
			if stack.is_empty():
				return {"ok": false, "err": "Draco: C ohne Kante"}
			var ca: int = stack[-1]
			var v_x := vx(nxt(ca))
			if v_x < 0 or v_x >= vc.size():
				return {"ok": false, "err": "Draco: C kaputt"}
			var cb := nxt(vc[v_x])
			if ca == cb or cb < 0 or op(ca) != INV or op(cb) != INV:
				return {"ok": false, "err": "Draco: C kaputt"}
			setopp(ca, c + 1)
			setopp(cb, c + 2)
			var vap := vx(prv(ca))
			var vbn := vx(nxt(cb))
			if v_x == vap or v_x == vbn:
				return {"ok": false, "err": "Draco: C entartet"}
			c2v[c] = v_x
			c2v[c + 1] = vbn
			c2v[c + 2] = vap
			vc[vap] = c + 2
			stack[-1] = c
		elif s == 5 or s == 3:                            # R, L
			if stack.is_empty():
				return {"ok": false, "err": "Draco: R/L ohne Kante"}
			var ca: int = stack[-1]
			if op(ca) != INV:
				return {"ok": false, "err": "Draco: R/L kaputt"}
			var oc := c + 2 if s == 5 else c + 1
			var cl := c + 1 if s == 5 else c
			var cr := c if s == 5 else c + 2
			setopp(oc, ca)
			var nv := newv()
			if vc.size() > maxv:
				return {"ok": false, "err": "Draco: zu viele Ecken"}
			c2v[oc] = nv
			vc[nv] = oc
			var vr := vx(prv(ca))
			c2v[cr] = vr
			vc[vr] = cr
			c2v[cl] = vx(nxt(ca))
			stack[-1] = c
			chk = true
		elif s == 1:                                      # S
			if stack.is_empty():
				return {"ok": false, "err": "Draco: S ohne Kante"}
			var cb: int = stack.pop_back()
			if tsac.has(sid):
				stack.append(tsac[sid])
			if stack.is_empty():
				return {"ok": false, "err": "Draco: S ohne zweite Kante"}
			var ca: int = stack[-1]
			if ca == cb or op(ca) != INV or op(cb) != INV:
				return {"ok": false, "err": "Draco: S kaputt"}
			setopp(ca, c + 2)
			setopp(cb, c + 1)
			var vp := vx(prv(ca))
			c2v[c] = vp
			c2v[c + 1] = vx(nxt(ca))
			var vbp := vx(prv(cb))
			c2v[c + 2] = vbp
			vc[vbp] = c + 2
			var cn := nxt(cb)
			var vn := vx(cn)
			vc[vp] = vc[vn]
			var first := cn
			while cn != INV:
				c2v[cn] = vp
				cn = swl(cn)
				if cn == first:
					return {"ok": false, "err": "Draco: S im Kreis"}
			vc[vn] = INV
			if tdt == 2:
				valence[vp] += valence[vn]
			stack[-1] = c
		elif s == 7:                                      # E
			var v0 := newv()
			newv()
			newv()
			if vc.size() > maxv:
				return {"ok": false, "err": "Draco: zu viele Ecken"}
			for k in range(3):
				c2v[c + k] = v0 + k
				vc[v0 + k] = c + k
			stack.append(c)
			chk = true
		else:
			return {"ok": false, "err": "Draco: Symbol %d" % s}
		if tdt == 2:
			var ac: int = stack[-1]
			var vnx := vx(nxt(ac))
			var vpv := vx(prv(ac))
			var vcu := vx(ac)
			if s == 0 or s == 1:
				valence[vnx] += 1
				valence[vpv] += 1
			elif s == 5:
				valence[vcu] += 1
				valence[vnx] += 1
				valence[vpv] += 2
			elif s == 3:
				valence[vcu] += 1
				valence[vnx] += 2
				valence[vpv] += 1
			elif s == 7:
				valence[vcu] += 2
				valence[vnx] += 2
				valence[vpv] += 2
			active = clampi(valence[vnx], 2, 7) - 2
		if chk:
			var esid := nsym - sid - 1
			while not splits.is_empty() and splits[-1][1] >= esid:
				if splits[-1][1] != esid:
					return {"ok": false, "err": "Draco: Teilung verpasst"}
				var t: Array = splits.pop_back()
				var top: int = stack[-1]
				tsac[nsym - int(t[0]) - 1] = nxt(top) if t[2] == 1 else prv(top)
	while not stack.is_empty():                          # start faces
		var c0: int = stack.pop_back()
		if bit_next(startdec):
			var vn := vx(nxt(c0))
			if vn < 0 or vc[vn] < 0:
				return {"ok": false, "err": "Draco: Startfläche kaputt"}
			var cb := nxt(vc[vn])
			var v_x := vx(nxt(cb))
			if v_x < 0 or vc[v_x] < 0:
				return {"ok": false, "err": "Draco: Startfläche kaputt"}
			var cc := nxt(vc[v_x])
			var vp := vx(nxt(cc))
			if nfaces >= nf or c0 == cb or c0 == cc or cb == cc:
				return {"ok": false, "err": "Draco: Startfläche kaputt"}
			var nc := 3 * nfaces
			nfaces += 1
			setopp(nc, c0)
			setopp(nc + 1, cb)
			setopp(nc + 2, cc)
			c2v[nc] = v_x
			c2v[nc + 1] = vp
			c2v[nc + 2] = vn
	if nfaces != nf:
		return {"ok": false, "err": "Draco: %d statt %d Dreiecke" % [nfaces, nf]}
	# (isolated vertices keep their number: they are never visited, the names of the vertices do not matter here)
	p = after_trav
	# the attribute decoders: the positions must come first (always so: the others are predicted from them)
	var ndec := u8()
	var decs := []
	for i in range(ndec):
		decs.append({"data": i8(), "type": u8(), "trav": u8()})
	if decs.is_empty():
		return {"ok": false, "err": "Draco: keine Attribute"}
	for d in decs:                                        # the descriptions of all decoders come before the values
		var na := var_u()
		if na < 1 or na > 64 or err != "":
			return {"ok": false, "err": "Draco: keine Attribute"}
		d["atts"] = []
		for k in range(na):
			d["atts"].append({"att": u8(), "dt": u8(), "nc": u8(), "norm": u8(), "uid": var_u()})
		for k in range(na):
			d["atts"][k]["seq"] = u8()
	if err != "":
		return {"ok": false}
	var d0: Dictionary = decs[0]
	var a0: Dictionary = d0["atts"][0]
	if a0["att"] != 0 or a0["nc"] != 3 or d0["data"] != -1 or d0["type"] != 0:
		return {"ok": false, "err": "Draco: Positionen nicht zuerst"}
	if d0["atts"].size() > 1:
		return {"ok": false, "err": "Draco: Positionen mit anderen Attributen zusammen"}
	var nvert := vc.size()
	var res := {"ok": true, "nvert": nvert}
	var ord := {}                                         # traversal method -> [v2d, d2c]
	for di in range(decs.size()):
		var d: Dictionary = decs[di]
		var at: Dictionary = d["atts"][0]
		# only per-vertex attributes on the connectivity of the positions (positions, batch ids); the rest is not needed
		if d["type"] != 0 or d["atts"].size() != 1 or not at["seq"] in [1, 2] or at["nc"] < 1 or at["nc"] > 4:
			if di == 0:
				return {"ok": false, "err": "Draco: Positions-Art %d" % at["seq"]}
			break
		var trav: int = d["trav"]
		if not ord.has(trav):
			var v2d := PackedInt32Array()
			v2d.resize(nvert)
			var d2c := PackedInt32Array()
			if trav == 0:
				_depth_first(nf, nvert, v2d, d2c)
			elif trav == 1:
				_max_degree(nf, nvert, v2d, d2c)
			else:
				if di == 0:
					return {"ok": false, "err": "Draco: Durchlauf %d" % trav}
				break
			ord[trav] = [v2d, d2c]
		var vals := _values(int(at["nc"]), int(at["seq"]), nf, ord[trav][0], ord[trav][1])
		if vals.is_empty():
			if di == 0:
				return {"ok": false}
			err = ""
			break
		res[int(at["uid"])] = [int(at["att"]), int(at["nc"]), vals, ord[trav][0]]
		if di == 0:
			res["pos_uid"] = int(at["uid"])
	# the positions per vertex
	var pv: Array = res[res["pos_uid"]]
	var vals0: PackedFloat32Array = pv[2]
	var v2d0: PackedInt32Array = pv[3]
	var pos := PackedVector3Array()
	pos.resize(nvert)
	for v in range(nvert):
		var e: int = v2d0[v]
		if e >= 0:
			pos[v] = Vector3(vals0[e * 3], vals0[e * 3 + 1], vals0[e * 3 + 2])
	res["pos"] = pos
	res["tri"] = c2v.duplicate()
	return res


static func attribute(res: Dictionary, uid: int) -> PackedFloat32Array:
	"""the first component of an attribute per vertex (e.g. _BATCHID), empty if it was not decoded"""
	var out := PackedFloat32Array()
	if not res.has(uid):
		return out
	var a: Array = res[uid]
	var vals: PackedFloat32Array = a[2]
	var v2d: PackedInt32Array = a[3]
	var nc: int = a[1]
	out.resize(v2d.size())
	for v in range(v2d.size()):
		out[v] = vals[v2d[v] * nc] if v2d[v] >= 0 else -1.0
	return out


func _values(ncomp: int, seq: int, nf: int, v2d: PackedInt32Array, d2c: PackedInt32Array) -> PackedFloat32Array:
	"""the values of one attribute in the order of the encoder (empty on a fault, err says why)"""
	var nent := d2c.size()
	var none := PackedFloat32Array()
	var pm := i8()
	var pt := -1
	if pm != -2:
		pt = i8()
	var comp := u8()
	var vals := PackedInt32Array()
	if comp > 0:
		vals = symbols(nent * ncomp, ncomp)
	else:
		var nb := u8()
		if nb < 1 or nb > 4 or p + nb * nent * ncomp > b.size():
			err = "Draco: Rohwerte kaputt"
			return none
		vals.resize(nent * ncomp)
		for i in range(nent * ncomp):
			var v := 0
			for k in range(nb):
				v |= b[p + k] << (8 * k)
			vals[i] = v
			p += nb
	if err != "":
		return none
	for i in range(vals.size()):                          # back to signed (zigzag)
		var v: int = vals[i]
		vals[i] = (v >> 1) if v & 1 == 0 else -(v >> 1) - 1
	var crease := []
	if pm == 4:
		for i in range(4):
			var n := var_u()
			var fl := PackedByteArray()
			if n > 3 * nf:
				err = "Draco: Kanten unplausibel"
				return none
			if n > 0:
				var rb := bit_dec()
				fl.resize(n)
				for j in range(n):
					fl[j] = bit_next(rb)
			crease.append(fl)
	var mn := 0
	var mx := 0
	if pm != -2:
		if pt != 1:
			err = "Draco: Transform %d" % pt
			return none
		mn = i32()
		mx = i32()
	var out := PackedInt32Array()
	out.resize(nent * ncomp)
	var wr := [mn, mx, mx - mn + 1, ncomp]
	var pred := PackedInt32Array()
	pred.resize(ncomp)
	if pm == -2:
		out = vals
	elif pm == 0 or pm == 1 or pm == 2 or pm == 4:
		_wrap(out, pred, vals, 0, wr)
		var cpos := [0, 0, 0, 0]
		for q in range(1, nent):
			var used := 0
			if pm == 1:
				if _para(q, d2c[q], v2d, out, pred, ncomp):
					used = 1
			elif pm == 2 or pm == 4:
				var acc := PackedInt32Array()
				acc.resize(ncomp)
				var preds := []
				var sc: int = d2c[q]
				var c: int = sc
				var first := true
				while c != INV:
					var pr := PackedInt32Array()
					pr.resize(ncomp)
					if _para(q, c, v2d, out, pr, ncomp):
						preds.append(pr)
						if pm == 4 and preds.size() == 4:
							break
					if pm == 2:
						c = swr(c)
						if c == sc:
							break
						continue
					c = swl(c) if first else swr(c)
					if c == sc:
						break
					if c == INV and first:
						first = false
						c = swr(sc)
				if not preds.is_empty():
					var ctx := preds.size() - 1
					for pr in preds:
						var crs := false
						if pm == 4:
							if ctx > 3 or cpos[ctx] >= (crease[ctx] as PackedByteArray).size():
								err = "Draco: Kanten fehlen"
								return none
							crs = crease[ctx][cpos[ctx]] != 0
							cpos[ctx] += 1
						if not crs:
							used += 1
							for j in range(ncomp):
								acc[j] += pr[j]
				if used > 0:
					for j in range(ncomp):
						pred[j] = acc[j] / used            # (truncated towards zero, as in C++)
			if used == 0:
				for j in range(ncomp):
					pred[j] = out[(q - 1) * ncomp + j]
			_wrap(out, pred, vals, q * ncomp, wr)
	else:
		err = "Draco: Vorhersage %d" % pm
		return none
	# dequantization (its data comes after the values)
	var res := PackedFloat32Array()
	res.resize(out.size())
	if seq == 2:
		var mins := []
		for i in range(ncomp):
			mins.append(f32())
		var rng := f32()
		var qb := u8()
		if qb < 1 or qb > 30 or err != "":
			err = "Draco: Quantisierung kaputt"
			return none
		var delta := rng / float((1 << qb) - 1)
		for i in range(out.size()):
			res[i] = mins[i % ncomp] + out[i] * delta
	else:
		for i in range(out.size()):
			res[i] = out[i]
	if res.is_empty():
		res.append(0.0)                                   # (no vertex: still «decoded»)
	return res


func _wrap(out: PackedInt32Array, pred: PackedInt32Array, corr: PackedInt32Array, o: int, wr: Array) -> void:
	var mn: int = wr[0]
	var mx: int = wr[1]
	for i in range(wr[3]):
		var v: int = clampi(pred[i], mn, mx) + corr[o + i]
		if v > mx:
			v -= wr[2]
		elif v < mn:
			v += wr[2]
		out[o + i] = v


func _para(q: int, c: int, v2d: PackedInt32Array, out: PackedInt32Array, pr: PackedInt32Array, nc: int) -> bool:
	var oc := op(c)
	if oc == INV:
		return false
	var eo: int = v2d[c2v[oc]]
	var en: int = v2d[c2v[nxt(oc)]]
	var ep: int = v2d[c2v[prv(oc)]]
	if eo < q and en < q and ep < q and eo >= 0 and en >= 0 and ep >= 0:
		for j in range(nc):
			pr[j] = out[en * nc + j] + out[ep * nc + j] - out[eo * nc + j]
		return true
	return false


func _visit(v: int, c: int, vvis: PackedByteArray, v2d: PackedInt32Array, d2c: PackedInt32Array) -> void:
	vvis[v] = 1
	v2d[v] = d2c.size()
	d2c.append(c)


func _depth_first(nf: int, nvert: int, v2d: PackedInt32Array, d2c: PackedInt32Array) -> void:
	var vvis := PackedByteArray()
	vvis.resize(nvert)
	var fvis := PackedByteArray()
	fvis.resize(nf)
	v2d.fill(-1)
	for f in range(nf):
		var c0 := 3 * f
		if fvis[f]:
			continue
		var st: Array[int] = [c0]
		var nv0 := c2v[nxt(c0)]
		var pv0 := c2v[prv(c0)]
		if not vvis[nv0]:
			_visit(nv0, nxt(c0), vvis, v2d, d2c)
		if not vvis[pv0]:
			_visit(pv0, prv(c0), vvis, v2d, d2c)
		while not st.is_empty():
			var c: int = st[-1]
			if c == INV or fvis[c / 3]:
				st.pop_back()
				continue
			while true:
				fvis[c / 3] = 1
				var v := c2v[c]
				if not vvis[v]:
					var onb := swl(vc[v]) == INV
					_visit(v, c, vvis, v2d, d2c)
					if not onb:
						c = op(nxt(c))
						continue
				var rc := op(nxt(c))
				var lc := op(prv(c))
				var rv := rc == INV or fvis[rc / 3]
				var lv := lc == INV or fvis[lc / 3]
				if rv:
					if lv:
						st.pop_back()
						break
					c = lc
				elif lv:
					c = rc
				else:
					st[-1] = lc
					st.append(rc)
					break


func _max_degree(nf: int, nvert: int, v2d: PackedInt32Array, d2c: PackedInt32Array) -> void:
	var vvis := PackedByteArray()
	vvis.resize(nvert)
	var fvis := PackedByteArray()
	fvis.resize(nf)
	var deg := PackedInt32Array()
	deg.resize(nvert)
	v2d.fill(-1)
	var stacks := [[], [], []]
	for f in range(nf):
		var c := 3 * f
		if fvis[f]:
			continue
		stacks[0].append(c)
		var best := 0
		for cc in [nxt(c), prv(c), c]:
			if not vvis[c2v[cc]]:
				_visit(c2v[cc], cc, vvis, v2d, d2c)
		while true:
			c = INV
			for i in range(best, 3):
				if not stacks[i].is_empty():
					c = stacks[i].pop_back()
					best = i
					break
			if c == INV:
				break
			if fvis[c / 3]:
				continue
			while true:
				fvis[c / 3] = 1
				var v := c2v[c]
				if not vvis[v]:
					_visit(v, c, vvis, v2d, d2c)
				var rc := op(nxt(c))
				var lc := op(prv(c))
				var rv := rc == INV or fvis[rc / 3]
				var lv := lc == INV or fvis[lc / 3]
				if not lv:
					var pr := _prio(lc, vvis, deg)
					if rv and pr <= best:
						c = lc
						continue
					stacks[pr].append(lc)
					best = mini(best, pr)
				if not rv:
					var pr := _prio(rc, vvis, deg)
					if pr <= best:
						c = rc
						continue
					stacks[pr].append(rc)
					best = mini(best, pr)
				break


func _prio(c: int, vvis: PackedByteArray, deg: PackedInt32Array) -> int:
	var v := c2v[c]
	if vvis[v]:
		return 0
	deg[v] += 1
	return 1 if deg[v] > 1 else 2
