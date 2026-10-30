#@ Motion Watch – Teil 460: Web: Seite Werkzeuge. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
TOOLS_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye - Tools</title>
<style>
/*BASECSS*/
main.tools{display:grid;grid-template-columns:270px minmax(0,1fr);gap:20px;max-width:1240px;margin:0 auto;padding:20px 16px 40px;align-items:start}
main.tools.solo{grid-template-columns:minmax(0,1fr);max-width:900px}main.tools.solo .tlist,main.tools.solo .thd .back{display:none!important}
main.tools.solo .tpane{display:block!important}
.tlist{position:sticky;top:76px;display:flex;flex-direction:column;gap:1px;max-height:calc(100vh - 96px);overflow:auto;padding-right:2px}
.tm{border:1px solid var(--line);border-radius:12px;padding:12px;margin:0 0 14px;background:var(--panel)}
.tm.on{border-color:var(--yel)}
.tm-h{display:flex;justify-content:space-between;gap:8px;align-items:baseline}.tm-h .mut{white-space:nowrap;margin:0}.tm-h b{font-weight:600;font-size:14px}
.tm .mut{font-size:12px;margin-top:4px;line-height:1.45}
.tm-a{display:flex;gap:8px;align-items:center;margin-top:10px;flex-wrap:wrap}.tm-a select{flex:none;width:auto}.tm-a button{flex:1;padding:7px 10px;font-size:13px}
#tm-until{font-size:13px;color:var(--yel);flex-basis:100%}
.tlg{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--mut);font-weight:600;margin:16px 10px 6px}
.tlg:first-child{margin-top:0}
.tli{display:flex;align-items:center;gap:11px;width:100%;background:none;border:0;border-radius:9px;padding:8px 10px;color:var(--txt);text-align:left;font-weight:400;cursor:pointer}
.tli:hover{background:var(--field);filter:none}
.tli.on{background:var(--btn2)}
.tli .tln{display:flex;flex-direction:column;min-width:0;flex:1}
.tli .tln b{font-weight:500;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tsum{font-size:12px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-height:0}
.tsum:empty{display:none}
/* 2.95.71: like every menu - symbol left, name, arrow right; symbol and arrow green while the tool's function is on / ok
   (yellow / red = to watch / a problem); the former dot became the arrow */
.tdot{flex:none;font-style:normal;color:var(--mut);font-size:17px;line-height:1;opacity:.75}.tdot::after{content:"›"}
.tdot.ok{color:var(--grn);opacity:1}.tdot.warn{color:var(--yel);opacity:1}.tdot.bad{color:var(--red);opacity:1}
.tli:has(.tdot.ok) svg.tico{color:var(--grn)}.tli:has(.tdot.warn) svg.tico{color:var(--yel)}.tli:has(.tdot.bad) svg.tico{color:var(--red)}
svg.tico{flex:none;width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;color:var(--mut)}
.tli.on svg.tico{color:var(--txt)}
.tpane{min-width:0}
.tool{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px 22px 22px}
.thd{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding-bottom:14px;margin-bottom:14px;border-bottom:1px solid var(--line)}
.tht{display:flex;align-items:center;gap:10px;flex:1;min-width:0}
.tht svg.tico{width:22px;height:22px;color:var(--txt)}
.tht h2{margin:0;font-size:18px;font-weight:600}
.thd .back{display:none}
.tact{display:flex;gap:8px;flex-wrap:wrap}
.tact button,.tact .btn{padding:7px 16px;font-size:13px}
.tbd>*+*{margin-top:12px}
.tbd .mut{font-size:13px;line-height:1.5}
.rs-steps{display:flex;gap:6px;flex-wrap:wrap}.rs-steps>span{font-size:12px;padding:5px 10px;border-radius:999px;border:1px solid var(--line);color:var(--mut);cursor:pointer}
.rs-steps>span.on{background:var(--acc,#3b8cff);border-color:var(--acc,#3b8cff);color:#fff}.rs-steps>span.done{color:var(--grn);border-color:var(--grn)}
.rs-live img{width:100%;max-height:52vh;object-fit:contain;border-radius:12px;background:#000;display:block}
.rs-pad button{flex:1;min-width:48px}
.rs-prog{height:10px;border-radius:6px;background:var(--field);overflow:hidden}.rs-prog i{display:block;height:100%;width:0;background:var(--acc,#3b8cff);transition:width .4s}
.rs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:6px}.rs-grid img{width:100%;border-radius:8px;display:block}
.rs-grid figure{margin:0}.rs-grid figcaption{font-size:11px;color:var(--mut);text-align:center}
.rs-rep{border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin:6px 0;cursor:pointer;display:flex;justify-content:space-between;gap:8px;align-items:center}
.rs-rep.sel{border-color:var(--acc,#3b8cff)}.rs-rep b{font-weight:600}
.rs-pair{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:8px 0}.rs-pair img{width:100%;border-radius:8px;display:block}.rs-pair div{font-size:11px;color:var(--mut)}
.rs-ch{font-size:13px;margin:2px 0}.rs-ch.gone{color:#ff3b30;font-weight:700}.rs-ch.ok{color:var(--grn)}
.rs-grid figure{cursor:pointer;position:relative}.rs-grid figure i{position:absolute;right:4px;top:4px;font-style:normal;font-size:11px;background:rgba(10,14,20,.8);border-radius:6px;padding:1px 5px}
#rs-ed{position:fixed;inset:0;z-index:90;background:rgba(5,8,12,.94);display:flex;flex-direction:column;padding:12px;gap:10px;overflow:auto}
#rs-ed .cv{position:relative;align-self:center;max-width:min(100%,1100px);width:100%;touch-action:none;user-select:none}#rs-ed .cv img{width:100%;display:block;border-radius:8px;pointer-events:none}
#rs-ed .bx{position:absolute;border:2px dashed #3fcf6b;background:rgba(63,207,107,.12)}#rs-ed .bx span{position:absolute;left:0;top:-20px;font-size:12px;background:#3fcf6b;color:#000;border-radius:4px;padding:0 4px;white-space:nowrap}
#rs-ed .bx.drag{border-color:#ffd166}.rs-ch.missing{color:#ff6b6b}.rs-ch.new{color:#4fa3ff}.rs-ch.changed{color:#f5a623}
.opt{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:11px 0;border-top:1px solid var(--line);font-size:14px;cursor:pointer}
.opt+.opt{margin-top:0}
.tbd .opt + :not(.opt){margin-top:12px}
.trow{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:14px}
.trow input[type=number]{width:84px;flex:none}
.tl{width:100%;border-collapse:collapse;font-size:13px}
.tl th{color:var(--mut);font-weight:500;font-size:12px;text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
.tl td{padding:8px;border-bottom:1px solid var(--line);vertical-align:middle}
.tl tr:last-child td{border-bottom:0}
.tl input[type=text]{padding:4px 8px;font-size:13px;width:120px}
.tscroll{max-height:420px;overflow:auto;border:1px solid var(--line);border-radius:10px}
.tscroll:has(table:empty){display:none}
.newdev{color:var(--yel);font-weight:500}
.lv{display:flex;gap:10px;align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--line);font-size:14px}
.lv:last-of-type{border-bottom:0}
.lv i.lvl{flex:none;width:8px;height:8px;border-radius:50%;margin-top:6px;background:var(--mut)}
.lv i.ok{background:var(--grn)}.lv i.warn{background:var(--yel)}.lv i.bad{background:var(--red)}
.big{font-size:24px;font-weight:600;line-height:1.2}
.bar{height:6px;border-radius:3px;background:var(--field);overflow:hidden}
.bar>div{height:100%;background:var(--acc);width:0;transition:width .3s}
.spark{width:100%;height:56px;display:block;color:var(--acc)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;font-size:14px}
.kv span:nth-child(odd){color:var(--mut)}
.kv:empty{display:none}
.pw label{display:flex;gap:10px;align-items:center;padding:7px 0;font-size:14px;border-bottom:1px solid var(--line)}
.pw label{cursor:pointer;padding:9px 0}.pw label b{margin-left:auto;font-weight:500;color:var(--mut);font-size:13px}
.chans{display:flex;gap:4px;align-items:flex-end;height:56px}
.chans div{flex:1;background:var(--line);border-radius:3px 3px 0 0;min-height:2px}
.chans div.best{background:var(--acc)}
.chans:empty,.chl:empty{display:none}
.chl{display:flex;gap:4px;font-size:10px;color:var(--mut);margin-top:4px!important}.chl span{flex:1;text-align:center}
.warnbox{border-left:3px solid var(--yel);padding:4px 12px;font-size:13px;color:var(--mut)}
.adp{padding:10px 0;border-top:1px solid var(--line);font-size:14px}.adp:first-child{border-top:0}
.adp-h{display:flex;justify-content:space-between;gap:10px}.adp-h b{font-weight:600}
@media(max-width:760px){
  main.tools{display:block;padding:12px 12px 32px}
  .tlist{position:static;max-height:none;overflow:visible;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:6px}
  .tli{padding:12px 10px}
  .tlg{margin:14px 10px 4px}
  body.picked .tlist{display:none}
  body:not(.picked) .tpane{display:none}
  .tool{padding:14px}
  .thd .back{display:block;flex:0 0 100%;text-align:left;background:none;border:0;color:var(--acc2);padding:0 0 6px;font-size:14px;font-weight:500}
  .tht h2{font-size:17px}
}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main class="tools">
<nav class="tlist" aria-label="Tools">
  <div class="tm" id="tm">
    <div class="tm-h"><b data-i18n="Full power for the tools">Full power for the tools</b><span class="mut" id="tm-cpu"></span></div>
    <div class="mut" id="tm-note" data-i18n="tm-note">tm-note</div>
    <div class="tm-a" id="tm-off"><select id="tm-min"><option value="10">10 min</option><option value="30" selected>30 min</option><option value="60">60 min</option><option value="120">120 min</option></select>
      <button type="button" class="sec" onclick="toolmode(+$('#tm-min').value)" data-i18n="Pause MoveEye">Pause MoveEye</button></div>
    <div class="tm-a" id="tm-on" hidden><span id="tm-until"></span><button type="button" onclick="toolmode(0)" data-i18n="Resume now">Resume now</button></div>
  </div>
  <div class="tlg" data-i18n="Network and internet">Network and internet</div>
  <button type="button" class="tli" data-k="net" onclick="pick('net')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="5" rx="1"/><rect x="3" y="16" width="6" height="5" rx="1"/><rect x="15" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M6 16v-4h12v4"/></svg><span class="tln"><b data-i18n="Network scanner">Network scanner</b><span class="tsum" id="s-net"></span></span><i class="tdot" id="d-net"></i></button>
  <button type="button" class="tli" data-k="pres" onclick="pick('pres')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></svg><span class="tln"><b data-i18n="Am I at home?">Am I at home?</b><span class="tsum" id="s-pres"></span></span><i class="tdot" id="d-pres"></i></button>
  <button type="button" class="tli" data-k="nettest" onclick="pick('nettest')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 9.5a15 15 0 0 1 20 0M5 13a10 10 0 0 1 14 0"/><path d="M12 20l3.5-6"/><circle cx="12" cy="20" r="1.3"/></svg><span class="tln"><b data-i18n="Network check of the players">Network check of the players</b><span class="tsum" id="s-nettest"></span></span><i class="tdot" id="d-nettest"></i></button>
  <button type="button" class="tli" data-k="info" onclick="pick('info')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><circle cx="12" cy="7.5" r="1"/></svg><span class="tln"><b data-i18n="Product page for guests">Product page for guests</b><span class="tsum" id="s-info"></span></span><i class="tdot" id="d-info"></i></button>
  <button type="button" class="tli" data-k="speed" onclick="pick('speed')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/></svg><span class="tln"><b data-i18n="Internet test">Internet test</b><span class="tsum" id="s-speed"></span></span><i class="tdot" id="d-speed"></i></button>
  <a class="tli" data-k="sec" href="/settings?open=grp:security" style="text-decoration:none;color:inherit"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg><span class="tln"><b data-i18n="Security check">Security check</b><span class="tsum" data-i18n="now in Settings → Security">now in Settings → Security</span></span><i class="tdot"></i></a>
  <div class="tlg" data-i18n="Wi-Fi">Wi-Fi</div>
  <button type="button" class="tli" data-k="dual" onclick="pick('dual')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 9.5a15 15 0 0 1 20 0M5 13a10 10 0 0 1 14 0M8.5 16.5a5 5 0 0 1 7 0"/><circle cx="12" cy="20" r="1"/></svg><span class="tln"><b data-i18n="Wi-Fi adapters and repeater">Wi-Fi adapters and repeater</b><span class="tsum" id="s-dual"></span></span><i class="tdot" id="d-dual"></i></button>
  <button type="button" class="tli" data-k="guard" onclick="pick('guard')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg><span class="tln"><b data-i18n="Wi-Fi guard">Wi-Fi guard</b><span class="tsum" id="s-guard"></span></span><i class="tdot" id="d-guard"></i></button>
  <button type="button" class="tli" data-k="wifi" onclick="pick('wifi')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20v-4M9 20v-8M14 20V8M19 20V4"/></svg><span class="tln"><b data-i18n="Wi-Fi around">Wi-Fi around</b><span class="tsum" id="s-wifi"></span></span><i class="tdot" id="d-wifi"></i></button>
  <div class="tlg" data-i18n="Device tests">Device tests</div>
  <button type="button" class="tli" data-k="focus" onclick="pick('focus')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg><span class="tln"><b data-i18n="Focus assistant">Focus assistant</b><span class="tsum" id="s-focus"></span></span><i class="tdot" id="d-focus"></i></button>
  <button type="button" class="tli" data-k="refscan" onclick="pick('refscan')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/><circle cx="12" cy="12" r="3.5"/><path d="M12 6v2M12 16v2M6 12h2M16 12h2"/></svg><span class="tln"><b data-i18n="Reference scan">Reference scan</b><span class="tsum" id="s-refscan"></span></span><i class="tdot" id="d-refscan"></i></button>
  <a class="tli" data-k="servo" href="/servo#test" style="text-decoration:none;color:inherit"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v18M3 12h18M9 6l3-3 3 3M9 18l3 3 3-3M6 9l-3 3 3 3M18 9l3 3-3 3"/></svg><span class="tln"><b data-i18n="Servos">Servos</b><span class="tsum" id="s-servo" data-i18n="Positions, test, diagnosis, Not-Aus">Positions, test, diagnosis, Not-Aus</span></span><i class="tdot" id="d-servo"></i></a>
  <button type="button" class="tli" data-k="audio" onclick="pick('audio')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12"/></svg><span class="tln"><b data-i18n="Speaker and microphone">Speaker and microphone</b><span class="tsum" id="s-audio"></span></span><i class="tdot" id="d-audio"></i></button>
  <button type="button" class="tli" data-k="sd" onclick="pick('sd')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h8l4 4v14H7z"/><path d="M10 7v3M13 7v3M16 8v2"/></svg><span class="tln"><b data-i18n="Memory card test">Memory card test</b><span class="tsum" id="s-sd"></span></span><i class="tdot" id="d-sd"></i></button>
  <button type="button" class="tli" data-k="bt" onclick="pick('bt')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10-5 4V3l5 4L7 17"/></svg><span class="tln"><b data-i18n="Bluetooth scanner">Bluetooth scanner</b><span class="tsum" id="s-bt"></span></span><i class="tdot" id="d-bt"></i></button>
  <button type="button" class="tli" data-k="usb" onclick="pick('usb')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2v15"/><path d="M9 5l3-3 3 3"/><path d="M12 13l-5-3V7"/><path d="M12 11l5-3V6"/><rect x="5.5" y="5" width="3" height="2.5"/><circle cx="17" cy="5" r="1.4"/><circle cx="12" cy="19" r="2.5"/></svg><span class="tln"><b data-i18n="USB devices">USB devices</b><span class="tsum" id="s-usb"></span></span><i class="tdot" id="d-usb"></i></button>
  <button type="button" class="tli" data-k="party" onclick="pick('party')" hidden><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="8" cy="8" r="1.4"/><circle cx="16" cy="8" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="8" cy="16" r="1.4"/><circle cx="16" cy="16" r="1.4"/></svg><span class="tln"><b data-i18n="Game corner">Game corner</b><span class="mut" id="s-party"></span></span><i class="tdot" id="d-party"></i></button>
  <button type="button" class="tli" data-k="helper" onclick="pick('helper')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/><path d="M8 10h2l1-2 2 4 1-2h2"/></svg><span class="tln"><b data-i18n="AI helper (PC)">AI helper (PC)</b><span class="tsum" id="s-helper"></span></span><i class="tdot" id="d-helper"></i></button>
  <div class="tlg" data-i18n="Power and help">Power and help</div>
  <a class="tli" href="/almanach/" target="_blank" style="text-decoration:none;color:inherit"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5M8 7h7M8 11h7"/></svg><span class="tln"><b data-i18n="Survival almanac">Survival almanac</b><span class="tsum" data-i18n="tips for camping, to look up or read in the evening">tips for camping, to look up or read in the evening</span></span><i class="tdot" id="d-alm"></i></a>
  <button type="button" class="tli" data-k="pow" onclick="pick('pow')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="7" width="16" height="10" rx="2"/><path d="M21 11v2M7 10v4M11 10v4"/></svg><span class="tln"><b data-i18n="Power calculator">Power calculator</b><span class="tsum" id="s-pow"></span></span><i class="tdot" id="d-pow"></i></button>
  <a class="tli" id="t-dev" href="/dev" style="text-decoration:none;color:inherit;display:none"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h12"/><circle cx="19" cy="18" r="2"/></svg><span class="tln"><b data-i18n="Developer">Developer</b><span class="tsum" data-i18n="own network, read-only">own network, read-only</span></span><span class="tdot"></span></a>
  <button type="button" class="tli" data-k="diag" onclick="pick('diag')"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6z"/><path d="M8 14h2l1.5-3 2 5 1.5-2H16"/></svg><span class="tln"><b data-i18n="Diagnosis package">Diagnosis package</b><span class="tsum" id="s-diag"></span></span><i class="tdot" id="d-diag"></i></button>
</nav>
<div class="tpane">
  <section class="tool" id="c-refscan" data-k="refscan" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/><circle cx="12" cy="12" r="3.5"/><path d="M12 6v2M12 16v2M6 12h2M16 12h2"/></svg><h2 data-i18n="Reference scan">Reference scan</h2></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="refscan-note">refscan-note</div>
    <div class="rs-steps"><span data-n="1">1 · <span data-i18n="Set up">Set up</span></span><span data-n="2">2 · <span data-i18n="Settings">Settings</span></span><span data-n="3">3 · <span data-i18n="Scan">Scan</span></span><span data-n="4">4 · <span data-i18n="Compare">Compare</span></span></div>
    <div class="rs-pane" data-p="1">
      <div class="mut" data-i18n="rs-setup">rs-setup</div>
      <div class="rs-live"><img id="rs-live" alt=""></div>
      <div class="trow rs-pad"><button type="button" class="sec" onclick="rsMove('left')">◀</button><button type="button" class="sec" onclick="rsMove('up')">▲</button><button type="button" class="sec" onclick="rsMove('down')">▼</button><button type="button" class="sec" onclick="rsMove('right')">▶</button><button type="button" class="sec" onclick="rsMove('center')" data-i18n="Middle">Middle</button></div>
      <div class="trow"><button type="button" onclick="rsStep(2)"><span data-i18n="Next">Next</span> ›</button></div>
    </div>
    <div class="rs-pane" data-p="2" hidden>
      <div class="mut" data-i18n="rs-settings">rs-settings</div>
      <div id="rs-set"></div>
      <div class="mut" id="rs-plan"></div>
      <div class="trow"><button type="button" class="sec" onclick="rsStep(1)">‹ <span data-i18n="Back">Back</span></button><button type="button" onclick="rsStep(3)"><span data-i18n="Next">Next</span> ›</button></div>
    </div>
    <div class="rs-pane" data-p="3" hidden>
      <div class="mut" data-i18n="rs-scan">rs-scan</div>
      <div class="trow"><button type="button" id="rs-scan" onclick="rsGo('scan')">📸 <span data-i18n="Take the reference now">Take the reference now</span></button><button type="button" class="sec" id="rs-stop" onclick="rsGo('stop')" hidden data-i18n="Stop">Stop</button></div>
      <div class="rs-prog" id="rs-prog" hidden><i></i></div><div class="mut" id="rs-msg"></div>
      <div id="rs-ref"></div>
      <div class="trow"><button type="button" class="sec" onclick="rsStep(2)">‹ <span data-i18n="Back">Back</span></button><button type="button" id="rs-to4" onclick="rsStep(4)"><span data-i18n="Next">Next</span> ›</button></div>
    </div>
    <div class="rs-pane" data-p="4" hidden>
      <div class="mut" data-i18n="rs-compare">rs-compare</div>
      <div class="trow"><button type="button" id="rs-cmp" onclick="rsGo('compare')">🔍 <span data-i18n="Compare now">Compare now</span></button><button type="button" class="sec" onclick="rsStep(3)" data-i18n="New reference">New reference</button></div>
      <div class="rs-prog" id="rs-prog2" hidden><i></i></div><div class="mut" id="rs-msg2"></div>
      <div id="rs-opts"></div>
      <h3 data-i18n="Reports">Reports</h3>
      <div id="rs-reps"></div>
      <div id="rs-rep"></div>
      <h3>🖼 <span data-i18n="Panorama report «Missing things»">Panorama report «Missing things»</span></h3>
      <div class="mut" data-i18n="pano-desc">pano-desc</div>
      <div class="trow"><button type="button" class="sec" onclick="rsPano(false)">🖼 <span data-i18n="Make it now (last 24 h)">Make it now (last 24 h)</span></button><button type="button" class="sec" onclick="rsPano(true)">📲 <span data-i18n="Make and send">Make and send</span></button></div>
      <div id="rs-pano"></div>
    </div>
    </div>
  </section>
  <section class="tool" id="c-usb" data-k="usb" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2v15"/><path d="M9 5l3-3 3 3"/><path d="M12 13l-5-3V7"/><path d="M12 11l5-3V6"/><rect x="5.5" y="5" width="3" height="2.5"/><circle cx="17" cy="5" r="1.4"/><circle cx="12" cy="19" r="2.5"/></svg><h2 data-i18n="USB devices">USB devices</h2></div><div class="tact"><button type="button" onclick="usbLoad(true)" data-i18n="Read again">Read again</button></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="usb-note">usb-note</div>
    <div id="usb-sum" class="mut" style="margin:8px 0"></div>
    <div id="usb-box"></div>
    </div>
  </section>
  <section class="tool" id="c-helper" data-k="helper" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/><path d="M8 10h2l1-2 2 4 1-2h2"/></svg><h2 data-i18n="AI helper (PC)">AI helper (PC)</h2></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="helper-note">helper-note</div>
    <div id="hp-box" style="margin-top:10px"></div>
    <label class="opt"><span data-i18n="Let a PC do the AI when one is there">Let a PC do the AI when one is there</span><input type="checkbox" class="sw" id="hp-use" onchange="hpSet({use:this.checked})"></label>
    <details class="sub" style="margin-top:8px"><summary data-i18n="Another PC by hand">Another PC by hand</summary>
      <div class="mut" data-i18n="helper-manual">helper-manual</div>
      <div class="trow" style="margin-top:6px"><input type="text" id="hp-url" placeholder="192.168.1.20" style="flex:2 1 160px"><input type="text" id="hp-code" inputmode="numeric" maxlength="6" placeholder="123456" style="flex:1 1 90px">
      <button type="button" onclick="hpSet({url:$('#hp-url').value, code:$('#hp-code').value})" data-i18n="Save">Save</button></div></details>
    <label class="opt" style="margin-top:8px"><span data-i18n="This MoveEye works as AI helper for others (port 5057)">This MoveEye works as AI helper for others (port 5057)</span><input type="checkbox" class="sw" id="hp-serve" onchange="hpSet({serve:this.checked})"></label>
    </div>
  </section>
  <section class="tool" id="c-info" data-k="info" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><circle cx="12" cy="7.5" r="1"/></svg><h2 data-i18n="Product page for guests">Product page for guests</h2></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="info-note">info-note</div>
    <label class="opt"><span data-i18n="Show the product page to guests in the same Wi-Fi (without login)">Show the product page to guests in the same Wi-Fi (without login)</span><input type="checkbox" class="sw" id="info-on" onchange="infoSet({on:this.checked})"></label>
    <label class="opt" style="display:block"><span data-i18n="Your e-mail address on the page (empty = not shown)">Your e-mail address on the page (empty = not shown)</span>
      <input type="text" inputmode="email" autocomplete="email" id="info-mail" style="width:100%;margin-top:6px" placeholder="name@beispiel.ch" onchange="infoSet({mail:this.value})"></label>
    <div id="info-box" style="margin-top:10px"></div>
    </div>
  </section>
  <section class="tool" id="c-nettest" data-k="nettest" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 9.5a15 15 0 0 1 20 0M5 13a10 10 0 0 1 14 0"/><path d="M12 20l3.5-6"/><circle cx="12" cy="20" r="1.3"/></svg><h2 data-i18n="Network check of the players">Network check of the players</h2></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="How well does every phone reach MoveEye? Each one measures reaction time, jitter, losses, download and upload; MoveEye adds the signal it receives from each phone (at its own Wi-Fi).">How well does every phone reach MoveEye? Each one measures reaction time, jitter, losses, download and upload; MoveEye adds the signal it receives from each phone (at its own Wi-Fi).</div>
    <div id="nt-box" style="margin-top:10px"></div>
    </div>
  </section>
  <section class="tool" id="c-party" data-k="party" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="8" cy="8" r="1.4"/><circle cx="16" cy="8" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="8" cy="16" r="1.4"/><circle cx="16" cy="16" r="1.4"/></svg><h2 data-i18n="Game corner">Game corner</h2></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="party-note">party-note</div>
    <div id="party-box"></div>
    <a class="btn sec" href="/tools#nettest" style="display:inline-block;margin-top:10px">📶 <span data-i18n="Network check of the players">Network check of the players</span></a>
    </div>
  </section>
  <section class="tool" id="c-net" data-k="net" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="5" rx="1"/><rect x="3" y="16" width="6" height="5" rx="1"/><rect x="15" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M6 16v-4h12v4"/></svg><h2 data-i18n="Network scanner">Network scanner</h2></div><div class="tact"><button id="b-net" onclick="run('net')" data-i18n="Scan">Scan</button></div></div>
    <div class="tbd">
    <div class="mut" id="net-info" data-i18n="All devices in your own network (only there).">All devices in your own network (only there).</div>
    <label class="opt"><span data-i18n="Warn me about new devices (push, check every 10 min)">Warn me about new devices (push, check every 10 min)</span><input type="checkbox" class="sw" id="cf-net_watch" onchange="cfg('net_watch',this.checked)"></label>
    <div class="tscroll"><table class="tl" id="net-tab"></table></div>
    </div>
  </section>
  <section class="tool" id="c-pres" data-k="pres" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></svg><h2 data-i18n="Am I at home?">Am I at home?</h2></div></div>
    <div class="tbd">
    <div class="big" id="pres-st">–</div>
    <div class="mut" id="pres-note" data-i18n="pres-note">pres-note</div>
    <label class="opt"><span data-i18n="Automatic: on when my phone is gone">Automatic: on when my phone is gone</span><input type="checkbox" class="sw" id="cf-presence_auto" onchange="cfg('presence_auto',this.checked)"></label>
    <div class="trow"><span data-i18n="When my phone comes back:">When my phone comes back:</span> <select id="cf-presence_back" onchange="cfg('presence_back',this.value)">
      <option value="off" data-i18n="switch the protection off">switch the protection off</option><option value="ask" data-i18n="ask «Is it you?» (person alarms wait)">ask «Is it you?» (person alarms wait)</option>
      <option value="none" data-i18n="nothing (the protection stays on)">nothing (the protection stays on)</option></select></div>
    <div class="trow"><span data-i18n="Gone after">Gone after</span> <input type="number" id="cf-presence_gone_min" min="2" max="120" onchange="cfg('presence_gone_min',+this.value)"> <span data-i18n="minutes">minutes</span></div>
    </div>
  </section>
  <section class="tool" id="c-speed" data-k="speed" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/></svg><h2 data-i18n="Internet test">Internet test</h2></div><div class="tact"><button id="b-speed" onclick="run('speed')" data-i18n="Start">Start</button></div></div>
    <div class="tbd">
    <div class="warnbox" data-i18n="speed-warn">speed-warn</div>
    <div class="kv" id="speed-now"></div>
    <div class="tscroll"><table class="tl" id="speed-tab"></table></div>
    </div>
  </section>
  <section class="tool" id="c-dual" data-k="dual" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 9.5a15 15 0 0 1 20 0M5 13a10 10 0 0 1 14 0M8.5 16.5a5 5 0 0 1 7 0"/><circle cx="12" cy="20" r="1"/></svg><h2 data-i18n="Wi-Fi adapters and repeater">Wi-Fi adapters and repeater</h2></div><div class="tact"><button class="sec" onclick="dualAct('adapters')" data-i18n="Search again">Search again</button></div></div>
    <div class="tbd">
    <div id="du-st" class="big" style="font-size:20px">–</div>
    <div class="mut" id="du-note"></div>
    <div id="du-ads"></div>
    <label class="opt"><span data-i18n="Use a second adapter (repeater)">Use a second adapter (repeater)</span><input type="checkbox" class="sw" id="du-wifi_repeater" onchange="dualRep(this)"></label>
    <label class="opt"><span data-i18n="Internet over the USB stick (better antenna)">Internet over the USB stick (better antenna)</span><input type="checkbox" class="sw" id="du-wifi_swap" onchange="dualSet('wifi_swap',this.checked)"></label>
    <label class="opt"><span data-i18n="Push message when the internet was gone">Push message when the internet was gone</span><input type="checkbox" class="sw" id="du-net_inet_notify" onchange="dualSet('net_inet_notify',this.checked)"></label>
    <svg class="spark" id="du-spark" viewBox="0 0 300 50" preserveAspectRatio="none"><polyline id="du-line" fill="none" stroke="currentColor" stroke-width="2" points=""/></svg>
    <div class="mut" id="du-sig"></div>
    <div id="du-log"></div>
    </div>
  </section>
  <section class="tool" id="c-guard" data-k="guard" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg><h2 data-i18n="Wi-Fi guard">Wi-Fi guard</h2></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="guard-note">guard-note</div>
    <div id="gu-st" class="big" style="font-size:20px">–</div>
    <div class="mut" id="gu-msg"></div>
    <label class="opt"><span data-i18n="Alarm on Wi-Fi jamming (deauthentication attack)">Alarm on Wi-Fi jamming (deauthentication attack)</span><input type="checkbox" class="sw" id="du-wifi_guard" onchange="dualSet('wifi_guard',this.checked)"></label>
    <div class="trow"><span data-i18n="Alarm from">Alarm from</span> <input type="number" id="du-wifi_guard_thr" min="5" max="500" onchange="dualSet('wifi_guard_thr',+this.value)"> <span data-i18n="disconnect frames per minute">disconnect frames per minute</span></div>
    <label class="opt"><span data-i18n="Recognise my marked devices by listening (Am I at home?)">Recognise my marked devices by listening (Am I at home?)</span><input type="checkbox" class="sw" id="du-wifi_presence" onchange="dualSet('wifi_presence',this.checked)"></label>
    <label class="opt"><span data-i18n="Count devices nearby (anonymous, nothing is stored)">Count devices nearby (anonymous, nothing is stored)</span><input type="checkbox" class="sw" id="du-wifi_count" onchange="dualSet('wifi_count',this.checked)"></label>
    <svg class="spark" id="gu-spark" viewBox="0 0 300 50" preserveAspectRatio="none"><polyline id="gu-line" fill="none" stroke="var(--red)" stroke-width="2" points=""/><polyline id="gu-line2" fill="none" stroke="currentColor" stroke-width="1" opacity=".5" points=""/></svg>
    <div class="mut" id="gu-info"></div>
    <div id="gu-alarms"></div>
    </div>
  </section>
  <section class="tool" id="c-wifi" data-k="wifi" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20v-4M9 20v-8M14 20V8M19 20V4"/></svg><h2 data-i18n="Wi-Fi around">Wi-Fi around</h2></div><div class="tact"><button id="b-wifi" onclick="run('wifi')" data-i18n="Scan">Scan</button></div></div>
    <div class="tbd">
    <div id="wifi-best" class="mut" data-i18n="Shows the Wi-Fi networks nearby and the best channel for the own Wi-Fi (hotspot).">Shows the Wi-Fi networks nearby and the best channel for the own Wi-Fi (hotspot).</div>
    <div class="chans" id="wifi-ch"></div><div class="chl" id="wifi-chl"></div>
    <div class="tscroll"><table class="tl" id="wifi-tab"></table></div>
    </div>
  </section>
  <section class="tool" id="c-focus" data-k="focus" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg><h2 data-i18n="Focus assistant">Focus assistant</h2></div><div class="tact"><button id="b-focus" onclick="focusToggle()" data-i18n="Start">Start</button></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="focus-note">focus-note</div>
    <div class="trow"><span class="big" id="f-val">–</span><span class="mut" id="f-best"></span></div>
    <div class="bar"><div id="f-bar"></div></div>
    <svg class="spark" id="f-spark" style="display:none" viewBox="0 0 300 50" preserveAspectRatio="none"><polyline id="f-line" fill="none" stroke="currentColor" stroke-width="2" points=""/></svg>
    <div class="mut" id="f-trend"></div>
    </div>
  </section>
  <section class="tool" id="c-audio" data-k="audio" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12"/></svg><h2 data-i18n="Speaker and microphone">Speaker and microphone</h2></div><div class="tact"><button onclick="soundTest()" data-i18n="Test sound">Test sound</button></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="Clap or speak: the bar shows what the microphone hears.">Clap or speak: the bar shows what the microphone hears.</div>
    <div class="bar"><div id="a-bar"></div></div>
    <div class="mut" id="a-info"></div>
    </div>
  </section>
  <section class="tool" id="c-sd" data-k="sd" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h8l4 4v14H7z"/><path d="M10 7v3M13 7v3M16 8v2"/></svg><h2 data-i18n="Memory card test">Memory card test</h2></div><div class="tact"><button id="b-sd" onclick="run('sd')" data-i18n="Start">Start</button></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="Writes and reads 64 MB once, then deletes them again.">Writes and reads 64 MB once, then deletes them again.</div>
    <div class="kv" id="sd-res"></div>
    </div>
  </section>
  <section class="tool" id="c-bt" data-k="bt" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10-5 4V3l5 4L7 17"/></svg><h2 data-i18n="Bluetooth scanner">Bluetooth scanner</h2></div><div class="tact"><button id="b-bt" onclick="run('bt')" data-i18n="Scan (10 s)">Scan (10 s)</button></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="bt-note">bt-note</div>
    <label class="opt"><span data-i18n="Warn me about unknown trackers that stay near">Warn me about unknown trackers that stay near</span><input type="checkbox" class="sw" id="cf-bt_tracker_warn" onchange="cfg('bt_tracker_warn',this.checked)"></label>
      <div class="trow"><span data-i18n="after">after</span> <input type="number" id="cf-bt_tracker_min" min="10" max="180" onchange="cfg('bt_tracker_min',+this.value)"> <span data-i18n="minutes">minutes</span></div>
    <div id="bt-trk"></div>
    <div class="tscroll"><table class="tl" id="bt-tab"></table></div>
    </div>
  </section>
  <section class="tool" id="c-pow" data-k="pow" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="7" width="16" height="10" rx="2"/><path d="M21 11v2M7 10v4M11 10v4"/></svg><h2 data-i18n="Power calculator">Power calculator</h2></div></div>
    <div class="tbd">
    <div class="trow"><span data-i18n="Now">Now</span> <span class="big" id="p-now">–</span><span class="mut" id="p-src"></span></div>
    <div class="mut" data-i18n="Tick what should be on - the calculator shows the consumption and the running time.">Tick what should be on - the calculator shows the consumption and the running time.</div>
    <div class="pw" id="p-parts"></div>
    <div class="trow"><span data-i18n="Battery">Battery</span> <input type="number" id="p-wh" min="1" max="5000" step="1"> Wh <span class="mut" id="p-whn"></span></div>
    <div class="kv" id="p-res"></div>
    </div>
  </section>
  <section class="tool" id="c-diag" data-k="diag" hidden>
    <div class="thd"><button class="sec back" type="button" onclick="showList()">‹ <span data-i18n="All tools">All tools</span></button>
      <div class="tht"><svg class="tico" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6z"/><path d="M8 14h2l1.5-3 2 5 1.5-2H16"/></svg><h2 data-i18n="Diagnosis package">Diagnosis package</h2></div><div class="tact"><button id="b-diag" onclick="location.href='/tools/diag.zip'" data-i18n="Download">Download</button></div></div>
    <div class="tbd">
    <div class="mut" data-i18n="diag-note">diag-note</div>
    </div>
  </section>
</div>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, {"Leisure": "Freizeit", "Game corner": "Spielecke",
 "party-note": "Spiele für den Abend auf den Handys: Quiz mit Buzzer, Werwolf mit Erzähler, Montagsmaler, Vier gewinnt, Würfel, Sanduhr und Punkte. Alle verbinden sich mit dem QR-Code im WLAN von MoveEye – ohne Passwort und ohne App. Die Spielecke schliesst sich nach der gewählten Zeit von selbst.",
 "Open the game corner": "Spielecke öffnen", "Scan with the phone (same Wi-Fi as MoveEye):": "Mit dem Handy scannen (gleiches WLAN wie MoveEye):",
 "open for": "offen noch", "game": "Spiel", "lobby": "Lobby", "quiz": "Quiz", "wolf": "Werwolf", "draw": "Montagsmaler", "c4": "Vier gewinnt",
 "Play myself": "Selbst mitspielen", "Close": "Schliessen", "Player": "Spieler", "Points": "Punkte", "away": "weg", "Make host": "Zum Gastgeber machen", "Remove": "Entfernen",
 "players": "Spieler", "Game collection": "Spielesammlung", "Without login in your own Wi-Fi:": "Ohne Login im eigenen WLAN:",
  "MoveEye is resting – only the game server runs": "MoveEye ruht – nur der Spiele-Server läuft", "MoveEye is watching": "MoveEye wacht",
  "rest-note": "Ruhemodus: Kamera, Erkennung und Alarme pausieren, der Pi hat die ganze Leistung für die Spiele. Endet von selbst, wenn die Spielecke schliesst.",
  "rest-note-on": "Kamera, Erkennung und Alarme pausieren. Endet von selbst mit der Spielecke.",
  "Watch again now": "Jetzt wieder überwachen", "Rest mode: only game server": "Ruhemodus: nur Spiele-Server",
  "rest-armed": "Der Schutz von MoveEye ist an. Im Ruhemodus gibt es keine Alarme. Trotzdem einschalten?", "until": "bis", "USB devices": "USB-Geräte", "Read again": "Neu einlesen",
  "usb-note": "Alles, was am USB steckt: Hersteller, Modell, Geschwindigkeit, Strombedarf und was der Pi daraus macht (WLAN-Karte, Laufwerk, Kamera …). Neu eingesteckte Geräte werden markiert.",
  "devices": "Geräte", "power need together": "Strombedarf zusammen", "usb-power": "der Pi gibt an allen USB-Buchsen zusammen etwa 1,2 A ab (Pi 5 mit kleinem Netzteil nur 0,6 A).",
  "No USB device plugged in.": "Kein USB-Gerät eingesteckt.", "No USB information on this computer.": "Auf diesem Computer gibt es keine USB-Angaben.",
  "USB controller": "USB-Anschluss", "bus": "Bus", "unknown device": "unbekanntes Gerät", "new": "neu", "Maker": "Hersteller", "Model (list)": "Modell (Liste)",
  "Type": "Art", "Speed": "Geschwindigkeit", "device can": "Gerät kann", "Power need": "Strombedarf", "Port": "Anschluss", "device": "Gerät",
  "Serial number": "Seriennummer", "Driver": "Treiber", "Network": "Netzwerk", "connected": "verbunden", "not connected": "nicht verbunden",
  "Drive": "Laufwerk", "opened at": "eingebunden unter", "not opened": "nicht eingebunden", "Camera": "Kamera", "Serial port": "Serielle Schnittstelle",
  "Sound card": "Soundkarte", "usb3-slow": "USB-3-Gerät läuft nur mit USB-2-Tempo: in eine blaue Buchse stecken (Pi 4/5).",
  "usb-hungry": "braucht viel Strom – bei Problemen ein USB-Hub mit eigenem Netzteil verwenden.",
  "usb-ids": "Hinweis: Die Namensliste usb.ids fehlt – Namen nur, wenn das Gerät sie selbst meldet (sudo apt install usbutils).",
  "Audio": "Audio", "Communication": "Kommunikation", "Input device (keyboard, mouse …)": "Eingabegerät (Tastatur, Maus …)", "Image (photo camera)": "Bild (Fotokamera)",
  "Printer": "Drucker", "Mass storage": "Massenspeicher", "Hub": "Verteiler (Hub)", "CDC data": "CDC-Daten", "Smart card": "Chipkarte", "Video (webcam)": "Video (Webcam)",
  "Wireless (Bluetooth, Wi-Fi …)": "Funk (Bluetooth, WLAN …)", "Miscellaneous": "Verschiedenes", "Application specific": "Anwendungsspezifisch", "Vendor specific": "Herstellereigen", "Audio/video": "Audio/Video", "Installed": "Installiert", "Up to date": "Aktuell", "Install / update": "Installieren / aktualisieren",
 "coll-note": "Freie Browserspiele (Open Source) zum Spielen allein: 2048, Hextris, A Dark Room, Schach, Rennspiel und mehr. Sie werden einmal von GitHub geladen und laufen danach ohne Internet.",
 "installed": "installiert", "downloading …": "lädt herunter …",
 "Tools": "Werkzeuge", "Network scanner": "Netzwerkscanner", "Scan": "Suchen", "All devices in your own network (only there).": "Alle Geräte im eigenen Netz (nur dort).",
 "Warn me about new devices (push, check every 10 min)": "Bei neuen Geräten warnen (Push, Prüfung alle 10 Min.)", "Am I at home?": "Bin ich zu Hause?",
 "pres-note": "Markiere unten im Netzwerkscanner dein Handy mit «🏠 meins». Handys melden sich im WLAN zuverlässiger als über Bluetooth.",
 "Disarm when my device comes, arm when it is gone": "Entschärfen, wenn mein Gerät kommt – Schutz einschalten, wenn es weg ist", "Automatic: on when my phone is gone": "Automatisch an, wenn mein Handy weg ist", "When my phone comes back:": "Wenn mein Handy zurückkommt:", "switch the protection off": "Schutz ausschalten", "ask «Is it you?» (person alarms wait)": "fragen «Bist du's?» (Personen-Alarme warten)", "nothing (the protection stays on)": "nichts (der Schutz bleibt an)", "Gone after": "Weg nach", "minutes": "Minuten",
 "Wi-Fi around": "WLAN-Umgebung", "Shows the Wi-Fi networks nearby and the best channel for the own Wi-Fi (hotspot).": "Zeigt die WLANs in der Nähe und den besten Kanal für das eigene WLAN (Hotspot).",
 "Internet test": "Internet-Test", "Start": "Start", "Stop": "Stopp", "speed-warn": "Braucht etwa 6 MB Daten – bei einem Handy-Abo mit wenig Volumen nur selten starten.",
 "Security check": "Sicherheits-Check", "Check": "Prüfen", "What can be reached from the network or the internet, and what is risky.": "Was aus dem Netz oder dem Internet erreichbar ist und was riskant ist.",
 "Bluetooth scanner": "Bluetooth-Scanner", "Scan (10 s)": "Suchen (10 s)", "bt-note": "Geräte in der Nähe. Fremde Geräte werden nicht gespeichert – nur die, die du als «meins» markierst.",
 "Warn me about unknown trackers that stay near": "Warnen bei fremden Trackern, die lange in der Nähe bleiben", "after": "nach",
 "Focus assistant": "Fokus-Assistent", "focus-note": "Dreh am Objektiv: je höher die Zahl, desto schärfer. Gemessen wird die Bildmitte.",
 "Servo test": "Servo-Test", "Servos": "Servos", "Positions, test, diagnosis, Not-Aus": "Positionen, Test, Diagnose, Not-Aus", "servo-note": "Fährt Schwenken und Neigen langsam über den ganzen Bereich und prüft, ob sich das Bild jedes Mal bewegt. Danach zurück an die alte Stelle.",
 "Speaker and microphone": "Lautsprecher und Mikrofon", "Test sound": "Testton", "Clap or speak: the bar shows what the microphone hears.": "Klatsche oder sprich: der Balken zeigt, was das Mikrofon hört.",
 "Memory card test": "Speicherkarten-Test", "Writes and reads 64 MB once, then deletes them again.": "Schreibt und liest einmal 64 MB und löscht sie danach wieder.",
 "Diagnosis package": "Diagnose-Paket", "Download": "Herunterladen", "diag-note": "Ein ZIP für die Fehlersuche: Protokoll, Systemwerte und Einstellungen – ohne Passwörter, Adressen, Themen und Bilder.",
 "Power calculator": "Strom-Rechner", "Now": "Jetzt", "Tick what should be on - the calculator shows the consumption and the running time.": "Hake an, was laufen soll – der Rechner zeigt Verbrauch und Laufzeit.",
 "Battery": "Akku", "Consumption": "Verbrauch", "Running time": "Laufzeit", "per day": "pro Tag", "measured": "gemessen", "estimate": "geschätzt",
 "IP": "IP", "Name": "Name", "Maker": "Hersteller", "Known as": "Bekannt als", "mine": "meins", "this device": "dieses Gerät", "router": "Router", "new": "neu",
 "private address (phone / tablet)": "private Adresse (Handy / Tablet)", "devices": "Geräte", "seconds": "Sekunden", "running…": "läuft …", "Network": "Netz",
 "Channel": "Kanal", "Signal": "Signal", "Best channel for the own Wi-Fi": "Bester Kanal fürs eigene WLAN", "connected": "verbunden",
 "Upload": "Hochladen", "Ping": "Ping", "Name lookup": "Namensauflösung", "Loss": "Verlust", "Time": "Zeit",
 "Kind": "Art", "Tracker": "Tracker", "Trackers nearby": "Tracker in der Nähe", "best": "bestes", "sharper": "schärfer", "less sharp": "unschärfer", "about the same": "etwa gleich",
 "Axis": "Achse", "To": "Nach", "Picture change": "Bildänderung", "Result": "Ergebnis", "moved": "bewegt", "no change": "keine Änderung", "pan": "schwenken", "tilt": "neigen",
 "Write": "Schreiben", "Read": "Lesen", "Card": "Karte", "Size": "Grösse", "Written since start": "Geschrieben seit Start", "Errors in the system log": "Fehler im Systemprotokoll",
 "Verdict": "Urteil", "good": "gut", "slow": "langsam", "replace soon": "bald ersetzen", "Microphone": "Mikrofon", "no microphone": "kein Mikrofon", "Level": "Pegel",
 "Here": "Da", "Away": "Weg", "No device marked": "Kein Gerät markiert", "since": "seit", "hours": "Std.", "not possible": "nicht möglich", "Name for this device": "Name für dieses Gerät",
 "Saved": "Gespeichert", "Only for the administrator": "Nur für den Administrator", "hidden": "versteckt", "ok": "ok",
 "AI detection": "KI-Erkennung", "Thermal camera": "Wärmebild", "Power saving (when quiet)": "Stromsparen (wenn ruhig)", "Infrared light": "Infrarot-Licht", "White light": "Weisslicht",
 "Own Wi-Fi (hotspot)": "Eigenes WLAN (Hotspot)", "Patrol (servos)": "Patrouille (Servos)", "Basic consumption": "Grundverbrauch"});
Object.assign(I18N.de, {"now in Settings → Security": "jetzt unter Einstellungen → Sicherheit"});   // 573
Object.assign(I18N.de, {"Web password set": "Web-Passwort gesetzt", "Web password missing": "Web-Passwort fehlt", "Everybody in the network can operate MoveEye": "Jeder im Netz kann MoveEye bedienen", "Secure page (https) on": "Sichere Seite (https) ein", "Secure page (https) off": "Sichere Seite (https) aus", "Passwords go through the network unencrypted - important in foreign Wi-Fi (camping)": "Passwörter gehen unverschlüsselt durchs Netz – wichtig in fremden WLANs (Camping)", "Open in the network: port": "Offen im Netz: Port", "SSH: login with password allowed": "SSH: Anmelden mit Passwort erlaubt", "SSH: login with password off (keys only)": "SSH: Anmelden mit Passwort aus (nur Schlüssel)", "Use a strong password or keys": "Starkes Passwort oder Schlüssel verwenden", "Public IPv6 address present": "Öffentliche IPv6-Adresse vorhanden", "Depending on the router the Pi can be reached directly from the internet - keep the web password on": "Je nach Router ist der Pi direkt aus dem Internet erreichbar – Web-Passwort eingeschaltet lassen", "Router forwards ports to this device:": "Router leitet Ports an dieses Gerät weiter:", "No port forwarding of the router to this device (UPnP)": "Keine Port-Weiterleitung des Routers an dieses Gerät (UPnP)", "Address in the internet:": "Adresse im Internet:", "shared address of the mobile network - not reachable from outside": "geteilte Adresse des Handynetzes – von aussen nicht erreichbar", "Internet not reachable": "Internet nicht erreichbar", "Tailscale: access from outside only for your own devices": "Tailscale: Zugriff von aussen nur für die eigenen Geräte", "no network": "kein Netz", "no Wi-Fi scan possible (NetworkManager / nmcli missing or no Wi-Fi)": "keine WLAN-Suche möglich (NetworkManager / nmcli fehlt oder kein WLAN)", "Bluetooth scanner needs: sudo apt install python3-bleak": "Der Bluetooth-Scanner braucht: sudo apt install python3-bleak", "steps without a change of the picture - blocked, at the end or camera not on the head?": "Schritte ohne Bildänderung – blockiert, am Anschlag oder Kamera nicht auf dem Kopf?", "Apple Find My (AirTag or a lost Apple device)": "Apple «Wo ist?» (AirTag oder verlorenes Apple-Gerät)", "Apple device": "Apple-Gerät", "Samsung device": "Samsung-Gerät", "Microsoft device": "Microsoft-Gerät"});
Object.assign(I18N.de, {"Wi-Fi adapters and repeater": "WLAN-Adapter und Repeater", "Search again": "Neu suchen", "Use a second adapter (repeater)": "Zweiten Adapter verwenden (Repeater)", "Swap: the USB stick makes the own Wi-Fi": "Tauschen: der USB-Stick macht das eigene WLAN", "Push message when the internet was gone": "Push-Meldung, wenn das Internet weg war", "Wi-Fi guard": "WLAN-Wächter", "guard-note": "Hört mit einem passenden USB-Stick mit, ob jemand das WLAN stört (Trennungs-Angriff, wie ihn Einbrecher gegen WLAN-Kameras benutzen).", "Alarm on Wi-Fi jamming (deauthentication attack)": "Alarm bei WLAN-Störung (Trennungs-Angriff)", "Alarm from": "Alarm ab", "disconnect frames per minute": "Trennungs-Meldungen pro Minute", "Recognise my marked devices by listening (Am I at home?)": "Meine markierten Geräte durch Mithören erkennen (Bin ich zu Hause?)", "Count devices nearby (anonymous, nothing is stored)": "Geräte in der Nähe zählen (anonym, nichts wird gespeichert)", "Repeater on": "Repeater aktiv", "Two adapters in use": "Zwei Adapter in Betrieb", "Second adapter not in use": "Zweiter Adapter nicht in Gebrauch", "Only one Wi-Fi adapter": "Nur ein WLAN-Adapter", "Own Wi-Fi": "Eigenes WLAN", "own Wi-Fi": "eigenes WLAN", "Internet": "Internet", "internet": "Internet", "off": "aus", "not connected": "nicht verbunden", "Plug in a USB Wi-Fi stick: then the Pi makes its own Wi-Fi and gets the internet from another network at the same time.": "Steck einen USB-WLAN-Stick ein: dann macht der Pi sein eigenes WLAN und holt gleichzeitig das Internet aus einem anderen Netz.", "no internet": "kein Internet", "connection unstable": "Verbindung unstabil", "No internet for devices": "Kein Internet für Geräte", "Adapter": "Adapter", "Chip": "Chip", "Listening": "Mithören", "Signal of the internet adapter (4 hours)": "Signal des Internet-Adapters (4 Stunden)", "weak: put the stick higher or nearer, use a USB extension cable": "schwach: Stick höher oder näher hinstellen, USB-Verlängerung benutzen", "listening": "hört mit", "error": "Fehler", "with": "mit", "Disconnect frames last minute": "Trennungs-Meldungen letzte Minute", "against your networks": "gegen deine Netze", "in total": "insgesamt", "devices nearby": "Geräte in der Nähe", "no internet for this device": "kein Internet für dieses Gerät", "only one Wi-Fi adapter": "nur ein WLAN-Adapter", "needs NetworkManager": "braucht NetworkManager", "very good: own Wi-Fi, 5 GHz and listening (monitor) work": "sehr gut: eigenes WLAN, 5 GHz und Mithören gehen", "good: 5 GHz and listening (monitor) work": "gut: 5 GHz und Mithören gehen", "simple stick: only 2.4 GHz": "einfacher Stick: nur 2,4 GHz", "only 2.4 GHz, listening (monitor) works": "nur 2,4 GHz, Mithören geht", "simple driver: no own Wi-Fi, no listening": "einfacher Treiber: kein eigenes WLAN, kein Mithören", "simple driver: no listening": "einfacher Treiber: kein Mithören", "listening (monitor) mostly not possible": "Mithören meist nicht möglich", "only 2.4 GHz": "nur 2,4 GHz", "extra driver needed": "braucht Zusatz-Treiber", "no Wi-Fi adapter here can listen (monitor mode) - e.g. a stick with MediaTek MT7612U / MT7921AU": "kein Adapter hier kann mithören (Monitor-Modus) – z. B. ein Stick mit MediaTek MT7612U / MT7921AU", "Built in": "Eingebaut"});
Object.assign(I18N.de, {"Full power for the tools": "Volle Leistung für die Werkzeuge", "tm-note": "Pausiert Kamera, Erkennung und KI, damit rechenintensive Werkzeuge die ganze Leistung bekommen. Danach läuft alles von selbst wieder.", "Pause MoveEye": "MoveEye pausieren", "Resume now": "Jetzt fortsetzen", "paused until": "Pausiert bis", "Camera, detection and alarms are paused - they come back by themselves.": "Kamera, Erkennung und Alarme ruhen – sie kommen von selbst zurück.", "tm-confirm": "Der Schutz von MoveEye ist an. Während der Pause gibt es keine Überwachung und keine Alarme. Trotzdem pausieren?"});
Object.assign(I18N.de, {"Internet over the USB stick (better antenna)": "Internet über den USB-Stick (bessere Antenne)"});
Object.assign(I18N.de, {"rep-confirm": "Repeater einschalten? Ein Adapter wird dann zum eigenen WLAN «MoveEye» (bei älteren Geräten «MotionWatch»). Der Pi bekommt im Heimnetz eventuell eine neue Adresse. Hat er nach 2½ Minuten keine Verbindung mehr, schaltet er den Repeater selbst wieder aus.",
  "repeater switched off again: no connection to a network": "Repeater wieder ausgeschaltet: keine Verbindung zu einem Netz"});
Object.assign(I18N.de, {"All tools": "Alle Werkzeuge", "problem": "Problem", "problems": "Probleme", "warning": "Warnung", "warnings": "Warnungen", "all ok": "alles in Ordnung"});
Object.assign(I18N.de, {"tools-intro": "Tippe auf ein Werkzeug, um es aufzuklappen. Die Zeile rechts zeigt das letzte Ergebnis.", "Open all": "Alle aufklappen", "Close all": "Alle zuklappen", "Network and internet": "Netz und Internet", "Wi-Fi": "WLAN", "Device tests": "Geräte-Tests", "Power and help": "Strom und Hilfe", "Developer": "Entwickler", "own network, read-only": "eigenes Netz, nur lesen", "Wi-Fi jamming!": "WLAN-Störung!", "Best channel": "Bester Kanal", "networks": "Netze"});
let S = null, FOC = null;
const fmtT = ts => ts ? new Date(ts * 1000).toLocaleString(LOCALE || undefined, {hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit"}) : "–";
function tr_(cells, head) { const r = el("tr"); cells.forEach(c => { const d = el(head ? "th" : "td"); if (c instanceof Node) d.appendChild(c); else d.textContent = c == null ? "–" : c; r.appendChild(d); }); return r; }
async function load() {
  const r = await fetch("/api/tools").then(x => x.ok ? x.json() : null).catch(() => null);
  if (!r) { $("#net-info").textContent = t("Only for the administrator"); return; }
  S = r; draw();
  const busy = ["net", "wifi", "speed", "bt", "servo", "sd"].some(k => S[k] && S[k].running);
  clearTimeout(load.t); load.t = setTimeout(load, busy ? 1500 : 10000);
}
async function run(what) {
  const b = $("#b-" + what); if (b) { b.disabled = true; b.textContent = t("running…"); }
  const r = await post("/api/tools", {action: what});
  if (!r.ok) toast(r.error || t("not possible"));
  setTimeout(load, 600);
}
async function cfg(key, value, extra) { const r = await post("/api/tools", Object.assign({action: "cfg", key, value}, extra || {})); if (!r.ok) toast(r.error || t("not possible")); else load(); }
function btn(id, label, running) { const b = $("#b-" + id); if (!b) return; b.disabled = !!running; b.textContent = running ? t("running…") : t(label); }
function draw() {
  const C = S.cfg || {};
  ["net_watch", "presence_auto", "bt_tracker_warn"].forEach(k => { const e = $("#cf-" + k); if (e) e.checked = !!C[k]; });
  { const e = $("#cf-presence_back"); if (e && document.activeElement !== e) e.value = C.presence_back || "ask"; }      // 2.98.15
  ["presence_gone_min", "bt_tracker_min"].forEach(k => { const e = $("#cf-" + k); if (e && document.activeElement !== e) e.value = C[k] != null ? C[k] : ""; });
  // network
  const N = S.net; btn("net", "Scan", N.running);
  if (N.t) $("#net-info").textContent = N.net + " · " + N.devices.length + " " + t("devices") + " · " + fmtT(N.t) + " · " + N.secs + " " + t("seconds") + (N.msg ? " · " + t(N.msg) : "");
  const tb = $("#net-tab"); tb.innerHTML = ""; const anyHs = N.devices.some(d => d.hs); if (N.devices.length) tb.appendChild(tr_([t("IP"), t("Name"), t("Maker"), t("Known as"), "🏠"].concat(anyHs ? ["🚫🌐"] : []), true));
  const mine = new Set(C.presence_macs || []);
  N.devices.forEach(d => {
    const ip = el("span", d.new ? "newdev" : "", d.ip + (d.role ? " (" + t(d.role) + ")" : "") + (d.new ? " ★ " + t("new") : ""));
    let kn = "", own = "";
    if (d.mac && d.role !== "this device") {
      kn = el("input"); kn.type = "text"; kn.value = d.known || ""; kn.placeholder = t("Name for this device");
      kn.onchange = () => post("/api/tools", {action: "known", mac: d.mac, name: kn.value.trim() || null}).then(r => { toast(r.ok ? t("Saved") : (r.error || t("not possible"))); load(); });
      own = el("input"); own.type = "checkbox"; own.checked = mine.has(d.mac); own.title = t("mine");
      own.onchange = () => cfg("presence_macs", own.checked, {mac: d.mac});
    }
    let ni = "";
    if (d.hs && d.mac && d.role !== "this device") { ni = el("input"); ni.type = "checkbox"; ni.checked = !!d.noinet; ni.title = t("no internet for this device");
      ni.onchange = () => post("/api/tools", {action: "noinet", mac: d.mac, value: ni.checked}).then(r => { toast(r.ok ? t("Saved") : (r.error || t("not possible"))); load(); }); }
    tb.appendChild(tr_([ip, d.name || "", t(d.vendor) || (d.mac || ""), kn, own].concat(anyHs ? [ni] : [])));
  });
  // presence
  const P = S.presence;
  $("#pres-st").textContent = !mine.size ? t("No device marked") : P.here == null ? "…" : (P.here ? "✅ " + t("Here") : "🚶 " + t("Away")) + (P.since ? " · " + t("since") + " " + fmtT(P.since) : "");
  // wifi
  const W = S.wifi; btn("wifi", "Scan", W.running);
  if (W.t) $("#wifi-best").textContent = W.best ? t("Best channel for the own Wi-Fi") + ": " + W.best + (W.own ? " · " + t("connected") + ": " + W.own.ssid + " (" + t("Channel") + " " + W.own.ch + ")" : "") : t(W.msg || "not possible");
  const ch = $("#wifi-ch"), chl = $("#wifi-chl"); ch.innerHTML = ""; chl.innerHTML = "";
  if (W.t && W.nets.length) { const mx = Math.max(1, ...Object.values(W.channels || {}));
    for (let c = 1; c <= 13; c++) { const b = el("div", c === W.best ? "best" : ""); b.style.height = Math.round(100 * ((W.channels || {})[c] || 0) / mx) + "%"; b.title = c; ch.appendChild(b); chl.appendChild(el("span", "", c)); } }
  const wt = $("#wifi-tab"); wt.innerHTML = ""; if (W.nets.length) wt.appendChild(tr_([t("Name"), t("Channel"), t("Signal"), ""], true));
  W.nets.forEach(n => wt.appendChild(tr_([(n.own ? "✓ " : "") + n.ssid, n.ch + (n.mhz > 5000 ? " (5 GHz)" : ""), n.signal + " %", n.sec || "🔓"])));
  // speed
  const Q = S.speed; btn("speed", "Start", Q.running);
  const last = Q.hist[Q.hist.length - 1]; const kv = $("#speed-now"); kv.innerHTML = "";
  if (last) { if (last.error) kv.append(el("span", "", "⚠"), el("span", "", last.error));
    else [["Download", (last.down_mbit ?? "–") + " Mbit/s"], ["Upload", (last.up_mbit ?? "–") + " Mbit/s"], ["Ping", (last.ping_ms ?? "–") + " ms"], ["Name lookup", (last.dns_ms ?? "–") + " ms"], ["Loss", (last.loss ?? "–") + " %"]]
      .forEach(([a, b]) => kv.append(el("span", "", t(a)), el("span", "", b))); }
  const st = $("#speed-tab"); st.innerHTML = ""; if (Q.hist.length > 1) { st.appendChild(tr_([t("Time"), "↓", "↑", t("Ping")], true));
    Q.hist.slice().reverse().forEach(h => st.appendChild(tr_([fmtT(h.t), h.error ? "⚠" : h.down_mbit, h.error ? "" : h.up_mbit, h.error ? "" : h.ping_ms]))); }
  // security
  const sl = $("#sec-list"); if (sl) { sl.innerHTML = ""; btn("sec", "Check", S.sec.running);   // 573: the check is in Settings → Security now
  (S.sec.items || []).forEach(it => { const r = el("div", "lv"); r.append(el("i", "lvl " + it.level));
    const tx = el("div", "", t(it.text) + (it.arg ? " " + it.arg : "")); if (it.tip) { tx.appendChild(el("br")); tx.appendChild(el("span", "mut", t(it.tip))); } r.appendChild(tx); sl.appendChild(r); });
  if (S.sec.t) sl.appendChild(el("div", "mut", fmtT(S.sec.t))); }
  // bluetooth
  const B = S.bt; btn("bt", "Scan (10 s)", B.running);
  const mbt = new Set(C.presence_bt || []);
  const tk = $("#bt-trk"); tk.innerHTML = "";
  if ((B.trackers || []).length) { tk.appendChild(el("b", "", t("Trackers nearby") + ":")); B.trackers.forEach(x => tk.appendChild(el("div", x.min >= (C.bt_tracker_min || 30) ? "newdev" : "mut", "📍 " + t(x.kind) + " · " + x.min + " " + t("minutes")))); }
  const bt = $("#bt-tab"); bt.innerHTML = ""; if (B.msg) bt.appendChild(tr_([t(B.msg)]));
  if (B.devices.length) bt.appendChild(tr_([t("Name"), t("Kind"), t("Signal"), "🏠"], true));
  B.devices.forEach(d => { const own = el("input"); own.type = "checkbox"; own.checked = mbt.has((d.addr || "").toLowerCase()); own.onchange = () => cfg("presence_bt", own.checked, {mac: d.addr});
    bt.appendChild(tr_([el("span", d.tracker ? "newdev" : "", d.name || d.addr), t(d.kind) || "", d.rssi != null ? d.rssi + " dBm" : "", own])); });
  // sd
  const D = S.sd; btn("sd", "Start", D.running); const sd = $("#sd-res"); sd.innerHTML = ""; const R = D.res || {};
  if (D.msg) sd.append(el("span", "", "⚠"), el("span", "", D.msg));
  if (R.write_mb_s != null) [["Write", R.write_mb_s + " MB/s"], ["Read", R.read_mb_s + " MB/s"], ["Card", [R.name, R.type, R.date].filter(Boolean).join(" · ") || R.device],
      ["Size", R.size_gb != null ? R.size_gb + " GB" : null], ["Written since start", R.written_gb != null ? R.written_gb + " GB" : null], ["Errors in the system log", R.errors],
      ["Verdict", {ok: "✅ " + t("good"), warn: "⚠ " + t("slow"), bad: "⛔ " + t("replace soon")}[R.verdict]]]
    .forEach(([a, b]) => { if (b != null && b !== "") sd.append(el("span", "", t(a)), el("span", "", b)); });
  drawPower(); drawDual(); drawSums(); drawTm();
  ["#pres-st", "#du-st", "#gu-st"].forEach(id => { const e = $(id); if (e) e.textContent = PLAIN(e.textContent); });
}
// one tool at a time: list on the left (phone: list first, then the tool)
const PLAIN = x => String(x == null ? "" : x).replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B50}\u{2705}\u{FE0F}\u{200D}]/gu, "").replace(/^\s+/, "");
let SEL = "";
// ---- game corner (2.95.29) ----
let PTY = null, ptyT = null;
async function partyLoad() {
  clearTimeout(ptyT);
  const r = await fetch("/api/party").then(x => x.ok ? x.json() : null).catch(() => null);
  if (r) { PTY = r; partyPaint(); }
  ptyT = setTimeout(partyLoad, SEL === "party" ? 3000 : 20000);
}
async function partyDo(d) { const r = await post("/api/party", d); if (r && r.ok) { PTY = r; partyPaint(); } }
function partyPaint() {
  const P = PTY || {}, box = $("#party-box"); if (!box) return;
  const sm = $("#s-party"); if (sm) sm.textContent = P.on ? "🟢 " + t("open") + " · " + (P.players || []).length + " " + t("players") : "";
  if (box.contains(document.activeElement) && document.activeElement.tagName === "SELECT") return;
  box.innerHTML = "";
  if (!P.on) {
    const row = el("div", "trow"); const sel = document.createElement("select"); [[2, "2 h"], [4, "4 h"], [6, "6 h"], [12, "12 h"]].forEach(([v, n]) => { const o = el("option", "", n); o.value = v; sel.appendChild(o); }); sel.value = 6;
    const b = el("button", "", "🎮 " + t("Open all games")); b.type = "button"; b.onclick = () => partyDo({action: "all", hours: +sel.value});
    row.append(b, sel); box.appendChild(row); box.appendChild(el("div", "mut", t("all-games-note")));
  } else {
    const q = el("div"); q.style.cssText = "display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin:10px 0";
    const qr = el("div"); qr.innerHTML = P.qr; qr.style.cssText = "width:190px;height:190px;background:#fff;padding:8px;border-radius:12px"; const sv = qr.querySelector("svg"); if (sv) { sv.style.width = "100%"; sv.style.height = "100%"; }
    const info = el("div"); info.style.flex = "1 1 240px";
    info.append(el("div", "", t("Scan with the phone (same Wi-Fi as MoveEye):")));
    const a = el("a", "", P.url); a.href = P.url; a.target = "_blank"; a.style.wordBreak = "break-all"; info.appendChild(a);
    info.appendChild(el("div", "mut", t("open for") + " " + Math.round(P.left / 60) + " min · " + t("game") + ": " + t(P.game)));
    const A = P.all || {};                                   // 2.98.7: what «all games» opened
    info.appendChild(el("div", "mut", "✓ " + t("Game corner") + " · " + (A.coll ? "✓ " + t("Game collection") + " (" + A.coll + ")" : ((P.dl && P.dl.running) ? "⏳ " : "– ") + t("Game collection"))
      + " · " + (A.sim ? "✓ " + t("Simulator game") + " (" + A.sim_n + " " + t("runners") + ")" : "– " + t("Simulator game") + " (" + t("simulator not running") + ")")));
    const r2 = el("div", "trow"); const pl = el("a", "btn", "▶ " + t("Play myself")); pl.href = P.url; pl.target = "_blank";
    const cl = el("button", "sec", "⛔ " + t("Close")); cl.type = "button"; cl.onclick = () => partyDo({action: "close"}); r2.append(pl, cl); info.appendChild(r2);
    q.append(qr, info); box.appendChild(q);
    const tb = el("table", "tl"); tb.innerHTML = "<tr><th>" + [t("Player"), t("Points"), ""].join("</th><th>") + "</th></tr>";
    (P.players || []).forEach(p => { const tr = el("tr"); tr.append(el("td", "", (p.host ? "👑 " : "") + p.name + (p.on ? "" : " (" + t("away") + ")")), el("td", "", String(p.score)));
      const td = el("td"); if (!p.host) { const hb = el("button", "sec", "👑"); hb.type = "button"; hb.title = t("Make host"); hb.onclick = () => partyDo({action: "host", id: p.id}); td.appendChild(hb); }
      const kb = el("button", "sec", "✕"); kb.type = "button"; kb.title = t("Remove"); kb.onclick = () => partyDo({action: "kick", id: p.id}); td.appendChild(kb); tr.appendChild(td); tb.appendChild(tr); });
    if ((P.players || []).length) box.appendChild(tb);
  }
  const R = P.rest || {}, rr = el("div", "adp"); rr.style.cssText = "margin:12px 0;padding:12px;border:1px solid var(--line);border-radius:12px";
  const rh = el("div", "adp-h"); rh.append(el("b", "", R.on ? "😴 " + t("MoveEye is resting – only the game server runs") : "👁 " + t("MoveEye is watching")),
    el("span", "mut", R.cpu != null ? "CPU " + Math.round(R.cpu) + " %" + (R.temp != null ? " · " + Math.round(R.temp) + " °C" : "") : ""));
  rr.appendChild(rh);
  rr.appendChild(el("div", "mut", R.on ? t("until") + " " + new Date(R.until * 1000).toLocaleTimeString(LOCALE || undefined, {hour: "2-digit", minute: "2-digit"}) + " · " + t("rest-note-on") : t("rest-note")));
  const rb = el("button", R.on ? "" : "sec", R.on ? "👁 " + t("Watch again now") : "😴 " + t("Rest mode: only game server")); rb.type = "button"; rb.style.marginTop = "8px";
  rb.onclick = () => { if (!R.on && R.armed && !confirm(t("rest-armed"))) return; const hs = box.querySelector("select"); partyDo({action: "rest", on: !R.on, hours: hs ? +hs.value : 6}); };
  rr.appendChild(rb); box.appendChild(rr);
  if (P.lan_url) { const lr = el("div", "mut"); lr.style.margin = "8px 0"; lr.append(t("Without login in your own Wi-Fi:") + " "); const la = el("a", "", P.lan_url); la.href = P.lan_url; la.target = "_blank"; lr.appendChild(la); box.appendChild(lr); }
  const h = el("h3", "", "🕹 " + t("Game collection")); h.style.margin = "16px 0 6px"; box.appendChild(h);
  const gl = P.games || [];
  box.appendChild(el("div", "mut", gl.length ? t("Installed") + ": " + gl.map(x => x.name).join(", ") + " (" + P.games_ver + ")" : t("coll-note")));
  const ib = el("button", gl.length ? "sec" : "", (P.dl && P.dl.running) ? "⏳ " + Math.round((P.dl.got || 0) / 1e6) + " MB …" : (gl.length && P.games_ver === (P.games_pkg || {}).version ? "✓ " + t("Up to date") : "⬇ " + t("Install / update") + " (" + Math.round(((P.games_pkg || {}).size || 0) / 1e6) + " MB)"));
  ib.type = "button"; ib.disabled = !!(P.dl && P.dl.running); ib.onclick = () => partyDo({action: "install"}); box.appendChild(ib);
  if (P.dl && P.dl.msg && !P.dl.running) box.appendChild(el("div", "mut", t(P.dl.msg)));
  if (gl.length) { const GG = {touch: "👆 " + t("Touch (phone, tablet)"), buttons: "🎮 " + t("With on-screen buttons")};       // 2.95.54
    (gl.some(x => x.input) ? ["touch", "buttons"] : [null]).forEach(grp => { const part = gl.filter(x => grp === null || (x.input || "touch") === grp); if (!part.length) return;
      if (grp) box.appendChild(el("div", "mut", GG[grp]));
      const g2 = el("div", "trow"); part.forEach(x => { const a = el("a", "btn sec", (x.icon && x.icon.length < 4 ? x.icon + " " : "") + x.name); a.href = "/games/" + x.dir + "/"; a.target = "_blank"; g2.appendChild(a); }); box.appendChild(g2); }); }
}
(async () => { for (let i = 0; i < 30 && !LANG; i++) await new Promise(r => setTimeout(r, 100)); partyLoad(); })();   // after the language is known
Object.assign(I18N.de, {"Network check of the players": "Netz-Check der Mitspieler", "How well does every phone reach MoveEye? Each one measures reaction time, jitter, losses, download and upload; MoveEye adds the signal it receives from each phone (at its own Wi-Fi).": "Wie gut erreicht jedes Handy MoveEye? Jedes misst Reaktionszeit, Schwankung, Verluste, Download und Upload; MoveEye ergänzt das Signal, das es von jedem Handy empfängt (am eigenen WLAN).", "running": "läuft", "measured": "gemessen", "weak": "schwach", "measure all phones at once": "alle Handys auf einmal messen", "End the check": "Check beenden", "open for": "offen noch", "Start the check": "Check starten", "Clear": "Leeren", "Phones in the game corner measure by themselves. Everybody else: scan the QR code or open": "Handys in der Spielecke messen von selbst. Alle anderen: QR-Code scannen oder öffnen", "still waiting for": "warte noch auf", "MoveEye is the Wi-Fi itself: the signal of every phone is measured too.": "MoveEye ist selbst das WLAN: Das Signal jedes Handys wird mitgemessen.", "Player": "Spieler", "Reaction": "Reaktion", "Jitter": "Schwankung", "Signal": "Signal", "Down / Up in Mbit/s, between the phone and MoveEye (not the internet). Reaction under 30 ms and over 10 Mbit/s are fine for all games.": "Down / Up in Mbit/s, zwischen Handy und MoveEye (nicht Internet). Reaktion unter 30 ms und über 10 Mbit/s reichen für alle Spiele.", "nt-tips": "Schwache Handys näher zu MoveEye bringen, MoveEye höher stellen (nicht am Boden, nicht hinter dem Auto), Körper und Wände dazwischen meiden. Viele Handys gleichzeitig teilen sich die Geschwindigkeit.", "At the own Wi-Fi, not measured yet": "Am eigenen WLAN, noch nicht gemessen", "lost packets": "Pakete verloren", "slow reaction": "langsame Reaktion", "reaction a bit slow": "Reaktion etwas langsam", "unsteady": "schwankend", "little speed": "wenig Geschwindigkeit", "medium speed": "mittlere Geschwindigkeit", "weak signal": "schwaches Signal", "signal could be better": "Signal könnte besser sein"});
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"nt-tips": "Bring weak phones closer to MoveEye, put MoveEye higher (not on the ground, not behind the car), avoid bodies and walls in between. Many phones at the same time share the speed."});
Object.assign(I18N.de, {"Product page for guests": "Infoseite für Gäste", "info-note": "Deine Homepage von MoveEye, direkt vom Pi – auch ohne Internet. Freunde am eigenen WLAN oder Nachbarn im WLAN des Campingplatzes öffnen sie über den QR-Code, ohne Login. Sie sehen nur diese Seite, nichts von deinen Kameras. Fragen aus dem Formular kommen als Push-Nachricht zu dir.", "Show the product page to guests in the same Wi-Fi (without login)": "Infoseite für Gäste im gleichen WLAN zeigen (ohne Login)", "Your e-mail address on the page (empty = not shown)": "Deine E-Mail-Adresse auf der Seite (leer = nicht zeigen)", "shared": "freigegeben", "off": "aus", "Guests scan the QR code (same Wi-Fi) or open": "Gäste scannen den QR-Code (gleiches WLAN) oder öffnen", "Open the page": "Seite öffnen", "Questions from the page": "Fragen von der Seite", "No questions yet. A new question also comes as a push message.": "Noch keine Fragen. Eine neue Frage kommt auch als Push-Nachricht."});
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"info-note": "Your MoveEye homepage, straight from the Pi - also without internet. Friends at your own Wi-Fi or neighbours in the Wi-Fi of the camping site open it with the QR code, without login. They only see this page, nothing of your cameras. Questions from the form reach you as a push message."});
Object.assign(I18N.de, {"AI helper (PC)": "KI-Rechenhilfe (PC)", "helper-note": "Ein PC im gleichen Netz rechnet die Erkennung (Menschen, Tiere, Fahrzeuge) für den Pi: viel schneller, der Pi bleibt kühl und braucht weniger Strom. Antwortet der PC nicht mehr, rechnet der Pi sofort wieder selbst. Zum PC gehen nur kleine Bilder, gespeichert wird dort nichts.", "Let a PC do the AI when one is there": "Einen PC rechnen lassen, wenn einer da ist", "Another PC by hand": "Anderen PC von Hand eintragen", "helper-manual": "Auf dem PC MoveEye mit «--helper» starten (oder dort «Diese MoveEye rechnet für andere» einschalten). Dann hier seine Adresse und den 6-stelligen Code eintragen.", "Save": "Speichern", "This MoveEye works as AI helper for others (port 5057)": "Diese MoveEye rechnet für andere (Port 5057)", "works for others": "rechnet für andere", "no PC found": "kein PC gefunden", "The PC does the AI": "Der PC rechnet die KI", "The Pi does the AI itself": "Der Pi rechnet die KI selbst", "found through the simulator": "über den Simulator gefunden", "by hand": "von Hand", "AI": "KI", "way there and back": "Hin und zurück", "pictures": "Bilder", "helper-how": "Am einfachsten: Im 3D-Simulator auf dem PC «MoveEye auf diesem PC starten» drücken – der Pi findet die Rechenhilfe dann von selbst.", "Pairing code for the Pi": "Code für den Pi", "pairing code wrong": "Code falsch", "the PC is still loading its AI model": "der PC lädt noch sein KI-Modell", "not a MoveEye helper": "keine MoveEye-Rechenhilfe"});
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"helper-note": "A PC in the same network does the detection (people, animals, vehicles) for the Pi: much faster, the Pi stays cool and needs less power. If the PC stops answering, the Pi does it itself again at once. Only small pictures go to the PC, nothing is stored there.", "helper-manual": "Start MoveEye on the PC with «--helper» (or switch on «works as AI helper for others» there). Then enter its address and the 6-digit code here.", "helper-how": "Easiest: in the 3D simulator on the PC press «Start MoveEye on this PC» - the Pi then finds the helper by itself."});
Object.assign(I18N.de, {"Survival almanac": "Überlebens-Almanach", "tips for camping, to look up or read in the evening": "Tipps fürs Camping – zum Nachschlagen oder als Abendlektüre"});
Object.assign(I18N.de, {"Touch (phone, tablet)": "Touch (Handy, Tablet)", "With on-screen buttons": "Mit Bildschirm-Tasten"});
Object.assign(I18N.de, {"Open all games": "Spiele freigeben", "all-games-note": "Eine Taste für alles: Spielecke (Quiz, Werwolf …), Spielesammlung und – wenn der 3D-Simulator läuft – «Team gegen MoveEye». Die Mitspieler scannen einen QR-Code, geben ihren Namen ein und sind dabei.",
  "Simulator game": "Simulator-Spiel", "runners": "Läufer", "simulator not running": "Simulator läuft nicht"});
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"all-games-note": "One button for everything: game corner (quiz, werewolf …), game collection and - when the 3D simulator runs - «Team against MoveEye». The players scan one QR code, type their name and are in."});
// ---- AI helper (2.95.53) ----
let hpT = 0;
async function hpLoad() {
  clearTimeout(hpT);
  let j; try { j = await (await fetch("/api/helper", {cache: "no-store"})).json(); } catch (e) { j = null; }
  if (j && j.ok) hpPaint(j);
  hpT = setTimeout(hpLoad, SEL === "helper" ? 3000 : 30000);
}
async function hpSet(d) { const r = await fetch("/api/helper", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: LANG}, d))}).then(x => x.json()).catch(() => null);
  if (r && r.ok) hpPaint(r); else if (r && r.error) alert(r.error); }
