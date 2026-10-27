#@ Motion Watch – Teil 450: Web: gemeinsames Aussehen (CSS), Bluetooth-Teil. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Web stream + remote control (Flask) - http://<pi-ip>:5000/
#   /              control page (live video, pan/tilt pad, CPU, all settings)
#   /video_feed    raw MJPEG stream          /snapshot.jpg   current frame
#   /api/...       JSON API used by the page (state, set, move, action, relay, triggers)
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Shared look of all web pages (header, navigation, buttons, cards, forms)
# ----------------------------------------------------------------------------
BT_JS = r"""
Object.assign(I18N.de, {"Everything about the simulator (tab Simulator)": "Alles zum Simulator (Reiter Simulator)"});
Object.assign(I18N.de, {"3D simulator for Windows (ZIP)": "MW Sim · 3D für Windows (ZIP)", "Link for the PC browser": "Link für den Browser am PC"});
Object.assign(I18N.de, {"own Wi-Fi on + internet from": "Eigenes WLAN ein + Internet von", "repeater": "Repeater",
  "own Wi-Fi on - the second adapter looks for known networks": "Eigenes WLAN ein – der zweite Adapter sucht bekannte Netze"});
Object.assign(I18N.de, {"Bluetooth loudspeaker": "Bluetooth-Lautsprecher", "Search Bluetooth loudspeakers": "Bluetooth-Lautsprecher suchen",
  "Bluetooth is not available (sudo apt install bluez)": "Bluetooth ist nicht verfügbar (sudo apt install bluez)",
  "Searching … put the loudspeaker into pairing mode (blue light blinking)": "Suche läuft … Lautsprecher in den Kopplungsmodus versetzen (blaues Licht blinkt)",
  "connecting …": "verbinde …", "no devices yet - press «Search»": "noch keine Geräte - «suchen» drücken", "connected": "verbunden",
  "paired": "gekoppelt", "connected - used for the siren and for talking": "verbunden - wird für Sirene und Sprechen verwendet",
  "Connect": "Verbinden", "Disconnect": "Trennen", "Remove": "Entfernen", "🔊 Test sound": "🔊 Testton",
  "Loudspeaker in use": "Lautsprecher in Gebrauch", "none": "keiner"});
// ---- Bluetooth loudspeaker: search, connect (pairs + trusts it), disconnect, remove ----
let btTimer = null, btLast = null;
function btBox(noTitle) {
  const box = el("div", "btbox");
  const h = el("div", "", "🔵 " + t("Bluetooth loudspeaker")); h.style.fontWeight = "700"; h.style.marginTop = "10px";
  const b = el("div", "btns"); const sc = el("button", "sec", t("Search Bluetooth loudspeakers")); sc.type = "button"; sc.id = "bt-scan"; sc.onclick = btScan;
  b.appendChild(sc);
  const st = el("div", "mut", ""); st.id = "bt-st"; const list = el("div"); list.id = "bt-list";
  if (noTitle) box.append(b, st, list); else box.append(h, b, st, list);
  setTimeout(btPoll, 300);
  return box;
}
async function btScan() {
  const r = await post("/api/bt", {action: "scan", lang: LANG});
  if (!r.ok) { $("#bt-st").textContent = "⚠ " + (r.error || "error"); return; }
  btPoll();
}
async function btPoll() {
  let j; try { j = await (await fetch("/api/bt", {cache: "no-store"})).json(); } catch (e) { return; }
  btLast = j; btRender(j);
  clearTimeout(btTimer); if (j.scanning || j.busy) btTimer = setTimeout(btPoll, 1500);
}
function btRender(j) {
  const st = $("#bt-st"), L = $("#bt-list"), sc = $("#bt-scan"); if (!st) return;
  if (!j.available) { st.textContent = t("Bluetooth is not available (sudo apt install bluez)"); L.textContent = ""; sc.disabled = true; return; }
  sc.disabled = !!j.scanning;
  st.textContent = j.scanning ? t("Searching … put the loudspeaker into pairing mode (blue light blinking)") : (j.busy ? t("connecting …")
    : (j.msg ? "⚠ " + j.msg : (j.devices.length ? "" : t("no devices yet - press «Search»"))));
  L.textContent = "";
  j.devices.forEach(d => {
    const row = el("div", "row btrow"), used = j.out === "bt:" + d.mac;
    const nm = el("span", "", (d.audio ? "🔊 " : "• ") + d.name + (d.connected ? " · ✓ " + t("connected") : (d.paired ? " · " + t("paired") : "")));
    if (used) nm.style.fontWeight = "700";
    const bs = el("span", "btns"); bs.style.margin = "0"; bs.style.flexWrap = "nowrap";
    const mk = (txt, cls, act) => {
      const x = el("button", cls, txt); x.type = "button"; x.style.padding = "4px 10px";
      x.onclick = async () => {
        x.disabled = true; st.textContent = act === "connect" ? t("connecting …") : "…";
        const r = await post("/api/bt", {action: act, mac: d.mac, lang: LANG});
        await btPoll(); if (window.refreshEnums) refreshEnums(["audio_out"]);
        $("#bt-st").textContent = r.ok ? (act === "connect" ? "✓ " + t("connected - used for the siren and for talking") : "") : "⚠ " + (r.error || "error");
      };
      return x;
    };
    if (!d.connected || !used) bs.appendChild(mk(t("Connect"), "", "connect"));
    if (d.connected) bs.appendChild(mk(t("Disconnect"), "sec", "disconnect"));
    if (d.paired) { const rm = mk("✕", "sec", "remove"); rm.title = t("Remove"); bs.appendChild(rm); }
    row.append(nm, bs); L.appendChild(row);
  });
}

"""


