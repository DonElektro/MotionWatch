extends RefCounted
## Start with the PC (from 3D-2.1).
## Windows: a value «MotionWatch3D» under HKCU\...\Run (no administrator needed) – starts after the sign-in of this user.
## Linux: ~/.config/autostart/motionwatch3d.desktop.
## «Without signing in»: Windows only shows a desktop (and a graphics card for 3D) after a sign-in. So the automatic sign-in
## of Windows is set up with «Autologon» of Microsoft (Sysinternals; the password is typed in there and stored encrypted by
## Windows, never by the simulator), and the simulator locks the screen right after its start.

const RUN_KEY := "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
const NAME := "MotionWatch3D"
const AUTOLOGON_URL := "https://download.sysinternals.com/files/AutoLogon.zip"


static func command() -> String:
	"""what is started with the PC"""
	return "\"%s\" --autostart" % OS.get_executable_path()


static func _desktop_file() -> String:
	var home := OS.get_environment("XDG_CONFIG_HOME")
	if home == "":
		home = OS.get_environment("HOME").path_join(".config")
	return home.path_join("autostart").path_join("motionwatch3d.desktop")


static func current() -> String:
	"""the command that is registered now ("" = no autostart)"""
	if OS.get_name() == "Windows":
		var out := []
		if OS.execute("reg", ["query", RUN_KEY, "/v", NAME], out, true) != 0:
			return ""
		for line in "\n".join(PackedStringArray(out)).split("\n"):
			var i := line.find("REG_SZ")
			if i >= 0:
				return line.substr(i + 6).strip_edges()
		return ""
	var p := _desktop_file()
	if not FileAccess.file_exists(p):
		return ""
	for line in FileAccess.get_file_as_string(p).split("\n"):
		if line.begins_with("Exec="):
			return line.substr(5).strip_edges()
	return ""


static func is_on() -> bool:
	return current() != ""


static func set_on(on: bool) -> String:
	"""switches the autostart on or off; returns "" or the reason why it did not work"""
	if OS.get_name() == "Windows":
		var out := []
		var code: int
		if on:
			code = OS.execute("reg", ["add", RUN_KEY, "/v", NAME, "/t", "REG_SZ", "/d", command(), "/f"], out, true)
		else:
			if not is_on():
				return ""
			code = OS.execute("reg", ["delete", RUN_KEY, "/v", NAME, "/f"], out, true)
		return "" if code == 0 else "Windows-Registry: %s" % "\n".join(PackedStringArray(out)).strip_edges()
	var p := _desktop_file()
	if not on:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)
		return ""
	DirAccess.make_dir_recursive_absolute(p.get_base_dir())
	var f := FileAccess.open(p, FileAccess.WRITE)
	if f == null:
		return "kann %s nicht schreiben" % p
	f.store_string("[Desktop Entry]\nType=Application\nName=Motion Watch 3D-Simulator\nExec=%s\nX-GNOME-Autostart-enabled=true\n" % command())
	return ""


static func repair() -> void:
	"""the program was moved to another folder: the autostart follows it"""
	var c := current()
	if c != "" and c != command():
		set_on(true)


static func lock_screen() -> void:
	"""Windows: lock the screen (the simulator keeps running behind it)"""
	if OS.get_name() == "Windows":
		OS.create_process("rundll32.exe", ["user32.dll,LockWorkStation"])


static func autologon_dir() -> String:
	return OS.get_user_data_dir().path_join("autologon")


static func autologon_exe() -> String:
	var a := OS.get_environment("PROCESSOR_ARCHITECTURE").to_upper()
	var n := "Autologon64a.exe" if a == "ARM64" else ("Autologon64.exe" if a.contains("64") else "Autologon.exe")
	return autologon_dir().path_join(n)


static func get_autologon() -> String:
	"""downloads Autologon of Microsoft (only the first time) and opens it; returns "" or the reason why not.
	It asks Windows for administrator rights (UAC), there the password of the user is typed in and «Enable» pressed."""
	if OS.get_name() != "Windows":
		return "nur unter Windows"
	var exe := autologon_exe()
	if not FileAccess.file_exists(exe):
		DirAccess.make_dir_recursive_absolute(autologon_dir())
		var z := autologon_dir().path_join("AutoLogon.zip")
		var out := []
		var code := OS.execute("curl.exe", ["-L", "-f", "-s", "-S", "--retry", "2", "-o", z, AUTOLOGON_URL], out, true)
		if code != 0:
			return "Download fehlgeschlagen (%s)" % "\n".join(PackedStringArray(out)).strip_edges()
		code = OS.execute("tar.exe", ["-xf", z, "-C", autologon_dir()], out, true)
		if code != 0 or not FileAccess.file_exists(exe):
			return "Entpacken fehlgeschlagen"
	OS.shell_open(exe)          # ShellExecute: Windows asks for the administrator rights itself
	return ""
