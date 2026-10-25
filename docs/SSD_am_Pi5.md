# Motion Watch – SSD statt Speicherkarte (Raspberry Pi 5)

Eine Speicherkarte nutzt sich durch das ständige Schreiben von Aufnahmen ab. Bei Stromausfällen kann sie ausserdem beschädigt werden.
Eine SSD hält deutlich länger und ist schneller.

## Variante A – nur die Aufnahmen auf SSD / USB (einfach, ab Version 2.48.0)

1. SSD anschliessen:
   - über einen **USB-SSD-Stick** oder ein USB-Gehäuse mit SSD (am blauen USB-3-Anschluss),
   - oder über ein **M.2-HAT** (z. B. «Raspberry Pi M.2 HAT+») mit einer NVMe-SSD.
2. Raspberry Pi OS hängt das Laufwerk meist von selbst unter `/media/<benutzer>/<name>` ein.
3. In Motion Watch: **Einstellungen → Aufnahme → «Aufnahmen speichern auf»** das Laufwerk wählen.
   Die bisherigen Aufnahmen werden hinüber verschoben.
4. Fehlt das Laufwerk bei einem Start, nimmt Motion Watch vorübergehend wieder die Speicherkarte.
   Die 🩺 Selbstdiagnose zeigt das rot an.

Das System selbst bleibt auf der Speicherkarte. Weil darauf aber fast nur noch gelesen wird, hält sie viel länger.

## Variante B – ganzer Pi von der SSD (am robustesten)

1. M.2-HAT+ mit NVMe-SSD einbauen (Anleitung des HATs befolgen).
2. Auf dem Pi: **Zubehör → SD Card Copier** öffnen. Von der Speicherkarte auf die SSD kopieren.
3. Startreihenfolge auf NVMe stellen: `sudo raspi-config` → *Advanced Options* → *Boot Order* → *NVMe/USB Boot*.
4. Ausschalten, Speicherkarte herausnehmen, einschalten. Der Pi startet von der SSD.

## Einkaufstipp (ca. Preise, Stand 2026)

| Teil | ca. Preis |
|------|-----------|
| Raspberry Pi M.2 HAT+ | 15 Fr. |
| NVMe-SSD 256 GB (2230 oder 2242) | 25–35 Fr. |
| oder: USB-3-SSD-Stick 128–256 GB | 25–40 Fr. |

Hinweis: Die SSD braucht zusätzlich Strom. Mit SSD ist ein Netzteil mit **5 V / 5 A** erst recht wichtig.