function hpPaint(j) {
  const H = j.helper;
  const sm = $("#s-helper"); if (sm) sm.textContent = H.ok ? "✓ " + (H.name || "PC") + " · " + H.ms + " ms" : (H.serve ? t("works for others") + (H.served ? " · " + H.served : "") : (H.use ? t("no PC found") : t("off")));
  const dt = $("#d-helper"); if (dt) dt.className = "tdot " + (H.ok || (H.serve && H.served) ? "ok" : "");
  const u = $("#hp-use"); if (u) u.checked = H.use; const sv = $("#hp-serve"); if (sv) sv.checked = H.serve;
  const iu = $("#hp-url"); if (iu && iu !== document.activeElement && !iu.value) iu.value = (H.manual_url || "").replace(/^https?:\/\//, "").replace(/:5057$/, "");
  const box = $("#hp-box"); if (!box) return; box.textContent = "";
  const big = el("div", "big", H.ok ? "🟢 " + t("The PC does the AI") : (H.use ? "⚪ " + t("The Pi does the AI itself") : "⚪ " + t("off"))); box.appendChild(big);
  if (H.ok) box.appendChild(el("div", "mut", (H.name || "PC") + " · " + H.url + " · " + (H.src === "simulator" ? t("found through the simulator") : t("by hand")) + " · " + t("AI") + " " + H.ms + " ms, " + t("way there and back") + " " + H.rtt + " ms · " + H.n + " " + t("pictures") + (H.accel ? " · " + H.accel : "") + (H.model ? " · 🧠 " + t(H.model) : "")));
  else if (H.url && H.msg) box.appendChild(el("div", "mut", "⚠ " + H.url + ": " + t(H.msg)));
  else if (H.use) box.appendChild(el("div", "mut", t("helper-how")));
  if (H.serve) box.appendChild(el("div", "", "🖥 " + t("Pairing code for the Pi") + ": " + H.my_code + (H.served ? " · " + H.served + " " + t("pictures") + " · " + H.serve_ms + " ms · " + H.serve_from : "") + (H.serve_model ? " · 🧠 " + t(H.serve_model) : "")));
}
(async () => { for (let i = 0; i < 30 && !LANG; i++) await new Promise(r => setTimeout(r, 100)); hpLoad(); })();
// ---- product page for guests (2.95.52) ----
let infoT = 0, INFOK = "";
async function infoLoad() {
  clearTimeout(infoT);
  let j; try { j = await (await fetch("/api/info", {cache: "no-store"})).json(); } catch (e) { j = null; }
  if (j && j.ok) infoPaint(j);
  infoT = setTimeout(infoLoad, SEL === "info" ? 5000 : 60000);
}
async function infoSet(d) { const r = await fetch("/api/info", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: LANG}, d))}).then(x => x.json()).catch(() => null);
  if (r && r.ok) infoPaint(r); else if (r && r.error) alert(r.error); }
