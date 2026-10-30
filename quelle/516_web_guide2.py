#@ MoveEye – Teil 516: Web: Guide 2 – Einrichtung schnell / ausgiebig, Rundgänge mit Sprechblasen, Einfach/Experte pro Seite, «Tipps & Tricks», «?» bei Einstellungen, Tipp des Tages, Werkseinstellungen (Skript /g2/ui.js für alle Seiten). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# The logic is in 586 (state of the guide, help texts, tip of the day, factory reset), the window in 584. Every page loads
# /g2/ui.js?lang=xx once (the loader is at the end of guide_js, 515). The texts come translated with the script.
# ----------------------------------------------------------------------------
def g2_page_key(active):
    a = str(active or "")
    return "history" if a in ("rec", "history") else a


# tours: page -> [(CSS selector (first visible one), English title, English text)]; missing / hidden controls are left out
G2_TOURS = {
    "live": [("#vcard, #video", "The live picture", "What the camera sees right now. Double-tap = only the picture, big."),
             ("#lv-joy, #stick", "Turn the head", "With the joystick you turn the camera head. Tapping into the picture makes it look there."),
             ("#qsw", "Quick switches", "Recording, photo, follow, patrol, light, infrared and thermal picture - one tap each."),
             ("#b-arm", "The state", "Off · Watchful · Full: tap here to switch the protection."),
             ("nav.nav", "The six tabs", "Live · Protection · History · Settings · Simulator · More. The «?» at the top shows this tour again.")],
    "protect": [("#protect-box", "Protection level", "Off, Watchful (only messages) or Full (light, siren). The traffic light says what is still missing."),
                ("#pr-night", "Guard tonight", "One tap: everything for the night - and off again in the morning."),
                ("#pr-wt", "Walk test", "Walk past the camera: MoveEye beeps at every detection and shows how far it sees you."),
                ("#mode-box", "Mode", "Camping, home, wildlife … the mode decides what MoveEye does by itself."),
                ("nav.subnav a[href='/zones']", "Zones", "Draw areas into the picture: ignore the road, privacy, sleeping place.")],
    "history": [("#statcard", "Overview", "How many alarms, when and where - for the last days."),
                ("#f-kind, #f-q", "Filter", "Only persons, only animals, a day or a word - find a recording quickly."),
                ("#btn-fav", "Favourites", "⭐ keeps a recording for ever; the others are deleted when the memory is full."),
                ("nav.subnav", "More history", "Night timeline, animal diary, message list and log.")],
    "settings": [("#srch", "Search", "Type a word - every setting is found, sorted by topic."),
                 ("#simplebar", "Simple or Expert", "«Simple» shows only the important settings - for this page. «Expert» shows all."),
                 ("#settings", "Topics", "Open a topic to change it. Changes are saved at once."),
                 ("#settings .g2-q", "The «?»", "Next to a setting: what it does and what we recommend."),
                 ("nav.subnav a[href='/cams']", "Cameras", "Choose the camera, add a second one, check the thermal picture.")],
    "sim": [("#c-conn", "Connection", "The 3D simulator runs on a PC. Here MoveEye connects to it."),
            ("#c-status", "State", "Is the simulator connected, which version, which scene."),
            ("#c-prev", "Preview and control", "The picture of the simulation - move the camera, walk a person, change the weather."),
            ("#c-hub, #simhub", "Simulator centre", "Tests, «Improve detection», training night - MoveEye learns without the real place."),
            ("#c-game", "Team against MoveEye", "A game for guests: who gets past MoveEye unseen?")],
    "more": [("#games", "Games", "«Open all games»: game corner, game collection and the simulator game with one QR code."),
             ("a.mi[href='/help']", "Manual", "Everything explained, with a search - and a quick guide to print."),
             ("#g2-more", "Setup and help", "Start or continue the setup, show the tours again, tip of the day."),
             ("#g2-sys", "System", "Reset to factory settings - with a copy of the old settings first."),
             ("a.mi[href='/tools']", "Tools", "Network test, servo test, diagnosis and more.")],
}
# «Tipps & Tricks» per page: (s = Simple and Expert, e = only Expert, English text)
G2_TT = {
    "live": [("s", "Double-tap the picture = only the picture, big. Double-tap again = back."),
             ("s", "Tap into the picture: the head looks there (with a pan / tilt head)."),
             ("e", "«◫ View»: layout, picture size, favourite buttons and cards - for this device or for all."),
             ("e", "⇱ or F11: full screen, e.g. for a tablet on the table.")],
    "protect": [("s", "«Guard tonight» switches everything on for the night and off again in the morning."),
                ("s", "Before the first night: a walk test shows how far MoveEye recognises you."),
                ("e", "A PIN for disarming: three wrong PINs give a theft alarm with a picture."),
                ("e", "Draw the road as «ignore» under Zones - that saves many false alarms.")],
    "history": [("s", "⭐ keeps a recording for ever - old ones are deleted when the memory is full."),
                ("s", "Mark a false alarm: MoveEye learns from it (with the simulator)."),
                ("e", "The night timeline shows the whole night at one glance."),
                ("e", "The log explains why MoveEye did something.")],
    "settings": [("s", "The «?» next to a setting explains it and says what we recommend."),
                 ("s", "The search at the top finds every setting quickly."),
                 ("e", "«Expert» is only for this page - the other pages stay as they are."),
                 ("e", "Keep a copy of your settings: System → 💾 Settings file → ⬇ Save settings.")],
    "sim": [("s", "Test without the real place: day, night, weather, animals and people in the 3D simulator."),
            ("s", "«Improve detection» tries changes and keeps only what is clearly better."),
            ("e", "Team against MoveEye: the guests try to get past MoveEye unseen.")],
    "more": [("s", "Print the quick guide (1 page) with the QR codes and keep it in the camper."),
             ("s", "See the tours and tips again: «Reset all tours» below."),
             ("e", "Factory settings: Wi-Fi, remote access, the push channel and the own AI model stay.")],
    "zones": [("s", "Draw the road as «ignore»: passing cars then give no alarm."),
              ("s", "Privacy zones are black and never recorded."),
              ("e", "A line gives an alarm only when somebody crosses it.")],
    "cams": [("s", "Picture upside down? Settings → Camera → turn the picture."),
             ("e", "Add a second camera (USB or network) as an overview.")],
    "place": [("s", "Set up the place every time you put MoveEye somewhere new: it looks round and suggests zones."),
              ("e", "The waypoints of the patrol come straight from the look round.")],
    "tools": [("s", "The network test shows whether the Wi-Fi is good enough for the live picture."),
              ("e", "The diagnosis package helps the developer when something does not work.")],
}
G2_MODE_PAGES = ("history", "zones", "cams", "place", "tools")      # a small Simple / Expert switch on top (settings / protect have theirs)
G2_UI = [
    "Tour of this page", "Next", "Skip", "Done", "Back", "Later", "Continue later", "Tips & tricks", "Simple", "Expert", "View of this page:",
    "Recommended", "Close", "Tip of the day", "Show me", "Not now", "Tip of the day off", "Step", "of",
    "Quick (about 5 min.) or thorough?", "Quick", "about 5 minutes", "In depth", "about 20 to 30 minutes",
    "Basics, push messages to the phone, camera test and place, protection and walk test.",
    "Everything of «Quick» plus zones, night time, light and siren, head, AI model, thermal camera, battery, simulator - each step can be skipped.",
    "Welcome to MoveEye", "Every step can be skipped. You can stop at any time and continue later (More → Setup).",
    "Language", "Name of this device (optional)", "e.g. camper, garden", "Time and place", "Time on MoveEye", "on this device",
    "🕒 Take the time of this device", "📍 Location of this device", "Latitude", "Longitude", "Location: only on a secure page (https) - or type it.",
    "Password for this page", "Without a password everybody in the same network (and with the link) can watch and switch everything.",
    "Password (6-64 characters)", "Repeat password", "Continue without a password (not recommended)", "The passwords are not the same",
    "A password is set already. Enter a new one only to change it.", "The password was given on the command line (--web-password).",
    "The page now asks once for the new password (user name: anything) and then continues here.",
    "1. Install the free app «ntfy» (App Store / Play Store).",
    "2. In the app: + → enter the topic below (and the server, if it is not the default one) - or open this code with the phone camera.",
    "Server", "Topic (like a secret channel name)", "📨 Send test message", "Sent - did it arrive on the phone?", "The push channel is set up already:",
    "Is the picture right? Upright, sharp, the place in view?", "No picture yet.", "📷 Choose the camera", "🎮 Use the 3D simulator as camera",
    "Address of the simulator", "Connecting …", "📐 Set up the place", "MoveEye looks round once and suggests zones, paths and the things to guard (a few minutes). Then come back here.",
    "frames/s", "Who should see «Simple» - and what is MoveEye for?", "Default of every page (each page can switch by itself).",
    "What is MoveEye for?", "Camping: tent, caravan", "House and garden", "Watching animals", "Holiday house, alpine hut", "In the room: wake-up alarm", "everything (not chosen)",
    "Draw areas into the picture: ignore the road, privacy, the sleeping place for the wake-up alarm, a line.", "✏ Draw the zones",
    "State of the protection", "Everything ready.", "Still missing:", "Switch on now?", "Leave it off", "Watchful", "Full", "switches on at once (with the countdown)",
    "🚶 Start walk test", "■ Stop", "Walk past the camera like a visitor - MoveEye beeps at every detection. 3 minutes, no alarms meanwhile.", "left", "recognised",
    "Night report in the morning", "End of the night time", "o'clock", "🕘 Schedules", "Schedules switch features by themselves, e.g. the protection every night.",
    "💡 Light 3 s", "🌙 Infrared 3 s", "🔊 Test sound", "🚨 Siren 2 s", "Loud! Warn the neighbours first.",
    "◎ Centre", "◀ ▶ Turn a little", "Direction of turning wrong? Swap it:", "Invert pan direction", "Invert tilt direction", "🛠 Servo test (tools)",
    "AI detection", "The AI says «person», «animal», «car». It runs on the Pi or on a helper PC.", "Own AI model",
    "Thermal picture over the live picture", "Alarm from the thermal camera", "Battery", "Battery saving automatic", "charge",
    "no battery", "Powerbank capacity", "Fast updates (development)", "🔋 Charged full now",
    "The 3D simulator on the PC tests MoveEye without the real place. Optional.", "🔌 Connect", "connected", "not connected",
    "Tours and tips", "Tour of a page on its first visit", "Tip of the day", "Explanations the first time something is opened",
    "off", "basic", "normal", "all", "Done!", "Done", "skipped", "skipped automatically", "Open MoveEye on other devices with these codes. On the phone: Share → «Add to Home Screen» - then it starts like an app.",
    "Home network", "Own Wi-Fi of the device", "On the road (Tailscale)", "🖨 Quick start card with QR codes", "Let's go", "➕ Set up more (thorough)",
    "↩ Back to the setup", "Setup", "Setup finished.", "Setup paused - step", "never done", "🧭 Start the setup", "🧭 Continue the setup", "🧭 Setup again",
    "↺ Reset all tours", "All tours will show again.", "System", "⚠ Reset to factory settings …", "Copies of the old settings", "⬇",
    "Reset to factory settings", "Back to the factory settings:", "all settings, zones, schedules, waypoints, password, users, PIN, the place",
    "These stay:", "Wi-Fi and own Wi-Fi, remote access (Tailscale), the push channel (ntfy), the update settings, the own AI model and what it learned",
    "These are deleted:", "all recordings and photos, the animal diary, the log", "First a copy of the old settings is saved - you can download it below.",
    "Your password", "Your PIN", "Type {w} to confirm", "Reset now", "Reset done.", "Copy of the old settings:", "Start the setup",
    "error", "Setup assistant", "Help", "on", "optional", "ok", "Saved",
]


