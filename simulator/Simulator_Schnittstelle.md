# Motion Watch – Schnittstelle für einen Simulator (Protokoll 1)

Der Simulator ist ein **eigenes Python-Programm**. Er zeigt zwei simulierte Kameras und eine Wärmebildkamera. Motion Watch schickt ihm laufend, wo die Servos stehen und welche Lichter brennen, und der Simulator zeichnet sein Bild entsprechend.

Alles steht in **einer Datei**: `motionwatch_sim_interface.py`. Beide Seiten können sie benutzen:

- **Simulator-Seite:** eine eigene Klasse von `SimServer` ableiten und zwei Methoden schreiben, `render_camera()` und `render_thermal()`.
- **Motion-Watch-Seite:** mit `SimClient` den Zustand schicken und das Wärmebild sowie die Sensor-Ereignisse holen.

Die Verbindung läuft über einfaches HTTP auf einem Port (Standard **8765**). Dafür braucht es nur Python mit numpy und OpenCV, keine weiteren Pakete.

## Was hin und her geht

| Richtung | Adresse | Inhalt |
|---|---|---|
| Motion Watch → Simulator | `POST /state` | Servos (Prozent **und** Grad), Licht weiss / IR, Relais, Ton, scharf, Bildmodus. Etwa 10 × pro Sekunde und bei jeder Änderung. |
| Simulator → Motion Watch | Antwort auf `/state` | Tag/Nacht, Simulationszeit, Lufttemperatur, Luftdruck, Wind, Nummer des letzten Ereignisses |
| Simulator → Motion Watch | `GET /info` | welche Kameras (Auflösung, Blickwinkel, auf dem Schwenkkopf oder fest), Wärmebildkamera, Sensoren |
| Simulator → Motion Watch | `GET /cam/0/video.mjpg`, `/cam/1/video.mjpg` | Kamerabild als MJPEG-Stream. Motion Watch liest das **heute schon** als Netzwerkkamera. |
| Simulator → Motion Watch | `GET /cam/<n>/snapshot.jpg` | ein Einzelbild |
| Simulator → Motion Watch | `GET /thermal.bin` | Wärmebild in °C (float32, Grösse in den Kopfzeilen `X-Width` / `X-Height`) |
| Simulator → Motion Watch | `GET /events?since=<nr>` | Sensor-Ereignisse (PIR, Tür, Gas …) |

## Regeln, damit beide Seiten gleich rechnen

- **Schwenk und Neigung** werden in Prozent übertragen, 0 bis 100. 50 ist die Mitte. Schwenk 100 heisst rechts, Neigung 100 heisst oben.
- Zusätzlich gibt es die Werte in **Grad ab der Mitte**: `pan_deg = (pan − 50) / 50 × pan_limit`. Die Grenzen `pan_limit` / `tilt_limit` kommen aus den Einstellungen von Motion Watch und werden mitgeschickt.
- **Kamera 0** sitzt auf dem Schwenkkopf, **Kamera 1** ist fest montiert. Die Wärmebildkamera sitzt neben Kamera 0. Was davon gilt, legt `/info` fest.
- Bilder werden als `numpy`-Array übergeben, im **BGR**-Format (OpenCV). Das Wärmebild ist ein `float32`-Array in **°C**.
- Unbekannte Felder werden auf beiden Seiten ignoriert. So lassen sich neue Felder ergänzen, ohne dass sich die Protokollnummer ändert.

## Eigenen Simulator schreiben (Gerüst)

```python
from motionwatch_sim_interface import SimServer, SimInfo, CamInfo

class MeinSimulator(SimServer):
    def render_camera(self, cam, state, t):
        # state.servo.pan_deg / tilt_deg, state.lights.white / ir, state.relays ...
        return bild_bgr                     # numpy H x W x 3, uint8

    def render_thermal(self, state, t):
        return temperaturen_celsius         # numpy h x w, float32 (oder None)

MeinSimulator(SimInfo(cameras=[CamInfo(0, "Kopf"), CamInfo(1, "Fest", on_head=False)])).serve_forever()
```

Sensor-Ereignisse löst du mit `self.add_event("Wohnwagen-Tür", "door", True)` aus.

## Demo ausprobieren

```
python3 motionwatch_sim_interface.py --night
```