function infoPaint(j) {
  const sm = $("#s-info"); if (sm) sm.textContent = j.on ? t("shared") + (j.msgs.length ? " · ✉ " + j.msgs.length : "") : t("off");
  const dt = $("#d-info"); if (dt) dt.className = "tdot " + (j.on ? "ok" : "");
  const on = $("#info-on"); if (on) on.checked = j.on;
  const ml = $("#info-mail"); if (ml && ml !== document.activeElement) ml.value = j.mail || "";
  const box = $("#info-box"); if (!box) return;
  const key = JSON.stringify([j.on, j.url, j.msgs.length, j.msgs[0] && j.msgs[0].t]); if (key === INFOK) return; INFOK = key; box.textContent = "";
  if (j.on) {
    const q = el("div", ""); q.style.cssText = "display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:6px 0 10px";
    const qr = el("div", ""); qr.style.cssText = "background:#fff;padding:8px;border-radius:10px;width:150px;height:150px"; qr.innerHTML = j.qr; const sv = qr.querySelector("svg"); if (sv) { sv.style.width = "100%"; sv.style.height = "100%"; }
    const tx = el("div", ""); tx.style.flex = "1 1 200px"; tx.append(el("div", "", t("Guests scan the QR code (same Wi-Fi) or open")), el("b", "", j.url));
    const a = el("a", "btn sec", "🔗 " + t("Open the page")); a.href = "/info/"; a.target = "_blank"; a.style.marginTop = "8px"; a.style.display = "inline-block"; tx.appendChild(a);
    q.append(qr, tx); box.appendChild(q);
  }
  box.appendChild(el("h3", "", "✉ " + t("Questions from the page") + " (" + j.msgs.length + ")"));
  if (!j.msgs.length) box.appendChild(el("div", "mut", t("No questions yet. A new question also comes as a push message.")));
  j.msgs.forEach(m => { const c = el("div", ""); c.style.cssText = "border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin:6px 0";
    c.append(el("div", "mut", new Date(m.t * 1000).toLocaleString() + " · " + (m.name || m.ip) + " · " + m.topic)); const p = el("div", "", m.msg); p.style.whiteSpace = "pre-wrap"; c.appendChild(p); box.appendChild(c); });
  if (j.msgs.length) { const b = el("button", "sec", "🗑 " + t("Clear")); b.type = "button"; b.onclick = () => infoSet({action: "clear"}); box.appendChild(b); }
}
(async () => { for (let i = 0; i < 30 && !LANG; i++) await new Promise(r => setTimeout(r, 100)); infoLoad(); })();
Object.assign(I18N.de, {"Reception map (walk round)": "Empfangskarte (Rundgang)", "walk-note": "Mit dem Handy um den Platz gehen: auf dem Plan tippen, wo man steht, und messen. So siehst du, wo das WLAN gut ist und wo nicht – praktisch, um MoveEye oder den Spielbereich gut zu platzieren. Geht, solange der Netz-Check offen ist.", "spots": "Stellen", "walk-tip": "Rot = schwach: dort spielt man besser nicht, oder MoveEye näher hin / höher stellen.", "Show in the 3D simulator": "Im 3D-Simulator zeigen", "shown on the ground of the simulator": "im Simulator am Boden eingezeichnet", "Clear the map": "Karte leeren"});
Object.assign(I18N.en, {"walk-note": "Walk round the place with the phone: tap on the plan where you stand and measure. So you see where the Wi-Fi is good and where not - handy to place MoveEye or the play area. Works while the network check is open.", "walk-tip": "Red = weak: better not play there, or put MoveEye closer / higher."});
// ---- reception map (2.95.53): Empfangs-Rundgang ----
function ntWalk(j, box) {
  const w = el("div", ""); w.style.marginTop = "14px";
  w.appendChild(el("h3", "", "🗺 " + t("Reception map (walk round)")));
  w.appendChild(el("div", "mut", t("walk-note")));
  if (j.open && j.walk_qr) { const q = el("div", ""); q.style.cssText = "display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:8px 0";
    const qr = el("div", ""); qr.style.cssText = "background:#fff;padding:6px;border-radius:10px;width:120px;height:120px"; qr.innerHTML = j.walk_qr; const sv = qr.querySelector("svg"); if (sv) { sv.style.width = "100%"; sv.style.height = "100%"; }
    q.append(qr, el("b", "", j.walk_url)); w.appendChild(q); }
  if ((j.walk || []).length) {
    const cv = document.createElement("canvas"); cv.width = 520; cv.height = 520; cv.style.cssText = "width:min(100%,360px);aspect-ratio:1;background:#0b1310;border-radius:12px;display:block;margin:8px 0";
    const cx = cv.getContext("2d"), R = 25, P = (x, z) => [260 + x / R * 240, 260 - z / R * 240];
    cx.strokeStyle = "#24324a"; cx.lineWidth = 2; [5, 10, 20].forEach(r => { cx.beginPath(); cx.arc(260, 260, r / R * 240, 0, 7); cx.stroke(); });
    j.walk.forEach(p => { const [a, b] = P(p.x, p.z); const g = cx.createRadialGradient(a, b, 2, a, b, 46); const c = "hsla(" + Math.round(p.q * 120) + ",80%,50%,";
      g.addColorStop(0, c + ".85)"); g.addColorStop(1, c + "0)"); cx.fillStyle = g; cx.beginPath(); cx.arc(a, b, 46, 0, 7); cx.fill(); });
    cx.fillStyle = "#f59a4a"; cx.beginPath(); cx.arc(260, 260, 10, 0, 7); cx.fill();
    cx.strokeStyle = "#e8eef6"; cx.lineWidth = 3; cx.beginPath(); cx.moveTo(260, 260); cx.lineTo(260, 215); cx.stroke();
    w.appendChild(cv);
    const good = j.walk.filter(p => p.q >= .66).length, weak = j.walk.filter(p => p.q < .33).length;
    w.appendChild(el("div", "mut", j.walk.length + " " + t("spots") + " · 🟢 " + good + " · 🔴 " + weak + (weak ? " · " + t("walk-tip") : "")));
    const r = el("div", "trow");
    if (j.sim_ok) { const b = el("button", "sec", "🎮 " + t("Show in the 3D simulator")); b.type = "button"; b.onclick = async () => { const x = await (await fetch("/api/nettest", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: "walk_sim", lang: LANG})})).json(); toast(x.ok ? "✓ " + t("shown on the ground of the simulator") : "⚠ " + (x.error || t("error"))); }; r.appendChild(b); }
    const c = el("button", "sec", "🗑 " + t("Clear the map")); c.type = "button"; c.onclick = () => ntAct("walk_clear"); r.appendChild(c); w.appendChild(r);
  }
  box.appendChild(w);
}
// ---- network check of the players (2.95.52) ----
let ntT = 0, NTK = "";
async function ntLoad() {
  clearTimeout(ntT);
  let j; try { j = await (await fetch("/api/nettest", {cache: "no-store"})).json(); } catch (e) { j = null; }
  if (j && j.ok) ntPaint(j);
  ntT = setTimeout(ntLoad, SEL === "nettest" ? (j && j.open ? 2000 : 6000) : 30000);
}
async function ntAct(a, extra) { const r = await fetch("/api/nettest", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({action: a}, extra || {}))}).then(x => x.json()).catch(() => null); if (r && r.ok) ntPaint(r); }
function ntPaint(j) {
  const n = j.res.length, weak = j.res.filter(r => r.grade === "weak").length, fair = j.res.filter(r => r.grade === "fair").length;
  const sm = $("#s-nettest"); if (sm) sm.textContent = j.open ? t("running") + " · " + n + " " + t("measured") : (n ? n + " " + t("measured") + (weak ? " · " + weak + " " + t("weak") : "") : t("measure all phones at once"));
  const dt = $("#d-nettest"); if (dt) dt.className = "tdot " + (weak ? "bad" : fair ? "warn" : n ? "ok" : "");
  const box = $("#nt-box"); if (!box) return;
  const key = JSON.stringify([j.open, j.left > 0 ? Math.floor(j.left / 5) : 0, j.res, j.others, j.pending, j.pi_link, j.hotspot, (j.walk || []).length, j.sim_ok]); if (key === NTK) return; NTK = key;
  box.textContent = "";
  const row = el("div", "trow");
  if (j.open) { const b = el("button", "", "⏹ " + t("End the check")); b.type = "button"; b.onclick = () => ntAct("stop"); row.append(b, el("span", "mut", t("open for") + " " + Math.ceil(j.left / 60) + " min")); }
  else { const b = el("button", "", "▶ " + t("Start the check")); b.type = "button"; b.onclick = () => ntAct("start", {minutes: 3}); row.appendChild(b); }
  if (n) { const c = el("button", "sec", "🗑 " + t("Clear")); c.type = "button"; c.onclick = () => ntAct("clear"); row.appendChild(c); }
  box.appendChild(row);
  if (j.open) {
    const q = el("div", ""); q.style.cssText = "display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:10px 0";
    const qr = el("div", ""); qr.style.cssText = "background:#fff;padding:8px;border-radius:10px;width:150px;height:150px"; qr.innerHTML = j.qr; const sv = qr.querySelector("svg"); if (sv) { sv.style.width = "100%"; sv.style.height = "100%"; }
    const tx = el("div", "", ""); tx.style.flex = "1 1 200px";
    tx.append(el("div", "", t("Phones in the game corner measure by themselves. Everybody else: scan the QR code or open")), el("b", "", j.full_url));
    if (j.pending.length) tx.appendChild(el("div", "mut", "⏳ " + t("still waiting for") + ": " + j.pending.join(", ")));
    q.append(qr, tx); box.appendChild(q);
  }
  if (j.pi_link) box.appendChild(el("div", "mut", "📡 MoveEye → " + (j.pi_link.ssid || "WLAN") + ": " + (j.pi_link.dbm != null ? j.pi_link.dbm + " dBm" : "–") + (j.pi_link.rate ? " · " + j.pi_link.rate : "")));
  else if (j.hotspot) box.appendChild(el("div", "mut", "📡 " + t("MoveEye is the Wi-Fi itself: the signal of every phone is measured too.")));
  if (n) {
    const tb = document.createElement("table"); tb.className = "tl"; tb.style.marginTop = "10px";
    const hd = document.createElement("tr"); [t("Player"), "", t("Reaction"), t("Jitter"), "Down", "Up", t("Signal")].forEach(h => hd.appendChild(el("th", "", h))); tb.appendChild(hd);
    const f = (v, d) => v == null ? "–" : (+v).toFixed(d);
    j.res.forEach(r => { const tr = document.createElement("tr");
      const nm = el("td", ""); nm.append(el("b", "", r.name), el("div", "mut", [r.dev, r.maker, r.ip].filter(x => x).join(" · ")));
      const gd = el("td", "", {good: "🟢", fair: "🟠", weak: "🔴"}[r.grade] || "?"); gd.title = (r.why || []).map(t).join(", ");
      [nm, gd, el("td", "", f(r.rtt, 0) + " ms" + (r.loss ? " · " + r.loss + "✗" : "")), el("td", "", f(r.jitter, 0) + " ms"), el("td", "", f(r.down, 1)), el("td", "", f(r.up, 1)),
       el("td", "", r.dbm != null ? r.dbm + " dBm" + (r.link_tx ? " · " + Math.round(r.link_tx) + " Mbit/s" : "") : "–")].forEach(x => tr.appendChild(x));
      tb.appendChild(tr);
      if (r.why && r.why.length) { const w = document.createElement("tr"); const td = el("td", "mut", "↳ " + r.why.map(t).join(", ")); td.colSpan = 7; w.appendChild(td); tb.appendChild(w); } });
    const sc = el("div", "tscroll"); sc.appendChild(tb); box.appendChild(sc);
    box.appendChild(el("div", "mut", t("Down / Up in Mbit/s, between the phone and MoveEye (not the internet). Reaction under 30 ms and over 10 Mbit/s are fine for all games.")));
    if (weak || fair) box.appendChild(el("div", "mut", "💡 " + t("nt-tips")));
  }
  ntWalk(j, box);
  if (j.others && j.others.length) box.appendChild(el("div", "mut", "📱 " + t("At the own Wi-Fi, not measured yet") + ": " + j.others.map(o => (o.maker || o.mac) + (o.dbm != null ? " (" + o.dbm + " dBm)" : "")).join(", ")));
}
(async () => { for (let i = 0; i < 30 && !LANG; i++) await new Promise(r => setTimeout(r, 100)); ntLoad(); })();
// ---- USB devices (2.95.30) ----
let USBSEEN = null, USBNEW = {}, usbT = 0;
const USBICON = {"Mass storage": "💾", "Video (webcam)": "📷", "Image (photo camera)": "📷", "Audio": "🔊", "Input device (keyboard, mouse …)": "⌨️",
  "Wireless (Bluetooth, Wi-Fi …)": "📶", "Communication": "🔌", "Printer": "🖨", "Hub": "🔀", "Vendor specific": "🧩"};
