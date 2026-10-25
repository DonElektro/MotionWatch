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

## 7. Sturmwarnung (ab Version 2.55.0)

Unter *Sensoren → ⛈ Sturmwarnung*. Du bekommst eine Push-Nachricht, höchstens alle 3 Stunden pro Grund:

- **Luftdruck:** Der Temperaturfühler **BME280** (I2C) misst auch den Luftdruck. Fällt er schnell (Standard: 3 hPa in 3 Stunden), kommt oft starker Wind oder ein Gewitter. Die Tendenz ist erst nach 1 Stunde Messung verfügbar.
- **Windmesser:** Ein Schalen-Anemometer (z. B. aus einem Wetterstations-Ersatzteilset, ca. 20–30 Fr.) hat einen Reed-Kontakt. Die zwei Drähte kommen an einen freien GPIO und an GND. Bei den üblichen Modellen ergibt 1 Impuls pro Sekunde 2,4 km/h. Das ist voreingestellt und lässt sich anpassen.
- **Prognose (freiwillig):** Böen in den nächsten 12 Stunden von Open-Meteo. Dafür wird der Standort an Open-Meteo geschickt.

## 8. Eigenes GPS-Modul und Diebstahl-Ortung (ab Version 2.56.0)

- Einfachste Variante: ein **USB-GPS-Empfänger** (z. B. «VK-162» oder ein u-blox-Stick, ca. 15–25 Fr.). Einstecken, unter *Sensoren → 🛰 GPS-Modul* einschalten, fertig. Er wird von selbst gefunden.
- Der Empfänger braucht **Sicht zum Himmel**. Im Wohnwagen am besten ans Fenster legen. Beim ersten Mal kann es einige Minuten dauern.
- Läuft auf dem Pi schon **gpsd**, wird es automatisch genutzt.
- Die Position kommt in Fotos und Videos und stellt den Ort für Sonnenauf- und -untergang ein. Ein Handy ist dann nicht mehr nötig.

**Diebstahl-Ortung:** Ist Motion Watch scharf, merkt es sich die Position. Wird das Gerät weiter als die eingestellte Distanz weggetragen (Standard 150 m), gibt es einen Diebstahl-Alarm. Danach kommt **alle 5 Minuten die Position mit Kartenlink**, bis du unscharf schaltest.
Damit das unterwegs funktioniert, braucht der Pi eine Internetverbindung, also den **LTE-Stick**, und Strom, also Powerbank oder UPS. Mit eingerichtetem SMS-Versand kommt der Alarm auch als SMS.

## 9. Solarpanel und Nacht-Prognose (ab Version 2.62.0)

- Ein **INA219-Strommesser** (das kleine blaue Modul, ca. 5 Fr.) kommt in die Plus-Leitung zwischen Panel und Laderegler: Panel-Plus an **VIN+**, **VIN−** zum Laderegler. Dazu VCC an 3,3 V, GND, SDA und SCL an den I2C-Pins des Pi.
- Die Adresse stellst du mit den Lötbrücken A0/A1 auf **0x41** oder **0x44** ein. 0x40 ist oft schon vom Servo-Board belegt, 0x42 vom UPS-HAT.
- Das Modul misst bis etwa 26 V und 3,2 A. Für grössere Panels braucht es einen anderen Shunt-Widerstand; den Wert kannst du einstellen.
- Angezeigt werden Watt, Volt, Ampere, der Ertrag von heute und die Spitze des Tages.

**Nacht-Prognose:** Mit einem Akku-Wert (UPS-HAT oder Powerbank-Kapazität unter *Akku*) rechnet Motion Watch aus, ob der Akku beim aktuellen Verbrauch bis Sonnenaufgang reicht. Am Abend kommt eine Push-Nachricht, wenn es knapp wird.

## Was beim Alarm passiert

- Eine Push-Nachricht (dringend) mit dem aktuellen Kamerabild, z. B. «Wohnwagen: geöffnet».
- Eine Aufnahme von einer Minute.
- Die Sirene, wie bei den anderen Alarmen eingestellt. Gas gibt auch im unscharfen Zustand einen Ton.
- Ein Eintrag im Ereignisprotokoll.