- Die Demo zeichnet eine Camping-Landschaft. Kamera 0 schaut je nach Servostellung auf einen anderen Ausschnitt.
- Nachts ist es dunkel. Das weisse Licht beleuchtet einen Kegel, IR macht das Bild grau-hell.
- Ab und zu läuft eine Person vorbei. Im Wärmebild ist sie warm.
- Alle 45 Sekunden geht die Wohnwagentür auf.
- Mit `--day` ist es immer Tag.

## Simulation starten (ab Motion Watch 2.69.0)

0. **Am einfachsten** (ab Motion Watch 2.70.0): in Motion Watch unter *System & Netz → 🧪 Simulator* auf **«Simulator auf dem Pi installieren»** drücken. Danach mit **«Simulator hier starten»** starten. Es gibt dann auch ein Symbol auf dem Desktop und einen Eintrag im Menü. **«Für einen PC herunterladen (ZIP)»** lädt beide Dateien für einen PC herunter.
1. Von Hand: beide Dateien in einen Ordner legen: `motionwatch_sim_interface.py` und `motionwatch_simulator.py`.
2. Simulator starten: `python3 motionwatch_simulator.py`. Es öffnet sich ein Bedienfenster mit:
   - der Vorschau beider Kameras,
   - Tag / Dämmerung / Nacht,
   - Knöpfen für Besuch (Person, Fuchs, Wildschwein, Reh),
   - den Sensoren (Wohnwagentür, PIR Zelt, Gas, Velo),
   - Reglern für Temperatur, Luftdruck und Wind.
   Ohne Fenster geht es mit `--no-window`.
3. In Motion Watch unter *System & Netz → 🧪 Simulator* die Adresse eintragen. Auf demselben Gerät ist das `http://127.0.0.1:8765`, sonst die Adresse des PCs.
4. Die Taste **«🧪 Simulation»** in der Kamerasteuerung drücken (im Pi-Fenster auch **F9**). Dann passiert Folgendes:
   - Kamera 0, Kamera 1 und das Wärmebild kommen aus dem Simulator.
   - Die Sensoren des Simulators erscheinen als Zusatz-Sensoren.
   - Tag/Nacht, Temperatur, Luftdruck und Wind kommen ebenfalls aus der Simulation.
   - Motion Watch schickt dem Simulator laufend Servos, Licht, Relais, Ton und scharf/unscharf.
   - Oben steht gelb **«🧪 SIMULATION»**.
5. Nochmals drücken: Motion Watch nimmt wieder die echten Kameras. Die Simulator-Sensoren werden entfernt.

Lampen funktionieren in der Simulation auch ohne angeschlossene Lampe. Tiere laufen davon, wenn die Sirene ertönt oder nachts das weisse Licht angeht. So lässt sich die Abschreckung testen.

## Simulator 2: was er kann (ab Motion Watch 2.71.0)

Das Bedienfenster hat vier Reiter:

| Reiter | Inhalt |
|---|---|
| **Szene** | Uhrzeit einstellen (Mittag / Abend / Nacht / Morgen), Zeit schneller laufen lassen (bis 120×), Mond. Besuch: Person, Fuchs, Wildschwein, Reh, Katze, Auto mit Scheinwerfern. Eigenes 360°-Foto laden. Richtung von Kamera 1. |
| **Wetter** | klar, Regen, Nebel, Schnee. Wind (die Bäume bewegen sich), Temperatur, Feuchte, Luftdruck. «Sturm zieht auf» senkt den Luftdruck. |
| **Kamera** | Tau auf der Linse und Spinnennetz (zum Testen der Linsen-Prüfung), Kamera abgedeckt (Sabotage-Alarm), Insekten im IR-Licht (typischer Fehlalarm), Bildrauschen, Datum/Zeit im Bild |
| **Sensoren** | Wohnwagentür, Gas, Velo, PIR. Dazu **«Nacht-Test starten»**: ein fertiger Ablauf von etwa 2 Minuten mit Fuchs, Wildschwein, Auto, Person beim Zelt, Tür, Velo und Gas. |

**Echter 3D-Blick:** Die Kameras schauen in eine 360°-Welt. Die Besucher laufen in echten Abständen (Meter) und werden richtig verdeckt.