function usbSpeed(m) { return m >= 20000 ? "USB 3.2 · 20 Gbit/s" : m >= 10000 ? "USB 3.1 · 10 Gbit/s" : m >= 5000 ? "USB 3 · 5 Gbit/s" : m >= 480 ? "USB 2 · 480 Mbit/s" : m >= 12 ? "USB 1 · 12 Mbit/s" : m > 0 ? "USB 1 · 1,5 Mbit/s" : "?"; }
function usbSize(b) { return b >= 1e12 ? (b / 1e12).toFixed(1) + " TB" : b >= 1e9 ? Math.round(b / 1e9) + " GB" : Math.round(b / 1e6) + " MB"; }
async function usbLoad(manual) {
  clearTimeout(usbT);
  let j; try { j = await (await fetch("/api/usb", {cache: "no-store"})).json(); } catch (e) { j = null; }
  if (j && j.ok) usbPaint(j, manual);
  usbT = setTimeout(usbLoad, SEL === "usb" ? 4000 : 30000);
}
function usbPaint(j, manual) {
  const box = $("#usb-box"); if (!box) return;
  const D = (j.devices || []), real = D.filter(d => !d.root && !d.hub);
  const keys = D.map(d => d.port + "|" + d.vid + ":" + d.pid);
  const now = Date.now();
  if (manual) USBNEW = {};
  if (USBSEEN) keys.filter(k => !USBSEEN.includes(k)).forEach(k => USBNEW[k] = now);   // plugged in while the page is open: marked 5 minutes
  Object.keys(USBNEW).forEach(k => { if (now - USBNEW[k] > 300000) delete USBNEW[k]; });
  USBSEEN = keys; const fresh = keys.filter(k => USBNEW[k]);
  const sm = $("#s-usb"); if (sm) sm.textContent = real.length + " " + t("devices");
  const ma = real.reduce((a, d) => a + (d.ma || 0), 0);
  $("#usb-sum").textContent = real.length ? real.length + " " + t("devices") + " · " + t("power need together") + " " + ma + " mA · " + t("usb-power") : (D.length ? t("No USB device plugged in.") : t("No USB information on this computer."));
  if (box.dataset.k === keys.join() + fresh.join() && !manual) return;
  box.dataset.k = keys.join() + fresh.join(); box.innerHTML = "";
  D.forEach((d, i) => {
    const c = el("div", "adp"); c.style.marginLeft = Math.min(4, d.depth) * 14 + "px";
    const isNew = fresh.includes(keys[i]);
    if (isNew) { c.style.background = "color-mix(in srgb, var(--acc) 14%, transparent)"; c.style.borderRadius = "10px"; c.style.padding = "10px"; }
    const ic = d.root ? "🖥" : d.hub ? "🔀" : (d.classes.map(x => USBICON[x]).find(Boolean) || "🔌");
    const nm = d.root ? t("USB controller") + " (" + t("bus") + " " + d.bus + ")" : (d.product || t("unknown device"));
    const h = el("div", "adp-h"); h.append(el("b", "", ic + " " + nm + (isNew ? "  🆕 " + t("new") : "")), el("span", "mut", d.vid + ":" + d.pid));
    c.appendChild(h);
    const L = [];
    if (!d.root) {
      if (d.maker || d.maker_db) L.push([t("Maker"), (d.maker || d.maker_db) + (d.maker && d.maker_db && d.maker_db !== d.maker ? " (" + d.maker_db + ")" : "")]);
      if (d.product_db && d.product_db !== d.product) L.push([t("Model (list)"), d.product_db]);
      L.push([t("Type"), d.classes.map(x => t(x)).join(", ") || "?"]);
    }
    L.push([t("Speed"), usbSpeed(d.speed) + (d.usb && !d.root ? " · " + t("device can") + " USB " + d.usb.trim().replace(/\.00$/, "").replace(/0$/, "") : "")]);
    if (!d.root && d.ma) L.push([t("Power need"), d.ma + " mA"]);
    if (!d.root) L.push([t("Port"), d.port + " · " + t("bus") + " " + d.bus + " " + t("device") + " " + d.dev]);
    if (d.serial && !d.root) L.push([t("Serial number"), d.serial]);
    if (d.drivers.length) L.push([t("Driver"), d.drivers.join(", ")]);
    (d.links || []).forEach(x => {
      if (x.kind === "net") L.push([t("Network"), x.name + (x.mac ? " · " + x.mac : "") + (x.state ? " · " + t(x.state === "up" ? "connected" : x.state === "down" ? "not connected" : x.state) : "")]);
      else if (x.kind === "disk") L.push([t("Drive"), x.name + " · " + usbSize(x.size) + (x.mounts.length ? " · " + t("opened at") + " " + x.mounts.join(", ") : " · " + t("not opened"))]);
      else if (x.kind === "video") L.push([t("Camera"), x.name + (x.label ? " · " + x.label : "")]);
      else if (x.kind === "serial") L.push([t("Serial port"), x.name]);
      else if (x.kind === "sound") L.push([t("Sound card"), x.name]);
    });
    const kv = el("div"); kv.style.cssText = "display:grid;grid-template-columns:max-content 1fr;gap:2px 12px;font-size:13px;margin-top:4px";
    L.forEach(([k, v]) => { kv.append(el("span", "mut", k), el("span", "", v)); }); c.appendChild(kv);
    if (!d.root && d.usb && parseFloat(d.usb) >= 3 && d.speed && d.speed < 5000) c.appendChild(el("div", "warnbox", "⚠ " + t("usb3-slow")));
    if (!d.root && d.ma >= 500) c.appendChild(el("div", "mut", "⚡ " + t("usb-hungry")));
    box.appendChild(c);
  });
  if (!j.ids) box.appendChild(el("div", "mut", t("usb-ids")));
}
(async () => { for (let i = 0; i < 30 && !LANG; i++) await new Promise(r => setTimeout(r, 100)); usbLoad(); })();
// ---- 2.95.97: reference scan - assistant, progress, reports ----
let RS = null, RSP = 0, RST = null, RSLIVE = null, RSREP = "";
const RSSET = [["refscan_pan_steps", "Directions side by side", 1, 12, 1], ["refscan_pan_from", "Turn from (% of the pan range)", 0, 100, 1], ["refscan_pan_to", "Turn to (% of the pan range)", 0, 100, 1],
  ["refscan_tilt_steps", "Heights (rows)", 1, 3, 1], ["refscan_tilt_mid", "Middle height (tilt %)", 20, 80, 1], ["refscan_tilt_span", "Distance between the rows (tilt %)", 4, 40, 1],
  ["refscan_photos", "Photos per direction (more = less noise)", 1, 5, 1], ["refscan_settle", "Wait after turning (seconds)", 0.5, 5, 0.5], ["refscan_sens", "Sensitivity of the comparison (%)", 10, 100, 5],
  ["refscan_min_area", "Smallest change (% of the picture)", 0.1, 5, 0.1]];