def g2_js(L):
    T = lambda s: tr(s, L)
    tours = {p: [{"s": s, "t": T(a), "x": T(b)} for s, a, b in v] for p, v in G2_TOURS.items()}
    tt = {p: [{"l": lv, "x": T(x)} for lv, x in v] for p, v in G2_TT.items()}
    tx = {s: T(s) for s in G2_UI}
    data = {"lang": L, "tx": tx, "tours": tours, "tt": tt, "help": g2_help(L), "modePages": list(G2_MODE_PAGES), "ver": APP_VERSION}
    return "window.MW_G2D=" + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + ";\n" + G2_JS


G2_LOADER_JS = r"""
(function () {                                     // 586: guide 2 (tours, tips, setup, factory reset) - one script for every page
  if (window._g2l) return; window._g2l = true;
  let L = "de"; try { L = (typeof LANG !== "undefined" && LANG) || localStorage.getItem("mw-lang") || "de"; } catch (e) {}
  const s = document.createElement("script"); s.src = "/g2/ui.js?v=" + encodeURIComponent((window.MW_GUIDE || {}).ver || "") + "&lang=" + encodeURIComponent(L); s.defer = true;
  (document.head || document.documentElement).appendChild(s);
})();
"""

G2_JS = r"""
(function g2() {
  if (window._g2) return; window._g2 = true;
  const D = window.MW_G2D || {tx: {}, tours: {}, tt: {}, help: {}}, B = window.MW_G2B || {};
  const T = k => D.tx[k] || k;
  const PG = B.page || "";
  const LG = () => { try { return (typeof LANG !== "undefined" && LANG) || D.lang || "de"; } catch (e) { return D.lang || "de"; } };
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const BT = (text, cls, fn) => { const b = E("button", cls || "", text); b.type = "button"; if (fn) b.onclick = fn; return b; };
  const J = async (u) => { try { return await (await fetch(u, {cache: "no-store"})).json(); } catch (e) { return null; } };
  const P = async (u, b) => { try { const r = await fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: LG()}, b || {}))});
    let j = {}; try { j = await r.json(); } catch (e) { j = {ok: false, error: "HTTP " + r.status}; } if (r.status >= 400 && j.ok !== false) j.ok = false; return j; } catch (e) { return {ok: false, error: String(e)}; } };
  const LSget = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } };
  const LSset = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const css = E("style");
  css.textContent = `
.g2-q{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;min-height:0!important;min-width:0;padding:0!important;margin:0 0 0 6px;border-radius:50%!important;border:1px solid var(--line,#2a3646)!important;background:transparent!important;color:var(--mut,#9fb0c3)!important;font-size:12px!important;font-weight:700;line-height:1;cursor:pointer;vertical-align:middle;flex:none;box-shadow:none!important}
.g2-q:hover,.g2-q:focus-visible{color:var(--acc,#3d8bff)!important;border-color:var(--acc,#3d8bff)!important}
#g2-pop{position:fixed;z-index:265;width:min(340px,calc(100vw - 24px));background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-left:4px solid var(--acc,#3d8bff);border-radius:12px;padding:10px 12px;box-shadow:0 10px 30px rgba(0,0,0,.45);font-size:14px;line-height:1.4}
#g2-pop b{display:block;margin-bottom:4px;padding-right:22px}#g2-pop .r{margin-top:6px;color:var(--grn,#3ecf8e)}#g2-pop .d{margin-top:4px;color:var(--mut,#9fb0c3);font-size:12px}
#g2-pop .x{position:absolute;top:4px;right:6px;background:none!important;border:0!important;color:var(--mut,#9fb0c3);min-height:0;padding:2px 6px;font-size:16px}
#g2-ov{position:fixed;inset:0;z-index:280;background:transparent}
#g2-spot{position:fixed;z-index:281;border-radius:12px;box-shadow:0 0 0 200vmax rgba(0,0,0,.64);outline:3px solid var(--acc,#3d8bff);outline-offset:2px;transition:left .25s ease,top .25s ease,width .25s ease,height .25s ease;pointer-events:none}
#g2-bub{position:fixed;z-index:282;width:min(340px,calc(100vw - 24px));background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-radius:14px;padding:12px 14px;box-shadow:0 12px 40px rgba(0,0,0,.55);box-sizing:border-box}
#g2-bub b{display:block;font-size:16px;margin-bottom:4px}#g2-bub p{margin:0 0 12px;font-size:14px;line-height:1.45;color:var(--mut,#9fb0c3)}
#g2-bub .gb{display:flex;gap:8px;align-items:center}#g2-bub .n{margin-right:auto;font-size:12px;color:var(--mut,#9fb0c3)}
#g2-bub .dots{display:flex;gap:4px;margin-right:auto}#g2-bub .dots i{width:7px;height:7px;border-radius:50%;background:var(--line,#2a3646)}#g2-bub .dots i.on{background:var(--acc,#3d8bff)}
#g2-help{font-weight:800}
details.g2-tt{margin:0 0 12px;border:1px solid var(--line,#1f2b3a);border-radius:14px;background:var(--panel,#111822);padding:0 14px}
details.g2-tt>summary{cursor:pointer;padding:11px 0;font-weight:700;list-style:none}details.g2-tt>summary::-webkit-details-marker{display:none}
details.g2-tt>summary::after{content:"▸";float:right;color:var(--mut,#9fb0c3)}details.g2-tt[open]>summary::after{content:"▾"}
details.g2-tt ul{margin:0 0 12px;padding-left:20px}details.g2-tt li{margin:4px 0;line-height:1.4;font-size:14px}details.g2-tt li.e::marker{content:"◆ ";color:var(--acc,#3d8bff)}
.g2-modebar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 10px;font-size:13px;color:var(--mut,#9fb0c3)}
.g2-seg{display:inline-flex;border:1px solid var(--line,#2a3646);border-radius:999px;overflow:hidden}
.g2-seg button{border:0!important;border-radius:0!important;min-height:0!important;padding:5px 12px!important;background:transparent!important;color:var(--txt,#e8eef5)!important;font-size:13px;box-shadow:none!important}
.g2-seg button.on{background:var(--acc,#3d8bff)!important;color:#fff!important}
.g2m{position:fixed;inset:0;z-index:270;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;padding:10px}
.g2m .wc{background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-radius:16px;max-width:560px;width:100%;max-height:94vh;max-height:94dvh;display:flex;flex-direction:column;overflow:hidden;box-sizing:border-box}
.g2m .wh{padding:12px 16px 6px}.g2m .wb{padding:4px 16px 12px;overflow-y:auto;flex:1}.g2m .wf{display:flex;gap:8px;padding:10px 16px 14px;border-top:1px solid var(--line,#1f2b3a);flex-wrap:wrap;justify-content:flex-end}
.g2m .wf .sp{margin-right:auto}
.g2m .pb{height:6px;border-radius:3px;background:var(--line,#1f2b3a);overflow:hidden;margin:6px 0 2px}.g2m .pb i{display:block;height:100%;background:var(--acc,#3d8bff);transition:width .3s}
.g2m .st{font-size:12px;color:var(--mut,#9fb0c3);display:flex;justify-content:space-between;gap:8px}
.g2m .later{background:none!important;border:0!important;color:var(--mut,#9fb0c3)!important;font-size:13px;padding:2px 4px!important;min-height:0!important;box-shadow:none!important}
.g2m h2{font-size:19px;margin:8px 0 6px}.g2m p{margin:6px 0;line-height:1.45}.g2m label.l{display:block;margin:12px 0 4px;font-weight:600}
.g2m input[type=text],.g2m input[type=password],.g2m input[type=number],.g2m select{width:100%;box-sizing:border-box;padding:9px 11px;border-radius:10px}
.g2m .two{display:grid;grid-template-columns:1fr 1fr;gap:10px}.g2m .row2{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.g2m .big{display:block;width:100%;text-align:left;padding:14px!important;margin:0 0 10px;border-radius:14px;height:auto}.g2m .big b{font-size:17px;display:block}.g2m .big small{display:block;opacity:.85;margin-top:4px;line-height:1.35;font-size:13px}
.g2m .qr{width:170px;height:170px;margin:8px auto;background:#fff;border-radius:10px;overflow:hidden}.g2m .qr svg{width:100%;height:100%;display:block}
.g2m .qrs{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;text-align:center}.g2m .qrs .mut{word-break:break-all;font-size:12px}
.g2m .cam{width:100%;aspect-ratio:16/9;object-fit:contain;background:#000;border-radius:10px;display:block}
.g2m .usegrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0}.g2m .useopt{display:flex;flex-direction:column;align-items:center;gap:3px;padding:10px 6px!important;font-size:13px;text-align:center;height:auto}
.g2m .on2{border-color:var(--acc,#3d8bff)!important;box-shadow:0 0 0 2px var(--acc,#3d8bff) inset!important}
.g2m .del{color:var(--red,#ff5d5d)}.g2m .ok{color:var(--grn,#3ecf8e)}.g2m .warn{color:var(--yel,#f0c040)}.g2m .err{color:var(--red,#ff5d5d);min-height:1.2em;font-size:13px}
.g2m .mut{color:var(--mut,#9fb0c3)}.g2m ul.sum{padding-left:18px;margin:6px 0}.g2m ul.sum li{margin:3px 0}
.g2m .tg{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:8px 0;font-weight:400}
#g2-pill{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(14px + env(safe-area-inset-bottom,0px));z-index:240;box-shadow:0 8px 24px rgba(0,0,0,.45);border-radius:999px!important;white-space:nowrap;max-width:calc(100vw - 24px);overflow:hidden;text-overflow:ellipsis}
#g2-tip{position:fixed;left:50%;bottom:calc(16px + env(safe-area-inset-bottom,0px));transform:translate(-50%,20px);opacity:0;transition:transform .35s ease,opacity .35s ease;z-index:249;width:min(440px,calc(100vw - 24px));background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-left:4px solid var(--yel,#f0a540);border-radius:14px;padding:12px 14px;box-shadow:0 12px 40px rgba(0,0,0,.45);box-sizing:border-box}
#g2-tip.on{transform:translate(-50%,0);opacity:1}#g2-tip b{display:block;font-size:15px;margin-bottom:4px}#g2-tip p{margin:0 0 10px;font-size:14px;line-height:1.4;color:var(--mut,#9fb0c3)}#g2-tip .gb{display:flex;gap:8px;flex-wrap:wrap}
#g2-tip small{display:block;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--yel,#f0a540);margin-bottom:2px;font-weight:700}
.g2-card{border:1px solid var(--line,#1f2b3a);border-radius:14px;background:var(--panel,#111822);padding:12px 14px;margin:0 0 10px}
.g2-card h3{margin:0 0 6px;font-size:16px}.g2-card .btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.g2-card .tg{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:8px 0}
.g2-card ul{margin:6px 0;padding-left:18px}.g2-card li{font-size:13px;margin:3px 0}
@media (prefers-reduced-motion:reduce){#g2-spot,#g2-tip,.g2m .pb i{transition:none}}`;
  document.head.appendChild(css);
  try {                                              // German of the main page: its own dictionary (I18N.de) - add the new texts
    if (LG() === "de" && window.I18N && I18N.de) { for (const k in D.tx) if (!(k in I18N.de)) I18N.de[k] = D.tx[k]; }
    document.querySelectorAll("[data-i18n]").forEach(e => { const k = e.dataset.i18n; if (D.tx[k] && D.tx[k] !== k && e.textContent.trim() === k) e.textContent = D.tx[k]; });
  } catch (e) {}
  const sw = (on, fn) => { const c = E("input"); c.type = "checkbox"; c.className = "sw"; c.checked = !!on; c.onchange = () => fn(c.checked); return c; };

  // ---------------------------------------------------------------- Simple / Expert per page
  const modes = () => { try { const m = JSON.parse(LSget("mw-page-mode", "{}")); return m && typeof m === "object" ? m : {}; } catch (e) { return {}; } };
  const simpleHere = () => { const v = modes()[PG]; return v === "simple" ? true : v === "expert" ? false : !!B.simple; };
  async function setSimple(on) { await P("/api/ui_simple", {on: on, page: PG}); const m = modes(); m[PG] = on ? "simple" : "expert";
    if (on === !!B.simple) delete m[PG]; LSset("mw-page-mode", JSON.stringify(m)); paintTT(); paintMode(); }
  function modeBar() {
    const w = E("div", "g2-modebar"); w.id = "g2-modebar"; w.appendChild(E("span", "", T("View of this page:")));
    const s = E("span", "g2-seg"), a = BT(T("Simple"), simpleHere() ? "on" : "", () => setSimple(true)), b = BT(T("Expert"), simpleHere() ? "" : "on", () => setSimple(false));
    s.append(a, b); w.appendChild(s); return w;
  }
  function paintMode() { const o = document.getElementById("g2-modebar"); if (o) o.replaceWith(modeBar()); document.body.classList.toggle("g2-simple", simpleHere()); }

  // ---------------------------------------------------------------- Tipps & Tricks
  function paintTT() {
    const list = D.tt[PG]; if (!list || !list.length) return;
    let d = document.getElementById("g2-tt");
    const simple = PG === "live" ? !!B.simple : simpleHere();
    const items = list.filter(x => x.l === "s" || !simple);
    if (!d) {
      d = E("details", "g2-tt"); d.id = "g2-tt";
      if (LSget("mw-g2-tt", "") === "open") d.open = true;
      d.addEventListener("toggle", () => LSset("mw-g2-tt", d.open ? "open" : "closed"));
      place(d);
    }
    d.textContent = "";
    d.appendChild(E("summary", "", "💡 " + T("Tips & tricks") + " (" + items.length + ")"));
    const ul = E("ul"); items.forEach(x => ul.appendChild(E("li", x.l === "e" ? "e" : "", x.x))); d.appendChild(ul);
  }
  function place(node) {
    const main = document.querySelector("main"); if (!main) return;
    if (PG === "live") { main.appendChild(node); return; }
    const sb = document.getElementById("simplebar");
    if (sb && sb.parentElement) { sb.parentElement.insertBefore(node, sb.nextSibling); return; }
    const mb = document.getElementById("g2-modebar");
    if (mb) { mb.parentElement.insertBefore(node, mb.nextSibling); return; }
    main.insertBefore(node, main.firstChild);
  }

  // ---------------------------------------------------------------- «?» next to the settings
  let pop = null;
  function closePop() { if (pop) { pop.remove(); pop = null; } }
  function showHelp(btn, key, label) {
    closePop(); const h = D.help[key]; if (!h) return;
    pop = E("div"); pop.id = "g2-pop"; pop.setAttribute("role", "dialog");
    pop.append(BT("✕", "x", closePop), E("b", "", label || key), E("div", "", h.x));
    if (h.r) pop.appendChild(E("div", "r", "👍 " + T("Recommended") + ": " + h.r));
    if (h.d) pop.appendChild(E("div", "d", h.d));
    document.body.appendChild(pop);
    const r = btn.getBoundingClientRect(), W = pop.offsetWidth, H = pop.offsetHeight;
    let x = Math.min(window.innerWidth - W - 12, Math.max(12, r.left - 20)), y = r.bottom + 8;
    if (y + H > window.innerHeight - 8) y = Math.max(8, r.top - H - 8);
    pop.style.left = x + "px"; pop.style.top = y + "px";
  }
  document.addEventListener("click", ev => { if (pop && !pop.contains(ev.target) && !ev.target.classList.contains("g2-q")) closePop(); }, true);
  document.addEventListener("keydown", ev => { if (ev.key === "Escape") closePop(); });
  function decorate() {
    const root = document.getElementById("settings"); if (!root) return;
    root.querySelectorAll("[data-key]").forEach(row => {
      if (row.tagName === "SELECT" || row.dataset.g2q) return; const key = row.dataset.key; if (!D.help[key]) return;
      const lab = row.classList.contains("tg") ? row.querySelector(":scope > span") : row.querySelector(":scope > .row > span, :scope > span");
      if (!lab) return; row.dataset.g2q = "1";
      const b = BT("?", "g2-q"); b.setAttribute("aria-label", T("Help") + ": " + lab.textContent);
      const ltxt = lab.textContent.trim();
      b.addEventListener("click", ev => { ev.preventDefault(); ev.stopPropagation(); showHelp(b, key, ltxt); });
      lab.appendChild(b);
    });
  }

  // ---------------------------------------------------------------- tours (coach marks)
  const toursSeen = () => { try { const v = JSON.parse(LSget("mw-tours-seen", "[]")); return Array.isArray(v) ? v : []; } catch (e) { return []; } };
  const markSeen = p => { const s = toursSeen(); if (!s.includes(p)) { s.push(p); LSset("mw-tours-seen", JSON.stringify(s)); } };
  const visible = el => { if (!el) return false; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 4 && r.height > 4 && cs.visibility !== "hidden" && cs.display !== "none" && !el.closest("[hidden]"); };
  const findEl = sel => { for (const s of sel.split(",")) { const all = document.querySelectorAll(s.trim()); for (const e of all) if (visible(e)) return e; } return null; };
  let TOUR = null;
  function tourEnd(done) {
    if (!TOUR) return; markSeen(TOUR.page);
    ["g2-ov", "g2-spot", "g2-bub"].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); });
    window.removeEventListener("resize", TOUR.pos); window.removeEventListener("scroll", TOUR.pos, true); document.removeEventListener("keydown", TOUR.key);
    TOUR = null;
  }
  function tour(page, force) {
    const def = D.tours[page]; if (!def || TOUR) return false;
    if (!force && (toursSeen().includes(page) || !B.tourAuto)) return false;
    const steps = def.map(s => ({el: findEl(s.s), t: s.t, x: s.x})).filter(s => s.el);
    if (!steps.length) return false;
    closePop();
    const gd = document.getElementById("gd-card"); if (gd) gd.remove();        // the short page tip (515) is part of the tour
    try { const ts = new Set(JSON.parse(LSget("mw-tips-seen", "[]"))); ts.add("page:" + (page === "history" ? "history" : page)); LSset("mw-tips-seen", JSON.stringify([...ts].slice(-400))); } catch (e) {}
    const ov = E("div"); ov.id = "g2-ov"; const sp = E("div"); sp.id = "g2-spot"; const bub = E("div"); bub.id = "g2-bub";
    bub.setAttribute("role", "dialog"); bub.setAttribute("aria-live", "polite");
    document.body.append(ov, sp, bub);
    TOUR = {page, i: 0, steps};
    TOUR.pos = () => {
      if (!TOUR) return; const s = TOUR.steps[TOUR.i]; const r = s.el.getBoundingClientRect(), pad = 6;
      const vw = window.innerWidth, vh = window.innerHeight;
      const L = Math.max(4, r.left - pad), Tp = Math.max(4, r.top - pad), W = Math.min(vw - 8, r.width + 2 * pad), H = Math.min(vh - 8, r.height + 2 * pad);
      Object.assign(sp.style, {left: L + "px", top: Tp + "px", width: W + "px", height: H + "px"});
      const bw = bub.offsetWidth, bh = bub.offsetHeight;
      let y = Tp + H + 10; if (y + bh > vh - 8) y = Tp - bh - 10; if (y < 8) y = Math.max(8, Math.min(vh - bh - 8, vh / 2 - bh / 2));
      const x = Math.max(12, Math.min(vw - bw - 12, L + W / 2 - bw / 2));
      bub.style.left = x + "px"; bub.style.top = y + "px";
    };
    TOUR.key = ev => { if (ev.key === "Escape") tourEnd(false); else if (ev.key === "ArrowRight" || ev.key === "Enter") go(1); else if (ev.key === "ArrowLeft") go(-1); };
    function go(d) {
      if (!TOUR) return; const n = TOUR.i + d; if (n >= TOUR.steps.length) { tourEnd(true); return; } if (n < 0) return; TOUR.i = n; paint(d);
    }
    function paint(d0) {
      const s = TOUR.steps[TOUR.i], n = TOUR.steps.length; bub.textContent = "";
      const BK = window.MWBlinki && MWBlinki.on() ? MWBlinki : null; bub.classList.toggle("bk-on", !!BK);
      if (BK) {                                      // 589: Blinki sits next to the bubble and «speaks» it
        const hi = !BK.seenHi() && TOUR.i === 0 ? E("p", "bk-hi", "👋 " + BK.t("Hello, I am Blinki!")) : null; if (hi) BK.markHi();
        const r = BK.row(TOUR.i === 0 ? "normal" : TOUR.i === n - 1 ? "happy" : "point", s.t, [hi, s.x]); bub.appendChild(r);
        if (TOUR.i > 0 && d0 > 0) BK.happyHop(r.fig, TOUR.i === n - 1 ? "happy" : "point");
      } else bub.append(E("b", "", s.t), E("p", "", s.x));
      const gb = E("div", "gb"), dots = E("span", "dots");
      for (let k = 0; k < n; k++) { const i = E("i"); if (k === TOUR.i) i.className = "on"; dots.appendChild(i); }
      dots.setAttribute("aria-label", T("Step") + " " + (TOUR.i + 1) + " " + T("of") + " " + n);
      const sk = BT(T("Skip"), "sec", () => tourEnd(false)), nx = BT(TOUR.i === n - 1 ? T("Done") : T("Next") + " ›", "", () => go(1));
      gb.append(dots, sk, nx); bub.appendChild(gb);
      try { s.el.scrollIntoView({block: "center", behavior: "instant"}); } catch (e) { s.el.scrollIntoView(); }
      requestAnimationFrame(() => { TOUR && TOUR.pos(); setTimeout(() => TOUR && TOUR.pos(), 120); });
      setTimeout(() => nx.focus(), 30);
    }
    ov.onclick = () => go(1);
    window.addEventListener("resize", TOUR.pos); window.addEventListener("scroll", TOUR.pos, true); document.addEventListener("keydown", TOUR.key);
    paint(); return true;
  }
  window.g2Tour = (p, f) => tour(p || PG, f !== false);
  function helpButton() {
    if (!D.tours[PG] || document.getElementById("g2-help")) return;
    const hc = document.querySelector("header .hdr-ctl") || document.querySelector("header"); if (!hc) return;
    const b = BT("?", "sec ic", () => tour(PG, true)); b.id = "g2-help"; b.title = T("Tour of this page"); b.setAttribute("aria-label", T("Tour of this page"));
    hc.insertBefore(b, hc.firstChild);
  }

  // ---------------------------------------------------------------- tip of the day
  async function tipOfDay() {
    if (PG !== "live" || B.lock) return;
    const j = await J("/api/g2?lang=" + LG()); if (!j || !j.tip) return;
    const x = j.tip; if (TOUR || busy() || document.querySelector("#gd-card, #g2-tip")) { setTimeout(tipOfDay, 15000); return; }
    const c = E("div"); c.id = "g2-tip"; c.setAttribute("role", "status");
    c.append(E("small", "", "☀ " + T("Tip of the day")), E("b", "", x.icon + " " + x.title), E("p", "", x.text));
    const gb = E("div", "gb"), close = () => { c.classList.remove("on"); setTimeout(() => c.remove(), 350); };
    const a = E("a", "btn", T("Show me") + " ›"); a.href = x.href;
    gb.append(a, BT(T("Not now"), "sec", close), BT(T("Tip of the day off"), "sec", async () => { await P("/api/set", {key: "tip_of_day", value: false}); close(); }));
    c.appendChild(gb); document.body.appendChild(c); requestAnimationFrame(() => requestAnimationFrame(() => c.classList.add("on")));
    P("/api/g2", {action: "tip_seen", id: x.id});
  }

  // ---------------------------------------------------------------- the guide (setup)
  const LANGS = [["de", "Deutsch"], ["fr", "Français"], ["it", "Italiano"], ["rm", "Rumantsch"], ["en", "English"]];
  let S = null;
  const loadS = async () => { S = await J("/api/setup?lang=" + LG()); return S; };
  const gpost = b => P("/api/setup", Object.assign({step: "guide"}, b));
  function modal(id) { let ov = document.getElementById(id); if (ov) ov.remove(); ov = E("div", "g2m"); ov.id = id; const wc = E("div", "wc"); ov.appendChild(wc); document.body.appendChild(ov); return {ov, wc}; }
  async function qrSvg(u) { try { return await (await fetch("/api/qr?t=" + encodeURIComponent(u))).text(); } catch (e) { return ""; } }

  async function mwGuide(force, start) {
    if (document.getElementById("g2w") || mwGuide.busy) return true;
    if (B.lock) return true;
    mwGuide.busy = true;
    try { await loadS(); } finally { mwGuide.busy = false; }
    if (!S || S.locked || document.getElementById("g2w")) return true;
    const G = S.guide || {};
    const want = /[?&]guide=1/.test(location.search);
    if (!force && !want && S.done) return true;
    if (want) { try { history.replaceState(null, "", location.pathname + location.hash); } catch (e) {} }
    const {ov, wc} = modal("g2w");
    let cur = start || (G.mode && !G.finished && !force ? (G.left[0] || "done") : "choose");
    if (force && G.mode && !G.finished && G.left.length) cur = G.left[0];
    const qrs = {}; for (const a of S.addresses || []) qrs[a.url] = await qrSvg(a.url);
    let timers = [];
    const clearT = () => { timers.forEach(clearInterval); timers = []; };
    const order = () => (S.guide.steps || []).filter(s => !s.auto_skip).map(s => s.id);
    const titleOf = id => ((S.guide.steps || []).find(s => s.id === id) || {});
    const close = () => { clearT(); ov.remove(); };
    async function refresh() { await loadS(); }
    async function move(dir) {
      const o = order(), i = o.indexOf(cur);
      if (dir > 0) cur = i < 0 ? (o[0] || "done") : (o[i + 1] || "done"); else cur = i <= 0 ? "choose" : o[i - 1];
      if (cur !== "done" && cur !== "choose") gpost({action: "step", id: cur});
      render();
    }
    async function render() {
      clearT(); wc.textContent = ""; await refresh();
      const head = E("div", "wh"), body = E("div", "wb"), foot = E("div", "wf");
      wc.append(head, body, foot);
      const later = BT(T("Continue later"), "later", async () => { await gpost({action: "pause"}); close(); });
      const o = order(), i = o.indexOf(cur);
      const st = E("div", "st"); st.append(E("span", "", "🧭 " + T("Setup") + (S.guide.mode ? " · " + T(S.guide.mode === "full" ? "In depth" : "Quick") : "")), later);
      head.appendChild(st);
      if (cur !== "choose") {
        const pb = E("div", "pb"), bi = E("i"); const n = o.length || 1, k = cur === "done" ? n : Math.max(0, i);
        bi.style.width = Math.round(100 * k / n) + "%"; pb.appendChild(bi); head.appendChild(pb);
        if (cur !== "done") head.appendChild(E("div", "st", T("Step") + " " + (i + 1) + " " + T("of") + " " + n));
      }
      const err = E("div", "err");
      const ctx = {body, foot, err, next: null, skip: true, back: cur !== "choose"};
      await (STEP[cur] || STEP.done)(ctx);
      body.appendChild(err);
      if (ctx.back) foot.appendChild(BT("‹ " + T("Back"), "sec sp", () => move(-1)));
      if (cur !== "choose" && cur !== "done") {
        if (ctx.skip) foot.appendChild(BT(T("Skip"), "sec", async () => { await gpost({action: "skip", id: cur}); move(1); }));
        foot.appendChild(BT(T("Next") + " ›", "", async () => {
          if (ctx.fig && window.MWBlinki) MWBlinki.mood(ctx.fig, "think");
          if (ctx.next) { const r = await ctx.next(); if (r === false) { if (ctx.fig) MWBlinki.mood(ctx.fig, "point"); return; } if (r === "stop") return; }
          await gpost({action: "done", id: cur}); bkHop = true; move(1); }));
      }
    }
    let bkHop = false;
    const H = (ctx, icon, title, text, extra) => {
      const BK = window.MWBlinki && MWBlinki.on() ? MWBlinki : null;
      if (!BK) { ctx.body.append(E("h2", "", icon + " " + title)); if (text) ctx.body.appendChild(E("p", "mut", text)); return; }
      const m = cur === "choose" ? "normal" : cur === "done" ? "happy" : "point";          // 589: Blinki says the text of the step
      const r = BK.row(m, icon + " " + title, [...(extra || []), text ? E("p", "mut", text) : null], true); ctx.body.appendChild(r); ctx.fig = r.fig;
      if (bkHop || cur === "done") BK.happyHop(r.fig, m); bkHop = false;
    };
    const setKey = (k, v) => P("/api/set", {key: k, value: v});
    const tgRow = (ctx, label, on, fn) => { const l = E("label", "tg"); l.append(E("span", "", label), sw(on, fn)); ctx.body.appendChild(l); return l; };
    const gotoWith = async (href) => { await gpost({action: "step", id: cur}); location.href = href; };
    const STEP = {
      async choose(ctx) {
        const BK = window.MWBlinki && MWBlinki.on() ? MWBlinki : null; if (BK) BK.markHi();
        H(ctx, "👋", T("Welcome to MoveEye"), T("Every step can be skipped. You can stop at any time and continue later (More → Setup)."),
          BK ? [E("p", "bk-hi", BK.t("Hello, I am Blinki!")), E("p", "", BK.t("I am the eye of MoveEye. I show you everything step by step - and when I blink, all is well."))] : null);
        ctx.body.appendChild(E("p", "", T("Quick (about 5 min.) or thorough?")));
        const mk = (mode, ic, name, dur, text, cls) => { const b = BT("", "big " + cls); const bb = E("b", "", ic + " " + name + " · " + dur); b.append(bb, E("small", "", text));
          b.onclick = async () => { const r = await gpost({action: "start", mode}); if (!r.ok) { ctx.err.textContent = r.error || T("error"); return; } await refresh(); cur = order()[0] || "done"; render(); }; return b; };
        ctx.body.append(mk("quick", "⚡", T("Quick"), T("about 5 minutes"), T("Basics, push messages to the phone, camera test and place, protection and walk test."), ""),
                        mk("full", "🔬", T("In depth"), T("about 20 to 30 minutes"), T("Everything of «Quick» plus zones, night time, light and siren, head, AI model, thermal camera, battery, simulator - each step can be skipped."), "sec"));
        ctx.foot.appendChild(BT(T("Later"), "sec", async () => { await gpost({action: "pause"}); close(); }));
        ctx.back = false;
      },
      async basics(ctx) {
        H(ctx, "🌐", titleOf("basics").title || "");
        ctx.body.appendChild(E("label", "l", T("Language")));
        const lg = E("div", "row2");
        LANGS.forEach(([k, n]) => lg.appendChild(BT(n, "sec" + (LG() === k ? " on2" : ""), async () => {
          LSset("mw-lang", k); await P("/api/setup", {step: "basics", ui_lang: k, device_name: ni.value.trim()}); location.href = "/?guide=1"; })));
        ctx.body.appendChild(lg);
        ctx.body.appendChild(E("label", "l", T("Name of this device (optional)")));
        const ni = E("input"); ni.type = "text"; ni.maxLength = 40; ni.value = S.device_name || ""; ni.placeholder = T("e.g. camper, garden"); ctx.body.appendChild(ni);
        ctx.body.appendChild(E("label", "l", T("Time and place")));
        const tl = E("div", "mut"); const now = new Date();
        tl.textContent = T("Time on MoveEye") + ": " + (S.time || "–") + " · " + T("on this device") + ": " + now.toLocaleString([], {day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit"});
        const tb = BT(T("🕒 Take the time of this device"), "sec", async () => { const r = await gpost({action: "place_time", t: Date.now(), tz: (Intl.DateTimeFormat().resolvedOptions().timeZone || "")});
          await refresh(); tl.textContent = (r.ok ? "✓ " : "⚠ ") + T("Time on MoveEye") + ": " + (S.time || "–"); });
        const r1 = E("div", "row2"); r1.appendChild(tb); ctx.body.append(tl, r1);
        const two = E("div", "two"), la = E("input"), lo = E("input"); la.type = lo.type = "number"; la.step = lo.step = "0.0001";
        la.value = S.lat; lo.value = S.lon; la.setAttribute("aria-label", T("Latitude")); lo.setAttribute("aria-label", T("Longitude"));
        const c1 = E("div"), c2 = E("div"); c1.append(E("div", "mut", T("Latitude")), la); c2.append(E("div", "mut", T("Longitude")), lo); two.append(c1, c2);
        const gb = BT(T("📍 Location of this device"), "sec", () => {
          if (!window.isSecureContext || !navigator.geolocation) { ctx.err.textContent = T("Location: only on a secure page (https) - or type it."); return; }
          navigator.geolocation.getCurrentPosition(p => { la.value = p.coords.latitude.toFixed(4); lo.value = p.coords.longitude.toFixed(4); }, e => { ctx.err.textContent = e.message; }, {timeout: 10000}); });
        const r2 = E("div", "row2"); r2.appendChild(gb); ctx.body.append(two, r2);
        tgRow(ctx, "⚡ " + T("Fast updates (development)"), S.guide.update_fast, x => setKey("update_fast", x));
        ctx.body.appendChild(E("label", "l", "🔒 " + T("Password for this page")));
        ctx.body.appendChild(E("p", "mut", T("Without a password everybody in the same network (and with the link) can watch and switch everything.")));
        let p1 = null, p2 = null, without = null;
        if (S.pw_cmdline) ctx.body.appendChild(E("p", "ok", "✓ " + T("The password was given on the command line (--web-password).")));
        else {
          if (S.has_pw) ctx.body.appendChild(E("p", "ok", "✓ " + T("A password is set already. Enter a new one only to change it.")));
          p1 = E("input"); p1.type = "password"; p1.autocomplete = "new-password"; p1.placeholder = T("Password (6-64 characters)");
          p2 = E("input"); p2.type = "password"; p2.autocomplete = "new-password"; p2.placeholder = T("Repeat password"); p2.style.marginTop = "8px";
          ctx.body.append(p1, p2);
          if (!S.has_pw) { const l = E("label", "tg"); without = E("input"); without.type = "checkbox"; l.append(E("span", "", T("Continue without a password (not recommended)")), without); ctx.body.appendChild(l); }
        }
        ctx.next = async () => {
          if (p1 && p1.value !== p2.value) { ctx.err.textContent = T("The passwords are not the same"); return false; }
          if (p1 && !p1.value && !S.has_pw && !(without && without.checked)) { ctx.err.textContent = T("Password (6-64 characters)"); p1.focus(); return false; }
          let r = await P("/api/setup", {step: "basics", ui_lang: LG(), device_name: ni.value.trim()}); if (!r.ok) { ctx.err.textContent = r.error || T("error"); return false; }
          if (String(la.value) !== String(S.lat) || String(lo.value) !== String(S.lon)) { r = await gpost({action: "place_time", lat: la.value, lon: lo.value}); if (!r.ok) { ctx.err.textContent = r.error || T("error"); return false; } }
          if (p1 && p1.value) {
            await gpost({action: "done", id: "basics"});
            r = await P("/api/password", {password: p1.value}); if (!r.ok) { ctx.err.textContent = r.error || T("error"); await gpost({action: "step", id: "basics"}); return false; }
            ctx.body.appendChild(E("p", "ok", "✓ " + T("The page now asks once for the new password (user name: anything) and then continues here.")));
            setTimeout(() => { location.href = "/?guide=1"; }, 1600); return "stop";
          }
          return true;
        };
      },
      async push(ctx) {
        H(ctx, "🔔", titleOf("push").title || "");
        const nt = (S.notify_type === "ntfy" && /^https:\/\/[^/]+\/[^/]+$/.test(S.notify_url || "")) ? S.notify_url : "";
        let server = nt ? nt.replace(/\/[^/]+$/, "") : "https://ntfy-me.com";
        let topic = nt ? nt.replace(/^.*\//, "") : "mw-" + Array.from(crypto.getRandomValues(new Uint8Array(8)), b => "abcdefghijkmnpqrstuvwxyz23456789"[b % 32]).join("");
        if (nt) ctx.body.appendChild(E("p", "ok", "✓ " + T("The push channel is set up already:") + " " + server.replace(/^https:\/\//, "") + " / " + topic));
        ctx.body.append(E("p", "", T("1. Install the free app «ntfy» (App Store / Play Store).")), E("p", "", T("2. In the app: + → enter the topic below (and the server, if it is not the default one) - or open this code with the phone camera.")));
        const box = E("div", "qr"); const upd = async () => { box.innerHTML = await qrSvg(server.replace(/\/+$/, "") + "/" + topic); };
        ctx.body.appendChild(E("label", "l", T("Topic (like a secret channel name)")));
        const ti = E("input"); ti.type = "text"; ti.value = topic; ti.maxLength = 64; ti.oninput = () => { topic = ti.value.trim().replace(/[^A-Za-z0-9_-]/g, ""); }; ti.onchange = upd; ctx.body.appendChild(ti);
        ctx.body.appendChild(E("label", "l", T("Server")));
        const si = E("input"); si.type = "text"; si.value = server; si.oninput = () => { server = si.value.trim(); }; si.onchange = upd; ctx.body.append(si, box); upd();
        const res = E("div", "mut");
        const save = async () => { const r = await P("/api/setup", {step: "push", url: server.replace(/\/+$/, "") + "/" + topic}); if (!r.ok) ctx.err.textContent = r.error || T("error"); return r.ok; };
        const rw = E("div", "row2"); rw.appendChild(BT(T("📨 Send test message"), "sec", async () => { if (!(await save())) return; const r = await P("/api/notify_test", {});
          res.textContent = r.ok ? "✓ " + T("Sent - did it arrive on the phone?") : "⚠ " + (r.error || T("error")); res.className = r.ok ? "ok" : "warn"; }));
        ctx.body.append(rw, res);
        ctx.next = async () => (topic.length < 3 ? true : await save());
      },
      async camera(ctx) {
        H(ctx, "📷", titleOf("camera").title || "", T("Is the picture right? Upright, sharp, the place in view?"));
        const img = E("img", "cam"); img.alt = ""; const stl = E("div", "mut");
        const tick = async () => { img.src = "/api/frame.jpg?t=" + Date.now();
          const j = await J("/api/state?lang=" + LG()); const s = j && j.state; if (!s) return;
          const fps = +s.fps || 0; stl.textContent = (s.source_status || "") + " · " + fps.toFixed(1) + " " + T("frames/s"); noPic.hidden = fps > 0; };
        const noPic = E("div"); noPic.hidden = true;
        noPic.appendChild(E("p", "warn", "⚠ " + T("No picture yet.")));
        const r0 = E("div", "row2"); const ca = E("a", "btn sec", T("📷 Choose the camera")); ca.href = "#"; ca.onclick = e => { e.preventDefault(); gotoWith("/cams"); }; r0.appendChild(ca); noPic.appendChild(r0);
        noPic.appendChild(E("label", "l", T("🎮 Use the 3D simulator as camera")));
        const su = E("input"); su.type = "text"; su.placeholder = "http://192.168.1.20:8765"; noPic.appendChild(su);
        J("/api/sim").then(j => { if (j && (j.url || (j.sim && j.sim.url))) su.value = j.url || j.sim.url; });
        const sm = E("div", "mut"); const r1 = E("div", "row2");
        r1.appendChild(BT(T("🔌 Connect"), "sec", async () => { sm.textContent = T("Connecting …"); const r = await P("/api/sim", {url: su.value.trim(), on: true, confirm: true});
          sm.textContent = r.ok === false ? "⚠ " + (r.error || T("error")) : "✓ " + T("Connecting …"); }));
        noPic.append(r1, sm);
        ctx.body.append(img, stl, noPic);
        ctx.body.appendChild(E("p", "", T("MoveEye looks round once and suggests zones, paths and the things to guard (a few minutes). Then come back here.")));
        const r2 = E("div", "row2"); r2.appendChild(BT(T("📐 Set up the place"), "", () => gotoWith("/place"))); ctx.body.appendChild(r2);
        tick(); timers.push(setInterval(tick, 2000));
      },
      async view(ctx) {
        H(ctx, "🧭", titleOf("view").title || "", T("Who should see «Simple» - and what is MoveEye for?"));
        let simple = S.guide.default_simple, use = S.guide.use_case;
        const seg = E("div", "row2"); const a = BT("🙂 " + T("Simple"), "sec"), b = BT("🧑‍🔧 " + T("Expert"), "sec");
        const pa = () => { a.classList.toggle("on2", simple); b.classList.toggle("on2", !simple); }; a.onclick = () => { simple = true; pa(); }; b.onclick = () => { simple = false; pa(); }; pa();
        seg.append(a, b); ctx.body.append(seg, E("p", "mut", T("Default of every page (each page can switch by itself).")));
        ctx.body.appendChild(E("label", "l", T("What is MoveEye for?")));
        const g = E("div", "usegrid"), opts = [];
        [["camping", "⛺", "Camping: tent, caravan"], ["home", "🏡", "House and garden"], ["wild", "🦌", "Watching animals"], ["holiday", "🏔", "Holiday house, alpine hut"],
         ["room", "⏰", "In the room: wake-up alarm"], ["", "🧰", "everything (not chosen)"]].forEach(([v, ic, n]) => {
          const o = BT("", "sec useopt"); o.append(E("span", "", ic), E("span", "", T(n))); o.onclick = () => { use = v; opts.forEach(([x, e]) => e.classList.toggle("on2", x === use)); };
          opts.push([v, o]); g.appendChild(o); });
        opts.forEach(([x, e]) => e.classList.toggle("on2", x === use)); ctx.body.appendChild(g);
        ctx.next = async () => { const r = await gpost({action: "view", simple, use}); if (!r.ok) { ctx.err.textContent = r.error || T("error"); return false; }
          B.simple = simple; LSset("mw-page-mode", "{}"); return true; };
      },
      async zones(ctx) {
        H(ctx, "✏", titleOf("zones").title || "", T("Draw areas into the picture: ignore the road, privacy, the sleeping place for the wake-up alarm, a line."));
        const r = E("div", "row2"); r.appendChild(BT(T("✏ Draw the zones"), "", () => gotoWith("/zones"))); ctx.body.appendChild(r);
      },
      async protect(ctx) {
        H(ctx, "🛡", titleOf("protect").title || "");
        const box = E("div"); ctx.body.appendChild(box);
        const paint = async () => { const v = await J("/api/protect?lang=" + LG()); if (!v) return; box.textContent = "";
          const col = {green: "ok", orange: "warn", red: "err"}[v.colour] || "mut";
          const bad = (v.items || []).filter(x => !x.ok);
          box.appendChild(E("p", col, (v.colour === "green" ? "🟢 " : v.colour === "red" ? "🔴 " : "🟠 ") + T("State of the protection") + ": " + (bad.length ? T("Still missing:") : T("Everything ready."))));
          if (bad.length) { const ul = E("ul", "sum"); bad.forEach(x => ul.appendChild(E("li", "", x.text))); box.appendChild(ul); } };
        paint();
        ctx.body.appendChild(E("label", "l", "🚶 " + T("Walk past the camera like a visitor - MoveEye beeps at every detection. 3 minutes, no alarms meanwhile.")));
        const ws = E("div", "mut"), wr = E("div", "row2");
        const wb = BT(T("🚶 Start walk test"), "", async () => { const on = wb.dataset.on === "1"; const r = await P("/api/walktest", {action: on ? "stop" : "start"}); if (r.ok === false) ws.textContent = "⚠ " + (r.error || T("error")); wpaint(r); });
        const wpaint = w => { if (!w) return; wb.dataset.on = w.on ? "1" : "0"; wb.textContent = w.on ? T("■ Stop") : T("🚶 Start walk test");
          ws.textContent = w.on ? ("⏱ " + Math.floor(w.left / 60) + ":" + String(w.left % 60).padStart(2, "0") + " " + T("left") + " · " + w.n_det + " × " + T("recognised")) : (w.result ? "✓ " + (w.result.text || "") : ""); };
        wr.appendChild(wb); ctx.body.append(wr, ws);
        J("/api/walktest?lang=" + LG()).then(wpaint); timers.push(setInterval(async () => { if (wb.dataset.on === "1") wpaint(await J("/api/walktest?lang=" + LG())); }, 1500));
        ctx.body.appendChild(E("label", "l", T("Switch on now?")));
        const lv = E("div", "row2"); const lm = E("div", "mut", T("switches on at once (with the countdown)"));
        [["off", T("Leave it off")], ["watch", "🛡 " + T("Watchful")], ["full", "🚨 " + T("Full")]].forEach(([k, n]) => lv.appendChild(BT(n, "sec", async e => {
          lv.querySelectorAll("button").forEach(x => x.classList.remove("on2")); e.target.classList.add("on2");
          const r = await P("/api/protect", {action: "level", level: k}); lm.textContent = r.ok === false ? "⚠ " + (r.error || T("error")) : "✓ " + n; paint(); })));
        ctx.body.append(lv, lm);
      },
      async schedules(ctx) {
        H(ctx, "🕘", titleOf("schedules").title || "");
        const sc = await J("/api/schema?lang=" + LG()) || []; let rep = null;
        sc.forEach(s => { (s.toggles || []).forEach(x => { if (x.key === "report_on") rep = x; }); (s.sliders || []).forEach(x => { if (x.key === "report_hour") ctx._h = x; }); });
        tgRow(ctx, T("Night report in the morning"), rep ? rep.value : true, v => setKey("report_on", v));
        if (ctx._h) { const l = E("label", "tg"); const s = E("select"); for (let h = ctx._h.min; h <= ctx._h.max; h++) { const o = E("option", "", h + ":00"); o.value = h; s.appendChild(o); }
          s.value = ctx._h.value; s.style.width = "auto"; s.onchange = () => setKey("report_hour", +s.value); l.append(E("span", "", T("End of the night time")), s); ctx.body.appendChild(l); }
        ctx.body.appendChild(E("p", "mut", T("Schedules switch features by themselves, e.g. the protection every night.")));
        const r = E("div", "row2"); r.appendChild(BT(T("🕘 Schedules"), "sec", () => gotoWith("/protect#sched-list"))); ctx.body.appendChild(r);
      },
      async lightsiren(ctx) {
        H(ctx, "💡", titleOf("lightsiren").title || "");
        const hw = S.guide.hw || {}; const r = E("div", "row2"); const m = E("div", "mut");
        const lightT = async (n) => { await P("/api/light", {light: n, mode: "on"}); m.textContent = "✓ " + n; setTimeout(() => P("/api/light", {light: n, mode: "auto"}), 3000); };
        if (hw.light) r.append(BT(T("💡 Light 3 s"), "sec", () => lightT("white")), BT(T("🌙 Infrared 3 s"), "sec", () => lightT("ir")));
        if (hw.speaker) r.append(BT(T("🔊 Test sound"), "sec", async () => { const x = await P("/api/audio", {action: "test"}); m.textContent = x.ok ? "✓" : "⚠ " + (x.error || ""); }),
                                 BT(T("🚨 Siren 2 s"), "sec", async () => { const x = await P("/api/audio", {action: "siren"}); m.textContent = x.ok ? "✓" : "⚠ " + (x.error || ""); setTimeout(() => P("/api/audio", {action: "stop"}), 2000); }));
        ctx.body.append(r, m); if (hw.speaker) ctx.body.appendChild(E("p", "mut", T("Loud! Warn the neighbours first.")));
      },
      async servos(ctx) {
        H(ctx, "🎯", titleOf("servos").title || "");
        const r = E("div", "row2"); const mv = d => P("/api/move", {dir: d, step: 8});
        r.append(BT(T("◎ Centre"), "sec", () => mv("center")), BT(T("◀ ▶ Turn a little"), "sec", async () => { await mv("left"); setTimeout(() => mv("right"), 900); setTimeout(() => mv("center"), 1800); }));
        ctx.body.append(r, E("p", "mut", T("Direction of turning wrong? Swap it:")));
        const sc = await J("/api/schema?lang=" + LG() + "&simple=0") || []; const v = {};
        sc.forEach(s => (s.toggles || []).forEach(x => { v[x.key] = x.value; }));
        tgRow(ctx, T("Invert pan direction"), v.invert_pan, x => setKey("invert_pan", x)); tgRow(ctx, T("Invert tilt direction"), v.invert_tilt, x => setKey("invert_tilt", x));
        const r2 = E("div", "row2"); r2.appendChild(BT(T("🛠 Servo test (tools)"), "sec", () => gotoWith("/tools"))); ctx.body.appendChild(r2);
      },
      async ai(ctx) {
        H(ctx, "🤖", titleOf("ai").title || "", T("The AI says «person», «animal», «car». It runs on the Pi or on a helper PC."));
        const sc = await J("/api/schema?lang=" + LG() + "&simple=0") || []; const v = {}; sc.forEach(s => (s.toggles || []).forEach(x => { v[x.key] = x.value; }));
        tgRow(ctx, T("AI detection"), v.ai_enabled !== false, x => setKey("ai_enabled", x));
        const st = await J("/api/state?lang=" + LG()); if (st && st.state) ctx.body.appendChild(E("p", "mut", "🤖 " + (st.state.ai_status || "")));
        const om = await J("/api/own_model?lang=" + LG()); if (om) ctx.body.appendChild(E("p", "mut", T("Own AI model") + ": " + (om.msg || om.status || (om.loaded ? "✓" : "–"))));
      },
      async thermal(ctx) {
        H(ctx, "🌡", titleOf("thermal").title || "");
        const sc = await J("/api/schema?lang=" + LG() + "&simple=0") || []; const v = {}; sc.forEach(s => (s.toggles || []).forEach(x => { v[x.key] = x.value; }));
        tgRow(ctx, T("Thermal picture over the live picture"), v.thermal_on, x => setKey("thermal_on", x)); tgRow(ctx, T("Alarm from the thermal camera"), v.thermal_alarm, x => setKey("thermal_alarm", x));
        const st = await J("/api/state?lang=" + LG()); if (st && st.state && st.state.thermal) ctx.body.appendChild(E("p", "mut", "🌡 " + st.state.thermal));
      },
      async battery(ctx) {
        H(ctx, "🔋", titleOf("battery").title || "");
        const st = await J("/api/state?lang=" + LG()); const b = st && st.state && st.state.battery;
        if (b && b.on) ctx.body.appendChild(E("p", "", "🔋 " + (b.pct != null ? b.pct + " % " + T("charge") : "") + (b.hours != null ? " · ~" + b.hours + " h" : "")));
        const sc = await J("/api/schema?lang=" + LG() + "&simple=0") || []; const v = {}; sc.forEach(s => { (s.toggles || []).forEach(x => { v[x.key] = x.value; }); (s.sliders || []).forEach(x => { v[x.key] = x.value; }); });
        if (!(b && b.src === "ups")) {                     // no UPS HAT: a powerbank? (it cannot be detected)
          const l = E("label", "tg"), s = E("select"); s.style.width = "auto";
          [0, 5000, 10000, 20000, 26800, 30000, 40000, 50000].forEach(m => { const o = E("option", "", m ? m + " mAh" : "– " + T("no battery") + " –"); o.value = m; s.appendChild(o); });
          s.value = String(v.batt_mah || 0); if (s.value === "") { const o = E("option", "", v.batt_mah + " mAh"); o.value = v.batt_mah; s.appendChild(o); s.value = String(v.batt_mah); }
          s.onchange = () => setKey("batt_mah", +s.value); l.append(E("span", "", T("Powerbank capacity")), s); ctx.body.appendChild(l);
          const r = E("div", "row2"), m = E("span", "mut"); r.append(BT(T("🔋 Charged full now"), "sec", async () => { const x = await P("/api/battery", {}); m.textContent = x.ok ? "✓" : "⚠"; }), m); ctx.body.appendChild(r);
        }
        tgRow(ctx, T("Battery saving automatic"), v.batt_save_on, x => setKey("batt_save_on", x));
      },
      async sim(ctx) {
        H(ctx, "🎮", titleOf("sim").title || "", T("The 3D simulator on the PC tests MoveEye without the real place. Optional."));
        const j = await J("/api/sim") || {}; const su = E("input"); su.type = "text"; su.placeholder = "http://192.168.1.20:8765"; su.value = j.url || (j.sim && j.sim.url) || "";
        ctx.body.append(E("label", "l", T("Address of the simulator")), su);
        const sm = E("div", "mut", (j.on || (j.sim && j.sim.on)) ? "✓ " + T("connected") : ""); const r = E("div", "row2");
        r.appendChild(BT(T("🔌 Connect"), "sec", async () => { sm.textContent = T("Connecting …"); const x = await P("/api/sim", {url: su.value.trim(), on: true, confirm: true}); sm.textContent = x.ok === false ? "⚠ " + (x.error || T("error")) : "✓ " + T("Connecting …"); }));
        ctx.body.append(r, sm);
      },
      async tours(ctx) {
        H(ctx, "💡", titleOf("tours").title || "");
        tgRow(ctx, T("Tour of a page on its first visit"), S.guide.tours_auto, x => { B.tourAuto = x; setKey("tours_auto", x); });
        tgRow(ctx, T("Tip of the day"), S.guide.tip_of_day, x => setKey("tip_of_day", x));
        if (window.MWBlinki) tgRow(ctx, MWBlinki.t("Show Blinki"), MWBlinki.on(), x => { MWBlinki.set(x); setKey("blinki_on", x); render(); });
        const l = E("label", "tg"), s = E("select"); s.style.width = "auto";
        ["off", "basic", "normal", "all"].forEach(k => { const o = E("option", "", T(k)); o.value = k; s.appendChild(o); });
        try { s.value = ["off", "basic", "normal", "all"][(window.MW_GUIDE || {}).level ?? 2]; } catch (e) {}
        s.onchange = () => P("/api/text", {key: "tips_level", value: s.value}); l.append(E("span", "", T("Explanations the first time something is opened")), s); ctx.body.appendChild(l);
        const r = E("div", "row2"); r.appendChild(BT(T("↺ Reset all tours"), "sec", async () => { await gpost({action: "tours_reset"}); LSset("mw-tours-seen", "[]"); ctx.err.textContent = ""; r.appendChild(E("span", "ok", "✓ " + T("All tours will show again."))); })); ctx.body.appendChild(r);
      },
      async done(ctx) {
        H(ctx, "✅", T("Done!"));
        const ul = E("ul", "sum");
        (S.guide.steps || []).forEach(s => { const d = (S.guide.done || []).includes(s.id), k = (S.guide.skipped || []).includes(s.id);
          ul.appendChild(E("li", d ? "ok" : "mut", (d ? "✓ " : "⤼ ") + s.icon + " " + s.title + (d ? "" : " · " + (s.auto_skip ? T("skipped automatically") + " (" + s.auto_skip + ")" : k ? T("skipped") : "–")))); });
        ctx.body.appendChild(ul);
        ctx.body.appendChild(E("p", "mut", T("Open MoveEye on other devices with these codes. On the phone: Share → «Add to Home Screen» - then it starts like an app.")));
        const g = E("div", "qrs");
        for (const a of S.addresses || []) { const c = E("div"), b = E("div", "qr"); b.innerHTML = qrs[a.url] || "";
          c.append(E("b", "", T({lan: "Home network", hotspot: "Own Wi-Fi of the device", tailscale: "On the road (Tailscale)"}[a.kind] || a.kind)), b, E("div", "mut", a.url)); g.appendChild(c); }
        ctx.body.appendChild(g);
        const r = E("div", "row2"); const lk = E("a", "btn sec", T("🖨 Quick start card with QR codes")); lk.href = "/setup-card?lang=" + LG(); lk.target = "_blank"; r.appendChild(lk); ctx.body.appendChild(r);
        if (S.guide.mode !== "full") ctx.foot.appendChild(BT(T("➕ Set up more (thorough)"), "sec", async () => { await gpost({action: "start", mode: "full"}); await refresh(); cur = S.guide.left[0] || "done"; render(); }));
        ctx.foot.appendChild(BT(T("Let's go"), "", async () => { await gpost({action: "finish"}); close(); if (D.tours[PG] && B.tourAuto) setTimeout(() => tour(PG, false), 600); }));
        ctx.skip = false;
      },
    };
    render();
    return true;
  }
  window.mwGuide = mwGuide;

  // ---------------------------------------------------------------- «back to the setup» on the other pages
  function pill() {
    const g = B.guide || {}; if (!g.mode || g.finished || g.paused || !g.step) return;
    if (PG === "live" || document.getElementById("g2-pill")) return;
    const b = BT(T("↩ Back to the setup"), "", () => { location.href = "/?guide=1"; }); b.id = "g2-pill"; document.body.appendChild(b);
  }

  // ---------------------------------------------------------------- factory reset (Mehr → System, Einstellungen → System)
  async function g2Factory() {
    const F = await J("/api/factory?lang=" + LG()); if (!F || F.ok === false) { alert(T("error")); return; }
    const {ov, wc} = modal("g2f"); const h = E("div", "wh"), b = E("div", "wb"), f = E("div", "wf"); wc.append(h, b, f);
    h.appendChild(E("h2", "", "⚠ " + T("Reset to factory settings")));
    const sec = (t1, t2, cls) => { b.append(E("b", cls || "", t1), E("p", "mut", t2)); };
    sec(T("Back to the factory settings:"), T("all settings, zones, schedules, waypoints, password, users, PIN, the place"));
    sec(T("These stay:"), T("Wi-Fi and own Wi-Fi, remote access (Tailscale), the push channel (ntfy), the update settings, the own AI model and what it learned"), "ok");
    sec(T("These are deleted:"), T("all recordings and photos, the animal diary, the log"), "del");
    b.appendChild(E("p", "", T("First a copy of the old settings is saved - you can download it below.")));
    let pw = null, pin = null;
    if (F.need_pw) { b.appendChild(E("label", "l", T("Your password"))); pw = E("input"); pw.type = "password"; pw.autocomplete = "current-password"; b.appendChild(pw); }
    else if (F.need_pin) { b.appendChild(E("label", "l", T("Your PIN"))); pin = E("input"); pin.type = "password"; pin.inputMode = "numeric"; b.appendChild(pin); }
    b.appendChild(E("label", "l", T("Type {w} to confirm").replace("{w}", "«" + F.word + "»")));
    const w = E("input"); w.type = "text"; w.autocomplete = "off"; w.autocapitalize = "characters"; w.spellcheck = false; b.appendChild(w);
    const err = E("div", "err"); b.appendChild(err);
    const go = BT(T("Reset now"), ""); go.disabled = true; go.style.background = "var(--red,#d33)"; go.style.borderColor = "var(--red,#d33)";
    w.oninput = () => { go.disabled = w.value.trim().toUpperCase() !== String(F.word).toUpperCase(); };
    go.onclick = async () => {
      go.disabled = true; err.textContent = "";
      const r = await P("/api/factory", {word: w.value, password: pw ? pw.value : "", pin: pin ? pin.value : ""});
      if (!r.ok) { err.textContent = "⚠ " + (r.error || T("error")); go.disabled = false; return; }
      try { Object.keys(localStorage).forEach(k => { if (/^mw-/.test(k) && k !== "mw-lang") localStorage.removeItem(k); }); } catch (e) {}
      b.textContent = ""; f.textContent = "";
      b.append(E("p", "ok", "✓ " + T("Reset done.")), E("p", "", T("Copy of the old settings:")));
      const a = E("a", "btn sec", "⬇ " + r.backup); a.href = "/api/factory/backup/" + encodeURIComponent(r.backup); a.download = r.backup; b.appendChild(a);
      f.appendChild(BT(T("Start the setup"), "", () => { location.href = "/?guide=1"; }));
    };
    f.append(BT(T("Close"), "sec sp", () => ov.remove()), go);
    if (F.backups && F.backups.length) {
      b.appendChild(E("label", "l", T("Copies of the old settings")));
      F.backups.forEach(x => { const a = E("a", "", "⬇ " + x.when + " (" + x.kb + " kB)"); a.href = "/api/factory/backup/" + encodeURIComponent(x.name); a.download = x.name; a.style.display = "block"; b.appendChild(a); });
    }
    setTimeout(() => (pw || pin || w).focus(), 50);
  }
  window.g2Factory = g2Factory;

  // ---------------------------------------------------------------- Mehr: setup, tours, system
  async function moreCards() {
    const box = document.getElementById("g2-more"); if (!box) return;
    const j = await J("/api/g2?lang=" + LG()); if (!j || !j.guide) return;
    const g = j.guide; box.textContent = ""; box.className = "g2-card";
    box.appendChild(E("h3", "", "🧭 " + T("Setup") + " · " + T("Help")));
    const n = (g.steps || []).filter(s => !s.auto_skip).length, k = n - (g.left || []).length;
    box.appendChild(E("div", "mut", g.finished || (!g.mode && g.setup_done) ? "✓ " + T("Setup finished.") : g.mode ? T("Setup paused - step") + " " + Math.min(n, k + 1) + " " + T("of") + " " + n : T("never done")));
    const bt = E("div", "btns");
    const start = E("a", "btn", g.mode && !g.finished ? T("🧭 Continue the setup") : (g.finished || g.setup_done) ? T("🧭 Setup again") : T("🧭 Start the setup"));
    start.href = "/?guide=1"; start.onclick = async e => { e.preventDefault(); if (g.finished || !g.mode) await P("/api/setup", {step: "again"}); else await gpost({action: "resume"}); location.href = "/?guide=1"; };
    const rs = BT(T("↺ Reset all tours"), "sec", async () => { await gpost({action: "tours_reset"}); LSset("mw-tours-seen", "[]"); rs.textContent = "✓ " + T("All tours will show again."); });
    bt.append(start, rs); box.appendChild(bt);
    const row = (label, on, key) => { const l = E("label", "tg"); l.append(E("span", "", label), sw(on, v => P("/api/set", {key, value: v}))); box.appendChild(l); };
    row(T("Tour of a page on its first visit"), g.tours_auto, "tours_auto"); row(T("Tip of the day"), g.tip_of_day, "tip_of_day");
    if (window.MWBlinki) { const l = E("label", "tg"); l.append(E("span", "", MWBlinki.t("Show Blinki")), sw(MWBlinki.on(), v => { MWBlinki.set(v); P("/api/set", {key: "blinki_on", value: v}); })); box.appendChild(l); }
    const sysb = document.getElementById("g2-sys"); if (!sysb) return;
    sysb.textContent = ""; sysb.className = "g2-card"; sysb.appendChild(E("h3", "", "⚙ " + T("System")));
    const sb = E("div", "btns"); sb.appendChild(BT(T("⚠ Reset to factory settings …"), "sec", g2Factory)); sysb.appendChild(sb);
    const F = await J("/api/factory?lang=" + LG());
    if (F && F.backups && F.backups.length) { sysb.appendChild(E("div", "mut", T("Copies of the old settings") + ":")); const ul = E("ul");
      F.backups.forEach(x => { const li = E("li"), a = E("a", "", "⬇ " + x.when + " (" + x.kb + " kB)"); a.href = "/api/factory/backup/" + encodeURIComponent(x.name); a.download = x.name; li.appendChild(a); ul.appendChild(li); });
      sysb.appendChild(ul); }
  }

  // ---------------------------------------------------------------- start
  const busy = () => !!document.querySelector(".g2m, #wiz, #spa, .prt-wiz, #g2-bub");
  function startAll() {
    helpButton();
    if (D.modePages.includes(PG)) { const main = document.querySelector("main"); if (main && !document.getElementById("g2-modebar")) main.insertBefore(modeBar(), main.firstChild); paintMode(); }
    paintTT();
    decorate();
    const st = document.getElementById("settings");
    if (st) new MutationObserver(() => { clearTimeout(startAll._d); startAll._d = setTimeout(() => { decorate(); if (!document.getElementById("g2-tt")) paintTT(); }, 150); }).observe(st, {childList: true, subtree: true});
    moreCards(); pill();
    const wantGuide = /[?&]guide=1/.test(location.search) || (!B.setupDone && !B.lock);
    if (PG === "live" && wantGuide) setTimeout(() => mwGuide(false), 300);
    else if (B.setupDone && B.tourAuto && D.tours[PG] && !toursSeen().includes(PG)) {
      let tries = 0;                                   // after other windows (news of the version, protection assistant, guide)
      const go = () => { if (busy() && tries++ < 20) { setTimeout(go, 2000); return; } if (!busy()) tour(PG, false); };
      setTimeout(go, 1800);
    }
    if (B.setupDone) setTimeout(tipOfDay, 6000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", startAll); else startAll();
})();
"""
