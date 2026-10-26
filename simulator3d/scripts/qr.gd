extends RefCounted
## QR code (byte mode, error correction M) for the join address of the game - after the encoder of Motion Watch
## (qr_matrix, ISO 18004). Only short texts (versions 1 to 10). Mask 0 (every mask is valid; scanners read it).

const ECW_M := [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26]
const NBL_M := [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5]
const FMT_M := 0


static func _raw_modules(v: int) -> int:
	var r := (16 * v + 128) * v + 64
	if v >= 2:
		var na := v / 7 + 2
		r -= (25 * na - 10) * na - 55
		if v >= 7:
			r -= 36
	return r


static func _data_cw(v: int) -> int:
	return _raw_modules(v) / 8 - ECW_M[v] * NBL_M[v]


static func _gmul(x: int, y: int) -> int:
	var z := 0
	for i in range(7, -1, -1):
		z = (z << 1) ^ ((z >> 7) * 0x11D)
		z ^= ((y >> i) & 1) * x
	return z & 0xFF


static func matrix(text: String) -> Array:
	"""rows of bools (true = dark); [] if the text is too long"""
	var data := text.to_utf8_buffer()
	var ver := 0
	for v in range(1, 11):
		if 4 + 8 + 8 * data.size() <= _data_cw(v) * 8:
			ver = v
			break
	if ver == 0:
		return []
	var bits: Array[int] = []
	var put := func(val: int, n: int):
		for i in range(n - 1, -1, -1):
			bits.append((val >> i) & 1)
	put.call(4, 4)
	put.call(data.size(), 8)
	for b in data:
		put.call(b, 8)
	var cap := _data_cw(ver) * 8
	put.call(0, min(4, cap - bits.size()))
	put.call(0, posmod(-bits.size(), 8))
	var pad := 0xEC
	while bits.size() < cap:
		put.call(pad, 8)
		pad ^= 0xEC ^ 0x11
	var cws: Array[int] = []
	for i in range(0, bits.size(), 8):
		var c := 0
		for j in range(8):
			c = (c << 1) | bits[i + j]
		cws.append(c)
	var nb: int = NBL_M[ver]
	var el: int = ECW_M[ver]
	var rawcw := _raw_modules(ver) / 8
	var nshort := nb - rawcw % nb
	var slen := rawcw / nb
	var div: Array[int] = []
	div.resize(el)
	div.fill(0)
	div[el - 1] = 1
	var root := 1
	for _i in range(el):
		for j in range(el):
			div[j] = _gmul(div[j], root)
			if j + 1 < el:
				div[j] ^= div[j + 1]
		root = _gmul(root, 0x02)
	var blocks := []
	var k := 0
	for i in range(nb):
		var n := slen - el + (0 if i < nshort else 1)
		var dat: Array[int] = []
		for q in range(n):
			dat.append(cws[k + q])
		k += n
		var rem: Array[int] = []
		rem.resize(el)
		rem.fill(0)
		for b in dat:
			var f: int = b ^ rem.pop_front()
			rem.append(0)
			for j in range(el):
				rem[j] ^= _gmul(div[j], f)
		if i < nshort:
			dat.append(0)
		blocks.append(dat + rem)
	var allcw: Array[int] = []
	for i in range((blocks[0] as Array).size()):
		for j in range(blocks.size()):
			if i != slen - el or j >= nshort:
				allcw.append(blocks[j][i])
	var size := ver * 4 + 17
	var M := []
	var F := []
	for y in range(size):
		var r1 := []
		r1.resize(size)
		r1.fill(false)
		M.append(r1)
		var r2 := []
		r2.resize(size)
		r2.fill(false)
		F.append(r2)
	var setf := func(x: int, y: int, dark: bool):
		M[y][x] = dark
		F[y][x] = true
	for i in range(size):
		setf.call(6, i, i % 2 == 0)
		setf.call(i, 6, i % 2 == 0)
	for c in [Vector2i(3, 3), Vector2i(size - 4, 3), Vector2i(3, size - 4)]:
		for dy in range(-4, 5):
			for dx in range(-4, 5):
				var x: int = c.x + dx
				var y: int = c.y + dy
				if x >= 0 and x < size and y >= 0 and y < size:
					setf.call(x, y, not (max(abs(dx), abs(dy)) in [2, 4]))
	if ver > 1:
		var na := ver / 7 + 2
		var step := (ver * 4 + na * 2 + 1) / (na * 2 - 2) * 2
		var pos: Array[int] = [6]
		var tail: Array[int] = []
		for i in range(na - 1):
			tail.append(size - 7 - i * step)
		tail.reverse()
		pos.append_array(tail)
		for i in range(pos.size()):
			for j in range(pos.size()):
				if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0):
					continue
				for dy in range(-2, 3):
					for dx in range(-2, 3):
						setf.call(pos[i] + dx, pos[j] + dy, max(abs(dx), abs(dy)) != 1)
	var mask := 0
	# format bits (also reserves those modules before the data is placed)
	var d := FMT_M << 3 | mask
	var rem2 := d
	for _i in range(10):
		rem2 = (rem2 << 1) ^ ((rem2 >> 9) * 0x537)
	var fb := (d << 10 | rem2) ^ 0x5412
	var g := func(i: int) -> bool: return (fb >> i) & 1 == 1
	for i in range(6):
		setf.call(8, i, g.call(i))
	setf.call(8, 7, g.call(6))
	setf.call(8, 8, g.call(7))
	setf.call(7, 8, g.call(8))
	for i in range(9, 15):
		setf.call(14 - i, 8, g.call(i))
	for i in range(8):
		setf.call(size - 1 - i, 8, g.call(i))
	for i in range(8, 15):
		setf.call(8, size - 15 + i, g.call(i))
	setf.call(8, size - 8, true)
	if ver >= 7:
		var rv := ver
		for _i in range(12):
			rv = (rv << 1) ^ ((rv >> 11) * 0x1F25)
		var vb := ver << 12 | rv
		for i in range(18):
			var bit := (vb >> i) & 1 == 1
			setf.call(size - 11 + i % 3, i / 3, bit)
			setf.call(i / 3, size - 11 + i % 3, bit)
	var bi := 0
	var right := size - 1
	while right >= 1:
		if right == 6:
			right = 5
		for vert in range(size):
			for j in range(2):
				var x := right - j
				var up := ((right + 1) & 2) == 0
				var y := size - 1 - vert if up else vert
				if not F[y][x] and bi < allcw.size() * 8:
					M[y][x] = (allcw[bi >> 3] >> (7 - (bi & 7))) & 1 == 1
					bi += 1
		right -= 2
	for y in range(size):                                  # mask 0: (x + y) even
		for x in range(size):
			if not F[y][x] and (x + y) % 2 == 0:
				M[y][x] = not M[y][x]
	return M


static func texture(text: String, scale := 5) -> ImageTexture:
	var m := matrix(text)
	if m.is_empty():
		return null
	var n := m.size()
	var q := 4                                             # quiet zone
	var img := Image.create((n + 2 * q) * scale, (n + 2 * q) * scale, false, Image.FORMAT_L8)
	img.fill(Color.WHITE)
	for y in range(n):
		for x in range(n):
			if m[y][x]:
				img.fill_rect(Rect2i((x + q) * scale, (y + q) * scale, scale, scale), Color.BLACK)
	return ImageTexture.create_from_image(img)