const RSOPT = [["refscan_on_arm", "Compare with the reference when armed"], ["refscan_push", "Push message when something is missing"], ["refscan_push_all", "Push message also for new or changed things"], ["refscan_pano_on", "Panorama report «Missing things» every morning (separate from the night report)"]];
async function rsPost(d) { return await fetch("/api/refscan", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: LANG}, d))}).then(x => x.json()).catch(() => null); }
async function rsSet(k, v) { await fetch("/api/set", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({key: k, value: v})}).catch(() => null); rsLoad(); }
async function rsMove(dir) { await fetch("/api/move", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({dir: dir, step: 4})}).catch(() => null); }
async function rsGo(op) { const r = await rsPost({op: op}); if (r && !r.ok && r.error) alert(r.error); rsLoad(); }
function rsStep(n) {
  RSP = n; try { localStorage.setItem("mw-rs-step", n); } catch (e) {}
  document.querySelectorAll("#c-refscan .rs-pane").forEach(x => x.hidden = +x.dataset.p !== n);
  document.querySelectorAll("#c-refscan .rs-steps>span").forEach(x => { x.classList.toggle("on", +x.dataset.n === n); x.classList.toggle("done", +x.dataset.n < n || (+x.dataset.n === 3 && RS && RS.ref)); });
  clearInterval(RSLIVE); RSLIVE = null;
  if (n === 1) { const im = $("#rs-live"); const go = () => { if (SEL === "refscan" && RSP === 1 && !document.hidden) im.src = "/snapshot.jpg?r=" + Date.now(); }; go(); RSLIVE = setInterval(go, 1200); }
  if (n === 2) rsSetPaint();
}
function rsSetPaint() {
  const C = (RS && RS.cfg) || {}, box = $("#rs-set"); box.textContent = "";
  RSSET.forEach(([k, lb, mn, mx, st]) => { const r = el("label", "opt"); r.style.display = "block";
    const v = C[k] ?? mn, top = el("div", "trow"); top.append(el("span", "", t(lb)), el("b", "", String(v))); top.style.justifyContent = "space-between";
    const i = document.createElement("input"); i.type = "range"; i.min = mn; i.max = mx; i.step = st; i.value = v; i.style.width = "100%";
    i.oninput = () => { top.lastChild.textContent = i.value; }; i.onchange = () => rsSet(k, +i.value); r.append(top, i); box.appendChild(r); });
  const n = (RS && RS.plan) || 0, sec = Math.round(n * ((+(C.refscan_settle || 1.5)) + 0.6 * (+(C.refscan_photos || 2)) + 0.8));
  $("#rs-plan").textContent = n + " " + t("directions") + " · " + t("about") + " " + (sec >= 60 ? Math.round(sec / 60) + " min" : sec + " s");
}
function rsOptsPaint() {
  const C = (RS && RS.cfg) || {}, box = $("#rs-opts"); if (box.dataset.k === JSON.stringify(C)) return; box.dataset.k = JSON.stringify(C); box.textContent = "";
  RSOPT.forEach(([k, lb]) => { const l = el("label", "opt"); const i = document.createElement("input"); i.type = "checkbox"; i.className = "sw"; i.checked = !!C[k];
    i.onchange = () => rsSet(k, i.checked); l.append(el("span", "", t(lb)), i); box.appendChild(l); });
  const l = el("label", "opt"); l.style.display = "block"; const top = el("div", "trow"); top.style.justifyContent = "space-between";
  top.append(el("span", "", t("Compare every (minutes while armed, 0 = off)")), el("b", "", String(C.refscan_every || 0)));
  const i = document.createElement("input"); i.type = "range"; i.min = 0; i.max = 240; i.step = 5; i.value = C.refscan_every || 0; i.style.width = "100%";
  i.oninput = () => { top.lastChild.textContent = i.value; }; i.onchange = () => rsSet("refscan_every", +i.value); l.append(top, i); box.appendChild(l);
}
async function rsLoad() {
  clearTimeout(RST);
  const r = await fetch("/api/refscan", {cache: "no-store"}).then(x => x.ok ? x.json() : null).catch(() => null);
  if (r) { RS = r; rsPaint(); }
  RST = setTimeout(rsLoad, RS && RS.busy ? 1000 : (SEL === "refscan" ? 4000 : 30000));
}
function rsWhen(ts) { const d = new Date(ts * 1000); return d.toLocaleDateString(LANG === "de" ? "de-CH" : undefined) + " " + d.toTimeString().slice(0, 5); }
function rsPaint() {
  const R = RS, L = (R.reports || [])[0];
  sum("refscan", R.busy ? (R.busy === "scan" ? t("Scanning") : t("Comparing")) + " " + R.step + "/" + R.n : !R.ref ? t("No reference yet") : L ? (L.missing ? "⚠ " + L.missing + " " + t("missing") : "✓ " + t("nothing missing")) : R.ref.n + " " + t("directions"),
      R.busy ? "warn" : L && L.missing ? "bad" : R.ref ? "ok" : "");
  if (!RSP) { let n = 0; try { n = +localStorage.getItem("mw-rs-step") || 0; } catch (e) {} rsStep(n || (R.ref ? 4 : 1)); }
  const pr = R.n ? Math.round(100 * Math.max(0, R.step - (R.busy ? 0.5 : 0)) / R.n) : 0;
  [["scan", "#rs-prog", "#rs-msg"], ["compare", "#rs-prog2", "#rs-msg2"]].forEach(([op, pg, mg]) => {
    $(pg).hidden = R.busy !== op; $(pg).firstChild.style.width = pr + "%";
    $(mg).textContent = R.busy === op ? (op === "scan" ? t("Scanning") : t("Comparing")) + ": " + t("direction") + " " + R.step + " / " + R.n + " …" : (R.msg ? t(R.msg) : ""); });
  $("#rs-scan").disabled = !!R.busy; $("#rs-cmp").disabled = !!R.busy || !R.ref; $("#rs-stop").hidden = !R.busy;
  const rb = $("#rs-ref"), RF = R.refs || {}, key = JSON.stringify(["day", "night"].map(k => RF[k] ? [RF[k].t, RF[k].n, (RF[k].watch || []).length] : 0));
  if (rb.dataset.k !== key) { rb.dataset.k = key; rb.textContent = "";
    ["day", "night"].forEach(k => { const F = RF[k]; if (!F) return;
      rb.appendChild(el("div", "mut", (k === "day" ? "☀️ " + t("Day reference") : "🌙 " + t("Night reference")) + " · " + rsWhen(F.t) + " · " + t("tap a photo to guard a thing")));
      const g_ = el("div", "rs-grid");
      (F.positions || []).forEach(p => { const f = el("figure"); const im = document.createElement("img"); im.loading = "lazy"; im.src = "/refscan/file/" + F.dir + "/" + p.file + "?t=" + F.t;
        const nw = (F.watch || []).filter(w => w.pos === p.i); f.append(im, el("figcaption", "", t("Pan") + " " + p.pan + " % · " + t("Tilt") + " " + p.tilt + " %"));
        if (nw.length) f.appendChild(el("i", "", "🛡 " + nw.map(w => w.name).join(", ")));
        f.onclick = () => rsEdit(k, p.i); g_.appendChild(f); });
      rb.appendChild(g_); }); }
  if (R.ref && R.busy !== "scan") $("#rs-msg").textContent = (R.msg ? t(R.msg) + " · " : "") + (R.dark ? "🌙 " + t("It is dark now: the scan saves the night reference.") : "☀️ " + t("It is light now: the scan saves the day reference."));
  rsOptsPaint();
  const rl = $("#rs-reps"), rk = JSON.stringify((R.reports || []).map(x => x.id));
  if (rl.dataset.k !== rk) { rl.dataset.k = rk; rl.textContent = "";
    if (!(R.reports || []).length) rl.appendChild(el("div", "mut", t("No report yet - press «Compare now».")));
    (R.reports || []).forEach(x => { const d = el("div", "rs-rep"); d.dataset.id = x.id;
      d.append(el("span", "", rsWhen(x.t) + " · " + t(x.reason || "")), el("b", "", (x.missing ? "⚠ " + x.missing + " " + t("missing") + " · " : "") + x.new + " " + t("new") + " · " + x.changed + " " + t("changed")));
      d.onclick = () => rsReport(x.id); rl.appendChild(d); });
    if ((R.reports || []).length && !RSREP) rsReport(R.reports[0].id); }
  rsPanoPaint();
}
async function rsPano(send) {                  // 2.96.1: the panorama with the marks of the last 24 hours
  $("#rs-pano").textContent = "⏳ …";
  const r = await post("/api/refscan", {op: "panorama", send: send, lang: LANG});
  if (!r.ok) { $("#rs-pano").textContent = "⚠ " + (r.error || t("error")); return; }
  RS = r; $("#rs-pano").dataset.k = ""; rsPanoPaint();
}
function rsPanoPaint() {
  const box = $("#rs-pano"); if (!box || !RS) return; const L = RS.panoramas || [], k = JSON.stringify(L.map(x => x.file));
  if (box.dataset.k === k) return; box.dataset.k = k; box.textContent = "";
  if (!L.length) { box.appendChild(el("div", "mut", t("No panorama yet."))); return; }
  L.forEach((x, i) => { const d = document.createElement("details"); d.open = i === 0; const sm = document.createElement("summary");
    const g = x.marks.filter(m => m.kind === "missing" && !m.back).length, n = x.marks.filter(m => m.kind === "new" && !m.back).length;
    sm.textContent = x.file.slice(6, 8) + "." + x.file.slice(4, 6) + ". " + x.file.slice(9, 11) + ":" + x.file.slice(11, 13) + " · " + (g ? "⚠ " + g + " " + t("gone") + " · " : "") + n + " " + t("new") + " · " + x.checks + " " + t("checks");
    const a = document.createElement("a"); a.href = "/refscan/file/panorama/" + x.file; a.target = "_blank";
    const im = document.createElement("img"); im.src = a.href; im.loading = "lazy"; im.style.cssText = "width:100%;border-radius:8px;margin-top:6px"; a.appendChild(im);
    const ul = el("div", "mut"); x.marks.slice(0, 30).forEach(m => ul.appendChild(el("div", "", ({missing: "🔴 ", new: "🟢 ", changed: "🟠 "}[m.kind] || "") + (m.name ? m.name + " · " : "") + t({missing: "gone", new: "new", changed: "changed"}[m.kind]) + " " + rsWhen(m.first).split(" ").pop() + (m.back ? " · " + t("back") + " " + rsWhen(m.back).split(" ").pop() : ""))));
    d.append(sm, a, ul); box.appendChild(d); });
}
async function rsReport(id) {
  RSREP = id; document.querySelectorAll(".rs-rep").forEach(x => x.classList.toggle("sel", x.dataset.id === id));
  const r = await rsPost({op: "report", id: id}); const box = $("#rs-rep"); box.textContent = ""; if (!r || !r.report) return;
  const P = r.report.positions || [];
  box.appendChild(el("h3", "", t("Report") + " " + rsWhen(r.report.t)));
  box.appendChild(el("div", "mut", r.report.missing + " " + t("missing") + " · " + r.report.new + " " + t("new") + " · " + r.report.changed + " " + t("changed") + " · " + P.length + " " + t("directions")
    + " · " + (r.report.ref_kind === "night" ? "🌙 " + t("night reference") : "☀️ " + t("day reference")) + (!!r.report.dark_now !== (r.report.ref_kind === "night") ? " (" + t("other light now - take a reference for this light too") + ")" : "")));
  (r.report.watch || []).forEach(w => box.appendChild(el("div", "rs-ch " + (w.gone ? "gone" : "ok"), (w.gone ? "🚨 " + t("Guarded thing missing") + ": " : "🛡 " + t("guarded, still there") + ": ") + w.name)));
  const lab = {missing: "missing", new: "new", changed: "changed"};
  P.filter(p => (p.changes || []).length).concat(P.filter(p => !(p.changes || []).length)).forEach(p => {
    const w = el("div", "");
    w.appendChild(el("div", "mut", t("Pan") + " " + p.pan + " % · " + t("Tilt") + " " + p.tilt + " %" + ((p.changes || []).length ? "" : " · ✓ " + t("no change"))));
    if ((p.changes || []).length) {
      const pr = el("div", "rs-pair"); const a = el("div"), b = el("div");
      const ia = document.createElement("img"); ia.src = "/refscan/file/reports/" + id + "/ref_" + String(p.i).padStart(2, "0") + ".jpg"; a.append(ia, el("div", "", t("Reference")));
      const ib = document.createElement("img"); ib.src = "/refscan/file/reports/" + id + "/cur_" + String(p.i).padStart(2, "0") + ".jpg"; b.append(ib, el("div", "", t("Now")));
      pr.append(a, b); w.appendChild(pr);
      p.changes.forEach(c => w.appendChild(el("div", "rs-ch " + c.kind, "● " + t(lab[c.kind] || c.kind) + " · " + Math.round(c.w * c.h * 1000) / 10 + " % " + t("of the picture")))); }
    box.appendChild(w); });
}
document.querySelectorAll("#c-refscan .rs-steps>span").forEach(x => x.onclick = () => rsStep(+x.dataset.n));
// 2.95.98: guard things - drag a box over the thing on a reference photo and name it
function rsEdit(kind, pos) {
  const F = ((RS || {}).refs || {})[kind]; if (!F) return;
  const p = (F.positions || []).find(x => x.i === pos); let items = JSON.parse(JSON.stringify(F.watch || []));
  const ov = el("div"); ov.id = "rs-ed"; document.body.appendChild(ov);
  const hd = el("div", "trow"); hd.append(el("b", "", "🛡 " + t("Guard things") + " · " + t("Pan") + " " + p.pan + " %"));
  const cv = el("div", "cv"); const im = document.createElement("img"); im.src = "/refscan/file/" + F.dir + "/" + p.file + "?t=" + F.t; cv.appendChild(im);
  const help = el("div", "mut", t("Drag a box over the thing (bike, grill, tent …) and give it a name. If it is missing at a comparison, MoveEye gives an alarm at once."));
  const list = el("div", ""); const bar = el("div", "trow");
  const save = el("button", "", "✓ " + t("Save")), cancel = el("button", "sec", t("Cancel")); bar.append(save, cancel);
  ov.append(hd, help, cv, list, bar);
  const paint = () => { cv.querySelectorAll(".bx").forEach(b => b.remove()); list.textContent = "";
    items.forEach((w, n) => { if (w.pos !== pos) return; const b = el("div", "bx"); Object.assign(b.style, {left: w.x * 100 + "%", top: w.y * 100 + "%", width: w.w * 100 + "%", height: w.h * 100 + "%"});
      b.appendChild(el("span", "", w.name)); cv.appendChild(b);
      const r_ = el("div", "trow"); const del = el("button", "sec", "✕"); del.onclick = () => { items.splice(n, 1); paint(); }; r_.append(el("span", "", "🛡 " + w.name), del); list.appendChild(r_); }); };
  let st = null, dr = null;
  const at = e => { const b = cv.getBoundingClientRect(); return [Math.max(0, Math.min(1, (e.clientX - b.left) / b.width)), Math.max(0, Math.min(1, (e.clientY - b.top) / b.height))]; };
  cv.addEventListener("pointerdown", e => { e.preventDefault(); st = at(e); dr = el("div", "bx drag"); cv.appendChild(dr); try { cv.setPointerCapture(e.pointerId); } catch (x) {} });
  cv.addEventListener("pointermove", e => { if (!st) return; const q = at(e);
    Object.assign(dr.style, {left: Math.min(st[0], q[0]) * 100 + "%", top: Math.min(st[1], q[1]) * 100 + "%", width: Math.abs(q[0] - st[0]) * 100 + "%", height: Math.abs(q[1] - st[1]) * 100 + "%"}); });
  cv.addEventListener("pointerup", e => { if (!st) return; const q = at(e), a = st; st = null; dr.remove();
    const w = Math.abs(q[0] - a[0]), h = Math.abs(q[1] - a[1]); if (w < 0.02 || h < 0.02) return;
    const name = prompt(t("Name of the thing (e.g. bike)"), t("Thing")); if (name === null) return;
    items.push({pos: pos, x: Math.min(a[0], q[0]), y: Math.min(a[1], q[1]), w: w, h: h, name: name.slice(0, 40) || t("Thing")}); paint(); });
  cancel.onclick = () => ov.remove();
  save.onclick = async () => { const r = await rsPost({op: "watch", kind: kind, items: items}); if (r && r.ok) { ov.remove(); $("#rs-ref").dataset.k = ""; rsLoad(); } else alert((r && r.error) || t("error")); };
  paint();
}
Object.assign(I18N.de, {"Day reference": "Tag-Referenz", "Night reference": "Nacht-Referenz", "day reference": "Tag-Referenz", "night reference": "Nacht-Referenz",
  "tap a photo to guard a thing": "Foto antippen, um einen Gegenstand zu bewachen", "It is dark now: the scan saves the night reference.": "Jetzt ist es dunkel: der Scan speichert die Nacht-Referenz.",
  "It is light now: the scan saves the day reference.": "Jetzt ist es hell: der Scan speichert die Tag-Referenz.", "other light now - take a reference for this light too": "jetzt anderes Licht – auch für dieses Licht eine Referenz aufnehmen",
  "Guarded thing missing": "Bewachter Gegenstand fehlt", "guarded, still there": "bewacht, noch da", "Guard things": "Gegenstände bewachen", "Save": "Speichern", "Cancel": "Abbrechen",
  "Drag a box over the thing (bike, grill, tent …) and give it a name. If it is missing at a comparison, MoveEye gives an alarm at once.": "Ein Rechteck über den Gegenstand ziehen (Velo, Grill, Zelt …) und ihm einen Namen geben. Fehlt er bei einem Vergleich, gibt MoveEye sofort Alarm.",
  "Name of the thing (e.g. bike)": "Name des Gegenstands (z. B. Velo)", "Thing": "Gegenstand", "night reference saved": "Nacht-Referenz gespeichert"});
