#@ Motion Watch – Teil 540: Web: Anleitung, Aufnahmen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
HELP_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Watch - Manual</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:900px;margin:0 auto}
.hsearch{display:flex;gap:8px;margin-bottom:12px}.hsearch input{flex:1;font-size:16px}
.toc{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.toc a{background:var(--field);border:1px solid var(--line);border-radius:999px;padding:5px 11px;font-size:13px;color:var(--txt);text-decoration:none;white-space:nowrap}
.toc a:hover{border-color:var(--acc)}
details.hsec{margin-bottom:10px}
details.hsec>summary{font-size:15px;letter-spacing:.02em;text-transform:none}
details.hsec>summary .ic{margin-right:8px}
.hsec h2{display:none}
.hsec h3{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);margin:14px 0 4px}
.hsec li{margin:5px 0;line-height:1.45}.hsec p{line-height:1.5}
.hsec ol,.hsec ul{padding-left:20px;margin:6px 0}
.hsec table{border-collapse:collapse;width:100%;margin:6px 0}.hsec td{border-top:1px solid var(--line);padding:6px 4px;vertical-align:top}
.hsec td:first-child{white-space:nowrap;padding-right:12px;font-weight:600}
.hsec dt{font-weight:700;margin-top:10px}.hsec dd{margin:3px 0 0 0;color:var(--mut);line-height:1.45}
.hsec code,.hsec pre{background:var(--field);border:1px solid var(--line);border-radius:6px;padding:1px 5px;font-size:12.5px;overflow-wrap:anywhere}
.hsec pre{padding:8px;white-space:pre-wrap;overflow-x:auto}
.tip{background:rgba(63,185,80,.1);border:1px solid rgba(63,185,80,.45);border-radius:10px;padding:8px 11px;margin:10px 0;line-height:1.45}
details.hsec.tips{border-color:var(--acc)}
.hsec.tips ul{list-style:none;padding-left:0}.hsec.tips li{padding:6px 0;border-bottom:1px solid var(--line)}
mark{background:#d2992299;color:inherit;border-radius:3px}
.nohit{display:none}
#hbody>div[lang]{display:none}.lang-de #hbody>div[lang=de],.lang-en #hbody>div[lang=en],.lang-fr #hbody>div[lang=fr],.lang-it #hbody>div[lang=it],.lang-rm #hbody>div[lang=rm]{display:block}
@media(max-width:520px){.hsec td:first-child{white-space:normal}}
</style></head><body>
<header>
  <h1>Motion Watch</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" onclick="window.print()" title="Print">🖨</button>
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <div class="hsearch"><input type="search" id="q" placeholder="Search …" autocomplete="off"><a class="btn sec" href="/quick" target="_blank" id="h-quick">📄</a></div>
  <div class="toc" id="toc"></div>
  <div id="hbody">
    <div lang="de"><section id="start" data-icon="🚀"><h2>Schnellstart: die ersten 10 Minuten</h2>
<ol>
<li><b>Strom anschliessen.</b> Nach etwa einer Minute ist Motion Watch bereit (mit Autostart startet es von selbst).</li>
<li><b>Mit dem Handy verbinden.</b> Entweder ist der Pi im selben WLAN wie das Handy (z. B. Handy-Hotspot), oder du verbindest das Handy mit dem <b>eigenen WLAN des Pi</b> (Name «MotionWatch», das Passwort steht unter <i>Alarm &amp; Camping → Schalter</i>).</li>
<li><b>Seite öffnen:</b> im eigenen WLAN <code>http://10.42.0.1:5000</code>, sonst <code>http://&lt;Adresse-des-Pi&gt;:5000</code>. Die Adresse kommt auch als Push-Nachricht, sobald der Pi ein Netz findet.</li>
<li><b>Passwort festlegen.</b> Beim ersten Besuch fragt die Seite danach. Danach fragt der Browser einmal (Benutzername beliebig).</li>
<li><b>Push-Nachrichten einrichten</b> (<i>Benachrichtigungen</i>) und mit «Test-Nachricht senden» prüfen.</li>
<li><b>Zonen zeichnen</b> (Reiter <i>Zonen</i>): Bereiche, die ignoriert werden sollen (Strasse, Bäume im Wind).</li>
<li><b>Scharf schalten:</b> 🛡 oben antippen oder <i>Alarm &amp; Camping → Schalter → Scharf schalten</i>. Der Countdown gibt dir Zeit, den Bereich zu verlassen.</li>
</ol>
<div class="tip">💡 <b>Tipp:</b> Lege die Seite als Lesezeichen oder als Symbol auf den Startbildschirm des Handys («Zum Home-Bildschirm»). Dann ist sie mit einem Tipp offen.</div>
</section>

<section id="live" data-icon="📺"><h2>Die Live-Seite</h2>
<h3>Kopfzeile</h3>
<p>Oben links stehen Name und <b>Version</b>. Daneben zeigen kleine Anzeigen nur, was gerade wichtig ist. Was im Normalzustand ist (kein Regen, Licht ok …), wird nicht angezeigt.</p>
<table><tr><td>🛡 Scharf / Unscharf</td><td>Alarme an oder aus. Antippen schaltet um.</td></tr>
<tr><td>Personen · ● Aufnahme</td><td>Was die Kamera jetzt sieht, ob gerade aufgenommen wird.</td></tr>
<tr><td>⛺ 🔋 ⏱ 💡 🌡 🔄 📡</td><td>Eingeschaltete Funktionen: Camping, Stromsparen, Zeitraffer, Licht, Wärmebild, Patrouille, eigenes WLAN.</td></tr>
<tr><td>⚠ ⚡ 💾</td><td>Warnungen: kein Passwort, Unterspannung, Speicher fast voll.</td></tr>
<tr><td>CPU · FPS</td><td>Auslastung und Temperatur des Pi, Bilder pro Sekunde.</td></tr></table>
<p>Rechts: 🔔 Alarmton im Browser, ☰ Ansicht (Anzeigen ein-/ausblenden), ▶ Einstellungen ein/aus, ⛶ Vollbild (nur Video, mit ✕ oben rechts zurück – funktioniert auch auf dem iPhone), ☀ hell/dunkel, DE/EN, ▲ Kopfzeile ausblenden.</p>
<h3>Bild und Steuerung</h3>
<ul><li><b>Stick:</b> mit dem Finger ziehen – je weiter, desto schneller dreht die Kamera. Der kleine Ring zeigt, wo die Kamera gerade hinschaut. «Mitte» fährt in die Mitte.</li>
<li>Von Hand steuern pausiert Verfolgung und Patrouille für ein paar Sekunden.</li>
<li><b>Licht:</b> Weiss und Infrarot direkt Aus / Ein / Auto.</li>
<li><b>Relais:</b> jedes Relais Aus / Ein / Auto mit Auslöser.</li>
<li><b>🎧 Mithören</b> und <b>🎙 Gedrückt halten zum Sprechen</b> erscheinen, sobald Mikrofon bzw. Lautsprecher gewählt sind.</li>
<li>Doppelklick aufs Bild: nur noch Video, nochmals doppelklicken: zurück.</li></ul>
</section>

<section id="alarm" data-icon="🛡"><h2>Alarm &amp; Camping</h2><p><b>Modus (ab 2.95.47):</b> ein Schalter für das ganze Gerät, oben in «Camping / Schutz» (auch im Fenster): ⛺ Camping-Wache · 🔥 Lagerfeuer-Spiele (Spielecke offen im bestehenden WLAN, die Wache schaut sparsam weiter; zur eingestellten Zeit oder bei knappem Akku zurück zur Camping-Wache) · 🎮 Gamer (nur mit Netzstrom: Powermodus, alle Spiele, Wache nach Wahl; auf Akku zurück zu den Lagerfeuer-Spielen) · 🏠 Zuhause · 🦌 Wildbeobachtung (keine Sirene, kein Licht von selbst) · 🌙 Nachtwache · 🔕 Transport. «Eigene Einstellungen» stellt alles zurück, wie es vor dem ersten Modus war.</p><p><b>📺 TV-Anzeige und Internet vom Handy (ab 2.95.51):</b> Unter dem Modus zeigt «Am HDMI zeigen» eine grosse Spielseite auf dem Fernseher am Pi (Raspberry Pi OS mit Desktop und Chromium nötig): links das Bild des Simulators oder der Kamera, rechts der Spielassistent, der QR-Code zum Mitspielen, die Zeit, die Spieler und die Rangliste. Bei Lagerfeuer und Gamer geht sie von selbst an. Den Link kann auch jeder andere Bildschirm im gleichen Netz öffnen. Ein Handy am USB-Kabel (Android «USB-Tethering», iPhone «Persönlicher Hotspot») gibt Motion Watch Internet – das eigene WLAN (Spiel-Netz) bekommt es dann auch.</p><p><b>📶 Netz-Check und 🛈 Infoseite (ab 2.95.52):</b> Werkzeuge → «Netz-Check der Mitspieler» misst bei allen Handys Reaktionszeit, Schwankung, Verluste, Download und Upload bis zu Motion Watch; Handys in der Spielecke messen von selbst, alle anderen über den QR-Code. Ist Motion Watch selbst das WLAN, kommt das Empfangssignal jedes Handys dazu, mit Tipps für schwache Verbindungen. Werkzeuge → «Infoseite für Gäste» zeigt deine Homepage von Motion Watch allen im gleichen WLAN, ohne Login und ohne Internet (QR-Code, auch auf der TV-Anzeige). Fragen aus dem Formular kommen als Push-Nachricht.</p><p><b>🖥 Simulator als Helfer (ab 2.95.53):</b> <b>KI-Rechenhilfe</b> (Werkzeuge): Läuft Motion Watch auch auf dem PC (im 3D-Simulator «Motion Watch auf diesem PC starten»), rechnet der PC die Erkennung für den Pi – der Pi findet ihn von selbst und rechnet wieder selbst, wenn der PC weg ist. <b>TV-Modus</b>: Taste T im Simulator oder «TV-Modus im 3D-Simulator» unter dem Modus – grosses Bild mit Spiel, QR-Code und Rangliste. Im Tab Simulator: <b>Aufstell-Planer</b> (wo Motion Watch hin soll, tote Winkel, Patrouille übernehmen), <b>Alarm-Rückblick in 3D</b> (ein Alarm wird nachgespielt), <b>KI-Prüfung mit Simulator-Bildern</b> (wie gut erkennt die KI bei Nacht, Regen, Nebel? mit Trainingsbildern als ZIP). Im Netz-Check: <b>Empfangs-Rundgang</b> – eine Karte, wo das WLAN gut ist.</p><p><b>📖 Almanach, 🪩 Disco-Licht, 🔒 Tunnel, 🎮 Spiele (ab 2.95.54):</b> Werkzeuge → «Überlebens-Almanach»: Tipps fürs Camping in der Schweiz zum Nachschlagen oder als Abendlektüre, offline, mit Suche, Rotlicht und Vorlesen (Adresse /almanach/, auch für Gäste). Unter dem Modus: «Disco-Licht» – das weisse Licht blitzt im Takt der Musik (Mikrofon) oder in festem Takt, höchstens 3-mal pro Sekunde, ein Alarm geht vor. Tab Simulator → «Simulator hinter einer Firewall»: Läuft der Simulator auf einem PC ohne Adminrechte, verbindet er sich mit Adresse und Code selbst zu Motion Watch. Die Spielesammlung ist in Touch-Spiele und Spiele mit Bildschirm-Tasten geteilt (Tetris, Racer, Breakout, Pong, Astray).</p>
<ul><li><b>Scharf / Unscharf:</b> nur scharf gibt es Alarme, Push-Nachrichten, Sirene und Aufnahmen. Der Countdown (einstellbar) gibt dir Zeit wegzugehen. «Sofort scharf» überspringt ihn.</li>
<li><b>Camping-Profil:</b> ein Schalter für alles Nötige: eigenes WLAN an, Kamera bleibt stehen (keine Patrouille/Verfolgung/Zeitraffer), Alarme, Aufnahmen und Stromsparen an, nach dem Countdown scharf. Ausschalten stellt deine vorherigen Einstellungen wieder her.</li>
<li><b>Eigenes WLAN (Hotspot):</b> der Pi macht sein eigenes WLAN – funktioniert ohne Handynetz. Name und Passwort unter <i>Schutz &amp; Netzwerk</i>.</li>
<li><b>Netzwerk:</b> «Automatisch» sucht zuerst bekannte Netze (z. B. den Handy-Hotspot, dann gibt es Internet und Push-Nachrichten) und schaltet sonst das eigene WLAN ein.</li>
<li><b>Autostart:</b> Motion Watch startet beim Einschalten von selbst, ohne Bildschirm.</li>
<li><b>Stromsparen:</b> wenige Bilder pro Sekunde, solange alles ruhig ist – bei der ersten Bewegung, einem Geräusch oder wenn jemand zuschaut sofort volle Geschwindigkeit.</li>
<li><b>🔋 USV-Akku (Waveshare UPS HAT, 2 × 18650):</b> wird selbst erkannt (I2C 0x42). Oben steht 🔌 bei Netzstrom bzw. 🔋 % und Restzeit im Akkubetrieb. Bei Stromausfall und wenn der Strom zurück ist kommt eine Push-Nachricht, bei 20 % eine Warnung, bei 8 % (einstellbar) schaltet sich der Pi sauber aus. Unter Akku die Kapazität einer Zelle eintragen (z. B. 3450 mAh).</li>
<li><b>🔋 Akku:</b> Kapazität der Powerbank eintragen (mAh, wie aufgedruckt), nach dem Laden «Akku ist jetzt voll» drücken. Oben steht dann z. B. «🔋 62 % · 14 h». Bei 15 % kommt eine Push-Nachricht. Es ist eine Schätzung aus dem Verbrauch des Pi (Powerbanks melden ihren Ladestand nicht).</li>
<li><b>Uhrzeit vom Handy:</b> ohne Internet holt sich der Pi die Uhrzeit vom Handy, damit Aufnahmen die richtige Zeit haben.</li></ul>
<p><b>🧭 Referenz-Scan (ab 2.95.97):</b> Werkzeuge → «Referenz-Scan» führt in vier Schritten: Kamera aufstellen und ausrichten, Raster einstellen (Richtungen, Höhen, Fotos pro Richtung), Referenz aufnehmen, vergleichen. Motion Watch fährt dabei mit dem Kopf alle Richtungen ab. Der Bericht zeigt pro Richtung Referenz und jetzt nebeneinander: rot = fehlt, blau = neu, orange = verändert. Vergleichen geht von Hand, beim Scharfschalten oder alle N Minuten (Einstellungen → Alarm &amp; Camping → Referenz-Scan), auf Wunsch mit Push-Meldung. Im 3D-Simulator starten die Knöpfe «Motion Watch: Referenz-Scan» und «Mit Referenz vergleichen» dasselbe; «Testhilfe: Velo wegnehmen» zeigt, wie ein fehlender Gegenstand gemeldet wird.</p></section>

<section id="notify" data-icon="🔔"><h2>Benachrichtigungen</h2>
<ul><li><b>📲 Web-Push (ohne App):</b> Benachrichtigungen → «Auf diesem Gerät einschalten». Braucht https: unter Benachrichtigungen «https über Tailscale einschalten» (in der Tailscale-Verwaltung einmal «HTTPS Certificates» erlauben), dann die Seite über <code>https://NAME.….ts.net/</code> öffnen. iPhone / iPad: diese https-Seite zum Home-Bildschirm hinzufügen und von dort einschalten. Funktioniert neben ntfy / Telegram.</li>
<li><b>ntfy</b> (empfohlen): App installieren, ein Thema abonnieren, die Adresse (z. B. <code>https://ntfy-me.com/&lt;dein-thema&gt;</code>) bei «Webhook / ntfy URL» eintragen, Typ «ntfy» wählen. Wichtig: in der App muss derselbe Server eingestellt sein wie in der Adresse.</li>
<li><b>Telegram</b> oder <b>Webhook</b> (z. B. Home Assistant) gehen auch.</li>
<li><b>Voralarm:</b> kurze Nachricht mit kleinem Bild schon bei der ersten Bewegung, bevor eine Person bestätigt ist.</li>
<li><b>Nachrichtentexte:</b> eigene Titel und Texte, mit Platzhaltern {name} {time} {date} {count} {camera} {link} {db}. Leer = Standardtext.</li>
<li><b>«Adresse dieser Seite für Links»:</b> dann öffnet ein Tipp auf die Nachricht direkt die Seite.</li>
<li><b>🔔 Alarmton im Browser:</b> oben die Glocke antippen und «Ton an». Die Seite muss offen bleiben (auch im Hintergrund).</li></ul>
<div class="tip">💡 <b>Tipp:</b> Nach jeder Änderung «Test-Nachricht senden». Kommt nichts, steht der Grund unter «Status» und im Ereignisprotokoll.</div>
</section>

<section id="detect" data-icon="🎯"><h2>Erkennung</h2>
<ul><li><b>Empfindlichkeit</b> und <b>Min. Objektgrösse</b> sind die wichtigsten Regler gegen Fehlalarme.</li>
<li><b>KI-Erkennung</b> erkennt Personen, Tiere und Fahrzeuge. «Bewegungs-Personen brauchen KI-Bestätigung» = weniger Fehlalarme, aber etwas langsamer.</li>
<li><b>Zonen</b> (Reiter <i>Zonen</i>): «Ignorieren» für Bäume, Strasse, Zeltwand; «Nur hier» wenn nur ein Bereich zählen soll.</li>
<li><b>Privatsphäre-Zone</b> (Reiter <i>Zonen</i>): der Bereich wird gleich nach der Kamera schwarz abgedeckt – im Live-Bild, in Aufnahmen, Fotos, Zeitraffer und für Gäste. Für Nachbarzelt, Weg, fremde Fenster. Wichtig für den Datenschutz: fremde Personen und öffentlichen Grund nicht dauernd filmen.</li>
<li>Regen, Wind, Schatten und Schwachlicht werden automatisch erkannt und ausgeglichen (Feineinstellungen).</li>
<li><b>Auto-Abstimmung</b> lernt die Szene selbst; «Neu kalibrieren», wenn sich die Umgebung stark geändert hat (Szene dabei leer lassen).</li></ul>
</section>

<section id="camera" data-icon="📷"><h2>Kamera &amp; Servos</h2>
<ul><li><b>Grenzen:</b> wie weit die Kamera schwenken/neigen darf (Grad aus der Mitte) – schützt Kabel und Gehäuse.</li>
<li><b>Person verfolgen:</b> die Kamera dreht einer erkannten Person nach.</li>
<li><b>Patrouille:</b> die Kamera fährt zwischen Wegpunkten hin und her (Wegpunkt = aktuelle Position, Schwenk und Neigung, mit «+ Wegpunkt»; Anzeige z.B. 24/60 = 24 % links–rechts, 60 % unten–oben). Der Knopf 🔄 schaltet bei jedem Tippen weiter: Aus → hin und zurück (1-2-3-2-1) → Runde (1-2-3-1) → Aus.</li>
<li><b>Videoquelle:</b> Pi-Kamera, USB- oder Netzwerkkamera. Weitere Kameras im Reiter <i>Kameras</i>.</li>
<li><b>Servo-Treiber</b> (Feineinstellungen): PCA9685 und Adresse, Kanäle.</li><li><b>🚜 Mover (Kettenfahrzeug, ab 2.94.0):</b> steht Motion Watch auf einem kleinen Kettenfahrzeug, erscheint ein zweiter, grüner Stick: hoch = vorwärts, runter = rückwärts, seitlich = an Ort drehen. Den Motortreiber (Motor HAT mit PCA9685 + TB6612, I2C 0x60) findet Motion Watch von selbst – ohne ihn bleibt der Stick weg. Einstellungen unter Kamera &amp; Servos → Mover. Ohne neuen Befehl halten die Ketten nach 0,6 s an. Im 3D-Simulator: «Mover simulieren». In der Simulation lässt sich der Stick auch ohne Mover einblenden (Mover → «Simulation: den Stick auch ohne Mover … zeigen», ab 2.94.4) – zum Ausprobieren der Bedienung.</li></ul>
</section>

<section id="thermal" data-icon="🌡"><h2>Wärmebild</h2>
<ul><li>Wärmebildkamera wählen (Thermal-90 oder USB), «Wärmebild überlagern» einschalten.</li>
<li><b>Ausrichten:</b> mit «Zoom» und «Verschieben» so einstellen, dass eine warme Person im Wärmebild genau auf der Person im Kamerabild liegt.</li>
<li><b>Wärme-Alarm:</b> warmer Körper in der Zone. «Nur bewegte» ignoriert warme Steine und Motoren.</li>
<li>Der Status zeigt die höchste gemessene Temperatur.</li></ul>
</section>

<section id="lightsound" data-icon="💡"><h2>Licht &amp; Ton</h2>
<h3>Licht</h3>
<ul><li>Weiss und Infrarot: Aus / Ein / Auto. «Auto» = bei Alarm nur nachts, bei Alarm Tag und Nacht, oder die ganze Nacht (nach Sonnenuntergang, berechnet aus Breiten-/Längengrad unter <i>Einrichtung</i>).</li>
<li><b>Bild:</b> «nachts grau» ist ideal mit der NoIR-Kamera.</li></ul>
<h3>Mikrofon</h3>
<ul><li>Gerät wählen, Pegel beobachten. <b>Geräusch-Alarm</b>: lauter als der Hintergrund um X dB, mindestens Y Sekunden.</li>
<li><b>🎧 Mithören</b>: Ton live auf dem Handy, Lautstärke pro Gerät.</li>
<li><b>Ton in den Aufnahmen</b>: Videos werden mit Ton gespeichert.</li></ul>
<h3>Lautsprecher</h3>
<ul><li>Eingebaut (USB) oder <b>Bluetooth</b>: «Bluetooth-Lautsprecher suchen» (Lautsprecher im Kopplungsmodus), dann «Verbinden».</li>
<li><b>Sirene bei Alarm</b> (nur wenn scharf), Ton, Lautstärke, Dauer. Eigene Töne (.wav/.mp3) in <code>~/.config/motionwatch/sounds</code>.</li>
<li><b>🎙 Sprechen</b>: Knopf gedrückt halten. Braucht die sichere Seite <code>https://…:5001</code> (Handys erlauben das Mikrofon nur dort).</li></ul>
</section>

<section id="rec" data-icon="🎬"><h2>Aufnahmen &amp; Zeitraffer</h2>
<ul><li>Bei Alarm werden Videos (mit Vorlauf und Ton) und Schnappschüsse gespeichert.</li>
<li>Reiter <i>Aufzeichnungen</i>: ansehen, filtern, ⭐ Favoriten (werden nie automatisch gelöscht), mehrere als ZIP herunterladen, Statistik pro Tag.</li>
<li><b>Bild für andere Programme:</b> unter <i>Einstellungen → Web-Stream</i> «Bild für andere Programme» einschalten. Dann gibt es eine geheime Adresse für das Video (MJPEG) und ein Standbild, z. B. für Home Assistant, Frigate, Blue Iris oder VLC. <b>RTSP</b> zusätzlich: mediamtx installieren (<code>https://github.com/bluenviron/mediamtx/releases</code>, Datei «linux_arm64» entpacken nach <code>~/mediamtx/</code>), dann «RTSP-Video» einschalten. RTSP braucht Rechenleistung.</li>
<li><b>Orte &amp; Karte:</b> Fotos und Videos mit GPS-Position (vom Handy oder fester Ort) bekommen einen Ort. Filter «Ort» zeigt nur einen Ort (oder «Ohne Ort»). 🗺 <i>Karte</i> zeigt alle Orte mit Anzahl; Punkt antippen → Vorschau, «Nur diesen Ort zeigen», ✎ umbenennen. Kartenhintergrund und Ortsnamen kommen von OpenStreetMap (abschaltbar unter <i>Einstellungen → Setup</i>).</li>
<li>Die ältesten Aufnahmen werden gelöscht, wenn der Ordner zu gross oder die Speicherkarte fast voll ist.</li>
<li><b>Zeitraffer:</b> alle N Minuten ein Foto von einer festen Position, daraus ein Video («Video erstellen»). Ein Alarm hat immer Vorrang. Die Zeitraffer-Videos erscheinen auch unter <i>Aufzeichnungen</i> (mit ⏱); der Typ «Zeitraffer» zeigt dort zusätzlich alle Einzelfotos.</li></ul>
</section>

<section id="diary" data-icon="🦊"><h2>Tagebuch, Nachtbericht &amp; Gäste</h2>
<ul><li><b>Tier-Tagebuch</b> (Reiter <i>Tagebuch</i>): von jedem Tier-Besuch wird das beste Bild automatisch gespeichert, mit Tierart, Datum und Dauer. Filtern nach Tierart, ★ = behalten, ⤴ teilen (z. B. WhatsApp), ⤓ herunterladen. Ältere Einträge werden nach der eingestellten Zeit gelöscht (★ nie).</li>
<li>Die KI kennt Vogel, Katze, Hund, Pferd, Schaf, Kuh, Bär (und ein paar exotische). Ein Fuchs erscheint meist als «Hund» oder «Katze», ein Wildschwein oft als «Schaf» oder «Bär».</li>
<li><b>Nachtbericht:</b> jeden Morgen (einstellbar, Standard 7 Uhr) eine Push-Nachricht: was in der Nacht (ab 20 Uhr) los war – Personen, Tiere, Geräusche, Wärmebild – mit dem besten Bild. «Jetzt senden» zum Ausprobieren. Einstellungen unter <i>Benachrichtigungen → Nachtbericht</i>.</li>
<li><b>Gast-Zugang</b> (<i>System &amp; Netz</i>): «Neuen Link erstellen», Gültigkeit wählen (2 h bis unbegrenzt), Link teilen. Gäste sehen nur das Live-Bild (mit Privatsphäre-Zonen), kein Passwort nötig, sie können nichts verstellen. «Gast-Zugang beenden» sperrt den Link sofort. Der Gast muss den Pi erreichen: im selben WLAN / Hotspot oder über Tailscale.</li>
<li><b>App-Symbol:</b> iPhone: in Safari <i>Teilen → Zum Home-Bildschirm</i>. Android: Chrome-Menü <i>⋮ → Zum Startbildschirm hinzufügen</i>. Motion Watch öffnet sich dann wie eine App, ohne Browser-Leisten.</li></ul>
</section>

<section id="relay" data-icon="⚡"><h2>Relais &amp; Zeitplan</h2>
<ul><li><b>Relais:</b> Aus / Ein / Auto. Auto schaltet ein, solange der Auslöser zutrifft (Person, Bewegung, Voralarm, Wärme, Geräusch, Tierart …), plus Haltezeit.</li>
<li><b>Warnlampe bei Fernzugriff:</b> Relais auf Auto, Auslöser «Fernzugriff». Es ist an, solange jemand über Tailscale zuschaut – auch wenn das Gerät unscharf ist. Eine kleine LED (mit Vorwiderstand ca. 330 Ω) kann direkt an den GPIO, eine grössere Lampe über ein Relais-Modul.</li>
<li><b>Zeitplan:</b> schaltet Funktionen zu bestimmten Zeiten ein oder aus, z. B. nachts scharf, tagsüber Stromsparen. Auch «bei Sonnenuntergang» und Ausnahmedaten.</li></ul>
</section>

<section id="system" data-icon="⚙"><h2>System &amp; Netz</h2>
<ul><li><b>System:</b> CPU, Temperatur, Stromversorgung (Spannung, Unterspannung), freier Speicher, Version.</li>
<li><b>📜 Ereignisprotokoll:</b> alles wird sofort auf die Speicherkarte geschrieben (auch alle 15 Minuten eine Statuszeile mit CPU, Temperatur, WLAN, Speicher, Akku). «Ganzes Protokoll & Archiv» zeigt den heutigen Tag und jeden früheren Tag als eigene Datei (gepackt, 60 Tage aufbewahrt, einstellbar unter Einrichtung) – filtern, suchen, herunterladen.</li>
<li><b>🔐 Bedienmodus:</b> «Bedienmodus (Einstellungen sperren)» unter System – PIN festlegen (4–8 Ziffern), dann sind alle Einstellungen gesperrt. Bedienbar bleiben: scharf/unscharf, Camping-Profil, die wichtigsten Schalter (Erkennung, Aufnahme, Benachrichtigungen, Stromsparen, Patrouille, Zeitraffer …), Licht, Kamera, Mithören/Sprechen, Aufnahmen ansehen. «Entsperren» mit der PIN; nach 5 falschen PINs 5 Minuten Pause.</li>
<li><b>⏸ Programm pausieren:</b> Dauer wählen (5 Minuten bis 12 Stunden) – Motion Watch schaltet sich sofort aus (Aufnahme wird fertig gespeichert) und startet danach von selbst wieder. In der Zwischenzeit zeigt die Seite einen Countdown und «Jetzt starten». Während der Pause gibt es keine Überwachung und keine Alarme.</li>
<li><b>⏻ Pi ausschalten / ↻ neu starten:</b> laufende Aufnahme wird vorher fertig gespeichert. Strom erst trennen, wenn die grüne LED dunkel bleibt.</li>
<li><b>🔒 Web-Passwort</b>, <b>⬇ Einstellungen sichern / ⬆ laden</b> (die Datei enthält auch deine Zugangsdaten – privat aufbewahren).</li>
<li><b>WLAN:</b> Netze suchen und verbinden, gespeicherte Netze.</li>
<li><b>🌐 Fernzugriff (Tailscale):</b> unter System steht, ob Tailscale verbunden ist, die Adresse für unterwegs (http://100.…:5000/) und wer gerade von aussen zuschaut. Oben erscheint dann «🌐 Fern: Gerätename». Auf Wunsch kommt eine Push-Nachricht (Benachrichtigungen). Einrichten: <code>curl -fsSL https://tailscale.com/install.sh | sh</code>, dann <code>sudo tailscale up</code>, auf dem Handy die Tailscale-App mit demselben Konto.</li>
<li><b>Web-Stream:</b> Bildqualität und Breite – kleiner = weniger Daten über den Handy-Hotspot.</li>
<li><b>Einrichtung:</b> Standort (für Sonnenauf-/untergang), Anwesenheit, Warnungen (Temperatur, Speicher).</li>
<li><b>Automatisches Update:</b> «Neue Versionen automatisch installieren» einschalten und die Stunde wählen (Standard 12 Uhr). Installiert wird nur, wenn nichts los ist (unscharf, keine Aufnahme, keine Person – «auch wenn scharf» erlaubt es auch scharf). Startet die neue Version dreimal nicht, kehrt Motion Watch von selbst zur vorherigen zurück.</li>
<li><b>🔏 Signierte Updates:</b> jede Version ist mit dem geheimen Schlüssel des Entwicklers unterschrieben. Motion Watch installiert nur Versionen mit gültiger Unterschrift – selbst wer in das GitHub-Konto eindringt, kann so kein fremdes Programm auf die Geräte bringen. In der Liste steht «🔏 signiert» oder «⚠ nicht signiert». Eigene, unsignierte Versionen nur mit «Auch nicht signierte Versionen annehmen».</li>
<li><b>Privates GitHub-Repository:</b> unter Updates zusätzlich den <b>GitHub-Schlüssel (Token)</b> eintragen – auf github.com unter Settings → Developer settings → Fine-grained tokens erstellen, nur für dieses Repository, Recht «Contents: Read-only». Der Schlüssel wird nur an GitHub gesendet und nie angezeigt.</li>
<li><b>Updates:</b> Quelle eintragen (Internet-Adresse einer versions.json oder ein Ordner/USB-Stick), «Nach Versionen suchen», Version wählen. Ältere Versionen bleiben für den Weg zurück. <b>Test-Modus</b> («Neue Versionen sofort holen»): schaut jede Minute auf GitHub und installiert eine neue Version gleich (auch wenn scharf, nie während einer Aufnahme) – zum Testen, danach wieder ausschalten.</li></ul>
</section>

<section id="window" data-icon="🖥"><h2>Desktop-Fenster auf dem Pi</h2>
<table><tr><td>Doppelklick aufs Video</td><td>nur Video</td></tr><tr><td>⛶ / F11 / Esc</td><td>Video-Vollbild / ganze Seite als Vollbild / zurück</td></tr>
<tr><td>Strg+B</td><td>Einstellungsbereich ein/aus</td></tr><tr><td>Strg+T / Strg+L</td><td>hell/dunkel, Sprache</td></tr>
<tr><td>Pfeiltasten / Pos1</td><td>Kamera bewegen / Mitte</td></tr><tr><td>Rechtsklick aufs Video</td><td>Felder ein-/ausblenden</td></tr></table>
<p>Die Einstellungen sind gleich gegliedert wie auf der Webseite. Der Knopf «Anleitung» öffnet diese Seite.</p>
</section>

<section id="tips" data-icon="🧭" class="tips"><h2>Tipps &amp; Tricks</h2>
<ul>
<li>🔍 <b>Einstellung suchen:</b> im Einstellungsbereich oben ins Suchfeld tippen (z. B. «Passwort», «Sirene», «WLAN») – alles andere verschwindet, die Treffer sind blau umrandet. ✕ oder Esc zeigt wieder alles.</li>
<li>💬 <b>Feedback an den Entwickler:</b> System → «Feedback an den Entwickler» (im Fenster: Einrichtung). Ideen, Fehler, Lob – anonym, ohne Absender. Ohne Internet wartet die Nachricht und geht später weg.</li>
<li>🎞 <b>Markierungen in Aufnahmen:</b> Aufnahme → «Markierungen in Aufnahmen und Alarmbildern»: dünne Eckmarken (Standard, das Gesicht bleibt frei), keine, oder rote Rahmen wie im Live-Bild.</li>
<li>⚡ <b>Schnellschalter neben dem Stick</b> (grün = an): 🌡 Wärmebild über das Live-Bild, 🏷 Objekte markieren, 💡 weisses Licht, 🔴 IR-Licht, 🎧 Mithören, ⚡ je Relais (ein / automatisch), 🎯 Person folgen, 🔄 Patrouille, ⏺ jetzt aufnehmen (max. 10 min, rot während der Aufnahme, nochmals tippen = stopp), 📷 Foto in die Aufnahmen. Grau = nicht angeschlossen.</li>
<li>🕹 <b>Steuer-Stick im Vollbild</b> (Handy, Tablet, PC): das Bild füllt den ganzen Bildschirm, der Stick liegt durchsichtig unten rechts darüber. Nach 3 s ohne Berührung wird er blass, beim Berühren wieder deutlich. Daneben: ◎ Mitte, 🎧 Mithören; ⇆ oben neben ✕ legt den Stick auf die andere Seite.</li>
<li>🟢 <b>Übersicht in den Einstellungen:</b> der Pfeil eines Themas ist grün, wenn seine Hauptfunktion eingeschaltet ist (z. B. Nachtbericht, Zeitraffer, Sicherung), sonst grau. Der Pfeil einer Gruppe ist grün, wenn mindestens ein Thema darin läuft. Im Fenster auf dem Pi: grüner Titel.</li>
<li>📱 <b>SMS über LTE-Stick</b> (Benachrichtigungen → SMS): mit einem USB-LTE-Stick und SIM-Karte kommt der Alarm (Person, Sabotage, warmer Körper, Geräusch) als SMS – ab Werk nur, wenn kein Internet da ist. Funktioniert mit ModemManager (<code>sudo apt install modemmanager</code>), AT-Befehlen oder Huawei-HiLink-Sticks (192.168.8.1). Pause und Tageslimit schützen vor Kosten; «Test-SMS senden» prüft alles.</li>
<li>🎬 <b>Demo-Modus:</b> <code>python3 webcam_bewegung_X.py --demo</code> (für eine Online-Demo zusätzlich <code>--headless --port 8080</code>) zeigt eine gezeichnete Camping-Szene, in der ab und zu eine Person, ein Hund oder ein Bär vorbeikommt – Alarm, Aufnahme, Tagebuch und Abschreckung reagieren wie echt. Eigene Einstellungen (im Temp-Ordner), «DEMO» im Kopf, nichts am Computer wird verändert.</li>
<li>🏠 <b>MQTT / Home Assistant</b> (System &amp; Netz): Broker-Adresse (z. B. der Mosquitto-Add-on von Home Assistant), Benutzer und Passwort eintragen, «MQTT ein». Home Assistant zeigt Motion Watch dann von selbst als Gerät: Alarmanlage (scharf/unscharf schalten), Person, Bewegung, Tier, Aufnahme, Akku, Temperatur und das letzte Alarmbild. Befehle auch über <code>motionwatch/&lt;id&gt;/cmd/arm</code> (ARM_AWAY / DISARM), <code>…/cmd/light_white</code> (on/off/auto).</li>
<li>🛰 <b>Mehrere Geräte:</b> Reiter Kameras → «Weitere Motion-Watch-Geräte»: Bild, scharf/Alarm, Akku und letztes Ereignis jedes Geräts, einzeln oder alle zusammen scharf/unscharf schalten. «Im Netzwerk suchen» findet Geräte im gleichen Netz und über Tailscale; Geräte mit Passwort brauchen dieses einmal.</li>
<li>⤴ <b>Teilen mit Logo:</b> Tagebuch-Bilder, Schnappschüsse, Aufnahmen und Zeitraffer (Knopf ⤴ in der Aufnahme-Ansicht) sowie das Bild im Nachtbericht bekommen unten rechts einen dezenten Streifen «Motion Watch» mit Datum. Abschaltbar unter Aufnahme.</li>
<li>🦊 <b>Gezielte Abschreckung</b> (Licht &amp; Ton → Abschreckung): für Person, grosses Tier (Bär, Kuh, Pferd …), kleines Tier (Katze, Hund, Vogel) und warmen Körper (Wärmebild) je eine eigene Reaktion – Ton (neu: hohes Pfeifen, Knallen/Klatschen oder eigene Töne) und/oder Lichtblitze mit dem weissen Licht. Dauer und Pause einstellbar; «auch wenn unscharf» z. B. für den Garten. Tiere brauchen die KI-Erkennung.</li>
<li>🚨 <b>Diebstahlschutz</b> (Alarm &amp; Camping): wenn scharf gibt es eine dringende Push-Nachricht mit Bild und die Sirene, sobald die Kamera <b>abgedeckt oder weggedreht</b> wird, das Gerät <b>bewegt oder umgeworfen</b> wird (Bewegungssensor MPU-6050 an I2C 0x68, ca. 3 Fr., optional) oder der <b>Strom getrennt</b> wird (mit USV-Akku). Während sich der Kamerakopf selbst bewegt (Patrouille, Verfolgen, Joystick), lernt die Bildprüfung neu.</li>
<li>☁️ <b>Sicherung der Alarm-Aufnahmen:</b> Aufnahmen &amp; Zeitraffer → Sicherung. Fertige Alarm-Aufnahmen (scharf oder mit Person) gehen automatisch auf einen WebDAV-Ordner (Nextcloud: <code>https://…/remote.php/dav/files/BENUTZER/MotionWatch/</code> mit App-Passwort, Synology/QNAP-NAS, viele Clouds), in einen Ordner (USB-Stick, eingebundenes NAS) oder als Video zu Telegram. Ein Unterordner pro Tag. «Sicherung testen» prüft die Einstellungen.</li>
<li>🧭 <b>Einrichtungs-Assistent:</b> erscheint beim ersten Öffnen der Seite – Sprache und Gerätename, Push-Nachrichten (ntfy-Thema mit QR-Code und Test-Nachricht), Web-Passwort, QR-Codes für weitere Geräte. Jederzeit wieder unter System → «Einrichtungs-Assistent». «Kurzanleitung (QR)» ergibt eine Karte zum Ausdrucken mit QR-Codes für das eigene WLAN des Pi und die Seite. Im Fenster auf dem Pi: Einrichtung → «QR-Code fürs Handy».</li>
<li>🔗 <b>Ein Symbol für zu Hause und unterwegs:</b> die Seite über die Tailscale-Adresse zum Home-Bildschirm hinzufügen (z. B. <code>http://NAME-DES-PI:5000</code> oder die 100.…-Adresse aus der Tailscale-App). Zu Hause verbindet Tailscale direkt im WLAN, unterwegs übers Internet – die Tailscale-App muss eingeschaltet sein. Nur im eigenen WLAN des Pi ohne Internet die lokale Adresse nehmen (z. B. <code>http://10.42.0.1:5000</code>). Oben zeigt «🌐 Fern», wenn du über Tailscale verbunden bist.</li>
<li>📱 <b>Wie eine App:</b> Motion Watch auf den Home-Bildschirm legen (iPhone: Teilen → Zum Home-Bildschirm). Dann gibt es auch auf dem iPhone ein richtiges Vollbild. Oben rechts erscheint dort der Knopf <b>⟳</b> zum Neuladen; läuft nach einem Update eine neue Version, erscheint unten «Neu laden».</li>
<li>🦊 <b>Tierfotos sammeln:</b> KI-Erkennung eingeschaltet lassen, Kamera auf einen Futterplatz oder Wildwechsel richten – am Morgen im <i>Tagebuch</i> nachsehen.</li>
<li>🌙 <b>Vor der ersten Nacht testen:</b> scharf schalten, einmal durchs Bild laufen und prüfen: Push kommt an, Aufnahme ist da, Sirene/Licht reagieren.</li>
<li>🌳 <b>Fehlalarme durch Äste:</b> Bäume und Büsche als «Ignorieren»-Zone zeichnen und die Mindestgrösse etwas erhöhen. Bei Wind hilft die automatische Wind-Erkennung.</li>
<li>🐗 <b>Tiere vertreiben:</b> Sirene «bei Alarm» plus weisses Licht «bei Alarm, nur nachts» – das schreckt die meisten Tiere zuverlässig ab. Für die eigene Nachtruhe die Sirene kurz (5–10 s) einstellen.</li>
<li>🔴 <b>Infrarot und Spiegelungen:</b> IR-Licht nicht durch eine Scheibe oder nahe an eine Zeltwand richten – das blendet die Kamera.</li>
<li>🔇 <b>Stille Überwachung:</b> Sirene aus, nur Push-Nachrichten und Glocke im Browser – niemand am Platz wird geweckt.</li>
<li>🔋 <b>Strom sparen:</b> Camping-Profil (enthält Stromsparen), Bildbreite im Web-Stream kleiner, Mithören nur kurz. Eine Powerbank mit 5 V / 3 A oder mehr verwenden; bei «Unterspannung» das Kabel oder die Powerbank wechseln.</li>
<li>📶 <b>Wenig Datenvolumen:</b> Voralarm-Bild bleibt klein (640 px); Live-Bild nur öffnen, wenn nötig (der Pi sendet nur, wenn jemand zuschaut).</li>
<li>🎤 <b>Mikrofon:</b> ein Stück Schaumstoff als Windschutz verhindert Fehlalarme bei Wind. Die Servos stören nicht – der Geräusch-Alarm pausiert, solange sie sich bewegen.</li>
<li>🔊 <b>Bluetooth-Lautsprecher</b> schalten sich oft nach einiger Zeit selbst aus. Der Pi verbindet sie wieder, sobald sie an sind – für die Nacht einen Lautsprecher ohne Auto-Aus wählen.</li>
<li>🧭 <b>Kamera ausrichten:</b> mit dem Stick die beste Position suchen und als Wegpunkt bzw. als Zeitraffer-Position übernehmen.</li>
<li>🕒 <b>Falsche Uhrzeit</b> in den Aufnahmen: einmal die Seite mit dem Handy öffnen – der Pi übernimmt die Uhrzeit des Handys.</li>
<li>💾 <b>Wichtige Aufnahmen</b> mit ⭐ markieren – sie werden nie automatisch gelöscht.</li>
<li>🔁 <b>Neue Version ausprobieren</b> ohne Risiko: unter Updates jederzeit zur vorherigen Version zurückwechseln.</li>
<li>📱 <b>Glocke im Browser</b> nur auf einem Gerät einschalten, das nachts offen bleibt – sonst klingelt es überall.</li>
</ul></section>

<section id="privacy" data-icon="🔏"><h2>Datenschutz &amp; Sicherheit</h2>
<p><b>Grundsatz:</b> Motion Watch arbeitet auf dem Gerät selbst. Bilder, Aufnahmen, Ton und Einstellungen bleiben auf der Speicherkarte – es gibt keine Hersteller-Cloud und kein Konto.</p>
<ul>
<li><b>Was auf dem Gerät gespeichert wird:</b> Aufnahmen und Schnappschüsse (Ordner «recordings», alte werden bei vollem Speicher gelöscht – Favoriten nie), Tier-Tagebuch (Bilder), Ereignisprotokoll (60 Tage, einstellbar), Einstellungen. Das Web-Passwort ist nur als sicherer Hash gespeichert.</li>
<li><b>Was das Gerät nur verlässt, wenn du es einschaltest:</b> Push-Nachrichten (ntfy / Telegram / Webhook – mit Bild, über deren Server), Web-Push (über Apple / Google / Mozilla, verschlüsselt), Sicherung der Clips (dein WebDAV / NAS / Telegram), MQTT (dein Broker), SMS (Mobilfunk), Updates (GitHub; nur signierte Versionen werden installiert), Fernzugriff (Tailscale, verschlüsselt).</li>
<li><b>Ton:</b> Mikrofon, Mithören und Ton in den Aufnahmen sind ab Werk aus. Gespräche aufzunehmen ist in vielen Ländern nur mit Einverständnis erlaubt.</li>
<li><b>Privatsphäre-Zonen</b> (Reiter Zonen): Bereiche wie Nachbars Garten, Weg oder Fenster werden schwarz übermalt – im Live-Bild, in Aufnahmen und Bildern.</li>
<li><b>Gäste-Links</b> zeigen nur das Live-Bild, sind befristet und lassen sich jederzeit ungültig machen.</li>
<li><b>Schutz vor Fremden:</b> Web-Passwort (beim Einrichten), Sperre nach 8 falschen Versuchen, Bedienmodus mit PIN, signierte Updates, Fernzugriff nur über Tailscale.</li>
</ul>
<p><b>Rechtliches (Schweiz: DSG, EU: DSGVO – keine Rechtsberatung):</b> Filme nur deinen eigenen Platz. Öffentlicher Grund, Wege und fremde Grundstücke gehören nicht ins Bild (sonst Privatsphäre-Zonen nutzen). Weise mit einem Hinweis («Videoüberwachung») auf die Kamera hin und informiere Mitreisende und Gäste. Auf Campingplätzen gilt zudem die Platzordnung. Aufnahmen nur so lange behalten wie nötig.</p>
</section>
<section id="faq" data-icon="🛠"><h2>Probleme lösen</h2>
<dl>
<dt>Die Seite lässt sich nicht öffnen</dt><dd>Ist das Handy im richtigen WLAN (eigenes WLAN des Pi oder dasselbe Netz)? Adresse mit <code>:5000</code> am Ende? Im eigenen WLAN immer <code>http://10.42.0.1:5000</code>.</dd>
<dt>Die Seite zeigt eine alte Version</dt><dd>Oben links steht die Version. Läuft noch eine alte Kopie (z. B. vom Autostart), das neue Programm einfach von Hand starten – es übernimmt. Danach Seite neu laden.</dd>
<dt>Kein Bild</dt><dd>Unter <i>Kamera &amp; Servos → Videoquelle</i> «Nach Kameras suchen». Pi-Kamera: Flachbandkabel prüfen.</dd>
<dt>Push-Nachrichten kommen nicht</dt><dd>«Test-Nachricht senden» und Status lesen. Bei ntfy: derselbe Server in App und Adresse. Ohne Internet (nur eigenes WLAN) können keine Push-Nachrichten verschickt werden – dann hilft die Glocke im Browser.</dd>
<dt>Autostart startet nicht</dt><dd>Im Terminal: <code>systemctl --user status motionwatch</code>. Einmalig <code>sudo python3 webcam_bewegung_X.py --allow-wifi</code> ausführen (erlaubt den Start ohne Anmeldung).</dd>
<dt>Bild nachts schwarz, aber Bewegungen werden markiert</dt><dd>Die Szene ist zu dunkel für die normale Kamera. «Im Dunkeln auch das sichtbare Bild aufhellen» (Erkennung → Schwachlicht) hellt es so weit wie möglich auf – bei völliger Dunkelheit hilft nur Licht: Infrarot-Lampe + NoIR-Kamera (unsichtbar) oder die weisse Lampe.</dd>
<dt>Viele Fehlalarme</dt><dd>Zonen zeichnen, Empfindlichkeit senken, Mindestgrösse erhöhen, «KI-Bestätigung» einschalten.</dd>
<dt>Servos zittern oder fahren an den Anschlag</dt><dd>PCA9685 verwenden (Servo-Treiber), Grenzen in Grad verkleinern, eigene 5-V-Versorgung für die Servos.</dd>
<dt>«Unterspannung»</dt><dd>Kürzeres/dickeres USB-C-Kabel oder stärkere Powerbank. Unterspannung kann Abstürze und kaputte Aufnahmen verursachen.</dd>
<dt>Kein Ton über Bluetooth</dt><dd>Lautsprecher an und in Reichweite? «Verbinden» erneut tippen. Das Programm muss als normaler Benutzer laufen (nicht mit sudo).</dd>
<dt>Sprechen geht nicht</dt><dd>Nur auf der sicheren Seite <code>https://…:5001</code>. Zertifikatswarnung einmal bestätigen und das Mikrofon erlauben.</dd>
</dl></section>

<section id="setup" data-icon="🧰"><h2>Einrichtung auf dem Raspberry Pi</h2>
<pre>sudo apt install python3-pil.imagetk python3-tk python3-gpiozero ffmpeg python3-picamera2 alsa-utils openssl bluez pulseaudio-utils
pip install opencv-python numpy pillow flask psutil</pre>
<ul><li>I2C und SPI einschalten (<code>sudo raspi-config</code>), in <code>/boot/firmware/config.txt</code> unter <code>[all]</code>: <code>dtoverlay=spi0-0cs</code>.</li>
<li>Einmalig: <code>sudo python3 webcam_bewegung_X.py --allow-wifi</code> (WLAN, Uhrzeit, Autostart, Ausschalten, Watchdog).</li>
<li>Starten: <code>python3 webcam_bewegung_X.py</code> (Fenster + Webseite) oder <code>--headless</code> (nur Webseite).</li>
<li>Einstellungen, Protokoll, Töne: <code>~/.config/motionwatch/</code> – bleiben bei neuen Versionen erhalten.</li></ul>
</section>
</div>
    <div lang="en"><section id="start" data-icon="🚀"><h2>Quick start: the first 10 minutes</h2>
<ol>
<li><b>Connect the power.</b> After about a minute Motion Watch is ready (with autostart it starts by itself).</li>
<li><b>Connect the phone.</b> Either the Pi is in the same Wi-Fi as the phone (e.g. the phone hotspot), or you join the <b>own Wi-Fi of the Pi</b> (name «MotionWatch», the password is shown under <i>Alarm &amp; camping → Switches</i>).</li>
<li><b>Open the page:</b> in the own Wi-Fi <code>http://10.42.0.1:5000</code>, otherwise <code>http://&lt;address-of-the-pi&gt;:5000</code>. The address also comes as a push message when the Pi joins a network.</li>
<li><b>Set a password.</b> The page asks for it at the first visit; then the browser asks once (any user name).</li>
<li><b>Set up push messages</b> (<i>Notifications</i>) and check them with «Test notification».</li>
<li><b>Draw zones</b> (tab <i>Zones</i>): areas to ignore (road, trees in the wind).</li>
<li><b>Arm:</b> tap 🛡 at the top or <i>Alarm &amp; camping → Switches → Arm</i>. The countdown gives you time to leave the area.</li>
</ol>
<div class="tip">💡 <b>Tip:</b> save the page as a bookmark or as an icon on the home screen of the phone («Add to Home Screen»).</div>
</section>

<section id="live" data-icon="📺"><h2>The live page</h2>
<h3>Header</h3>
<p>Top left: name and <b>version</b>. Small badges show only what matters right now; things in their normal state (no rain, light ok …) are not shown.</p>
<table><tr><td>🛡 Armed / disarmed</td><td>Alarms on or off. Tap to switch.</td></tr>
<tr><td>Persons · ● REC</td><td>What the camera sees now, whether it is recording.</td></tr>
<tr><td>⛺ 🔋 ⏱ 💡 🌡 🔄 📡</td><td>Features that are on: camping, power saving, timelapse, light, thermal, patrol, own Wi-Fi.</td></tr>
<tr><td>⚠ ⚡ 💾</td><td>Warnings: no password, under-voltage, memory almost full.</td></tr>
<tr><td>CPU · FPS</td><td>Load and temperature of the Pi, pictures per second.</td></tr></table>
<p>Right: 🔔 alarm sound in the browser, ☰ view (show / hide badges), ▶ settings panel, ⛶ full screen (video only, ✕ top right to go back – works on iPhone too), ☀ light/dark, DE/EN, ▲ hide the header.</p>
<h3>Picture and controls</h3>
<ul><li><b>Stick:</b> drag with the finger – the further, the faster. The small ring shows where the camera looks. «Centre» moves to the middle.</li>
<li>Manual control pauses tracking and patrol for a few seconds.</li>
<li><b>Lights:</b> white and infrared Off / On / Auto.</li>
<li><b>Relays:</b> each relay Off / On / Auto with a trigger.</li>
<li><b>🎧 Listen</b> and <b>🎙 Hold to talk</b> appear when a microphone / loudspeaker is chosen.</li>
<li>Double-click the picture: video only; double-click again: back.</li></ul>
</section>

<section id="alarm" data-icon="🛡"><h2>Alarm &amp; camping</h2><p><b>Mode (from 2.95.47):</b> one switch for the whole device, at the top of «Camping / protection» (also in the window): ⛺ camping guard · 🔥 campfire games (game corner open, the guard watches on sparingly; back to the camping guard at the set time or when the battery gets low) · 🎮 gamer (only with mains power: power mode, all games, guard if you want; on battery back to the campfire games) · 🏠 home · 🦌 wildlife watching (no siren, no light by itself) · 🌙 night guard · 🔕 transport. «Own settings» brings everything back as it was before the first mode.</p><p><b>📺 TV view and internet from the phone (from 2.95.51):</b> Below the mode, «Show on the HDMI» puts a big game page on the TV at the Pi (Raspberry Pi OS with desktop and Chromium needed): left the picture of the simulator or the camera, right the game wizard, the QR code to join, the time, the players and the ranking. In the campfire and gamer mode it starts by itself. Any other screen in the same network can open the link too. A phone on the USB cable (Android «USB tethering», iPhone «Personal Hotspot») gives Motion Watch internet – the own Wi-Fi (game network) gets it too.</p><p><b>📶 Network check and 🛈 product page (from 2.95.52):</b> Tools → «Network check of the players» measures reaction time, jitter, losses, download and upload from every phone to Motion Watch; phones in the game corner measure by themselves, all others with the QR code. When Motion Watch is the Wi-Fi itself, the signal of every phone is added, with tips for weak connections. Tools → «Product page for guests» shows your Motion Watch homepage to everybody in the same Wi-Fi, without login and without internet (QR code, also on the TV view). Questions from the form arrive as a push message.</p><p><b>🖥 The simulator as helper (from 2.95.53):</b> <b>AI helper</b> (Tools): when Motion Watch also runs on the PC (in the 3D simulator «Start Motion Watch on this PC»), the PC does the detection for the Pi - the Pi finds it by itself and does it again itself when the PC is gone. <b>TV mode</b>: key T in the simulator or «TV mode in the 3D simulator» below the mode. In the tab Simulator: <b>Aufstell-Planer</b> (where Motion Watch should stand, blind spots, take over the patrol), <b>alarm replay in 3D</b>, <b>AI test with simulator pictures</b> (how well does the AI see at night, in rain, fog? with training pictures as ZIP). In the network check: <b>walk round</b> - a map where the Wi-Fi is good.</p><p><b>📖 Almanac, 🪩 disco light, 🔒 tunnel, 🎮 games (from 2.95.54):</b> Tools → «Survival almanac» (German): camping tips to look up or read in the evening, offline, with search, red light and reading aloud (/almanach/, also for guests). Below the mode: «Disco light» - the white light flashes with the music (microphone) or a fixed tempo, at most 3 times a second, an alarm comes first. Tab Simulator → «Simulator behind a firewall»: a simulator on a PC without admin rights connects to Motion Watch itself with address and code. The game collection is split into touch games and games with on-screen buttons.</p>
<ul><li><b>Armed / disarmed:</b> only when armed there are alarms, push messages, siren and recordings. The countdown gives you time to leave; «Arm now» skips it.</li>
<li><b>Camping profile:</b> one switch for everything: own Wi-Fi on, the camera stays where it is, alarms, recordings and power saving on, armed after the countdown. Switching it off restores your settings.</li>
<li><b>Own Wi-Fi (hotspot):</b> the Pi makes its own Wi-Fi – works without a mobile network. Name and password under <i>Protection &amp; network</i>.</li>
<li><b>Network:</b> «Automatic» tries known networks first (e.g. the phone hotspot: internet + push messages), otherwise it switches the own Wi-Fi on.</li>
<li><b>Autostart:</b> Motion Watch starts by itself at power-on, without a screen.</li>
<li><b>Power saving:</b> few pictures per second while all is quiet – full speed at once at the first movement, a noise or when somebody watches.</li>
<li><b>🔋 UPS HAT (Waveshare, 2 × 18650):</b> found by itself (I2C 0x42). The header shows 🔌 on mains power or 🔋 % and time left on battery. A push message at a power cut and when power is back, a warning at 20 %, a clean shutdown at 8 % (adjustable). Under Battery enter the capacity of one cell (e.g. 3450 mAh).</li>
<li><b>🔋 Battery:</b> enter the capacity of the powerbank (mAh, as on the label), press «Battery is full now» after charging. The header then shows e.g. «🔋 62 % · 14 h». At 15 % a push message comes. It is an estimate from what the Pi uses (powerbanks do not report their charge).</li>
<li><b>Clock from the phone:</b> without internet the Pi takes the time from the phone, so recordings have the right time.</li></ul>
<p><b>🧭 Reference scan (from 2.95.97):</b> Tools → «Reference scan» guides you in four steps: set up and align the camera, set the grid (directions, heights, photos per direction), take the reference, compare. Motion Watch drives the head through all directions. The report shows reference and now side by side for every direction: red = missing, blue = new, orange = changed. Compare by hand, when armed or every N minutes (Settings → Alarm &amp; camping → Reference scan), with a push message if you like. In the 3D simulator the buttons «Motion Watch: Referenz-Scan» and «Mit Referenz vergleichen» start the same; «Testhilfe: Velo wegnehmen» shows how a missing thing is reported.</p></section>

<section id="notify" data-icon="🔔"><h2>Notifications</h2>
<ul><li><b>📲 Web push (no app):</b> Notifications → «Switch on on this device». Needs https: under Notifications «Switch on https over Tailscale» (allow «HTTPS Certificates» once in the Tailscale admin page), then open the page via <code>https://NAME.….ts.net/</code>. iPhone / iPad: add this https page to the home screen and switch it on from there. Works besides ntfy / Telegram.</li>
<li><b>ntfy</b> (recommended): install the app, subscribe to a topic, enter the address (e.g. <code>https://ntfy-me.com/&lt;your-topic&gt;</code>) as «Webhook / ntfy URL», type «ntfy». The app must use the same server as the address.</li>
<li><b>Telegram</b> or a <b>webhook</b> (e.g. Home Assistant) work too.</li>
<li><b>Pre-alarm:</b> a short message with a small picture at the first movement, before a person is confirmed.</li>
<li><b>Message texts:</b> own titles and texts with placeholders {name} {time} {date} {count} {camera} {link} {db}. Empty = standard text.</li>
<li><b>«Address of this page for links»:</b> a tap on the message opens the page.</li>
<li><b>🔔 Alarm sound in the browser:</b> tap the bell at the top and «Sound on». The page must stay open (also in the background).</li></ul>
<div class="tip">💡 <b>Tip:</b> after every change: «Test notification». If nothing arrives, the reason is under «status» and in the event log.</div>
</section>

<section id="detect" data-icon="🎯"><h2>Detection</h2>
<ul><li><b>Sensitivity</b> and <b>min. object size</b> are the most important settings against false alarms.</li>
<li><b>AI detection</b> recognises persons, animals and vehicles. «Motion persons need AI confirmation» = fewer false alarms, a little slower.</li>
<li><b>Zones</b> (tab <i>Zones</i>): «Ignore» for trees, road, tent wall; «Only here» when only one area counts.</li>
<li><b>Privacy zone</b> (tab <i>Zones</i>): the area is painted black right after the camera – in the live picture, recordings, photos, timelapse and for guests. For a neighbour's tent, a path, other people's windows. Important for data protection: do not film strangers and public ground all the time.</li>
<li>Rain, wind, shadows and low light are detected and handled automatically (fine-tuning).</li>
<li><b>Auto-tune</b> learns the scene; «Recalibrate» after big changes (scene empty).</li></ul>
</section>

<section id="camera" data-icon="📷"><h2>Camera &amp; servos</h2>
<ul><li><b>Limits:</b> how far the camera may pan / tilt (degrees from the middle) – protects cables and housing.</li>
<li><b>Follow person:</b> the camera follows a detected person.</li>
<li><b>Patrol:</b> the camera moves between waypoints (waypoint = current position, pan and tilt, «+ Waypoint»; shown e.g. as 24/60 = 24 % left–right, 60 % down–up). The 🔄 button steps on with each tap: off → back and forth (1-2-3-2-1) → round trip (1-2-3-1) → off.</li>
<li><b>Video source:</b> Pi camera, USB or network camera; more cameras in the tab <i>Cameras</i>.</li>
<li><b>Servo driver</b> (fine-tuning): PCA9685, address, channels.</li><li><b>🚜 Mover (tracked vehicle, from 2.94.0):</b> when Motion Watch sits on a small tracked vehicle, a second, green stick appears: up = forward, down = back, sideways = turn on the spot. The motor driver (Motor HAT with PCA9685 + TB6612, I2C 0x60) is found by itself – without it the stick stays away. Settings under Camera &amp; servos → Mover. Without a new command the tracks stop after 0.6 s. In the 3D simulator: «Mover simulieren». In the simulation the stick can also be shown without a mover (Mover → «Simulation: show the stick even without …», from 2.94.4) – to try out the controls.</li></ul>
</section>

<section id="thermal" data-icon="🌡"><h2>Thermal camera</h2>
<ul><li>Choose the thermal camera (Thermal-90 or USB), switch on «Overlay the thermal picture».</li>
<li><b>Align:</b> with «zoom» and «shift» so that a warm person in the thermal picture lies exactly on the person in the camera picture.</li>
<li><b>Thermal alarm:</b> a warm body in the zone; «only warm bodies that move» ignores warm stones and engines.</li>
<li>The status shows the highest temperature measured.</li></ul>
</section>

<section id="lightsound" data-icon="💡"><h2>Light &amp; sound</h2>
<h3>Lights</h3>
<ul><li>White and infrared: Off / On / Auto. «Auto» = at an alarm only at night, at an alarm day and night, or the whole night (from sunset, computed from latitude / longitude under <i>Setup</i>).</li>
<li><b>Picture:</b> «grey at night» is ideal with the NoIR camera.</li></ul>
<h3>Microphone</h3>
<ul><li>Choose the device, watch the level. <b>Noise alarm</b>: louder than the background by X dB for at least Y seconds.</li>
<li><b>🎧 Listen</b>: live sound on the phone, volume per device.</li>
<li><b>Sound in the recordings</b>: videos are saved with sound.</li></ul>
<h3>Loudspeaker</h3>
<ul><li>Built-in (USB) or <b>Bluetooth</b>: «Search Bluetooth loudspeakers» (speaker in pairing mode), then «Connect».</li>
<li><b>Siren at an alarm</b> (only when armed), sound, volume, duration. Own sounds (.wav/.mp3) in <code>~/.config/motionwatch/sounds</code>.</li>
<li><b>🎙 Talk</b>: hold the button. Needs the secure page <code>https://…:5001</code> (phones only allow the microphone there).</li></ul>
</section>

<section id="rec" data-icon="🎬"><h2>Recordings &amp; timelapse</h2>
<ul><li>At an alarm, videos (with pre-roll and sound) and snapshots are saved.</li>
<li>Tab <i>Recordings</i>: watch, filter, ⭐ favourites (never deleted automatically), download several as ZIP, statistics per day.</li>
<li><b>Picture for other programs:</b> under <i>Settings → Web stream</i> switch on «Picture for other programs». You get a secret address for the video (MJPEG) and a still picture, e.g. for Home Assistant, Frigate, Blue Iris or VLC. <b>RTSP</b> too: install mediamtx (<code>https://github.com/bluenviron/mediamtx/releases</code>, unpack the «linux_arm64» file to <code>~/mediamtx/</code>), then switch on «RTSP video». RTSP needs CPU power.</li>
<li><b>Places &amp; map:</b> photos and videos with a GPS position (phone or fixed place) get a place. The filter «Place» shows one place only (or «Without location»). 🗺 <i>Map</i> shows all places with their count; tap a point → preview, «Show only this place», ✎ rename. Map background and place names come from OpenStreetMap (can be switched off under <i>Settings → Setup</i>).</li>
<li>The oldest recordings are deleted when the folder is too big or the memory card almost full.</li>
<li><b>Timelapse:</b> a photo every N minutes from a fixed position, then a video («Create video»). An alarm always has priority. Timelapse videos also appear under <i>Recordings</i> (marked ⏱); the type «Timelapse» there also shows all single photos.</li></ul>
</section>

<section id="diary" data-icon="🦊"><h2>Diary, night report &amp; guests</h2>
<ul><li><b>Animal diary</b> (tab <i>Diary</i>): the best picture of every animal visit is saved automatically, with species, date and duration. Filter by species, ★ = keep, ⤴ share (e.g. WhatsApp), ⤓ download. Older entries are deleted after the set time (★ never).</li>
<li>The AI knows bird, cat, dog, horse, sheep, cow, bear (and a few exotic ones). A fox usually shows up as «dog» or «cat», a wild boar often as «sheep» or «bear».</li>
<li><b>Night report:</b> every morning (adjustable, default 7 o'clock) a push message: what happened in the night (from 20 o'clock) – persons, animals, noises, thermal – with the best picture. «Send now» to try it. Settings under <i>Notifications → Night report</i>.</li>
<li><b>Guest access</b> (<i>System &amp; network</i>): «Create new link», choose how long (2 h to no limit), share the link. Guests only see the live picture (with privacy zones), no password needed, they cannot change anything. «End guest access» blocks the link at once. The guest must reach the Pi: same Wi-Fi / hotspot or via Tailscale.</li>
<li><b>App icon:</b> iPhone: in Safari <i>Share → Add to Home Screen</i>. Android: Chrome menu <i>⋮ → Add to Home screen</i>. Motion Watch then opens like an app, without browser bars.</li></ul>
</section>

<section id="relay" data-icon="⚡"><h2>Relays &amp; schedule</h2>
<ul><li><b>Relays:</b> Off / On / Auto. Auto = on while the trigger applies (person, motion, pre-alarm, warm body, noise, animal …) plus the hold time.</li>
<li><b>Warning lamp for remote access:</b> relay on Auto, trigger «remote access». It is on while somebody watches over Tailscale – also when disarmed. A small LED (with a ~330 Ω resistor) can go straight to the GPIO, a bigger lamp via a relay module.</li>
<li><b>Schedule:</b> switches features on or off at certain times, e.g. armed at night, power saving by day. Also «at sunset» and exception dates.</li></ul>
</section>

<section id="system" data-icon="⚙"><h2>System &amp; network</h2>
<ul><li><b>System:</b> CPU, temperature, power supply (voltage, under-voltage), free memory, version.</li>
<li><b>📜 Event log:</b> everything is written to the memory card at once (also a status line every 15 minutes with CPU, temperature, Wi-Fi, memory, battery). «Whole log & archive» shows today and every earlier day as its own file (packed, kept 60 days, adjustable under Setup) – filter, search, download.</li>
<li><b>🔐 Operator mode:</b> «Operator mode (lock settings)» under System – set a PIN (4–8 digits), then all settings are locked. Still usable: arm/disarm, camping profile, the main switches (detection, recording, notifications, power saving, patrol, timelapse …), lights, camera, listen/talk, watching recordings. «Unlock» with the PIN; after 5 wrong PINs a 5-minute pause.</li>
<li><b>⏸ Pause the program:</b> choose how long (5 minutes to 12 hours) – Motion Watch switches off at once (a recording is finished first) and starts again by itself. Meanwhile the page shows a countdown and «Start now». While paused there is no monitoring and there are no alarms.</li>
<li><b>⏻ Shut down / ↻ restart the Pi:</b> a running recording is finished first. Unplug only when the green LED stays dark.</li>
<li><b>🔒 Web password</b>, <b>⬇ save / ⬆ load settings</b> (the file contains your access data – keep it private).</li>
<li><b>Wi-Fi:</b> search and join networks, saved networks.</li>
<li><b>🌐 Remote access (Tailscale):</b> System shows whether Tailscale is connected, the address for on the road (http://100.…:5000/) and who watches from outside right now. The header then shows «🌐 Remote: device name». Optional push message (Notifications). Setup: <code>curl -fsSL https://tailscale.com/install.sh | sh</code>, then <code>sudo tailscale up</code>, on the phone the Tailscale app with the same account.</li>
<li><b>Web stream:</b> picture quality and width – smaller = less data over the phone hotspot.</li>
<li><b>Setup:</b> location (sunrise / sunset), presence, warnings (temperature, memory).</li>
<li><b>Automatic update:</b> switch on «Install new versions automatically» and choose the hour (default 12 o'clock). It installs only when nothing is going on (disarmed, no recording, no person – «also while armed» allows it when armed). If the new version fails to start three times, Motion Watch goes back to the previous one by itself.</li>
<li><b>🔏 Signed updates:</b> every version is signed with the developer&#39;s secret key. Motion Watch installs only versions with a valid signature – even somebody who breaks into the GitHub account cannot push a foreign program onto the devices. The list shows «🔏 signed» or «⚠ not signed». Own unsigned builds only with «Also accept unsigned versions».</li>
<li><b>Private GitHub repository:</b> also enter the <b>GitHub key (token)</b> under Updates – create it on github.com under Settings → Developer settings → Fine-grained tokens, only for this repository, permission «Contents: Read-only». The key is only sent to GitHub and never shown.</li>
<li><b>Updates:</b> enter the source (address of a versions.json or a folder / USB stick), «Search versions», pick a version. Older versions stay for going back. <b>Test mode</b> («Get new versions at once»): looks on GitHub every minute and installs a new version right away (also while armed, never during a recording) - for testing, switch it off afterwards.</li></ul>
</section>

<section id="window" data-icon="🖥"><h2>Desktop window on the Pi</h2>
<table><tr><td>Double-click the video</td><td>video only</td></tr><tr><td>⛶ / F11 / Esc</td><td>video full screen / whole page full screen / back</td></tr>
<tr><td>Ctrl+B</td><td>settings panel on / off</td></tr><tr><td>Ctrl+T / Ctrl+L</td><td>light/dark, language</td></tr>
<tr><td>Arrow keys / Home</td><td>move the camera / centre</td></tr><tr><td>Right-click the video</td><td>show / hide fields</td></tr></table>
<p>The settings are grouped like on the web page. The button «Manual» opens this page.</p>
</section>

<section id="tips" data-icon="🧭" class="tips"><h2>Tips &amp; tricks</h2>
<ul>
<li>🔍 <b>Find a setting:</b> type into the search box at the top of the settings (e.g. «password», «siren», «Wi-Fi») – everything else disappears, matches get a blue frame. ✕ or Esc shows everything again.</li>
<li>💬 <b>Feedback to the developer:</b> System → «Feedback to the developer» (window: Setup). Ideas, errors, praise – anonymous, no sender. Without internet the message waits and is sent later.</li>
<li>🎞 <b>Markings in recordings:</b> Recording → «Markings in recordings and alarm pictures»: thin corner marks (default, the face stays free), none, or red boxes like the live picture.</li>
<li>⚡ <b>Quick switches next to the stick</b> (green = on): 🌡 thermal picture over the live picture, 🏷 mark objects, 💡 white light, 🔴 IR light, 🎧 listen, ⚡ per relay (on / automatic), 🎯 follow person, 🔄 patrol, ⏺ record now (max. 10 min, red while recording, tap again = stop), 📷 photo into the recordings. Grey = not connected.</li>
<li>🕹 <b>Joystick in full screen</b> (phone, tablet, PC): the picture fills the whole screen, the stick floats see-through at the bottom right. After 3 s untouched it becomes pale, on touch clearly visible again. Next to it: ◎ centre, 🎧 listen; ⇆ at the top next to ✕ puts the stick on the other side.</li>
<li>🟢 <b>Overview in the settings:</b> the arrow of a topic is green while its main function is on (e.g. night report, timelapse, backup), otherwise grey. The arrow of a group is green when at least one topic in it is on. In the window on the Pi: green title.</li>
<li>📱 <b>SMS over an LTE stick</b> (Notifications → SMS): with a USB LTE stick and a SIM card the alarm (person, sabotage, warm body, noise) comes as SMS – by default only when there is no internet. Works with ModemManager (<code>sudo apt install modemmanager</code>), AT commands or Huawei HiLink sticks (192.168.8.1). Pause and daily limit protect against costs; «Send test SMS» checks everything.</li>
<li>🎬 <b>Demo mode:</b> <code>python3 webcam_bewegung_X.py --demo</code> (for an online demo add <code>--headless --port 8080</code>) shows a drawn camping scene where now and then a person, a dog or a bear walks by – alarm, recording, diary and deterrence react like real. Own settings (in the temp folder), «DEMO» in the header, nothing on the computer is changed.</li>
<li>🏠 <b>MQTT / Home Assistant</b> (System &amp; network): enter the broker address (e.g. the Mosquitto add-on of Home Assistant), user and password, «MQTT on». Home Assistant then shows Motion Watch by itself as a device: alarm panel (arm/disarm), person, motion, animal, recording, battery, temperature and the last alarm picture. Commands also via <code>motionwatch/&lt;id&gt;/cmd/arm</code> (ARM_AWAY / DISARM), <code>…/cmd/light_white</code> (on/off/auto).</li>
<li>🛰 <b>Several devices:</b> tab Cameras → «Other Motion Watch devices»: picture, armed/alarm, battery and last event of every device, arm/disarm one or all together. «Search in the network» finds devices in the same network and over Tailscale; devices with a password need it once.</li>
<li>⤴ <b>Share with logo:</b> diary pictures, snapshots, recordings and timelapse (button ⤴ in the recording viewer) and the night report picture get a discreet strip «Motion Watch» with the date at the bottom right. Can be switched off under Recording.</li>
<li>🦊 <b>Targeted deterrence</b> (Light &amp; sound → Deterrence): an own reaction for person, big animal (bear, cow, horse …), small animal (cat, dog, bird) and warm body (thermal camera) – sound (new: high whistle, bangs/claps or own sounds) and/or the white light flashing. Duration and pause adjustable; «also when disarmed» e.g. for the garden. Animals need the AI detection.</li>
<li>🚨 <b>Theft protection</b> (Alarm &amp; camping): when armed an urgent push with picture and the siren as soon as the camera is <b>covered or turned away</b>, the device is <b>moved or knocked over</b> (motion sensor MPU-6050 at I2C 0x68, about 3 $, optional) or the <b>power is cut</b> (with the UPS HAT). While the camera head moves itself (patrol, tracking, joystick) the picture check learns anew.</li>
<li>☁️ <b>Backup of alarm recordings:</b> Recordings &amp; timelapse → Backup. Finished alarm recordings (armed or with a person) go automatically to a WebDAV folder (Nextcloud: <code>https://…/remote.php/dav/files/USER/MotionWatch/</code> with an app password, Synology/QNAP NAS, many clouds), to a folder (USB stick, mounted NAS) or as a video to Telegram. One sub-folder per day. «Test the backup» checks the settings.</li>
<li>🧭 <b>Setup assistant:</b> shows the first time the page is opened – language and device name, push messages (ntfy topic with QR code and test message), web password, QR codes for more devices. Any time again under System → «Setup assistant». «Quick start (QR)» gives a card to print with QR codes for the own Wi-Fi of the Pi and the page. In the window on the Pi: Setup → «QR code for the phone».</li>
<li>🔗 <b>One icon for home and away:</b> add the page to the home screen from the Tailscale address (e.g. <code>http://NAME-OF-THE-PI:5000</code> or the 100.… address shown in the Tailscale app). At home Tailscale connects directly over the Wi-Fi, away over the internet – the Tailscale app must be on. Only on the Pi&#39;s own Wi-Fi without internet use the local address (e.g. <code>http://10.42.0.1:5000</code>). «🌐 Remote» at the top shows when you are connected over Tailscale.</li>
<li>📱 <b>Like an app:</b> put Motion Watch on the home screen (iPhone: Share → Add to Home Screen). Then the iPhone also gets a real full screen. In this mode the button <b>⟳</b> (top right) reloads the page; after an update a «Reload» bar appears at the bottom.</li>
<li>🦊 <b>Collect animal photos:</b> keep AI detection on, point the camera at a feeding place or a game trail – check the <i>Diary</i> in the morning.</li>
<li>🌙 <b>Test before the first night:</b> arm, walk through the picture once and check: push arrives, recording is there, siren / light react.</li>
<li>🌳 <b>False alarms from branches:</b> draw trees and bushes as «Ignore» zones and raise the minimum size a little. The automatic wind detection helps too.</li>
<li>🐗 <b>Scare animals away:</b> siren «at an alarm» plus white light «at an alarm, only at night». For your own sleep keep the siren short (5–10 s).</li>
<li>🔴 <b>Infrared and reflections:</b> do not point IR light through a window or close to a tent wall – it blinds the camera.</li>
<li>🔇 <b>Silent watch:</b> siren off, only push messages and the bell in the browser – nobody at the campsite wakes up.</li>
<li>🔋 <b>Save power:</b> camping profile (includes power saving), smaller stream width, listen only briefly. Use a power bank with 5 V / 3 A or more; at «under-voltage» change the cable or power bank.</li>
<li>📶 <b>Little mobile data:</b> the pre-alarm picture stays small (640 px); open the live picture only when needed (the Pi only sends while somebody watches).</li>
<li>🎤 <b>Microphone:</b> a piece of foam as wind shield prevents false alarms in the wind. The servos do not disturb – the noise alarm pauses while they move.</li>
<li>🔊 <b>Bluetooth speakers</b> often switch themselves off after a while. The Pi reconnects them when they are back – for the night choose one without auto-off.</li>
<li>🧭 <b>Aim the camera:</b> find the best position with the stick and use it as waypoint or timelapse position.</li>
<li>🕒 <b>Wrong time</b> in the recordings: open the page once on the phone – the Pi takes the time of the phone.</li>
<li>💾 <b>Important recordings:</b> mark them with ⭐ – they are never deleted automatically.</li>
<li>🔁 <b>Try a new version</b> without risk: under Updates you can always switch back.</li>
<li>📱 <b>Bell in the browser</b> only on one device that stays open at night – otherwise everything rings.</li>
</ul></section>

<section id="privacy" data-icon="🔏"><h2>Privacy &amp; security</h2>
<p><b>Principle:</b> Motion Watch works on the device itself. Pictures, recordings, sound and settings stay on the memory card – there is no manufacturer cloud and no account.</p>
<ul>
<li><b>What is stored on the device:</b> recordings and snapshots (folder «recordings», old ones are deleted when the card is full – favourites never), animal diary (pictures), event log (60 days, adjustable), settings. The web password is only stored as a secure hash.</li>
<li><b>What leaves the device only when you switch it on:</b> push messages (ntfy / Telegram / webhook – with picture, through their servers), web push (through Apple / Google / Mozilla, encrypted), backup of the clips (your WebDAV / NAS / Telegram), MQTT (your broker), SMS (mobile network), updates (GitHub; only signed versions are installed), remote access (Tailscale, encrypted).</li>
<li><b>Sound:</b> microphone, listening and sound in recordings are off by default. Recording conversations is in many countries only allowed with consent.</li>
<li><b>Privacy zones</b> (tab Zones): areas like the neighbour's garden, a path or windows are painted black – in the live picture, recordings and pictures.</li>
<li><b>Guest links</b> only show the live picture, expire and can be made invalid at any time.</li>
<li><b>Protection against strangers:</b> web password (at setup), lock after 8 wrong attempts, operator mode with PIN, signed updates, remote access only through Tailscale.</li>
</ul>
<p><b>Legal (Switzerland: FADP, EU: GDPR – no legal advice):</b> film only your own pitch. Public ground, paths and other people's property do not belong in the picture (otherwise use privacy zones). Put up a notice («video surveillance») and tell fellow travellers and guests. On camp sites the site rules apply too. Keep recordings only as long as needed.</p>
</section>
<section id="faq" data-icon="🛠"><h2>Troubleshooting</h2>
<dl>
<dt>The page does not open</dt><dd>Is the phone in the right Wi-Fi (own Wi-Fi of the Pi or the same network)? Address with <code>:5000</code>? In the own Wi-Fi always <code>http://10.42.0.1:5000</code>.</dd>
<dt>The page shows an old version</dt><dd>The version stands top left. If an old copy still runs (e.g. from the autostart), start the new program by hand – it takes over. Then reload the page.</dd>
<dt>No picture</dt><dd><i>Camera &amp; servos → Video source</i> → «Scan for cameras». Pi camera: check the ribbon cable.</dd>
<dt>Push messages do not arrive</dt><dd>«Test notification» and read the status. ntfy: the same server in the app and the address. Without internet (own Wi-Fi only) no push messages can be sent – use the bell in the browser.</dd>
<dt>Autostart does not start</dt><dd>Terminal: <code>systemctl --user status motionwatch</code>. Run once <code>sudo python3 webcam_bewegung_X.py --allow-wifi</code> (start without login).</dd>
<dt>Picture black at night, but movements are marked</dt><dd>The scene is too dark for the normal camera. «In the dark also brighten the picture you see» (Detection → Low light) brightens it as far as possible – in total darkness only light helps: infrared lamp + NoIR camera (invisible) or the white lamp.</dd>
<dt>Picture black at night, but movements are marked</dt><dd>The scene is too dark for the normal camera. «In the dark also brighten the picture you see» (Detection → Low light) brightens it as far as possible – in total darkness only light helps: infrared lamp + NoIR camera (invisible) or the white lamp.</dd>
<dt>Motion Watch does not start after a power cut</dt><dd>Switch autostart (Alarm &amp; camping) off and on again. If a hint with «enable-linger» appears, run that command once in the terminal.</dd>
<dt>Many false alarms</dt><dd>Draw zones, lower the sensitivity, raise the minimum size, switch on «AI confirmation».</dd>
<dt>Servos jitter or hit the end</dt><dd>Use the PCA9685 (servo driver), reduce the limits in degrees, own 5 V supply for the servos.</dd>
<dt>«Under-voltage»</dt><dd>Shorter / thicker USB-C cable or a stronger power bank. Under-voltage can cause crashes and broken recordings.</dd>
<dt>No sound over Bluetooth</dt><dd>Speaker on and in range? Tap «Connect» again. The program must run as normal user (not with sudo).</dd>
<dt>Talking does not work</dt><dd>Only on the secure page <code>https://…:5001</code>. Confirm the certificate warning once and allow the microphone.</dd>
</dl></section>

<section id="setup" data-icon="🧰"><h2>Setup on the Raspberry Pi</h2>
<pre>sudo apt install python3-pil.imagetk python3-tk python3-gpiozero ffmpeg python3-picamera2 alsa-utils openssl bluez pulseaudio-utils
pip install opencv-python numpy pillow flask psutil</pre>
<ul><li>Switch on I2C and SPI (<code>sudo raspi-config</code>); in <code>/boot/firmware/config.txt</code> under <code>[all]</code>: <code>dtoverlay=spi0-0cs</code>.</li>
<li>Once: <code>sudo python3 webcam_bewegung_X.py --allow-wifi</code> (Wi-Fi, clock, autostart, shut down, watchdog).</li>
<li>Start: <code>python3 webcam_bewegung_X.py</code> (window + web page) or <code>--headless</code> (web page only).</li>
<li>Settings, log, sounds: <code>~/.config/motionwatch/</code> – kept for new versions.</li></ul>
</section>
</div>
  </div>
  <p class="mut" style="margin-top:18px" id="hfoot"></p>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, {"Search …": "Suchen …", "Manual": "Anleitung", "Diary": "Tagebuch", "Expand all": "Alle öffnen", "No match": "Nichts gefunden",
  "Motion Watch manual · version": "Anleitung zu Motion Watch · Version"});
let SECS = [];
function buildHelp() {
  if (["fr", "it", "rm"].includes(LANG) && window.HELPX && !document.querySelector('#hbody > div[lang="' + LANG + '"]')) {
    const x = document.createElement("div"); x.innerHTML = HELPX; const d = x.firstElementChild; if (d) $("#hbody").appendChild(d);
  }
  const hl = document.querySelector('#hbody > div[lang="' + LANG + '"]') ? LANG : (LANG === "rm" ? "de" : (LANG === "de" ? "de" : "en"));
  document.body.classList.add("lang-" + hl);
  const box = document.querySelector('#hbody > div[lang="' + hl + '"]');
  const toc = $("#toc"); toc.textContent = "";
  SECS = [];
  [...box.querySelectorAll(":scope > section")].forEach((s, i) => {
    const title = s.querySelector("h2").textContent, icon = s.dataset.icon || "";
    const d = el("details", "card hsec" + (s.classList.contains("tips") ? " tips" : "")); d.id = "h-" + s.id;
    const sm = el("summary"); sm.append(el("span", "ic", icon), el("span", "", title)); d.appendChild(sm);
    [...s.childNodes].forEach(n => d.appendChild(n));
    s.replaceWith(d);
    if (i === 0 || location.hash === "#" + s.id) d.open = true;
    const a = el("a", "", icon + " " + title); a.href = "#" + s.id;
    a.onclick = e => { e.preventDefault(); d.open = true; d.scrollIntoView({behavior: "smooth", block: "start"}); history.replaceState(null, "", "#" + s.id); };
    toc.appendChild(a);
    SECS.push({d: d, html: d.innerHTML});
  });
  const h = location.hash.slice(1); if (h) { const d = $("#h-" + h); if (d) { d.open = true; setTimeout(() => d.scrollIntoView(), 100); } }
  $("#q").placeholder = t("Search …");
}
function search() {
  const q = $("#q").value.trim().toLowerCase();
  SECS.forEach(x => {
    x.d.innerHTML = x.html;
    if (!q) { x.d.classList.remove("nohit"); return; }
    const hit = x.d.textContent.toLowerCase().includes(q);
    x.d.classList.toggle("nohit", !hit);
    if (hit) {
      x.d.open = true;
      const walk = n => { if (n.nodeType === 3) { const i = n.data.toLowerCase().indexOf(q); if (i >= 0) { const m = document.createElement("mark"); const r = n.splitText(i); r.splitText(q.length); m.textContent = r.data; r.replaceWith(m); } }
        else if (n.nodeName !== "SUMMARY" && n.nodeName !== "MARK") [...n.childNodes].forEach(walk); };
      [...x.d.childNodes].forEach(walk);
    }
  });
}
(async () => {
  await initAppearance(); buildHelp();
  let tm = null; $("#q").addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(search, 150); });
  try { const v = await (await fetch("/api/version")).json(); $("#hfoot").textContent = t("Motion Watch manual · version") + " " + v.version; } catch (e) {}
})();
/*ALERTS*/
</script></body></html>
"""


REC_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Watch - Recordings</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:1600px;margin:0 auto}
.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px 16px;align-items:end}
.filters label,.flab{display:block;font-size:11px;font-weight:700;letter-spacing:.08em;color:var(--mut);text-transform:uppercase;margin-bottom:4px}
.filters select,.filters input[type=text],.filters input[type=date]{width:100%}
.dates{display:flex;gap:6px}
.quick{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}
.quick button{padding:3px 10px;font-size:12px}
.seg{width:100%}.seg button{flex:1;padding:6px 10px;font-size:13px}
.seg button.sel{background:var(--acc);color:#fff}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.bar .sp{flex:1}
button.favf.on{background:var(--yel);color:#fff;border-color:var(--yel)}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.mapcard{margin-bottom:14px;padding:10px}
.loopcard{margin-bottom:14px}.lhead{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:6px 0}.lhead input{width:auto;padding:6px 8px}
.ltl{position:relative;display:grid;grid-template-columns:repeat(144,1fr);height:44px;border-radius:8px;overflow:hidden;background:var(--field);border:1px solid var(--line)}
.ltl i{display:block;border-right:1px solid rgba(0,0,0,.08)}.ltl i.on{background:var(--acc);cursor:pointer}.ltl i.on:hover{background:var(--grn)}.ltl i.live{background:var(--yel)}
.ltl b{position:absolute;top:0;bottom:0;width:3px;background:var(--red);pointer-events:none;margin-left:-1px}
.lhours{display:flex;justify-content:space-between;font-size:11px;color:var(--mut);margin-top:2px}
.fa-card{margin-bottom:14px;padding:10px 12px;border-color:var(--yel)}.fa-card .fah{font-weight:700;margin-bottom:6px}
.fa-card .fas{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:6px 0;border-top:1px solid var(--line);flex-wrap:wrap}
.fatag{position:absolute;left:6px;top:6px;background:rgba(0,0,0,.7);color:#fff;font-size:11px;padding:2px 7px;border-radius:9px;z-index:2}
#m-farow{display:flex;gap:6px;flex-wrap:wrap;align-items:center;padding:6px 0}#m-farow button{padding:5px 10px;font-size:13px}
#m-farow button.on,#m-fa.on{background:var(--yel);color:#000}
.map{position:relative;height:min(55vh,460px);overflow:hidden;border-radius:12px;touch-action:none;cursor:grab;user-select:none;
  background:#22313b repeating-linear-gradient(0deg,transparent 0 63px,rgba(255,255,255,.06) 63px 64px),repeating-linear-gradient(90deg,transparent 0 63px,rgba(255,255,255,.06) 63px 64px)}
.map.drag{cursor:grabbing}
.mtiles,.mpins{position:absolute;inset:0}
.mtiles img{position:absolute;width:256px;height:256px;max-width:none;-webkit-user-drag:none;pointer-events:none}
.mpin{position:absolute;transform:translate(-50%,-50%);min-width:30px;height:30px;padding:0 8px;box-sizing:border-box;border-radius:15px;background:var(--org);color:#fff;
  font:700 13px system-ui,sans-serif;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.5);cursor:pointer;z-index:2}
.mpin.sel{background:var(--red);z-index:3;transform:translate(-50%,-50%) scale(1.15)}
.mdot{position:absolute;width:9px;height:9px;margin:-5px 0 0 -5px;border-radius:50%;background:var(--yel);border:1.5px solid #222;pointer-events:none;z-index:1}
.mzoom{position:absolute;right:8px;top:8px;display:flex;flex-direction:column;gap:6px;z-index:4}
.mzoom button{width:38px;height:38px;padding:0;font-size:18px}
.mattr{position:absolute;right:4px;bottom:2px;font-size:10px;background:rgba(255,255,255,.8);color:#333;padding:0 4px;border-radius:3px;z-index:4}
.mattr a{color:#333}
#map-note{margin-top:6px;font-size:12px}
.mpop{margin-top:8px;border-top:1px solid var(--line);padding-top:8px}
.mpop .mh{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.mpop .mh b{font-size:15px}
.mpop .mth{display:flex;gap:8px;overflow-x:auto;padding:8px 0 2px}
.mpop .mth div{flex:0 0 auto;width:120px;cursor:pointer;font-size:11px}
.mpop .mth img{width:120px;height:72px;object-fit:cover;border-radius:8px;display:block;background:var(--field)}
.rc{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;position:relative;box-shadow:var(--shadow);transition:transform .12s,border-color .12s}
.rc:hover{border-color:var(--acc);transform:translateY(-2px)}
.rc.sel{outline:2px solid var(--acc)}
.th{position:relative;aspect-ratio:16/9;background:#000;display:flex;align-items:center;justify-content:center;color:var(--mut);font-size:30px}
.th img{width:100%;height:100%;object-fit:cover;display:block}
.th .play{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity .15s;background:rgba(0,0,0,.28);color:#fff;font-size:38px}
.rc:hover .play{opacity:1}
.tag{position:absolute;left:8px;bottom:8px;background:rgba(0,0,0,.72);color:#fff;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:700}
.tag.live{background:var(--red)}
.star{position:absolute;right:8px;top:6px;font-size:22px;line-height:1;color:#fff;text-shadow:0 1px 4px rgba(0,0,0,.8);cursor:pointer;background:none;border:0;padding:0}
.star.on{color:var(--yel)}
.chk{position:absolute;left:8px;top:8px;width:20px;height:20px;display:none}
body.selecting .chk{display:block}
.rb{padding:9px 11px}
.rb b{display:block;font-size:13px}
.chips{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px}
.chip{font-size:11px;border:1px solid var(--blu);border-radius:99px;padding:0 8px;color:var(--blu)}
.empty{padding:40px;text-align:center;color:var(--mut)}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.82);z-index:50;display:flex;align-items:center;justify-content:center;padding:12px}
.modal[hidden]{display:none}
.mbox{background:var(--panel);border:1px solid var(--line);border-radius:14px;max-width:1100px;width:100%;max-height:100%;display:flex;flex-direction:column;overflow:hidden}
.mhead{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:8px 12px;border-bottom:1px solid var(--line)}
.mhead .sp{flex:1}
#m-body{background:#000;display:flex;align-items:center;justify-content:center;min-height:200px;overflow:auto}
#m-body video,#m-body img{max-width:100%;max-height:72vh;display:block}
#m-note{padding:8px 12px;min-height:30px}
/* statistics */
.stats{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}
@media(max-width:900px){.stats{grid-template-columns:1fr}}
.stats h4{margin:0 0 8px;font-size:11px;letter-spacing:.08em;color:var(--mut);text-transform:uppercase}
.heat{display:grid;grid-template-columns:22px repeat(24,minmax(0,1fr));gap:2px;align-items:center}
.heat .hl{font-size:10px;color:var(--mut)}
.heat .c{aspect-ratio:1;border-radius:3px;background:var(--field);border:1px solid var(--line)}
.dbars{display:flex;align-items:flex-end;gap:5px;height:88px}
.dbars .d{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;cursor:pointer;min-width:0}
.dbars .d i{display:block;width:100%;background:var(--acc);border-radius:4px 4px 0 0;min-height:2px;opacity:.75}
.dbars .d.on i{opacity:1;background:var(--yel)}
.dbars .d small{font-size:10px;color:var(--mut);margin-top:3px}
.tl{position:relative;height:38px;background:var(--field);border:1px solid var(--line);border-radius:8px;margin-top:6px}
.tl .m{position:absolute;top:5px;bottom:5px;width:5px;margin-left:-2px;border-radius:3px;background:var(--acc);cursor:pointer}
.tl .m.image{background:var(--mut)}
.tl .m:hover{background:var(--yel)}
.tl .tk{position:absolute;top:100%;font-size:10px;color:var(--mut);transform:translateX(-50%);margin-top:2px}
</style></head><body>
<header>
  <h1>Motion Watch</h1>
  <!--NAV-->
  <span class="badge" id="b-count">–</span>
  <span class="badge" id="b-disk">–</span>
  <span class="badge red" id="b-live" hidden>● REC</span>
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <details class="card" id="statcard">
    <summary data-i18n="Statistics">Statistics</summary>
    <div class="stats">
      <div><h4 data-i18n="Events per weekday and hour">Events per weekday and hour</h4><div class="heat" id="heat"></div></div>
      <div><h4 data-i18n="Last 14 days (click a day)">Last 14 days (click a day)</h4><div class="dbars" id="dbars"></div>
        <h4 style="margin-top:16px" id="tl-title"></h4><div class="tl" id="tl"></div><div style="height:16px"></div></div>
    </div>
  </details>
  <section class="card filters">
    <div>
      <span class="flab" data-i18n="Date">Date</span>
      <div class="dates"><input type="date" id="f-from" aria-label="from"><input type="date" id="f-to" aria-label="to"></div>
      <div class="quick">
        <button class="sec" data-q="all" data-i18n="All time">All time</button>
        <button class="sec" data-q="today" data-i18n="Today">Today</button>
        <button class="sec" data-q="yday" data-i18n="Yesterday">Yesterday</button>
        <button class="sec" data-q="week" data-i18n="Last 7 days">Last 7 days</button>
      </div>
    </div>
    <div>
      <span class="flab" data-i18n="Type">Type</span>
      <div class="seg" id="f-kind">
        <button data-kind="" data-i18n="All">All</button><button data-kind="video" data-i18n="Videos">Videos</button><button data-kind="image" data-i18n="Images">Images</button><button data-kind="timelapse" data-i18n="Timelapse">Timelapse</button>
      </div>
    </div>
    <div id="w-sched"><label for="f-sched" data-i18n="Schedule">Schedule</label><select id="f-sched"></select></div>
    <div id="w-src"><label for="f-src" data-i18n="Video source">Video source</label><select id="f-src"></select></div>
    <div id="w-place" hidden><label for="f-place" data-i18n="Place">Place</label><select id="f-place"></select></div>
    <div><label for="f-q" data-i18n="Search">Search</label><input type="text" id="f-q" placeholder="person_2026…"></div>
    <div><label for="f-sort" data-i18n="Sort">Sort</label>
      <select id="f-sort"><option value="new" data-i18n="Newest first">Newest first</option><option value="old" data-i18n="Oldest first">Oldest first</option><option value="size" data-i18n="Largest first">Largest first</option></select></div>
  </section>
  <div class="bar">
    <span class="mut" id="result-info"></span><span class="sp"></span>
    <button class="sec favf" id="btn-map">🗺 <span data-i18n="Map">Map</span></button>
    <button class="sec favf" id="btn-fav">★ <span data-i18n="Favorites">Favorites</span></button>
    <button class="sec favf" id="btn-fa">👎 <span data-i18n="False alarms">False alarms</span></button>
    <button class="sec" id="btn-reset" data-i18n="Reset filters">Reset filters</button>
    <button class="sec" id="btn-refresh" data-i18n="Refresh">Refresh</button>
    <button class="sec" id="btn-select" data-i18n="Select">Select</button>
    <button class="sec" id="btn-starsel" hidden></button>
    <button class="sec" id="btn-zipsel" hidden></button>
    <button class="red" id="btn-delsel" hidden></button>
  </div>
  <section class="card fa-card" id="fa-card" hidden></section>
  <details class="card loopcard" id="loopcard" hidden>
    <summary><span data-i18n="🎞 Continuous recording">🎞 Continuous recording</span></summary>
    <div class="lhead"><button class="sec" type="button" id="lp-prev">‹</button><input type="date" id="lp-day"><button class="sec" type="button" id="lp-next">›</button><span class="mut" id="lp-info"></span></div>
    <div class="ltl" id="lp-tl"></div>
    <div class="lhours"><span>0</span><span>6</span><span>12</span><span>18</span><span>24</span></div>
    <div class="mut" id="lp-note" style="font-size:12px;margin-top:4px"></div>
  </details>
  <section class="card mapcard" id="mapcard" hidden>
    <div class="map" id="map"><div class="mtiles"></div><div class="mpins"></div>
      <div class="mzoom"><button class="sec" type="button" data-z="1">+</button><button class="sec" type="button" data-z="-1">−</button><button class="sec" type="button" data-z="0" id="map-fit">⤢</button></div>
      <div class="mattr" id="map-attr">© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a></div></div>
    <div class="mut" id="map-note"></div>
    <div id="map-pop"></div>
  </section>
  <div id="grid"></div>
  <div class="empty" id="empty" hidden data-i18n="No recordings match the filters">No recordings match the filters</div>
  <div style="text-align:center;margin:14px"><button class="sec" id="more" hidden data-i18n="Load more">Load more</button></div>
</main>
<div class="modal" id="modal" hidden>
  <div class="mbox">
    <div class="mhead">
      <b id="m-title"></b><span class="mut" id="m-meta"></span><span class="sp"></span>
      <button class="sec" id="m-prev" title="←">&#8249;</button><button class="sec" id="m-next" title="→">&#8250;</button>
      <button class="sec" id="m-fav" title="★">☆</button>
      <button class="sec" id="m-fa" title="👎">👎</button>
      <button class="sec" id="m-share" title="Share">⤴</button>
      <a class="btn sec" id="m-pdf" target="_blank" rel="noopener" title="Report (PDF)">📄</a>
      <a class="btn sec" id="m-dl" download data-i18n="Download">Download</a>
      <button class="red" id="m-del" data-i18n="Delete">Delete</button>
      <button class="sec" id="m-close">&#10005;</button>
    </div>
    <div id="m-farow" hidden></div>
    <div id="m-body"></div>
    <div class="mut" id="m-note"></div>
  </div>
</div>
<form id="zipform" method="post" action="/rec/zip" hidden><input type="hidden" name="names" id="zipnames"></form>
<script>
/*COMMON*/
Object.assign(I18N.de, {
  "Date": "Datum", "All time": "Gesamter Zeitraum", "Today": "Heute", "Yesterday": "Gestern", "Last 7 days": "Letzte 7 Tage", "Type": "Typ", "All": "Alle", "Videos": "Videos",
  "Images": "Bilder", "Schedule": "Zeitplan", "Video source": "Videoquelle", "Search": "Suche", "Sort": "Sortierung",
  "Newest first": "Neueste zuerst", "Oldest first": "Älteste zuerst", "Largest first": "Grösste zuerst",
  "Reset filters": "Filter zurücksetzen", "Refresh": "Aktualisieren", "Select": "Auswählen", "Cancel selection": "Auswahl beenden",
  "Delete selected": "Auswahl löschen", "Load more": "Mehr laden", "No recordings match the filters": "Keine Aufnahmen passen zu den Filtern",
  "Download": "Herunterladen", "Delete": "Löschen", "Share": "Teilen", "Preparing the video for sharing …": "Video wird zum Teilen vorbereitet …", "Inside any schedule": "In irgendeinem Zeitplan",
  "Outside all schedules": "Ausserhalb aller Zeitpläne", "All sources": "Alle Quellen", "off": "aus", "every day": "täglich",
  "recordings": "Aufnahmen", "shown": "angezeigt", "persons": "Personen", "Preparing video…": "Video wird vorbereitet …",
  "Converting for the browser (one time)…": "Wird für den Browser umgewandelt (einmalig) …",
  "This video uses a codec browsers cannot play. Install ffmpeg on the Pi (sudo apt install ffmpeg) or download the file.":
    "Dieses Video nutzt einen Codec, den Browser nicht abspielen. Installiere ffmpeg auf dem Pi (sudo apt install ffmpeg) oder lade die Datei herunter.",
  "Still recording - available when it ends.": "Aufnahme läuft noch - danach verfügbar.", "Error": "Fehler",
  "Delete this recording?": "Diese Aufnahme löschen?", "recordings?": "Aufnahmen löschen?", "Image": "Bild", "Video": "Video",
  "Statistics": "Statistik", "Events per weekday and hour": "Ereignisse pro Wochentag und Stunde", "Last 14 days (click a day)": "Letzte 14 Tage (Tag anklicken)",
  "Favorites": "Favoriten", "Protect selected": "Auswahl schützen", "Download ZIP": "ZIP laden", "events": "Ereignisse", "Timeline": "Zeitleiste",
  "Favorites are never deleted by the automatic cleanup": "Favoriten werden vom automatischen Aufräumen nie gelöscht", "Timelapse": "Zeitraffer",
  "Place": "Ort", "All places": "Alle Orte", "Without location": "Ohne Ort", "Map": "Karte", "Show only this place": "Nur diesen Ort zeigen",
  "Rename place": "Ort umbenennen", "Name of this place (empty = automatic)": "Name dieses Orts (leer = automatisch)", "Fit": "Alles zeigen",
  "recordings with location": "Aufnahmen mit Ort",
  "No recordings with a location yet. Photos and videos get one when the GPS position is known (phone or fixed place in the settings).":
    "Noch keine Aufnahmen mit Ort. Fotos und Videos bekommen einen, sobald die GPS-Position bekannt ist (Handy oder fester Ort in den Einstellungen).",
  "Map background not reachable (offline?) – the points are still right.": "Kartenhintergrund nicht erreichbar (offline?) – die Punkte stimmen trotzdem.",
  "Map background is switched off in the settings.": "Kartenhintergrund ist in den Einstellungen ausgeschaltet."
});
const DAYN = () => ({de: ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"], fr: ["lu", "ma", "me", "je", "ve", "sa", "di"], it: ["lu", "ma", "me", "gi", "ve", "sa", "do"], rm: ["gli", "ma", "me", "gie", "ve", "so", "du"]})[LANG] || ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const pad = n => String(n).padStart(2, "0");
const ymd = d => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
function fmtSize(b) { return b < 1024 ? b + " B" : b < 1048576 ? (b / 1024).toFixed(0) + " KB" : b < 1073741824 ? (b / 1048576).toFixed(1) + " MB" : (b / 1073741824).toFixed(2) + " GB"; }
function fmtDur(s) { if (s === null || s === undefined) return ""; s = Math.round(s); return Math.floor(s / 60) + ":" + pad(s % 60); }
function fmtDays(days) {
  const N = DAYN();
  if (days.length === 7) return t("every day");
  if (days.join() === "0,1,2,3,4") return N[0] + "–" + N[4];
  return days.map(d => N[d]).join(", ") || "–";
}

const F = {from: "", to: "", kind: "", schedule: "", source: "", q: "", sort: "new", fav: "", place: "", fa: ""};
let items = [], DATA = null, reqId = 0, selecting = false, modalIdx = -1, modalToken = 0, openAfter = null, tlDay = "";
const selected = new Set();

async function load(reset) {
  const my = ++reqId, p = new URLSearchParams();
  Object.entries(F).forEach(([k, v]) => { if (v) p.set(k, v); });
  p.set("offset", reset ? 0 : items.length); p.set("limit", 48);
  let j;
  try { j = await (await fetch("/api/recordings?" + p)).json(); } catch (e) { return; }
  if (my !== reqId) return;                           // a newer request is on its way
  DATA = j;
  const grid = $("#grid");
  if (reset) { items = []; grid.textContent = ""; selected.clear(); updateSelBtn(); }
  j.items.forEach(it => { items.push(it); grid.appendChild(card(it)); });
  $("#b-count").textContent = j.disk.files + " " + t("recordings");
  $("#b-disk").textContent = j.disk.mb + " MB / " + j.disk.limit_gb + " GB";
  $("#b-live").hidden = !j.recording;
  $("#result-info").textContent = items.length + " / " + j.total + " " + t("shown");
  $("#empty").hidden = items.length > 0; $("#more").hidden = items.length >= j.total;
  fillOptions(j);
  if (reset && MAP.on) mapLoad();
  if (openAfter && items.length) { const n = openAfter; openAfter = null; const i = items.findIndex(x => x.name === n); openAt(i >= 0 ? i : 0, items); }
}

function fillOptions(j) {
  const ss = $("#f-sched"), cur = F.schedule;
  $("#w-sched").hidden = !j.schedules.length;
  ss.textContent = "";
  const add = (v, label) => { const o = el("option", "", label); o.value = v; ss.appendChild(o); };
  add("", t("All") + " (" + j.counts.all + ")");
  add("any", t("Inside any schedule") + " (" + j.counts.any + ")");
  add("none", t("Outside all schedules") + " (" + j.counts.none + ")");
  j.schedules.forEach(s => add(String(s.index), (s.active_now ? "● " : "") + s.name + " · " + s.start + "–" + s.end + " · " + fmtDays(s.days)
      + " (" + s.count + ")" + (s.enabled ? "" : " [" + t("off") + "]")));
  ss.value = cur; if (ss.value !== cur) { F.schedule = ""; ss.value = ""; }
  const sr = $("#f-src"), cs = F.source; sr.textContent = "";
  const a0 = el("option", "", t("All sources")); a0.value = ""; sr.appendChild(a0);
  j.sources.forEach(n => { const o = el("option", "", n); o.value = n; sr.appendChild(o); });
  sr.value = cs; if (sr.value !== cs) { F.source = ""; sr.value = ""; }
  $("#w-src").hidden = !j.sources.length;
  const pl = $("#f-place"), cp = F.place; pl.textContent = ""; PLACES = j.places || [];
  const p0 = el("option", "", t("All places")); p0.value = ""; pl.appendChild(p0);
  PLACES.forEach(p => { const o = el("option", "", p.name + " (" + p.count + ")"); o.value = p.id; pl.appendChild(o); });
  if (j.no_place && PLACES.length) { const o = el("option", "", t("Without location") + " (" + j.no_place + ")"); o.value = "none"; pl.appendChild(o); }
  pl.value = cp; if (pl.value !== cp) { F.place = ""; pl.value = ""; }
  $("#w-place").hidden = !PLACES.length;
}

function card(it) {
  const c = el("div", "rc"); c.dataset.name = it.name;
  const th = el("div", "th");
  const img = el("img"); img.loading = "lazy"; img.alt = "";
  img.src = "/rec/thumb/" + encodeURIComponent(it.name);
  img.onerror = () => { img.remove(); th.insertBefore(document.createTextNode(it.kind === "video" ? "▶" : "🖼"), th.firstChild); };
  th.appendChild(img);
  if (it.kind === "video") th.appendChild(el("div", "play", "▶"));
  if (it.false) th.appendChild(el("span", "fatag", "👎 " + FA_TXT()[it.false]));
  th.appendChild(el("span", "tag" + (it.recording ? " live" : ""), it.recording ? "● REC" : (it.timelapse ? "⏱ " : "") + (it.kind === "video" ? "▶ " + fmtDur(it.duration) : t(it.timelapse ? "Timelapse" : "Image"))));
  const st = el("button", "star" + (it.fav ? " on" : ""), it.fav ? "★" : "☆"); st.title = t("Favorites are never deleted by the automatic cleanup");
  st.onclick = async e => { e.stopPropagation(); await setFav([it.name], !it.fav); it.fav = !it.fav; st.className = "star" + (it.fav ? " on" : ""); st.textContent = it.fav ? "★" : "☆"; };
  const cb = el("input", "chk"); cb.type = "checkbox"; cb.onclick = e => e.stopPropagation();
  cb.onchange = () => toggleSel(it.name, cb.checked, c);
  th.append(cb, st);
  const body = el("div", "rb");
  body.appendChild(el("b", "", it.time));
  body.appendChild(el("div", "mut", [fmtSize(it.size), it.persons ? it.persons + " " + t("persons") : "", it.timelapse ? "⏱ " + t("Timelapse") : (it.source || "")].filter(Boolean).join(" · ")));
  if (it.schedules.length) { const ch = el("div", "chips"); it.schedules.forEach(n => ch.appendChild(el("span", "chip", n))); body.appendChild(ch); }
  c.append(th, body);
  c.onclick = () => { if (selecting) { cb.checked = !cb.checked; toggleSel(it.name, cb.checked, c); } else openAt(items.indexOf(it), items); };
  return c;
}
async function setFav(names, value) { const r = await post("/api/rec/fav", {names: names, value: value}); return r; }

function toggleSel(name, on, c) { on ? selected.add(name) : selected.delete(name); c.classList.toggle("sel", on); updateSelBtn(); }
function updateSelBtn() {
  const n = selected.size;
  const d = $("#btn-delsel"), z = $("#btn-zipsel"), s = $("#btn-starsel");
  d.hidden = z.hidden = s.hidden = !selecting;
  d.textContent = t("Delete selected") + " (" + n + ")"; z.textContent = t("Download ZIP") + " (" + n + ")"; s.textContent = "★ " + t("Protect selected") + " (" + n + ")";
  d.disabled = z.disabled = s.disabled = !n;
}
function setSelecting(on) {
  selecting = on; document.body.classList.toggle("selecting", on);
  $("#btn-select").textContent = on ? t("Cancel selection") : t("Select");
  if (!on) { selected.clear(); document.querySelectorAll(".rc.sel").forEach(c => c.classList.remove("sel")); document.querySelectorAll(".chk").forEach(c => c.checked = false); }
  updateSelBtn();
}
async function remove(names) {
  const msg = names.length === 1 ? t("Delete this recording?") : names.length + " " + t("recordings?");
  if (!confirm(msg)) return false;
  await post("/api/rec/delete", {names});
  return true;
}
function zip(names) { $("#zipnames").value = JSON.stringify(names); $("#zipform").submit(); }
// share a picture / video (with the small logo, if switched on): the phone's share menu, otherwise download
async function recShare(it) {
  const b = $("#m-share"), note = $("#m-note"); const video = /\.mp4$/i.test(it.name);
  const url = "/rec/share/" + encodeURIComponent(it.name) + "?cap=" + encodeURIComponent(it.time);
  b.disabled = true; if (video) note.textContent = t("Preparing the video for sharing …");
  try {
    const r = await fetch(url); if (!r.ok) throw new Error(await r.text());
    const bl = await r.blob(), f = new File([bl], it.name, {type: video ? "video/mp4" : "image/jpeg"});
    note.textContent = "";
    if (navigator.canShare && navigator.canShare({files: [f]})) { await navigator.share({files: [f], title: "Motion Watch – " + it.time}); }
    else { const a = el("a"); a.href = URL.createObjectURL(bl); a.download = it.name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 5000); }
  } catch (e) { if (!(e && e.name === "AbortError")) note.textContent = "⚠ " + (e.message || e); }
  b.disabled = false;
}

// ---- viewer ----
let ML = [];                                          // the list the viewer walks through (the grid or a place on the map)
function openAt(i, list) {
  if (list) ML = list;
  if (i < 0 || i >= ML.length) return;
  modalIdx = i; const it = ML[i], token = ++modalToken;
  $("#modal").hidden = false;
  $("#m-title").textContent = it.time; $("#m-meta").textContent = [fmtSize(it.size), it.source || "", it.schedules.join(", ")].filter(Boolean).join(" · ");
  $("#m-dl").href = "/rec/file/" + encodeURIComponent(it.name) + "?dl=1"; $("#m-dl").setAttribute("download", it.name);
  $("#m-share").onclick = () => recShare(it); $("#m-share").title = t("Share");
  $("#m-pdf").href = "/rec/report/" + encodeURIComponent(it.name) + "?lang=" + LANG; $("#m-pdf").title = t("Event report (PDF) for the police / insurance");
  $("#m-fav").textContent = it.fav ? "★" : "☆"; $("#m-fav").style.color = it.fav ? "var(--yel)" : "";
  faRow(it);
  $("#m-prev").disabled = i === 0; $("#m-next").disabled = i === ML.length - 1;
  const body = $("#m-body"), note = $("#m-note"); body.textContent = ""; note.textContent = "";
  if (it.kind === "image") { const im = el("img"); im.src = "/rec/file/" + encodeURIComponent(it.name); body.appendChild(im); }
  else showVideo(it, token);
}
async function showVideo(it, token) {
  const body = $("#m-body"), note = $("#m-note");
  note.textContent = t("Preparing video…");
  for (let n = 0; n < 1200; n++) {                    // converting a long clip can take a while: poll up to ~30 min
    const r = await post("/api/rec/prepare", {name: it.name});
    if (token !== modalToken) return;                 // the viewer was closed or moved on
    if (r.state === "ready") {
      const v = el("video"); v.controls = true; v.autoplay = true; v.playsInline = true; v.src = r.url; body.appendChild(v); note.textContent = ""; return;
    }
    if (r.state === "converting") { note.textContent = t("Converting for the browser (one time)…"); await sleep(1500); continue; }
    if (r.state === "live") { note.textContent = t("Still recording - available when it ends."); return; }
    if (r.state === "unsupported") {
      note.textContent = t("This video uses a codec browsers cannot play. Install ffmpeg on the Pi (sudo apt install ffmpeg) or download the file."); return;
    }
    note.textContent = t("Error") + ": " + (r.error || r.state); return;
  }
}
function closeModal() { modalToken++; $("#modal").hidden = true; $("#m-body").textContent = ""; modalIdx = -1; }
$("#m-close").onclick = closeModal;
$("#m-prev").onclick = () => openAt(modalIdx - 1);
$("#m-next").onclick = () => openAt(modalIdx + 1);
$("#m-fav").onclick = async () => { const it = ML[modalIdx]; if (!it) return; await setFav([it.name], !it.fav); it.fav = !it.fav; openAtKeep(); load(true); };
function openAtKeep() { const it = ML[modalIdx]; if (it) { $("#m-fav").textContent = it.fav ? "★" : "☆"; $("#m-fav").style.color = it.fav ? "var(--yel)" : ""; } }
$("#m-del").onclick = async () => { const it = ML[modalIdx]; if (it && await remove([it.name])) { closeModal(); load(true); loadStats(); } };
$("#modal").addEventListener("click", e => { if (e.target.id === "modal") closeModal(); });
addEventListener("keydown", e => {
  if ($("#modal").hidden) return;
  if (e.key === "Escape") closeModal(); else if (e.key === "ArrowLeft") openAt(modalIdx - 1); else if (e.key === "ArrowRight") openAt(modalIdx + 1);
});

// ---- statistics ----
async function loadStats() {
  const p = new URLSearchParams({days: 14}); if (tlDay) p.set("day", tlDay);
  let j; try { j = await (await fetch("/api/recordings/stats?" + p)).json(); } catch (e) { return; }
  if (!tlDay) tlDay = ymd(new Date());
  if (!j.day) { const p2 = new URLSearchParams({days: 14, day: tlDay}); try { j = await (await fetch("/api/recordings/stats?" + p2)).json(); } catch (e) { return; } }
  const heat = $("#heat"); heat.textContent = "";
  const max = Math.max(1, ...j.heat.map(r => Math.max(...r)));
  heat.appendChild(el("span", "hl", ""));
  for (let h = 0; h < 24; h++) heat.appendChild(el("span", "hl", h % 6 === 0 ? String(h) : ""));
  j.heat.forEach((row, d) => {
    heat.appendChild(el("span", "hl", DAYN()[d]));
    row.forEach((n, h) => { const c = el("span", "c"); c.title = DAYN()[d] + " " + pad(h) + ":00 · " + n + " " + t("events");
      if (n) { c.style.background = "var(--acc)"; c.style.opacity = String(0.22 + 0.78 * n / max); c.style.borderColor = "transparent"; } heat.appendChild(c); });
  });
  const mx = Math.max(1, ...j.days.map(d => d.count)), db = $("#dbars"); db.textContent = "";
  j.days.forEach(d => {
    const b = el("div", "d" + (d.date === tlDay ? " on" : "")); b.title = d.date + " · " + d.count + " " + t("events");
    const i = el("i"); i.style.height = Math.max(2, 100 * d.count / mx * 0.8) + "%"; b.append(i, el("small", "", d.date.slice(8)));
    b.onclick = () => { tlDay = d.date; setDates(d.date, d.date); loadStats(); }; db.appendChild(b);
  });
  $("#tl-title").textContent = t("Timeline") + " · " + tlDay + " · " + j.events.length + " " + t("events");
  const tl = $("#tl"); tl.textContent = "";
  [0, 3, 6, 9, 12, 15, 18, 21, 24].forEach(h => { const k = el("span", "tk", pad(h)); k.style.left = (h / 24 * 100) + "%"; tl.appendChild(k); });
  j.events.forEach(ev => { const m = el("span", "m " + ev.kind); m.style.left = (ev.m / 1440 * 100) + "%"; m.title = ev.t;
    m.onclick = () => { openAfter = ev.name; setDates(tlDay, tlDay); }; tl.appendChild(m); });
}

// ---- filter controls ----
function setDates(a, b) { F.from = a; F.to = b; $("#f-from").value = a; $("#f-to").value = b; load(true); }
document.querySelectorAll(".quick button").forEach(b => b.onclick = () => {
  const now = new Date(), d1 = new Date(now), d7 = new Date(now);
  d1.setDate(d1.getDate() - 1); d7.setDate(d7.getDate() - 6);
  const q = b.dataset.q;
  if (q === "all") setDates("", ""); else if (q === "today") setDates(ymd(now), ymd(now));
  else if (q === "yday") setDates(ymd(d1), ymd(d1)); else setDates(ymd(d7), ymd(now));
});
$("#f-from").onchange = () => { F.from = $("#f-from").value; load(true); };
$("#f-to").onchange = () => { F.to = $("#f-to").value; load(true); };
document.querySelectorAll("#f-kind button").forEach(b => b.onclick = () => { F.kind = b.dataset.kind; markKind(); load(true); });
function markKind() { document.querySelectorAll("#f-kind button").forEach(b => b.classList.toggle("sel", b.dataset.kind === F.kind)); }
$("#f-sched").onchange = () => { F.schedule = $("#f-sched").value; load(true); };
$("#f-src").onchange = () => { F.source = $("#f-src").value; load(true); };
$("#f-place").onchange = () => { F.place = $("#f-place").value; load(true); };

// ---- false alarms: «was nothing» + suggestions ----
Object.assign(I18N.de, {"Continuous recording (all the time, few pictures per second) with a timeline": "Daueraufnahme (immer, wenige Bilder pro Sekunde) mit Zeitleiste", "Continuous recording: keep (hours)": "Daueraufnahme: behalten (Stunden)", "Continuous recording: pictures per second": "Daueraufnahme: Bilder pro Sekunde", "🎞 Continuous recording": "🎞 Daueraufnahme", "Continuous recording": "Daueraufnahme", "recording now": "wird gerade aufgenommen", "alarms": "Alarme", "Tap a blue piece to watch it. Red lines: alarms.": "Ein blaues Stück antippen zum Ansehen. Rote Striche: Alarme.", "Continuous recording is off (Settings → Recording).": "Daueraufnahme ist aus (Einstellungen → Aufnahme)."});
Object.assign(I18N.de, {"Event report (PDF) for the police / insurance": "Ereignisbericht (PDF) für Polizei / Versicherung"});
Object.assign(I18N.de, {"False alarms": "Fehlalarme", "Animal": "Tier", "Wind / branches": "Wind / Äste", "Light / shadow": "Licht / Schatten", "Rain": "Regen", "Car": "Auto", "Other": "Anderes", "Was nothing (false alarm)": "War nichts (Fehlalarm)", "Was nothing - what was it?": "War nichts – was war es?", "Was real after all": "War doch echt", "false alarms marked in the last": "Fehlalarme markiert in den letzten", "days": "Tagen", "of": "von", "suggestions:": "Vorschläge:", "Open": "Öffnen", "Take over": "Übernehmen", "Switch on the automatic wind detection": "Automatische Wind-Erkennung einschalten", "Less sensitive to light changes": "Weniger empfindlich auf Lichtwechsel", "Switch on the automatic rain detection": "Automatische Regen-Erkennung einschalten", "Detect rain earlier": "Regen früher erkennen", "Switch on the vehicle filter": "Fahrzeug-Filter einschalten", "Somewhat less sensitive overall": "Insgesamt etwas weniger empfindlich"});
const FA_TXT = () => ({animal: "🐾 " + t("Animal"), wind: "🌿 " + t("Wind / branches"), light: "💡 " + t("Light / shadow"), rain: "🌧 " + t("Rain"), car: "🚗 " + t("Car"), other: "❓ " + t("Other")});
function faRow(it) {
  const r = $("#m-farow"); r.textContent = ""; r.hidden = true;
  $("#m-fa").hidden = !!it.timelapse; $("#m-fa").classList.toggle("on", !!it.false);
  $("#m-fa").title = t("Was nothing (false alarm)");
  $("#m-fa").onclick = () => { r.hidden = !r.hidden; };
  r.appendChild(el("span", "mut", t("Was nothing - what was it?")));
  Object.entries(FA_TXT()).forEach(([k, v]) => { const b = el("button", "sec" + (it.false === k ? " on" : ""), v); b.type = "button";
    b.onclick = () => faSet(it, k); r.appendChild(b); });
  if (it.false) { const b = el("button", "sec", "↩ " + t("Was real after all")); b.type = "button"; b.onclick = () => faSet(it, ""); r.appendChild(b); }
}
async function faSet(it, cause) {
  await post("/api/rec/false", {names: [it.name], cause: cause}); it.false = cause || null; faRow(it);
  const c = document.querySelector('.rc[data-name="' + CSS.escape(it.name) + '"]'); if (c) { const n = card(it); c.replaceWith(n); }
  toast(cause ? "👎 " + FA_TXT()[cause] : "↩ " + t("Was real after all")); faLoad();
}
async function faLoad() {
  let j; try { j = await (await fetch("/api/fa?lang=" + LANG, {cache: "no-store"})).json(); } catch (e) { return; }
  const c = $("#fa-card"); c.textContent = ""; c.hidden = !(j.suggestions || []).length;
  if (c.hidden) return;
  c.appendChild(el("div", "fah", "💡 " + j.false + " " + t("false alarms marked in the last") + " " + j.days + " " + t("days") + " (" + t("of") + " " + j.total + ") – " + t("suggestions:")));
  j.suggestions.forEach(x => { const r = el("div", "fas"); r.appendChild(el("span", "", x.text + " (" + x.n + "×)"));
    if (x.link) { const a = el("a", "btn sec", t("Open")); a.href = x.link; r.appendChild(a); }
    else { const b = el("button", "", t("Take over")); b.type = "button"; b.onclick = async () => { const q = await post("/api/fa", {id: x.id, lang: LANG}); toast(q.ok ? "✓ " + t("Saved") : "⚠"); faLoad(); }; r.appendChild(b); }
    c.appendChild(r); });
}
// ---- continuous recording: 24 h timeline, one cell = 10 minutes, red marks = alarms ----
const LP = {day: ""};
async function loopLoad() {
  if (!LP.day) LP.day = ymd(new Date());
  let j; try { j = await (await fetch("/api/loop?day=" + LP.day, {cache: "no-store"})).json(); } catch (e) { return; }
  const card = $("#loopcard"); card.hidden = !j.on && !(j.days || []).length; if (card.hidden) return;
  $("#lp-day").value = LP.day;
  const tl = $("#lp-tl"); tl.textContent = "";
  const segs = {}; (j.segments || []).forEach(s => { const k = Math.floor(s.min / 10); if (!segs[k] || segs[k].live) segs[k] = s; });   // a finished piece wins
  const list = (j.segments || []).filter(s => !s.live).map(s => ({name: s.name, kind: "video", time: LP.day + " " + s.start, size: s.size, schedules: [], source: t("Continuous recording")}));
  for (let i = 0; i < 144; i++) { const s = segs[i], c = el("i", s ? (s.live ? "live" : "on") : ""); const hh = String(Math.floor(i / 6)).padStart(2, "0"), mm = String(i % 6 * 10).padStart(2, "0");
    c.title = hh + ":" + mm + (s ? (s.live ? " · " + t("recording now") : "") : " · –");
    if (s && !s.live) c.onclick = () => openAt(list.findIndex(x => x.name === s.name), list);
    tl.appendChild(c); }
  (j.events || []).forEach(m => { const b = el("b"); b.style.left = (m / 1440 * 100) + "%"; tl.appendChild(b); });
  $("#lp-info").textContent = (j.segments || []).length + " × 10 min" + ((j.events || []).length ? " · " + j.events.length + " " + t("alarms") : "");
  $("#lp-note").textContent = j.on ? t("Tap a blue piece to watch it. Red lines: alarms.") : t("Continuous recording is off (Settings → Recording).");
}
$("#lp-day").onchange = () => { LP.day = $("#lp-day").value; loopLoad(); };
$("#lp-prev").onclick = () => { const d = new Date(LP.day + "T12:00"); d.setDate(d.getDate() - 1); LP.day = ymd(d); loopLoad(); };
$("#lp-next").onclick = () => { const d = new Date(LP.day + "T12:00"); d.setDate(d.getDate() + 1); LP.day = ymd(d); loopLoad(); };
$("#loopcard").addEventListener("toggle", () => { if ($("#loopcard").open) loopLoad(); });
setTimeout(loopLoad, 400); setInterval(() => { if ($("#loopcard").open && !document.hidden) loopLoad(); }, 60000);
$("#btn-fa").onclick = () => { F.fa = F.fa ? "" : "1"; $("#btn-fa").classList.toggle("on", !!F.fa); load(true); };
setTimeout(faLoad, 300);

// ---- map of the places (OpenStreetMap tiles, drawn without any library) ----
let PLACES = [];
const MAP = {on: false, z: 3, cx: 0, cy: 0, pts: [], places: [], sel: "", online: true, bad: 0, fitted: false};
const mapW = (lat, lon, z) => { const s = 256 * Math.pow(2, z), r = Math.max(-85, Math.min(85, lat)) * Math.PI / 180;
  return [(lon + 180) / 360 * s, (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * s]; };
async function mapLoad() {
  const p = new URLSearchParams(); Object.entries(F).forEach(([k, v]) => { if (v) p.set(k, v); }); p.set("map", "1"); p.set("limit", 1);
  let j; try { j = await (await fetch("/api/recordings?" + p)).json(); } catch (e) { return; }
  MAP.pts = j.points || []; MAP.online = j.map_online !== false;
  const used = new Set(MAP.pts.map(x => x.place));
  MAP.places = (j.places || []).filter(x => used.has(x.id)).map(x => Object.assign({}, x, {n: MAP.pts.filter(q => q.place === x.id).length}));
  if (!MAP.places.some(x => x.id === MAP.sel)) { MAP.sel = ""; $("#map-pop").textContent = ""; }
  $("#map-attr").hidden = !MAP.online;
  mapNote(); if (!MAP.fitted) mapFit(); else mapDraw(); if (MAP.sel) mapPop(MAP.sel);
}
function mapNote() {
  const n = $("#map-note");
  n.textContent = !MAP.pts.length ? t("No recordings with a location yet. Photos and videos get one when the GPS position is known (phone or fixed place in the settings).")
    : MAP.pts.length + " " + t("recordings with location") + (!MAP.online ? " · " + t("Map background is switched off in the settings.")
    : MAP.bad > 3 ? " · " + t("Map background not reachable (offline?) – the points are still right.") : "");
}
function mapFit() {
  const m = $("#map"), w = m.clientWidth || 600, h = m.clientHeight || 400, P = MAP.places.length ? MAP.places : [{lat: 46.8, lon: 8.2}];
  let z = P.length === 1 ? 13 : 16;
  for (; z > 2; z--) {
    const xy = P.map(p => mapW(p.lat, p.lon, z)), xs = xy.map(a => a[0]), ys = xy.map(a => a[1]);
    if (Math.max(...xs) - Math.min(...xs) < w - 90 && Math.max(...ys) - Math.min(...ys) < h - 90) break;
  }
  if (!MAP.places.length) z = 7;
  const xy = P.map(p => mapW(p.lat, p.lon, z));
  MAP.z = z; MAP.cx = (Math.min(...xy.map(a => a[0])) + Math.max(...xy.map(a => a[0]))) / 2; MAP.cy = (Math.min(...xy.map(a => a[1])) + Math.max(...xy.map(a => a[1]))) / 2;
  MAP.fitted = MAP.places.length > 0; mapDraw();
}
function mapZoom(dz, px, py) {
  const m = $("#map"), w = m.clientWidth, h = m.clientHeight; if (px === undefined) { px = w / 2; py = h / 2; }
  const z2 = Math.max(2, Math.min(18, MAP.z + dz)); if (z2 === MAP.z) return;
  const f = Math.pow(2, z2 - MAP.z), wx = MAP.cx - w / 2 + px, wy = MAP.cy - h / 2 + py;
  MAP.cx = wx * f - px + w / 2; MAP.cy = wy * f - py + h / 2; MAP.z = z2; mapDraw();
}
function mapDraw() {
  const m = $("#map"), w = m.clientWidth, h = m.clientHeight, z = MAP.z, N = Math.pow(2, z), x0 = MAP.cx - w / 2, y0 = MAP.cy - h / 2;
  const T = m.querySelector(".mtiles"), have = {}; T.querySelectorAll("img").forEach(i => { have[i.dataset.k] = i; });
  if (MAP.online) {
    for (let ty = Math.floor(y0 / 256); ty <= Math.floor((y0 + h) / 256); ty++) {
      if (ty < 0 || ty >= N) continue;
      for (let tx = Math.floor(x0 / 256); tx <= Math.floor((x0 + w) / 256); tx++) {
        const k = z + "/" + (((tx % N) + N) % N) + "/" + ty;
        let im = have[k + "@" + tx];
        if (!im) { im = el("img"); im.alt = ""; im.dataset.k = k + "@" + tx; im.onerror = () => { im.style.visibility = "hidden"; MAP.bad++; mapNote(); };
          im.src = "https://tile.openstreetmap.org/" + k + ".png"; T.appendChild(im); }
        im.style.left = Math.round(tx * 256 - x0) + "px"; im.style.top = Math.round(ty * 256 - y0) + "px"; im.dataset.keep = "1";
      }
    }
  }
  T.querySelectorAll("img").forEach(i => { if (i.dataset.keep) delete i.dataset.keep; else i.remove(); });
  const Pn = m.querySelector(".mpins"); Pn.textContent = "";
  if (z >= 13) MAP.pts.forEach(p => { const [x, y] = mapW(p.lat, p.lon, z); if (x < x0 - 20 || x > x0 + w + 20 || y < y0 - 20 || y > y0 + h + 20) return;
    const d = el("div", "mdot"); d.style.left = (x - x0) + "px"; d.style.top = (y - y0) + "px"; Pn.appendChild(d); });
  MAP.places.forEach(p => { const [x, y] = mapW(p.lat, p.lon, z);
    const b = el("div", "mpin" + (p.id === MAP.sel ? " sel" : ""), String(p.n)); b.title = p.name;
    b.style.left = (x - x0) + "px"; b.style.top = (y - y0) + "px";
    b.onpointerdown = e => e.stopPropagation(); b.onclick = e => { e.stopPropagation(); mapPop(p.id); };
    Pn.appendChild(b); });
}
function mapPop(id) {
  MAP.sel = id; mapDraw();
  const p = MAP.places.find(x => x.id === id), box = $("#map-pop"); box.textContent = ""; if (!p) return;
  const list = MAP.pts.filter(x => x.place === id).sort((a, b) => a.time < b.time ? 1 : -1);
  const pop = el("div", "mpop"), hd = el("div", "mh");
  hd.append(el("b", "", "📍 " + p.name), el("span", "mut", list.length + " " + t("recordings") + " · " + list[list.length - 1].time.slice(0, 10) + (list.length > 1 ? " – " + list[0].time.slice(0, 10) : "")));
  const rn = el("button", "sec", "✎"); rn.type = "button"; rn.title = t("Rename place");
  rn.onclick = async () => { const v = prompt(t("Name of this place (empty = automatic)"), p.name); if (v === null) return; await post("/api/places", {id: id, name: v}); load(true); };
  const only = el("button", "sec", t("Show only this place")); only.type = "button";
  only.onclick = () => { F.place = id; $("#f-place").value = id; load(true); $("#grid").scrollIntoView({behavior: "smooth", block: "start"}); };
  hd.append(rn, only); pop.appendChild(hd);
  const th = el("div", "mth");
  list.slice(0, 24).forEach((it, i) => { const c = el("div"); const im = el("img"); im.loading = "lazy"; im.alt = ""; im.src = "/rec/thumb/" + encodeURIComponent(it.name);
    c.append(im, el("div", "mut", (it.kind === "video" ? "▶ " : "") + it.time.slice(5, 16))); c.onclick = () => openAt(i, list); th.appendChild(c); });
  pop.appendChild(th); box.appendChild(pop);
}
(function () {
  const m = $("#map"), act = new Map(); let last = null, pinch = 0, moved = 0;
  m.addEventListener("pointerdown", e => { m.setPointerCapture(e.pointerId); act.set(e.pointerId, [e.clientX, e.clientY]); moved = 0; m.classList.add("drag");
    if (act.size === 2) { const [a, b] = [...act.values()]; pinch = Math.hypot(a[0] - b[0], a[1] - b[1]); } });
  m.addEventListener("pointermove", e => { if (!act.has(e.pointerId)) return; const o = act.get(e.pointerId); act.set(e.pointerId, [e.clientX, e.clientY]);
    if (act.size === 1) { MAP.cx -= e.clientX - o[0]; MAP.cy -= e.clientY - o[1]; moved += Math.abs(e.clientX - o[0]) + Math.abs(e.clientY - o[1]); mapDraw(); }
    else if (act.size === 2 && pinch) { const [a, b] = [...act.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]), r = m.getBoundingClientRect();
      if (d / pinch > 1.6 || d / pinch < 0.62) { mapZoom(d > pinch ? 1 : -1, (a[0] + b[0]) / 2 - r.left, (a[1] + b[1]) / 2 - r.top); pinch = d; } } });
  const up = e => { act.delete(e.pointerId); if (!act.size) m.classList.remove("drag"); if (act.size < 2) pinch = 0; };
  m.addEventListener("pointerup", up); m.addEventListener("pointercancel", up);
  m.addEventListener("wheel", e => { e.preventDefault(); const r = m.getBoundingClientRect(); mapZoom(e.deltaY < 0 ? 1 : -1, e.clientX - r.left, e.clientY - r.top); }, {passive: false});
  m.addEventListener("dblclick", e => { const r = m.getBoundingClientRect(); mapZoom(1, e.clientX - r.left, e.clientY - r.top); });
  m.querySelectorAll(".mzoom button").forEach(b => { b.onpointerdown = e => e.stopPropagation();
    b.onclick = e => { e.stopPropagation(); const d = +b.dataset.z; d ? mapZoom(d) : mapFit(); }; });
  $("#map-fit").title = t("Fit");
  addEventListener("resize", () => { if (MAP.on) mapDraw(); });
  function show(on) { MAP.on = on; $("#mapcard").hidden = !on; $("#btn-map").classList.toggle("on", on);
    try { localStorage.setItem("mw-map", on ? "1" : "0"); } catch (e) {}
    if (on) { MAP.fitted = false; mapLoad(); } }
  $("#btn-map").onclick = () => show(!MAP.on);
  let v = null; try { v = localStorage.getItem("mw-map"); } catch (e) {}
  if (v === "1") setTimeout(() => show(true), 0);
})();
$("#f-sort").onchange = () => { F.sort = $("#f-sort").value; load(true); };
$("#btn-fav").onclick = () => { F.fav = F.fav ? "" : "1"; $("#btn-fav").classList.toggle("on", !!F.fav); load(true); };
let qTimer = null;
$("#f-q").oninput = () => { clearTimeout(qTimer); qTimer = setTimeout(() => { F.q = $("#f-q").value.trim(); load(true); }, 300); };
$("#btn-reset").onclick = () => {
  Object.assign(F, {from: "", to: "", kind: "", schedule: "", source: "", q: "", sort: "new", fav: "", place: "", fa: ""}); $("#btn-fa").classList.remove("on");
  $("#f-from").value = $("#f-to").value = $("#f-q").value = ""; $("#f-sort").value = "new"; $("#btn-fav").classList.remove("on"); markKind(); load(true);
};
$("#btn-refresh").onclick = () => { load(true); loadStats(); };
$("#btn-select").onclick = () => setSelecting(!selecting);
$("#btn-delsel").onclick = async () => { if (selected.size && await remove([...selected])) { setSelecting(false); load(true); loadStats(); } };
$("#btn-zipsel").onclick = () => { if (selected.size) zip([...selected]); };
$("#btn-starsel").onclick = async () => { if (selected.size) { await setFav([...selected], true); toast("★ " + selected.size); setSelecting(false); load(true); } };
$("#more").onclick = () => load(false);

(async () => {
  await initAppearance(); markKind(); updateSelBtn(); load(true); loadStats();
})();
/*ALERTS*/
</script></body></html>
"""


def web_specs():
    """key -> spec for every setting that may be changed remotely (reuses the GUI definitions)."""
    specs = {}
    for sec, key, label in TOGGLES:
        if key != "web_stream":                  # the stream must not be switched off from the stream itself
            specs[key] = {"type": "bool"}
    for sec, key, label, lo, hi, step in SLIDERS:
        specs[key] = {"type": "num", "min": lo, "max": hi, "step": step}
    return specs


def web_schema(lang=None):
    out = []
    for sec in SECTIONS:
        if simple_hidden(None, sec):
            continue
        toggles = [{"key": k, "label": tr(l, lang)} for s, k, l in TOGGLES if s == sec and k != "web_stream" and not simple_hidden(k)]
        sliders = [{"key": k, "label": tr(l, lang), "min": lo, "max": hi, "step": st} for s, k, l, lo, hi, st in SLIDERS if s == sec and not simple_hidden(k)]
        texts = [x for x in web_texts(lang) if x["section"] == sec and not simple_hidden(x["key"])]
        if toggles or sliders or texts:
            out.append({"id": sec, "name": tr(sec, lang), "toggles": toggles, "sliders": sliders, "texts": texts})
    return out


def set_cfg(key, value):
    """Validated setter for the web API. Returns (ok, error_message)."""
    spec = web_specs().get(key)
    if spec is None:
        return False, "unknown setting"
    if spec["type"] == "bool":
        CFG[key] = bool(value)
        sched_user_changed(key)
        save_settings()
        if key == "patrol":
            log_event("patrol", "Patrol switched ON (web)" if CFG[key] else "Patrol switched OFF (web)")
        return True, ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False, "not a number"
    if not math.isfinite(v):
        return False, "not a number"
    v = max(spec["min"], min(spec["max"], v))
    v = round(round(v / spec["step"]) * spec["step"], 2)
    CFG[key] = int(round(v)) if isinstance(CFG[key], int) else float(v)
    save_settings()
    return True, ""


