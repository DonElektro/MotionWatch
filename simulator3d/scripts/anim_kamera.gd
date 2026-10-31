extends RefCounted
## «Animationen verbessern» 16 (Daniel 31.10.2026): die Ansicht wippt leicht beim Gehen der Spielfigur (Maggie-Geschichte,
## Kamera hinter der Figur). Abschaltbar: Einstellung «Ansicht wippt beim Gehen» (main.cam_wippen, System → Grafik,
## Standard an; eine Einstellung für Bewegungsempfindlichkeit gibt es im Simulator nicht). Nur bei hoher Qualität
## (anim_mensch.hoch), nie in Lite. Das Schaukeln in der Seilbahn macht abenteuer_action.gd (seit 3.14).
## Gebrauch:   AnimKamera.weg(cam)  … die eigene Kamera setzen …  AnimKamera.wippen(main, cam, figur, dt)
## (weg() nimmt das Wippen des letzten Bildes zurück, damit eine nachziehende Kamera es nicht aufsammelt.)

const AnimMensch = preload("res://scripts/anim_mensch.gd")


static func weg(cam: Camera3D) -> void:
	if cam == null or not cam.has_meta("anim_wipp"):
		return
	var off: Transform3D = cam.get_meta("anim_wipp")
	cam.global_transform = cam.global_transform * off.affine_inverse()
	cam.remove_meta("anim_wipp")


static func wippen(m, cam: Camera3D, fig, dt: float) -> void:
	if cam == null or fig == null or not is_instance_valid(fig):
		return
	if not bool(m.get("cam_wippen")) or not AnimMensch.hoch(m):
		return
	var spd: float = float(fig.get("cur_speed"))
	if spd < 0.15:
		return
	var k := clampf(spd / 1.5, 0.0, 1.4)
	var ph: float = float(fig.get("phase"))
	var y := (absf(cos(ph)) - 0.6) * 0.035 * k                     # up and down with every step
	var roll := sin(ph) * 0.006 * k                                # a little from side to side
	var off := Transform3D(Basis(Vector3(0, 0, 1), roll), Vector3(0, y, 0))
	cam.global_transform = cam.global_transform * off
	cam.set_meta("anim_wipp", off)