BASE_CSS = r"""
/* nothing may make the page wider than the screen (a long option in a list, a long address ...) */
select,input,textarea{max-width:100%;min-width:0}
/* iPhone / iPad zoom in by themselves when a field with text smaller than 16 px is tapped - so on touch screens fields use 16 px */
@media(pointer:coarse){input:not([type=range]):not([type=checkbox]):not([type=radio]),select,textarea{font-size:16px!important}}
.card,details,.row{min-width:0}

:root{--bg:#0a0e14;--panel:#111822;--panel2:#151e2b;--line:#1f2b3a;--txt:#e8eef5;--mut:#8a9bb0;--acc:#3b8cff;--acc2:#6aa9ff;--red:#ff4d4d;--grn:#3fcf6b;--yel:#e0a526;--blu:#5aa9ff;--org:#f59a4a;--pur:#b794f6;--field:#0c121a;--btn2:#1a2433;--hdr:rgba(10,14,20,.8);--glow:rgba(59,140,255,.13);--shadow:0 1px 2px rgba(0,0,0,.45),0 10px 28px rgba(0,0,0,.22);--r:14px}
body.light{--bg:#eef2f7;--panel:#ffffff;--panel2:#f8fafc;--line:#d7dfea;--txt:#18212d;--mut:#5a6b80;--acc:#1f6feb;--acc2:#4d8ff5;--red:#d1242f;--grn:#1a8f3c;--yel:#9a6700;--blu:#0969da;--org:#bc4c00;--pur:#8250df;--field:#f2f5fa;--btn2:#e3e9f2;--hdr:rgba(238,242,247,.85);--glow:rgba(31,111,235,.10);--shadow:0 1px 2px rgba(20,30,50,.08),0 10px 28px rgba(20,30,50,.08)}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{scrollbar-width:thin;scrollbar-color:var(--line) transparent}
body{margin:0;color:var(--txt);font:14px/1.45 Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;min-height:100vh;
  background:radial-gradient(1100px 480px at 75% -8%,var(--glow),transparent 70%),var(--bg);background-attachment:fixed}
header{position:sticky;top:0;z-index:30;display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;padding:10px 16px;
  background:var(--hdr);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
header h1{font-size:17px;margin:0 8px 0 0;font-weight:700;letter-spacing:.2px;display:flex;align-items:center;gap:9px}
/* little extra */
.mw-marmot{position:absolute;left:50%;bottom:0;z-index:70;width:180px;margin-left:-90px;transform:translateY(105%);transition:transform .4s cubic-bezier(.2,1.4,.4,1);pointer-events:none}
.mw-marmot.up{transform:translateY(1%)}
.mw-marmot > svg{display:block;width:180px;height:180px;filter:drop-shadow(0 4px 10px rgba(0,0,0,.5))}
.mw-marmot .bub{position:absolute;bottom:160px;left:50%;transform:translateX(-50%) scale(.6);opacity:0;transition:.25s .3s;white-space:nowrap;
  background:#fff;color:#1b2430;font:700 14px system-ui,sans-serif;padding:8px 12px;border-radius:14px;box-shadow:0 6px 18px rgba(0,0,0,.35)}
.mw-marmot .bub::after{content:"";position:absolute;left:50%;bottom:-7px;margin-left:-7px;border:7px solid transparent;border-top-color:#fff;border-bottom:0}
.mw-marmot.up .bub{opacity:1;transform:translateX(-50%) scale(1)}
.mw-marmot .hrt{position:absolute;left:52px;top:104px;width:76px;height:74px;display:grid;place-items:center;pointer-events:auto;touch-action:none;cursor:grab;perspective:200px}
.mw-marmot .hrt svg{width:34px;height:31px;animation:mwHrt 1.6s linear infinite;filter:drop-shadow(0 0 6px rgba(255,90,140,.8))}
@keyframes mwHrt{0%{transform:rotateY(0) scale(1)}25%{transform:rotateY(90deg) scale(1.12)}50%{transform:rotateY(180deg) scale(1)}75%{transform:rotateY(270deg) scale(1.12)}100%{transform:rotateY(360deg) scale(1)}}
.mw-marmot.drawing .hrt svg{animation-duration:.6s}
.mw-trail{position:fixed;left:0;top:0;width:100vw;height:100vh;z-index:2147483600;pointer-events:none}
.mw-burst{position:fixed;z-index:2147483601;pointer-events:none}
.mw-burst svg{position:absolute;inset:0;width:100%;height:100%;transition:transform .75s cubic-bezier(.2,.7,.3,1),opacity .75s ease-in}
/* 1 August (Swiss national day): a small Swiss cross and sparks next to the name */
body.aug1 header h1{position:relative}
body.aug1 header h1::after{content:"";flex:none;width:18px;height:18px;border-radius:3px;margin-left:2px;
  background:linear-gradient(#fff,#fff) center/11px 3.6px no-repeat,linear-gradient(#fff,#fff) center/3.6px 11px no-repeat,#e8112d;box-shadow:0 0 10px rgba(232,17,45,.6)}
.aug-spark{position:absolute;width:5px;height:5px;border-radius:50%;pointer-events:none;animation:augspark 1.6s ease-out infinite;opacity:0}
@keyframes augspark{0%{opacity:0;transform:translate(0,0) scale(.4)}15%{opacity:1}100%{opacity:0;transform:translate(var(--dx),var(--dy)) scale(1)}}
#langmenu{position:fixed;z-index:90;display:flex;flex-direction:column;min-width:160px;padding:6px;border-radius:12px;background:var(--panel);
  border:1px solid var(--line);box-shadow:0 12px 32px rgba(0,0,0,.45)}
#langmenu button{background:none;border:0;color:var(--txt);text-align:left;padding:9px 12px;border-radius:8px;font:inherit;font-size:14px;cursor:pointer}
#langmenu button:hover{background:var(--field)}#langmenu button.on{background:var(--acc);color:#fff}
header h1::before{content:"";flex:none;width:28px;height:28px;border-radius:8px;background:var(--mw-icon,url(/icon-192.png)) center/cover;
  box-shadow:0 2px 10px rgba(232,89,12,.35)}      /* the app icon (orange camera head) instead of a dot */
.nav{display:flex;gap:2px;background:var(--field);border:1px solid var(--line);border-radius:11px;padding:3px;max-width:100%;overflow-x:auto;scrollbar-width:none}
.nav::-webkit-scrollbar{display:none}
.nav a{padding:5px 13px;border-radius:8px;color:var(--mut);text-decoration:none;font-weight:600;font-size:13px;white-space:nowrap}
.nav a:hover{color:var(--txt)}.nav a.on{background:var(--acc);color:#fff;box-shadow:0 2px 10px var(--glow)}
.badge{display:inline-flex;align-items:center;gap:6px;padding:3px 11px;border:1px solid var(--line);border-radius:99px;font-size:12px;font-weight:600;color:var(--mut);background:var(--field);white-space:nowrap}
.badge.red{color:var(--red);border-color:var(--red)}.badge.blu{color:var(--blu);border-color:var(--blu)}
.badge.yel{color:var(--yel);border-color:var(--yel)}.badge.grn{color:var(--grn);border-color:var(--grn)}
.badge.org{color:var(--org);border-color:var(--org)}
.hdr-ctl{margin-left:auto;display:flex;gap:6px;align-items:center}
.hdr-ctl button,.hdr-ctl .btn{padding:5px 11px;font-size:13px}
/* header icon buttons: all the same size, drawn icons instead of characters (look the same on every device) */
.hdr-ctl button.ic{width:38px;height:34px;padding:0!important;display:inline-flex;align-items:center;justify-content:center;flex:none}
.hdr-ctl button.ic svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
header .badge{min-height:30px}
.chips{display:contents}
@media(min-width:761px){
  header .nav{margin-right:auto}
  header .nav~.hdr-ctl{margin-left:4px;padding-left:10px;border-left:1px solid var(--line)}
  /* main page: title, tabs and buttons in the first line, the status badges in their own line below the tabs
     (so the buttons and tabs never jump when a badge appears or disappears) */
  header:has(.chips){display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:8px 12px}
  header:has(.chips)>h1{grid-column:1;grid-row:1;margin:0}
  header:has(.chips)>.nav{grid-column:2;grid-row:1;justify-self:start;margin:0;max-width:100%}
  header:has(.chips)>.hdr-ctl{grid-column:3;grid-row:1;margin-left:0}
  .chips{grid-column:2/4;grid-row:2;display:flex;flex-wrap:nowrap;align-items:center;gap:8px;min-width:0;overflow-x:auto;scrollbar-width:none}
  .chips::-webkit-scrollbar{display:none}.chips>.badge{flex:none}
  body.hdr-small header:has(.chips){row-gap:4px}
}
@media(min-width:761px) and (max-width:1099px){
  /* narrow tablet: tabs in their own line over the full width, badges below */
  header:has(.chips)>.nav{grid-column:1/4;grid-row:2;justify-self:stretch}
  header:has(.chips)>.nav a{flex:1 1 auto;text-align:center}
  .chips{grid-column:1/4;grid-row:3}
}
button,.btn{background:var(--acc);color:#fff;border:0;border-radius:9px;padding:8px 14px;font:inherit;font-weight:600;cursor:pointer;text-decoration:none;text-align:center;display:inline-block;transition:filter .12s,transform .06s,background .15s}
button:hover,.btn:hover{filter:brightness(1.1)}
button:active,.btn:active{transform:translateY(1px);filter:brightness(1.2)}
button:focus-visible,.btn:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--acc2);outline-offset:2px}
button.sec,.btn.sec{background:var(--btn2);color:var(--txt);border:1px solid var(--line)}
button.red{background:var(--red)}
button:disabled{opacity:.5;cursor:default;filter:none;transform:none}
.card{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:var(--r);padding:14px;margin-bottom:14px;box-shadow:var(--shadow)}
details.card>summary{margin:0;font-size:11px;letter-spacing:.09em;color:var(--mut);font-weight:700;text-transform:uppercase;cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center;user-select:none}
details.card>summary::after{content:"▾";font-size:13px;transition:transform .15s}
details.card:not([open])>summary::after{transform:rotate(-90deg)}
details.card[open]>summary{margin-bottom:10px}
details.card>summary::-webkit-details-marker{display:none}
select,input[type=text],input[type=number],input[type=date],input[type=time],input[type=password]{background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:6px 9px;font:inherit;color-scheme:dark;max-width:100%}
body.light select,body.light input[type=date],body.light input[type=time]{color-scheme:light}
select:focus,input:focus{outline:none;border-color:var(--acc);box-shadow:0 0 0 3px var(--glow)}
input[type=range]{width:100%;accent-color:var(--acc);margin:4px 0 0}
input[type=checkbox],input[type=radio]{accent-color:var(--acc)}
input.sw{appearance:none;-webkit-appearance:none;width:42px;height:24px;border-radius:12px;background:#2a3542;position:relative;cursor:pointer;flex:none;outline:none;transition:background .15s;margin:0;border:0;padding:0}
input.sw::after{content:"";position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:left .15s;box-shadow:0 1px 3px rgba(0,0,0,.4)}
input.sw:checked{background:var(--acc)}input.sw:checked::after{left:21px}
body.light input.sw{background:#c4ccd8}body.light input.sw:checked{background:var(--acc)}
.mut{color:var(--mut);font-size:12px}
.row{display:flex;justify-content:space-between;align-items:center;gap:10px}
.err{color:var(--red);font-size:12px;min-height:16px}
.vh{display:none!important}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.btns>*{flex:1 1 auto}
h1 .ver{font-size:.62em;font-weight:600;color:var(--mut);margin-left:4px;letter-spacing:0}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{border-radius:0;padding:5px 11px;font-size:12px;background:transparent;color:var(--mut)}
#lock-btn.lock-on{background:var(--yel);color:#000;border-color:var(--yel);font-weight:700}
.night-btn{display:flex;flex-direction:column;align-items:flex-start;gap:2px;width:100%;margin:8px 0 4px;padding:12px 14px;font-size:16px;font-weight:700;text-align:left;
  background:linear-gradient(135deg,#2b3a6b,#4a3a8a);color:#fff;border-radius:12px}
.night-btn small{font-size:12px;font-weight:500;opacity:.85}
#night-res{margin:6px 0 8px;padding:8px 10px;border:1px solid var(--line);border-radius:10px;font-size:13px}
#night-res .nr-ok{color:var(--grn)}#night-res .nr-h{font-weight:700;margin-top:6px}#night-res .nr-miss{margin-top:4px}
.simplebar{margin:0 0 12px}.simplebar .seg{display:flex}.simplebar .seg button{flex:1;padding:8px;font-size:13px}.simplebar .mut{font-size:12px;margin-top:4px}
.hrow{display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid var(--line)}.hrow:last-child{border-bottom:0}
.hdot{flex:0 0 12px;height:12px;border-radius:50%;margin-top:4px;background:var(--mut)}
.h-ok .hdot{background:var(--grn)}.h-warn .hdot{background:var(--yel)}.h-bad .hdot{background:var(--red);box-shadow:0 0 8px var(--red)}.h-off .hdot{background:transparent;border:2px solid var(--mut);box-sizing:border-box}
.hbody{flex:1;min-width:0}.htop{display:flex;gap:8px;flex-wrap:wrap;align-items:baseline}.htop b{font-size:14px}.htop .mut{font-size:12px}
.htip{font-size:12px;margin-top:2px;color:var(--txt);opacity:.85}
.msghint{font-size:12px;margin:8px 0 2px}
.msgcard{border:1px solid var(--line);border-radius:12px;padding:10px;margin-top:10px;background:var(--field)}
details.msgcard{border-top:1px solid var(--line);padding-top:10px}details.msgcard>summary{font-size:14px}
details.msgcard>summary .msgsum{flex:1;text-align:right;margin-right:10px;font-size:12px;font-weight:500}
.msghead{font-weight:700;margin-bottom:6px}
.msgrow{display:grid;grid-template-columns:44px 1fr auto;gap:6px;align-items:start;margin-top:6px}.msgrow>.mut{font-size:12px;padding-top:9px}
.msginp{width:100%;box-sizing:border-box;font:inherit;font-size:14px}
textarea.msginp{background:var(--bg);color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:8px 10px;line-height:1.35}
textarea.msginp:focus{outline:none;border-color:var(--acc);box-shadow:0 0 0 3px var(--glow)}textarea.msginp::placeholder{color:var(--mut)}textarea.msginp{resize:vertical;min-height:52px}
.msgstd{padding:6px 10px}
.msgchips{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}.msgchips button{padding:3px 9px;font-size:12px;border-radius:999px}
.msgprev{margin-top:8px;padding:8px 10px;border-radius:10px;background:var(--panel);border:1px dashed var(--line);font-size:13px}
.msgprev b{display:block;margin-top:2px}
.locbox .lseg{display:flex;margin:6px 0 4px}.locbox .lseg button{flex:1;padding:8px 6px;font-size:13px}
.locbox .ltools{gap:6px;margin:6px 0 0}.locbox .ltools input{flex:1;min-width:0}.locbox .ltools button{flex:0 0 auto}
.lmap{position:relative;height:240px;margin-top:8px;overflow:hidden;border-radius:10px;touch-action:none;cursor:grab;user-select:none;border:1px solid var(--line);
  background:#22313b repeating-linear-gradient(0deg,transparent 0 63px,rgba(255,255,255,.07) 63px 64px),repeating-linear-gradient(90deg,transparent 0 63px,rgba(255,255,255,.07) 63px 64px)}
.lmap.pick{cursor:crosshair}
.lmap .mtiles{position:absolute;inset:0}.lmap .mtiles img{position:absolute;width:256px;height:256px;max-width:none;pointer-events:none}
.lmap .lpin{position:absolute;transform:translate(-50%,-100%);font-size:30px;line-height:1;pointer-events:none;filter:drop-shadow(0 2px 3px rgba(0,0,0,.6));z-index:2}
.lmap .mzoom{position:absolute;right:6px;top:6px;display:flex;flex-direction:column;gap:5px;z-index:3}.lmap .mzoom button{width:34px;height:34px;padding:0;font-size:17px}
.lmap .mattr{position:absolute;right:3px;bottom:2px;font-size:10px;background:rgba(255,255,255,.8);color:#333;padding:0 4px;border-radius:3px;z-index:3}.lmap .mattr a{color:#333}
.locbox .lhint{font-size:12px;margin-top:4px}
.seg button.sel-off{background:var(--mut);color:#fff}.seg button.sel-on{background:var(--grn);color:#fff}.seg button.sel-auto{background:var(--acc);color:#fff}
::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-thumb{background:var(--line);border-radius:6px}
#toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:var(--panel);border:1px solid var(--line);color:var(--txt);padding:9px 16px;border-radius:10px;box-shadow:var(--shadow);z-index:90;font-weight:600;opacity:0;pointer-events:none;transition:opacity .2s}
#toast.on{opacity:1}
#hdr-show{display:none;position:fixed;top:0;left:50%;transform:translateX(-50%);z-index:70;padding:1px 22px 3px;opacity:.85;
  border-radius:0 0 10px 10px;border-top:0;box-shadow:var(--shadow);font-size:12px;line-height:1.2}
body.hdrhidden header{display:none}body.hdrhidden #hdr-show{display:block}body.videoonly #hdr-show{display:none!important}
body.hdrhidden .sndpop{top:44px}
@keyframes spin{to{transform:rotate(360deg)}}#btn-reload.spin svg{animation:spin .9s linear infinite}
.sndbtn{position:relative}.sndbtn.on{background:var(--acc);color:#fff;border-color:transparent}
.sndbtn.warn::after{content:"";position:absolute;top:3px;right:3px;width:8px;height:8px;border-radius:50%;background:var(--yel)}
.sndpop{position:fixed;top:58px;right:12px;z-index:80;width:300px;max-width:calc(100vw - 24px)}
.sndpop .row{margin:7px 0}.sndpop .sndhead{font-size:11px;letter-spacing:.09em;color:var(--mut);font-weight:700;text-transform:uppercase;margin-bottom:6px}
@keyframes alarmflash{0%,60%{box-shadow:inset 0 0 0 4px var(--red)}100%{box-shadow:inset 0 0 0 0 transparent}}
body.alarmflash{animation:alarmflash 1.6s ease-out 2}
@media(max-width:430px){.nav a{padding:5px 7px;font-size:12.5px}}
@media(max-width:700px){header{padding:8px 10px;gap:5px 6px}.nav a{padding:5px 9px}
  header h1{font-size:15px}.badge{font-size:11px;padding:2px 8px}header .badge{min-height:26px}.hdr-ctl button,.hdr-ctl .btn{padding:4px 9px;font-size:12px}
  .hdr-ctl button.ic{width:34px;height:30px}.hdr-ctl button.ic svg{width:17px;height:17px}}
"""

