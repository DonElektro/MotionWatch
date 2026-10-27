"""Names shown on Motion Watch's web page in its language (it sends "lang" / Accept-Language with /control).

The maps and places are named in English inside the simulator, the remote controls in German (Daniel's Motion Watch
is German). tr() turns either one into the language asked for; unknown words stay as they are."""

DE = {   # English -> German: maps and places
    "Camp site": "Campingplatz", "Garden behind the house": "Garten hinter dem Haus", "Parking lot": "Parkplatz",
    "Forest clearing": "Waldlichtung", "Lakeside": "Seeufer", "Winter camp": "Winter-Camp",
    "Valley (big, 700 m, skyscrapers)": "Tal (gross, 700 m, Hochhäuser)", "Region (touching places)": "Region (Orte nebeneinander)",
    "Start": "Start", "Start, high on a pole": "Start, hoch auf einem Mast", "Look back": "Zurückschauen",
    "Campsite (start)": "Campingplatz (Start)", "Campsite": "Campingplatz", "Camp on a pole": "Campingplatz, auf einem Mast",
    "Village & church": "Dorf & Kirche", "Downtown": "Stadtzentrum", "Farm": "Bauernhof", "Farmland": "Felder & Bauernhof",
    "Lake shore": "Seeufer", "Lake & beach": "See & Strand", "Car park": "Parkplatz", "Front-back road": "Strasse zur Stadt",
    "City crossing": "Kreuzung in der Stadt", "City (skyscrapers)": "Stadt (Hochhäuser)", "Skyscraper rooftop": "Auf dem Hochhausdach",
    "Forest edge": "Waldrand", "Forest": "Wald", "Hill": "Hügel", "Industrial zone": "Industriegebiet", "Park": "Park",
    "Airfield": "Flugplatz", "Suburbs": "Vorstadt", "Own map (map editor)": "Eigene Karte (Karten-Editor)",
}

EN = {   # German -> English: the remote controls
    "Szene": "Scene", "Wetter": "Weather", "Besuch": "Visitors", "Störungen": "Faults", "Sensoren": "Sensors", "Bild": "Picture",
    "Kamera-Platz": "Camera place", "(eigener Platz)": "(own place)", "Uhrzeit": "Time of day", "Echte Uhrzeit": "Real clock",
    "Pause (alles steht still)": "Pause (everything stands still)", "klar": "clear", "bewölkt": "cloudy", "Regen": "rain",
    "Sturm": "storm", "Nebel": "fog", "Wind": "Wind", "Lufttemperatur": "Air temperature", "Besuch von selbst": "Visitors by themselves",
    "Personen unterwegs": "People around", "Hunde unterwegs": "Dogs around", "Katzen unterwegs": "Cats around",
    "Bären unterwegs": "Bears around", "Rehe unterwegs": "Deer around", "Autos unterwegs": "Cars around",
    "Person schicken": "Send a person", "Hund schicken": "Send a dog", "Katze schicken": "Send a cat", "Bär schicken": "Send a bear",
    "Reh schicken": "Send a deer", "Auto schicken": "Send a car", "Alle wegschicken": "Send everybody away",
    "Kamera eingesteckt": "Camera plugged in", "Linse zugehalten (Sabotage)": "Lens covered (sabotage)",
    "Wärmebild eingesteckt": "Thermal camera plugged in", "Heisser Stein (Wärmebild)": "Hot stone (thermal)",
    "Lagerfeuer (Wärmebild)": "Camp fire (thermal)", "Tür auf": "Door open", "Tür zu": "Door closed", "Gas-Alarm": "Gas alarm",
    "Bildqualität": "Picture quality", "tief": "low", "mittel": "medium", "hoch": "high", "sehr hoch": "very high",
    "Personen & Autos": "People & cars", "Tiere": "Animals", "Jetzt schicken": "Send now",
    "Tag": "day", "Nacht": "night", "Dämmerung": "dusk", "unterwegs": "around", "lädt …": "loading …",
}


def tr(text, lang):
    """text in the language lang: "de" or nothing = German, any other language = English."""
    if lang and lang != "de":
        return EN.get(text, text)
    return DE.get(text, text)
