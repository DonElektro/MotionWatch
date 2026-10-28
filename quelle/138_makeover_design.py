#@ MoveEye – Teil 138: Makeover Design – Simulations-Streifen auf allen Seiten, einheitliche Ereignis-Symbole. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.96.4 (Makeover-Punkte 2 und 6):
#  2  Simulation sichtbar: läuft MoveEye mit dem Simulator, hat jede Seite oben einen orange-schwarz gestreiften Balken
#     «SIMULATION – Alarme sind nicht echt» und einen orangen Rahmen. Der Balken prüft alle 15 s (/api/simbar), ob das noch so ist.
#  6  Ein Satz Ereignis-Symbole für alles (Push-Titel, Tagebuch, Simulator-Tagebuch, Fenster-Protokoll, Simulator):
#     EV_ICON (Python) = window.EVI (Web). Neue Stellen immer von hier nehmen.
# ----------------------------------------------------------------------------
EV_ICON = {
    "person": "🚶", "animal": "🦊", "vehicle": "🚗", "warm": "🔥", "noise": "🔊", "tamper": "🛑", "gone": "📦", "new": "➕",
    "false": "⚪", "prealarm": "👀", "motion": "👀", "info": "ℹ️", "test": "🧪", "light": "💡", "siren": "🚨", "rec": "🎬",
    "photo": "📷", "protect": "🛡", "sim": "🧪", "weather": "☁", "battery": "🔋", "net": "📶",
}
# the kinds of log_event() -> the symbol in the window's log
LOG_ICON = {"person": "🚶", "car": "🚗", "rec": "🎬", "ai": "🦊", "rain": "☔", "wind": "💨", "web": "📶", "sys": "⚙",
            "sched": "🕑", "servo": "↔", "patrol": "↔", "auto": "⚡"}


def ev_icon(kind):
    return EV_ICON.get(kind, "")


SIMBAR_CSS = (".mwsimbar{position:relative;z-index:260;display:flex;align-items:center;justify-content:center;gap:8px;"
              "background:repeating-linear-gradient(135deg,#f59a4a 0 16px,#1a1206 16px 32px);padding:3px 8px}"
              ".mwsimbar span{background:#f59a4a;color:#1a1206;font:700 11px/1.5 system-ui,sans-serif;letter-spacing:.14em;"
              "padding:1px 10px;border-radius:9px;white-space:nowrap}"
              "html.mwsim body{box-shadow:inset 0 0 0 3px #f59a4a}")

SIMBAR_TXT = {"de": "SIMULATION – Alarme sind nicht echt", "fr": "SIMULATION – alarmes non réelles",
              "it": "SIMULAZIONE – allarmi non reali", "rm": "SIMULAZIUN – alarms betg reals", "en": "SIMULATION – alarms are not real"}


def makeover_head():
    """into the <head> of every page (render_page): the symbols, the stripe of the simulation"""
    on = bool(CFG.get("sim_on"))
    js = ("<script>window.EVI=" + json.dumps(EV_ICON, ensure_ascii=False) + ";(function(){const TX=" + json.dumps(SIMBAR_TXT, ensure_ascii=False)
          + ";const DL=" + json.dumps(norm_lang(CFG.get("lang")) or "de") + ";let on=" + ("true" if on else "false") + ";const L=()=>{try{return (typeof LANG!=='undefined'&&LANG)||new URLSearchParams(location.search).get('lang')||DL}catch(e){return DL}};"
          "const paint=()=>{document.documentElement.classList.toggle('mwsim',on);let b=document.querySelector('.mwsimbar');"
          "if(on&&!b&&document.body){b=document.createElement('div');b.className='mwsimbar';b.title='MoveEye';const s=document.createElement('span');b.appendChild(s);document.body.prepend(b);}"
          "if(b){b.hidden=!on;b.firstChild.textContent='🧪 '+(TX[L()]||TX.en);}};"
          "document.addEventListener('DOMContentLoaded',paint);"
          "setInterval(async()=>{try{const r=await (await fetch('/api/simbar')).json();if(r.on!==on){on=r.on;}paint();}catch(e){}},15000);setTimeout(paint,1500);})();</script>")
    return "<style>" + SIMBAR_CSS + "</style>" + js + simhub_head()
