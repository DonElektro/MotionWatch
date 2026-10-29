#@ MoveEye – Teil 607: Übersetzungen «Eigenes KI-Modell» (Teil 195). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
_HX_MODELL = {
    'AI model': ('KI-Modell', 'Modèle d’IA', 'Modello IA', 'Model IA'),
    'Standard (SSD MobileNet V2)': ('Standard (SSD MobileNet V2)', 'Standard (SSD MobileNet V2)', 'Standard (SSD MobileNet V2)', 'Standard (SSD MobileNet V2)'),
    'Own (MoveEye model)': ('Eigenes (MoveEye-Modell)', 'Propre (modèle MoveEye)', 'Proprio (modello MoveEye)', 'Agen (model MoveEye)'),
    'MoveEye model': ('MoveEye-Modell', 'Modèle MoveEye', 'Modello MoveEye', 'Model MoveEye'),
    'Own model: address of its description (moveeye_model.json)': ('Eigenes Modell: Adresse seiner Beschreibung (moveeye_model.json)', 'Propre modèle : adresse de sa description (moveeye_model.json)', 'Modello proprio: indirizzo della sua descrizione (moveeye_model.json)', 'Agen model: adressa da sia descripziun (moveeye_model.json)'),
    'Download own model': ('Eigenes Modell herunterladen', 'Télécharger le propre modèle', 'Scaricare il modello proprio', 'Telechargiar l’agen model'),
    'Update own model': ('Eigenes Modell aktualisieren', 'Mettre à jour le propre modèle', 'Aggiornare il modello proprio', 'Actualisar l’agen model'),
    'Own model: trained on GitHub from simulator pictures and your labelled alarm pictures (person, animal, vehicle). After the download MoveEye uses it (back to the standard: «AI model», Expert view). If it is missing or fails, the standard model runs.': (
        'Eigenes Modell: auf GitHub trainiert aus Simulator-Bildern und deinen beschrifteten Alarmbildern (Person, Tier, Fahrzeug). Nach dem Herunterladen nimmt MoveEye es (zurück zum Standard: «KI-Modell», Ansicht Experte). Fehlt es oder klappt es nicht, läuft das Standard-Modell.',
        'Propre modèle : entraîné sur GitHub avec des images du simulateur et tes images d’alarme annotées (personne, animal, véhicule). Après le téléchargement, MoveEye l’utilise (retour au standard : «Modèle d’IA», vue Expert). S’il manque ou ne marche pas, le modèle standard tourne.',
        'Modello proprio: addestrato su GitHub con immagini del simulatore e le tue immagini d’allarme etichettate (persona, animale, veicolo). Dopo il download MoveEye lo usa (ritorno allo standard: «Modello IA», vista Esperto). Se manca o non funziona, gira il modello standard.',
        'Agen model: trenà sin GitHub cun maletgs dal simulatur e tes maletgs d’alarm inscripziunads (persuna, animal, vehichel). Suenter il telechargiar al dovra MoveEye (enavos al standard: «Model IA», vista Expert). Sch’el manca u na funcziuna betg, gira il model standard.'),
    'Now running': ('Läuft jetzt', 'Tourne maintenant', 'Gira adesso', 'Gira ussa'),
    'own model not used': ('eigenes Modell nicht benutzt', 'propre modèle pas utilisé', 'modello proprio non usato', 'agen model betg duvrà'),
    'not downloaded yet': ('noch nicht heruntergeladen', 'pas encore téléchargé', 'non ancora scaricato', 'anc betg telechargià'),
    'downloaded': ('heruntergeladen', 'téléchargé', 'scaricato', 'telechargià'),
    'downloading the own model …': ('lädt das eigene Modell …', 'télécharge le propre modèle …', 'scarica il modello proprio …', 'telechargia l’agen model …'),
    'own model ready': ('eigenes Modell bereit', 'propre modèle prêt', 'modello proprio pronto', 'agen model pront'),
    'own model not downloaded yet': ('eigenes Modell noch nicht heruntergeladen', 'propre modèle pas encore téléchargé', 'modello proprio non ancora scaricato', 'agen model anc betg telechargià'),
    'made': ('erstellt', 'créé', 'creato', 'creà'),
    'animal': ('Tier', 'animal', 'animale', 'animal'),
    'https://... address of moveeye_model.json expected': ('eine https://…-Adresse von moveeye_model.json erwartet', 'adresse https://… de moveeye_model.json attendue', 'atteso un indirizzo https://… di moveeye_model.json', 'spetgà ina adressa https://… da moveeye_model.json'),
    'not a MoveEye model description': ('keine Beschreibung eines MoveEye-Modells', 'pas une description de modèle MoveEye', 'non è una descrizione di modello MoveEye', 'nagina descripziun d’in model MoveEye'),
    'classes missing in the model description': ('Klassen fehlen in der Modell-Beschreibung', 'classes manquantes dans la description du modèle', 'classi mancanti nella descrizione del modello', 'classas mancan en la descripziun dal model'),
    'input size of the model not valid': ('Eingangsgrösse des Modells ungültig', 'taille d’entrée du modèle invalide', 'dimensione d’ingresso del modello non valida', 'grondezza d’entrada dal model nunvalaivla'),
    'checksum missing in the model description': ('Prüfsumme fehlt in der Modell-Beschreibung', 'somme de contrôle manquante dans la description du modèle', 'checksum mancante nella descrizione del modello', 'summa da controlla manca en la descripziun dal model'),
    'file name not valid': ('Dateiname ungültig', 'nom de fichier invalide', 'nome del file non valido', 'num da datoteca nunvalaivel'),
    'the model description is not valid': ('die Modell-Beschreibung ist ungültig', 'la description du modèle est invalide', 'la descrizione del modello non è valida', 'la descripziun dal model è nunvalaivla'),
    'checksum wrong - the file is damaged or not the right one': ('Prüfsumme falsch – die Datei ist beschädigt oder nicht die richtige', 'somme de contrôle fausse – le fichier est endommagé ou pas le bon', 'checksum errato – il file è danneggiato o non è quello giusto', 'summa da controlla sbagliada – la datoteca è donnegiada u betg la dretga'),
    'the model has no class «person»': ('das Modell hat keine Klasse «person»', 'le modèle n’a pas de classe «person»', 'il modello non ha la classe «person»', 'il model n’ha nagina classa «person»'),
}
for _k, _v in _HX_MODELL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])
