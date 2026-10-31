#@ MoveEye – Teil 639h: «MoveEye Sim · Basis» (der alte Python-Simulator, SIM_ZIP_B64 in 360) nur noch mit dem Schalter «Basis-Simulator anzeigen» (Simulator, Experte, Standard aus; 2.98.55). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Ohne den Schalter: kein Download-Link, keine Knöpfe «Simulator auf dem Pi installieren / hier starten» (Web 470, Fenster 570).
# Der Code bleibt; /sim/simulator.zip bleibt erreichbar (bestehende Basis-Simulatoren holen dort ihre Updates); eine
# bestehende Installation auf dem Pi bleibt unberührt (nichts wird gelöscht), ein laufender lässt sich weiter stoppen.
_HX_BASIS = {
    'Show the basic simulator (MoveEye Sim · Basis, the old Python simulator)':
        ('Basis-Simulator anzeigen (MoveEye Sim · Basis, der alte Python-Simulator)',
         'Afficher le simulateur de base (MoveEye Sim · Basis, l’ancien simulateur Python)',
         'Mostra il simulatore di base (MoveEye Sim · Basis, il vecchio simulatore Python)',
         'Mussar il simulatur da basa (MoveEye Sim · Basis, il vegl simulatur Python)'),
    'Shows the download of the old Python simulator and the buttons to install and start it on the Pi (page Simulator → Programs and downloads, window → Simulator). An installation on the Pi stays as it is, also when this is off.':
        ('Zeigt den Download des alten Python-Simulators und die Knöpfe zum Installieren und Starten auf dem Pi (Seite Simulator → Programme und Downloads, Fenster → Simulator). Eine Installation auf dem Pi bleibt, wie sie ist, auch wenn dies aus ist.',
         'Affiche le téléchargement de l’ancien simulateur Python et les boutons pour l’installer et le démarrer sur le Pi (page Simulateur → Programmes et téléchargements, fenêtre → Simulateur). Une installation sur le Pi reste telle quelle, même si c’est désactivé.',
         'Mostra il download del vecchio simulatore Python e i pulsanti per installarlo e avviarlo sul Pi (pagina Simulatore → Programmi e download, finestra → Simulatore). Un’installazione sul Pi resta com’è, anche se questo è spento.',
         'Mussa la telechargiada dal vegl simulatur Python ed ils buttuns per l’installar e aviar sin il Pi (pagina Simulatur → Programs e telechargiadas, fanestra → Simulatur). Ina installaziun sin il Pi resta sco ch’ella è, er sche quai è stizzà.'),
    'Switch on «Show the basic simulator» first (Simulator, Expert)':
        ('Zuerst «Basis-Simulator anzeigen» einschalten (Simulator, Experte)',
         'Activez d’abord «Afficher le simulateur de base» (Simulateur, Expert)',
         'Prima attiva «Mostra il simulatore di base» (Simulatore, Esperto)',
         'Avant enconuschent «Mussar il simulatur da basa» (Simulatur, Expert)'),
    'Off: MoveEye Sim · 3D is the simulator.': ('Aus: MoveEye Sim · 3D ist der Simulator.', 'Désactivé : MoveEye Sim · 3D est le simulateur.',
                                                'Spento: MoveEye Sim · 3D è il simulatore.', 'Stizzà: MoveEye Sim · 3D è il simulatur.'),
}
for _k, _v in _HX_BASIS.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

SET_HELP["sim_basis_show"] = ("Shows the download of the old Python simulator and the buttons to install and start it on the Pi (page Simulator → "
                              "Programs and downloads, window → Simulator). An installation on the Pi stays as it is, also when this is off.",
                              "Off: MoveEye Sim · 3D is the simulator.")


_sim_status_558 = sim_status


# wraps: sim_status
def sim_status():                                         # + 639h: show «MoveEye Sim · Basis» (download, install / start on the Pi)?
    r = _sim_status_558()
    r["basis_show"] = bool(CFG.get("sim_basis_show"))
    return r