(async () => { for (let i = 0; i < 30 && !LANG; i++) await new Promise(r => setTimeout(r, 100)); rsLoad(); })();
Object.assign(I18N.de, {"Reference scan": "Referenz-Scan", "Set up": "Aufstellen", "Settings": "Einstellungen", "Scan": "Scannen", "Compare": "Vergleichen", "Middle": "Mitte", "Next": "Weiter", "Back": "Zurück",
  "refscan-note": "MoveEye fährt mit dem Kopf ein Raster von Richtungen ab und speichert Fotos als Referenz. Später fährt es dieselben Richtungen wieder ab und zeigt im Bericht, was fehlt, was neu ist und was sich verändert hat – z. B. ob das Velo, der Grill oder das Zelt noch da ist.",
  "rs-setup": "Stell die Kamera dort auf, wo sie bleiben soll, und richte sie gerade aus. Die Mitte zeigt in die Hauptrichtung. Danach die Kamera nicht mehr verschieben – sonst passt die Referenz nicht mehr.",
  "rs-settings": "Wie viele Richtungen und Höhen der Kopf abfährt. Mehr Richtungen = genauer, dauert länger.",
  "rs-scan": "Jetzt bitte nichts mehr verändern und aus dem Bild gehen. MoveEye fährt alle Richtungen ab und speichert die Fotos als Referenz.",
  "rs-compare": "Fährt dieselben Richtungen ab und vergleicht mit der Referenz. Rot = fehlt, blau = neu, orange = verändert.",
  "Panorama report «Missing things»": "Panorama-Bericht «Fehlende Gegenstände»", "pano-desc": "Ein Bild aus allen Richtungen des Referenz-Scans; darauf markiert, was verschwunden (rot), dazugekommen (grün) oder verändert (orange) ist – mit der Uhrzeit. Kommt jeden Morgen mit dem Nachtbericht, wenn oben eingeschaltet.",
  "Make it now (last 24 h)": "Jetzt erstellen (letzte 24 h)", "Make and send": "Erstellen und senden", "No panorama yet.": "Noch kein Panorama.", "gone": "weg", "back": "wieder da", "checks": "Vergleiche",
  "Panorama report «Missing things» every morning (separate from the night report)": "Panorama-Bericht «Fehlende Gegenstände» jeden Morgen (getrennt vom Nachtbericht)",
  "Take the reference now": "Referenz jetzt aufnehmen", "Compare now": "Jetzt vergleichen", "New reference": "Neue Referenz", "Reports": "Berichte", "Report": "Bericht",
  "Directions side by side": "Richtungen nebeneinander", "Turn from (% of the pan range)": "Drehen von (% des Schwenkbereichs)", "Turn to (% of the pan range)": "Drehen bis (% des Schwenkbereichs)",
  "Heights (rows)": "Höhen (Reihen)", "Middle height (tilt %)": "Mittlere Höhe (Neigung %)", "Distance between the rows (tilt %)": "Abstand der Reihen (Neigung %)",
  "Photos per direction (more = less noise)": "Fotos pro Richtung (mehr = weniger Rauschen)", "Wait after turning (seconds)": "Warten nach dem Drehen (Sekunden)",
  "Sensitivity of the comparison (%)": "Empfindlichkeit des Vergleichs (%)", "Smallest change (% of the picture)": "Kleinste Veränderung (% des Bildes)",
  "Compare with the reference when armed": "Beim Einschalten des Schutzes mit der Referenz vergleichen", "Push message when something is missing": "Push-Meldung, wenn etwas fehlt",
  "Push message also for new or changed things": "Push-Meldung auch bei Neuem oder Verändertem", "Compare every (minutes while armed, 0 = off)": "Vergleichen alle (Minuten, wenn der Schutz an ist; 0 = aus)",
  "directions": "Richtungen", "direction": "Richtung", "about": "etwa", "Scanning": "Scannen", "Comparing": "Vergleichen", "No reference yet": "Noch keine Referenz", "missing": "fehlt", "new": "neu", "changed": "verändert",
  "nothing missing": "nichts fehlt", "Reference": "Referenz", "Now": "Jetzt", "Pan": "Schwenk", "Tilt": "Neigung", "no change": "keine Veränderung", "of the picture": "des Bildes",
  "No report yet - press «Compare now».": "Noch kein Bericht – «Jetzt vergleichen» drücken.", "by hand": "von Hand", "night test": "Nacht-Test", "armed": "beim Einschalten des Schutzes", "simulator": "vom Simulator", "window": "im Fenster",
  "reference saved": "Referenz gespeichert", "report ready": "Bericht fertig", "stopped": "abgebrochen", "no picture from the camera": "kein Bild von der Kamera",
  "a scan is already running": "es läuft schon ein Scan", "no camera": "keine Kamera", "no reference yet - scan first": "noch keine Referenz – zuerst scannen"});
