# Motion Watch – Zusatz-Sensoren anschliessen

Die Sensoren findest du in den Einstellungen unter **📡 Sensoren**. Dort schaltest du sie ein und fügst sie mit «+» hinzu.
Bei jedem Sensor wählst du, wann er Alarm gibt: **nur wenn scharf**, **immer** (empfohlen für Gas/Rauch) oder **kein Alarm**.
Mit «🧪 Test» prüfst du, ob die Push-Nachricht ankommt.

> ⚠ **Strom aus, bevor du etwas an die GPIO-Pins steckst.** Die GPIO-Pins des Pi vertragen nur **3,3 V**. 5 V auf einem GPIO kann den Pi zerstören.

## 1. Bewegungsmelder (PIR) – ca. 3 Fr.

Empfohlen: **AM312** (klein, läuft mit 3,3 V) oder **HC-SR501**.

| Melder | Pi |
|---|---|
| VCC | AM312: 3,3 V (Pin 1) · HC-SR501: 5 V (Pin 2) |
| GND | GND (Pin 6) |
| OUT | ein freier GPIO, z. B. GPIO 5 (Pin 29) |

Der HC-SR501 braucht zwar 5 V, gibt am Ausgang aber nur 3,3 V aus. Das ist für den Pi in Ordnung.

**Stromsparen:** Ist ein Bewegungsmelder eingetragen und unter *Stromsparen* die Option «Mit Bewegungsmelder (PIR) …» an, macht die Kamera bei Ruhe nur noch 1 Bild pro Sekunde. Meldet der PIR etwas, läuft sofort alles mit voller Geschwindigkeit.

## 2. Tür- oder Deckelkontakt (Reed-Kontakt mit Magnet) – ca. 2 Fr.

Die beiden Drähte des Kontakts kommen an **einen freien GPIO** und an **GND**. Motion Watch schaltet den internen Pull-up selbst ein.
Ist der Kontakt geschlossen (Magnet daneben), gilt die Tür als zu. Wird sie geöffnet, gibt es einen Alarm.
Meldet der Kontakt verkehrt herum, setzt du beim Sensor das Häkchen «Umgekehrt».

## 3. Gas- / Rauchmodul (z. B. MQ-2, MQ-7) – ca. 5 Fr.

> ⚠ Ein solches Modul ist **kein Ersatz** für einen geprüften CO- oder Rauchmelder. Es ist nur eine zusätzliche Meldung aufs Handy.

- Die Module brauchen meist 5 V für den Heizdraht. Ihr Ausgang **DO** kann dann aber auch 5 V führen.
  Schliesse DO deshalb **über einen Spannungsteiler** an den GPIO an (z. B. 10 kΩ von DO zum GPIO und 20 kΩ vom GPIO zu GND).
- Bei Gas zieht DO meist auf LOW. Darum ist beim Gas-Sensor «Umgekehrt» schon eingeschaltet.
- Die Empfindlichkeit stellst du mit dem kleinen Drehregler auf dem Modul ein.
- Die Module brauchen nach dem Einschalten einige Minuten zum Aufwärmen.

## 4. Funk-Sensoren 433 MHz (Türkontakte, Bewegungsmelder aus dem Baumarkt)

1. Einen **RTL-SDR-USB-Stick** einstecken (z. B. «RTL-SDR Blog V4», ca. 40 Fr.).
2. Auf dem Pi einmal ausführen: `sudo apt install rtl-433`
3. In Motion Watch «433-MHz-Funksensoren» einschalten.
4. Den Sensor auslösen (Tür auf und zu). Er erscheint unter «Gefundene Funkgeräte». Antippen, und er ist eingetragen.

Nicht jeder billige Sensor wird erkannt. Die Liste der unterstützten Geräte steht bei rtl_433.

## 5. Zigbee-Sensoren (Türkontakt, Bewegung, Rauch, Vibration am Velo)

Das ist aufwendiger. Es braucht einen Zigbee-USB-Stick (z. B. Sonoff ZBDongle), **Mosquitto** (MQTT) und **Zigbee2MQTT** auf dem Pi.
Die Anleitung steht auf zigbee2mqtt.io. Danach:

1. In Motion Watch unter *System & Netz → MQTT* den Broker eintragen (meist `localhost`) und MQTT einschalten.
2. Unter *Sensoren* «Zigbee-Sensoren» einschalten.
3. Den Sensor auslösen. Er erscheint unter «Gefundene Funkgeräte», antippen.

## 6. Bluetooth-Anhänger (RuuviTag) – für Velo, Kühlbox, Grill

1. Auf dem Pi einmal ausführen: `sudo apt install python3-bleak`
2. «Bluetooth-Anhänger» einschalten. Der RuuviTag erscheint unter «Gefundene Funkgeräte», antippen.
3. Wird der Anhänger bewegt, meldet er das über seinen Bewegungszähler. Ist er länger nicht mehr in Reichweite (einstellbar, Standard 5 Minuten), gibt es ebenfalls einen Alarm (wenn scharf).

Hinweis: Ein Bluetooth-Lautsprecher und die Suche nach Anhängern teilen sich den Bluetooth-Chip. Das funktioniert meist, kann aber zu kurzen Aussetzern im Ton führen.

## Was beim Alarm passiert

- Eine Push-Nachricht (dringend) mit dem aktuellen Kamerabild, z. B. «Wohnwagen: geöffnet».
- Eine Aufnahme von einer Minute.
- Die Sirene, wie bei den anderen Alarmen eingestellt. Gas gibt auch im unscharfen Zustand einen Ton.
- Ein Eintrag im Ereignisprotokoll.
