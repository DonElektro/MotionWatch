#@ MoveEye – Teil 635: Übersetzungen zu Blinki (Teil 589, die Figur der Einrichtung und der Rundgänge) und eine Zeile in der Anleitung. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_BLINKI = {
    "Hello, I am Blinki!": ("Hallo, ich bin Blinki!", "Salut, je suis Blinki !", "Ciao, sono Blinki!", "Allegra, jau sun Blinki!"),
    "I am the eye of MoveEye. I show you everything step by step - and when I blink, all is well.":
        ("Ich bin das Auge von MoveEye. Ich zeige dir alles Schritt für Schritt – und wenn ich blinzle, ist alles in Ordnung.",
         "Je suis l’œil de MoveEye. Je te montre tout pas à pas – et quand je cligne de l’œil, tout va bien.",
         "Sono l’occhio di MoveEye. Ti mostro tutto passo dopo passo – e quando sbatto l’occhio, va tutto bene.",
         "Jau sun l’egl da MoveEye. Jau ta mussel tut pass per pass – e cura che jau tschegn, è tut en urden."),
    "Show Blinki": ("Blinki zeigen", "Afficher Blinki", "Mostra Blinki", "Mussar Blinki"),
    "Show Blinki (the little figure that explains the setup and the tours)":
        ("Blinki zeigen (die kleine Figur, die die Einrichtung und die Rundgänge erklärt)",
         "Afficher Blinki (le petit personnage qui explique la configuration et les visites)",
         "Mostra Blinki (la piccola figura che spiega la configurazione e i tour)",
         "Mussar Blinki (la pitschna figura che explitgescha l’installaziun ed ils girs)"),
    "Blinki is the little figure made of the MoveEye logo: it speaks the texts of the setup and the tours.":
        ("Blinki ist die kleine Figur aus dem MoveEye-Logo: Sie spricht die Texte der Einrichtung und der Rundgänge.",
         "Blinki est le petit personnage fait du logo MoveEye : il dit les textes de la configuration et des visites.",
         "Blinki è la piccola figura fatta dal logo MoveEye: dice i testi della configurazione e dei tour.",
         "Blinki è la pitschna figura fatga dal logo da MoveEye: ella di ils texts da l’installaziun e dals girs."),
    "On - switch it off if you prefer plain text boxes.":
        ("Ein – aus, wenn du lieber einfache Textfelder magst.", "Activé – désactive-le si tu préfères de simples cases de texte.",
         "Attivo – disattivalo se preferisci semplici caselle di testo.", "En – deactivar, sche ti prefereschas simplas chaschettas da text."),
}
for _k, _v in _HX_BLINKI.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])

# ---- the manual: one line in the chapter «Einrichtung, Rundgänge und Tipps» (633) ---------------------------------------
_HELP_BLINKI = {
    "de": '<li><b>Blinki</b> 👁: die kleine Figur aus dem Logo (das Auge mit Füssen; die Stimmung zeigt sie kurz in einer kleinen Sprechblase) spricht die Texte der Einrichtung und der Rundgänge – sie blinzelt, schaut umher und hüpft, wenn ein Schritt erledigt ist. Ausschalten: Einstellungen → Einrichtung → «Blinki zeigen» (oder unter Mehr).</li>',
    "en": '<li><b>Blinki</b> 👁: the little figure made of the logo (the eye with feet; it shows its mood briefly in a small speech bubble) speaks the texts of the setup and the tours – it blinks, looks around and hops when a step is done. Switch it off: Settings → Setup → «Show Blinki» (or under More).</li>',
    "fr": '<li><b>Blinki</b> 👁 : le petit personnage fait du logo (l’œil avec des pieds ; il montre brièvement son humeur dans une petite bulle) dit les textes de la configuration et des visites – il cligne de l’œil, regarde autour de lui et saute quand une étape est faite. Désactiver : Réglages → Configuration → «Afficher Blinki» (ou sous Plus).</li>',
    "it": '<li><b>Blinki</b> 👁: la piccola figura fatta dal logo (l’occhio con i piedi; mostra brevemente il suo umore in un piccolo fumetto) dice i testi della configurazione e dei tour – sbatte l’occhio, si guarda intorno e salta quando un passo è fatto. Disattivare: Impostazioni → Configurazione → «Mostra Blinki» (o sotto Altro).</li>',
    "rm": '<li><b>Blinki</b> 👁: la pitschna figura fatga dal logo (l’egl cun peis; ella mussa curt sia luna en ina pitschna bulla) di ils texts da l’installaziun e dals girs – ella tschegna, guarda enturn e siglia, cura ch’in pass è fatg. Deactivar: Parameters → Installaziun → «Mussar Blinki» (u sut Dapli).</li>',
}


def _help_blinki(doc, lang):
    i = doc.find('<section id="guide2"')
    j = doc.find("</ul>", i) if i >= 0 else -1
    if j < 0 or "<b>Blinki</b>" in doc[i:j]:
        return doc
    return doc[:j] + _HELP_BLINKI[lang] + doc[j:]


_hp_enb = HELP_PAGE.find('<div lang="en">')
if _hp_enb > 0:
    HELP_PAGE = _help_blinki(HELP_PAGE[:_hp_enb], "de") + _help_blinki(HELP_PAGE[_hp_enb:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_blinki(HELP_X[_L], _L)