function pick(k, push) {
  if (!document.getElementById("c-" + k)) k = "net";
  if (SEL === "focus" && k !== "focus" && FON) focusToggle();
  SEL = k;
  document.querySelectorAll("section.tool").forEach(x => x.hidden = x.dataset.k !== k);
  document.querySelectorAll(".tli").forEach(x => x.classList.toggle("on", x.dataset.k === k));
  document.body.classList.add("picked");
  if (window.MW_SOLO) return;
  try { localStorage.setItem("mw-tool-sel", k); } catch (e) {}
  if (push !== false && location.hash !== "#" + k) history.pushState(null, "", "#" + k);
  if (matchMedia("(max-width:760px)").matches) scrollTo(0, 0);
}
function showList() { document.body.classList.remove("picked"); if (location.hash) history.pushState(null, "", location.pathname); }
addEventListener("popstate", () => { const h = location.hash.slice(1); if (h) pick(h, false); else document.body.classList.remove("picked"); });
fetch("/api/dev", {cache: "no-store"}).then(r => r.ok ? r.json() : null).then(j => { if (j && j.ok && j.dev && j.dev.on) { const e = document.getElementById("t-dev"); if (e) e.style.display = ""; } }).catch(() => {});
(function () { let k = location.hash.slice(1);
  if (window.MW_SOLO) { pick(window.MW_SOLO, false); return; }
  if (k === "party") { location.replace("/party"); return; }               // the game corner has its own tab now
  if (k === "party" || !k) { try { k = localStorage.getItem("mw-tool-sel") || ""; } catch (e) {} if (k === "party") k = ""; }
  if (location.hash || !matchMedia("(max-width:760px)").matches) pick(k || "net", false);
  else { SEL = k || "net"; document.querySelectorAll("section.tool").forEach(x => x.hidden = x.dataset.k !== SEL); } })();
