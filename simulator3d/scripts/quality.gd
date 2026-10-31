extends RefCounted
## 3D-4.25 «Lite» (Wunsch Daniel 31.10.2026): die leichte Grafik-Stufe desselben Simulators, damit er auf einem Raspberry Pi 5
## sauber läuft. Gleiche Menüs, gleiches Aussehen – nur weniger Aufwand (main.gd lite_update / _lite_apply).
##
## Zentrale Abfrage für alle Teile (auch Pakete, die parallel entstehen):
##     const Quality = preload("res://scripts/quality.gd")
##     if Quality.lite(): …
## oder ohne preload:
##     if Engine.has_meta("lite") and Engine.get_meta("lite"): …
## main.gd setzt die Meta beim Start und bei jedem Wechsel (Einstellung «Grafik-Modus»: Automatisch / Lite / Normal / Hoch).
##
## Stufen: Lite < Normal (= Grafik wie bis 3D-4.24) < Hoch (scripts/grafik_hoch.gd: Forward+ / Vulkan, Neustart nötig).
## Neue Stufe: einen Eintrag in MODES anhängen (Kennung, Text) – mode_id() / mode_name() und das Menü nehmen sie dann
## von selbst; «lite» bleibt die einzige Stufe, die Engine-Meta «lite» = true setzt.

const MODES := [["auto", "Automatisch (Lite auf Raspberry Pi und sehr langsamen PCs, sonst Normal)"],
		["lite", "Lite (für Raspberry Pi 5: schneller, etwas einfacher)"], ["normal", "Normal"],
		["hoch", "Hoch (fotorealistisch – braucht eine gute Grafikkarte)"]]   # F1: grafik_hoch.gd, nur von Hand (nie automatisch)
const SCALE := 0.6          # Schärfe der grossen Ansicht im Fenster (die Bilder für MoveEye bleiben scharf)
const FPS := 25             # höchstens so viele Bilder pro Sekunde im Fenster
const KEEP := 0.35          # so viel bleibt von Partikeln (Rauch, Feuer, Regen, Schnee) und Gras
const FAR := 70.0           # kleine Dinge weiter weg als das werden nicht gezeichnet (m)
const VISITORS := 6         # höchstens so viele Besucher gleichzeitig
const VIEW_W := 640         # Bild des Fensters für MoveEye (/view.jpg, /view.mjpg): Breite …
const VIEW_Q := 0.55        # … und JPEG-Qualität
const VIEW_FPS := 4.0


static func mode_id(v) -> String:
	"""die Kennung einer Stufe («full» / «voll» aus Tests = normal); unbekannt = auto"""
	var k := str(v).to_lower()
	if k in ["full", "voll"]:
		k = "normal"
	for m in MODES:
		if m[0] == k:
			return k
	return "auto"


static func mode_name(v) -> String:
	var k := mode_id(v)
	for m in MODES:
		if m[0] == k:
			return str(m[1]).get_slice(" (", 0)
	return k


static func lite() -> bool:
	return Engine.has_meta("lite") and bool(Engine.get_meta("lite"))


static func set_lite(on: bool) -> void:
	Engine.set_meta("lite", on)


static func n(count: int, keep := KEEP) -> int:
	"""Anzahl (Partikel, Grashalme …): in Lite weniger"""
	return maxi(1, roundi(count * keep)) if lite() else count


static func pi_model() -> String:
	"""«Raspberry Pi 5 Model B Rev 1.0» – oder leer (kein Pi / nicht lesbar)"""
	if OS.get_name() != "Linux":
		return ""
	for p in ["/proc/device-tree/model", "/sys/firmware/devicetree/base/model"]:
		if FileAccess.file_exists(p):
			var b := FileAccess.get_file_as_bytes(p)
			var s := ""
			for x in b:
				if x >= 32 and x < 127:
					s += char(x)
			if s.strip_edges() != "":
				return s.strip_edges()
	return ""


static func weak_reason() -> String:
	"""warum «Automatisch» Lite wählt (leer = starke Hardware)"""
	var m := pi_model()
	if m.findn("Raspberry Pi") >= 0:
		return m
	var arch := Engine.get_architecture_name()
	if OS.get_name() == "Linux" and arch in ["arm64", "arm32"]:
		return "ARM-Rechner (%s)" % arch
	var a := RenderingServer.get_video_adapter_name().to_lower()
	if a.contains("v3d") or a.contains("videocore"):
		return "Grafik VideoCore (Raspberry Pi)"
	return ""


static func renderer() -> String:
	"""der Renderer, mit dem der Simulator gerade zeichnet"""
	var m := str(ProjectSettings.get_setting("rendering/renderer/rendering_method", ""))
	var drv := ""
	if OS.has_method("get_current_rendering_driver_name"):
		drv = str(OS.call("get_current_rendering_driver_name"))
	if RenderingServer.get_rendering_device() != null:
		return "Forward+ / Mobile (Vulkan%s)" % ("" if drv == "" else ", " + drv)
	if m == "gl_compatibility" or drv.begins_with("opengl"):
		return "Compatibility (OpenGL%s)" % ("" if drv == "" else ", " + drv)
	return m if m != "" else "unbekannt"