**Realistischer mit eigenen Bildern:**
- **360°-Foto:** ein Foto im Format 2:1, z. B. von einer 360°-Kamera oder einer Handy-Panorama-App. Du lädst es im Reiter «Szene» oder legst es als `sim_assets/pano.jpg` neben den Simulator. Dann siehst du deinen echten Platz, und die Kamera schwenkt darin.
- **Ausgeschnittene Fotos (PNG mit durchsichtigem Hintergrund):** in die Ordner `sim_assets/person/`, `sim_assets/fox/`, `sim_assets/boar/`, `sim_assets/deer/` und `sim_assets/cat/`. Dann laufen echte Bilder statt gezeichneter Figuren durchs Bild. Gut geeignet zum Testen der KI.

**Kameraeffekte:** automatische Belichtung, Rauschen bei Nacht, abgedunkelte Ecken und Bewegungsunschärfe beim Schwenken.

## Simulator 3: noch echter (ab Motion Watch 2.73.0)

**Automatisch aktuell:** Motion Watch bringt immer die passende Simulator-Version mit.
- Ist der Simulator auf dem Pi installiert, ersetzt Motion Watch ihn beim Start von selbst durch die neue Version. Läuft er gerade, wird er neu gestartet.
- Läuft der Simulator auf einem PC, merkt er beim Verbinden, dass Motion Watch eine neuere Version hat. Er lädt sie dann selbst von Motion Watch (`/sim/simulator.zip`), prüft jede Datei mit einer Prüfsumme und startet neu. Im Fenster steht kurz «Aktualisiert – startet neu …».
- Wer das nicht will, startet den Simulator mit `--no-update`.

**Was neu echter aussieht:**
- Jeder Bildpunkt kennt seine Entfernung. Dadurch werden Licht und Dunst richtig berechnet.
- Das Licht der Lampen nimmt mit der Entfernung ab: Nahes ist hell, Fernes bleibt dunkel. Das gilt für das weisse Licht, das IR-Licht, das Licht aus der offenen Wohnwagentür und die Scheinwerfer.
- Wiese mit Muster in der Perspektive, Berge mit Schneegipfeln, Wolken, die Sonne mit Blendung, Sterne und Mond in der Nacht.
- Dunst und Nebel nehmen mit der Entfernung zu. Bei Nebel sieht man etwa 45 m weit, bei Schnee etwa 250 m, bei Regen etwa 500 m. Neues Wetter: «bewölkt».
- Bessere Figuren: Menschen mit schwingenden Armen und verschiedenen Jacken, Fuchs mit Ohren und buschigem Schwanz, Wildschwein mit Rüssel, Reh mit Hals.
- Kamera: leichte Verzerrung wie bei einem Weitwinkel, farbiges Rauschen in der Nacht, Belichtung wird am unteren Bildteil gemessen.

**Wärmebild mit Physik:**
- Ein klarer Himmel ist sehr kalt (bis etwa 35 °C kälter als die Luft), ein bewölkter fast so warm wie die Luft.
- Der Boden wird an der Sonne warm und kühlt in klaren Nächten ab. Steine sind am Tag heiss und geben die Wärme am Abend ab.
- Wohnwagen-Wände sind am Abend warm. Aus der offenen Tür kommt warme Luft.
- Menschen: das Gesicht ist am wärmsten, die Jacke deutlich kühler. Tiere haben warme Augen.
- Beim Auto sind Motor und Auspuff heiss. Regen und Nebel machen alles gleichmässiger.
- Dazu kommen Rauschen und feine Streifen wie bei einem echten Wärmesensor.

## CPU schonen (ab Motion Watch 2.74.0)

- Der Simulator zeichnet jedes Bild **nur einmal**, auch wenn Motion Watch, ein Browser und das Bedienfenster gleichzeitig zuschauen. Das Fenster zeigt die Bilder, die Motion Watch abholt, statt eigene zu zeichnen.
- Motion Watch holt in der Simulation nur so viele Bilder, wie unter *Simulator → Bilder pro Sekunde* eingestellt sind (Standard 6). Die feste Kamera und das Wärmebild bekommen halb so viele. Das schaltest du mit «CPU schonen während der Simulation» ein und aus.
- Die Kamerabilder sind normal 960 × 540 (Kamera 1: 640 × 360). Wer grössere Bilder will, startet den Simulator mit `--hd`. Das braucht aber deutlich mehr CPU.
- Im Fenster steht, wie viele Bilder pro Sekunde gerade abgeholt werden.
- Ab 2.74.1 läuft die KI-Erkennung in der Simulation mit «CPU schonen» nur halb so oft.