function sum(k, text, cls) { const e = $("#s-" + k); if (!e) return; e.textContent = PLAIN(text); const d = $("#d-" + k); if (d) d.className = "tdot" + (cls ? " " + cls : ""); }
function drawSums() {
  const N = S.net, C = S.cfg || {};
  const nnew = N.devices.filter(d => d.new).length;
  sum("net", N.running ? t("running…") : N.t ? N.devices.length + " " + t("devices") + (nnew ? " · ★ " + nnew + " " + t("new") : "") : "", nnew ? "warn" : "");
  const P = S.presence; sum("pres", !(C.presence_macs || []).length ? t("No device marked") : P.here == null ? "…" : P.here ? "✅ " + t("Here") : "🚶 " + t("Away"), P.here ? "ok" : "");
  const Q = S.speed, L = Q.hist[Q.hist.length - 1];
  sum("speed", Q.running ? t("running…") : L ? (L.error ? "⚠ " + t("error") : "↓ " + L.down_mbit + " · ↑ " + L.up_mbit + " Mbit/s") : "", L && L.error ? "warn" : "");
  const it = S.sec.items || [], nb = it.filter(x => x.level === "bad").length, nw = it.filter(x => x.level === "warn").length;
  sum("sec", S.sec.running ? t("running…") : it.length ? [nb ? nb + " " + t(nb === 1 ? "problem" : "problems") : "", nw ? nw + " " + t(nw === 1 ? "warning" : "warnings") : ""].filter(Boolean).join(" · ") || t("all ok") : "",
      !it.length ? "" : nb ? "bad" : nw ? "warn" : "ok");
  const D = S.dual || {}, G = D.guard || {};
  sum("dual", D.repeater ? "✅ " + t("Repeater on") : D.on ? t("Two adapters in use") : (D.adapters || []).length >= 2 ? t("Second adapter not in use") : t("Only one Wi-Fi adapter"), D.repeater ? "ok" : D.unstable || D.online === false ? "warn" : "");
  const recent = (G.alarms || []).some(a => Date.now() / 1000 - a.t < 3600);
  sum("guard", recent ? "⚠ " + t("Wi-Fi jamming!") : G.state === "listening" ? "👂 " + t("listening") : G.state === "off" ? t("off") : t(G.state || ""), recent ? "bad" : G.state === "listening" ? "ok" : "");
  const W = S.wifi; sum("wifi", W.running ? t("running…") : W.best ? t("Best channel") + " " + W.best + " · " + W.nets.length + " " + t("networks") : "");
  const B = S.bt, tk = (B.trackers || []).length; sum("bt", B.running ? t("running…") : B.t ? B.devices.length + " " + t("devices") + (tk ? " · 📍 " + tk : "") : "", tk ? "warn" : "");
  const V = S.servo; if (V.running || V.msg) sum("servo", V.running ? t("running…") : V.msg === "ok" ? "✅ " + t("ok") : "⚠ " + (V.bad || ""), V.msg && V.msg !== "ok" ? "warn" : V.msg ? "ok" : "");   // the test is on /servo (541)
  const R = (S.sd || {}).res || {}; sum("sd", S.sd.running ? t("running…") : R.write_mb_s != null ? "✍ " + R.write_mb_s + " · 📖 " + R.read_mb_s + " MB/s" : "", {ok: "ok", warn: "warn", bad: "bad"}[R.verdict] || "");
  if (S.power) sum("pow", S.power.watts.toFixed(1) + " W");
}
// tool mode: MoveEye rests, the tools get the whole computer
async function toolmode(min) {
  if (min > 0 && S && S.toolmode && S.toolmode.armed && !confirm(t("tm-confirm"))) return;
  const r = await post("/api/tools", {action: "toolmode", minutes: min}); if (!r.ok) toast(r.error || t("not possible")); else { S.toolmode = r.toolmode; drawTm(); }
}
function drawTm() {
  const M = S.toolmode || {}; $("#tm").classList.toggle("on", !!M.on); $("#tm-off").hidden = !!M.on; $("#tm-on").hidden = !M.on;
  $("#tm-cpu").textContent = M.cpu != null ? "CPU " + Math.round(M.cpu) + " %" + (M.temp != null ? " · " + Math.round(M.temp) + " °C" : "") : "";
  $("#tm-note").textContent = M.on ? t("Camera, detection and alarms are paused - they come back by themselves.") : t("tm-note");
  if (M.on) $("#tm-until").textContent = t("paused until") + " " + new Date(M.until * 1000).toLocaleTimeString(LOCALE || undefined, {hour: "2-digit", minute: "2-digit"});
}
// second Wi-Fi adapter + guard
async function dualSet(key, value) { const r = await post("/api/tools", {action: "dual", key, value}); if (!r.ok) toast(r.error || t("not possible")); setTimeout(load, 800); }
function dualRep(cb) {
  if (cb.checked && !confirm(t("rep-confirm"))) { cb.checked = false; return; }
  dualSet("wifi_repeater", cb.checked);
}
async function dualAct(a) { await post("/api/tools", {action: a}); setTimeout(load, 1500); }
function spark(id, vals, lo, hi) { const n = vals.length; const sv = $(id).closest("svg"); if (sv) sv.style.display = n < 2 ? "none" : ""; $(id).setAttribute("points", n < 2 ? "" : vals.map((v, i) => (i * 300 / (n - 1)).toFixed(1) + "," + (48 - 46 * (Math.max(lo, Math.min(hi, v)) - lo) / Math.max(1, hi - lo)).toFixed(1)).join(" ")); }
function drawDual() {
  const D = S.dual; if (!D) return; const C = D.cfg || {};
  ["wifi_repeater", "wifi_swap", "net_inet_notify", "wifi_guard", "wifi_count", "wifi_presence"].forEach(k => { const e = $("#du-" + k); if (e) e.checked = !!C[k]; });
  const th = $("#du-wifi_guard_thr"); if (document.activeElement !== th) th.value = C.wifi_guard_thr || 20;
  const n = (D.adapters || []).length;
  $("#du-st").textContent = D.repeater ? "✅ " + t("Repeater on") : D.on ? "📡 " + t("Two adapters in use") : n >= 2 ? "⏸ " + t("Second adapter not in use") : "1️⃣ " + t("Only one Wi-Fi adapter");
  let note = "";
  if (D.on) note = t("Own Wi-Fi") + ": " + D.ap + (D.hotspot.on ? " «" + (D.hotspot.ssid || "") + "» · " + (D.hotspot.clients || 0) + " " + t("devices") : " (" + t("off") + ")")
      + " · " + t("Internet") + ": " + D.up + (D.uplink.connected ? " «" + D.uplink.ssid + "» " + D.uplink.dbm + " dBm" : " (" + t("not connected") + ")");
  else if (D.msg) note = t(D.msg);
  if (n < 2) note += (note ? " · " : "") + t("Plug in a USB Wi-Fi stick: then the Pi makes its own Wi-Fi and gets the internet from another network at the same time.");
  if (D.online === false) note += " · ⚠ " + t("no internet") + (D.offline_since ? " " + t("since") + " " + fmtT(D.offline_since) : "");
  if (D.unstable) note += " · ⚠ " + t("connection unstable");
  if (D.iso_msg) note += " · ⚠ " + t("No internet for devices") + ": " + D.iso_msg;
  $("#du-note").textContent = note;
  const ab = $("#du-ads"); ab.innerHTML = "";
  if (n) { const yn = (v, l) => t(l) + " " + (v == null ? "?" : v ? "✓" : "–");
    D.adapters.forEach(a => { const role = a.iface === D.ap ? t("own Wi-Fi") : a.iface === D.up ? t("internet") : "";
      const r = el("div", "adp"), h = el("div", "adp-h");
      h.append(el("b", "", (a.usb ? "USB · " : t("Built in") + " · ") + a.iface), el("span", "mut", role));
      const c = el("div", "", a.chip + (a.note ? " – " + t(a.note) : "")); if (a.usb_id) c.title = a.usb_id + " " + a.product + " (" + a.driver + ")";
      r.append(h, c, el("div", "mut", [yn(a.five, "5 GHz"), yn(a.ap, "Own Wi-Fi"), yn(a.monitor, "Listening")].join(" · "))); ab.appendChild(r); }); }
  const sg = (D.sig || []).map(x => x[1]); spark("#du-line", sg, -95, -30);
  $("#du-sig").textContent = sg.length ? t("Signal of the internet adapter (4 hours)") + ": " + sg[sg.length - 1] + " dBm" + (sg[sg.length - 1] < -75 ? " – " + t("weak: put the stick higher or nearer, use a USB extension cable") : "") : "";
  const lg = $("#du-log"); lg.innerHTML = ""; (D.log || []).slice(0, 6).forEach(x => lg.appendChild(el("div", "mut", fmtT(x.t) + " · " + t(x.text))));
  const G = D.guard || {};
  $("#gu-st").textContent = {listening: "👂 " + t("listening"), off: "⏸ " + t("off"), "no adapter": "–", "not possible": "⚠ " + t("not possible"), error: "⚠ " + t("error")}[G.state] || G.state;
  $("#gu-msg").textContent = G.msg ? t(G.msg) : (G.iface ? t("with") + " " + G.iface : "");
  const dm = G.deauth_min || []; spark("#gu-line", dm.map(x => x[1]), 0, Math.max(10, ...dm.map(x => x[2]))); spark("#gu-line2", dm.map(x => x[2]), 0, Math.max(10, ...dm.map(x => x[2])));
  $("#gu-info").textContent = G.state === "listening" ? t("Disconnect frames last minute") + ": " + (G.deauth_now || 0) + " " + t("against your networks") + ", " + (G.all_now || 0) + " " + t("in total")
      + (G.count_now != null ? " · " + t("devices nearby") + ": " + G.count_now : "") : "";
  const ga = $("#gu-alarms"); ga.innerHTML = ""; (G.alarms || []).slice(0, 5).forEach(a => ga.appendChild(el("div", "newdev", "⚠ " + fmtT(a.t) + " · " + a.n + " / " + a.all)));
}
// power calculator
let PWON = null;
function drawPower() {
  const P = S.power; if (!P) return;
  $("#p-now").textContent = P.watts.toFixed(1) + " W"; $("#p-src").textContent = "(" + t(P.src === "estimate" ? "estimate" : "measured") + ")";
  const box = $("#p-parts");
  if (PWON === null) { PWON = {}; P.parts.forEach(p => PWON[p.name] = p.w !== 0); }
  if (!box.dataset.n) { box.dataset.n = 1;
    P.parts.forEach(p => { const l = el("label"), c = el("input"); c.type = "checkbox"; c.className = "sw"; c.checked = PWON[p.name]; c.onchange = () => { PWON[p.name] = c.checked; calc(); };
      l.append(el("span", "", t(p.name)), el("b", "", ""), c); l.dataset.k = p.name; box.appendChild(l); }); }
  const wh = $("#p-wh"); if (!wh.value && P.cap_wh) wh.value = Math.round(P.cap_wh);
  $("#p-whn").textContent = P.cap_wh ? "" : "(" + t("Battery") + "?)"; wh.oninput = calc; calc();
}
const DEF_W = {"AI detection": 1.2, "Thermal camera": 0.4, "Power saving (when quiet)": -0.9, "Infrared light": 0.6, "White light": 0.6, "Own Wi-Fi (hotspot)": 0.3, "Patrol (servos)": 0.5};
function calc() {
  const P = S.power; let base = P.watts; P.parts.forEach(p => base -= p.w);
  let w = base; document.querySelectorAll("#p-parts label").forEach(l => { const k = l.dataset.k, v = DEF_W[k] || 0; l.querySelector("b").textContent = (v > 0 ? "+" : "") + v.toFixed(1) + " W"; if (PWON[k]) w += v; });
  w = Math.max(0.5, w); const wh = +$("#p-wh").value || 0; const r = $("#p-res"); r.innerHTML = "";
  [["Basic consumption", base.toFixed(1) + " W"], ["Consumption", w.toFixed(1) + " W · " + (w * 24).toFixed(0) + " Wh " + t("per day")], ["Running time", wh ? (wh / w).toFixed(1) + " " + t("hours") : "–"]]
    .forEach(([a, b]) => r.append(el("span", "", t(a)), el("span", "", b)));
}
// focus + microphone (live, twice a second while the page is open)
let FON = false, FH = [];
function focusToggle() { FON = !FON; $("#b-focus").textContent = t(FON ? "Stop" : "Start"); if (FON) FH = []; }
async function live() {
  if (!document.hidden) {
    const r = await fetch("/api/tools/live" + (FON ? "?focus=1" : "")).then(x => x.ok ? x.json() : null).catch(() => null);
    if (r) {
      const a = r.audio || {}, lv = a.level == null ? null : +a.level; sum("audio", a.dev ? "🎤 " + (lv == null ? "–" : lv.toFixed(0) + " dB") : t("no microphone")); $("#a-bar").style.width = lv == null ? "0" : Math.max(0, Math.min(100, Math.round((lv + 70) / 70 * 100))) + "%";
      $("#a-info").textContent = a.dev ? t("Microphone") + ": " + a.dev + " · " + t("Level") + " " + (lv == null ? "–" : lv.toFixed(0) + " dB") : t("no microphone");
      if (FON && r.focus && r.focus.val != null) { const f = r.focus; $("#f-spark").style.display = ""; FH.push(f.val); FH = FH.slice(-60);
        $("#f-val").textContent = Math.round(f.val); sum("focus", Math.round(f.val) + " / " + Math.round(f.best), "ok"); $("#f-best").textContent = t("best") + ": " + Math.round(f.best);
        $("#f-bar").style.width = Math.round(100 * f.val / Math.max(1, f.best)) + "%";
        const mx = Math.max(...FH, 1), mn = Math.min(...FH); $("#f-line").setAttribute("points", FH.map((v, i) => (i * 300 / 59).toFixed(1) + "," + (48 - 46 * (v - mn) / Math.max(1, mx - mn)).toFixed(1)).join(" "));
        if (FH.length > 6) { const a1 = FH.slice(-3).reduce((x, y) => x + y) / 3, a0 = FH.slice(-7, -4).reduce((x, y) => x + y) / 3; $("#f-trend").textContent = a1 > a0 * 1.05 ? "↑ " + t("sharper") : a1 < a0 * 0.95 ? "↓ " + t("less sharp") : "→ " + t("about the same"); } }
    }
  }
  setTimeout(live, 500);
}
async function soundTest() { const r = await post("/api/audio", {action: "test"}); if (r && r.ok === false) toast(r.error || t("not possible")); }
(async () => { await initAppearance(); load(); live(); })();
/*ALERTS*/
</script></body></html>
"""


