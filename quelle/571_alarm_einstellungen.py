#@ MoveEye – Teil 571: Einstellungen der Alarm-Extras (Teil 066) – Schalter und Regler für Web und Fenster. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.13: die Schalter der Alarm-Extras kommen in die bestehenden Abschnitte (Web und Fenster lesen dieselben Listen).
# Hier statt in 570, damit die grosse Liste dort unverändert bleibt.
# ----------------------------------------------------------------------------
TOGGLES.extend([
    ("Notifications", "push_actions", "Buttons in the push message: False alarm · Siren · Off (needs the address of this page for links)"),
    ("Notifications", "alarm_confirm2", "Double confirmation: a person alarm only when the AI and the thermal camera agree or the AI sees the person twice in a row (otherwise only a pre-alarm)"),
    ("Camping / protection", "arm_announce", "Announcement when arming: the loudspeaker says battery, Wi-Fi and camera - or what is missing"),
    ("Camping / protection", "presence_auto", "Protection on automatically when my phone is gone (choose the phone: Tools → Am I at home?)"),
    ("Night report", "report_strip", "Morning push short: one sentence and a picture strip of the night"),
])
SLIDERS.extend([
    ("Camping / protection", "back_hold_s", "«Is it you?»: person alarms wait (s)", 15, 300, 15),
])
