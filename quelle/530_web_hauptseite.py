#@ Motion Watch – Teil 530: Web: Hauptseite. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
WEB_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveEye</title>
<style>
/*BASECSS*/
main{display:grid;grid-template-columns:minmax(0,1fr) 400px;gap:16px;padding:16px;align-items:start;max-width:1800px;margin:0 auto}
body.noside main{grid-template-columns:minmax(0,1fr)}
@media(max-width:960px){main{grid-template-columns:minmax(0,1fr);row-gap:0}}
main>section,main>aside{min-width:0}
/* tablet / computer: both columns scroll on their own - the live picture always stays in view */
@media(min-width:961px){
  main{height:calc(100vh - var(--hdr-h,64px));height:calc(100dvh - var(--hdr-h,64px));align-items:stretch;padding-top:12px;padding-bottom:0}
  main>section,main>aside{min-height:0;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;padding-bottom:16px;scrollbar-width:thin}
  body.videoonly main{height:auto}
}
.vwrap{position:relative;border-radius:12px;overflow:hidden;background:#000;box-shadow:0 0 0 1px var(--line)}
#video{width:100%;display:block;background:#000;min-height:160px}
.vtag{position:absolute;bottom:10px;left:10px;display:flex;gap:6px;flex-wrap:wrap;pointer-events:none}
.vtag span{background:rgba(0,0,0,.62);color:#fff;border-radius:7px;padding:2px 9px;font-size:11px;font-weight:700;letter-spacing:.05em;-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}
.vtag .live::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:#3fcf6b;margin-right:6px;animation:pulse 1.6s infinite}
.vtag .rec{background:var(--red)}
@keyframes pulse{50%{opacity:.3}}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:9px;margin-top:12px}
.stat{background:var(--field);border:1px solid var(--line);border-radius:11px;padding:9px 12px}
.stat small{display:block;color:var(--mut);font-size:10px;font-weight:700;letter-spacing:.07em}
.stat b{font-size:22px;font-variant-numeric:tabular-nums}
.tg{padding:7px 0;cursor:pointer}
.sl{margin-top:9px}
.val{color:var(--mut);font-size:12px}
.pad{display:grid;grid-template-columns:repeat(3,58px);grid-template-rows:repeat(3,58px);gap:6px;touch-action:none;user-select:none}
details.grp>summary{font-size:12px;letter-spacing:.07em}
details.grp>summary .gi{font-size:16px;margin-right:9px;letter-spacing:0;filter:saturate(.9)}
details.grp>summary .gn{flex:1}
/* 2.95.70: symbols of the settings - coloured emoji with a green dot while on, or plain line symbols that turn green (switch «Symbols») */
.gi{display:inline-flex;align-items:center;justify-content:center;position:relative;flex:none}
.gi .is{display:none;width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;color:var(--mut)}
body.icplain .gi .ie{display:none}body.icplain .gi .is{display:inline-block}
.gi .gdot{display:none;position:absolute;right:-4px;bottom:-2px;width:8px;height:8px;border-radius:50%;background:var(--grn);box-shadow:0 0 0 2px var(--panel),0 0 7px var(--grn)}
body:not(.icplain) .mon>summary>.gi .gdot{display:block}body.icplain .mon>summary>.gi .is{color:var(--grn)}
details.sub>summary>.gi{margin-right:8px;font-size:13px;letter-spacing:0}details.sub>summary>.sn{flex:1}
.icseg{margin-top:8px}.icseg .mut{font-size:12px;margin:0 0 4px}
details.sub{border-top:1px solid var(--line);margin-top:12px;padding-top:9px}
details.sub>summary{font-size:10.5px;letter-spacing:.09em;color:var(--mut);font-weight:700;text-transform:uppercase;cursor:pointer;list-style:none;
  display:flex;justify-content:space-between;align-items:center;user-select:none}
details.sub>summary::-webkit-details-marker,details.adv>summary::-webkit-details-marker{display:none}
body.role-operate aside[data-view="sidebar"],body.role-view aside[data-view="sidebar"],body.role-operate #side-open,body.role-view #side-open,
body.role-view details[data-view="controls"],body.role-view #b-arm{display:none!important}
.sens-card{border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin:8px 0}.sens-card .row{gap:6px}.sens-card .row input{flex:1;min-width:0}
.sens-card .dot{font-size:14px}.sens-row{display:grid;grid-template-columns:1fr;gap:6px;margin-top:6px}.sens-row label{display:flex;flex-direction:column;gap:3px;font-size:12px;color:var(--mut)}
.sens-row select{width:100%}#sens-add,#sens-seen{flex-wrap:wrap}#sens-seen button{margin:4px 4px 0 0;font-size:13px}
details.sub>summary::after{content:"▾";font-size:12px;transition:transform .15s}details.sub:not([open])>summary::after{transform:rotate(-90deg)}
/* overview: the arrow of a topic / group is green while its main function is switched on */
details.sub.mon>summary::after,details.grp.mon>summary::after{color:var(--grn);font-size:15px;text-shadow:0 0 8px rgba(63,207,107,.55)}
details.sub.moff>summary::after,details.grp.moff>summary::after{color:var(--mut);opacity:.7}
details.sub[open]>summary{margin-bottom:7px}
details.sub.inline{border-top:0;margin-top:0;padding-top:0}details.sub.inline>summary{display:none}
details.grp>summary+details.sub,details.grp>summary+.blk{border-top:0;margin-top:0;padding-top:0}
.blk{border-top:1px solid var(--line);margin-top:12px;padding-top:7px}
#srch{position:relative;margin:0 0 12px}
/* the search and the three open / close buttons stay at the top while scrolling the settings */
#srch{position:sticky;top:var(--hdr-h,64px);z-index:25;background:var(--bg);padding:8px 0;margin:-8px 0 4px;box-shadow:0 -14px 0 var(--bg),0 6px 8px -6px rgba(0,0,0,.45)}
@media(min-width:961px){#srch{top:0}}
body.mobland #srch{top:0}
#srch.withall #allbtns{top:8px!important}
#srch{padding-left:54px!important}#srch .ic{left:66px!important}
#side-close{position:absolute;left:0;top:8px;width:46px;height:46px;padding:0;font-size:22px;border-radius:12px;display:inline-flex;align-items:center;justify-content:center}
#side-open{display:none;position:fixed;right:0;top:calc(var(--hdr-h,64px) + 14px);z-index:40;border-radius:12px 0 0 12px;padding:10px 8px;
  flex-direction:column;align-items:center;gap:6px;background:var(--panel);color:var(--txt);border:1px solid var(--line);border-right:0;box-shadow:var(--shadow)}
#side-open span{font-size:20px}#side-open b{writing-mode:vertical-rl;font-size:12px;letter-spacing:.08em;text-transform:uppercase}
body.noside #side-open{display:flex}
/* 2.95.73: phone / tablet - the settings button is at the bottom of the controls instead of the tab at the right edge */
#set-foot{display:none;width:100%;margin-top:6px;padding:11px;font-size:15px;grid-column:1/-1;justify-self:stretch}
@media(max-width:960px){body.noside #side-open{display:none}body.noside #set-foot{display:block}}
body.videoonly #set-foot{display:none!important}
/* 2.95.73: the mover stick only when switched on with 🚜 (per device) */
#mv-tog{display:none;flex:none;width:38px;padding:7px 0;font-size:15px}body.moveravail #mv-tog{display:inline-block}#mv-tog.on{background:var(--btn2);border-color:var(--grn)}body.videoonly #side-open,body.locked #side-close{display:none!important}
#lock-bar{display:flex;gap:10px;align-items:center;justify-content:space-between;margin:0 0 12px;padding:12px 14px;border-radius:12px;
  border:1px solid var(--yel);background:var(--panel)}
#lock-bar[hidden]{display:none}
/* compact header: the main state big, normal values hidden behind "all ok", rare buttons in the menu, one line when scrolled */
#b-arm{font-size:14px;font-weight:800;padding:5px 14px}
#b-arm.alarm{color:#fff;background:var(--red);border-color:var(--red);animation:apulse 1s infinite}
@keyframes apulse{50%{box-shadow:0 0 0 6px rgba(255,59,59,.25)}}
header .badge.q{display:none}
header.hx .badge.q:not([hidden]):not(.vh){display:inline-flex}
#btn-side,#btn-theme,#btn-lang,#btn-hdr{display:none}
header{transition:padding .2s}
@media(max-width:760px){header h1{order:-2}header .hdr-ctl{order:-1}}
body.hdr-small header{padding-top:6px;padding-bottom:6px}
body.hdr-small header .nav,body.hdr-small header .ver,body.hdr-small header .badge:not(#b-arm):not(.red){display:none!important}
.vmq{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:4px 0 10px}.vmq button{padding:7px 8px;font-size:13px}
#updbar{position:fixed;left:12px;right:12px;bottom:max(12px,env(safe-area-inset-bottom));z-index:89;display:flex;gap:10px;align-items:center;
  background:var(--panel);border:1px solid var(--grn);border-radius:12px;padding:10px 12px;box-shadow:var(--shadow);max-width:720px;margin:0 auto}
#updbar .mut{font-size:12px}
@media(max-width:520px){#updbar{flex-wrap:wrap}#updbar>div{flex-basis:100%!important}#updbar button{flex:1}}
body.locked .l-hide,body.locked .l-off,body.locked #srch:not(.withall),body.locked #view-menu-lock{display:none!important}
#srch input{width:100%;box-sizing:border-box;padding:11px 40px 11px 38px;font-size:15px;border-radius:12px}
#srch .ic{position:absolute;left:12px;top:50%;transform:translateY(-50%);opacity:.6;pointer-events:none}
#srch .x{position:absolute;right:6px;top:50%;transform:translateY(-50%);padding:4px 10px;border:0;background:none;color:var(--mut);font-size:18px;cursor:pointer}
#srch-none{margin-top:8px}
#allbtns button svg{display:none;width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
/* tablet / computer: "expand all" and "collapse all" as two small symbols right of the settings search */
#srch.withall{padding-right:152px}
#srch.withall #srch-in{height:46px}
#srch.withall .x{right:158px}
#srch.withall #allbtns{position:absolute;right:0;top:0;display:flex;gap:6px;margin:0!important;flex-wrap:nowrap}
#srch.withall #allbtns button{width:46px;height:46px;padding:0;display:inline-flex;align-items:center;justify-content:center;border-radius:12px;flex:none}
#srch.withall #allbtns button svg{display:block}#srch.withall #allbtns button span{display:none}
body.locked #srch.withall{display:flex!important;justify-content:flex-end;padding-right:0;min-height:46px}
body.locked #srch.withall>:not(#allbtns){display:none}body.locked #srch.withall #allbtns{position:static}
.s-hide{display:none!important}
.s-hit{box-shadow:0 0 0 2px var(--acc);border-radius:8px;padding:4px 6px}
.blk>h4{margin:0 0 2px;font-size:10.5px;letter-spacing:.09em;color:var(--mut);text-transform:uppercase;font-weight:700}
details.sub>.blk,details.grp>.blk{border-top:0;margin-top:0;padding-top:0}
.fine{margin:16px 0 0;padding-top:8px;border-top:1px dashed var(--line);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--acc2);font-weight:700}
.fine+details.sub{border-top:0;margin-top:4px}
details.adv{margin-top:12px;border-top:1px dashed var(--line);padding-top:8px}
details.adv>summary{cursor:pointer;color:var(--acc2);font-size:12.5px;font-weight:600;list-style:none;user-select:none}
details.adv>summary::before{content:"▸";display:inline-block;width:1.1em}details.adv[open]>summary::before{content:"▾"}
details.adv>.blk:first-of-type{border-top:0}
details.sblk{margin-top:10px;border-top:1px solid var(--line);padding-top:9px}
details.sblk>summary{display:flex;justify-content:space-between;align-items:center;color:var(--txt);font-size:13.5px;font-weight:700;padding:3px 0}
details.sblk>summary::before,details.sblk[open]>summary::before{content:none!important;display:none}details.sblk>summary::after{content:"▸";color:var(--mut);transition:transform .15s}details.sblk[open]>summary::after{transform:rotate(90deg)}
.mbar{margin-top:12px}.mbar .row{margin-bottom:3px}.mbar b{font-size:14px}
#settings .tg{padding:4px 0}#settings .sl{margin-top:7px}
@media(max-width:760px){.card{padding:12px}details.card>summary{font-size:11.5px}}
.pr-sw{margin-top:12px;padding-top:10px;border-top:1px solid var(--line);align-items:flex-start;cursor:pointer}
.pr-sw input.sw{margin-top:2px}#b-arm{user-select:none}
.wf-item{border:1px solid var(--line);border-radius:10px;margin-top:6px;background:var(--field);overflow:hidden}
.wf-item.on{border-color:var(--grn)}
.wf-head{display:flex;align-items:center;gap:8px;padding:8px 10px;cursor:pointer}
.wf-head b{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wf-tags{display:flex;gap:6px;align-items:center}
.wf-form,.wf-item>.mut{padding:0 10px 10px}.wf-item>input{margin:10px 10px 6px;width:calc(100% - 20px)!important}
.wf-saved{padding:6px 0;border-bottom:1px solid var(--line)}.wf-saved:last-child{border-bottom:0}
.wbars{display:inline-flex;align-items:flex-end;gap:1.5px;height:11px;margin-right:3px}
.wbars i{display:block;width:3px;background:currentColor;opacity:.25;border-radius:1px}
.wbars i:nth-child(1){height:3px}.wbars i:nth-child(2){height:5px}.wbars i:nth-child(3){height:8px}.wbars i:nth-child(4){height:11px}
.wbars i.on{opacity:1}
.qsw{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px 6px;margin-top:12px;width:100%;max-width:300px;margin-left:auto;margin-right:auto}
.qsw button{display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 2px 5px;border-radius:12px;background:var(--btn2);color:var(--txt);
  border:1px solid var(--line);font-size:19px;line-height:1.1;min-width:0}
.qsw button small{font-size:10px;color:var(--mut);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.qsw button.on{background:rgba(63,185,80,.16);border-color:var(--grn);box-shadow:0 0 0 2px rgba(63,185,80,.18)}.qsw button.on small{color:var(--grn)}
.qsw button.armed{background:rgba(240,136,62,.16);border-color:var(--org);animation:lpulse 1.2s infinite}.qsw button.armed small{color:var(--org)}
.qsw button.talking{background:rgba(255,59,59,.2);border-color:var(--red)}.qsw button.talking small{color:var(--red)}
.qsw button[data-talk]{touch-action:none;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
.qsw button.rec{background:rgba(255,59,59,.18);border-color:var(--red);animation:lpulse 1.6s infinite}.qsw button.rec small{color:var(--red)}
.qsw button.flash{background:var(--acc);color:#fff}
.qsw button:disabled{opacity:.35}
body.padmode .qsw{margin-top:12px}
.stickbox{display:flex;flex-direction:column;align-items:center;gap:10px}
/* ---- compact controls: stick | quick switches | small things - picture always fully visible (tablet / computer) ---- */
.ctl-grid{display:block}
#ctl-left{display:grid;grid-template-columns:auto 190px minmax(0,520px);grid-template-areas:"stick side mid";justify-content:space-between;gap:14px 24px;align-items:center;padding:0 6px}
#ctl-left .ctl-stick{grid-area:stick}#ctl-left .ctl-side{grid-area:side}#ctl-left .ctl-mid{grid-area:mid}
#ctl-left .stick{width:172px;height:172px}
#ctl-left .qsw{grid-template-columns:repeat(5,minmax(0,1fr));gap:10px 8px;max-width:none;margin:0}
.ctl-side{display:flex;flex-direction:column;gap:7px}
.ctl-side select{width:100%;padding:7px 8px}
.ctl-side .sr.spd select{flex:1;min-width:0;width:auto}.ctl-side .sr.spd button{flex:none;width:38px;padding:7px 0;font-size:15px}
/* ⇆ swap sides (left- / right-handed): the stick and the small buttons change places, in landscape the control column goes
   to the other side of the picture, in fullscreen the stick too */
body.swapside #ctl-left{grid-template-columns:190px auto minmax(0,520px);grid-template-areas:"side stick mid"}
@media(max-width:1180px) and (min-width:961px){body.swapside #ctl-left{grid-template-columns:170px auto minmax(0,1fr)}}
body.swapside.mobctl #ctl-left{grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"side stick" "mid mid"}
body.swapside.mobland #ctl-left{grid-template-columns:1fr;grid-template-areas:"stick" "side"}
body.swapside.mobland #vcard{grid-template-columns:auto minmax(0,1fr)}
body.swapside.mobland #vcard>.vwrap{grid-column:2}body.swapside.mobland #mctl{grid-column:1}
.ctl-side .sr{display:flex;gap:6px}.ctl-side .sr button{flex:1;padding:7px 4px;font-size:12.5px;white-space:nowrap}
.ctl-side .sr button{min-width:0;overflow:hidden;text-overflow:ellipsis}.ctl-side .sr button:last-child:not(:first-child){flex:0 1 auto}
.ctl-side .seg{display:flex}.ctl-side .seg button{flex:1;padding:6px 4px}
.ctl-side .row{gap:6px}.ctl-side .row select{width:auto;flex:1}
#patrol-st{margin-top:6px;font-size:11.5px;text-align:center}
#lights-box,#relays-box{margin:6px 0 10px}
@media(min-width:961px){
  main>section{display:flex;flex-direction:column}
  main>section>#vcard{flex:1 1 auto;min-height:220px;display:flex;flex-direction:column}
  main>section>#vcard>.vwrap{flex:1 1 auto;min-height:0;display:flex;align-items:center;justify-content:center;background:#000}
  main>section>#vcard #video{height:100%;width:100%;object-fit:contain;min-height:0}
  main>section>details[data-view="controls"]{flex:none;margin-top:12px;margin-bottom:0}
}
@media(max-width:1180px) and (min-width:961px){#ctl-left .stick{width:150px;height:150px}#ctl-left{grid-template-columns:auto 170px minmax(0,1fr);gap:12px 18px}}
/* phone: stick and small things side by side, the quick switches below */
body.mobctl #ctl-left{grid-template-columns:auto minmax(0,1fr);grid-template-areas:"stick side" "mid mid";gap:12px}
body.mobctl #ctl-left .ctl-stick{grid-area:stick}body.mobctl #ctl-left .ctl-side{grid-area:side}body.mobctl #ctl-left .ctl-mid{grid-area:mid}
body.mobctl #ctl-left .qsw{grid-template-columns:repeat(5,minmax(0,1fr))}
body.mobctl #ctl-left .stick{width:150px;height:150px}
body.mobctl details[data-view="controls"]{display:none}
body.mobland #ctl-left{grid-template-columns:1fr;grid-template-areas:"stick" "side"}
body.mobland #ctl-left .ctl-mid{display:none}body.mobland #ctl-left .stick{width:116px;height:116px}
body.mobland #ctl-left{gap:6px}body.mobland .ctl-side{gap:4px}
body.mobland .ctl-side select{padding:3px 6px;font-size:12px}
body.mobland .ctl-side .sr{gap:4px}body.mobland .ctl-side .sr button{padding:4px 3px;font-size:11.5px}
body.mobland .ctl-side .seg button{padding:3px 4px;font-size:12px}
body.mobland #spos-txt{font-size:10px;margin-top:-2px}

.stick{position:relative;width:184px;height:184px;border-radius:50%;touch-action:none;user-select:none;-webkit-user-select:none;cursor:grab;
  background:radial-gradient(circle at 50% 50%,var(--field) 0,var(--field) 38%,var(--panel2) 100%);border:1px solid var(--line);
  box-shadow:inset 0 2px 14px rgba(0,0,0,.35),0 0 0 5px var(--glow)}
.stick::before,.stick::after{content:"";position:absolute;background:var(--line);left:50%;top:50%;transform:translate(-50%,-50%);pointer-events:none}
.stick::before{width:1px;height:78%}.stick::after{height:1px;width:78%}
.stick .ar{position:absolute;color:var(--mut);font-size:11px;pointer-events:none;opacity:.8}
.stick .ar.u{top:7px;left:50%;transform:translateX(-50%)}.stick .ar.d{bottom:7px;left:50%;transform:translateX(-50%)}
.stick .ar.l{left:9px;top:50%;transform:translateY(-50%)}.stick .ar.r{right:9px;top:50%;transform:translateY(-50%)}
/* servo position shown on the stick: dashed frame = travel range, orange ring = where the camera points now */
.srange{position:absolute;left:14.65%;top:14.65%;width:70.7%;height:70.7%;border:1px dashed rgba(245,154,74,.45);
  border-radius:6px;pointer-events:none}
.sline{z-index:1;position:absolute;display:block;background:rgba(245,154,74,.38);pointer-events:none;transition:top .25s ease-out,left .25s ease-out}
.sline.h{left:0;right:0;height:1px;top:50%}.sline.v{top:0;bottom:0;width:1px;left:50%}
.spos{position:absolute;display:block;left:50%;top:50%;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;border:2.5px solid #f59a4a;
  box-shadow:0 0 0 3px rgba(245,154,74,.22),0 0 12px rgba(245,154,74,.65);z-index:3;pointer-events:none;transition:top .25s ease-out,left .25s ease-out}
.stick.on .spos,.stick.on .sline{transition:none}
.swp{position:absolute;inset:0;width:100%;height:100%;overflow:visible;z-index:0;pointer-events:none;opacity:.6;transition:opacity .3s}
.swp.dots{z-index:3;opacity:.8}.swp.run{opacity:.9}
.swp polyline,.swp line{fill:none;stroke:#9fc3ff;stroke-width:1.3;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.swp line{stroke-dasharray:3 3}
.swp circle{fill:#16233a;stroke:#9fc3ff;stroke-width:1.2;vector-effect:non-scaling-stroke}
.swp text{fill:#cfe0ff;font:700 5.8px system-ui,sans-serif;text-anchor:middle;dominant-baseline:central}
#spos-txt{font-size:11px;letter-spacing:.02em;text-align:center;margin-top:-4px}
#spos-txt b{color:#f59a4a;font-weight:700}
.knob{position:absolute;z-index:2;left:50%;top:50%;width:70px;height:70px;margin:-35px 0 0 -35px;border-radius:50%;pointer-events:none;will-change:transform;
  background:radial-gradient(circle at 36% 30%,var(--acc2),var(--acc) 62%);box-shadow:0 6px 16px rgba(0,0,0,.45),inset 0 1px 2px rgba(255,255,255,.35);transition:transform .16s ease-out}
.stick.on{cursor:grabbing}.stick.on .knob{transition:none;filter:brightness(1.12)}
.stickrow{display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap}
.stickrow select{padding:4px 8px}
#mctl{display:none}
#mbtns{display:none}body.mobctl #mbtns{display:block;width:100%}
body.mobctl #mbtns #allbtns{margin:10px 0 0!important}
#mbtns2{display:none}#mbtns2:empty{display:none!important}body.mobctl:not(.mobland) #mbtns2{display:block;margin:0 0 14px}body.mobctl #mbtns2 #allbtns{margin:0!important}
body.mobland #mbtns .btns>*{padding:5px 8px;font-size:12px}
body.videoonly #allbtns,body.videoonly #mbtns2{display:none!important}
#stick-listen{padding:5px 12px;font-size:17px;line-height:1;border-radius:999px}
#stick-listen.lon{background:var(--grn);border-color:var(--grn);color:#fff;box-shadow:0 0 0 3px rgba(63,185,80,.25);animation:lpulse 1.6s infinite}
@keyframes lpulse{50%{box-shadow:0 0 0 6px rgba(63,185,80,.08)}}
/* phone / tablet upright: small live picture in a corner while the big one is scrolled away (the same picture, no 2nd stream) */
#pip{position:fixed;z-index:45;width:min(44vw,260px);border-radius:12px;overflow:hidden;background:#000;cursor:pointer;touch-action:none;
  box-shadow:0 8px 26px rgba(0,0,0,.55),0 0 0 1px var(--line);-webkit-user-select:none;user-select:none}
#pip[hidden]{display:none}
#pip[data-c="br"]{right:12px;bottom:calc(env(safe-area-inset-bottom) + 12px)}#pip[data-c="bl"]{left:12px;bottom:calc(env(safe-area-inset-bottom) + 12px)}
#pip[data-c="tr"]{right:12px;top:calc(var(--hdr-h,64px) + 10px)}#pip[data-c="tl"]{left:12px;top:calc(var(--hdr-h,64px) + 10px)}
#pip .pip-in img{width:100%;height:auto;max-height:none;display:block;min-height:0;pointer-events:none}
#pip .pip-live{position:absolute;left:6px;bottom:6px;font:700 10px/1 system-ui,sans-serif;color:#fff;background:rgba(0,0,0,.55);padding:3px 6px;border-radius:6px}
#pip .pip-live{color:#fff}#pip .pip-live::first-letter{color:var(--grn)}
#pip-x{position:absolute;top:5px;right:5px;width:28px;height:28px;border-radius:50%;border:0;background:rgba(0,0,0,.6);color:#fff;font-size:13px;line-height:28px;padding:0;min-height:0}
#pip.alarm{box-shadow:0 0 0 3px var(--red),0 8px 26px rgba(0,0,0,.55)}#pip.alarm .pip-live{background:var(--red)}
body.mobland #pip{width:min(32vw,230px)}
@media(min-width:961px){#pip{display:none!important}}
body.mobland .stickbox{gap:6px}body.mobland .stickrow select,body.mobland .stickrow button{padding:3px 7px!important;font-size:12px}
body.mobctl #mctl{display:block;margin-top:12px}
body.mobctl #mctl .pad{margin:0 auto;justify-content:center}
body.mobctl #mctl>#ctl-left>.row{justify-content:center;gap:10px}
body.mobland main{padding:8px;row-gap:0}
body.mobland header{position:static}
body.mobland #vcard{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px 12px;align-items:center;padding:8px}
body.mobland #vcard>.vwrap{grid-column:1;grid-row:1}
body.mobland #mctl{grid-column:2;grid-row:1;margin:0;max-width:200px}
body.mobland #vcard>.stats,body.mobland #vcard>#obj-list{grid-column:1/-1}
body.mobland #video{max-height:calc(100vh - 20px);max-height:calc(100svh - 20px);object-fit:contain;min-height:0}
body.mobland .stick{width:136px;height:136px}
body.mobland .knob{width:54px;height:54px;margin:-27px 0 0 -27px}
body.mobland .pad{grid-template-columns:repeat(3,50px);grid-template-rows:repeat(3,50px)}
body.mobland #mctl .stickrow{gap:4px}body.mobland #mctl>#ctl-left>.row{flex-wrap:wrap;gap:4px 8px;margin-top:6px!important}
.padbox{display:none!important}          /* only the joystick (the arrow buttons were removed from the controls) */
button.dp{font-size:22px;padding:0;background:var(--btn2);color:var(--txt);border:1px solid var(--line);border-radius:12px}
button.dp.mid{background:var(--acc);color:#fff;border-color:transparent}
canvas{width:100%;height:56px;display:block;background:var(--field);border-radius:8px}
.bar{height:8px;background:var(--line);border-radius:4px;overflow:hidden;margin:6px 0}
.bar>i{display:block;height:100%;width:0;background:var(--grn);transition:width .4s,background .4s}
#log{font:12px/1.55 ui-monospace,Menlo,Consolas,monospace;max-height:320px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere}
#log .t{color:var(--mut)}
body.videoonly header,body.videoonly aside,body.videoonly .stats,body.videoonly #obj-list,body.videoonly details.card,body.videoonly .vtag{display:none}
body.videoonly main{display:block;padding:0;max-width:none}body.videoonly .card{margin:0;padding:0;border:0;border-radius:0;box-shadow:none;background:none}
body.videoonly .vwrap{border-radius:0;box-shadow:none}
body.videoonly #video{border-radius:0;height:100vh;height:100dvh;width:100%;object-fit:contain;background:#000}
body.videoonly{background:#000;overflow:hidden}
/* full screen (phone, tablet, computer): the picture fills the screen, the joystick floats see-through on top of it */
body.videoonly #mctl{display:none!important}
body.videoonly #vcard{display:block!important;padding:0!important}
body.videoonly #video{max-height:none!important;min-height:0}
/* the buttons sit INSIDE the picture box (not "fixed" to the screen): on the iPhone fixed buttons were drawn some
   millimetres away from where they react to a touch */
body.videoonly .vwrap{position:relative;overflow:hidden}
/* ---- mover (from 2.94.0): the second stick drives a tracked vehicle - only there when the mover is found (or simulated) ---- */
.ctl-mstick{display:none}body.mover .ctl-mstick{display:block;grid-area:mstick}
.mstick .knob{background:radial-gradient(circle at 36% 30%,#8be3a0,#2f9e4f 62%)}
.mstick::after{width:46%}
.mtrk{position:absolute;top:20%;bottom:20%;width:7px;border-radius:4px;background:rgba(127,127,127,.2);overflow:hidden;pointer-events:none;z-index:1}
.mtrk.l{left:9%}.mtrk.r{right:9%}.mtrk i{position:absolute;left:0;right:0;background:var(--grn);transition:all .12s}
#mstick-txt{font-size:11px;text-align:center;margin-top:-4px}
body.mover #ctl-left{grid-template-columns:auto auto 190px minmax(0,520px);grid-template-areas:"mstick stick side mid"}
body.mover.swapside #ctl-left{grid-template-columns:190px auto auto minmax(0,520px);grid-template-areas:"side stick mstick mid"}
@media(max-width:1180px) and (min-width:961px){body.mover #ctl-left .stick{width:132px;height:132px}
  body.mover #ctl-left{grid-template-columns:auto auto 160px minmax(0,1fr)}body.mover.swapside #ctl-left{grid-template-columns:160px auto auto minmax(0,1fr)}}
body.mover.mobctl #ctl-left{grid-template-columns:1fr 1fr;grid-template-areas:"mstick stick" "side side" "mid mid";justify-items:center}
body.mover.mobctl.swapside #ctl-left{grid-template-areas:"stick mstick" "side side" "mid mid"}
body.mover.mobctl #ctl-left .stick{width:140px;height:140px}body.mover.mobctl #ctl-left .ctl-side{width:100%}
body.mover.mobland #ctl-left{grid-template-columns:1fr;grid-template-areas:"mstick" "stick" "side"}
body.mover.mobland #ctl-left .stick{width:96px;height:96px}
#vo-mctl{display:none}
body.videoonly.mover #vo-mctl{display:flex;position:absolute;z-index:61;left:max(18px,env(safe-area-inset-left));bottom:calc(env(safe-area-inset-bottom) + 18px);transition:opacity .5s;touch-action:none}
body.videoonly.mover.swapside #vo-mctl{left:auto;right:max(18px,env(safe-area-inset-right))}
@media (orientation:landscape) and (max-height:520px){body.videoonly.mover #vo-mctl{bottom:calc(env(safe-area-inset-bottom) + 64px);left:calc(env(safe-area-inset-left) + 24px)}
  body.videoonly.mover.swapside #vo-mctl{left:auto;right:calc(env(safe-area-inset-right) + 24px)}}
#vo-mctl.idle{opacity:.38}
/* 2.95.82: the mover stick can be moved anywhere on the picture (✥ drag; double tap = back), one place per side (⇆) */
#vo-mctl .vo-grip{position:absolute;left:-12px;top:-12px;width:34px;height:34px;border-radius:50%;padding:0;z-index:2;
  border:1px solid rgba(255,255,255,.55);background:rgba(0,0,0,.55);color:#fff;font-size:17px;line-height:1;touch-action:none;cursor:grab}
#vo-mctl.drag{opacity:1!important;outline:2px dashed rgba(255,255,255,.6);outline-offset:6px;border-radius:50%}
#vo-mctl .stick{width:clamp(118px,24vmin,168px);height:clamp(118px,24vmin,168px);background:rgba(8,12,20,.22);border:2px solid rgba(255,255,255,.72);
  box-shadow:0 2px 14px rgba(0,0,0,.35);-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px)}
#vo-mctl .stick::before,#vo-mctl .stick::after{background:rgba(255,255,255,.3)}
#vo-mctl .stick .ar{color:#fff;opacity:.85;text-shadow:0 1px 3px #000}
#vo-mctl .knob{width:30%;height:30%;margin:-15% 0 0 -15%}
#vo-ctl{display:none}
body.videoonly #vo-ctl{display:flex;position:absolute;z-index:61;right:max(18px,env(safe-area-inset-right));bottom:max(18px,env(safe-area-inset-bottom));
  align-items:flex-end;gap:10px;transition:opacity .5s;touch-action:none}
body.videoonly #vo-ctl.left{right:auto;left:max(18px,env(safe-area-inset-left));flex-direction:row-reverse}
#vo-ctl.idle{opacity:.38}
body.videoonly #vo-ctl{bottom:calc(env(safe-area-inset-bottom) + 18px)}
/* phone held sideways: higher up, away from the bottom edge (the swipe bar of the phone takes the touches there) */
@media (orientation:landscape) and (max-height:520px){body.videoonly #vo-ctl{bottom:calc(env(safe-area-inset-bottom) + 64px);right:calc(env(safe-area-inset-right) + 24px)}
  body.videoonly #vo-ctl.left{left:calc(env(safe-area-inset-left) + 24px)}}
#vo-ctl .stick{width:clamp(118px,24vmin,168px);height:clamp(118px,24vmin,168px);background:rgba(8,12,20,.22);border:2px solid rgba(255,255,255,.72);
  box-shadow:0 2px 14px rgba(0,0,0,.35);-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px)}
#vo-ctl .stick::before,#vo-ctl .stick::after{background:rgba(255,255,255,.3)}
#vo-ctl .stick .ar{color:#fff;opacity:.85;text-shadow:0 1px 3px #000}
#vo-ctl .knob{width:30%;height:30%;margin:-15% 0 0 -15%}
#vo-ctl .srange{border-color:rgba(245,154,74,.6)}
#vo-ctl .vbtns{display:flex;flex-direction:column;gap:16px;padding:26px 10px 6px;margin:-26px -10px -6px}
#vo-ctl .vbtns button{pointer-events:none}
/* "other side" sits at the top next to ✕ (not next to "centre": phones report a touch a bit above the finger) */
#vo-side{display:none}
body.videoonly #vo-side{display:flex;position:absolute;top:max(10px,env(safe-area-inset-top));right:calc(max(10px,env(safe-area-inset-right)) + 56px);z-index:60;
  width:44px;height:44px;align-items:center;justify-content:center;border-radius:50%;border:1px solid rgba(255,255,255,.35);
  background:rgba(0,0,0,.55);color:#fff;font-size:20px;padding:0;cursor:pointer}
#vo-ctl .vbtns button{width:46px;height:46px;border-radius:50%;padding:0;display:flex;align-items:center;justify-content:center;font-size:20px;
  background:rgba(8,12,20,.38);color:#fff;border:2px solid rgba(255,255,255,.6);box-shadow:0 2px 10px rgba(0,0,0,.35)}
#vo-ctl .vbtns button.lon{background:var(--grn);border-color:var(--grn)}
#vo-ctl .vbtns button.hit{background:rgba(47,129,247,.75);border-color:#fff}
.vwrap.vlost{min-height:180px}
.vwrap.vlost::after{content:"↻";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#8b9bb0;font-size:34px;animation:vspin 1.2s linear infinite}
@keyframes vspin{to{transform:rotate(360deg)}}
/* 2.95.77: full screen - 🚜 shows / hides the mover stick (on the other side of the camera stick; ⇆ swaps both) */
#vo-mv{display:none}
body.videoonly.moveravail #vo-mv{display:flex;position:absolute;top:max(10px,env(safe-area-inset-top));right:calc(max(10px,env(safe-area-inset-right)) + 112px);z-index:60;
  width:44px;height:44px;align-items:center;justify-content:center;border-radius:50%;border:1px solid rgba(255,255,255,.35);
  background:rgba(0,0,0,.55);color:#fff;font-size:20px;padding:0;cursor:pointer}
body.videoonly.moveravail.mover #vo-mv{background:rgba(63,207,107,.55);border-color:var(--grn)}
#vo-exit{display:none}
body.videoonly #vo-exit{display:flex;position:absolute;top:max(10px,env(safe-area-inset-top));right:max(10px,env(safe-area-inset-right));z-index:60;
 width:44px;height:44px;align-items:center;justify-content:center;border-radius:50%;border:1px solid rgba(255,255,255,.35);
 background:rgba(0,0,0,.55);color:#fff;font-size:22px;cursor:pointer;padding:0}
.pop{position:fixed;top:58px;right:12px;z-index:40;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:8px 14px 12px;box-shadow:var(--shadow);max-height:80vh;overflow:auto;min-width:250px}
.pop h3{margin:10px 0 4px;font-size:11px;color:var(--mut);letter-spacing:.08em;text-transform:uppercase}
.pop label{display:flex;gap:8px;align-items:center;padding:3px 0;cursor:pointer}
.ctl-grid{display:grid;grid-template-columns:auto minmax(0,1fr);gap:18px;align-items:start}
@media(max-width:640px){.ctl-grid{grid-template-columns:1fr}}
h4.sub{margin:14px 0 4px;font-size:11px;letter-spacing:.08em;color:var(--mut);text-transform:uppercase}
.rq{display:grid;grid-template-columns:auto auto auto minmax(0,1fr);gap:6px 10px;align-items:center}
.dot{font-size:15px;color:var(--mut)}.dot.on{color:var(--grn)}
.rel-ed{border:1px solid var(--line);border-radius:10px;padding:9px;margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:6px 8px;align-items:end;background:var(--field)}
.rel-ed input[type=text],.rel-ed input[type=number]{width:100%}
.warn{color:var(--yel);font-size:13px;cursor:help}
.srcrow{display:flex;align-items:center;gap:8px;padding:6px 4px;cursor:pointer;border-radius:8px}
.srcrow:hover{background:var(--field)}
.srcrow input{margin:0}
.days{display:flex;gap:4px;flex-wrap:wrap}
.days button{padding:4px 9px;font-size:12px;background:var(--btn2);color:var(--mut);border:1px solid var(--line)}
.days button.on{background:var(--acc);color:#fff;border-color:transparent}
.auxbox{margin:2px 0 6px}
.aimg{border:1px solid var(--line);border-radius:12px;padding:8px 10px;margin:8px 0}.aimh{font-weight:700;margin:0 0 4px}.aimg>button.sec{margin-top:6px}
#upd-list{overflow-y:auto;overscroll-behavior:contain;-webkit-overflow-scrolling:touch}.updrow{padding:7px 0;border-bottom:1px solid var(--line)}.updrow .row{gap:8px}
.btrow{gap:8px;padding:5px 0;border-bottom:1px solid var(--line)}.btrow>span:first-child{flex:1;min-width:0;overflow-wrap:anywhere}
.aumeter{position:relative;height:12px;border-radius:6px;background:var(--field);border:1px solid var(--line);overflow:hidden;margin:6px 0 3px}
.aumeter i{position:absolute;left:0;top:0;bottom:0;width:0;background:#3fb950;transition:width .3s}
.aumeter s{position:absolute;top:0;bottom:0;width:2px;margin-left:-1px;background:var(--mut);display:none}
.aumeter b{position:absolute;top:0;bottom:0;width:3px;margin-left:-1px;background:var(--red);display:none}
button.on{box-shadow:inset 0 0 0 2px var(--grn)}
.pwr{margin-top:14px;padding-top:10px;border-top:1px solid var(--line)}
#wiz{position:fixed;inset:0;z-index:210;background:rgba(0,0,0,.82);display:flex;align-items:center;justify-content:center;padding:14px}
#wiz .card{max-width:470px;width:100%;max-height:92vh;overflow-y:auto;position:relative;padding:20px}
#wiz h2{margin:4px 0 6px;font-size:20px}#wiz p{margin:6px 0}#wiz label{display:block;margin:12px 0 4px;font-weight:600}
#wiz input[type=text],#wiz input[type=password]{width:100%;padding:10px 12px;border-radius:10px}
#wiz .dots{display:flex;gap:6px;justify-content:center;margin-bottom:6px}#wiz .dots i{width:8px;height:8px;border-radius:50%;background:var(--line)}
#wiz .dots i.on{background:var(--acc)}#wiz .usegrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}
#wiz .useopt{display:flex;flex-direction:column;align-items:center;gap:4px;padding:12px 6px;font-size:14px;text-align:center}#wiz .useopt .ic{font-size:26px}
#wiz .useopt.on{border-color:var(--acc);box-shadow:0 0 0 2px var(--acc) inset}#wiz .later{position:absolute;top:10px;right:12px;background:none;border:0;color:var(--mut);font-size:13px;padding:4px}
#wiz .qr{display:block;width:180px;height:180px;margin:8px auto;border-radius:10px;overflow:hidden;background:#fff}#wiz .qr svg{width:100%;height:100%;display:block}
#wiz .qrs{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;text-align:center}#wiz .qrs .mut{word-break:break-all}
#wiz .wnav{display:flex;gap:8px;margin-top:16px}#wiz .wnav button{flex:1;padding:11px}
#wiz .lang button.on{background:var(--acc);color:#fff}
#pw-ov{position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;padding:20px}
#pw-ov .card,#talk-ov .card,#pwd-ov .card{max-width:440px;width:100%;text-align:center}
#pwd-ov{position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;padding:20px}
#talk-ov{position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;padding:20px}
.talkbtn{touch-action:none;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none}
.talkbtn.on{background:var(--red);color:#fff;box-shadow:none}
#talk-slot{display:contents}#talk-slot[hidden]{display:none}
/* 2.98.0: one page, three tabs (Live · Schutz · Einstellungen) */
body[data-tab="live"] main>aside,body[data-tab] #side-open,body[data-tab] #btn-side,body[data-tab] #side-close{display:none!important}
body[data-tab="live"] main{grid-template-columns:minmax(0,1fr)!important}
body[data-tab="protect"] main>section,body[data-tab="settings"] main>section{display:none!important}
body[data-tab="protect"] main,body[data-tab="settings"] main{grid-template-columns:minmax(0,1fr)!important;max-width:980px}
body[data-tab="protect"] main>aside,body[data-tab="settings"] main>aside{display:block!important}
body[data-tab="protect"] [data-tab-of="settings"],body[data-tab="settings"] [data-tab-of="protect"],body[data-tab="settings"] #alarm-chain{display:none!important}
body[data-tab="live"] #set-foot{display:block!important}
/* 2.98.6: quick switches compact - what is not available is hidden, smaller tiles, more per line: the live picture gets the room */
.qsw button.na{display:none!important}
@media(max-width:960px){body[data-tab="live"] #ctl-left .ctl-mid{grid-column:1/-1;width:100%}}
body[data-tab="live"] .qsw,body[data-tab="live"] #ctl-left .qsw,body.mobctl[data-tab="live"] #ctl-left .qsw{grid-template-columns:repeat(auto-fill,minmax(52px,1fr));gap:6px 5px;max-width:none;width:100%}
body[data-tab="live"] .qsw button{padding:4px 1px 3px;border-radius:10px;gap:1px;font-size:16px}
body[data-tab="live"] .qsw button span{font-size:17px;line-height:1.1}
body[data-tab="live"] .qsw button small{font-size:9px}
body[data-tab="live"] #set-foot{padding:6px;font-size:13px;margin-top:4px}
body[data-tab="live"] #spos-txt{font-size:11px}
/* 2.98.3: the head of the settings tidy - search with its 3 buttons over the full width, below one small line
   «Einfach | Experte» and «Symbole farbig | schlicht» side by side; the explanations as tooltips */
body[data-tab] #srch{padding-left:0!important}body[data-tab] #srch .ic{left:12px!important}
body[data-tab] .simplebar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:2px 0 14px}
body[data-tab] .simplebar>.mut,body[data-tab] .simplebar .icseg>.mut{display:none}
body[data-tab] .simplebar .seg{display:inline-flex;flex:1 1 160px}
body[data-tab] .simplebar .seg button{flex:1;padding:7px 8px;font-size:12.5px;white-space:nowrap}
body[data-tab] .simplebar .icseg{margin:0;flex:1 1 160px;display:flex}
#alarm-chain .chain{display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin:4px 0}
#alarm-chain .chain button{padding:6px 9px;font-size:13px}#alarm-chain .chain button.off{opacity:.45;text-decoration:line-through}
#alarm-chain .chain em{color:var(--mut);font-style:normal}
</style></head><body>
<header>
  <h1 data-view="title" data-vgroup="Header" data-vlabel="Title">MoveEye</h1>
  <!--NAV-->
  <span class="chips">
  <span class="badge yel" id="b-sim" hidden style="cursor:pointer" onclick="post('/api/sim',{on:false}).then(()=>refresh())" title="Simulation off">🧪</span>
  <span class="badge" id="b-me" hidden></span>
  <span class="badge" id="b-arm" data-view="b-arm" data-vgroup="Header" data-vlabel="Armed / disarmed" style="cursor:pointer">🛡</span>
  <span class="badge grn" id="b-ok" hidden style="cursor:pointer">✓ ok</span>
  <span class="badge" id="b-person" data-view="b-person" data-vgroup="Header" data-vlabel="Persons">No person</span>
  <span class="badge" id="b-obj" data-view="b-obj" data-vgroup="Header" data-vlabel="Objects" hidden>0 objects</span>
  <span class="badge" id="b-rec" data-view="b-rec" data-vgroup="Header" data-vlabel="Recording" hidden>Idle</span>
  <span class="badge" id="b-camp" data-view="b-camp" data-vgroup="Header" data-vlabel="Camping profile" hidden>⛺</span>
  <span class="badge" id="b-eco" data-view="b-eco" data-vgroup="Header" data-vlabel="Power saving" hidden>🍃</span>
  <span class="badge" id="b-mode" data-view="b-mode" data-vgroup="Header" data-vlabel="Mode" hidden title="Mode" style="cursor:pointer"></span>
  <span class="badge" id="b-turbo" data-view="b-turbo" data-vgroup="Header" data-vlabel="Power mode" hidden title="Power mode">🚀</span>
  <span class="badge" id="b-batt" data-view="b-batt" data-vgroup="Header" data-vlabel="Battery" hidden>🔋</span>
  <span class="badge yel" id="b-lock" data-view="b-lock" data-vgroup="Header" data-vlabel="Operator mode" hidden style="cursor:pointer" onclick="unlockAct()">🔐</span>
  <span class="badge" id="b-tl" data-view="b-tl" data-vgroup="Header" data-vlabel="Timelapse" hidden>⏱</span>
  <span class="badge" id="b-lights" data-view="b-lights" data-vgroup="Header" data-vlabel="Lights" hidden>💡</span>
  <span class="badge" id="b-env" data-view="b-env" data-vgroup="Header" data-vlabel="Outside temperature" hidden>🌡</span>
  <span class="badge red" id="b-health" data-view="b-health" data-vgroup="Header" data-vlabel="Self-check" hidden style="cursor:pointer" onclick="healthOpen()">🩺</span>
  <span class="badge" id="b-therm" data-view="b-therm" data-vgroup="Header" data-vlabel="Thermal camera" hidden>🌡</span>
  <span class="badge" id="b-pat" data-view="b-pat" data-vgroup="Header" data-vlabel="Patrol / tracking" hidden>🔄</span>
  <span class="badge" id="b-hs" data-view="b-hs" data-vgroup="Header" data-vlabel="Own Wi-Fi (hotspot)" hidden>📡</span>
  <span class="badge" id="b-remote" data-view="b-remote" data-vgroup="Header" data-vlabel="Remote access" hidden>🌐</span>
  <span class="badge" id="b-sched" data-view="b-sched" data-vgroup="Header" data-vlabel="Schedule" hidden>Schedule –</span>
  <span class="badge" id="b-relay" data-view="b-relay" data-vgroup="Header" data-vlabel="Relays" hidden>Relays</span>
  <span class="badge" id="b-audio" data-view="b-audio" data-vgroup="Header" data-vlabel="Microphone" hidden>🎤</span>
  <span class="badge" id="b-rain" data-view="b-rain" data-vgroup="Header" data-vlabel="Rain" hidden>No rain</span>
  <span class="badge" id="b-wind" data-view="b-wind" data-vgroup="Header" data-vlabel="Wind" hidden>Wind: calm</span>
  <span class="badge" id="b-light" data-view="b-light" data-vgroup="Header" data-vlabel="Light level" hidden>Light –</span>
  <span class="badge" id="b-pres" data-view="b-pres" data-vgroup="Header" data-vlabel="Presence" hidden>Presence</span>
  <span class="badge yel" id="b-sec" data-view="b-sec" data-vgroup="Header" data-vlabel="Security warning" hidden title="Set a password: --web-password SECRET" data-i18n="⚠ no password">⚠ no password</span>
  <span class="badge red" id="b-pwr" data-view="b-pwr" data-vgroup="Header" data-vlabel="Power supply / memory" hidden>⚡</span>
  <span class="badge" id="b-src" data-view="b-src" data-vgroup="Header" data-vlabel="Video source" hidden>Source –</span>
  <span class="badge" id="b-conn" data-view="b-conn" data-vgroup="Header" data-vlabel="Connection" hidden>connecting…</span>
  <span class="badge" id="b-wifi" data-view="b-wifi" data-vgroup="Header" data-vlabel="Wi-Fi" hidden>Wi-Fi</span>
  <span class="badge" id="b-view" data-view="b-view" data-vgroup="Header" data-vlabel="Viewers" hidden>👁</span>
  <span class="badge" id="b-cpu" data-view="b-cpu" data-vgroup="Header" data-vlabel="CPU">CPU –</span>
  <span class="badge" id="b-fps" data-view="b-fps" data-vgroup="Header" data-vlabel="FPS">FPS –</span>
  </span>
  <span class="hdr-ctl">
    <button class="sec ic" id="btn-view" onclick="toggleViewMenu(event)" title="View"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
    <button class="sec" id="btn-side" onclick="toggleHidden('sidebar')" title="Settings panel">&#9654;</button>
    <button class="sec ic" id="btn-fs" onclick="toggleFullscreen()" title="Full screen"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/></svg></button>
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<div id="viewmenu" class="pop" hidden></div>
<main>
  <div id="pip" hidden data-c="br" title="Live"><div class="pip-in"></div><span class="pip-live">● LIVE</span><button type="button" id="pip-x" aria-label="close">✕</button></div>
  <section>
    <div class="card" id="vcard">
      <div class="vwrap"><img id="video" src="/video_feed" alt=""><button id="vo-exit" onclick="setVideoOnly(false)" title="Exit full screen">&#x2715;</button>
        <button type="button" id="vo-side" title="⇆">⇆</button>
        <button type="button" id="vo-mv" title="Mover" onclick="const m = document.getElementById('mv-tog'); if (m) m.click()">🚜</button>
        <div id="vo-ctl" class="idle"><div class="vbtns"><button type="button" id="vo-center" title="Centre">◎</button>
          <button type="button" id="vo-listen" title="Listen" hidden>🎧</button></div><div id="vo-slot"></div></div>
        <div id="vo-mctl" class="idle"><button type="button" class="vo-grip" id="vo-mgrip" title="Move (double tap: back to its place)">✥</button><div id="vo-mslot"></div></div>
        <div class="vtag"><span class="live">LIVE</span><span class="rec" id="v-rec" hidden>● REC</span><span id="v-src" hidden></span></div></div>
      <div id="mctl"></div>
    </div>
    <div id="mbtns2"></div>
    <details class="card" open data-view="controls" data-vgroup="Panels" data-vlabel="Controls">
      <summary data-i18n="Controls">Controls</summary>
      <div class="ctl-grid">
        <div id="ctl-left">
          <div class="ctl-mstick" id="ctl-mstick">
            <div class="stickbox" id="mstickbox">
              <div class="stick mstick" id="mstick" role="application" aria-label="mover joystick" title="Mover"><span class="ar u">&#8679;</span><span class="ar d">&#8681;</span><span class="ar l">&#8634;</span><span class="ar r">&#8635;</span><i class="mtrk l"><i id="mtl"></i></i><i class="mtrk r"><i id="mtr"></i></i><div class="knob" id="mknob"></div></div>
              <div class="mut" id="mstick-txt" aria-live="off">Mover</div>
            </div>
          </div>
          <div class="ctl-stick">
            <div class="stickbox">
              <div class="stick" id="stick" role="application" aria-label="camera joystick" title="arrow keys work too"><span class="ar u">&#9650;</span><span class="ar d">&#9660;</span><span class="ar l">&#9664;</span><span class="ar r">&#9654;</span><div class="srange" aria-hidden="true"><svg class="swp" id="swp" viewBox="0 0 100 100" preserveAspectRatio="none"></svg><svg class="swp dots" id="swp2" viewBox="0 0 100 100" preserveAspectRatio="none"></svg><i class="sline h" id="sline-h"></i><i class="sline v" id="sline-v"></i><i class="spos" id="spos"></i></div><div class="knob" id="knob"></div></div>
              <div class="mut" id="spos-txt" aria-live="off"></div>
            </div>
            <div class="pad padbox">
              <span></span><button class="dp" data-dir="up" aria-label="tilt up">&#9650;</button><span></span>
              <button class="dp" data-dir="left" aria-label="pan left">&#9664;</button>
              <button class="dp mid" data-dir="center" aria-label="centre">&#9679;</button>
              <button class="dp" data-dir="right" aria-label="pan right">&#9654;</button>
              <span></span><button class="dp" data-dir="down" aria-label="tilt down">&#9660;</button><span></span>
            </div>
          </div>
          <div class="ctl-mid">
            <div class="qsw" id="qsw"></div>
            <div class="mut" id="patrol-st"></div>
          </div>
          <div class="ctl-side" id="ctl-side">
            <div class="sr spd"><select id="stick-speed" title="Speed"><option value="12" data-i18n="Slow">Slow</option><option value="30" selected data-i18n="Medium">Medium</option><option value="60" data-i18n="Fast">Fast</option></select><button class="sec" type="button" id="swap-side" title="Swap stick and buttons (left- / right-handed)" aria-label="swap sides">⇆</button><button class="sec" type="button" id="mv-tog" title="Show / hide the mover stick" aria-label="mover stick">🚜</button></div>
            <div class="row padbox"><span class="mut" data-i18n="Step">Step</span>
              <select id="step"><option>1</option><option selected>3</option><option>5</option><option>10</option><option>20</option></select></div>
            <div class="sr"><button class="sec" type="button" data-dir="center" id="stick-center" data-i18n="◎ Centre">◎ Centre</button>
              <button class="sec" type="button" id="btn-recal" onclick="act('recalibrate'); toast('↻ ' + t('Recalibrating - keep the picture empty for a few seconds'))" data-i18n="↻ Calibrate">↻ Calibrate</button></div>
            <div class="sr"><button class="sec" type="button" onclick="act('wp_add'); toast('📍 ' + t('Waypoint added'))" data-i18n="📍＋ Waypoint">📍＋ Waypoint</button>
              <button class="sec" type="button" onclick="if(confirm(t('Clear all waypoints?')))act('wp_clear')" title="Clear waypoints">📍🗑</button></div>
            <span id="talk-slot" hidden></span>
          </div>
          <div id="mbtns"></div>
          <button type="button" class="sec" id="set-foot" onclick="location.href = '/settings'">⚙ <span data-i18n="Settings">Settings</span></button>
        </div>
        <div id="ctl-more" hidden>
          <span id="v-pan"></span><span id="v-tilt"></span>
          <button type="button" id="btn-listen" hidden></button><button type="button" id="stick-listen" hidden></button>
          <div id="lights-box"><div class="rq" id="light-quick"></div></div>
          <div id="relays-box"><div class="rq" id="relay-quick"></div><div class="err" id="relay-err"></div></div>
        </div>
      </div>
    </details>
    <div id="lv-simw" hidden>
      <style>
        .lv-vbox{position:relative;border-radius:10px;overflow:hidden;background:#000;user-select:none;-webkit-user-select:none}
        .lv-vbox img{display:block;width:100%;height:auto;cursor:grab;outline:none}.lv-vbox img:active{cursor:grabbing}
        .lv-vbox img:focus-visible{box-shadow:inset 0 0 0 2px var(--acc,#3b8cff)}
        .lv-vbtn{position:absolute;right:8px;top:8px;display:flex;flex-direction:column;gap:6px}
        .lv-vbtn button{width:38px;height:38px;padding:0;border-radius:10px;border:1px solid rgba(255,255,255,.25);background:rgba(10,14,20,.65);color:#fff;font-size:18px;cursor:pointer}
        .lv-vbtn button.on{background:var(--acc,#3b8cff)}
        .lv-vhelp{font-size:12px;margin:6px 0 8px}
        #lv-vw.big .lv-vbox{position:fixed;inset:0;z-index:60;border-radius:0;display:flex;align-items:center;justify-content:center;
          padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)}
        #lv-vw.big .lv-vbox img{width:auto;max-width:100%;max-height:100%}
      </style>
      <details class="card" id="lv-sim" open data-view="simctl" data-vgroup="Panels" data-vlabel="Simulator control">
        <summary><span id="lv-simt" data-i18n="Simulator control">Simulator control</span></summary>
        <div id="lv-vw" hidden>
          <div class="lv-vbox"><img id="lv-vimg" alt="" draggable="false" tabindex="0">
            <div class="lv-vbtn"><button type="button" id="lv-vctl" title="Bedienen mit dem Finger (sonst scrollt die Seite)">✋</button><button type="button" id="lv-vrot" title="Finger: drehen statt verschieben">⟲</button><button type="button" id="lv-vin">＋</button><button type="button" id="lv-vout">－</button><button type="button" id="lv-vbig" title="gross">⛶</button></div></div>
          <div class="mut lv-vhelp" id="lv-vhelp"></div>
        </div>
        <div class="mut" id="lv-simst" style="white-space:pre-wrap;margin:2px 0 6px"></div>
        <div id="lv-simg"></div>
      </details>
    </div>
  </section>
  <button type="button" id="side-open" onclick="toggleHidden('sidebar')" title="Settings"><span>⟨</span><b data-i18n="Settings">Settings</b></button>
  <aside data-view="sidebar" data-vgroup="Panels" data-vlabel="Settings panel">
    <div class="btns" id="allbtns" style="margin:0 0 12px">
      <button class="sec" id="all-groups" onclick="allGroups()"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v5H4zM4 14h16v5H4z"/></svg><span data-i18n="Groups only">Groups only</span></button>
      <button class="sec" id="all-open" onclick="allSections(true)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 15l5 5 5-5M7 9l5-5 5 5"/></svg><span data-i18n="Expand all">Expand all</span></button>
      <button class="sec" id="all-close" onclick="allSections(false)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l5 5 5-5M7 20l5-5 5 5"/></svg><span data-i18n="Collapse all">Collapse all</span></button>
    </div>
    <div id="simtile" data-simhub="tile" hidden style="margin-bottom:12px"></div>
    <details class="card" open data-view="protect" data-vgroup="Panels" data-vlabel="Camping / protection" id="pr-card">
      <summary data-i18n="Camping / protection">Camping / protection</summary>
      <div id="protect-box"></div>
      <div id="mode-box" style="margin:2px 0 12px"><div class="row" style="justify-content:space-between"><b data-i18n="Mode">Mode</b><span class="mut" id="mode-cur"></span></div>
        <div id="mode-grid" class="mode-grid"></div><div class="mut" id="mode-info" style="margin-top:6px"></div><div id="mode-opts"></div><div class="err" id="mode-err"></div><div id="mode-tv"></div><details id="btq" style="margin-top:8px"><summary id="btq-sum" style="cursor:pointer;font-size:14px">🔊 …</summary><div id="btq-box"></div></details><details id="disco-more" class="more" style="margin-top:8px"><summary id="disco-sum" style="cursor:pointer;color:var(--mut,#8a96a6);font-size:14px">🪩 <span>Disco light</span></summary><div id="mode-disco"></div></details></div>
      <div class="row"><b id="pr-state" style="font-size:18px">–</b><span class="mut" id="pr-left"></span></div>
      <button type="button" class="night-btn" id="pr-night" onclick="nightGuard()"><span data-i18n="🌙 Guard tonight">🌙 Guard tonight</span><small data-i18n="night-desc">switches on what a night needs, arms with the countdown and tells what is missing</small></button>
      <div id="night-res" hidden></div>
      <div class="btns">
        <button type="button" id="pr-arm" data-i18n="🛡 Arm (countdown)">🛡 Arm (countdown)</button>
        <button type="button" class="sec" id="pr-armnow" data-i18n="Arm now">Arm now</button>
        <button type="button" class="sec" id="pr-disarm" data-i18n="Disarm">Disarm</button>
      </div>
      <label class="row pr-sw" hidden><span><b>⛺ <span data-i18n="Camping profile">Camping profile</span></b><br>
        <span class="mut" data-i18n="cp-desc">Own Wi-Fi on, the camera stays where it is (no patrol / tracking / timelapse), alarms and recordings on, armed after the countdown. Switching it off restores your settings.</span></span>
        <input type="checkbox" class="sw" id="pr-camp"></label>
      <label class="row pr-sw"><span><b>🔋 <span data-i18n="Power saving">Power saving</span></b><br><span class="mut" id="pr-eco-info"></span></span>
        <input type="checkbox" class="sw" id="pr-eco"></label>
      <label class="row pr-sw"><span><b>🚀 <span data-i18n="Power mode">Power mode</span></b><br><span class="mut" id="pr-turbo-info"></span></span>
        <input type="checkbox" class="sw" id="pr-turbo"></label>
      <label class="row pr-sw l-hide"><span><b>📡 <span data-i18n="Own Wi-Fi (hotspot)">Own Wi-Fi (hotspot)</span></b><br><span class="mut" id="pr-hs-info"></span></span>
        <input type="checkbox" class="sw" id="pr-hs"></label>
      <div class="pr-sw l-hide" style="cursor:default"><b>📱 <span data-i18n="Internet from the phone (USB cable)">Internet from the phone (USB cable)</span></b><br><span class="mut" id="pr-teth"></span></div>
      <div class="pr-sw l-hide" style="cursor:default"><b>🌐 <span data-i18n="Network">Network</span></b>
        <select id="pr-net" style="width:100%;margin-top:6px">
          <option value="auto" data-i18n="Automatic: phone hotspot / known networks, otherwise own Wi-Fi">Automatic: phone hotspot / known networks, otherwise own Wi-Fi</option>
          <option value="hotspot" data-i18n="Own Wi-Fi at boot">Own Wi-Fi at boot</option>
          <option value="client" data-i18n="Only known networks">Only known networks</option>
        </select>
        <div class="mut" id="pr-net-info" style="margin-top:4px"></div></div>
      <label class="row pr-sw l-hide"><span><b>🔁 <span data-i18n="Autostart at boot">Autostart at boot</span></b><br><span class="mut" id="pr-as-info"></span></span>
        <input type="checkbox" class="sw" id="pr-as"></label>
      <div class="mut" id="pr-time" style="margin-top:6px"></div>
      <div class="mut" id="pr-gps" style="margin-top:4px"></div>
      <div class="mut" id="pr-env" style="margin-top:4px"></div>
      <div class="err" id="pr-err"></div>
    </details>
    <details class="card" data-view="tune" data-vgroup="Panels" data-vlabel="Improve detection"><summary data-i18n="Improve detection">Improve detection</summary><div id="tune-box"></div></details>
    <details class="card" id="hcard" data-view="health" data-vgroup="Panels" data-vlabel="Self-check">
      <summary><span data-i18n="🩺 Self-check">🩺 Self-check</span> <span class="mut" id="h-sum" style="text-transform:none;letter-spacing:0;font-weight:500"></span></summary>
      <div id="h-list"></div>
      <div class="btns"><button type="button" class="sec" onclick="healthLoad()" data-i18n="Check again">Check again</button></div>
    </details>
    <details class="card" open data-view="system" data-vgroup="Panels" data-vlabel="System">
      <summary data-i18n="System">System</summary>
      <div class="row"><b id="cpu-big" style="font-size:22px">–</b><span class="mut" id="cpu-info"></span></div>
      <div class="bar"><i id="cpu-bar"></i></div>
      <canvas id="cpu-spark" width="360" height="56"></canvas>
      <div class="mut" style="margin-top:4px" data-i18n="CPU load, last 60 seconds">CPU load, last 60 seconds</div>
      <div class="mbar"><div class="row"><b>🧠 <span data-i18n="Memory (RAM)">Memory (RAM)</span></b><span class="mut" id="ram-info">–</span></div><div class="bar"><i id="ram-bar"></i></div></div>
      <div class="mbar"><div class="row"><b>💾 <span id="dsk-name" data-i18n="Storage">Storage</span></b><span class="mut" id="dsk-info">–</span></div><div class="bar"><i id="dsk-bar"></i></div></div>
      <div id="wifi-box" hidden style="margin-top:12px">
        <div class="row"><b id="wifi-big" style="font-size:18px">–</b><span class="mut" id="wifi-name"></span></div>
        <div class="bar"><i id="wifi-bar"></i></div>
        <canvas id="wifi-spark" width="360" height="64"></canvas>
        <div class="mut" id="wifi-stat" style="margin-top:4px"></div>
        <div class="mut" id="wifi-info"></div>
      </div>
      <div class="mut" id="sys-supply" style="margin-top:8px"></div>
      <div class="mut" id="sys-remote" style="margin-top:4px"></div>
      <div class="mut" id="sys-proj" style="margin-top:4px;white-space:pre-wrap"></div>
      <details class="adv sblk" data-view="sysblk:power"><summary data-i18n="⏻ Switch off, restart, pause">⏻ Switch off, restart, pause</summary>
      <div class="btns pwr">
        <button type="button" class="red" id="pw-off" onclick="powerAct('poweroff')" data-i18n="⏻ Shut down Pi">⏻ Shut down Pi</button>
        <button type="button" class="sec" id="pw-reboot" onclick="powerAct('reboot')" data-i18n="↻ Restart Pi">↻ Restart Pi</button>
      </div>
      <div class="row" style="margin-top:10px"><span class="mut" data-i18n="Pause the program for">Pause the program for</span>
        <select id="pause-min"><option value="5">5 min</option><option value="15">15 min</option><option value="30" selected>30 min</option>
          <option value="60">1 h</option><option value="120">2 h</option><option value="240">4 h</option><option value="480">8 h</option><option value="720">12 h</option></select></div>
      <div class="btns pwr"><button type="button" class="sec" onclick="pauseAct()" data-i18n="⏸ Pause program">⏸ Pause program</button></div>
      <div class="err" id="pw-err"></div>
      </details>
      <details class="adv sblk" data-view="sysblk:lock" open><summary data-i18n="🔐 Operator mode">🔐 Operator mode</summary>
      <div class="btns pwr">
        <button type="button" class="sec" id="lock-btn" onclick="lockBtn()" data-i18n="🔐 Operator mode (lock settings)">🔐 Operator mode (lock settings)</button>
      </div>
      <div class="mut" id="lock-info" hidden style="margin:-2px 0 6px;text-align:center"></div>
      </details>
      <details class="adv sblk" data-view="sysblk:help"><summary data-i18n="🧭 Help and setup">🧭 Help and setup</summary>
      <div class="btns pwr">
        <button type="button" class="sec l-hide" onclick="setupWizard(true)" data-i18n="🧭 Setup assistant">🧭 Setup assistant</button>
        <button type="button" class="sec l-hide" onclick="hwCheck()" data-i18n="🧪 Hardware check (step by step)">🧪 Hardware check (step by step)</button>
        <a class="btn sec" id="lnk-quick" href="/quick" target="_blank" data-i18n="📄 Quick guide (1 page)">📄 Quick guide (1 page)</a>
        <a class="btn sec" href="/setup-card" target="_blank" data-i18n="🖨 Quick start (QR)">🖨 Quick start (QR)</a>
      </div>
      <div class="btns pwr"><button type="button" class="sec" onclick="fbDialog()" data-i18n="💬 Feedback to the developer">💬 Feedback to the developer</button></div>
      </details>
      <details class="adv sblk l-hide" data-view="sysblk:pw"><summary data-i18n="💾 Settings file">💾 Settings file</summary>
      <a class="btn sec" href="/settings?open=grp:security" onclick="if(typeof tabOpen==='function'&&document.querySelector('#settings [data-view=&quot;grp:security&quot;]')){tabOpen('grp:security');return false;}" data-i18n="🔐 Password, users and app keys: Settings → Security">🔐 Password, users and app keys: Settings → Security</a>
      <div class="btns pwr">
        <a class="btn sec l-hide" href="/api/settings/export" download="motionwatch_einstellungen.json" data-i18n="⬇ Save settings">⬇ Save settings</a>
        <button type="button" class="sec l-hide" onclick="document.getElementById('imp-file').click()" data-i18n="⬆ Load settings">⬆ Load settings</button>
        <input type="file" id="imp-file" accept=".json,application/json" hidden onchange="importSettings(this.files[0]); this.value=''">
      </div>
      <div class="btns pwr">
        <button class="sec l-hide" onclick="if(confirm(t('Reset all settings to defaults?')))act('reset_settings')" data-i18n="Reset settings">Reset settings</button>
      </div>
      </details>
      <details class="adv sblk" data-view="sysblk:info"><summary data-i18n="ℹ Version and status">ℹ Version and status</summary>
      <div class="mut" id="sys-info" style="margin-top:6px"></div>
      <div class="mut" id="app-ver" style="margin-top:4px"></div>
      </details>
    </details>
    <details class="card" open data-view="log" data-vgroup="Panels" data-vlabel="Event log"><summary data-i18n="Event log (important)">Event log (important)</summary><div id="log"></div>
      <div class="btns"><button type="button" class="sec" onclick="location.href='/log'" data-i18n="📜 Whole log &amp; archive">📜 Whole log &amp; archive</button></div></details>
    <details class="card l-hide" data-view="wifi" data-vgroup="Panels" data-vlabel="Wi-Fi / hotspot" id="wf-card">
      <summary data-i18n="Wi-Fi / hotspot">Wi-Fi / hotspot</summary>
      <div class="mut" id="wf-status">…</div>
      <div class="btns"><button type="button" id="wf-scan" data-i18n="Search networks">Search networks</button></div>
      <div class="err" id="wf-err"></div>
      <div id="wf-list"></div>
      <div class="mut" style="margin-top:12px;font-weight:700;letter-spacing:.06em;font-size:11px;text-transform:uppercase" data-i18n="Saved networks">Saved networks</div>
      <div id="wf-saved"></div>
    </details>
    <details class="card" open data-view="source" data-vgroup="Panels" data-vlabel="Video source">
      <summary data-i18n="Video source">Video source</summary>
      <div class="mut" id="src-status"></div>
      <div id="src-list"></div>
      <div class="err" id="src-err"></div>
      <div class="btns"><button class="sec" id="btn-scan" onclick="scanSources()" data-i18n="Scan for cameras">Scan for cameras</button></div>
      <div class="mut" id="src-hints"></div>
      <h4 class="sub" data-i18n="Add network camera">Add network camera</h4>
      <div class="rel-ed" style="grid-template-columns:1fr">
        <input type="text" id="ip-name" placeholder="Name" maxlength="40">
        <input type="text" id="ip-url" placeholder="rtsp://user:pass@192.168.1.50:554/stream1  |  http://192.168.1.50:8080/video" maxlength="500">
        <button class="sec" onclick="addIpSource()" data-i18n="Add">Add</button>
      </div>
    </details>
    <details class="card" open data-view="schedule" data-vgroup="Panels" data-vlabel="Schedule">
      <summary data-i18n="Schedule">Schedule</summary>
      <div class="mut" id="sched-note"></div>
      <div id="sched-list"></div>
      <div class="err" id="sched-err"></div>
      <div class="btns"><button class="sec" onclick="schedPost({action:'add'})" data-i18n="+ Add schedule">+ Add schedule</button></div>
    </details>
    <details class="card" data-view="relayset" data-vgroup="Panels" data-vlabel="Relay settings">
      <summary data-i18n="Relay settings">Relay settings</summary>
      <div class="mut" id="relay-note"></div>
      <div id="relay-editor"></div>
      <div class="btns"><button class="sec" onclick="relayPost({action:'add'})" data-i18n="+ Add relay">+ Add relay</button></div>
    </details>
    <details class="card" data-view="report" data-vgroup="Panels" data-vlabel="Night report">
      <summary data-i18n="Night report">Night report</summary>
      <div class="mut" id="rep-line" style="white-space:pre-wrap">…</div>
      <div class="btns"><button type="button" class="sec" onclick="repSend()" data-i18n="Send now">Send now</button>
        <button type="button" class="sec" onclick="location.href='/diary'" data-i18n="Open animal diary">Open animal diary</button></div>
    </details>
    <details class="card" data-view="guest" data-vgroup="Panels" data-vlabel="Guest access">
      <summary data-i18n="Guest access">Guest access</summary>
      <div class="mut" data-i18n="g-note">g-note</div>
      <div id="g-st" style="margin-top:8px;font-weight:600">…</div>
      <div class="row" style="margin-top:8px"><span class="mut" data-i18n="Valid for">Valid for</span>
        <select id="g-hours"><option value="2">2 h</option><option value="24" selected>24 h</option><option value="72">3 d</option>
          <option value="168">7 d</option><option value="0" data-i18n="no time limit">no time limit</option></select></div>
      <div class="btns"><button type="button" onclick="guestAct('create')" data-i18n="Create new link">Create new link</button>
        <button type="button" class="sec" id="g-share" onclick="guestShare()" data-i18n="Share / copy link" hidden>Share / copy link</button>
        <button type="button" class="red" id="g-end" onclick="guestAct('end')" data-i18n="End guest access" hidden>End guest access</button></div>
      <input type="text" id="g-link" readonly hidden style="width:100%;margin-top:8px" onclick="this.select()">
    </details>
    <details class="card" data-view="batt" data-vgroup="Panels" data-vlabel="Battery">
      <summary data-i18n="Battery">Battery</summary>
      <div id="batt-line" style="font-weight:600">…</div>
      <div class="mut" data-i18n="b-note" style="margin-top:4px">b-note</div>
      <div class="btns"><button type="button" class="sec" id="batt-full-btn" onclick="battFull()" data-i18n="Battery is full now">Battery is full now</button></div>
    </details>
    <div id="lock-bar" hidden><div><b>🔐 <span data-i18n="Operator mode">Operator mode</span></b><br><span class="mut" data-i18n="lock-note">lock-note</span></div>
      <button type="button" onclick="unlockAct()" data-i18n="Unlock">Unlock</button></div>
    <div id="srch"><button type="button" class="sec" id="side-close" onclick="toggleHidden('sidebar')" title="Hide settings">⟩</button><span class="ic">🔍</span><input type="text" id="srch-in" autocomplete="off" enterkeyhint="search"
      data-i18n-ph="Search settings … (e.g. password)" placeholder="Search settings … (e.g. password)"><button type="button" class="x" id="srch-x" hidden>✕</button>
      <div class="mut" id="srch-none" hidden></div></div>
    <div id="settings"></div>
  </aside>
</main>
<script>
// live picture that reconnects by itself (same as in the other pages)
function keepStream(img) {
  if (!img || img.dataset.keep) return;
  img.dataset.keep = "1";
  const base = (img.dataset.src || img.getAttribute("src") || "").split("?")[0];
  let tries = 0, timer = null;
  const box = img.parentNode;
  const lost = on => { img.style.visibility = on ? "hidden" : ""; if (box) box.classList.toggle("vlost", on); };
  let iv = 0;
  // 2.95.34: a picture that was removed from the page stops its stream (otherwise every rebuilt tile kept one open)
  const alive = () => { if (img.isConnected) return true; clearInterval(iv); clearTimeout(timer); document.removeEventListener("visibilitychange", vis); img.src = ""; return false; };
  const restart = () => { clearTimeout(timer); timer = null; if (alive()) img.src = base + "?r=" + Date.now(); };
  const later = () => { if (timer) return; lost(true); timer = setTimeout(restart, Math.min(10000, 1000 * (1 + tries++))); };
  const vis = () => { if (!document.hidden) restart(); };
  img.mwRestart = restart;                  // 2.95.72: the page fetches the picture anew when the video source changes
  img.addEventListener("error", later);
  img.addEventListener("load", () => { tries = 0; lost(false); });
  document.addEventListener("visibilitychange", vis);
  addEventListener("pageshow", e => { if (e.persisted) restart(); });
  iv = setInterval(() => {
    if (!alive() || document.hidden) return;
    if (img.naturalWidth) { if (!timer) { tries = 0; lost(false); } }
    else if (img.complete) later();
  }, 3000);
}
const $ = s => document.querySelector(s);
const post = (u, b) => fetch(u, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(b || {})})
    .then(r => r.json()).catch(() => ({ok: false, error: "connection"}));
const ctrl = {};
let editing = null;
const I18N_EN = {"🖨 Quick start (QR)": "🖨 QR codes for connecting", "night-desc": "switches on what a night needs, arms with the countdown and tells what is missing", "cp-desc": "Own Wi-Fi on, the camera stays where it is (no patrol / tracking / timelapse), alarms and recordings on, armed after the countdown. Switching it off restores your settings.", "lock-note": "Everything may be changed (except Wi-Fi, password, autostart). Unlocking with the PIN puts everything back.", "g-note": "A link for family or fellow campers: they only see the live picture and cannot change anything. The guest must be able to reach the Pi – same Wi-Fi / hotspot or via Tailscale. A new link makes the old one invalid.",
  "b-note": "UPS HAT (battery pack on the Pi): found by itself, real measurement. Otherwise powerbank estimate: capacity minus what was used since «Battery is full now»."};
const I18N = {en: I18N_EN, de: {
  "Power saving": "Stromsparmodus", "active: few pictures, everything quiet": "aktiv: wenige Bilder, alles ruhig",
  "full speed (something happened or somebody watches)": "volle Geschwindigkeit (etwas los oder jemand schaut zu)",
  "fewer pictures while all is quiet, full speed at the first movement or noise": "weniger Bilder, solange alles ruhig ist - volle Geschwindigkeit bei der ersten Bewegung oder einem Geräusch",
  "🔒 Web password": "🔒 Web-Passwort", "⬇ Save settings": "⬇ Einstellungen sichern", "⬆ Load settings": "⬆ Einstellungen laden",
  "The password was given on the command line (--web-password).": "Das Passwort wurde beim Start angegeben (--web-password).",
  "Change web password": "Web-Passwort ändern", "Set a web password": "Web-Passwort festlegen",
  "Nobody has set a password yet: anybody in this network can open this page, switch the alarm off or listen in. Set a password now (6 to 64 characters).":
    "Es ist noch kein Passwort gesetzt: Jeder in diesem Netz kann diese Seite öffnen, den Alarm ausschalten oder mithören. Lege jetzt ein Passwort fest (6 bis 64 Zeichen).",
  "6 to 64 characters. After saving, the browser asks for it once (any user name).": "6 bis 64 Zeichen. Nach dem Speichern fragt der Browser einmal danach (Benutzername beliebig).",
  "New password": "Neues Passwort", "Repeat": "Wiederholen", "Save": "Speichern", "at least 6 characters": "mindestens 6 Zeichen",
  "the two passwords are not the same": "die beiden Passwörter sind nicht gleich",
  "Password saved. The page reloads - log in with any user name and the new password.": "Passwort gespeichert. Die Seite lädt neu - melde dich mit beliebigem Benutzernamen und dem neuen Passwort an.",
  "Remove password": "Passwort entfernen", "Remove the password? Then anybody in the network can open the page.": "Passwort entfernen? Dann kann jeder im Netz die Seite öffnen.",
  "Password removed": "Passwort entfernt", "Later": "Später", "Cancel": "Abbrechen",
  "Web password: set": "Web-Passwort: gesetzt", "Web password: none": "Web-Passwort: keines",
  "under-voltage!": "Unterspannung!", "ok (under-voltage earlier)": "ok (früher Unterspannung)", "free": "frei", "under-voltage": "Unterspannung",
  "Load the settings from this file? The current settings are replaced (a copy is kept on the Pi).": "Einstellungen aus dieser Datei laden? Die aktuellen werden ersetzt (eine Kopie bleibt auf dem Pi).",
  "Settings loaded": "Einstellungen geladen",
  "Bluetooth loudspeaker": "Bluetooth-Lautsprecher", "Search Bluetooth loudspeakers": "Bluetooth-Lautsprecher suchen",
  "Bluetooth is not available (sudo apt install bluez)": "Bluetooth ist nicht verfügbar (sudo apt install bluez)",
  "Searching … put the loudspeaker into pairing mode (blue light blinking)": "Suche läuft … Lautsprecher in den Kopplungsmodus versetzen (blaues Licht blinkt)",
  "connecting …": "verbinde …", "no devices yet - press «Search»": "noch keine Geräte - «suchen» drücken", "connected": "verbunden",
  "paired": "gekoppelt", "connected - used for the siren and for talking": "verbunden - wird für Sirene und Sprechen verwendet",
  "Connect": "Verbinden", "Disconnect": "Trennen", "Remove": "Entfernen",
  "Search versions": "Nach Versionen suchen", "searched at": "gesucht um", "list from": "Liste vom", "Running now": "Läuft jetzt", "running now": "läuft jetzt", "on the Pi": "auf dem Pi",
  "available": "verfügbar", "Update": "Aktualisieren", "Switch": "Wechseln", "Install": "Installieren", "Switch to version": "Zu Version wechseln",
  "The program restarts (about 20 seconds). Settings, recordings and zones stay.": "Das Programm startet neu (ca. 20 Sekunden). Einstellungen, Aufnahmen und Zonen bleiben.",
  "Downloading and checking …": "Wird geladen und geprüft …", "Switching to version": "Wechsle zu Version", "The page reloads by itself.": "Die Seite lädt von selbst neu.",
  "Downloading": "Herunterladen", "Checking the signature": "Unterschrift wird geprüft", "Restarting": "Neustart", "Still about": "Noch etwa",
  "Takes longer than usual …": "Dauert länger als sonst …", "Done": "Fertig",
  "No update source set yet (see above)": "Noch keine Update-Quelle eingetragen (siehe oben)", "Updates": "Updates",
  "Fine-tuning": "Feineinstellungen", "Light & sound": "Licht & Ton", "Protection & network": "Schutz & Netzwerk",
  "Push messages": "Push-Nachrichten", "Switches": "Schalter", "Relays": "Relais", "Schedule": "Zeitplan",
  "Camping": "Camping", "Saving": "Sparen", "awake": "wach", "Timelapse": "Zeitraffer", "Light": "Licht", "Lamp": "Licht", "Thermal": "Wärmebild",
  "Patrol": "Patrouille", "Own Wi-Fi": "Eigenes WLAN", "LOW LIGHT": "WENIG LICHT", "MANUAL": "HAND", "TRACKING": "VERFOLGT",
  "Camping profile": "Camping-Profil", "Patrol / tracking": "Patrouille / Verfolgung", "Power supply / memory": "Strom / Speicher",
  "Lights": "Licht", "White": "Weiss", "Infrared": "Infrarot", "no output chosen": "kein Ausgang gewählt",
  "Audio": "Audio", "Microphone": "Mikrofon", "Search devices": "Geräte suchen", "Listening volume (this device)": "Lautstärke beim Mithören (dieses Gerät)",
  "Test sound": "Testton", "Siren now": "Sirene jetzt", "Stop": "Stopp", "Microphones": "Mikrofone", "Loudspeakers": "Lautsprecher",
  "microphone on": "Mikrofon an", "starting …": "startet …", "no microphone selected": "kein Mikrofon gewählt", "background": "Hintergrund",
  "noise alarm from": "Geräusch-Alarm ab", "no loudspeaker selected": "kein Lautsprecher gewählt", "playing …": "spielt …",
  "Listen": "Mithören", "Stop listening": "Mithören beenden", "this browser cannot play the live sound": "dieser Browser kann den Live-Ton nicht abspielen",
  "no microphone": "kein Mikrofon", "Listening ended": "Mithören beendet",
  "⏻ Shut down Pi": "⏻ Pi ausschalten", "↻ Restart Pi": "↻ Pi neu starten", "Shut down the Raspberry Pi now?": "Raspberry Pi jetzt herunterfahren?",
  "A running recording is finished first. To switch it on again: unplug the power and plug it in again.":
    "Eine laufende Aufnahme wird vorher abgeschlossen. Wieder einschalten: Strom aus- und wieder einstecken.",
  "Restart the Raspberry Pi now?": "Raspberry Pi jetzt neu starten?", "The Pi is shutting down …": "Der Pi fährt herunter …",
  "The Pi is restarting …": "Der Pi startet neu …", "Finishing the recording, saving the settings …": "Aufnahme wird abgeschlossen, Einstellungen werden gespeichert …",
  "Close": "Schliessen", "The Pi was not shut down": "Der Pi wurde nicht heruntergefahren", "The Pi is off": "Der Pi ist aus",
  "Wait until the green LED of the Pi stays dark (about 10 seconds), then you can unplug the power. To start it again: unplug the power and plug it in again.":
    "Warte, bis die grüne LED am Pi dunkel bleibt (ca. 10 Sekunden), dann kannst du den Strom trennen. Wieder starten: Strom aus- und wieder einstecken.",
  "Waiting for the Pi … the page reloads by itself (about 1 minute).": "Warte auf den Pi … die Seite lädt von selbst neu (ca. 1 Minute).",
  "No answer from the Pi.": "Keine Antwort vom Pi.",
  "Hold to talk": "Gedrückt halten zum Sprechen", "Talking … release to stop": "Sprechen … loslassen zum Beenden",
  "Talking needs the secure page": "Sprechen braucht die sichere Seite",
  "Phones only give the microphone to https pages. Open the secure page, confirm the certificate warning once («Advanced» → «Continue»), then hold the button again.":
    "Handys geben das Mikrofon nur für https-Seiten frei. Öffne die sichere Seite, bestätige einmal die Zertifikatswarnung («Erweitert» → «Weiter»), dann den Knopf wieder gedrückt halten.",
  "Open secure page": "Sichere Seite öffnen", "The secure page is not running (openssl missing).": "Die sichere Seite läuft nicht (openssl fehlt).",
  "the microphone of this device is not allowed": "das Mikrofon dieses Geräts ist nicht erlaubt", "somebody is talking": "jemand spricht",
  "Own sounds (.wav / .mp3): put the files into": "Eigene Töne (.wav / .mp3): Dateien ablegen in", "and press «Search devices»": "und «Geräte suchen» drücken",
  "Controls": "Steuerung", "System": "System", "Event log": "Ereignisprotokoll", "Expand all": "Alle öffnen",
  "Collapse all": "Alle schliessen", "Topics": "Themen", "Speed: slow": "Tempo: langsam", "Speed: medium": "Tempo: mittel", "Speed: fast": "Tempo: schnell",
  "Step": "Schritt", "◎ Centre": "◎ Mitte", "↻ Calibrate": "↻ Kalibrieren", "📍＋ Waypoint": "📍＋ Wegpunkt", "Clear all waypoints?": "Alle Wegpunkte löschen?",
  "Waypoint added": "Wegpunkt gesetzt", "Listen": "Mithören", "Listen to the microphone": "Mikrofon mithören", "Relay: on / automatic": "Relais: ein / automatisch", "Recalibrating - keep the picture empty for a few seconds": "Kalibriere neu – ein paar Sekunden niemand ins Bild", "💬 Feedback to the developer": "💬 Feedback an den Entwickler", "Feedback to the developer": "Feedback an den Entwickler",
  "Ideas, errors, praise - everything helps. The message is sent anonymously: no name, no address, unless you write one.": "Ideen, Fehler, Lob – alles hilft. Die Nachricht geht anonym weg: kein Name, keine Adresse, ausser du schreibst sie dazu.",
  "💡 Idea": "💡 Idee", "🐞 Error": "🐞 Fehler", "⭐ Praise": "⭐ Lob", "💬 Other": "💬 Sonstiges", "Your message …": "Deine Nachricht …",
  "Contact for an answer (optional)": "Kontakt für eine Antwort (freiwillig)", "Add technical details (version, device, last important events - no pictures, no passwords)": "Technische Angaben mitsenden (Version, Gerät, letzte wichtige Ereignisse – keine Bilder, keine Passwörter)",
  "Send": "Senden", "Cancel": "Abbrechen", "Thank you! The message is on its way.": "Danke! Die Nachricht ist unterwegs.", "need 2+ waypoints": "mindestens 2 Wegpunkte nötig (+ Wegpunkt)", "Thermal": "Wärme", "Marks": "Markieren", "Light": "Licht", "IR light": "IR-Licht",
  "Follow": "Folgen", "Patrol": "Patrouille", "Record": "Aufnahme", "Photo": "Foto", "Photo saved": "Foto gespeichert", "↻ Round": "↻ Runde", "⇄ Pendulum": "⇄ Pendel",
  "Patrol: tap = off → back and forth (1-2-3-2-1) → round trip (1-2-3-1) → off": "Patrouille: Tippen = Aus → hin und zurück (1-2-3-2-1) → Runde (1-2-3-1) → Aus",
  "Thermal picture over the live picture": "Wärmebild über das Live-Bild legen", "Mark detected objects (animals, cars ...)": "Erkannte Objekte markieren (Tiere, Autos …)",
  "White light on / off": "Weisses Licht ein / aus", "Infrared light on / off": "Infrarot-Licht ein / aus", "Follow a detected person": "Erkannter Person folgen",
  "Drive along the waypoints": "Wegpunkte abfahren", "Record now (max. 10 min) / stop": "Jetzt aufnehmen (max. 10 min) / stoppen",
  "Photo into the recordings": "Foto in die Aufnahmen", "not connected": "nicht angeschlossen", "Other side": "Andere Seite", "SMS (LTE stick)": "SMS (LTE-Stick)", "Send test SMS": "Test-SMS senden", "SMS sent": "SMS gesendet",
  "A USB LTE stick with a SIM card (with credit). Works also where there is only the mobile network. Costs per SMS - mind the limits.": "Ein USB-LTE-Stick mit SIM-Karte (mit Guthaben). Funktioniert auch dort, wo es nur Mobilfunk gibt. Jede SMS kostet – Grenzen beachten.", "Backup": "Sicherung", "Theft protection": "Diebstahlschutz", "Deterrence": "Abschreckung", "Last": "Zuletzt",
  "What is seen decides the reaction. Animals need the AI detection, warm bodies the thermal camera. Light flashes: the white light.": "Was erkannt wird, bestimmt die Reaktion. Tiere brauchen die KI-Erkennung, warme Körper die Wärmebildkamera. Lichtblitze: das weisse Licht.",
  "When armed: push message (urgent) and siren. The picture check pauses while the camera head moves itself.": "Wenn der Schutz an ist: Push-Nachricht (dringend) und Sirene. Die Bildprüfung pausiert, solange sich der Kamerakopf selbst bewegt.",
  "Motion sensor": "Bewegungssensor", "found": "gefunden", "not fitted": "nicht eingebaut", "learning the picture": "lernt das Bild", "on guard": "wacht",
  "Finished alarm recordings are copied away from the device - if it is stolen or broken, the clips are safe.": "Fertige Alarm-Aufnahmen werden ausser Haus kopiert – wird das Gerät gestohlen oder beschädigt, sind die Clips sicher.",
  "Test the backup": "Sicherung testen", "Test file copied - the settings work.": "Testdatei kopiert – die Einstellungen stimmen.", "Web push (no app needed)": "Web-Push (ohne App)",
  "Alarm messages straight into the browser / the home screen app of this device.": "Alarm-Nachrichten direkt in den Browser bzw. die Home-Bildschirm-App dieses Geräts.",
  "Devices": "Geräte", "python3-cryptography is missing (sudo apt install python3-cryptography)": "python3-cryptography fehlt (sudo apt install python3-cryptography)",
  "Web push needs https. Open the page over the https address (Tailscale):": "Web-Push braucht https. Öffne die Seite über die https-Adresse (Tailscale):",
  "Switch on https over Tailscale": "https über Tailscale einschalten",
  "iPhone / iPad: open the https address, then Share → «Add to Home Screen» and switch it on in the app from there.": "iPhone / iPad: die https-Adresse öffnen, dann Teilen → «Zum Home-Bildschirm» und in der App von dort einschalten.",
  "iPhone / iPad: first Share → «Add to Home Screen», then open MoveEye from there and switch web push on.": "iPhone / iPad: zuerst Teilen → «Zum Home-Bildschirm», dann MoveEye von dort öffnen und Web-Push einschalten.",
  "Switch off on this device": "Auf diesem Gerät ausschalten", "Switch on on this device": "Auf diesem Gerät einschalten",
  "Notifications are not allowed for this page (browser settings).": "Mitteilungen sind für diese Seite nicht erlaubt (Browser-Einstellungen).",
  "Send test": "Test senden", "sent": "gesendet", "Web push is on for this device.": "Web-Push ist auf diesem Gerät eingeschaltet.", "🧭 Setup assistant": "🧭 Einrichtungs-Assistent", "🖨 Quick start (QR)": "🖨 QR-Codes zum Verbinden", "📄 Quick guide (1 page)": "📄 Kurzanleitung (1 Seite)", "signed": "signiert", "not signed": "nicht signiert", "+ Waypoint": "+ Wegpunkt", "Clear waypoints": "Wegpunkte löschen", "Snapshot": "Schnappschuss",
  "Recalibrate": "Neu kalibrieren", "Reset counter": "Zähler zurücksetzen", "Reset settings": "Einstellungen zurücksetzen",
  "CPU load, last 60 seconds": "CPU-Last, letzte 60 Sekunden", "Step per click": "Schritt pro Klick",
  "Pi connected": "Pi verbunden", "Pi not reachable": "Pi nicht erreichbar",
  "calm": "ruhig", "breezy": "böig", "strong": "stark", "storm": "Sturm", "⚠ no password": "⚠ kein Passwort",
  "Wi-Fi / hotspot": "WLAN / Hotspot", "Search networks": "Netze suchen", "Searching …": "Suche läuft …", "Saved networks": "Gespeicherte Netze",
  "Connected with": "Verbunden mit", "Page address": "Adresse dieser Seite", "or": "oder", "connecting to": "verbinde mit", "connected to": "verbunden mit",
  "failed": "fehlgeschlagen", "back on": "zurück im Netz", "Password": "Passwort", "Password (empty = keep the saved one)": "Passwort (leer = gespeichertes behalten)",
  "show password": "Passwort zeigen", "prefer this network (before other known networks)": "dieses Netz bevorzugen (vor anderen bekannten Netzen)",
  "Connect now": "Jetzt verbinden", "Only save (connects automatically)": "Nur speichern (verbindet automatisch)", "Forget network": "Netz vergessen",
  "Forget this network?": "Dieses Netz vergessen?", "no networks found": "keine Netze gefunden",
  "Press 'Search networks'. Switch on the hotspot of the phone first.": "Auf «Netze suchen» tippen. Vorher den Hotspot am Handy einschalten.",
  "saved": "gespeichert", "preferred": "bevorzugt", "no auto connect": "nicht automatisch", "Other / hidden network …": "Anderes / verstecktes Netz …",
  "Network name (SSID)": "Netzname (SSID)", "The Pi is connected with this network.": "Der Pi ist mit diesem Netz verbunden.",
  "The Pi now switches to the network": "Der Pi wechselt jetzt ins Netz",
  "This page will probably lose its connection. Afterwards open it in that network at": "Diese Seite verliert dabei vermutlich die Verbindung. Öffne sie danach in diesem Netz unter",
  "or with the address from the push message. If it does not work, the Pi returns to the previous network after about a minute.":
    "oder mit der Adresse aus der Push-Nachricht. Klappt es nicht, kehrt der Pi nach etwa einer Minute ins bisherige Netz zurück.",
  "The connection to this page was interrupted - normal while the Pi changes the network. Open the page in the new network:":
    "Die Verbindung zu dieser Seite ist unterbrochen - beim Netzwechsel normal. Öffne die Seite im neuen Netz:",
  "(or the address from the push message).": "(oder mit der Adresse aus der Push-Nachricht).",
  "The Pi is connected with it right now - the page may lose its connection.": "Der Pi ist gerade damit verbunden - die Seite kann die Verbindung verlieren.",
  "Wi-Fi management is not available on this system (NetworkManager or wpa_supplicant missing).": "WLAN-Verwaltung ist auf diesem System nicht verfügbar (NetworkManager oder wpa_supplicant fehlt).",
  "none": "keine",
  "Network": "Netzwerk", "Automatic: phone hotspot / known networks, otherwise own Wi-Fi": "Automatik: Handy-Hotspot / bekannte Netze, sonst eigenes WLAN",
  "Own Wi-Fi at boot": "Beim Hochfahren eigenes WLAN", "Only known networks": "Nur bekannte Netze", "Autostart at boot": "Autostart beim Hochfahren",
  "automatic paused (switched by hand) - choose «Automatic» again to resume": "Automatik pausiert (von Hand geschaltet) - «Automatik» erneut wählen zum Fortsetzen",
  "own Wi-Fi on": "eigenes WLAN an", "searching known networks …": "suche bekannte Netze …",
  "own Wi-Fi on - search postponed (a device is connected)": "eigenes WLAN an - Suche verschoben (ein Gerät ist verbunden)",
  "connected with": "verbunden mit", "no known network - own Wi-Fi in": "kein bekanntes Netz - eigenes WLAN in",
  "own Wi-Fi on - next search for known networks in": "eigenes WLAN an - nächste Suche nach bekannten Netzen in",
  "tries the known networks (phone hotspot), otherwise switches the own Wi-Fi on": "versucht die bekannten Netze (Handy-Hotspot), sonst schaltet es das eigene WLAN ein",
  "switches the own Wi-Fi on": "schaltet das eigene WLAN ein", "joins the known networks": "verbindet sich mit den bekannten Netzen",
  "on: when the Pi boots, MoveEye starts by itself and": "an: beim Hochfahren startet MoveEye von selbst und",
  "Autostart with own Wi-Fi": "Autostart mit eigenem WLAN", "Autostart on": "Autostart an", "Autostart off": "Autostart aus",
  "on: when the Pi boots, MoveEye starts by itself and switches the own Wi-Fi on": "an: beim Hochfahren startet MoveEye von selbst und schaltet das eigene WLAN ein",
  "off: nothing starts at boot, the Pi joins its known networks": "aus: beim Hochfahren startet nichts, der Pi verbindet sich mit den bekannten Netzen",
  "Empty = standard text (grey). Placeholders:": "Leer = Standardtext (grau). Platzhalter:", "Send test message": "Testnachricht senden",
  "Alarm & camping": "Alarm & Camping", "Notifications": "Benachrichtigungen", "Detection": "Erkennung", "Camera & servos": "Kamera & Servos",
  "Recordings & timelapse": "Aufnahmen & Zeitraffer", "Thermal camera": "Wärmebild", "Relays & schedule": "Relais & Zeitplan",
  "System & network": "System & Netz", "Advanced": "Erweitert",
  "Camping / protection": "Camping / Schutz", "Armed": "Schutz an", "Armed in": "Schutz an in", "Disarmed": "Schutz aus",
  "🛡 Arm (countdown)": "🛡 Schutz an (Countdown)", "Arm now": "Sofort an", "Disarm": "Schutz aus",
  "no alarms, no recordings": "keine Alarme, keine Aufnahmen", "leave the area now": "jetzt den Bereich verlassen", "alarms active": "Alarme aktiv",
  "tap: arm / disarm": "Antippen: Schutz an / aus", "Camping profile": "Camping-Profil",
  "cp-desc": "Eigenes WLAN an, die Kamera bleibt stehen (keine Patrouille / Verfolgung / Zeitraffer), Alarme und Aufnahmen an, Schutz an nach dem Countdown. Ausschalten stellt deine Einstellungen wieder her.",
  "Own Wi-Fi (hotspot)": "Eigenes WLAN (Hotspot)", "Own Wi-Fi": "Eigenes WLAN", "own Wi-Fi": "eigenes WLAN", "device": "Gerät", "devices": "Geräte",
  "switching …": "schaltet um …", "on": "an", "name": "Name", "password": "Passwort", "Clock": "Uhrzeit", "taken from the phone": "vom Handy übernommen",
  "correct": "stimmt", "time zone": "Zeitzone", "set by the internet (NTP)": "über das Internet gestellt (NTP)",
  "needs NetworkManager (Raspberry Pi OS Bookworm or newer)": "braucht NetworkManager (Raspberry Pi OS Bookworm oder neuer)",
  "The Pi now switches on its own Wi-Fi": "Der Pi schaltet jetzt sein eigenes WLAN ein",
  "This page loses its connection. Connect the phone to": "Diese Seite verliert die Verbindung. Verbinde das Handy mit",
  "and open": "und öffne", "the camera stays where it is (no patrol, tracking or timelapse)": "die Kamera bleibt stehen (keine Patrouille, Verfolgung oder Zeitraffer)",
  "alarms and recordings on": "Alarme und Aufnahmen an", "armed after the countdown": "Schutz an nach dem Countdown",
  "End camping? The own Wi-Fi is switched off again - this page loses its connection and the Pi goes back to the known networks.":
    "Camping beenden? Das eigene WLAN wird ausgeschaltet - diese Seite verliert die Verbindung und der Pi geht zurück in die bekannten Netze.",
  "Switch the own Wi-Fi off? This page loses its connection; the Pi goes back to the known networks.":
    "Eigenes WLAN ausschalten? Diese Seite verliert die Verbindung; der Pi geht zurück in die bekannten Netze.",
  "Camping profile ON": "Camping-Profil an", "Camping profile OFF": "Camping-Profil aus",
  "Wi-Fi signal, last": "WLAN-Signal, letzte", "min": "Min.", "weakest": "schwächster", "drop-out": "Aussetzer",
  "drop-outs": "Aussetzer", "no drop-outs": "keine Aussetzer",
  "no Wi-Fi": "kein WLAN", "no internet": "kein Internet", "Wi-Fi": "WLAN", "not connected": "nicht verbunden", "Internet": "Internet",
  "online": "online", "offline": "offline",
  "Use current position": "Aktuelle Position übernehmen", "Show position": "Position anzeigen", "Photo now": "Foto jetzt",
  "Create video": "Video erstellen", "All days": "Alle Tage", "photos": "Fotos", "Download": "Herunterladen", "Remove this video?": "Dieses Video löschen?",
  "Photo requested": "Foto angefordert", "off": "aus", "waiting: alarm has priority": "wartet: Alarm hat Vorrang",
  "waiting: manual control": "wartet: Handsteuerung", "moving to the photo position": "fährt zur Fotoposition", "photo saved": "Foto gespeichert",
  "next photo in": "nächstes Foto in", "making video": "Video wird erstellt", "video ready": "Video fertig", "connected": "verbunden",
  "connecting…": "verbinde …", "no thermal camera selected": "keine Wärmebildkamera gewählt",
  "same camera as the main picture": "gleiche Kamera wie das Hauptbild", "connection lost - reconnecting": "Verbindung verloren - verbinde neu",
  "The thermal camera must look in the same direction as the main camera. Choose it in the list after a camera scan (Video source).":
    "Die Wärmebildkamera muss in dieselbe Richtung blicken wie die Hauptkamera. Wähle sie nach einem Kamera-Scan (Videoquelle) in der Liste aus.",
  "Speed": "Tempo", "slow": "langsam", "medium": "mittel", "fast": "schnell", "Centre": "Mitte", "Control": "Steuerung", "Stick": "Stick", "Buttons": "Tasten",
  "No person": "Keine Person", "PERSON DETECTED": "PERSON ERKANNT", "PERSONS DETECTED": "PERSONEN ERKANNT",
  "object": "Objekt", "objects": "Objekte", "No rain": "Kein Regen", "RAIN MODE": "REGENMODUS", "Wind": "Wind",
  "Idle": "Bereit", "REC": "AUFN", "LOW LIGHT": "SCHWACHLICHT", "Light ok": "Licht ok", "Settings": "Einstellungen",
  "recordings": "Aufnahmen", "viewers": "Zuschauer", "notify": "Alarm", "Tracking person": "Person wird verfolgt",
  "Manual control - tracking / patrol paused": "Handsteuerung - Verfolgung / Patrouille pausiert",
  "Patrol": "Patrouille", "waypoints": "Wegpunkte", "Objects": "Objekte", "FPS": "FPS", "PERSONS NOW": "PERSONEN JETZT",
  "OBJECTS": "OBJEKTE", "DETECTIONS": "ERKENNUNGEN", "cores": "Kerne", "online": "online", "offline": "offline",
  "Reset all settings to defaults?": "Alle Einstellungen auf Standard zurücksetzen?", "arrow keys work too": "Pfeiltasten gehen auch",
  "Relays": "Relais", "Relay settings": "Relais-Einstellungen", "+ Add relay": "+ Relais hinzufügen", "Off": "Aus", "On": "Ein",
  "Auto": "Auto", "Name": "Name", "GPIO": "GPIO", "Hold (s)": "Halten (s)", "Active low": "Low-aktiv", "Remove": "Entfernen",
  "Remove this relay?": "Dieses Relais entfernen?", "needs AI model": "braucht das KI-Modell",
  "Header": "Kopfzeile", "Statistics": "Statistiken", "Panels": "Bereiche", "Title": "Titel", "Persons": "Personen",
  "Rain": "Regen", "Recording": "Aufnahme", "Light level": "Lichtverhältnisse", "CPU": "CPU", "Connection": "Verbindung",
  "Persons now": "Personen jetzt", "Detections": "Erkennungen", "Object list": "Objektliste", "Settings panel": "Einstellungsbereich",
  "Remote access": "Fernzugriff", "Remote": "Fern", "not installed": "nicht installiert", "watching now": "schaut gerade zu", "nobody from outside": "niemand von aussen",
  "Show all": "Alle einblenden", "View": "Ansicht", "no relays": "keine Relais",
  "Auto: the relay switches on while its trigger is in view and stays on for the hold time. Animal and object triggers (e.g. cat) need the AI model.":
    "Auto: Das Relais schaltet ein, solange sein Auslöser im Bild ist, und bleibt für die Haltezeit an. Tier- und Objekt-Auslöser (z. B. Katze) brauchen das KI-Modell.",
  "Remote access switches on while somebody watches over Tailscale - also when disarmed (e.g. a small warning lamp).":
    "Fernzugriff schaltet ein, solange jemand über Tailscale zuschaut – auch bei Schutz aus (z. B. kleine Warnlampe)."
}};
Object.assign(I18N.de, {
  "Live": "Live", "Cameras": "Kameras", "Zones": "Zonen", "Manual": "Anleitung", "Diary": "Tagebuch", "Game corner": "Spielecke",
  "📜 Whole log & archive": "📜 Ganzes Protokoll & Archiv",
  "Nothing important yet – everything else is in the whole log.": "Noch nichts Wichtiges – alles andere steht im ganzen Protokoll.",
  "Event log (important)": "Ereignisprotokoll (Wichtiges)",
  "🔐 Operator mode (lock settings)": "🔐 Bedienmodus (Einstellungen sperren)", "Operator mode": "Bedienmodus", "Unlock": "Entsperren",
  "lock-note": "Alles darf verstellt werden (ausser WLAN, Passwort, Autostart). Beim Entsperren mit der PIN wird alles zurückgesetzt.",
  "Set a new PIN? (Cancel = keep the current PIN)": "Neue PIN festlegen? (Abbrechen = bisherige PIN behalten)",
  "New PIN for unlocking (4-8 digits):": "Neue PIN zum Entsperren (4–8 Ziffern):", "Repeat the PIN:": "PIN wiederholen:",
  "The PINs are not the same": "Die PINs sind nicht gleich",
  "Lock the settings now? Only the main switches stay usable. Unlocking needs the PIN.": "Einstellungen jetzt sperren? Nur die wichtigsten Schalter bleiben bedienbar. Entsperren nur mit der PIN.",
  "Operator mode on": "Bedienmodus ein", "PIN:": "PIN:", "Settings unlocked": "Einstellungen entsperrt",
  "Pause the program for": "Programm pausieren für", "⏸ Pause program": "⏸ Programm pausieren",
  "all ok": "alles ok", "hide": "einklappen", "tap: show all values": "antippen: alle Werte zeigen", "Quick": "Schnell",
  "Dark theme": "Dunkel", "Light theme": "Hell", "Hide header": "Kopfzeile ausblenden",
  "UPS HAT": "USV-Akku", "on battery": "Akkubetrieb", "charging": "lädt", "mains power": "Netzbetrieb",
  "New version": "Neue Version", "Update now": "Jetzt aktualisieren", "later": "später",
  "Switch the program off now and start it again in": "Programm jetzt ausschalten und wieder starten in",
  "While paused there is no monitoring and there are no alarms.": "Während der Pause gibt es keine Überwachung und keine Alarme.",
  "Program is pausing …": "Programm wird pausiert …",
  "Search settings … (e.g. password)": "Einstellung suchen … (z. B. Passwort)", "Search settings …": "Einstellung suchen …",
  "Nothing found – try another word (e.g. password, Wi-Fi, siren).": "Nichts gefunden – anderes Wort versuchen (z. B. Passwort, WLAN, Sirene).",
  "Night report": "Nachtbericht", "Send now": "Jetzt senden", "Open animal diary": "Tier-Tagebuch öffnen", "Guest access": "Gast-Zugang",
  "Valid for": "Gültig für", "no time limit": "unbegrenzt", "Create new link": "Neuen Link erstellen", "Share / copy link": "Link teilen / kopieren",
  "End guest access": "Gast-Zugang beenden", "Battery": "Akku", "Battery is full now": "Akku ist jetzt voll", "days": "Tage",
  "Night report is off.": "Der Nachtbericht ist aus.", "Last report": "Letzter Bericht",
  "No report sent yet – the first one comes in the morning.": "Noch kein Bericht – der erste kommt am Morgen.",
  "Guest access is on": "Gast-Zugang ist an", "Guest access is off": "Gast-Zugang ist aus", "until": "bis",
  "Off – enter the capacity of the powerbank below.": "Aus – unten die Kapazität der Powerbank eintragen.",
  "Press «Battery is full now» after charging.": "Nach dem Laden «Akku ist jetzt voll» drücken.", "about": "ca.", "left": "übrig",
  "estimated": "geschätzt", "Night report sent": "Nachtbericht gesendet", "Not sent – push messages are not set up": "Nicht gesendet – Push-Nachrichten sind nicht eingerichtet",
  "End guest access? The link stops working at once.": "Gast-Zugang beenden? Der Link funktioniert sofort nicht mehr.",
  "Link copied": "Link kopiert", "Copy the link from the field": "Link aus dem Feld kopieren", "Battery marked as full": "Akku als voll markiert",
  "g-note": "Ein Link für Familie oder Mitcamper: Sie sehen nur das Live-Bild und können nichts verstellen. Der Gast muss den Pi erreichen können – im selben WLAN / Hotspot oder über Tailscale. Ein neuer Link macht den alten ungültig.",
  "b-note": "USV-Akku (Akku-Modul auf dem Pi): wird selbst erkannt und echt gemessen. Sonst Schätzung für die Powerbank: Kapazität minus Verbrauch seit «Akku ist jetzt voll».", "Presence": "Anwesenheit", "Security warning": "Sicherheitswarnung",
  "⚠ no password": "⚠ kein Passwort", "Saved": "Gespeichert", "Clear": "Löschen", "set": "gesetzt", "Test notification": "Test-Nachricht senden", "Test all channels": "Alle Kanäle testen", "testing …": "teste …", "No channel set up.": "Kein Kanal eingerichtet.",
  "Test sent": "Test gesendet", "Fixed times": "Feste Zeiten", "Sunset → sunrise": "Sonnenuntergang → Sonnenaufgang", "Sunrise → sunset": "Sonnenaufgang → Sonnenuntergang",
  "Shift (minutes)": "Versatz (Minuten)", "Time window": "Zeitfenster", "Applies": "Gilt", "Always": "Immer", "Only when nobody is home": "Nur wenn niemand zuhause ist",
  "Only when somebody is home": "Nur wenn jemand zuhause ist", "Skip dates (YYYY-MM-DD, ranges with .., MM-DD every year)": "Ausnahmedaten (JJJJ-MM-TT, Bereiche mit .., MM-TT jedes Jahr)",
  "home": "zuhause", "away": "abwesend", "unknown": "unbekannt",
  "Video source": "Videoquelle", "Source": "Quelle", "Schedule": "Zeitplan", "Recordings": "Aufzeichnungen",
  "Scan for cameras": "Nach Kameras suchen", "Scanning…": "Suche läuft …",
  "Automatic (first working USB camera)": "Automatisch (erste funktionierende USB-Kamera)",
  "Add network camera": "Netzwerk-Kamera hinzufügen", "Add": "Hinzufügen", "Remove this network camera?": "Diese Netzwerk-Kamera entfernen?",
  "+ Add schedule": "+ Zeitplan hinzufügen", "no schedules": "keine Zeitpläne", "Remove this schedule?": "Diesen Zeitplan entfernen?",
  "active now": "aktiv", "From": "Von", "To": "Bis", "unchanged": "unverändert", "ON": "EIN", "OFF": "AUS", "Enabled": "Aktiv",
  "connected": "verbunden", "connecting…": "verbinde …", "failed": "fehlgeschlagen", "switch failed": "Wechsel fehlgeschlagen", "still using": "weiter mit", "starting": "startet",
  "connection lost - reconnecting": "Verbindung verloren - verbinde neu", "no cameras found": "keine Kameras gefunden", "in use": "in Benutzung",
  "While a schedule is active, the listed features are forced ON or OFF. Afterwards they return to your own setting. Switching one by hand overrides the schedule until its next change.":
    "Solange ein Zeitplan aktiv ist, werden die gewählten Funktionen fest EIN oder AUS geschaltet. Danach gilt wieder deine eigene Einstellung. Wer von Hand schaltet, überstimmt den Zeitplan bis zu dessen nächster Änderung."
});
let LANG = "", THEME = "", videoOnly = false, TRIG = [], sigQ = "", sigE = "";
let HIDDEN = new Set();
try { LANG = localStorage.getItem("mw-lang") || ""; THEME = localStorage.getItem("mw-theme") || "";
      HIDDEN = new Set(JSON.parse(localStorage.getItem("mw-hidden") || "[]")); } catch (e) {}
Object.assign(I18N.de, {"Person alarms at the campfire (off: only animals - the people at the fire are not burglars)": "Personen-Alarm am Lagerfeuer (aus: nur Tiere – die Leute am Feuer sind keine Einbrecher)"});  // 2.97.0
Object.assign(I18N.de, {"Protection": "Schutz", "History": "Verlauf", "Message list": "Nachrichten", "Settings": "Einstellungen", "Sett.": "Einst.", "More": "Mehr", "Overview": "Übersicht", "Log": "Protokoll", "Sim": "Sim", "Recordings": "Aufnahmen", "Diary": "Tagebuch", "Zones": "Zonen", "Cameras": "Kameras", "Manual": "Anleitung", "Game corner": "Spielecke", "Tools": "Werkzeuge"});  // 2.98.0: the six tabs
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"conn-note": "Address of the simulator program. Usually not needed: the simulator announces itself in the network and is found by itself.", "autostart-note": "And off again (back to the real cameras and sensors) when none is there for a minute. Switched off by hand: stays off until a new simulator appears.", "sim-missing": "A simulator is missing? Switch on «Send to MoveEye» in the simulator. On a PC the Windows firewall must allow its port (8765; a second simulator e.g. 8767).", "sim-view-help": "The window of the simulator: drag with the left mouse button = move, right = turn, wheel = zoom (after a click into the picture), double click = fly there. Finger: tap = click, otherwise the page scrolls; with ✋ the finger controls the simulator (drag = move, ⟲ = turn, two fingers = zoom). The buttons below change the view."});  // 2.97.0: no raw keys in English
Object.assign(I18N.de, {"Protection": "Schutz", "History": "Verlauf", "Message list": "Nachrichten", "Sett.": "Einst.", "More": "Mehr", "Overview": "Übersicht", "Log": "Protokoll", "Sim": "Sim", "Protection level": "Schutzstufe", "Arming and own Wi-Fi": "Einschalten und eigenes WLAN", "What happens at an alarm?": "Was passiert bei Alarm?", "Theft protection": "Diebstahlschutz", "Device": "Gerät", "Guarded things (reference scan)": "Bewachte Dinge (Referenz-Scan)", "Backup (pictures off the device)": "Sicherung (Bilder weg vom Gerät)", "Zones, schedule, presence": "Zonen, Zeitplan, Anwesenheit", "Cameras & head": "Kameras & Kopf", "Devices & sensors": "Geräte & Sensoren", "Power supply": "Strom", "Network & access": "Netz & Zugang", "System": "System", "Draw the zones": "Zonen zeichnen", "Person": "Person", "Push": "Push", "Light": "Licht", "Siren": "Sirene", "Siren after {s} s": "Sirene nach {s} s", "Crossed out = off. Tap a step to change it. «Test protection» plays the chain.": "Durchgestrichen = aus. Ein Glied antippen = einstellen. «Schutz testen» spielt die Kette durch.", "Protection is off - nothing happens. Choose «Wachsam» or «Voll» above.": "Der Schutz ist aus – es passiert nichts. Oben «Wachsam» oder «Voll» wählen.", "Watchful": "Wachsam", "Full protection": "Voll", "in": "in", "Off": "Aus", "Settings": "Einstellungen"});  // 2.98.0: tabs, groups, alarm chain
Object.assign(I18N.de, {"Keep what is detected in the middle: persons, animals, moving things": "Hält Erkanntes in der Bildmitte: Personen, Tiere, Bewegtes"});  // 2.98.1
function t(s) { return (LANG === "de" && I18N.de[s]) || (window.LX ? LX(s) : "") || (LANG === "rm" && I18N.de[s]) || (I18N.en && I18N.en[s]) || s; }
let toastTimer = null;
function toast(msg) { let e = $("#toast"); if (!e) { e = el("div"); e.id = "toast"; document.body.appendChild(e); } e.textContent = msg; e.classList.add("on");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => e.classList.remove("on"), 2600); }
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}
function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(e => e.textContent = t(e.dataset.i18n));
  document.querySelectorAll(".stat small").forEach(e => { if (!e.dataset.en) e.dataset.en = e.textContent; e.textContent = t(e.dataset.en); });
  $("#btn-lang").textContent = (LANG || "en").toUpperCase(); $("#btn-lang").title = "Deutsch · Français · Italiano · Rumantsch · English";
  [["#all-open", "Expand all"], ["#all-close", "Collapse all"], ["#stick-speed", "Speed"], ["#swap-side", "Swap stick and buttons (left- / right-handed)"]].forEach(([id, k]) => { const b = $(id); if (b) { b.title = t(k); b.setAttribute("aria-label", t(k)); } });
  $("#relay-note").textContent = t("Auto: the relay switches on while its trigger is in view and stays on for the hold time. Animal and object triggers (e.g. cat) need the AI model.")
    + " " + t("Remote access switches on while somebody watches over Tailscale - also when disarmed (e.g. a small warning lamp).");
  $("#sched-note").textContent = t("While a schedule is active, the listed features are forced ON or OFF. Afterwards they return to your own setting. Switching one by hand overrides the schedule until its next change.");
  document.documentElement.lang = LANG;
}
function themeStep() { return document.documentElement.classList.contains("sxnight") ? "red" : THEME === "light" ? "light" : "dark"; }   // 573/578: Hell → Dunkel → Rotlicht
function applyTheme() {
  document.body.classList.toggle("light", THEME === "light");
  const s = themeStep(); $("#btn-theme").innerHTML = s === "light" ? "&#9790;" : s === "dark" ? "&#9673;" : "&#9728;";
  $("#btn-theme").classList.toggle("thred", s === "red");
}
function toggleTheme() { const n = {light: "dark", dark: "red", red: "light"}[themeStep()];
  document.documentElement.classList.toggle("sxnight", n === "red"); THEME = n === "light" ? "light" : "dark";
  try { localStorage.setItem("mw-theme", THEME); localStorage.setItem("mw-night", n === "red" ? "1" : "0"); } catch (e) {} applyTheme();
  if (window.sxThemeSaid) window.sxThemeSaid(n); }
function toggleLang() { langMenu(document.querySelector("#btn-lang")); }
// Full screen: the video fills the whole screen. Real browser full screen where the browser allows it
// (PC, Android); on iPhone / iPad (also Chrome there) only the page layout changes, which works everywhere.
const fsEl = () => document.fullscreenElement || document.webkitFullscreenElement || null;
function fsEnter() {
  const el = document.documentElement, f = el.requestFullscreen || el.webkitRequestFullscreen;
  if (!f) return;
  try { const r = f.call(el); if (r && r.catch) r.catch(() => {}); } catch (e) {}
}
function fsExit() {
  const f = document.exitFullscreen || document.webkitExitFullscreen;
  if (f && fsEl()) { try { const r = f.call(document); if (r && r.catch) r.catch(() => {}); } catch (e) {} }
}
function setVideoOnly(on) {
  if (on && window.pipShow) pipShow(false);
  videoOnly = on; document.body.classList.toggle("videoonly", on);
  voStick(on);
  if (on) { fsEnter(); scrollTo(0, 0); } else fsExit();
}
// full screen: the joystick moves into a see-through overlay (bottom right; ⇆ = other side); 3 s untouched = pale
let voIdleT = null;
function voWake() { const c = $("#vo-ctl"); if (!c) return; c.classList.remove("idle"); clearTimeout(voIdleT); voIdleT = setTimeout(() => c.classList.add("idle"), 3000); }
function voStick(on) {
  const st = $("#stick"), slot = $("#vo-slot"), box = document.querySelector(".ctl-stick .stickbox");   // 2.95.69: not the mover box (that one comes first)
  if (!st || !slot || !box) return;
  if (on && st.parentNode !== slot) slot.appendChild(st);
  if (!on && st.parentNode !== box) box.insertBefore(st, box.firstChild);
  const ms = $("#mstick"), mslot = $("#vo-mslot"), mbox = $("#mstickbox");      // the mover stick (2.94.0): other corner
  if (ms && mslot && mbox) { if (on && ms.parentNode !== mslot) mslot.appendChild(ms); if (!on && ms.parentNode !== mbox) mbox.insertBefore(ms, mbox.firstChild); }
  if (on) { voWake(); const sl = $("#stick-listen"), vl = $("#vo-listen"); if (sl && vl) vl.hidden = sl.hidden;
            [50, 400, 1000].forEach(ms => setTimeout(() => { if (videoOnly) scrollTo(0, 0); }, ms)); }
}
(function () {
  const c = $("#vo-ctl"); if (!c) return;
  let sw = false;
  try { const v = localStorage.getItem("mw-swap"); sw = v !== null ? v === "1" : localStorage.getItem("mw-vo-side") === "left"; } catch (e) {}
  function setSwap(on, tell) {          // ⇆ left- / right-handed: one choice for the page, landscape and fullscreen (per device)
    document.body.classList.toggle("swapside", on); c.classList.toggle("left", on);
    try { localStorage.setItem("mw-swap", on ? "1" : "0"); } catch (e) {}
    if (tell) toast("⇆ " + t(on ? "Stick on the other side" : "Stick back on its usual side"));
  }
  setSwap(sw, false);
  c.addEventListener("pointerdown", voWake); c.addEventListener("pointermove", e => { if (e.buttons) voWake(); });
  $("#vo-side").onclick = () => setSwap(!document.body.classList.contains("swapside"), false);
  const sb = $("#swap-side"); if (sb) sb.onclick = () => setSwap(!document.body.classList.contains("swapside"), true);
  // the round buttons: the whole column catches the touch and the NEAREST button wins. Phones (iPhone in particular) report a
  // touch some pixels away from where the finger is seen - with small round buttons that missed or hit the wrong one.
  const col = c.querySelector(".vbtns");
  const act = {"vo-center": () => $("#stick-center").click(), "vo-listen": () => listenToggle()};
  let downY = null;
  col.addEventListener("pointerdown", e => { e.preventDefault(); downY = e.clientY; });
  col.addEventListener("pointerup", e => {
    if (downY === null) return;
    const y = (downY + e.clientY) / 2; downY = null;
    const bs = [...col.querySelectorAll("button")].filter(b => !b.hidden);
    let best = null, bd = 1e9;
    bs.forEach(b => { const r = b.getBoundingClientRect(), d = Math.abs(y - (r.top + r.height / 2)); if (d < bd) { bd = d; best = b; } });
    if (best && act[best.id]) { best.classList.add("hit"); setTimeout(() => best.classList.remove("hit"), 180); act[best.id](); }
  });
  col.addEventListener("pointercancel", () => { downY = null; });
  setTimeout(() => { $("#vo-center").title = t("Centre"); $("#vo-listen").title = t("Listen"); $("#vo-side").title = t("Other side"); }, 1500);
})();
function toggleFullscreen() { setVideoOnly(!videoOnly); }
if (new URLSearchParams(location.search).get("vo") === "1") setTimeout(() => { try { setVideoOnly(true); } catch (e) {} }, 1500);   // preview: full-screen version

// ---- header height for the two scrolling columns (tablet / computer) ----
(function () {
  const H = document.querySelector("header"); if (!H) return;
  const set = () => document.documentElement.style.setProperty("--hdr-h", (document.body.classList.contains("hdrhidden") ? 0 : H.offsetHeight) + "px");
  if (window.ResizeObserver) new ResizeObserver(set).observe(H);
  new MutationObserver(set).observe(document.body, {attributes: true, attributeFilter: ["class"]});
  addEventListener("resize", set); set();
})();
// ---- search in the settings: typing hides everything that does not contain the words ----
(function () {
  const inp = $("#srch-in"); if (!inp) return;
  const norm = x => (x || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/ß/g, "ss");
  let saved = null;
  const words = el => norm([el.textContent, ...[...el.querySelectorAll("[data-i18n]")].map(e => e.dataset.i18n),
    ...[...el.querySelectorAll("[placeholder],[title]")].map(e => (e.placeholder || "") + " " + (e.title || "")),
    el.dataset && el.dataset.i18n || ""].join(" "));
  const rowsOf = c => [...c.children].filter(k => k.tagName !== "SUMMARY").flatMap(k => k.classList.contains("blk") ? [...k.children] : [k]);
  function clear() {
    document.querySelectorAll("#settings .s-hide, #settings .s-hit").forEach(e => e.classList.remove("s-hide", "s-hit"));
    if (saved) { saved.forEach((o, d) => { d.open = o; }); saved = null; }
    $("#srch-none").hidden = true; $("#srch-x").hidden = !inp.value;
  }
  function run() {
    const q = norm(inp.value.trim()).split(/\s+/).filter(w => w.length > 0);
    if (!q.length || q.join("").length < 2) { clear(); return; }
    $("#srch-x").hidden = false;
    if (!saved) { saved = new Map(); document.querySelectorAll("#settings details").forEach(d => saved.set(d, d.open)); }
    document.querySelectorAll("#settings .s-hide, #settings .s-hit").forEach(e => e.classList.remove("s-hide", "s-hit"));
    const hit = txt => q.every(w => txt.includes(w));
    let total = 0;
    document.querySelectorAll("#settings > details.grp").forEach(G => {
      let gHits = 0;
      const gTitle = hit(words(G.querySelector(":scope > summary")));
      const isSub = r => r.tagName === "DETAILS" && r.classList.contains("sub");
      const check = (rows, all) => { let n = 0; rows.forEach(r => {
        if (isSub(r)) { n += doSub(r, all); return; }                  // a topic inside a topic (e.g. thermal camera parts)
        const m = all || hit(words(r)); r.classList.toggle("s-hide", !m); if (m && !all) r.classList.add("s-hit"); if (m) n++; }); return n; };
      const doSub = (S, all) => { const sTitle = all || hit(words(S.querySelector(":scope > summary")));
        const n = check(rowsOf(S), sTitle); S.classList.toggle("s-hide", !n); if (n) S.open = true; return n; };
      gHits += check(rowsOf(G).filter(r => !r.classList.contains("fine")), gTitle);
      G.querySelectorAll(":scope > .fine").forEach(f => f.classList.add("s-hide"));
      G.classList.toggle("s-hide", !gHits); if (gHits) G.open = true; total += gHits;
    });
    const none = $("#srch-none"); none.hidden = !!total; none.textContent = t("Nothing found – try another word (e.g. password, Wi-Fi, siren).");
  }
  inp.addEventListener("input", run);
  inp.addEventListener("keydown", e => { if (e.key === "Escape") { inp.value = ""; clear(); inp.blur(); } });
  $("#srch-x").addEventListener("click", () => { inp.value = ""; clear(); inp.focus(); });
})();

const TODAY = (d => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"))(new Date());
// ---- night report, guest access, battery ----
const fmtH = h => h >= 48 ? Math.round(h / 24) + " " + t("days") : (h >= 1 ? Math.floor(h) + " h " + String(Math.round((h % 1) * 60)).padStart(2, "0") : Math.round(h * 60) + " min");
// ---- operator mode: only the main switches stay visible, everything else is locked (the server enforces it) ----
const OPER = new Set(["detection_on", "record", "notify_on", "browser_alarm", "timelapse_on", "eco_on", "patrol", "track_person",
  "relays_on", "noise_alarm", "thermal_on", "thermal_alarm", "report_on"]);
const LOCK_KEEP = new Set(["protect", "batt", "report"]);
let lockShown = null;
const LOCK_DENY = new Set(["net_mode", "hotspot_ssid", "hotspot_password", "hotspot_on", "update_url", "update_token", "update_unsigned", "autostart"]);
Object.assign(I18N.de, {"👥 Users": "👥 Benutzer", "Operate (arm, lights, camera, talk - no settings)": "Bedienen (Schutz einschalten, Licht, Kamera, Sprechen – keine Einstellungen)", "View only (live picture and recordings)": "Nur ansehen (Live-Bild und Aufnahmen)", "Each person gets an own login (user name + password). The web password stays the administrator. The log shows who armed or switched something.": "Jede Person bekommt ein eigenes Login (Benutzername + Passwort). Das Web-Passwort bleibt der Administrator. Im Protokoll steht, wer Schutz eingeschaltet oder etwas umgeschaltet hat.", "set the web password first (it is the administrator)": "zuerst das Web-Passwort setzen (es ist der Administrator)", "New password": "Neues Passwort", "New password for": "Neues Passwort für", "Remove this user?": "Diesen Benutzer entfernen?", "Add user": "Benutzer hinzufügen", "Name": "Name", "Password (6–64)": "Passwort (6–64)", "view only": "nur ansehen", "operate": "bedienen", "not allowed for your user": "für deinen Benutzer nicht erlaubt", "name: 1 to 24 letters / digits": "Name: 1 bis 24 Buchstaben / Ziffern", "this name exists already": "diesen Namen gibt es schon", "at most 20 users": "höchstens 20 Benutzer", "unknown user": "unbekannter Benutzer"});
Object.assign(I18N.de, {"AI (person detection)": "KI (Personenerkennung)", "🧪 Hardware check (step by step)": "🧪 Hardware prüfen (Schritt für Schritt)", "Hardware check": "Hardware-Prüfung", "result": "Ergebnis", "step": "Schritt", "The live picture must be visible.": "Das Live-Bild muss sichtbar sein.", "Movement": "Bewegung", "Walk once through the picture (2–3 m in front of the camera).": "Geh einmal durchs Bild (2–3 m vor der Kamera).", "Stand still in the picture for a moment - the AI should see a person.": "Bleib kurz im Bild stehen – die KI soll eine Person erkennen.", "Thermal camera": "Wärmebildkamera", "Hold your hand in front of the thermal camera.": "Halte die Hand vor die Wärmebildkamera.", "Servos": "Servos", "Tap the buttons: the camera head must turn. Then answer.": "Tippe auf die Knöpfe: der Kamerakopf muss sich drehen. Dann antworten.", "Microphone": "Mikrofon", "Clap your hands loudly once.": "Klatsche einmal laut in die Hände.", "Loudspeaker": "Lautsprecher", "Tap «Test sound» - do you hear it?": "Tippe auf «Testton» – hörst du ihn?", "Lights": "Licht", "Tap the buttons - does the light switch on and off?": "Tippe auf die Knöpfe – geht das Licht an und aus?", "Push message": "Push-Nachricht", "Tap «Send» - does the message arrive on the phone?": "Tippe auf «Senden» – kommt die Nachricht auf dem Handy an?", "Send": "Senden", "Trigger this sensor now (open the door, walk past, move the tag …).": "Löse diesen Sensor jetzt aus (Tür öffnen, vorbeigehen, Anhänger bewegen …).", "Check the parts marked ❌ (cable, settings) and run the check again.": "Prüfe die mit ❌ markierten Teile (Kabel, Einstellungen) und mach die Prüfung nochmals.", "Everything that was tested works.": "Alles, was geprüft wurde, funktioniert.", "Again": "Nochmals", "Close": "Schliessen", "Yes, works": "Ja, funktioniert", "No": "Nein", "Does not work": "Funktioniert nicht", "waiting …": "warte …", "Skip": "Überspringen", "detected": "erkannt"});
// ---- hardware check step by step: every part in turn, checked automatically where the page can see it ----
async function hwCheck() {
  let ov = $("#hw-ov"); if (ov) ov.remove();
  ov = el("div"); ov.id = "hw-ov"; ov.style.cssText = "position:fixed;inset:0;z-index:210;background:rgba(0,0,0,.82);display:flex;align-items:center;justify-content:center;padding:14px";
  const c = el("div", "card"); c.style.cssText = "max-width:480px;width:100%;max-height:92vh;overflow:auto"; ov.appendChild(c); document.body.appendChild(ov);
  let J = null; const st = async () => { try { J = await (await fetch("/api/state?lang=" + LANG)).json(); } catch (e) {} return J; };
  await st(); if (!J) { ov.remove(); return; }
  const S = () => J.state || {}, CF = () => J.cfg || {};
  const steps = [
    {id: "cam", ic: "📷", title: "Camera", text: "The live picture must be visible.", auto: s => (s.fps || 0) >= 1},
    {id: "motion", ic: "🚶", title: "Movement", text: "Walk once through the picture (2–3 m in front of the camera).", auto: s => (s.present || []).some(x => x === "motion" || x === "person" || x === "prealarm") || (s.persons || 0) > 0},
    {id: "ai", ic: "🧠", title: "AI (person detection)", text: "Stand still in the picture for a moment - the AI should see a person.", skip: (c, s) => !c.ai_enabled, auto: s => (s.persons || 0) > 0},
    {id: "thermal", ic: "♨️", title: "Thermal camera", text: "Hold your hand in front of the thermal camera.", skip: c => !c.thermal_source, auto: s => (s.present || []).includes("warm")},
    {id: "servo", ic: "🕹", title: "Servos", text: "Tap the buttons: the camera head must turn. Then answer.", btns: [["◀", () => post("/api/move", {dir: "left", step: 8})], ["▶", () => post("/api/move", {dir: "right", step: 8})], ["▲", () => post("/api/move", {dir: "up", step: 8})], ["▼", () => post("/api/move", {dir: "down", step: 8})]], ask: true},
    {id: "mic", ic: "🎤", title: "Microphone", text: "Clap your hands loudly once.", skip: c => !c.audio_in, auto: (s, b) => { const a = s.audio || {}; return a.peak != null && b.audio && b.audio.bg != null && a.peak > b.audio.bg + 15; }},
    {id: "spk", ic: "🔊", title: "Loudspeaker", text: "Tap «Test sound» - do you hear it?", skip: (c, s) => !(s.audio && s.audio.spk), btns: [["🔊 " + t("Test sound"), () => post("/api/audio", {action: "test"})]], ask: true},
    {id: "light", ic: "💡", title: "Lights", text: "Tap the buttons - does the light switch on and off?", skip: (c, s) => !(s.light_cfg && (s.light_cfg.white_out || s.light_cfg.ir_out)),
     btns: [["💡 " + t("On"), () => post("/api/light", {light: "white", mode: "on"})], ["🔴 IR " + t("On"), () => post("/api/light", {light: "ir", mode: "on"})], [t("Off"), () => Promise.all([post("/api/light", {light: "white", mode: "auto"}), post("/api/light", {light: "ir", mode: "auto"})])]], ask: true},
    {id: "push", ic: "📲", title: "Push message", text: "Tap «Send» - does the message arrive on the phone?", skip: c => !c.notify_on, btns: [["📲 " + t("Send"), () => post("/api/notify_test", {lang: LANG})]], ask: true}];
  (CF().sensors || []).forEach(x => steps.push({id: "s_" + x.id, ic: SENS_IC[x.kind] || "📡", title: x.name, raw: true, text: "Trigger this sensor now (open the door, walk past, move the tag …).",
    skip: c => !c.sens_on || !x.src, auto: (s, b) => { const q = ((s.sens || {}).st || {})[x.id] || {}, q0 = ((b.sens || {}).st || {})[x.id] || {};
      return q.state === "active" || q.state === "pulse" || (q.last && q.last !== q0.last); }}));
  const res = {}; let i = 0, timer = null;
  const done = () => { clearInterval(timer); c.textContent = "";
    c.appendChild(el("h3", "", "🧪 " + t("Hardware check") + " – " + t("result")));
    steps.forEach(x => { const r = res[x.id] || "skip"; c.appendChild(el("div", "", (r === "ok" ? "✅ " : r === "bad" ? "❌ " : "➖ ") + x.ic + " " + (x.raw ? x.title : t(x.title)))); });
    const bad = steps.filter(x => res[x.id] === "bad");
    c.appendChild(el("div", "mut", bad.length ? t("Check the parts marked ❌ (cable, settings) and run the check again.") : t("Everything that was tested works.")));
    post("/api/hwcheck", {results: res});
    const b = el("div", "btns"), ag = el("button", "sec", "↻ " + t("Again")), cl = el("button", "", t("Close")); ag.type = cl.type = "button";
    ag.onclick = hwCheck; cl.onclick = () => ov.remove(); b.append(ag, cl); c.appendChild(b); };
  const show = async () => {
    clearInterval(timer);
    while (i < steps.length && steps[i].skip && steps[i].skip(CF(), S())) { res[steps[i].id] = "skip"; i++; }
    if (i >= steps.length) { done(); return; }
    const x = steps[i], base = JSON.parse(JSON.stringify(S())); c.textContent = "";
    c.appendChild(el("div", "mut", t("Hardware check") + " · " + t("step") + " " + (i + 1) + " / " + steps.length));
    c.appendChild(el("h3", "", x.ic + " " + (x.raw ? x.title : t(x.title))));
    c.appendChild(el("div", "", t(x.text)));
    const live = el("div", "mut", ""); live.style.margin = "8px 0"; c.appendChild(live);
    if (x.btns) { const bb = el("div", "btns"); x.btns.forEach(([l, f]) => { const b = el("button", "sec", l); b.type = "button"; b.onclick = () => f(); bb.appendChild(b); }); c.appendChild(bb); }
    const nav = el("div", "btns"); const next = (r) => { res[x.id] = r; i++; show(); };
    if (x.ask) { const y = el("button", "", "✅ " + t("Yes, works")), n = el("button", "red", "❌ " + t("No")); y.type = n.type = "button"; y.onclick = () => next("ok"); n.onclick = () => next("bad"); nav.append(y, n); }
    else { const n = el("button", "red", "❌ " + t("Does not work")); n.type = "button"; n.onclick = () => next("bad"); nav.appendChild(n); live.textContent = "⏳ " + t("waiting …"); }
    const sk = el("button", "sec", t("Skip")), cl = el("button", "sec", "✕"); sk.type = cl.type = "button"; sk.onclick = () => next("skip"); cl.onclick = () => { clearInterval(timer); ov.remove(); };
    nav.append(sk, cl); c.appendChild(nav);
    if (x.auto) timer = setInterval(async () => { if (!document.body.contains(ov)) { clearInterval(timer); return; } await st();
      if (x.auto(S(), base)) { clearInterval(timer); live.textContent = "✅ " + t("detected"); setTimeout(() => next("ok"), 900); } }, 1000);
  };
  show();
}
// ---- several users: the web password = administrator; others log in with their own name and password ----
const ROLE_TXT = () => ({operate: t("Operate (arm, lights, camera, talk - no settings)"), view: t("View only (live picture and recordings)")});
async function usersLoad() {
  const box = $("#users-box"); if (!box) return;
  let j = {users: [], pw: false}; try { j = await (await fetch("/api/users")).json(); } catch (e) { return; }
  box.textContent = "";
  box.appendChild(el("div", "mut", t("Each person gets an own login (user name + password). The web password stays the administrator. The log shows who armed or switched something.")));
  if (!j.pw) { box.appendChild(el("div", "err", "⚠ " + t("set the web password first (it is the administrator)"))); return; }
  const err = el("div", "err");
  const roleSel = v => { const s = el("select"); Object.entries(ROLE_TXT()).forEach(([k, l]) => { const o = el("option", "", l); o.value = k; s.appendChild(o); }); s.value = v; return s; };
  const go = async b => { b.lang = LANG; const r = await post("/api/users", b); err.textContent = r.ok ? "" : "⚠ " + (r.error || "error"); if (r.ok) usersLoad(); return r; };
  j.users.forEach(u => {
    const row = el("div", "sens-card"), r1 = el("div", "row"), del = el("button", "sec", "✕"), pwb = el("button", "sec", "🔑"); del.type = pwb.type = "button";
    pwb.title = t("New password"); del.title = t("Remove");
    del.onclick = () => { if (confirm(t("Remove this user?") + "\n" + u.name)) go({action: "remove", name: u.name}); };
    pwb.onclick = () => { const p = prompt(t("New password for") + " " + u.name + " (6–64)"); if (p) go({action: "password", name: u.name, password: p}).then(r => { if (r.ok) toast("✓ " + t("Saved")); }); };
    const rs = roleSel(u.role); rs.onchange = () => go({action: "role", name: u.name, role: rs.value});
    r1.append(el("b", "", "👤 " + u.name), pwb, del); row.append(r1, rs); box.appendChild(row);
  });
  const add = el("div", "sens-card"), nm = el("input"), pw = el("input"), rs = roleSel("operate"), ab = el("button", "", "+ " + t("Add user"));
  nm.type = "text"; nm.maxLength = 24; nm.placeholder = t("Name"); pw.type = "password"; pw.maxLength = 64; pw.placeholder = t("Password (6–64)"); pw.autocomplete = "new-password";
  [nm, pw, rs].forEach(x => { x.style.cssText = "width:100%;margin-top:6px"; }); ab.type = "button"; ab.style.marginTop = "8px";
  ab.onclick = () => go({action: "add", name: nm.value, password: pw.value, role: rs.value});
  add.append(nm, pw, rs, ab); box.append(add, err);
  trustLoad(box);
}
// ---- trusted devices (2.95.19): after a login the browser is remembered - no new login after an update ----
async function trustLoad(parent) {
  let j = null; try { j = await (await fetch("/api/trusted")).json(); } catch (e) { return; }
  if (!j || !j.ok || !j.pw) return;
  let box = $("#trust-box"); if (!box) { box = el("div", "sens-card"); box.id = "trust-box"; parent.appendChild(box); }
  box.textContent = "";
  box.appendChild(el("b", "", "🔐 " + t("Trusted devices")));
  box.appendChild(el("div", "mut", t("A device that has logged in once is remembered (also after updates). Remove a device here if it is lost or should log in again.")));
  const d2 = n => { if (!n) return "–"; const d = new Date(n * 1000); return d.toLocaleDateString() + " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2); };
  (j.devices || []).forEach((x, i) => { const r = el("div", "row"); r.style.marginTop = "6px";
    const tx = el("div", ""); tx.style.flex = "1"; tx.append(el("div", "", (x.me ? "⭐ " : "") + x.name + " · " + x.user + (x.me ? " (" + t("this device") + ")" : "")),
      el("div", "mut", t("since") + " " + d2(x.t0) + " · " + t("last") + " " + d2(x.seen) + " · " + (x.ip || "")));
    const b = el("button", "sec", "✕"); b.type = "button"; b.title = t("Remove");
    b.onclick = async () => { if (confirm(t("Remove this device? It must log in again.") + "\n" + x.name)) { await post("/api/trusted", {action: "remove", i: i}); trustLoad(parent); } };
    r.append(tx, b); box.appendChild(r); });
  if ((j.devices || []).length > 1) { const c = el("button", "sec", t("Remove all")); c.type = "button"; c.style.marginTop = "8px";
    c.onclick = async () => { if (confirm(t("Remove all trusted devices? Every device must log in again."))) { await post("/api/trusted", {action: "clear"}); trustLoad(parent); } }; box.appendChild(c); }
}
function applyRole(me) {
  const role = (me && me.role) || "admin";
  document.body.classList.toggle("role-operate", role === "operate"); document.body.classList.toggle("role-view", role === "view");
  const b = $("#b-me"); if (b) { b.hidden = !(me && me.users) || !me.name; b.textContent = "👤 " + (me && me.name || "") + (role !== "admin" ? " · " + t(role === "view" ? "view only" : "operate") : ""); }
}
function applyLock(on) {
  document.body.classList.toggle("locked", on);
  $("#lock-bar").hidden = !on;
  document.querySelectorAll("#settings .l-off").forEach(e => e.classList.remove("l-off"));
  if (!on) return;
  // everything stays usable (and is put back at unlocking) - only what could lock the owner out is hidden
  document.querySelectorAll("#settings [data-key]").forEach(r => { if (LOCK_DENY.has(r.dataset.key)) r.classList.add("l-off"); });
  document.querySelectorAll('[data-view="wifi"]').forEach(r => r.classList.add("l-off"));
}
async function lockAct() {
  const L = (window.LASTSTATE || {}).lock || {};
  let np = "";
  if (!L.pin_set || confirm(t("Set a new PIN? (Cancel = keep the current PIN)"))) {
    np = prompt(t("New PIN for unlocking (4-8 digits):")) || ""; if (!np) return;
    if ((prompt(t("Repeat the PIN:")) || "") !== np) { toast("⚠ " + t("The PINs are not the same")); return; }
  }
  if (!confirm(t("Switch on operator mode? Everything may be changed except Wi-Fi, password and autostart; unlocking with the PIN puts everything back."))) return;
  const r = await post("/api/lock", {action: "lock", new_pin: np, lang: LANG});
  toast(r.ok ? "🔐 " + t("Operator mode on") : "⚠ " + (r.error || "error")); refresh();
}
function lockBtn() { const L = (window.LASTSTATE || {}).lock || {}; if (L.on) unlockAct(); else lockAct(); }
function lockPaint(s) {
  const L = s.lock || {}, b = $("#lock-btn"), i = $("#lock-info"); if (!b) return;
  b.textContent = L.on ? "🔓 " + t("End operator mode (PIN)") : t("🔐 Operator mode (lock settings)");
  b.classList.toggle("lock-on", !!L.on);
  i.hidden = !L.on; i.textContent = L.on ? "🟡 " + t("Operator mode is on") + (L.since ? " " + t("since") + " " + L.since : "") + " · " + t("unlocking puts everything back") : "";
}
async function unlockAct() {
  const pin = prompt(t("PIN:")); if (!pin) return;
  const r = await post("/api/lock", {action: "unlock", pin: pin, lang: LANG});
  toast(r.ok ? "🔓 " + t("Settings unlocked") + (r.restored ? " · " + r.restored + " " + t("changes put back") : "") : "⚠ " + (r.error || "error")); refresh();
}
let updBarFor = "";
function updBar(s) {
  const u = s.update_new || {}, lk = !!(s.lock && s.lock.on);
  let later = ""; try { later = sessionStorage.getItem("mw-upd-later") || ""; } catch (e) {}
  const want = u.version && !lk && later !== u.version && !s.pending;
  let bar = $("#updbar");
  if (!want) { if (bar) bar.remove(); updBarFor = ""; return; }
  if (bar && updBarFor === u.version) return;
  if (bar) bar.remove();
  updBarFor = u.version;
  bar = el("div"); bar.id = "updbar";
  const tt = el("div", ""); tt.style.flex = "1";
  tt.append(el("b", "", "⬆ " + t("New version") + " " + u.version + " " + t("available")), el("div", "mut", u.notes ? u.notes.slice(0, 120) + (u.notes.length > 120 ? " …" : "") : ""));
  const go = el("button", "", t("Update now")); go.type = "button";
  go.onclick = async () => {
    if (!confirm(t("Switch to version") + " " + u.version + "?\n\n" + t("The program restarts (about 20 seconds). Settings, recordings and zones stay."))) return;
    go.disabled = true; go.textContent = t("Downloading and checking …");
    const r = await updInstall(u.version);
    if (!r.ok) { toast("⚠ " + (r.error || "error")); go.disabled = false; go.textContent = t("Update now"); return; }
    bar.remove();
  };
  const no = el("button", "sec", t("later")); no.type = "button";
  no.onclick = () => { try { sessionStorage.setItem("mw-upd-later", u.version); } catch (e) {} bar.remove(); };
  bar.append(tt, go, no); document.body.appendChild(bar);
}
function paintExtras(s) {
  window.LASTSTATE = s; updBar(s);
  const lk = !!(s.lock && s.lock.on);
  if (lk !== lockShown) { lockShown = lk; applyLock(lk); }
  hb("#b-lock", lk, "🔐 " + t("Operator mode"), "yel"); lockPaint(s);
  const pe = $("#pr-err"); if (pe && s.autostart_msg && !pe.textContent) pe.textContent = "⚠ " + s.autostart_msg;
  const L = s.report_last || {}, rl = $("#rep-line");
  if (rl) rl.textContent = (s.report_on ? "" : t("Night report is off.") + "\n")
    + (L.text ? t("Last report") + " " + L.t.slice(11, 16) + (L.sent ? " ✓" : "") + ":\n" + L.text : t("No report sent yet – the first one comes in the morning."));
  const g = s.guest || {}, gs = $("#g-st");
  if (gs) {
    gs.textContent = g.active ? "🟢 " + t("Guest access is on") + (g.until ? " · " + t("until") + " " + new Date(g.until * 1000).toLocaleString(LOCALE(LANG), {weekday: "short", hour: "2-digit", minute: "2-digit"}) : " · " + t("no time limit"))
      + (g.watching ? " · 👁 " + g.watching : "") : "⚪ " + t("Guest access is off");
    $("#g-share").hidden = $("#g-end").hidden = $("#g-link").hidden = !g.active;
    if (g.active) $("#g-link").value = location.origin + g.path;
  }
  const b = s.battery || {}, bl = $("#batt-line"), bfb = $("#batt-full-btn");
  if (bfb) bfb.hidden = b.src === "ups";
  if (bl && b.src === "ups") bl.textContent = "🔋 " + t("UPS HAT") + (b.model === "e" ? " (E)" : "") + ": " + b.pct + " % · " + b.volt + " V · "
    + (b.on_battery ? "⚡ " + t("on battery") + " · " + t("about") + " " + fmtH(b.hours) + " " + t("left") + " · " + b.watts + " W"
       : (b.charging ? "🔌 " + t(b.fast ? "fast charging" : "charging") + (b.full_min ? " · " + t("full in") + " " + fmtH(b.full_min / 60) : "") : "🔌 " + t("mains power")))
    + (b.cells ? "\n" + t("Cells") + ": " + b.cells.map(c => c.toFixed(2)).join(" / ") + " V" + (b.vbus ? " · USB-C " + b.vbus + " V" : "") : "");
  else if (bl) bl.textContent = !b.on ? t("Off – enter the capacity of the powerbank below.")
    : (b.pct == null ? t("Press «Battery is full now» after charging.") + " · " + b.watts + " W"
       : "🔋 " + b.pct + " % · " + t("about") + " " + fmtH(b.hours) + " " + t("left") + " · " + b.watts + " W" + (b.src === "estimate" ? " (" + t("estimated") + ")" : ""));
  if (bl && s.batt_save && s.batt_save.on) bl.textContent += " · 🐢 " + t("Battery saver active: fewer pictures, the AI less often");   // 2.98.13 (105)
}
async function repSend() { const r = await post("/api/report/send", {lang: LANG}); toast(r.ok ? t("Night report sent") : t("Not sent – push messages are not set up")); refresh(); }
async function guestAct(a) {
  if (a === "end" && !confirm(t("End guest access? The link stops working at once."))) return;
  const r = await post("/api/guest", {action: a, hours: Number($("#g-hours").value), lang: LANG});
  if (!r.ok) { toast("⚠ " + (r.error || "error")); return; }
  if (a === "create") { $("#g-link").hidden = false; $("#g-link").value = location.origin + r.path; guestShare(); }
  refresh();
}
async function guestShare() {
  const u = $("#g-link").value; if (!u) return;
  try { if (navigator.share) { await navigator.share({title: "MoveEye – Live", url: u}); return; } } catch (e) { if (e && e.name === "AbortError") return; }
  try { await navigator.clipboard.writeText(u); toast(t("Link copied")); } catch (e) { $("#g-link").hidden = false; $("#g-link").select(); toast(t("Copy the link from the field")); }
}
async function battFull() { const r = await post("/api/battery", {}); if (r.ok) toast(t("Battery marked as full")); refresh(); }
function pageFullscreen() { if (fsEl()) fsExit(); else fsEnter(); }

// ---- show / hide every field individually (stored per browser) ----
function saveHidden() { try { localStorage.setItem("mw-hidden", JSON.stringify([...HIDDEN])); } catch (e) {} }
function applyHidden() {
  document.querySelectorAll("[data-view]").forEach(e => e.classList.toggle("vh", HIDDEN.has(e.dataset.view)));
  document.body.classList.toggle("noside", HIDDEN.has("sidebar"));
  $("#btn-side").innerHTML = HIDDEN.has("sidebar") ? "&#9664;" : "&#9654;";
  const sc = $("#side-close"); if (sc) sc.title = t("Hide settings"); const so = $("#side-open"); if (so) so.title = t("Show settings");
}
function toggleHidden(k) { HIDDEN.has(k) ? HIDDEN.delete(k) : HIDDEN.add(k); saveHidden(); applyHidden(); }
function buildViewMenu() {
  const m = $("#viewmenu"); m.textContent = ""; const groups = {};
  const q = el("div", "vmq");
  const qb = (txt, fn) => { const b = el("button", "sec", txt); b.type = "button"; b.onclick = e => { e.stopPropagation(); fn(); buildViewMenu(); }; q.appendChild(b); };
  qb({light: "☾ " + t("Dark theme"), dark: "◉ " + t("Red light view"), red: "☀ " + t("Light theme")}[themeStep()], toggleTheme);
  qb("🌐 " + (LANGN[LANG] || "English") + " …", () => setTimeout(() => langMenu($("#btn-lang")), 0));
  qb((HIDDEN.has("sidebar") ? "◀ " : "▶ ") + t("Settings panel"), () => toggleHidden("sidebar"));
  qb("▴ " + t("Hide header"), () => { const b = $("#btn-hdr"); if (b) b.click(); $("#viewmenu").hidden = true; });
  if (window.lvMenu) qb("◫ " + t("View of the live page …"), () => { $("#viewmenu").hidden = true; setTimeout(window.lvMenu, 0); });   // 2.98.26: live cards per device (536)
  m.append(el("h3", "", t("Quick")), q);
  document.querySelectorAll("[data-view]").forEach(e => { if (window.lvMenu && e.closest("#lv-side,#lv-main")) return;
    (groups[e.dataset.vgroup] = groups[e.dataset.vgroup] || []).push(e); });
  ["Header", "Panels", "Settings"].forEach(g => {
    if (!groups[g]) return;
    m.appendChild(el("h3", "", t(g)));
    groups[g].forEach(e => {
      const lab = el("label"), cb = el("input"); cb.type = "checkbox"; cb.checked = !HIDDEN.has(e.dataset.view);
      cb.onchange = () => toggleHidden(e.dataset.view);
      lab.append(cb, el("span", "", t(e.dataset.vlabel))); m.appendChild(lab);
    });
  });
  const b = el("button", "sec", t("Show all")); b.style.cssText = "margin-top:10px;width:100%";
  b.onclick = () => { HIDDEN.clear(); saveHidden(); applyHidden(); buildViewMenu(); };
  m.appendChild(b);
}
function toggleViewMenu(ev) { ev.stopPropagation(); const m = $("#viewmenu"); m.hidden = !m.hidden; if (!m.hidden) buildViewMenu(); }
document.addEventListener("click", e => { const m = $("#viewmenu"); if (!m.hidden && !m.contains(e.target) && document.body.contains(e.target)) m.hidden = true; });

function badge(id, text, cls) { const b = $(id); b.textContent = text; b.className = "badge" + (cls ? " " + cls : "") + (HIDDEN.has(b.dataset.view) ? " vh" : "") + keepQ(b, cls); }
// a value in its normal range stays hidden behind "all ok" also when another poll refreshes it (no flicker)
function keepQ(b, cls) { return (typeof QUIET !== "undefined" && QUIET.includes(b.id) && !/red|yel|org/.test(cls || "")) ? " q" : ""; }
function act(a) { post("/api/action", {action: a}); }
function showPos(pan, tilt) {
  if (typeof pan !== "number" || typeof tilt !== "number") return;
  const x = Math.max(0, Math.min(100, pan)), y = 100 - Math.max(0, Math.min(100, tilt));     // tilt up = higher on the stick
  const p = $("#spos"); if (!p) return;
  p.style.left = x + "%"; p.style.top = y + "%";
  $("#sline-v").style.left = x + "%"; $("#sline-h").style.top = y + "%";
  const tx = $("#spos-txt"); tx.textContent = "";
  tx.append(el("b", "", "◎ "), document.createTextNode("Pan " + Math.round(pan) + " % · Tilt " + Math.round(tilt) + " %"));
}
function psText(x) {                     // patrol status in words: «moving to waypoint 2/4 (88/82)» -> «fährt zu Wegpunkt …»
  let m = /^moving to waypoint (\d+)\/(\d+) \((.+)\)$/.exec(x || "");
  if (m) return t("moving to waypoint") + " " + m[1] + "/" + m[2] + " (" + m[3] + ")";
  m = /^dwelling at (.+)$/.exec(x || ""); if (m) return t("waiting at") + " " + m[1];
  m = /^(.+?) \((.+)\)$/.exec(x || ""); if (m && t(m[1]) !== m[1]) return t(m[1]) + " (" + m[2] + ")";   // 2.98.30 (162)
  return t(x || "");
}
Object.assign(I18N.de, {"Temperature sensor (BME280 / BMP280 on I2C or DS18B20 on GPIO 4), if connected": "Temperaturfühler (BME280 / BMP280 an I2C oder DS18B20 an GPIO 4), falls angeschlossen", "Temperature sensor: correction (°C)": "Temperaturfühler: Korrektur (°C)", "Outside": "Aussen", "no temperature sensor": "kein Temperaturfühler", "Outside temperature": "Aussentemperatur", "Take the location from the phone (the page must be open over https)": "Standort vom Handy übernehmen (die Seite muss über https offen sein)", "GPS position in photos and videos": "GPS-Position in Fotos und Videos", "Location": "Standort", "from the phone": "vom Handy", "fixed (settings)": "fest (Einstellungen)", "unknown – the phone shares it only over the https page": "unbekannt – das Handy gibt ihn nur über die https-Seite weiter", "Night vision": "Nachtsicht", "Night vision: green picture, thermal outlines and temperatures": "Nachtsicht: grünes Bild, Wärme-Umrisse und Temperaturen",
  "Slow": "Langsam", "Medium": "Mittel", "Fast": "Schnell", "Swap stick and buttons (left- / right-handed)": "Stick und Knöpfe tauschen (Links- / Rechtshänder)",
  "Stick on the other side": "Stick auf der anderen Seite", "Stick back on its usual side": "Stick wieder auf der gewohnten Seite",
  "moving to waypoint": "fährt zu Wegpunkt", "waiting at": "wartet bei", "paused (tracking person)": "Pause (verfolgt Person)",
  "paused (manual control)": "Pause (Handsteuerung)"});
// waypoints drawn on the stick background (number = order); round trip: dashed line from the last back to the first
var WPSIG = "";
function wpPaint(wps, c) {
  const g = $("#swp"), g2 = $("#swp2"); if (!g || !g2) return;          // lines below the knob, numbered points above it
  const loop = c.patrol_mode === "loop", sig = JSON.stringify(wps) + loop;
  g.classList.toggle("run", !!c.patrol); g2.classList.toggle("run", !!c.patrol);
  if (sig === WPSIG) return; WPSIG = sig; g.textContent = ""; g2.textContent = "";
  const NS = "http://www.w3.org/2000/svg", mk = (n, a, to) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); (to || g).appendChild(e); return e; };
  const P = (wps || []).map(w => [Math.max(0, Math.min(100, w[0])), 100 - Math.max(0, Math.min(100, w[1]))]);
  if (P.length > 1) mk("polyline", {points: P.map(p => p.join(",")).join(" ")});
  if (P.length > 2 && loop) mk("line", {x1: P[P.length - 1][0], y1: P[P.length - 1][1], x2: P[0][0], y2: P[0][1]});
  P.forEach((p, i) => { mk("circle", {cx: p[0], cy: p[1], r: 4.6}, g2); mk("text", {x: p[0], y: p[1] + .2}, g2).textContent = i + 1; });
}
function move(dir) { post("/api/move", {dir: dir, step: parseFloat($("#step").value)}).then(r => { if (r && r.ok) showPos(r.pan, r.tilt); }); }

// ---- relays ----
function relayPost(body) {
  body.lang = LANG;
  return post("/api/relay", body).then(r => {
    const e = $("#relay-err"); e.textContent = r.ok ? "" : "⚠ " + (r.error || "error");
    if (!r.ok) setTimeout(() => { e.textContent = ""; }, 5000);
    sigQ = sigE = "";            // force a rebuild with the new values
    return r;
  });
}
let sigL = "";
function renderLights(L, st) {
  const q = $("#light-quick"); if (!q || !L) return;
  const names = {white: "💡 " + t("White"), ir: "🔴 " + t("Infrared")};
  const sl = JSON.stringify([L.white_out, L.ir_out, LANG]);
  if (sl !== sigL) {
    sigL = sl; q.textContent = "";
    ["white", "ir"].forEach(n => {
      const dot = el("span", "dot", "●"); dot.id = "lq-dot-" + n;
      const seg = el("span", "seg"); seg.id = "lq-seg-" + n;
      ["off", "on", "auto"].forEach(m => {
        const b = el("button", "", t(m === "off" ? "Off" : m === "on" ? "On" : "Auto")); b.dataset.mode = m;
        b.onclick = () => post("/api/light", {light: n, mode: m}).then(() => refresh()); seg.appendChild(b);
      });
      const info = el("span", "mut", L[n + "_out"] ? "" : t("no output chosen")); info.id = "lq-info-" + n; info.style.fontSize = "11px";
      q.append(dot, el("span", "", names[n]), seg, info);
    });
  }
  ["white", "ir"].forEach(n => {
    const d = $("#lq-dot-" + n); if (d) d.classList.toggle("on", !!(st.lights || {})[n]);
    const s = $("#lq-seg-" + n); if (s) s.querySelectorAll("button").forEach(b => b.className = b.dataset.mode === L[n] ? "sel-" + L[n] : "");
    const i = $("#lq-info-" + n); if (i && L[n + "_out"]) i.textContent = L[n] === "auto" ? t(L[n + "_auto_label"] || "") : "";
  });
}
function renderRelays(relays, states, aiOk) {
  const q = $("#relay-quick");
  const sq = JSON.stringify([relays.map(r => [r.name, r.trigger]), aiOk]);
  if (sq !== sigQ && !q.contains(document.activeElement)) {
    sigQ = sq; q.textContent = "";
    if (!relays.length) q.appendChild(el("span", "mut", t("no relays")));
    relays.forEach((r, i) => {
      const dot = el("span", "dot", "●"); dot.id = "rq-dot-" + i;
      const seg = el("span", "seg"); seg.id = "rq-seg-" + i;
      ["off", "on", "auto"].forEach(m => {
        const b = el("button", "", t(m === "off" ? "Off" : m === "on" ? "On" : "Auto")); b.dataset.mode = m;
        b.onclick = () => relayPost({action: "set", index: i, field: "mode", value: m}); seg.appendChild(b);
      });
      const sel = el("select");
      TRIG.forEach(o => { const op = el("option", "", o.label); op.value = o.key; sel.appendChild(op); });
      sel.value = r.trigger;
      sel.onchange = () => relayPost({action: "set", index: i, field: "trigger", value: sel.value});
      const tw = el("span"); tw.appendChild(sel);
      if (!aiOk && !["person", "motion", "prealarm", "warm", "noise"].includes(r.trigger)) { const w = el("span", "warn", " ⚠"); w.title = t("needs AI model"); tw.appendChild(w); }
      q.append(dot, el("span", "", r.name), seg, tw);
    });
  }
  relays.forEach((r, i) => {
    const d = $("#rq-dot-" + i); if (d) d.classList.toggle("on", !!states[i]);
    const s = $("#rq-seg-" + i); if (s) s.querySelectorAll("button").forEach(b => b.className = b.dataset.mode === r.mode ? "sel-" + r.mode : "");
  });
  const ed = $("#relay-editor"), se = JSON.stringify(relays);
  if (se !== sigE && !ed.contains(document.activeElement)) {
    sigE = se; ed.textContent = "";
    relays.forEach((r, i) => {
      const box = el("div", "rel-ed");
      const field = (label, input) => { const w = el("label", "mut"); w.append(el("div", "", t(label)), input); return w; };
      const send = (f, v) => relayPost({action: "set", index: i, field: f, value: v});
      const name = el("input"); name.type = "text"; name.value = r.name; name.onchange = () => send("name", name.value);
      const gpio = el("input"); gpio.type = "number"; gpio.min = 2; gpio.max = 27; gpio.value = r.gpio; gpio.onchange = () => send("gpio", gpio.value);
      const hold = el("input"); hold.type = "number"; hold.min = 0.5; hold.max = 600; hold.step = 0.5; hold.value = r.hold; hold.onchange = () => send("hold", hold.value);
      const al = el("input"); al.type = "checkbox"; al.className = "sw"; al.checked = r.active_low; al.onchange = () => send("active_low", al.checked);
      const alw = el("label", "row tg"); alw.append(el("span", "", t("Active low")), al);
      const del = el("button", "sec", t("Remove")); del.onclick = () => { if (confirm(t("Remove this relay?"))) relayPost({action: "remove", index: i}); };
      box.append(field("Name", name), field("GPIO", gpio), field("Hold (s)", hold), alw, del);
      ed.appendChild(box);
    });
  }
}

// ---- video source (scan, choose, network cameras) ----
let SRC = null, sigS = "", lastSrcId = null, autoScanned = false;
function srcErr(msg) {
  const e = $("#src-err"); e.textContent = msg ? "⚠ " + msg : "";
  if (msg) setTimeout(() => { e.textContent = ""; }, 6000);
}
function tStatus(s) {
  if (!s) return "";
  if (s.startsWith("switch failed:")) return t("switch failed") + s.slice(14).replace("(still using ", "(" + t("still using") + " ");
  if (s.startsWith("failed:")) return t("failed") + s.slice(7);
  return t(s);
}
function srcName(it) { return it.id === "auto" ? t("Automatic (first working USB camera)") : it.name; }
function renderSourceStatus(s) {
  $("#src-status").textContent = (s.source_label || "–") + (s.source_res ? " · " + s.source_res : "") + " · " + tStatus(s.source_status);
}
async function loadSources(scan) {
  const btn = $("#btn-scan");
  if (scan) { btn.disabled = true; btn.textContent = t("Scanning…"); }
  let r = null;
  try { r = scan ? await post("/api/sources/scan", {}) : await (await fetch("/api/sources")).json(); } catch (e) { r = null; }
  if (scan) { btn.disabled = false; btn.textContent = t("Scan for cameras"); }
  if (r && r.items) SRC = r;
  sigS = ""; renderSources();
  if (!scan && SRC && !SRC.scanned && !SRC.scanning && !autoScanned) { autoScanned = true; loadSources(true); }   // first visit: look for cameras once
}
function scanSources() { loadSources(true); }
function srcPost(body) {
  body.lang = LANG;
  return post("/api/source", body).then(r => { srcErr(r.ok ? "" : (r.error || "error")); loadSources(false); return r; });
}
function selectSource(id) { srcPost({action: "select", id: id}); }
function addIpSource() {
  srcPost({action: "add", name: $("#ip-name").value, url: $("#ip-url").value, select: true})
    .then(r => { if (r.ok) { $("#ip-name").value = ""; $("#ip-url").value = ""; } });
}
function renderSources() {
  if (!SRC || !SRC.items) return;
  $("#src-hints").textContent = (SRC.hints || []).join(" ");
  const L = $("#src-list"), sig = JSON.stringify([SRC.items, SRC.selected, SRC.active, LANG]);
  if (sig === sigS) return;
  sigS = sig; L.textContent = "";
  SRC.items.forEach(it => {
    const row = el("label", "srcrow");
    const rb = el("input"); rb.type = "radio"; rb.name = "src"; rb.checked = it.id === SRC.selected;
    rb.onchange = () => selectSource(it.id);
    const dot = el("span", "dot" + (it.id === SRC.active ? " on" : ""), "●");
    const info = el("span"); info.style.flex = "1"; info.style.minWidth = "0";
    info.append(el("div", "", srcName(it)), el("div", "mut", (it.detail || "").replace("in use", t("in use"))));
    row.append(rb, dot, info);
    if (it.kind === "url") {
      const x = el("button", "sec", "✕"); x.style.padding = "2px 8px"; x.title = t("Remove");
      x.onclick = e => { e.preventDefault(); if (confirm(t("Remove this network camera?"))) srcPost({action: "remove", id: it.id.slice(4)}); };
      row.appendChild(x);
    }
    L.appendChild(row);
  });
  if (SRC.items.length <= 1) L.appendChild(el("div", "mut", t("no cameras found")));
}

// ---- schedule ----
let FEAT = [], sigC = "";
const DAYS = () => ({de: ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"], fr: ["lu", "ma", "me", "je", "ve", "sa", "di"], it: ["lu", "ma", "me", "gi", "ve", "sa", "do"], rm: ["gli", "ma", "me", "gie", "ve", "so", "du"]})[LANG] || ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
function schedPost(body) {
  body.lang = LANG;
  return post("/api/schedule", body).then(r => {
    const e = $("#sched-err"); e.textContent = r.ok ? "" : "⚠ " + (r.error || "error");
    if (!r.ok) setTimeout(() => { e.textContent = ""; }, 5000);
    sigC = "";                                        // rebuild with the values the server really stored
    return r;
  });
}
function textField(x) {
  const wrap = el("div", "sl"), top = el("div", "row"); top.appendChild(el("span", "", x.label)); wrap.appendChild(top);
  let inp;
  if (x.kind === "enum") { inp = el("select"); inp.dataset.key = x.key; x.choices.forEach(c => { const o = el("option", "", (x.labels && x.labels[c]) || c); o.value = c; inp.appendChild(o); }); inp.value = x.value; }
  else { inp = el("input"); inp.type = x.kind === "secret" ? "password" : "text"; inp.value = x.value || ""; inp.autocomplete = "off";
         if (x.kind === "secret" && x.set) inp.placeholder = "•••••• (" + t("set") + ")";
         else if (x.placeholder) inp.placeholder = x.placeholder; }
  inp.style.width = "100%"; inp.style.marginTop = "4px";
  const err = el("div", "err");
  const send = v => post("/api/text", {key: x.key, value: v, lang: LANG}).then(r => { err.textContent = r.ok ? "" : "⚠ " + (r.error || "error"); if (r.ok) toast(t("Saved")); return r; });
  inp.onchange = () => { if (x.kind === "secret" && inp.value === "") return;
    send(inp.value).then(r => { if (r.ok && x.kind === "secret") { inp.value = ""; inp.placeholder = "•••••• (" + t("set") + ")"; } }); };
  wrap.dataset.key = x.key;
  wrap.append(inp, err);
  if (x.kind === "secret") { const c = el("button", "sec", t("Clear")); c.style.marginTop = "2px"; c.onclick = () => send(" ").then(r => { if (r.ok) inp.placeholder = ""; }); wrap.appendChild(c); }
  return wrap;
}
// ---- message texts: one card per message, tap a chip to insert a placeholder, preview with example values ----
function msgBoxes(d, texts) {
  const by = {}; texts.forEach(x => { by[x.key] = x; });
  const PH = [["name", "Device name"], ["time", "Time"], ["date", "Date"], ["count", "Number of persons"], ["camera", "Camera"], ["db", "Volume (dB)"], ["link", "Link"]];
  const EX = {name: () => (by.device_name && (by.device_name.value || by.device_name.placeholder)) || "MoveEye", time: () => new Date().toTimeString().slice(0, 5),
    date: () => new Date().toLocaleDateString(LOCALE(LANG)), count: () => "2", camera: () => "USB", db: () => "72", link: () => location.origin + "/"};
  const fill = s => String(s || "").replace(/\{(\w+)\}/g, (m, k) => EX[k] ? EX[k]() : m);
  if (by.device_name) d.appendChild(textField(by.device_name));
  d.appendChild(el("div", "mut msghint", t("Leave a field empty for the standard text. Tap a grey button to insert a placeholder at the cursor.")));
  [["person", "👤", "Person"], ["prealarm", "👀", "Pre-alarm"], ["warm", "🌡", "Thermal alarm"], ["noise", "🔊", "Noise alarm"]].forEach(([k, ic, nm]) => {
    const tx = by["msg_" + k + "_title"], bx = by["msg_" + k + "_text"]; if (!tx || !bx) return;
    const card = el("details", "adv sblk msgcard"); card.dataset.view = "msg:" + k;
    const sm = el("summary", ""), sl = el("span", "", ic + " " + t(nm)), sp = el("span", "mut msgsum"); sm.append(sl, sp); card.appendChild(sm);
    const prev = el("div", "msgprev"), pt = el("b"), pb = el("div"); prev.append(el("span", "mut", t("Preview") + ":"), pt, pb);
    let last = null; const fields = [];
    [[tx, "Title", false], [bx, "Text", true]].forEach(([x, lab, big]) => {
      const inp = el(big ? "textarea" : "input"); if (!big) inp.type = "text"; else inp.rows = 2;
      inp.value = x.value || ""; inp.placeholder = x.placeholder || ""; inp.className = "msginp"; if (big) inp.rows = 3;
      inp.onfocus = () => { last = inp; if (!inp.value && inp.placeholder) { inp.value = inp.placeholder; inp.dataset.std = "1"; } };   // edit the standard text
      inp.onblur = () => { if (inp.dataset.std && inp.value === inp.placeholder) inp.value = ""; delete inp.dataset.std; };
      const err = el("div", "err");
      const save = () => post("/api/text", {key: x.key, value: inp.value === inp.placeholder ? "" : inp.value, lang: LANG}).then(r => { err.textContent = r.ok ? "" : "⚠ " + (r.error || "error"); if (r.ok) toast(t("Saved")); });
      inp.onchange = save; inp.oninput = paint;
      const std = el("button", "sec msgstd", "↺"); std.type = "button"; std.title = t("Standard text");
      std.onclick = () => { inp.value = ""; save(); paint(); };
      const row = el("div", "msgrow"); row.append(el("span", "mut", t(lab)), inp, std);
      card.append(row, err); fields.push(inp);
    });
    const chips = el("div", "msgchips");
    PH.forEach(([p, lab]) => { const c = el("button", "sec", t(lab)); c.type = "button"; c.title = "{" + p + "}";
      c.onmousedown = e => e.preventDefault();
      c.onclick = () => { const f = last || fields[1]; const a = f.selectionStart ?? f.value.length, b = f.selectionEnd ?? a;
        f.value = f.value.slice(0, a) + "{" + p + "}" + f.value.slice(b); f.focus(); f.selectionStart = f.selectionEnd = a + p.length + 2;
        f.dispatchEvent(new Event("change")); paint(); };
      chips.appendChild(c); });
    function paint() { pt.textContent = fill(fields[0].value || fields[0].placeholder); pb.textContent = fill(fields[1].value || fields[1].placeholder);
      sp.textContent = fields[0].value || fields[1].value ? t("own text") : t("standard text"); }
    card.append(chips, prev); d.appendChild(card); paint();
  });
}
// ---- location: automatically from the phone, or tapped on a map ----
Object.assign(I18N.de, {"Location (sunrise / sunset, photos, weather)": "Standort (Sonnenauf-/untergang, Fotos, Wetter)", "Automatically (phone)": "Automatisch (Handy)", "Pick on the map": "Auf Karte wählen", "My position": "Meine Position", "Search a place …": "Ort suchen …", "The phone shares its position only over the https page.": "Das Handy gibt seine Position nur über die https-Seite heraus.", "From the phone": "Vom Handy", "updated": "aktualisiert vor", "Waiting for the position of the phone …": "Warte auf die Position des Handys …", "Until then": "Bis dahin", "No place chosen yet.": "Noch kein Ort gewählt.", "Fixed place": "Fester Ort", "Tap on the map to set the place. Move with one finger, zoom with + / −.": "Auf die Karte tippen, um den Ort zu setzen. Mit einem Finger verschieben, mit + / − zoomen.", "Place not found": "Ort nicht gefunden", "Search needs internet": "Suche braucht Internet", "Map background is switched off in the settings.": "Kartenhintergrund ist in den Einstellungen ausgeschaltet."});
function miniMap(o) {
  const M = {z: 13, cx: 0, cy: 0, mk: null, online: true, pick: null};
  const m = el("div", "lmap"), T = el("div", "mtiles"), pin = el("div", "lpin", "📍"), zb = el("div", "mzoom"), at = el("div", "mattr");
  at.innerHTML = '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';
  const s = z => 256 * Math.pow(2, z);
  const W = (lat, lon, z) => { const r = Math.max(-85, Math.min(85, lat)) * Math.PI / 180; return [(lon + 180) / 360 * s(z), (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * s(z)]; };
  const inv = (x, y, z) => [Math.atan(Math.sinh(Math.PI * (1 - 2 * y / s(z)))) * 180 / Math.PI, x / s(z) * 360 - 180];
  function draw() {
    const w = m.clientWidth, h = m.clientHeight; if (!w) return;
    const z = M.z, N = Math.pow(2, z), x0 = M.cx - w / 2, y0 = M.cy - h / 2, have = {};
    T.querySelectorAll("img").forEach(i => { have[i.dataset.k] = i; });
    if (M.online) for (let ty = Math.floor(y0 / 256); ty <= Math.floor((y0 + h) / 256); ty++) {
      if (ty < 0 || ty >= N) continue;
      for (let tx = Math.floor(x0 / 256); tx <= Math.floor((x0 + w) / 256); tx++) {
        const k = z + "/" + (((tx % N) + N) % N) + "/" + ty, key = k + "@" + tx;
        let im = have[key]; if (!im) { im = el("img"); im.alt = ""; im.dataset.k = key; im.onerror = () => { im.style.visibility = "hidden"; }; im.src = "https://tile.openstreetmap.org/" + k + ".png"; T.appendChild(im); }
        im.style.left = Math.round(tx * 256 - x0) + "px"; im.style.top = Math.round(ty * 256 - y0) + "px"; im.dataset.keep = "1";
      }
    }
    T.querySelectorAll("img").forEach(i => { if (i.dataset.keep) delete i.dataset.keep; else i.remove(); });
    pin.hidden = !M.mk;
    if (M.mk) { const [x, y] = W(M.mk[0], M.mk[1], z); pin.style.left = (x - x0) + "px"; pin.style.top = (y - y0) + "px"; }
  }
  function zoom(dz, px, py) { const w = m.clientWidth, h = m.clientHeight; if (px === undefined) { px = w / 2; py = h / 2; }
    const z2 = Math.max(3, Math.min(18, M.z + dz)); if (z2 === M.z) return; const f = Math.pow(2, z2 - M.z), wx = M.cx - w / 2 + px, wy = M.cy - h / 2 + py;
    M.cx = wx * f - px + w / 2; M.cy = wy * f - py + h / 2; M.z = z2; draw(); }
  [["+", 1], ["−", -1]].forEach(([l, d]) => { const b = el("button", "sec", l); b.type = "button"; b.onpointerdown = e => e.stopPropagation(); b.onclick = e => { e.stopPropagation(); zoom(d); }; zb.appendChild(b); });
  m.append(T, pin, zb, at);
  const act = new Map(); let moved = 0, pinch = 0;
  m.addEventListener("pointerdown", e => { m.setPointerCapture(e.pointerId); act.set(e.pointerId, [e.clientX, e.clientY]); if (act.size === 1) moved = 0;
    if (act.size === 2) { const [a, b] = [...act.values()]; pinch = Math.hypot(a[0] - b[0], a[1] - b[1]); moved = 99; } });
  m.addEventListener("pointermove", e => { if (!act.has(e.pointerId)) return; const o2 = act.get(e.pointerId); act.set(e.pointerId, [e.clientX, e.clientY]);
    if (act.size === 1) { const dx = e.clientX - o2[0], dy = e.clientY - o2[1]; moved += Math.abs(dx) + Math.abs(dy); if (moved > 6) { M.cx -= dx; M.cy -= dy; draw(); } }
    else if (act.size === 2 && pinch) { const [a, b] = [...act.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]), r = m.getBoundingClientRect();
      if (d / pinch > 1.6 || d / pinch < 0.62) { zoom(d > pinch ? 1 : -1, (a[0] + b[0]) / 2 - r.left, (a[1] + b[1]) / 2 - r.top); pinch = d; } } });
  const up = e => { if (!act.has(e.pointerId)) return; act.delete(e.pointerId); if (act.size < 2) pinch = 0;
    if (!act.size && moved <= 6 && M.pick) { const r = m.getBoundingClientRect(), [lat, lon] = inv(M.cx - m.clientWidth / 2 + e.clientX - r.left, M.cy - m.clientHeight / 2 + e.clientY - r.top, M.z);
      M.mk = [lat, lon]; draw(); M.pick(lat, lon); } };
  m.addEventListener("pointerup", up); m.addEventListener("pointercancel", e => { act.delete(e.pointerId); moved = 99; });
  m.addEventListener("wheel", e => { e.preventDefault(); const r = m.getBoundingClientRect(); zoom(e.deltaY < 0 ? 1 : -1, e.clientX - r.left, e.clientY - r.top); }, {passive: false});
  if (window.ResizeObserver) new ResizeObserver(draw).observe(m);
  return {el: m, M: M, draw: draw,
    show(lat, lon, z) { if (z) M.z = z; [M.cx, M.cy] = W(lat, lon, M.z); M.mk = [lat, lon]; draw(); },
    mark(lat, lon) { M.mk = [lat, lon]; draw(); }};
}
function locBox() {
  const box = el("div", "sl locbox"), top = el("div", "row"); top.appendChild(el("span", "", "📍 " + t("Location (sunrise / sunset, photos, weather)"))); box.appendChild(top);
  const seg = el("div", "seg lseg"), bA = el("button", "", "📱 " + t("Automatically (phone)")), bM = el("button", "", "🗺 " + t("Pick on the map"));
  bA.type = bM.type = "button"; seg.append(bA, bM);
  const info = el("div", "mut linfo"), tools = el("div", "row ltools"), q = el("input"), go = el("button", "sec", "🔍"), me = el("button", "sec", "◎ " + t("My position"));
  q.type = "text"; q.enterKeyHint = "search"; q.className = "lq"; q.placeholder = t("Search a place …"); go.type = me.type = "button"; tools.append(q, go, me);
  const mp = miniMap(), hint = el("div", "mut lhint"), err = el("div", "err");
  box.append(seg, info, tools, mp.el, hint, err);
  let G = null, mode = "auto";
  const save = async (lat, lon) => {
    lat = Math.max(-66, Math.min(66, lat)); lon = ((lon + 540) % 360) - 180;
    const a = await post("/api/text", {key: "latitude", value: lat.toFixed(4), lang: LANG}), b = await post("/api/text", {key: "longitude", value: lon.toFixed(4), lang: LANG});
    err.textContent = a.ok && b.ok ? "" : "⚠ " + (a.error || b.error || "error"); if (a.ok && b.ok) { toast("📍 " + t("Saved")); refresh(false); } };
  const geo = then => { if (!window.isSecureContext || !navigator.geolocation) { err.textContent = "⚠ " + t("The phone shares its position only over the https page."); return; }
    navigator.geolocation.getCurrentPosition(p => then(p.coords), e => { err.textContent = "⚠ " + (e.message || "GPS"); }, {enableHighAccuracy: true, timeout: 20000, maximumAge: 60000}); };
  function paint() {
    bA.className = mode === "auto" ? "sel-auto" : ""; bM.className = mode === "map" ? "sel-auto" : "";
    tools.hidden = mode !== "map"; me.hidden = !window.isSecureContext;
    mp.M.pick = mode === "map" ? save : null; mp.el.classList.toggle("pick", mode === "map");
    if (!G) return;
    const g = G.gps;
    if (mode === "auto") {
      if (g && g.src === "module") info.textContent = "🛰️ " + t("From the GPS module") + ": " + g.lat.toFixed(4) + ", " + g.lon.toFixed(4);
      else if (g && g.src === "phone") info.textContent = t("From the phone") + ": " + g.lat.toFixed(4) + ", " + g.lon.toFixed(4) + (g.age != null ? " · " + t("updated") + " " + Math.round(g.age / 60) + " min" : "");
      else info.textContent = (window.isSecureContext ? t("Waiting for the position of the phone …") : t("The phone shares its position only over the https page."))
        + (G.factory ? "" : " " + t("Until then") + ": " + G.lat.toFixed(4) + ", " + G.lon.toFixed(4));
      hint.textContent = "";
    } else { info.textContent = G.factory ? t("No place chosen yet.") : t("Fixed place") + ": " + G.lat.toFixed(4) + ", " + G.lon.toFixed(4);
      hint.textContent = t("Tap on the map to set the place. Move with one finger, zoom with + / −."); }
    mp.M.online = G.map_online;
  }
  async function refresh(center) {
    try { G = await (await fetch("/api/gps", {cache: "no-store"})).json(); } catch (e) { return; }
    mode = G.on ? "auto" : "map"; paint();
    const g = G.gps, lat = g ? g.lat : G.lat, lon = g ? g.lon : G.lon;
    if (center) mp.show(lat, lon, G.factory && !g ? 7 : 13); else mp.mark(lat, lon);
  }
  bA.onclick = async () => { await post("/api/set", {key: "gps_phone", value: true}); mode = "auto"; paint();
    geo(c => post("/api/gps", {lat: c.latitude, lon: c.longitude, acc: c.accuracy}).then(() => refresh(true))); refresh(true); };
  bM.onclick = async () => { await post("/api/set", {key: "gps_phone", value: false}); mode = "map"; paint(); refresh(false); };
  me.onclick = () => geo(c => { mp.show(c.latitude, c.longitude, 15); save(c.latitude, c.longitude); });
  const search = async () => { const s = q.value.trim(); if (!s) return; err.textContent = "";
    if (G && !G.map_online) { err.textContent = "⚠ " + t("Map background is switched off in the settings."); return; }
    try { const r = await (await fetch("https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&accept-language=" + LANG + "&q=" + encodeURIComponent(s))).json();
      if (!r.length) { err.textContent = "⚠ " + t("Place not found"); return; }
      mp.show(+r[0].lat, +r[0].lon, 14); save(+r[0].lat, +r[0].lon);
    } catch (e) { err.textContent = "⚠ " + t("Search needs internet"); } };
  go.onclick = search; q.onkeydown = e => { if (e.key === "Enter") { e.preventDefault(); search(); } };
  setTimeout(() => refresh(true), 0);
  setInterval(() => { if (box.offsetParent) refresh(false); }, 20000);
  return box;
}
function schedBox(s, i) {
  const box = el("div", "rel-ed"); box.style.gridTemplateColumns = "1fr";
  const cur = JSON.parse(JSON.stringify(s));          // working copy that the controls edit and send
  const save = () => schedPost({action: "save", index: i, schedule: cur});
  const r1 = el("div", "row"); r1.style.gap = "6px";
  const name = el("input"); name.type = "text"; name.value = s.name; name.style.flex = "1"; name.style.minWidth = "0";
  name.onchange = () => { cur.name = name.value; save(); };
  const act = el("span", "badge grn", t("active now")); act.id = "sc-act-" + i; act.hidden = true;
  const en = el("input"); en.type = "checkbox"; en.className = "sw"; en.checked = s.enabled; en.title = t("Enabled");
  en.onchange = () => { cur.enabled = en.checked; save(); };
  const del = el("button", "sec", "✕"); del.title = t("Remove"); del.style.padding = "4px 9px";
  del.onclick = () => { if (confirm(t("Remove this schedule?"))) schedPost({action: "remove", index: i}); };
  r1.append(name, act, en, del);
  const days = el("div", "days");
  DAYS().forEach((d, k) => {
    const b = el("button", cur.days.includes(k) ? "on" : "", d);
    b.onclick = () => {
      const on = !cur.days.includes(k);
      cur.days = on ? cur.days.concat([k]).sort() : cur.days.filter(x => x !== k);
      b.classList.toggle("on", on); save();
    };
    days.appendChild(b);
  });
  const times = el("div", "row"); times.style.justifyContent = "flex-start"; times.style.gap = "14px";
  [["start", "From"], ["end", "To"]].forEach(([key, label]) => {
    const w = el("label", "mut"), inp = el("input"); inp.type = "time"; inp.value = s[key];
    inp.onchange = () => { if (inp.value) { cur[key] = inp.value; save(); } };
    w.append(el("span", "", t(label) + " "), inp); times.appendChild(w);
  });
  const feats = el("div");
  FEAT.forEach(f => {
    const row = el("label", "row"); row.style.padding = "2px 0"; row.appendChild(el("span", "", f.label));
    const sel = el("select"); sel.style.width = "auto";
    [["", t("unchanged")], ["on", t("ON")], ["off", t("OFF")]].forEach(([v, l]) => { const o = el("option", "", l); o.value = v; sel.appendChild(o); });
    sel.value = f.key in cur.actions ? (cur.actions[f.key] ? "on" : "off") : "";
    sel.onchange = () => { if (sel.value === "") delete cur.actions[f.key]; else cur.actions[f.key] = sel.value === "on"; save(); };
    row.appendChild(sel); feats.appendChild(row);
  });
  const adv = el("div"); adv.style.cssText = "display:grid;gap:6px;margin:8px 0";
  const mk = (label, node) => { const w = el("label", "mut"); w.append(el("div", "", t(label)), node); return w; };
  const mkSel = (opts, val, fn) => { const sl = el("select"); sl.style.width = "100%"; opts.forEach(([v, l]) => { const o = el("option", "", l); o.value = v; sl.appendChild(o); }); sl.value = val; sl.onchange = () => fn(sl.value); return sl; };
  const off = el("input"); off.type = "number"; off.min = -180; off.max = 180; off.step = 5; off.value = cur.sun_offset || 0; off.style.width = "100px";
  const offw = mk("Shift (minutes)", off);
  const sync = () => { times.querySelectorAll("input").forEach(x => { x.disabled = !!cur.sun; }); offw.style.display = cur.sun ? "" : "none"; };
  off.onchange = () => { cur.sun_offset = parseInt(off.value, 10) || 0; save(); };
  const skip = el("input"); skip.type = "text"; skip.placeholder = "2026-12-24..2026-12-26, 08-01"; skip.value = cur.skip || ""; skip.style.width = "100%";
  skip.onchange = () => { cur.skip = skip.value; save(); };
  adv.append(mk("Time window", mkSel([["", t("Fixed times")], ["dark", t("Sunset → sunrise")], ["light", t("Sunrise → sunset")]], cur.sun || "", v => { cur.sun = v; sync(); save(); })), offw,
             mk("Applies", mkSel([["", t("Always")], ["away", t("Only when nobody is home")], ["home", t("Only when somebody is home")]], cur.presence || "", v => { cur.presence = v; save(); })),
             mk("Skip dates (YYYY-MM-DD, ranges with .., MM-DD every year)", skip));
  sync();
  box.append(r1, days, times, adv, feats);
  return box;
}
function renderSchedules(list, st) {
  const L = $("#sched-list"), sig = JSON.stringify([list, FEAT.length, LANG]);
  if (sig !== sigC && !L.contains(document.activeElement)) {
    sigC = sig; L.textContent = "";
    if (!list.length) L.appendChild(el("span", "mut", t("no schedules")));
    list.forEach((s, i) => L.appendChild(schedBox(s, i)));
  }
  const act = st.sched_active_idx || [];
  list.forEach((s, i) => { const b = $("#sc-act-" + i); if (b) b.hidden = !act.includes(i); });
}

// ---- settings in 9 groups. Rule: inside a group every topic is a sub-section that opens / closes the same way
//      (the first one is open). Fine-tuning comes last, under a small "Fine-tuning" line. A group with one topic shows it directly.
const MWIC = {   // 2.95.70: plain line symbols for the emoji of the settings (key: the emoji without U+FE0F)
  "🛡": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>', "🔘": '<rect x="2" y="7" width="20" height="10" rx="5"/><circle cx="16" cy="12" r="3"/>',
  "🏕": '<path d="M3 20L12 5l9 15zM9 20l3-5 3 5"/>', "🍃": '<path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14z"/><path d="M5 19l8-8"/>',
  "🔋": '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 10v4M6 10v4M10 10v4"/>', "🔒": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  "🔔": '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>', "📲": '<rect x="9" y="2" width="10" height="20" rx="2"/><path d="M13 18h2M2 9h5M5 7l2 2-2 2"/>',
  "🌙": '<path d="M20 14A8 8 0 1 1 10 4a6 6 0 0 0 10 10z"/>', "💬": '<path d="M4 5h16v11H9l-5 4z"/>', "📱": '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
  "🎯": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>', "👁": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  "🤖": '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M12 4v4M9 13h.01M15 13h.01M9 17h6"/>', "🚶": '<circle cx="13" cy="4" r="2"/><path d="M11 21l2-6-3-3 1-5 3 3 3 1M10 12l-2 3"/>',
  "🚗": '<path d="M3 16v-4l2-5h14l2 5v4z"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>', "🌧": '<path d="M6 14a4 4 0 0 1 1-8 6 6 0 0 1 11 2 3 3 0 0 1 0 6z"/><path d="M8 18v2M12 18v3M16 18v2"/>',
  "🌬": '<path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h8"/>', "🌘": '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/>',
  "🎚": '<path d="M6 4v16M12 4v16M18 4v16M4 8h4M10 15h4M16 10h4"/>', "📷": '<path d="M3 8h4l2-3h6l2 3h4v11H3z"/><circle cx="12" cy="13" r="4"/>',
  "🕹": '<circle cx="12" cy="6" r="3"/><path d="M12 9v7M5 16h14v4H5z"/>', "🔄": '<path d="M20 12a8 8 0 1 1-2.3-5.7L20 8M20 3v5h-5"/>',
  "🎥": '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3"/>', "🚜": '<rect x="2" y="13" width="20" height="7" rx="3.5"/><circle cx="7" cy="16.5" r="1.5"/><circle cx="12" cy="16.5" r="1.5"/><circle cx="17" cy="16.5" r="1.5"/><path d="M7 13V8h9v5"/>',
  "🔌": '<path d="M9 2v5M15 2v5M6 7h12v4a6 6 0 0 1-12 0zM12 17v5"/>', "🌡": '<path d="M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0z"/>',
  "📡": '<path d="M4 10a8 8 0 0 1 16 0M7 10a5 5 0 0 1 10 0"/><circle cx="12" cy="10" r="1.5"/><path d="M12 12v9M8 21h8"/>', "⛈": '<path d="M6 14a4 4 0 0 1 1-8 6 6 0 0 1 11 2 3 3 0 0 1 0 6"/><path d="M13 12l-3 5h4l-2 4"/>',
  "🛰": '<path d="M12 7l5 5-5 5-5-5z"/><path d="M4 4l4.5 4.5M15.5 15.5L20 20M3 14a7 7 0 0 0 7 7"/>', "☀": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5"/>',
  "💡": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z"/>', "📢": '<path d="M3 10v4h4l9 5V5L7 10z"/><path d="M19 9a4 4 0 0 1 0 6"/>',
  "🎤": '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v4"/>', "🔊": '<path d="M4 9v6h4l5 4V5L8 9z"/><path d="M16 9a4 4 0 0 1 0 6M19 6a8 8 0 0 1 0 12"/>',
  "👏": '<path d="M7 11l4-4a2 2 0 0 1 3 3l-1 1M10 14l5-5a2 2 0 0 1 3 3l-6 6a5 5 0 0 1-7-7l2-2M17 3l1-1M20 6l1-1"/>', "🤧": '<circle cx="12" cy="12" r="9"/><path d="M8 10h2M14 10h2M9 15a4 4 0 0 0 6 0"/>',
  "🎬": '<rect x="3" y="9" width="18" height="11" rx="1"/><path d="M3 9l2-5h16l-2 5M8 4l-2 5M13 4l-2 5M18 4l-2 5"/>', "⏺": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4" fill="currentColor"/>',
  "⏱": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M10 2h4M12 2v3"/>', "☁": '<path d="M6 18a4 4 0 0 1 1-8 6 6 0 0 1 11 2 3 3 0 0 1 0 6z"/>',
  "⚡": '<path d="M13 3L4 14h7l-1 7 9-11h-7z"/>', "🗓": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  "⚙": '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="7"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/>',
  "🖥": '<rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>', "📶": '<path d="M2 9.5a15 15 0 0 1 20 0M5 13a10 10 0 0 1 14 0M8.5 16.5a5 5 0 0 1 7 0"/><circle cx="12" cy="20" r="1"/>',
  "👥": '<circle cx="9" cy="8" r="3.5"/><path d="M2 20a7 7 0 0 1 14 0M16 4.5a3.5 3.5 0 0 1 0 7M18 13a6 6 0 0 1 4 7"/>', "📍": '<path d="M12 22s7-7 7-12a7 7 0 0 0-14 0c0 5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
  "🏠": '<path d="M3 11l9-7 9 7v10H3z"/><path d="M10 21v-6h4v6"/>', "🧪": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3M7.5 15h9"/>',
  "⬆": '<path d="M12 20V5M6 11l6-6 6 6"/>', "📜": '<path d="M6 3h12v18H6z"/><path d="M9 8h6M9 12h6M9 16h4"/>'};
function icSpan(e) {                                         // symbol of a settings topic: emoji + plain symbol + green dot (CSS picks)
  const s = el("span", "gi"); if (!e) return s; s.appendChild(el("span", "ie", e));
  const k = String(e).replace(/\uFE0F/g, ""); if (MWIC[k]) s.insertAdjacentHTML("beforeend", '<svg class="is" viewBox="0 0 24 24" aria-hidden="true">' + MWIC[k] + "</svg>");
  s.appendChild(el("i", "gdot")); return s;
}
try { document.body.classList.toggle("icplain", localStorage.getItem("mw-icons") === "plain"); } catch (e) {}
const GROUPS = [                                            // 2.98.0: by goal - tab «Schutz» (protect) and tab «Einstellungen» (settings)
  {id: "alarm", tab: "protect", icon: "🛡", name: "Protection", open: true,
   items: [{card: "protect", title: "Protection level", ic: "🛡"}, {sec: "Camping / protection", title: "Arming and own Wi-Fi", ic: "🏕️"}]},
  {id: "notify", tab: "protect", icon: "🚨", name: "What happens at an alarm?", items: [{sec: "Notifications", title: "Push messages", ic: "📲"},
   {sec: "Deterrence", title: "Deterrence", ic: "📢"}, {sec: "Recording", ic: "⏺"}, {sec: "Messages", ic: "💬"}, {sec: "SMS (LTE stick)", title: "SMS (LTE stick)", ic: "📱"},
   {card: "report", sec: "Night report", title: "Night report", ic: "🌙"}]},
  {id: "theft", tab: "protect", icon: "🔒", name: "Theft protection", items: [{sec: "Theft protection", title: "Device", ic: "🔒"},
   {sec: "Reference scan", title: "Guarded things (reference scan)", ic: "🧭"}, {sec: "Backup", title: "Backup (pictures off the device)", ic: "☁️"}]},
  {id: "sched", tab: "protect", icon: "🗓", name: "Zones, schedule, presence", items: [{card: "schedule", sec: "Schedule", title: "Schedule", ic: "🗓️"}]},
  {id: "detect", tab: "settings", icon: "🎯", name: "Detection", items: [{card: "tune", title: "Improve detection", ic: "🎯"}, {sec: "Detection", ic: "👁️"}, {sec: "AI detection", ic: "🤖"}, {sec: "Thermal camera", ic: "🌡"}, {fine: true},
   {sec: "Walking recognition", ic: "🚶"}, {sec: "Vehicle filter", ic: "🚗"}, {sec: "Rain", ic: "🌧️"}, {sec: "Wind", ic: "🌬️"}, {sec: "Low light", ic: "🌘"}, {sec: "Auto-tune", ic: "🎚️"}]},
  {id: "camera", tab: "settings", icon: "📷", name: "Cameras & head", items: [{sec: "Camera / Servos", ic: "🕹️"}, {sec: "Patrol", ic: "🔄"}, {sec: "Automatic head movement", ic: "🤖"}, {card: "source", sec: "Video source", ic: "🎥"},
   {sec: "Timelapse", ic: "⏱️"}, {sec: "Mover", title: "Mover (tracked vehicle)", ic: "🚜"}, {fine: true}, {sec: "Servo driver", ic: "🔌"}]},
  {id: "lightsound", tab: "settings", icon: "🔌", name: "Devices & sensors", items: [{sec: "Lights", ic: "💡"}, {sec: "Microphone", ic: "🎤"}, {sec: "Loudspeaker", ic: "🔊"},
   {card: "relayset", sec: "Relays", title: "Relays", ic: "⚡"}, {sec: "Extra sensors", ic: "📡"}, {sec: "Clap switch", ic: "👏"}, {sec: "Bless you", title: "«Bless you!»", ic: "🤧"},
   {sec: "Wake-up alarm", ic: "⏰"}, {sec: "Storm warning", ic: "⛈️"}, {sec: "GPS module", ic: "🛰️"}]},
  {id: "power", tab: "settings", icon: "🔋", name: "Power supply", items: [{card: "batt", sec: "Battery", title: "Battery", ic: "🔋"}, {sec: "Power saving", ic: "🍃"}, {sec: "Solar panel", ic: "☀️"}]},
  {id: "net", tab: "settings", icon: "📶", name: "Network & access", items: [{card: "wifi", sec: "Wi-Fi / hotspot", ic: "📶"}, {sec: "Web stream", ic: "📡"},
   {card: "guest", title: "Guest access", ic: "👥"}, {sec: "MQTT / Home Assistant", title: "MQTT / Home Assistant", ic: "🏠"}]},
  {id: "security", tab: "settings", icon: "🔐", name: "Security", items: [{sec: "Security", ic: "🔐"}]},   // 573: password, users, app keys, check
  {id: "sys", tab: "settings", icon: "⚙", name: "System", items: [{card: "system", ic: "🖥️"}, {sec: "Setup", ic: "📍"}, {sec: "Updates", ic: "⬆️"},
   {card: "log", ic: "📜"}]},
];
Object.assign(I18N.de, {"Improve detection": "Erkennung verbessern", "Automatic head movement": "Automatische Kopfbewegung",
  "paused (the head is busy)": "Pause (der Kopf ist beschäftigt)", "saving: stays at the most important direction": "sparsam: bleibt bei der wichtigsten Richtung"});   // 2.98.14: the assistant (312); the simulator settings are on the page Simulator
function toBlock(d) {                                        // a settings section -> its controls (without its own title)
  const b = el("div", "blk");
  [...d.children].filter(c => c.tagName !== "SUMMARY").forEach(k => b.appendChild(k));
  d.remove();
  return b.children.length ? b : null;
}
function regroup() {
  const box = $("#settings"), aside = box.parentNode, used = new Set();
  const byView = v => document.querySelector('details[data-view="' + v + '"]');
  const frag = document.createDocumentFragment();
  const make = (g, it) => {                                  // one topic = card and / or settings section in one sub-section
    const card = it.card ? byView(it.card) : null, sd = it.sec ? byView("sec:" + it.sec) : null;
    if (it.card) used.add(it.card); if (it.sec) used.add("sec:" + it.sec);
    if (!card && !sd) return null;
    const title = it.title ? t(it.title) : (card ? card.querySelector("summary").textContent : sd.querySelector("summary").textContent);
    const S = el("details", "sub"); S.dataset.view = card ? card.dataset.view : "sec:" + it.sec;
    S.dataset.vgroup = "Panels"; S.dataset.vlabel = title;
    if (card && card.id) { S.id = card.id; card.removeAttribute("id"); }
    const sum = el("summary"); if (it.ic) sum.appendChild(icSpan(it.ic)); sum.appendChild(el("span", "sn", title)); S.appendChild(sum);
    if (card) { [...card.children].filter(c => c.tagName !== "SUMMARY").forEach(k => S.appendChild(k)); card.remove(); }
    if (sd) { const b = toBlock(sd); if (b) S.appendChild(b); }
    return S.children.length > 1 ? S : null;
  };
  GROUPS.forEach(g => {
    const G = el("details", "card grp"); G.dataset.view = "grp:" + g.id; G.dataset.vgroup = "Panels"; G.dataset.vlabel = g.name;
    G.dataset.tabOf = g.tab || "settings";
    if (g.open) G.open = true;
    const sm = el("summary"); sm.append(icSpan(g.icon), el("span", "gn", t(g.name))); G.appendChild(sm);
    const subs = [];
    g.items.forEach(it => { if (it.fine) subs.push("fine"); else { const S = make(g, it); if (S) subs.push(S); } });
    const real = subs.filter(x => x !== "fine");
    if (real.length === 1) G.dataset.main = real[0].dataset.view;   // the group shows the switch of its only topic
    if (real.length === 1) {                                 // only one topic: show it directly
      [...real[0].children].filter(c => c.tagName !== "SUMMARY").forEach(k => G.appendChild(k));
    } else {
      let first = true;
      subs.forEach((S, i) => {
        if (S === "fine") { if (subs.slice(i + 1).some(x => x !== "fine")) G.appendChild(el("div", "fine", t("Fine-tuning"))); return; }
        if (first) { S.open = true; first = false; }
        G.appendChild(S);
      });
    }
    if (G.children.length > 1) frag.appendChild(G);
  });
  // anything not listed (e.g. a section added in a later version) ends up as a sub-section of System
  const sys = frag.querySelector('[data-view="grp:sys"]');
  [...box.querySelectorAll(':scope > details[data-view^="sec:"]')].filter(d => !used.has(d.dataset.view)).forEach(d => {
    const S = el("details", "sub"); S.dataset.view = d.dataset.view; S.appendChild(el("summary", "", d.querySelector("summary").textContent));
    const b = toBlock(d); if (b) { S.appendChild(b); sys.appendChild(S); }
  });
  box.textContent = ""; box.appendChild(frag);
  setTimeout(() => { const sb = $("#srch"); if (sb && box.parentNode) box.parentNode.insertBefore(sb, box);
    const lb = $("#lock-bar"); if (lb && box.parentNode) box.parentNode.insertBefore(lb, sb || box);
    const si = $("#srch-in"); if (si) si.placeholder = t(sb && sb.classList.contains("withall") ? "Search settings …" : "Search settings … (e.g. password)"); }, 0);
  const ab = $("#allbtns");                                 // right under "expand / collapse all" (computer)
  aside.insertBefore(box, ab && ab.parentNode === aside ? ab.nextSibling : aside.firstChild);
  // Off / On / Auto of the lights and the relays: in their settings topics (the live page has the quick switches)
  const put = (blk, view) => { const d = document.querySelector('#settings [data-view="' + view + '"]'); if (!blk || !d) return;
    const sm = d.querySelector(":scope > summary"); d.insertBefore(blk, sm ? sm.nextSibling : d.firstChild); };
  put($("#lights-box"), "sec:Lights"); put($("#relays-box"), "relayset");
  tabsArrange();
}
// 2.98.0: the switches of the old catch-all «Alarm & Camping › Schalter» go where they belong (power, network, system);
// the protection tab gets the alarm chain on top, the zones as a link; the simulator tile goes to the live picture
function tabsArrange() {
  const row = id => { const e = $(id); return e ? (e.closest("label") || e.closest(".pr-sw") || e) : null; };
  const into = (gid, nodes) => { const G = document.querySelector('#settings [data-view="grp:' + gid + '"]'); if (!G) return;
    const box = el("div", "blk"); nodes.filter(Boolean).forEach(n => box.appendChild(n)); if (!box.children.length) return;
    const sm = G.querySelector(":scope > summary"); G.insertBefore(box, sm ? sm.nextSibling : G.firstChild); };
  into("power", [row("#pr-eco"), row("#pr-turbo")]);
  into("net", [row("#pr-hs"), $("#pr-teth") ? $("#pr-teth").closest(".pr-sw") : null, $("#pr-net") ? $("#pr-net").closest(".pr-sw") : null]);
  into("sys", [row("#pr-as")]);
  const sc = document.querySelector('#settings [data-view="grp:sched"]');
  if (sc) { const a = el("a", "btn sec", "🗺 " + t("Draw the zones") + " ›"); a.href = "/zones"; a.style.cssText = "display:block;margin:6px 0 10px";
    const sm = sc.querySelector(":scope > summary"); sc.insertBefore(a, sm ? sm.nextSibling : sc.firstChild); }
  const box = $("#settings");
  if (box && !$("#alarm-chain")) { const c = el("div", "card"); c.id = "alarm-chain"; box.parentNode.insertBefore(c, box); }
  const sbar = $("#simplebar"); if (sbar && box) box.parentNode.insertBefore(sbar, box);     // Simple / Expert on top, not 3800 px down
  setTimeout(() => { const sb = $("#srch"), bar = $("#simplebar"); if (sb && bar) sb.after(bar);      // 2.98.3: search first, then the small line
    if (bar) { const sg = bar.querySelector(":scope > .seg"); if (sg) sg.title = t("Simple: only the important settings. «Expert» shows all of them.");
      const ic = bar.querySelector(".icseg .seg"); if (ic) ic.title = t("Symbols: green dot or green symbol = switched on"); } }, 0);
  const tile = $("#simtile"), sec = document.querySelector("main>section");
  if (tile && sec) sec.appendChild(tile);
}
// open a group / topic of the settings - on its own tab (another tab: go there, ?open= opens it after loading)
function tabOpen(v) {
  const d = document.querySelector('#settings [data-view="' + v + '"]'); if (!d) return;
  const g = d.closest(".grp") || d, tab = g.dataset.tabOf || "settings";
  if (tab !== document.body.dataset.tab) { location.href = "/" + tab + "?open=" + encodeURIComponent(v); return; }
  d.open = true; g.open = true; setTimeout(() => d.scrollIntoView({behavior: "smooth", block: "start"}), 50);
}
setTimeout(() => { const v = new URLSearchParams(location.search).get("open"); if (v) tabOpen(v); }, 1500);
// the alarm chain: person -> push -> light -> recording -> siren (after the wait); tap = its settings
function chainPaint(c, s) {
  const box = $("#alarm-chain"); if (!box || document.body.dataset.tab !== "protect") return;
  const lv = (s.protect_level || c.protect_level || "watch"), armed = s.arm_state === "armed" || s.arm_state === "arming";
  const siren = c.siren_on !== "off" && (c.escalate_on || c.siren_on !== "off");
  const key = [armed, lv, c.notify_on, c.light_white_auto, c.record, c.siren_on, c.escalate_on, c.escalate_siren_s, LANG].join("|");
  if (box.dataset.k === key) return; box.dataset.k = key; box.textContent = "";
  box.appendChild(el("h3", "", "🚨 " + t("What happens at an alarm?"))).style.margin = "0 0 6px";
  const ch = el("div", "chain");
  const go = v => () => tabOpen(v);
  const step = (on, txt, v) => { const b = el("button", "sec" + (on ? "" : " off"), txt); b.type = "button"; b.onclick = go(v); ch.appendChild(b); };
  const ar = () => ch.appendChild(el("em", "", "→"));
  step(true, "🚶 " + t("Person"), "grp:detect"); ar();
  step(!!c.notify_on, "📲 " + t("Push"), "sec:Notifications"); ar();
  step(c.light_white_auto && c.light_white_auto !== "off", "💡 " + t("Light"), "sec:Lights"); ar();
  step(!!c.record, "⏺ " + t("Recording"), "sec:Recording"); ar();
  step(siren, "🚨 " + (c.escalate_on ? t("Siren after {s} s").replace("{s}", c.escalate_siren_s || 30) : t("Siren")), "sec:Deterrence");
  box.appendChild(ch);
  box.appendChild(el("div", "mut", armed ? t("Crossed out = off. Tap a step to change it. «Test protection» plays the chain.") : t("Protection is off - nothing happens. Choose «Wachsam» or «Voll» above.")));
}

// ---- feedback to the developer (anonymous) ----
function fbDialog() {
  let ov = $("#fb-ov"); if (ov) ov.remove();
  ov = el("div"); ov.id = "fb-ov"; ov.style.cssText = "position:fixed;inset:0;z-index:210;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;padding:14px";
  const c = el("div", "card"); c.style.cssText = "max-width:460px;width:100%;max-height:92vh;overflow:auto"; ov.appendChild(c); document.body.appendChild(ov);
  c.append(el("h3", "", "💬 " + t("Feedback to the developer")), el("div", "mut", t("Ideas, errors, praise - everything helps. The message is sent anonymously: no name, no address, unless you write one.")));
  const kind = el("select"); [["idea", "💡 Idea"], ["bug", "🐞 Error"], ["praise", "⭐ Praise"], ["other", "💬 Other"]].forEach(([v, l]) => { const o = el("option", "", t(l)); o.value = v; kind.appendChild(o); });
  kind.style.cssText = "width:100%;margin:10px 0 8px";
  const tx = el("textarea"); tx.rows = 6; tx.maxLength = 3000; tx.placeholder = t("Your message …");
  tx.style.cssText = "width:100%;box-sizing:border-box;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:10px;font:inherit";
  const ct = el("input"); ct.type = "text"; ct.maxLength = 120; ct.placeholder = t("Contact for an answer (optional)"); ct.style.cssText = "width:100%;margin-top:8px";
  const dl = el("label", "row"); const dg = el("input"); dg.type = "checkbox"; dg.checked = true; dl.style.cssText = "justify-content:flex-start;gap:8px;margin-top:8px";
  dl.append(dg, el("span", "mut", t("Add technical details (version, device, last important events - no pictures, no passwords)")));
  const st = el("div", "err"), bt = el("div", "btns"), send = el("button", "", t("Send")), cancel = el("button", "sec", t("Cancel"));
  send.type = cancel.type = "button"; cancel.onclick = () => ov.remove();
  send.onclick = async () => { send.disabled = true; const r = await post("/api/feedback", {kind: kind.value, text: tx.value, contact: ct.value, diag: dg.checked, lang: LANG});
    send.disabled = false; if (!r.ok) { st.textContent = "⚠ " + (r.error || "error"); return; } ov.remove(); toast("✓ " + t("Thank you! The message is on its way.")); };
  bt.append(cancel, send); c.append(kind, tx, ct, dl, st, bt); tx.focus();
}
// ---- quick switches below the joystick: thermal overlay, marks, lights, tracking, patrol, recording, photo ----
const QS = [
  {id: "therm", ic: "🌡", lb: "Thermal", tip: "Thermal picture over the live picture", on: (c, s) => c.thermal_on, ok: (c, s) => !!c.thermal_source,
   go: c => post("/api/set", {key: "thermal_on", value: !c.thermal_on})},
  {id: "nv", ic: "🌙", lb: "Night vision", tip: "Night vision: green picture, thermal outlines and temperatures", on: (c, s) => !!s.nightvision,
   go: c => post("/api/set", {key: "nightvision", value: !c.nightvision})},
  {id: "marks", ic: "🏷", lb: "Marks", tip: "Mark detected objects (animals, cars ...)", on: c => c.show_objects, go: c => post("/api/set", {key: "show_objects", value: !c.show_objects})},
  {id: "mask", ic: "▒", lb: "Mask", tip: "Motion mask over the picture: red = what the detection sees as movement", on: c => c.show_mask,
   ok: c => c.detection_on !== false, go: c => post("/api/set", {key: "show_mask", value: !c.show_mask})},
  {id: "white", ic: "💡", lb: "Lamp", tip: "White light on / off", on: (c, s) => !!(s.lights && s.lights.white), ok: (c, s) => !!(s.light_cfg && s.light_cfg.white_out),
   go: (c, s) => post("/api/light", {light: "white", mode: (s.lights && s.lights.white) ? "off" : "on"})},
  {id: "ir", ic: "🔴", lb: "IR light", tip: "Infrared light on / off", on: (c, s) => !!(s.lights && s.lights.ir), ok: (c, s) => !!(s.light_cfg && s.light_cfg.ir_out),
   go: (c, s) => post("/api/light", {light: "ir", mode: (s.lights && s.lights.ir) ? "off" : "on"})},
  {id: "listen", ic: "🎧", lb: "Listen", tip: "Listen to the microphone", on: () => typeof AU !== "undefined" && AU.on, ok: () => !!window.LISTEN_CAN || (typeof AU !== "undefined" && AU.on),
   go: () => { listenToggle(); return Promise.resolve({ok: true}); }},
  {id: "talk", ic: "🎙", lb: "Talk", tip: "Talk through the loudspeaker: tap once to unlock, then hold the button while you talk",
   on: () => false, ok: (c, s) => !!(s.audio && s.audio.spk) || TK.on, talk: true},
  {id: "sim", ic: "🧪", lb: "Simulation", tip: "Simulation on / off: cameras, thermal camera and sensors from the simulation program", on: (c, s) => !!(s.sim && s.sim.on && s.sim.ok && s.sim.pic !== false),   /* 2.95.93: lit only with a real connection */
   go: (c, s) => mwSimSet(!(s.sim && s.sim.on), LANG)},
  {id: "track", ic: "🎯", lb: "Follow", tip: "Keep what is detected in the middle: persons, animals, moving things", on: c => c.track_person || c.track_motion,
   go: c => post("/api/follow", {on: !(c.track_person || c.track_motion)})},
  {id: "patrol", ic: "🔄", lb: "Patrol", tip: "Patrol: tap = off → back and forth (1-2-3-2-1) → round trip (1-2-3-1) → off", on: c => c.patrol,
   lbf: c => !c.patrol ? "Patrol" : c.patrol_mode === "loop" ? "↻ Round" : "⇄ Pendulum",
   icf: c => c.patrol && c.patrol_mode === "loop" ? "🔁" : "🔄", go: c => post("/api/quick", {action: "patrol"})},
  {id: "rec", ic: "⏺", lb: "Record", tip: "Record now (max. 10 min) / stop", on: (c, s) => s.quick_rec, cls: "rec", go: () => post("/api/quick", {action: "rec"})},
  {id: "photo", ic: "📷", lb: "Photo", tip: "Photo into the recordings", on: () => false, go: () => post("/api/quick", {action: "photo"}), flash: true},
  {id: "kino", ic: "🎬", lb: "Cinema", tip: "Full screen for TV / projector: live picture, clock and the last events", on: () => false,     // 2.96.12: from the tool row
   go: () => { location.href = "/kino"; return Promise.resolve({ok: true}); }},
  {id: "games", ic: "🎮", lb: "Games", tip: "All games for the phones: game corner, game collection and the simulator game - one QR code", on: (c, s) => !!(s.games && s.games.on),   // 2.98.7
   lbf: (c, s) => s.games && s.games.on ? "🟢 " + s.games.n : "Games",
   go: async (c, s) => { if (s.games && s.games.on) { if (!confirm(t("Close all games? The players are logged out."))) return {ok: true}; return post("/api/party", {action: "close"}); }
     const r = await post("/api/party", {action: "all", hours: 6}); if (r && r.ok) location.href = "/party"; return r; }},
  {id: "demo", ic: "▶", lb: "Demo", tip: "3 minutes demonstration with the simulator (in the cinema mode)", on: () => false, ok: (c, s) => !!(s.sim && s.sim.on),
   go: () => { demoGo(); return Promise.resolve({ok: true}); }}];
let QSJ = null, QSSIG = "";
var RELPREV = {};                          // relay mode before the quick switch turned it on (back to it on the next tap)
function relQuick(i) {
  const r = ((QSJ && QSJ.relays) || [])[i]; if (!r) return Promise.resolve({ok: false, error: "relay?"});   // always the current state
  let v;
  if (r.mode === "on") { v = RELPREV[i] && RELPREV[i] !== "on" ? RELPREV[i] : "auto"; toast("⚡ " + r.name + ": " + t(v === "off" ? "Off" : "Auto")); }
  else { RELPREV[i] = r.mode; v = "on"; toast("⚡ " + r.name + ": " + t("On")); }
  return relayPost({action: "set", index: i, field: "mode", value: v});
}
function qsList(j) {                     // the fixed switches + one per relay (tap: on <-> back to before, mostly automatic)
  const rel = (j && j.relays) || [];
  return QS.concat(rel.map((r, i) => ({id: "rel" + i, ic: "⚡", lb: r.name || ("Relay " + (i + 1)), raw: true, tip: "Relay: on / automatic",
    on: (c, s) => !!((s.relay_states || [])[i]), go: () => relQuick(i)})));
}
function qsArrange(L, c, keepHidden) {        // the order and selection the user chose (new switches come at the end)
  const lay = (typeof window.lvQsLay === "function" && window.lvQsLay(c)) || (c && c.qs_layout) || {}, order = lay.order || [], hid = new Set(lay.hidden || []);   // 2.98.29: per device (536)
  const pos = {}; order.forEach((k, i) => pos[k] = i);
  return L.map((q, i) => [q, pos[q.id] !== undefined ? pos[q.id] : order.length + i]).sort((a, b) => a[1] - b[1]).map(x => x[0])
    .filter(q => keepHidden || !hid.has(q.id));
}
// 2.98.29: the separate «✏️ Anpassen» is gone - favourites, order and hidden switches are in the one edit mode of «Ansicht» (536),
// per device, with «Für alle Geräte übernehmen» (= cfg.qs_layout, the default for devices without an own arrangement)
function qsBuild(j) {
  const box = $("#qsw"); if (!box) return;
  const L = qsArrange(qsList(j), j && j.cfg);
  const sig = JSON.stringify(L.map(q => q.id + q.lb)) + LANG;
  if (sig === QSSIG) return; QSSIG = sig; box.textContent = "";
  L.forEach(q => { const b = el("button", "sec"); b.type = "button"; b.id = "qs-" + q.id; b.append(el("span", "", q.ic), el("small", "", q.raw ? q.lb : t(q.lb))); b.title = t(q.tip);
    if (q.talk) { talkTile(b); box.appendChild(b); return; }
    b.onclick = async () => { if (!QSJ) return; b.disabled = true; const r = await q.go(QSJ.cfg, QSJ.state); b.disabled = false;
      if (r && r.ok === false) toast("⚠ " + (r.error || "error"));
      else if (q.flash) { b.classList.add("flash"); setTimeout(() => b.classList.remove("flash"), 400); toast("📷 " + t("Photo saved")); }
      refresh(); };
    box.appendChild(b); });
}
Object.assign(I18N.de, {"Talk": "Sprechen", "Hold now": "Jetzt halten", "Talking …": "Spricht …", "Talk through the loudspeaker: tap once to unlock, then hold the button while you talk": "Durch den Lautsprecher sprechen: einmal antippen zum Freischalten, dann den Knopf gedrückt halten, solange du sprichst", "Unlocked - now hold the button while you talk": "Freigeschaltet – jetzt den Knopf gedrückt halten, solange du sprichst"});
Object.assign(I18N.de, {"Games": "Spiele", "All games for the phones: game corner, game collection and the simulator game - one QR code": "Alle Spiele fürs Handy: Spielecke, Spielesammlung und Simulator-Spiel – ein QR-Code",
  "Close all games? The players are logged out.": "Alle Spiele schliessen? Die Spieler werden abgemeldet."});
Object.assign(I18N.de, {"Mask": "Maske", "Motion mask over the picture: red = what the detection sees as movement": "Bewegungsmaske über dem Bild: rot = was die Erkennung als Bewegung sieht"});
// talk tile: two steps against an accidental press - a tap unlocks it for 6 s, then hold it while talking
const QTALK = {until: 0, timer: null, down: false};
function talkTilePaint() {
  const b = $("#qs-talk"); if (!b) return;
  const armed = Date.now() < QTALK.until, sm = b.querySelector("small");
  b.classList.toggle("armed", armed && !TK.on); b.classList.toggle("talking", TK.on);
  const tx = t(TK.on ? "Talking …" : armed ? "Hold now" : "Talk"); if (sm.textContent !== tx) sm.textContent = tx;
}
function talkTile(b) {
  b.dataset.talk = "1";
  const lock = () => { QTALK.until = 0; clearTimeout(QTALK.timer); talkTilePaint(); };
  b.addEventListener("contextmenu", e => e.preventDefault());
  b.addEventListener("pointerdown", e => { e.preventDefault(); if (b.disabled) return; QTALK.t0 = Date.now();
    if (Date.now() < QTALK.until) { QTALK.down = true; clearTimeout(QTALK.timer); try { b.setPointerCapture(e.pointerId); } catch (x) {}
      Promise.resolve(talkStart()).then(talkTilePaint); talkTilePaint(); } });
  const up = e => { e.preventDefault();
    if (QTALK.down) { QTALK.down = false; talkStop(); lock(); return; }      // after talking it is locked again at once
    if (e.type !== "pointerup" || b.disabled || Date.now() - (QTALK.t0 || 0) > 600) return;   // only a short tap unlocks
    QTALK.until = Date.now() + 6000; talkTilePaint(); toast("🎙 " + t("Unlocked - now hold the button while you talk"));
    clearTimeout(QTALK.timer); QTALK.timer = setTimeout(lock, 6000); };
  b.addEventListener("pointerup", up); b.addEventListener("pointercancel", up);
}
function qsPaint(j) {
  qsBuild(j); QSJ = j; const c = j.cfg || {}, s = j.state || {};
  qsList(j).forEach(q => { const b = $("#qs-" + q.id); if (!b) return;
    const on = !!q.on(c, s); b.classList.toggle(q.cls || "on", on);
    if (q.lbf) { const sm = b.querySelector("small"), tx = t(q.lbf(c, s)); if (sm.textContent !== tx) sm.textContent = tx; }
    if (q.icf) { const sp = b.querySelector("span"), ic = q.icf(c, s); if (sp.textContent !== ic) sp.textContent = ic; }
    const ok = q.ok ? q.ok(c, s) : true; if (!b.dataset.busy) b.disabled = !ok;
    b.classList.toggle("na", !ok);                          // 2.98.6: not available here (no lamp, no thermal camera ...) = hidden
    b.title = t(q.tip) + (ok ? "" : " – " + t("not connected")); });
  talkTilePaint();
}
// ---- overview: green arrow = main function of this topic is on ----
const MAINSW = {
  "protect": (c, s) => s.arm_state === "armed" || s.arm_state === "arming", "sec:Camping / protection": (c, s) => !!s.camping,
  "sec:Reference scan": c => !!(c.refscan_on_arm || +c.refscan_every > 0), "sec:Power saving": c => c.eco_on, "sec:Extra sensors": c => c.sens_on && (c.sensors || []).length > 0, "sec:Storm warning": c => c.storm_on, "sec:GPS module": c => c.gpsmod_on, "sec:Simulator": (c, s) => !!(s.sim && s.sim.on && s.sim.ok && s.sim.pic !== false), "sec:Solar panel": c => c.solar_on, "batt": (c, s) => !!(s.battery && s.battery.on), "sec:Theft protection": c => c.tamper_on || c.tamper_motion || c.tamper_power,
  "sec:Notifications": c => c.notify_on, "report": c => c.report_on, "sec:SMS (LTE stick)": c => c.sms_on,
  "sec:Detection": c => c.detection_on, "sec:AI detection": c => c.ai_enabled, "sec:Vehicle filter": c => c.car_filter, "sec:Rain": c => c.rain_auto,
  "sec:Wind": c => c.wind_auto, "sec:Low light": c => c.lowlight_auto || c.nightvision || c.nightvision_auto, "sec:Auto-tune": c => c.auto_tune,
  "sec:Camera / Servos": c => c.track_person, "sec:Patrol": c => c.patrol, "sec:Thermal camera": c => c.thermal_on || c.thermal_alarm, "th:alarm": c => c.thermal_alarm, "th:view": c => c.thermal_on,
  "sec:Lights": (c, s) => !!(s.light_cfg && (s.light_cfg.white !== "off" || s.light_cfg.ir !== "off")),
  "sec:Deterrence": (c, s) => {                // green only if a reaction is set AND its loudspeaker / light is there
    const spk = !!(s.audio && s.audio.spk), lamp = !!(s.light_cfg && s.light_cfg.white_out);
    return ["person", "big", "small", "warm"].some(g => { const a = c["deter_" + g + "_act"];
      return (a === "sound" && spk) || (a === "light" && lamp) || (a === "both" && (spk || lamp)); }); },
  "sec:Wake-up alarm": c => !!c.wake_on, "sec:Microphone": c => !!c.audio_in, "sec:Loudspeaker": c => !!c.siren_on && c.siren_on !== "off",
  "sec:Recording": c => c.record, "sec:Timelapse": c => c.timelapse_on, "sec:Backup": c => !!c.backup_type && c.backup_type !== "off",
  "relayset": c => c.relays_on, "schedule": (c, s, j) => (j.schedules || []).some(x => x.enabled),
  "wifi": (c, s) => !!(s.hotspot && s.hotspot.on), "sec:Web stream": c => c.web_stream, "guest": (c, s) => !!(s.guest && s.guest.active),
  "sec:MQTT / Home Assistant": c => c.mqtt_on, "sec:Updates": c => c.update_auto};
let MAINJ = null;
function mainPaint(j) {
  if (j) MAINJ = j; else j = MAINJ || {};
  const c = Object.assign({}, j.cfg || {}), s = j.state || {};
  Object.entries(ctrl).forEach(([k, x]) => { if (x && x.type === "bool" && x.input) c[k] = x.input.checked; });   // what the page shows right now
  const val = v => { const f = MAINSW[v]; if (!f) return null; try { return !!f(c, s, j); } catch (e) { return null; } };
  document.querySelectorAll("#settings details.sub, #settings details.grp").forEach(d => {
    let on = null;
    if (d.classList.contains("sub")) on = val(d.dataset.view);
    else if (d.dataset.main) on = val(d.dataset.main);
    else { const subs = [...d.querySelectorAll(":scope > details.sub")].map(x => val(x.dataset.view)).filter(x => x !== null); on = subs.length ? subs.some(Boolean) : null; }
    try { d.classList.toggle("mon", on === true); d.classList.toggle("moff", on === false); } catch (e) {}
  });
}

async function build() {
  try { TRIG = await (await fetch("/api/triggers?lang=" + LANG)).json(); } catch (e) { TRIG = []; }
  try { FEAT = (await (await fetch("/api/schedule?lang=" + LANG)).json()).features || []; } catch (e) { FEAT = []; }
  const sch = await (await fetch("/api/schema?lang=" + LANG)).json();
  const box = $("#settings");
  try { const u = await (await fetch("/api/ui_simple")).json(); const old = document.getElementById("simplebar"); if (old) old.remove();
    const sbar = simpleBar(!!u.on); sbar.id = "simplebar"; box.parentElement.insertBefore(sbar, box); } catch (e) {}
  sch.forEach(sec => {
    const d = el("details", "card");
    d.appendChild(el("summary", "", sec.name));
    d.dataset.view = "sec:" + sec.id; d.dataset.vgroup = "Settings"; d.dataset.vlabel = sec.name;
    sec.toggles.forEach(tg => {
      const row = el("label", "row tg"); row.dataset.key = tg.key;
      const cb = el("input"); cb.type = "checkbox"; cb.className = "sw";
      cb.onchange = () => { post("/api/set", {key: tg.key, value: cb.checked}); try { mainPaint(); } catch (e) {} };
      row.append(el("span", "", tg.label), cb);
      d.appendChild(row); ctrl[tg.key] = {type: "bool", input: cb};
    });
    if (sec.id === "Messages") msgBoxes(d, sec.texts || []);
    else (sec.texts || []).forEach(x => { if (x.key === "longitude") return; d.appendChild(x.key === "latitude" ? locBox() : textField(x)); });
    if ((sec.texts || []).some(x => x.key === "latitude")) d.querySelectorAll('.row.tg[data-key="gps_phone"]').forEach(r => { r.hidden = true; });

    if (sec.id === "Web stream") {
      const box = el("div", "sl"); const out = el("div", "mut"); out.style.fontSize = "12px"; out.style.wordBreak = "break-all";
      const rn = el("button", "sec", "🔄 " + t("New secret address")); rn.type = "button"; rn.style.marginTop = "6px";
      box.append(out, rn); d.appendChild(box);
      const show = j => { out.textContent = ""; rn.hidden = !j.on;
        if (!j.on) { out.textContent = t("Off – switch on «Picture for other programs» above."); return; }
        [["🎥 MJPEG", j.mjpeg], ["🖼 " + t("Still picture"), j.jpg], ["📼 RTSP", j.rtsp]].forEach(([l, u]) => { if (!u) return;
          const r = el("div", ""); r.style.margin = "4px 0"; const b = el("b", "", l + ": "); const c = el("code", "", u); c.style.userSelect = "all";
          const cp = el("button", "sec", "⧉"); cp.type = "button"; cp.style.padding = "2px 8px"; cp.title = t("Copy");
          cp.onclick = () => { try { navigator.clipboard.writeText(u); toast("⧉ " + t("Copied")); } catch (e) {} };
          r.append(b, c, " ", cp, qrBtn(u, l, {secret: true})); out.appendChild(r); });
        if (j.rtsp_msg && j.rtsp_msg !== "running") out.appendChild(el("div", "err", "RTSP: " + t(j.rtsp_msg)));
        out.appendChild(el("div", "", t("Keep these addresses secret: whoever has them sees the picture without a password."))); };
      const load = () => fetch("/api/ext").then(r => r.json()).then(show).catch(() => {});
      rn.onclick = async () => { if (!confirm(t("Make a new secret address? The old one stops working (other programs need the new one)."))) return; show(await post("/api/ext", {action: "renew"})); };
      load(); setInterval(() => { if (box.offsetParent) load(); }, 10000);
    }
    if (sec.id === "Recording") {
      const box = el("div", "sl"); box.appendChild(el("div", "row", "")).appendChild(el("span", "", "🗄 " + t("Recordings stored on")));
      const sel = el("select"); sel.style.width = "100%"; sel.style.marginTop = "4px"; const info = el("div", "mut", ""); info.style.fontSize = "12px";
      box.append(sel, info); d.appendChild(box);
      const KIND = {sd: t("memory card"), ssd: "SSD (NVMe)", usb: t("USB drive"), other: t("drive")};
      const fill = j => { sel.textContent = ""; const o0 = el("option", "", "💾 " + t("memory card (next to the program)")); o0.value = ""; sel.appendChild(o0);
        (j.candidates || []).forEach(c => { const o = el("option", "", (c.kind === "ssd" ? "⚡ " : "🔌 ") + KIND[c.kind] + " · " + c.path + " · " + c.free_gb + " / " + c.total_gb + " GB " + t("free")
          + (c.fat ? " · ⚠ FAT" : "") + (c.writable ? "" : " · ⚠ " + t("read only"))); o.value = c.path; sel.appendChild(o); });
        sel.value = j.want || ""; if (sel.value !== (j.want || "")) { const o = el("option", "", "⚠ " + j.want + " (" + t("missing") + ")"); o.value = j.want; sel.appendChild(o); sel.value = j.want; }
        info.textContent = (j.fallback ? "⚠ " + t("chosen drive missing - recordings on the memory card") + " · " : "") + t("now") + ": " + j.rec_dir + (j.moving || j.msg ? " · " + t(j.msg) : "")
          + (!(j.candidates || []).length ? " · " + t("no SSD / USB drive found") : ""); };
      const load = () => fetch("/api/storage").then(r => r.json()).then(fill).catch(() => {});
      sel.onchange = async () => { if (!confirm(t("Store the recordings there from now on? The existing ones are moved over (this can take a while)."))) { load(); return; }
        const r = await post("/api/storage", {path: sel.value, move: true, lang: LANG}); toast(r.ok ? "✓ " + t("Saved") : "⚠ " + (r.error || "error")); if (r.candidates) fill(r); setTimeout(load, 3000); };
      load();
    }
    if (sec.id === "AI detection") {
      const ab = el("button", "sec", "⬇ " + t("Download AI model") + " (≈ 70 MB)"); ab.type = "button"; ab.style.marginTop = "8px"; const am = el("div", "mut", "");
      fetch("/api/ai_model").then(r => r.json()).then(j => { if (j.present) { ab.hidden = true; } }).catch(() => {});
      ab.onclick = async () => { ab.disabled = true; const r = await post("/api/ai_model", {}); if (!r.ok) { am.textContent = "⚠ " + (r.error || "error"); ab.disabled = false; return; }
        const iv = setInterval(async () => { let j = {}; try { j = await (await fetch("/api/ai_model")).json(); } catch (e) {}
          am.textContent = j.busy ? t("downloading the AI model …") + " " + j.pct + " %" : (j.msg === "ready" ? "✓ " + t("AI ready") : "⚠ " + (j.msg || ""));
          if (!j.busy) { clearInterval(iv); ab.disabled = false; if (j.msg === "ready") ab.hidden = true; } }, 1500); };
      d.append(ab, am); ownExtras(d); spExtras(d); aiModelGroup(d, ab, am);
    }
    if (sec.id === "Notifications") {
      const tb = el("button", "sec", t("Test notification")); tb.style.marginTop = "8px";
      tb.onclick = () => post("/api/notify_test", {lang: LANG}).then(r => toast(r.ok ? t("Test sent") : "⚠ " + (r.error || "error"))); d.appendChild(tb);
      const ta = el("button", "sec", "🧪 " + t("Test all channels")); ta.style.margin = "8px 0 0 8px";
      const tr_ = el("div", "mut"); tr_.style.cssText = "margin-top:6px;white-space:pre-line";
      ta.onclick = async () => { ta.disabled = true; tr_.textContent = t("testing …");
        const r = await post("/api/notify_test", {lang: LANG, all: true}); ta.disabled = false;
        tr_.textContent = !r.ok ? "⚠ " + (r.error || "error") : (r.results || []).length ? r.results.map(x => (x.ok ? "✓ " : "✗ ") + x.ch + " – " + x.msg).join("\n") : t("No channel set up."); };
      d.append(ta, tr_);
    }
    sec.sliders.forEach(s => {
      const wrap = el("div", "sl"), top = el("div", "row");
      const val = el("span", "val", "");
      top.append(el("span", "", s.label), val);
      const r = el("input"); r.type = "range"; r.min = s.min; r.max = s.max; r.step = s.step;
      let timer = null;
      const send = () => post("/api/set", {key: s.key, value: parseFloat(r.value)});
      r.oninput = () => {
        editing = s.key; val.textContent = r.value;
        if (!timer) timer = setTimeout(() => { timer = null; send(); }, 100);   // throttle while dragging
      };
      r.onchange = () => { clearTimeout(timer); timer = null; send(); editing = null; };
      wrap.dataset.key = s.key; wrap.append(top, r); d.appendChild(wrap);
      ctrl[s.key] = {type: "num", input: r, val: val};
    });
    if (sec.id === "Timelapse") tlExtras(d);
    if (sec.id === "Microphone") micExtras(d);
    if (sec.id === "Updates") updExtras(d);
    if (sec.id === "Notifications") wpExtras(d);
    if (sec.id === "Backup") bkExtras(d);
    if (sec.id === "Theft protection") tpExtras(d);
    if (sec.id === "Reference scan") { const bx = el("div", "auxbox"); bx.append(el("div", "mut", t("refscan-note")));   // 2.95.97
      const a_ = el("a", "btn", "🧭 " + t("Open the assistant")); a_.href = "/tools#refscan"; a_.style.cssText = "display:block;margin-top:8px;text-align:center"; bx.appendChild(a_); d.appendChild(bx); }
    if (sec.id === "Extra sensors") sensExtras(d);
    if (sec.id === "Storm warning") stormExtras(d);
    if (sec.id === "GPS module") gpsExtras(d);
    if (sec.id === "Mover") moverExtras(d);
    if (sec.id === "Simulator") simExtras(d);
    if (sec.id === "Solar panel") solarExtras(d);
    if (sec.id === "Deterrence") dtExtras(d);
    if (sec.id === "MQTT / Home Assistant") mqExtras(d);
    if (sec.id === "SMS (LTE stick)") smsExtras(d);
    if (sec.id === "Loudspeaker") spkExtras(d);
    if (sec.id === "Thermal camera") thExtras(d);
    if (sec.id === "Security") secExtras(d);
    box.appendChild(d);
  });
}

// ---- «Log in only encrypted» (574): explanation, state, warning when there is no secure page ----
Object.assign(I18N.de, {"Security": "Sicherheit", "secure page": "sichere Seite", "this connection": "diese Verbindung", "encrypted": "verschlüsselt",
  "not encrypted": "nicht verschlüsselt", "Open the secure page": "Sichere Seite öffnen", "To the secure page": "Zur sicheren Seite",
  "For your safety a password can only be set over the secure page (https).": "Zu deiner Sicherheit lässt sich ein Passwort nur über die sichere Seite (https) setzen.",
  "The browser warns once about the certificate (MoveEye made it itself): «Advanced» → «Continue».": "Der Browser warnt einmal wegen des Zertifikats (MoveEye hat es selbst gemacht): «Erweitert» → «Weiter».",
  "port": "Port"});
function secExtras(d) {
  const bx = el("div", "auxbox"), st = el("div", ""), nt = el("div", "mut"); nt.style.marginTop = "6px"; bx.append(st, nt); d.appendChild(bx);
  const load = async () => { let j = null; try { j = await (await fetch("/api/seclogin?lang=" + LANG)).json(); } catch (e) { return; }
    if (!j || !j.ok) return; st.textContent = ""; nt.textContent = j.note || "";
    st.appendChild(el("div", "", (j.secure ? "🔒 " : "🔓 ") + t("this connection") + ": " + t(j.secure ? "encrypted" : "not encrypted")
      + (j.port ? " · https " + t("port") + " " + j.port : "")));
    if (j.warn) st.appendChild(el("div", "err", "⚠ " + j.warn));
    if (!j.secure && j.url) { const a = el("a", "btn sec", "🔒 " + t("Open the secure page")); a.href = j.url; a.style.cssText = "display:inline-block;margin-top:6px"; st.appendChild(a); } };
  load(); d.addEventListener("toggle", () => { if (d.open) load(); });
  if (typeof secPanel === "function") secPanel(d);          // 573: password, users, app keys, security check
}

// ---- audio: microphone level, live listening (WebAudio: works on every phone), loudspeaker of the Pi ----
const AU = {ctx: null, gain: null, reader: null, on: false, next: 0, vol: 2, st: null};
try { AU.vol = parseFloat(localStorage.getItem("mw-listen-vol")) || 2; } catch (e) {}
function micExtras(d) {
  const box = el("div", "auxbox");
  const r1 = el("div", "row"), lv = el("b", "", "–"); lv.id = "au-lvl"; lv.style.fontSize = "18px";
  const st = el("span", "mut", ""); st.id = "au-st"; r1.append(lv, st);
  const m = el("div", "aumeter"), bar = el("i"), bg = el("s"), thr = el("b"); bar.id = "au-bar"; bg.id = "au-bg"; thr.id = "au-thr";
  m.append(bar, bg, thr);
  const lg = el("div", "mut", ""); lg.id = "au-legend"; lg.style.fontSize = "11px";
  const b = el("div", "btns");
  const li = el("button", "sec", ""); li.type = "button"; li.id = "au-listen"; li.onclick = listenToggle;
  const sc = el("button", "sec", t("Search devices")); sc.type = "button"; sc.onclick = audioScan;
  b.append(li, sc);
  const vr = el("div", "sl"), top = el("div", "row"), vv = el("span", "val", "");
  top.append(el("span", "", t("Listening volume (this device)")), vv);
  const r = el("input"); r.type = "range"; r.min = 0.5; r.max = 8; r.step = 0.5; r.value = AU.vol;
  const sv = () => { vv.textContent = "× " + AU.vol; }; sv();
  r.oninput = () => { AU.vol = parseFloat(r.value); sv(); if (AU.gain) AU.gain.gain.value = AU.vol; try { localStorage.setItem("mw-listen-vol", String(AU.vol)); } catch (e) {} };
  vr.append(top, r);
  const er = el("div", "err"); er.id = "au-err";
  box.append(r1, m, lg, b, vr, er);
  d.insertBefore(box, d.children[1] || null);
  li.textContent = "🎧 " + (AU.on ? t("Stop listening") : t("Listen"));
  moveSelects(d, box, ["audio_in"]);
}
function spkExtras(d) {
  const box = el("div", "auxbox"), b = el("div", "btns");
  const te = el("button", "sec", "🔊 " + t("Test sound")); te.type = "button"; te.onclick = () => audioAct("test");
  const si = el("button", "red", "🚨 " + t("Siren now")); si.type = "button"; si.onclick = () => audioAct("siren");
  const sp = el("button", "sec", "⏹ " + t("Stop")); sp.type = "button"; sp.id = "au-stop"; sp.onclick = () => audioAct("stop");
  b.append(te, si, sp);
  const tb = el("div", "btns"); const tbb = talkButton(""); tbb.style.flex = "1"; tb.appendChild(tbb); box.appendChild(tb);
  const st = el("div", "mut", ""); st.id = "au-spk";
  const er = el("div", "err"); er.id = "au-err2";
  const hint = el("div", "mut", ""); hint.style.fontSize = "11px"; hint.style.marginTop = "4px";
  fetch("/api/audio").then(r => r.json()).then(j => { hint.textContent = t("Own sounds (.wav / .mp3): put the files into") + " " + j.folder + " " + t("and press «Search devices»"); }).catch(() => {});
  box.insertBefore(b, tb); box.append(st, er, ttsBox(), hint, btBox());
  d.insertBefore(box, d.children[1] || null);
  moveSelects(d, box, ["audio_out", "siren_on", "siren_sound"]);
}
Object.assign(I18N.de, {"Announcement": "Ansage", "Announcement: the Pi speaks this text": "Ansage: der Pi spricht diesen Text", "e.g. Please keep your distance - you are being filmed.": "z. B. Bitte Abstand halten – Sie werden gefilmt.", "Please keep your distance - you are being filmed.": "Bitte Abstand halten – Sie werden gefilmt.", "Hello, this place is under video surveillance.": "Hallo, dieser Platz wird videoüberwacht.", "Attention: the owner has been informed.": "Achtung: Der Besitzer wurde informiert.", "Voice": "Stimme", "Speak now": "Jetzt sprechen", "Save as own sound": "Als eigenen Klang speichern", "Saved - now selectable as sound for the siren / deterrence": "Gespeichert – jetzt als Klang für Sirene / Abschreckung wählbar", "no speech program (sudo apt install espeak-ng - or libttspico-utils for a nicer voice)": "kein Sprachprogramm (sudo apt install espeak-ng – oder libttspico-utils für eine schönere Stimme)", "empty text": "leerer Text"});
function ttsBox() {                                 // the Pi speaks a typed text (offline)
  const w = el("div"); w.style.marginTop = "10px";
  w.appendChild(el("div", "mut", "🗣 " + t("Announcement: the Pi speaks this text")));
  const tx = el("textarea"); tx.rows = 2; tx.maxLength = 200; tx.placeholder = t("e.g. Please keep your distance - you are being filmed.");
  tx.style.cssText = "width:100%;box-sizing:border-box;margin-top:6px;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:8px;font:inherit";
  const chips = el("div", "btns"); chips.style.flexWrap = "wrap";
  ["Please keep your distance - you are being filmed.", "Hello, this place is under video surveillance.", "Attention: the owner has been informed."].forEach(p => {
    const c = el("button", "sec", t(p)); c.type = "button"; c.style.fontSize = "12px"; c.onclick = () => { tx.value = t(p); }; chips.appendChild(c); });
  const lang = el("select"); [["de", "Deutsch"], ["fr", "Français"], ["it", "Italiano"], ["en", "English"]].forEach(([v, l]) => { const o = el("option", "", l); o.value = v; lang.appendChild(o); });
  lang.value = LANG === "rm" ? "de" : LANG; lang.title = t("Voice");
  const bt = el("div", "btns"), say = el("button", "", "🗣 " + t("Speak now")), sv = el("button", "sec", "💾 " + t("Save as own sound"));
  say.type = sv.type = "button"; const msg = el("div", "mut", "");
  const go = async save => { if (!tx.value.trim()) { tx.focus(); return; } say.disabled = sv.disabled = true; msg.textContent = "…";
    const r = await post("/api/tts", {text: tx.value, voice: lang.value, save: save, lang: LANG}); say.disabled = sv.disabled = false;
    msg.textContent = r.ok ? (save ? "✓ " + t("Saved - now selectable as sound for the siren / deterrence") + ": " + r.file : "✓") : "⚠ " + (r.error || "error"); };
  say.onclick = () => go(false); sv.onclick = () => go(true);
  bt.append(lang, say, sv); w.append(tx, chips, bt, msg); return w;
}
function moveSelects(d, after, keys) {              // the device choice comes first, then the switches and sliders
  let ref = after;
  keys.forEach(k => { const s = d.querySelector('select[data-key="' + k + '"]'); const w = s && s.closest(".sl");
    if (w) { d.insertBefore(w, ref.nextSibling); ref = w; } });
}
async function audioAct(a) {
  const r = await post("/api/audio", {action: a, lang: LANG});
  const e = $("#au-err2"); if (e) e.textContent = r.ok ? "" : "⚠ " + (r.error || "error");
  setTimeout(auPoll, 300);
}
async function audioScan() {
  const e = $("#au-err"); if (e) e.textContent = t("Searching …");
  const r = await post("/api/audio", {action: "scan", lang: LANG});
  if (e) e.textContent = r.error ? "⚠ " + r.error : "";
  toast("🎤 " + t("Microphones") + ": " + (r.in || 0) + " · 🔊 " + t("Loudspeakers") + ": " + (r.out || 0));
  refreshEnums(["audio_in", "audio_out", "siren_sound"]);
}
async function refreshEnums(keys) {
  let sch; try { sch = await (await fetch("/api/schema?lang=" + LANG)).json(); } catch (e) { return; }
  sch.forEach(sec => (sec.texts || []).forEach(x => {
    if (x.kind !== "enum" || !keys.includes(x.key)) return;
    const s = document.querySelector('select[data-key="' + x.key + '"]'); if (!s || s === document.activeElement) return;
    s.textContent = ""; x.choices.forEach(c => { const o = el("option", "", (x.labels && x.labels[c]) || c); o.value = c; s.appendChild(o); }); s.value = x.value;
  }));
}
function auTxt(st) {
  if (!st) return "";
  if (st.startsWith("error: ")) return "⚠ " + st.slice(7);
  return ({"listening": t("microphone on"), "off": t("off"), "starting": t("starting …")})[st] || st;
}
function updateAudio(a) {
  if (!a) return;
  AU.st = a;
  const pct = v => Math.max(0, Math.min(100, (v + 70) / 70 * 100));
  const on = a.level != null && a.status === "listening";
  const lv = $("#au-lvl");
  if (lv) {
    lv.textContent = on ? Math.round(a.level) + " dB" : (a.mic ? "–" : t("no microphone selected"));
    lv.style.color = a.loud ? "var(--red)" : "";
    $("#au-st").textContent = (a.mic ? auTxt(a.status) : "") + (a.listeners ? " · 🎧 " + a.listeners : "") + (a.rec ? " · ● " + t("REC") : "");
    const bar = $("#au-bar"); bar.style.width = (on ? pct(a.peak != null ? a.peak : a.level) : 0) + "%"; bar.style.background = a.loud ? "#ff3b3b" : "#3fb950";
    const thr = $("#au-thr"), bg = $("#au-bg");
    thr.style.display = on && a.thr != null ? "block" : "none"; if (a.thr != null) thr.style.left = pct(a.thr) + "%";
    bg.style.display = on && a.bg != null ? "block" : "none"; if (a.bg != null) bg.style.left = pct(a.bg) + "%";
    $("#au-legend").textContent = on && a.bg != null ? t("background") + " " + Math.round(a.bg) + " dB · " + t("noise alarm from") + " " + Math.round(a.thr) + " dB" : "";
  }
  const sp = $("#au-spk");
  if (sp) sp.textContent = (!a.spk ? t("no loudspeaker selected") : (a.talk ? "🎙 " + t("somebody is talking") : (a.playing ? "🔊 " + t("playing …") : ""))) + (a.sound_msg ? " ⚠ " + a.sound_msg : "");
  const stop = $("#au-stop"); if (stop) stop.disabled = !a.playing;
  const can = (a.mic && a.status === "listening") || AU.on;
  const bl = $("#btn-listen"); if (bl) bl.hidden = !can;
  const sl = $("#stick-listen"); if (sl) sl.hidden = !can;
  const vl = $("#vo-listen"); if (vl) vl.hidden = !can;
  window.LISTEN_CAN = can;
  const ts = $("#talk-slot");
  if (ts) ts.hidden = true;                                 // talking: the protected tile in the quick switches (tap, then hold)
  const li = $("#au-listen"); if (li) li.disabled = !can;
  const hb = $("#b-audio");
  if (hb) { if (a.mic) badge("#b-audio", "🎤 " + (on ? Math.round(a.level) + " dB" : "–"), a.loud ? "red" : (on ? "" : "yel")); hb.hidden = !a.mic || HIDDEN.has("b-audio"); }
}
async function auPoll() {
  try { const j = await (await fetch("/api/audio", {cache: "no-store"})).json(); updateAudio(j.state); } catch (e) {}
}
setInterval(() => { const g = document.querySelector('[data-view="grp:audio"]'); if (!document.hidden && ((g && g.open) || AU.on)) auPoll(); }, 700);
function paintListen() {
  ["#au-listen", "#btn-listen"].forEach(id => { const b = $(id); if (b) { b.textContent = "🎧 " + (AU.on ? t("Stop listening") : t("Listen")); b.classList.toggle("on", AU.on); } });
  const sl = $("#stick-listen");
  if (sl) { sl.classList.toggle("lon", AU.on); sl.title = AU.on ? t("Stop listening") : t("Listen"); sl.setAttribute("aria-label", sl.title); }
  const vl = $("#vo-listen"); if (vl) vl.classList.toggle("lon", AU.on);
  const ql = $("#qs-listen"); if (ql) { ql.classList.toggle("on", AU.on); if (AU.on) ql.disabled = false; }    // the quick switch lights up at once
}
function listenToggle() { AU.on ? listenStop() : listenStart(); }
function listenStop() { AU.on = false; try { if (AU.reader) AU.reader.cancel(); } catch (e) {} AU.reader = null; paintListen(); }
async function listenStart() {
  const A = window.AudioContext || window.webkitAudioContext;
  if (!A || !window.ReadableStream) { toast("⚠ " + t("this browser cannot play the live sound")); return; }
  if (!AU.ctx) { AU.ctx = new A(); AU.gain = AU.ctx.createGain(); AU.gain.connect(AU.ctx.destination); }
  try { await AU.ctx.resume(); } catch (e) {}
  AU.gain.gain.value = AU.vol; AU.on = true; paintListen();
  let r = null;
  try { r = await fetch("/api/audio/live", {cache: "no-store"}); } catch (e) {}
  if (!r || !r.ok || !r.body) { AU.on = false; paintListen(); toast("⚠ " + t("no microphone")); return; }
  if (!AU.on) { try { r.body.cancel(); } catch (e) {} return; }
  const rate = parseInt(r.headers.get("X-Audio-Rate"), 10) || 16000, up = rate < 22050 ? 2 : 1;    // old Safari: buffers need >= 22.05 kHz
  AU.reader = r.body.getReader(); AU.next = 0;
  let rest = null, last = 0;
  try {
    while (AU.on) {
      const res = await AU.reader.read(); if (res.done) break;
      let bytes = res.value;
      if (rest) { const m = new Uint8Array(rest.length + bytes.length); m.set(rest); m.set(bytes, rest.length); bytes = m; rest = null; }
      if (bytes.length % 2) { rest = bytes.slice(bytes.length - 1); bytes = bytes.subarray(0, bytes.length - 1); }
      const n = bytes.length / 2; if (!n) continue;
      const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.length);
      const buf = AU.ctx.createBuffer(1, n * up, rate * up), ch = buf.getChannelData(0);
      for (let i = 0; i < n; i++) {
        const v = dv.getInt16(i * 2, true) / 32768;
        if (up === 2) { ch[2 * i] = (last + v) / 2; ch[2 * i + 1] = v; } else ch[i] = v;
        last = v;
      }
      const now = AU.ctx.currentTime;
      if (AU.next < now + 0.03 || AU.next > now + 1.2) AU.next = now + 0.25;     // start, or catch up after a hiccup (keeps the delay short)
      const src = AU.ctx.createBufferSource(); src.buffer = buf; src.connect(AU.gain); src.start(AU.next); AU.next += n / rate;
    }
  } catch (e) {}
  if (AU.on) { AU.on = false; paintListen(); toast(t("Listening ended")); }
}

// ---- talk through the loudspeaker of the Pi (hold the button). Phones only allow the microphone on https pages. ----
const TK = {on: false, want: false, stream: null, ctx: null, src: null, proc: null, buf: [], timer: null, q: Promise.resolve(), err: false};
function talkButton(cls) {
  const b = el("button", cls || "sec", "🎙 " + t("Hold to talk")); b.type = "button"; b.classList.add("talkbtn");
  const down = e => { e.preventDefault(); try { b.setPointerCapture(e.pointerId); } catch (x) {} talkStart(); };
  const up = e => { e.preventDefault(); talkStop(); };
  b.addEventListener("pointerdown", down); b.addEventListener("pointerup", up); b.addEventListener("pointercancel", up);
  b.addEventListener("contextmenu", e => e.preventDefault());
  b.addEventListener("keydown", e => { if ((e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); talkStart(); } });
  b.addEventListener("keyup", e => { if (e.key === " " || e.key === "Enter") { e.preventDefault(); talkStop(); } });
  return b;
}
function paintTalk() {
  if (typeof talkTilePaint === "function") talkTilePaint();
  document.querySelectorAll(".talkbtn").forEach(b => { b.textContent = "🎙 " + (TK.on ? t("Talking … release to stop") : t("Hold to talk")); b.classList.toggle("on", TK.on); });
}
function talkHint() {
  const port = (AU.st && AU.st.https_port) || "";
  let ov = $("#talk-ov"); if (!ov) { ov = el("div"); ov.id = "talk-ov"; document.body.appendChild(ov); }
  ov.textContent = ""; const c = el("div", "card"); ov.appendChild(c);
  c.appendChild(el("div", "", "🎙")).style.fontSize = "36px";
  const h = el("div", "", t("Talking needs the secure page")); h.style.fontWeight = "700"; h.style.margin = "6px 0"; c.appendChild(h);
  c.appendChild(el("div", "mut", t("Phones only give the microphone to https pages. Open the secure page, confirm the certificate warning once («Advanced» → «Continue»), then hold the button again.")));
  if (port) {
    const a = el("a", "btn", "🔒 " + t("Open secure page")); a.href = "https://" + location.hostname + ":" + port + location.pathname; a.style.marginTop = "12px";
    c.appendChild(a);
  } else c.appendChild(el("div", "err", t("The secure page is not running (openssl missing).")));
  const x = el("button", "sec", t("Close")); x.style.margin = "12px 0 0 8px"; x.onclick = () => ov.remove(); c.appendChild(x);
}
async function talkStart() {
  if (TK.want) return;
  if (!window.isSecureContext || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { talkHint(); return; }
  TK.want = true; TK.err = false;
  try {
    if (!TK.stream) TK.stream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}});
  } catch (e) { TK.want = false; toast("⚠ " + t("the microphone of this device is not allowed")); return; }
  if (!TK.want) return;                                      // released while the permission question was open
  const A = window.AudioContext || window.webkitAudioContext;
  if (!TK.ctx) TK.ctx = new A();
  try { await TK.ctx.resume(); } catch (e) {}
  TK.src = TK.ctx.createMediaStreamSource(TK.stream);
  TK.proc = TK.ctx.createScriptProcessor(4096, 1, 1);
  const step = TK.ctx.sampleRate / 16000; let acc = 0, cnt = 0, pos = 0;
  TK.proc.onaudioprocess = e => {                            // down to 16 kHz: average of the samples of each step
    const x = e.inputBuffer.getChannelData(0);
    for (let i = 0; i < x.length; i++) { acc += x[i]; cnt++; pos += 1; if (pos >= step) { pos -= step; TK.buf.push(acc / cnt); acc = 0; cnt = 0; } }
  };
  TK.src.connect(TK.proc); TK.proc.connect(TK.ctx.destination);   // the output stays silent, it only keeps the node running
  TK.on = true; paintTalk();
  if (AU.gain) AU.gain.gain.value = 0;                      // no echo: listening is muted while you talk
  TK.timer = setInterval(talkSend, 200);
}
function talkSend() {
  if (!TK.buf.length) return;
  const f = TK.buf; TK.buf = [];
  const b = new Int16Array(f.length);
  for (let i = 0; i < f.length; i++) b[i] = Math.max(-1, Math.min(1, f[i])) * 32767;
  TK.q = TK.q.then(() => fetch("/api/talk?lang=" + LANG, {method: "POST", headers: {"Content-Type": "application/octet-stream"}, body: b.buffer})
    .then(async r => { if (!r.ok && !TK.err) { TK.err = true; const j = await r.json().catch(() => ({})); toast("⚠ " + (j.error || "error")); talkStop(); } })
    .catch(() => {}));
}
function talkStop() {
  TK.want = false;
  if (!TK.on) return;
  TK.on = false; clearInterval(TK.timer); talkSend();
  try { TK.src.disconnect(); TK.proc.disconnect(); } catch (e) {}
  if (TK.stream) { TK.stream.getTracks().forEach(tr => tr.stop()); TK.stream = null; }   // the phone shows the microphone as off again
  if (AU.gain) AU.gain.gain.value = AU.vol;
  TK.q = TK.q.then(() => post("/api/talk/stop", {}));
  paintTalk();
}

// ---- web password (first start: asked once per visit) + settings backup ----
function pwDialog(first) {
  const st = window.__lastState || {};
  if (st.pw_cli) { toast(t("The password was given on the command line (--web-password).")); return; }
  let ov = $("#pwd-ov"); if (!ov) { ov = el("div"); ov.id = "pwd-ov"; document.body.appendChild(ov); }
  ov.textContent = ""; const c = el("div", "card"); ov.appendChild(c); c.style.textAlign = "left";
  const h = el("div", "", "🔒 " + (st.pw_set ? t("Change web password") : t("Set a web password"))); h.style.fontWeight = "700"; h.style.fontSize = "17px";
  c.appendChild(h);
  const SL = st.seclogin || {};
  if (SL.plain && SL.url) {                                  // 574: never a password over plain http from another device
    c.append(el("div", "mut", t("For your safety a password can only be set over the secure page (https).")), el("div", "mut", t("The browser warns once about the certificate (MoveEye made it itself): «Advanced» → «Continue».")));
    const bb = el("div", "btns"), go = el("a", "btn", "🔒 " + t("To the secure page")), cl = el("button", "sec", first ? t("Later") : t("Cancel"));
    go.href = SL.url.replace(/^(https:\/\/[^/]+).*$/, "$1/"); cl.type = "button"; cl.onclick = () => { try { sessionStorage.setItem("mw-pw-later", "1"); } catch (e) {} ov.remove(); };
    bb.append(go, cl); c.appendChild(bb); return;
  }
  c.appendChild(el("div", "mut", first ? t("Nobody has set a password yet: anybody in this network can open this page, switch the alarm off or listen in. Set a password now (6 to 64 characters).")
                                      : t("6 to 64 characters. After saving, the browser asks for it once (any user name).")));
  const i1 = el("input"); i1.type = "password"; i1.placeholder = t("New password"); i1.autocomplete = "new-password";
  const i2 = el("input"); i2.type = "password"; i2.placeholder = t("Repeat"); i2.autocomplete = "new-password";
  [i1, i2].forEach(i => { i.style.width = "100%"; i.style.marginTop = "8px"; c.appendChild(i); });
  const er = el("div", "err"); c.appendChild(er);
  const b = el("div", "btns");
  const ok = el("button", "", t("Save")); ok.type = "button";
  ok.onclick = async () => {
    if (i1.value.length < 6) { er.textContent = "⚠ " + t("at least 6 characters"); return; }
    if (i1.value !== i2.value) { er.textContent = "⚠ " + t("the two passwords are not the same"); return; }
    const r = await post("/api/password", {action: "set", password: i1.value, lang: LANG});
    if (!r.ok) { er.textContent = "⚠ " + (r.error || "error"); return; }
    c.textContent = ""; c.appendChild(el("div", "", "✓ " + t("Password saved. The page reloads - log in with any user name and the new password.")));
    setTimeout(() => location.reload(), 2500);
  };
  b.appendChild(ok);
  if (st.pw_set) {
    const rm = el("button", "sec", t("Remove password")); rm.type = "button";
    rm.onclick = async () => { if (!confirm(t("Remove the password? Then anybody in the network can open the page."))) return;
      const r = await post("/api/password", {action: "remove", lang: LANG}); if (r.ok) { ov.remove(); toast(t("Password removed")); } else er.textContent = "⚠ " + (r.error || "error"); };
    b.appendChild(rm);
  }
  const later = el("button", "sec", first ? t("Later") : t("Cancel")); later.type = "button";
  later.onclick = () => { try { sessionStorage.setItem("mw-pw-later", "1"); } catch (e) {} ov.remove(); };
  b.appendChild(later); c.appendChild(b);
  setTimeout(() => i1.focus(), 50);
}
let pwAsked = false;
function updateSecurity(s) {
  const av = $("#app-ver"); if (av && s.version) av.textContent = "MoveEye " + s.version;
  const h1 = document.querySelector("header h1"); if (h1 && s.version) h1.title = "MoveEye " + s.version;
  const info = $("#pw-info");
  if (info) info.textContent = "🔒 " + (s.pw_set ? t("Web password: set") : t("Web password: none"));
  const b = $("#b-sec"); if (b && !b.dataset.click) { b.dataset.click = "1"; b.style.cursor = "pointer"; b.onclick = () => pwDialog(false); }
  const local = ["localhost", "127.0.0.1", "::1", "[::1]"].includes(location.hostname);
  let later = false; try { later = sessionStorage.getItem("mw-pw-later") === "1"; } catch (e) {}
  if (!pwAsked && !s.pw_set && !s.pw_cli && !local && !later && s.web_open) { pwAsked = true; pwDialog(true); }
  const sp = s.supply || {}, dk = s.disk || {}, line = $("#sys-supply");
  if (line) {
    const parts = [];
    if (sp.known) parts.push("⚡ " + (sp.volt ? sp.volt.toFixed(2) + " V · " : "") + (sp.uv_now ? "⚠ " + t("under-voltage!") : (sp.uv_boot ? t("ok (under-voltage earlier)") : "ok")));
    if (dk.free_mb != null) parts.push("💾 " + (dk.free_mb >= 1024 ? (dk.free_mb / 1024).toFixed(1) + " GB" : dk.free_mb + " MB") + " " + t("free"));
    line.textContent = parts.join(" · ");
    line.style.color = sp.uv_now ? "var(--red)" : "";
  }
  paintExtras(s);
  const rl = $("#sys-remote");
  if (rl) {
    const ts = s.remote_ts || {}, rem = s.remote || [];
    rl.textContent = "🌐 Tailscale: " + (!ts.state ? t("not installed") : (ts.state === "Running" ? t("connected") + (ts.ip ? " · http://" + ts.ip + ":" + location.port.replace(/^$/, "80") + "/" : "") : ts.state))
      + " · " + (rem.length ? t("watching now") + ": " + rem.join(", ") : t("nobody from outside"));
    rl.style.color = rem.length ? "var(--org)" : "";
  }
  const pj = $("#sys-proj"), P = s.project;
  if (pj && P) {
    const mb = v => v >= 1024 ? (v / 1024).toFixed(1) + " GB" : v + " MB";
    const dur = n => n < 3600 ? Math.round(n / 60) + " min" : n < 86400 ? Math.floor(n / 3600) + " h " + Math.floor(n % 3600 / 60) + " min" : Math.floor(n / 86400) + " " + t("days") + " " + Math.floor(n % 86400 / 3600) + " h";
    pj.textContent = "📦 " + t("Program") + ": MoveEye " + P.version + " · " + (P.file_kb >= 1024 ? (P.file_kb / 1024).toFixed(2) + " MB" : P.file_kb + " KB") + " · " + (P.lines || 0).toLocaleString("de-CH") + " " + t("lines")
      + "\n🗂 " + t("Data") + ": " + mb(P.data_mb) + " (" + P.data_n + " " + t("files") + ")" + (P.settings_kb != null ? " · " + t("settings") + " " + P.settings_kb + " KB" : "")
      + " · " + t("recordings") + " " + mb(P.rec_mb) + " (" + P.rec_n + ")" + (P.sim_mb ? " · " + t("simulator") + " " + mb(P.sim_mb) : "")
      + "\n⏱ " + t("running for") + " " + dur(P.run_s) + (P.ram_mb != null ? " · " + t("memory") + " " + P.ram_mb + " MB" : "") + " · Python " + P.python
      + (P.model || P.os ? "\n🖥 " + [P.model, P.os].filter(Boolean).join(" · ") : "");
  }
  const bp = $("#b-pwr");
  if (bp) {
    const low = dk.free_mb != null && dk.free_mb < 500;
    bp.hidden = !(sp.uv_now || low) || HIDDEN.has("b-pwr");
    if (sp.uv_now) badge("#b-pwr", "⚡ " + t("under-voltage"), "red"); else if (low) badge("#b-pwr", "💾 " + dk.free_mb + " MB", "yel");
  }
}
async function importSettings(f) {
  if (!f) return;
  if (!confirm(t("Load the settings from this file? The current settings are replaced (a copy is kept on the Pi)."))) return;
  let txt = ""; try { txt = await f.text(); } catch (e) {}
  const r = await fetch("/api/settings/import?lang=" + LANG, {method: "POST", headers: {"Content-Type": "application/json"}, body: txt})
    .then(x => x.json()).catch(() => ({ok: false, error: "connection"}));
  if (!r.ok) { toast("⚠ " + (r.error || "error")); return; }
  toast("✓ " + t("Settings loaded")); setTimeout(() => location.reload(), 1200);
}

// ---- header: status first, then what is switched on, then warnings, then the system. Things in their normal state are
//      not shown (no rain, calm, light ok, source connected ...), so the header stays short.
function hb(id, show, text, cls) {
  const b = $(id); if (!b) return;
  if (show && text !== undefined) badge(id, text, cls);
  b.hidden = !show;
}
function tidyHeader(s, c) {
  const L = s.lights || {}, hs = s.hotspot || {};
  hb("#b-obj", s.objects > 0);
  hb("#b-rec", !!s.recording);
  hb("#b-rain", !!s.rain_mode);
  hb("#b-wind", s.wind_level && s.wind_level !== "calm" && s.wind_level !== "off");
  hb("#b-light", !!s.lowlight, "🌙 " + t("LOW LIGHT"), "yel");
  hb("#b-relay", (s.relay_states || []).some(Boolean));
  hb("#b-sched", (s.sched_active || []).length > 0);
  const srcOk = (s.source_status || "") === "connected"; hb("#b-src", !srcOk);
  const cn = $("#b-conn"); if (cn) cn.hidden = cn.classList.contains("grn");
  hb("#b-camp", !!s.camping, "⛺ " + t("Camping"), "grn");
  const VW = s.viewers || {}; hb("#b-view", VW.n > 0, "👁 " + VW.n + " " + t(VW.n === 1 ? "viewer" : "viewers"), "");
  if ($("#b-view")) $("#b-view").title = t("viewers") + ": " + t("web") + " " + (VW.web || 0) + " · " + t("screen of the Pi") + " " + (VW.local || 0);
  hb("#b-eco", s.eco && s.eco !== "off", "🍃 " + t("Saving") + " · " + (s.eco === "saving" ? c.eco_fps + " FPS" : t("awake")), "blu");
  let tl = ""; const m = /^next photo in (\d+) min$/.exec(s.timelapse || ""); if (m) tl = " · " + m[1] + " min";
  hb("#b-tl", !!c.timelapse_on, "⏱ " + t("Timelapse") + tl, TL_HOLD_CLS(s));
  hb("#b-lights", !!(L.white || L.ir), (L.white ? "💡 " + t("Lamp") : "") + (L.white && L.ir ? " · " : "") + (L.ir ? "🔴 IR" : ""), "yel");
  const thOn = !!(c.thermal_on || c.thermal_alarm), thOk = s.thermal === "connected";
  hb("#b-therm", thOn, "🌡 " + t("Thermal") + (thOk && s.thermal_max != null ? " · " + Math.round(s.thermal_max) + " °C" : (thOk ? "" : " ⚠")), thOk ? ((s.warm || 0) > 0 ? "red" : "") : "yel");
  hb("#b-pat", !!(s.tracking || c.patrol || s.manual), s.manual ? "✋ " + t("MANUAL") : (s.tracking ? "🎯 " + t("TRACKING") : "🔄 " + t("Patrol")), s.manual ? "yel" : "blu");
  hb("#b-hs", !!hs.on, "📡 " + (hs.ssid || t("Own Wi-Fi")) + (hs.clients ? " · " + hs.clients : ""), "grn");
  const bt = s.battery || {};
  const ups = bt.src === "ups";
  hb("#b-batt", !!(bt.on && bt.pct != null), (ups && !bt.on_battery ? "🔌 " : "🔋 ") + bt.pct + " %" + (bt.hours != null ? " · " + fmtH(bt.hours) : "")
     + (ups && bt.charging ? " · " + t("charging") : "") + (s.batt_save && s.batt_save.on ? " · 🐢 " + t("saver") : ""), ups && !bt.on_battery ? "grn" : (bt.pct <= 15 ? "red" : (bt.pct <= 30 ? "yel" : "grn")));
  const rem = s.remote || [];
  hb("#b-remote", rem.length > 0, "🌐 " + t("Remote") + ": " + rem.join(", ").slice(0, 30), "org");
  if (typeof s.fps === "number") badge("#b-fps", (s.eco === "saving" ? "💤 " : "") + Math.round(s.fps) + " FPS",   // 2.95.64: real pictures per second; power saving is slow on purpose
    s.eco === "saving" ? "" : (s.fps >= 12 ? "grn" : (s.fps >= 6 ? "yel" : "red")));
  document.querySelectorAll("header .badge").forEach(b => { if (HIDDEN.has(b.dataset.view)) b.hidden = true; });
  compactHeader(s, c);                                    // right away (same frame): no flash of the long texts
}
// ---- compact header ----
var QUIET = ["b-person", "b-cpu", "b-fps", "b-wifi", "b-audio", "b-conn", "b-pres", "b-src"];
let hdrOpenUntil = 0;
function compactHeader(s, c) {
  const H = document.querySelector("header"); if (!H) return;
  const sh = (id, txt, title) => { const b = $(id); if (!b || b.hidden) return; b.title = title || b.textContent; b.textContent = txt; };
  // short symbols instead of long words (the full text stays as tooltip)
  const m = /^next photo in (\d+) min$/.exec(s.timelapse || "");
  sh("#b-tl", "⏱" + (m ? " " + m[1] + "′" : ""));
  sh("#b-light", "🌙"); sh("#b-camp", "⛺"); sh("#b-view", "👁 " + ((s.viewers || {}).n || 0), $("#b-view") && $("#b-view").title); sh("#b-eco", "🍃" + (s.eco === "saving" ? " " + c.eco_fps + " FPS" : ""));
  const L = s.lights || {}; sh("#b-lights", (L.white ? "💡" : "") + (L.ir ? " IR" : ""));
  sh("#b-pat", s.manual ? "✋" : (s.tracking ? "🎯" : "🔄"));
  const hs = s.hotspot || {}; sh("#b-hs", "📡" + (hs.clients ? " " + hs.clients : ""));
  // the main state: big; red and pulsing while a person / warm body / noise alarm is on
  const ab = $("#b-arm"); if (ab) ab.classList.toggle("alarm", !!(s.persons || s.warm || (s.audio && s.audio.loud)) && s.arm_state === "armed");
  // values in their normal range hide behind one "all ok" chip
  let quiet = 0;
  QUIET.forEach(id => { const b = $("#" + id); if (!b) return;
    const normal = !b.classList.contains("red") && !b.classList.contains("yel") && !b.classList.contains("org") && !(id === "b-person" && s.persons);
    b.classList.toggle("q", normal); if (normal && !b.hidden && !b.classList.contains("vh")) quiet++; });
  const ok = $("#b-ok");
  if (ok) {
    ok.hidden = !quiet; ok.textContent = H.classList.contains("hx") ? "✓ " + t("hide") : "✓ " + t("all ok");
    ok.title = t("tap: show all values");
    if (!ok.dataset.on) { ok.dataset.on = "1"; ok.onclick = () => { const x = !H.classList.contains("hx"); H.classList.toggle("hx", x);
      hdrOpenUntil = x ? Date.now() + 10000 : 0; ok.textContent = x ? "✓ " + t("hide") : "✓ " + t("all ok"); }; }
    if (hdrOpenUntil && Date.now() > hdrOpenUntil) { hdrOpenUntil = 0; H.classList.remove("hx"); }
  }
}
// one line when scrolled down (phone): name, state, bell
(function () {
  let small = false;
  addEventListener("scroll", () => {
    const y = scrollY;
    if (!small && y > 90) { small = true; document.body.classList.add("hdr-small"); }
    else if (small && y < 12) { small = false; document.body.classList.remove("hdr-small"); }
  }, {passive: true});
})();
function TL_HOLD_CLS(s) { return /moving|photo saved/.test(s.timelapse || "") ? "yel" : ""; }

/*BTJS*/
// ---- updates: list of versions (installed here / available at the update source), switch with one tap ----
// ---- web push: switch on on this device (needs https; iPhone: from the home screen app) ----
function wpExtras(d) {
  const box = el("div", "auxbox"); box.id = "wp-box"; d.appendChild(box);
  setTimeout(wpRender, 400);
}
const wpIOS = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
const wpApp = (window.matchMedia && matchMedia("(display-mode: standalone)").matches) || navigator.standalone === true;
function wpLabel() {
  const u = navigator.userAgent;
  const dev = /iPad/.test(u) || (wpIOS && !/iPhone/.test(u)) ? "iPad" : /iPhone/.test(u) ? "iPhone" : /Android/.test(u) ? "Android" : /Mac/.test(u) ? "Mac" : /Windows/.test(u) ? "Windows" : "PC";
  const br = /Edg\//.test(u) ? "Edge" : /Firefox\//.test(u) ? "Firefox" : /Chrome\//.test(u) ? "Chrome" : /Safari\//.test(u) ? "Safari" : "";
  return dev + (br ? " · " + br : "");
}
async function wpSub() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return null;
  try { const r = await navigator.serviceWorker.getRegistration("/"); return r ? await r.pushManager.getSubscription() : null; } catch (e) { return null; }
}
async function wpRender() {
  const box = $("#wp-box"); if (!box) return;
  let j; try { j = await (await fetch("/api/webpush", {cache: "no-store"})).json(); } catch (e) { return; }
  box.textContent = "";
  box.appendChild(el("b", "", "📲 " + t("Web push (no app needed)")));
  const info = el("div", "mut"); box.appendChild(info);
  const st = el("div", "mut"); const bt = el("div", "btns");
  info.textContent = t("Alarm messages straight into the browser / the home screen app of this device.") + " " +
    t("Devices") + ": " + j.count + (j.devices && j.devices.length ? " (" + j.devices.map(x => x.label || "?").join(", ") + ")" : "");
  if (!j.supported) { st.textContent = "⚠ " + t("python3-cryptography is missing (sudo apt install python3-cryptography)"); box.append(st); return; }
  if (!window.isSecureContext) {
    st.textContent = "🔒 " + t("Web push needs https. Open the page over the https address (Tailscale):");
    box.appendChild(st);
    if (j.https_url) {
      const a = el("a", "", j.https_url); a.href = j.https_url; const q = el("div", "qr"); q.style.cssText = "width:150px;height:150px;margin:8px 0;background:#fff;border-radius:8px;overflow:hidden";
      fetch("/api/qr?t=" + encodeURIComponent(j.https_url)).then(r => r.text()).then(x => { q.innerHTML = x; const s = q.querySelector("svg"); if (s) s.style.cssText = "width:100%;height:100%"; });
      box.append(a, q);
    } else {
      const b = el("button", "sec l-hide", "🔒 " + t("Switch on https over Tailscale")); b.type = "button";
      b.onclick = async () => { b.disabled = true; const r = await post("/api/webpush", {action: "https", on: true, lang: LANG});
        if (!r.ok) { st.textContent = "⚠ " + (r.error || "error"); b.disabled = false; return; } wpRender(); };
      bt.appendChild(b); box.appendChild(bt);
    }
    if (wpIOS) box.appendChild(el("div", "mut", t("iPhone / iPad: open the https address, then Share → «Add to Home Screen» and switch it on in the app from there.")));
    return;
  }
  if (wpIOS && !wpApp) { st.textContent = "ℹ " + t("iPhone / iPad: first Share → «Add to Home Screen», then open MoveEye from there and switch web push on."); box.appendChild(st); return; }
  const sub = await wpSub();
  const on = el("button", sub ? "sec" : "", sub ? "🔕 " + t("Switch off on this device") : "🔔 " + t("Switch on on this device")); on.type = "button";
  on.onclick = async () => {
    on.disabled = true;
    try {
      if (sub) { await post("/api/webpush", {action: "unsubscribe", endpoint: sub.endpoint}); await sub.unsubscribe(); }
      else {
        const perm = await Notification.requestPermission();
        if (perm !== "granted") { st.textContent = "⚠ " + t("Notifications are not allowed for this page (browser settings)."); on.disabled = false; return; }
        const reg = await navigator.serviceWorker.register("/sw.js", {scope: "/"}); await navigator.serviceWorker.ready;
        const key = Uint8Array.from(atob(j.key.replace(/-/g, "+").replace(/_/g, "/") + "==".slice(0, (4 - j.key.length % 4) % 4)), c => c.charCodeAt(0));
        const s = await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: key});
        const r = await post("/api/webpush", {action: "subscribe", sub: s.toJSON(), label: wpLabel(), lang: LANG});
        if (!r.ok) { st.textContent = "⚠ " + (r.error || "error"); on.disabled = false; return; }
      }
    } catch (e) { st.textContent = "⚠ " + e; on.disabled = false; return; }
    wpRender();
  };
  bt.appendChild(on);
  if (j.count) { const tb = el("button", "sec", "📨 " + t("Send test")); tb.type = "button";
    tb.onclick = async () => { const r = await post("/api/webpush", {action: "test", lang: LANG}); st.textContent = r.ok ? "✓ " + t("sent") : "⚠ " + (r.error || "error"); };
    bt.appendChild(tb); }
  box.append(bt, st);
  if (sub) st.textContent = "✓ " + t("Web push is on for this device.");
}
// ---- SMS: test ----
function smsExtras(d) {
  const box = el("div", "auxbox"); const st = el("div", "mut"); st.id = "sms-st";
  box.appendChild(el("div", "mut", t("A USB LTE stick with a SIM card (with credit). Works also where there is only the mobile network. Costs per SMS - mind the limits.")));
  const bt = el("div", "btns"), b = el("button", "sec", "📱 " + t("Send test SMS")); b.type = "button";
  b.onclick = async () => { b.disabled = true; st.textContent = "…"; const r = await post("/api/sms", {action: "test", lang: LANG});
    st.textContent = r.ok ? "✓ " + t("SMS sent") : "⚠ " + (r.error || "error"); b.disabled = false; };
  bt.appendChild(b); box.append(bt, st); d.appendChild(box);
}
// ---- MQTT: status ----
function mqExtras(d) { const box = el("div", "auxbox"); const st = el("div", "mut"); st.id = "mq-st"; box.append(st); d.appendChild(box); }
function mqPaint(s) { const st = $("#mq-st"); if (!st) return; const m = s.mqtt || {};
  st.textContent = "MQTT: " + (m.status === "connected" ? "✓ " + t("connected") : t(m.status || "off").replace(/^error: /, "⚠ ")) + (m.topic ? " · " + t("Topics") + ": " + m.topic + "/…" : ""); }
// ---- deterrence: short explanation + last reaction ----
function dtExtras(d) {
  const box = el("div", "auxbox"); const st = el("div", "mut"); st.id = "dt-st";
  box.append(el("div", "mut", t("What is seen decides the reaction. Animals need the AI detection, warm bodies the thermal camera. Light flashes: the white light.")), st);
  d.appendChild(box);
}
function dtPaint(s) { const st = $("#dt-st"); if (st) st.textContent = s.deter_last ? "↻ " + t("Last") + ": " + s.deter_last : ""; }
// ---- theft protection: what is watched ----
function tpExtras(d) {
  const box = el("div", "auxbox"); const st = el("div", "mut"); st.id = "tp-st";
  box.append(el("div", "mut", t("When armed: push message (urgent) and siren. The picture check pauses while the camera head moves itself.")), st);
  d.appendChild(box);
}
Object.assign(I18N.de, {"open": "offen", "closed": "zu", "last": "zuletzt", "Extra sensors": "Zusatz-Sensoren", "Sensors": "Sensoren", "Extra sensors on": "Zusatz-Sensoren ein", "433 MHz radio sensors (RTL-SDR stick + program rtl_433)": "433-MHz-Funksensoren (RTL-SDR-Stick + Programm rtl_433)", "Zigbee sensors (Zigbee2MQTT - needs MQTT)": "Zigbee-Sensoren (Zigbee2MQTT – braucht MQTT)", "Bluetooth tags (RuuviTag - needs python3-bleak)": "Bluetooth-Anhänger (RuuviTag – braucht python3-bleak)", "With a motion detector (PIR): only 1 picture per second while all is quiet": "Mit Bewegungsmelder (PIR): nur 1 Bild pro Sekunde, solange alles ruhig ist", "Bluetooth tag: alarm when not seen for (min)": "Bluetooth-Anhänger: Alarm, wenn nicht gesehen seit (Min.)", "Motion detector": "Bewegungsmelder", "Door": "Tür", "Gas / smoke": "Gas / Rauch", "Tag": "Anhänger", "Sensor": "Sensor", "at most 16 sensors": "höchstens 16 Sensoren", "unknown sensor": "unbekannter Sensor", "this GPIO is already in use": "dieser GPIO ist schon belegt", "test - it works": "Test – es funktioniert", "out of range (not seen any more)": "ausser Reichweite (nicht mehr gesehen)", "motion detected": "Bewegung erkannt", "opened": "geöffnet", "gas / smoke detected!": "Gas / Rauch erkannt!", "moved": "bewegt", "triggered": "ausgelöst", "GAS ALARM": "GAS-ALARM", "SENSOR ALARM": "SENSOR-ALARM", "rtl_433 missing (sudo apt install rtl-433)": "rtl_433 fehlt (sudo apt install rtl-433)", "listening": "hört zu", "no RTL-SDR stick found": "kein RTL-SDR-Stick gefunden", "python3-bleak missing (sudo apt install python3-bleak)": "python3-bleak fehlt (sudo apt install python3-bleak)", "needs MQTT": "braucht MQTT", "Motion detector (PIR)": "Bewegungsmelder (PIR)", "Door / lid contact": "Tür- / Deckelkontakt", "Bluetooth tag": "Bluetooth-Anhänger", "Other sensor": "Anderer Sensor", "only when armed": "nur wenn der Schutz an ist", "always (also when disarmed)": "immer (auch bei Schutz aus)", "no alarm, only note it": "kein Alarm, nur notieren", "Kind": "Art", "Connected to": "Angeschlossen an", "Reversed (reports at LOW)": "Umgekehrt (meldet bei LOW)", "Found radio devices - tap one to add it:": "Gefundene Funkgeräte – antippen zum Hinzufügen:", "Door contact": "Türkontakt", "Radio sensor": "Funksensor", "Remove this sensor?": "Diesen Sensor entfernen?", "gas / smoke!": "Gas / Rauch!", "motion": "Bewegung", "moved / triggered": "bewegt / ausgelöst", "out of range": "ausser Reichweite", "quiet": "ruhig", "GPIO error": "GPIO-Fehler", "waiting for data": "wartet auf Daten", "choose where it is connected": "wähle, wo er angeschlossen ist", "Extra sensors are switched off": "Zusatz-Sensoren sind ausgeschaltet", "Motion detector, door contact or gas / smoke module on a GPIO - or radio sensors (433 MHz, Zigbee) and Bluetooth tags. «Test» sends a push message.": "Bewegungsmelder, Türkontakt oder Gas-/Rauchmodul an einem GPIO – oder Funksensoren (433 MHz, Zigbee) und Bluetooth-Anhänger. «Test» schickt eine Push-Nachricht."});
Object.assign(I18N.de, {"fast charging": "lädt schnell", "full in": "voll in", "Cells": "Zellen"});
// ---- extra sensors (PIR, door contact, gas, 433 MHz, Zigbee, Bluetooth tags) ----
const SENS_IC = {pir: "🚶", door: "🚪", gas: "🔥", tag: "🏷️", other: "📡"};
const SENS_KN = [["pir", "Motion detector (PIR)"], ["door", "Door / lid contact"], ["gas", "Gas / smoke"], ["tag", "Bluetooth tag"], ["other", "Other sensor"]];
var SENSSIG = "";
function sensExtras(d) {
  const box = el("div", "auxbox"); box.id = "sens-box";
  box.appendChild(el("div", "mut", t("Motion detector, door contact or gas / smoke module on a GPIO - or radio sensors (433 MHz, Zigbee) and Bluetooth tags. «Test» sends a push message.")));
  const list = el("div"); list.id = "sens-list"; const err = el("div", "err"); err.id = "sens-err";
  const add = el("div", "btns"); add.id = "sens-add";
  [["pir", "Motion detector"], ["door", "Door contact"], ["gas", "Gas / smoke"], ["tag", "Bluetooth tag"], ["other", "Radio sensor"]].forEach(([k, l]) => {
    const b = el("button", "sec", "+ " + SENS_IC[k] + " " + t(l)); b.type = "button"; b.onclick = () => sensPost({action: "add", kind: k}); add.appendChild(b); });
  const st = el("div", "mut"); st.id = "sens-st"; st.style.marginTop = "8px";
  const sh = el("div", "mut"); sh.id = "sens-seenh"; sh.style.marginTop = "8px"; const seen = el("div", "btns"); seen.id = "sens-seen";
  box.append(list, err, add, st, sh, seen); d.appendChild(box);
}
function sensPost(b) {
  b.lang = LANG;
  return post("/api/sensors", b).then(r => { const e = $("#sens-err"); if (e) e.textContent = r.ok ? "" : "⚠ " + (r.error || "error"); SENSSIG = ""; refresh(); return r; });
}
function sensSrcLabel(v, seen) {
  if (!v) return "– " + t("not connected") + " –";
  if (v.startsWith("gpio:")) return "GPIO " + v.slice(5);
  const f = (seen || []).find(x => x.src === v), nm = f ? f.label : v.replace(/^[a-z]+:/, "");
  return (v.startsWith("rf:") ? "📻 433 MHz: " : v.startsWith("zb:") ? "🐝 Zigbee: " : v.startsWith("sim:") ? "🧪 " : "🔵 Bluetooth: ") + nm;
}
function sensGuess(e) {
  const d = e.data || {};
  if (e.src.startsWith("ble:")) return "tag";
  if ("contact" in d || "closed" in d || "contact_open" in d || "state" in d) return "door";
  if ("smoke" in d || "gas" in d || "carbon_monoxide" in d) return "gas";
  if ("occupancy" in d || "motion" in d) return "pir";
  return "other";
}
function sensAgo(sec) { return sec < 60 ? sec + " s" : sec < 3600 ? Math.round(sec / 60) + " min" : Math.round(sec / 3600) + " h"; }
function sensPaint(c, s) {
  const list = $("#sens-list"); if (!list || !c) return;
  const S = s.sens || {st: {}, seen: [], free: []}, L = c.sensors || [], seenL = S.seen || [];
  const sig = JSON.stringify([L, S.free, seenL.map(x => x.src + x.label), LANG]);
  const busy = document.activeElement && list.contains(document.activeElement) && /INPUT|SELECT/.test(document.activeElement.tagName);
  if (sig !== SENSSIG && !busy) {
    SENSSIG = sig; list.textContent = "";
    L.forEach(x => {
      const card = el("div", "sens-card"); card.dataset.id = x.id;
      const r1 = el("div", "row"); const dot = el("span", "dot", "●"); dot.id = "sd-" + x.id;
      const nm = el("input"); nm.type = "text"; nm.value = x.name; nm.maxLength = 24; nm.onchange = () => sensPost({action: "set", id: x.id, field: "name", value: nm.value});
      const del = el("button", "sec", "✕"); del.type = "button"; del.title = t("Remove");
      del.onclick = () => { if (confirm(t("Remove this sensor?") + "\n" + x.name)) sensPost({action: "remove", id: x.id}); };
      r1.append(el("span", "", SENS_IC[x.kind] || "📡"), dot, nm, del);
      const mk = (label, pairs, val, field) => { const lb = el("label", "", t(label)), sel = el("select");
        pairs.forEach(([v, l]) => { const o = el("option", "", l); o.value = v; sel.appendChild(o); }); sel.value = val;
        sel.onchange = () => sensPost({action: "set", id: x.id, field: field, value: sel.value}); lb.appendChild(sel); return lb; };
      const opts = [""].concat((S.free || []).map(g => "gpio:" + g), seenL.map(e => e.src));
      if (x.src && !opts.includes(x.src)) opts.splice(1, 0, x.src);
      const r2 = el("div", "sens-row");
      r2.append(mk("Kind", SENS_KN.map(([v, l]) => [v, t(l)]), x.kind, "kind"),
                mk("Connected to", [...new Set(opts)].map(v => [v, sensSrcLabel(v, seenL)]), x.src, "src"),
                mk("Alarm", [["armed", t("only when armed")], ["always", t("always (also when disarmed)")], ["off", t("no alarm, only note it")]], x.alarm, "alarm"));
      card.append(r1, r2);
      if (x.src.startsWith("gpio:")) { const lb = el("label"), cb = el("input"); cb.type = "checkbox"; cb.checked = !!x.inv; cb.style.cssText = "flex:none;width:auto;margin:0";
        cb.onchange = () => sensPost({action: "set", id: x.id, field: "inv", value: cb.checked}); lb.style.cssText = "display:flex;align-items:center;gap:8px;margin-top:8px;cursor:pointer";
        lb.append(cb, el("span", "mut", t("Reversed (reports at LOW)"))); card.appendChild(lb); }
      const foot = el("div", "row"); foot.style.marginTop = "6px"; const stl = el("span", "mut", ""); stl.id = "ss-" + x.id;
      const tb = el("button", "sec", "🧪 " + t("Test")); tb.type = "button";
      tb.onclick = () => sensPost({action: "test", id: x.id}).then(r => { if (r.ok) toast("✓ " + t("Test sent")); });
      foot.append(stl, tb); card.appendChild(foot); list.appendChild(card);
    });
    const sw = $("#sens-seen"), sh = $("#sens-seenh"); sw.textContent = "";
    const fresh = seenL.filter(e => !L.some(x => x.src === e.src)).slice(0, 12);
    sh.textContent = fresh.length ? t("Found radio devices - tap one to add it:") : "";
    fresh.forEach(e => { const g = sensGuess(e), b = el("button", "sec", SENS_IC[g] + " " + sensSrcLabel(e.src, seenL) + " · " + sensAgo(e.ago)); b.type = "button";
      b.onclick = () => sensPost({action: "add", kind: g, src: e.src, name: e.label.slice(0, 24)}); sw.appendChild(b); });
  }
  const col = {active: "var(--red)", pulse: "var(--yel)", missing: "var(--org)", ok: "var(--grn)", error: "var(--red)"};
  const word = {active: x => ({door: "open", gas: "gas / smoke!", pir: "motion"}[x.kind] || "triggered"), pulse: () => "moved / triggered", missing: () => "out of range",
                ok: x => x.kind === "door" ? "closed" : "quiet", error: () => "GPIO error", unknown: () => "waiting for data", off: () => "off"};
  L.forEach(x => { const q = (S.st || {})[x.id] || {}, d = $("#sd-" + x.id), sl = $("#ss-" + x.id); if (!d || !sl) return;
    d.style.color = col[q.state] || "var(--mut)";
    sl.textContent = (x.src ? t((word[q.state] || word.unknown)(x)) : t("choose where it is connected")) + (q.last ? " · " + t("last") + ": " + q.last : ""); });
  const st = $("#sens-st");
  if (st) { const p = []; if (c.rf433_on) p.push("📻 433 MHz: " + t(S.rf || "off")); if (c.zigbee_on) p.push("🐝 Zigbee: " + t(S.zb || "off")); if (c.ble_on) p.push("🔵 Bluetooth: " + t(S.ble || "off"));
    if (!c.sens_on) p.unshift("⚠ " + t("Extra sensors are switched off")); st.textContent = p.join(" · "); }
}
Object.assign(I18N.de, {"Storm warning": "Sturmwarnung", "Storm warning (push message)": "Sturmwarnung (Push-Nachricht)", "Also from the weather forecast: gusts in the next 12 hours (sends the location to Open-Meteo)": "Auch aus der Wetterprognose: Böen in den nächsten 12 Stunden (schickt den Standort an Open-Meteo)", "Warn when the air pressure falls by (hPa in 3 hours)": "Warnen, wenn der Luftdruck fällt um (hPa in 3 Stunden)", "Warn from wind / gusts of (km/h)": "Warnen ab Wind / Böen von (km/h)", "Wind meter: km/h per pulse per second": "Windmesser: km/h pro Impuls pro Sekunde", "Wind meter (anemometer) connected to": "Windmesser (Anemometer) angeschlossen an", "STORM WARNING": "STURMWARNUNG", "the air pressure falls fast": "der Luftdruck fällt schnell", "strong wind or a thunderstorm may come. Secure the awning and the tent.": "es kann starker Wind oder ein Gewitter kommen. Markise und Zelt sichern.", "strong wind measured": "starker Wind gemessen", "secure the awning and the tent.": "Markise und Zelt sichern.", "gusts expected in the next 12 hours": "Böen erwartet in den nächsten 12 Stunden", "secure the awning and the tent in time.": "Markise und Zelt rechtzeitig sichern.", "Air pressure from the BME280 temperature sensor. A wind meter: the two wires of the cup anemometer to a GPIO and GND.": "Luftdruck vom Temperaturfühler BME280. Windmesser: die zwei Drähte des Schalenanemometers an einen GPIO und GND.", "Air pressure": "Luftdruck", "trend after 1 hour": "Tendenz nach 1 Stunde", "no BME280 sensor": "kein BME280-Fühler", "Wind meter": "Windmesser", "gusts": "Böen", "Forecast, next 12 h": "Prognose, nächste 12 h", "no forecast yet": "noch keine Prognose", "Last warning": "Letzte Warnung"});
// ---- storm warning ----
function stormExtras(d) {
  const box = el("div", "auxbox"); const st = el("div", "mut"); st.id = "storm-st"; st.style.whiteSpace = "pre-wrap";
  box.appendChild(el("div", "mut", t("Air pressure from the BME280 temperature sensor. A wind meter: the two wires of the cup anemometer to a GPIO and GND.")));
  const b = el("button", "sec", "🧪 " + t("Test")); b.type = "button";
  b.onclick = () => post("/api/storm_test", {lang: LANG}).then(r => toast(r.ok ? "✓ " + t("Test sent") : "⚠ " + (r.error || "error")));
  const bt = el("div", "btns"); bt.appendChild(b); box.append(st, bt); d.appendChild(box);
}
function stormText(c, S) {
  const L = [];
  L.push("🧭 " + t("Air pressure") + ": " + (S.p ? S.p + " hPa" + (S.trend != null ? " (" + (S.trend > 0 ? "+" : "") + S.trend + " hPa / 3 h)" : " (" + t("trend after 1 hour") + ")") : t("no BME280 sensor")));
  L.push("🌬️ " + t("Wind meter") + ": " + (!S.meter ? t("none") : !S.meter_ok ? t("GPIO error") : (S.wind != null ? S.wind + " km/h" : "–") + (S.gust != null ? " · " + t("gusts") + " " + S.gust + " km/h" : "")));
  if (c.storm_forecast) L.push("📡 " + t("Forecast, next 12 h") + ": " + (S.fc != null ? t("gusts") + " " + Math.round(S.fc) + " km/h" : t("no forecast yet")));
  if (S.last) L.push("⚠ " + t("Last warning") + ": " + S.last);
  return L.join("\n");
}
Object.assign(I18N.de, {"Mover": "Mover", "Mover (tracked vehicle)": "Mover (Kettenfahrzeug)", "Motor driver": "Motortreiber", "Motor driver: address (I2C)": "Motortreiber: Adresse (I2C)", "Top speed (%)": "Höchstgeschwindigkeit (%)", "Turning speed (%)": "Drehgeschwindigkeit (%)", "Gentle start and stop (seconds)": "Sanft anfahren und bremsen (Sekunden)", "Left track runs the wrong way (turn round)": "Linke Kette läuft falsch herum (umdrehen)", "Right track runs the wrong way (turn round)": "Rechte Kette läuft falsch herum (umdrehen)", "Left and right tracks swapped": "Linke und rechte Kette vertauscht", "automatic: on when the motor driver is found": "automatisch: an, wenn der Motortreiber gefunden wird", "Motor HAT (Adafruit or compatible): M1 left, M2 right": "Motor HAT (Adafruit oder kompatibel): M1 links, M2 rechts", "Waveshare Motor Driver HAT: A left, B right": "Waveshare Motor Driver HAT: A links, B rechts", "the address is the one of the servo driver": "die Adresse ist die des Servo-Treibers", "no motor driver found": "kein Motortreiber gefunden", "motor driver found": "Motortreiber gefunden", "simulated": "simuliert", "test only - nothing moves": "nur Test – nichts fährt", "Simulation: show the stick even without a mover or motor driver (to try it out)": "Simulation: den Stick auch ohne Mover oder Motortreiber zeigen (zum Ausprobieren)", "stick shown for testing (the simulator has no mover)": "Stick zum Testen eingeblendet (der Simulator hat keinen Mover)", "the simulator has no mover": "der Simulator hat keinen Mover (im Simulator «Mover simulieren» einschalten)", "A tracked vehicle under MoveEye: the second stick drives it (up = forward, down = back, sideways = turn on the spot). The motor driver (Motor HAT with PCA9685 + TB6612 on I2C) is found by itself - without it the stick stays hidden. Without a new command for 0.6 s both tracks stop.": "Ein Kettenfahrzeug unter MoveEye: der zweite Stick fährt es (hoch = vorwärts, runter = rückwärts, seitlich = an Ort drehen). Der Motortreiber (Motor HAT mit PCA9685 + TB6612 an I2C) wird von selbst gefunden – ohne ihn bleibt der Stick verborgen. Kommt 0,6 s lang kein neuer Befehl, halten beide Ketten an."});
Object.assign(I18N.de, {"GPS module": "GPS-Modul", "Own GPS module (USB or serial; gpsd is used if installed)": "Eigenes GPS-Modul (USB oder seriell; gpsd wird genutzt, falls installiert)", "Theft tracking: alarm when the armed device is carried away, then its position every 5 minutes": "Diebstahl-Ortung: Alarm, wenn das geschützte Gerät weggetragen wird, danach alle 5 Minuten seine Position", "Theft tracking: alarm from a distance of (m)": "Diebstahl-Ortung: Alarm ab einer Entfernung von (m)", "Connection": "Anschluss", "automatic": "automatisch", "the device was carried away": "das Gerät wurde weggetragen", "Position": "Position", "position": "Position", "Position now": "Position jetzt", "THEFT ALARM": "DIEBSTAHL-ALARM", "gpsd not running": "gpsd läuft nicht", "no GPS module found": "kein GPS-Modul gefunden", "searching satellites": "sucht Satelliten", "fix": "Position gefunden", "A USB GPS receiver (e.g. u-blox, VK-162) is found by itself. It needs a view of the sky. With an LTE stick the position arrives also when the device is stolen.": "Ein USB-GPS-Empfänger (z. B. u-blox, VK-162) wird von selbst gefunden. Er braucht freie Sicht zum Himmel. Mit LTE-Stick kommt die Position auch an, wenn das Gerät gestohlen wird.", "satellites": "Satelliten", "Theft tracking on guard": "Diebstahl-Ortung wacht", "Theft tracking starts when armed": "Diebstahl-Ortung startet, wenn der Schutz an ist", "From the GPS module": "Vom GPS-Modul", "from the GPS module": "vom GPS-Modul"});
Object.assign(I18N.de, {"Solar panel": "Solarpanel", "Solar panel with current meter (INA219 on I2C)": "Solarpanel mit Strommesser (INA219 an I2C)", "Push message in the evening when the battery will probably not last until sunrise": "Push-Nachricht am Abend, wenn der Akku voraussichtlich nicht bis Sonnenaufgang reicht", "Current meter: shunt resistor (Ohm, usually 0.1)": "Strommesser: Shunt-Widerstand (Ohm, meist 0,1)", "Current meter: address (I2C)": "Strommesser: Adresse (I2C)", "The battery will probably not last until sunrise ({sr}): about {have} h left, {need} h needed. Charge it or switch on power saving.": "Der Akku reicht voraussichtlich nicht bis Sonnenaufgang ({sr}): noch etwa {have} h, nötig {need} h. Aufladen oder Stromsparen einschalten.", "Battery": "Akku", "lasts until sunrise ({sr})": "reicht bis Sonnenaufgang ({sr})", "too little until sunrise ({sr})": "zu knapp bis Sonnenaufgang ({sr})", "INA219 current meter between the panel and the charger (address 0x41 or 0x44 - 0x40 is often taken by the servo board).": "INA219-Strommesser zwischen Panel und Laderegler (Adresse 0x41 oder 0x44 – 0x40 ist oft vom Servo-Board belegt).", "no current meter found at this address": "kein Strommesser an dieser Adresse gefunden", "today": "heute", "max.": "max.", "Battery lasts until sunrise": "Akku reicht bis Sonnenaufgang", "Battery probably too low until sunrise": "Akku reicht voraussichtlich nicht bis Sonnenaufgang", "Night forecast: needs a battery value (Settings → Battery)": "Nacht-Prognose: braucht einen Akku-Wert (Einstellungen → Akku)"});
Object.assign(I18N.de, {"Recognise the animal species (second AI model - see the guide)": "Tierart erkennen (zweites KI-Modell – siehe Anleitung)", "Animal species: minimum certainty": "Tierart: Mindest-Sicherheit", "Animal species: model": "Tierart: Modell", "Animal species: picture preparation of the model": "Tierart: Bildaufbereitung des Modells", "Animal species: a second AI model (ONNX) recognises fox, badger, wild boar … It is not included - install it from an address or copy it into the folder.": "Tierart: ein zweites KI-Modell (ONNX) erkennt Fuchs, Dachs, Wildschwein … Es ist nicht dabei – von einer Adresse installieren oder in den Ordner kopieren.", "or .zip": "oder .zip", "Install model": "Modell installieren", "Folder": "Ordner", "Models": "Modelle", "Last": "Zuletzt", "downloading …": "lädt herunter …", "no model chosen": "kein Modell gewählt", "address must start with https://": "die Adresse muss mit https:// beginnen", "the address must end with .onnx or .zip": "die Adresse muss auf .onnx oder .zip enden", "file too big": "Datei zu gross"});
Object.assign(I18N.de, {"AI model": "KI-Modell", "Standard (SSD MobileNet V2)": "Standard (SSD MobileNet V2)", "Own (MoveEye model)": "Eigenes (MoveEye-Modell)", "Own model: address of its description (moveeye_model.json)": "Eigenes Modell: Adresse seiner Beschreibung (moveeye_model.json)", "Download own model": "Eigenes Modell herunterladen", "Update own model": "Eigenes Modell aktualisieren", "Own model: trained on GitHub from simulator pictures and your labelled alarm pictures (person, animal, vehicle). After the download MoveEye uses it (back to the standard: «AI model», Expert view). If it is missing or fails, the standard model runs.": "Eigenes Modell: auf GitHub trainiert aus Simulator-Bildern und deinen beschrifteten Alarmbildern (Person, Tier, Fahrzeug). Nach dem Herunterladen nimmt MoveEye es (zurück zum Standard: «KI-Modell», Ansicht Experte). Fehlt es oder klappt es nicht, läuft das Standard-Modell.", "Now running": "Läuft jetzt", "own model not used": "eigenes Modell nicht benutzt", "not downloaded yet": "noch nicht heruntergeladen", "downloading the own model …": "lädt das eigene Modell …", "own model ready": "eigenes Modell bereit", "MoveEye model": "MoveEye-Modell", "made": "erstellt",
  "updates by itself (daily, only if not worse)": "aktualisiert sich selbst (täglich, nur wenn nicht schlechter)", "automatic update off": "automatisches Aktualisieren aus", "last check": "zuletzt geprüft"});
function aiModelGroup(d, ab, am) {                 // 2.98.23 (Konzept): the choice «AI model» and the own model in ONE group «KI-Modell»
  const q = k => d.querySelector('[data-key="' + k + '"]:not(select)'), sel = q("ai_model"), own = d.querySelector(".auxbox.ownai");
  const at = sel || q("ai_own_auto") || own; if (!at) return;                // «Simple» shows fewer of them: the group starts at the first one
  const g = el("div", "aimg"); at.before(g);
  g.appendChild(el("div", "aimh", "🧠 " + t("AI model")));
  [sel, ab, am, own, q("ai_own_auto"), q("ai_own_url")].forEach(x => { if (x) g.appendChild(x); });
}
function ownExtras(d) {                             // part 195: own MoveEye model (YOLO) - download + which model runs
  const box = el("div", "auxbox ownai"); const st = el("div", "mut"); st.style.whiteSpace = "pre-wrap";
  box.appendChild(el("div", "mut", "🧠 " + t("Own model: trained on GitHub from simulator pictures and your labelled alarm pictures (person, animal, vehicle). After the download MoveEye uses it (back to the standard: «AI model», Expert view). If it is missing or fails, the standard model runs.")));
  const b = el("button", "sec", "⬇ " + t("Download own model")); b.type = "button"; b.style.marginTop = "6px";
  const show = j => { b.textContent = "⬇ " + t(j.present ? "Update own model" : "Download own model");
    const L = [t("Now running") + ": " + (j.running === "ssd" ? "SSD MobileNet V2" : j.running === "own" ? t("MoveEye model") + " " + j.running_version : t("none"))];
    if (j.choice === "own" && j.note) L.push("⚠ " + t("own model not used") + ": " + j.note);
    L.push(t("Own (MoveEye model)") + ": " + (j.present ? j.version + " · " + (j.classes || []).join(", ") + " · " + j.input + " px" + (j.map50 != null ? " · mAP50 " + Number(j.map50).toFixed(2) : "") + (j.made ? " · " + t("made") + " " + j.made : "") : t("not downloaded yet")));
    if (j.summary) L.push("📊 " + j.summary);
    if (j.present) L.push("🔄 " + t(j.auto ? "updates by itself (daily, only if not worse)" : "automatic update off") + (j.checked ? " · " + t("last check") + " " + j.checked : ""));
    if (j.busy) L.push(t("downloading the own model …") + " " + j.pct + " %"); else if (j.msg && j.msg !== "ready") L.push("⚠ " + j.msg);
    st.textContent = L.join("\n"); };
  const load = () => fetch("/api/own_model?lang=" + LANG).then(r => r.json()).then(show).catch(() => {});
  b.onclick = async () => { b.disabled = true; const r = await post("/api/own_model", {lang: LANG}); if (!r.ok) { toast("⚠ " + (r.error || "error")); b.disabled = false; return; }
    const iv = setInterval(async () => { let j = {}; try { j = await (await fetch("/api/own_model?lang=" + LANG)).json(); } catch (e) {} show(j);
      if (!j.busy) { clearInterval(iv); b.disabled = false; toast(j.msg === "ready" ? "✓ " + t("own model ready") : "⚠ " + (j.msg || "error")); } }, 1500); };
  box.append(b, st); d.appendChild(box); load(); setInterval(() => { if (document.body.contains(st)) load(); }, 15000);
}
function spExtras(d) {                              // animal species: second model, install from an address
  const box = el("div", "auxbox"); const st = el("div", "mut"); st.style.whiteSpace = "pre-wrap";
  box.appendChild(el("div", "mut", "🦊 " + t("Animal species: a second AI model (ONNX) recognises fox, badger, wild boar … It is not included - install it from an address or copy it into the folder.")));
  const url = el("input"); url.type = "url"; url.placeholder = "https://…/model.onnx  (" + t("or .zip") + ")"; url.style.cssText = "width:100%;box-sizing:border-box;margin-top:6px;background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:8px";
  const b = el("button", "sec", "⬇ " + t("Install model")); b.type = "button"; b.style.marginTop = "6px";
  const load = () => fetch("/api/species?lang=" + LANG).then(r => r.json()).then(j => {
    st.textContent = t("Folder") + ": " + j.folder + "\n" + t("Models") + ": " + (j.models.length ? j.models.join(", ") : t("none")) + " · " + t(j.msg || "")
      + (j.last ? "\n" + t("Last") + ": " + j.last.label + " " + Math.round(j.last.conf * 100) + " %" : ""); }).catch(() => {});
  b.onclick = async () => { b.disabled = true; st.textContent = t("downloading …"); const r = await post("/api/species", {url: url.value.trim(), lang: LANG}); b.disabled = false;
    toast(r.ok ? "✓ " + t("Saved") : "⚠ " + (r.error || "error")); load(); };
  box.append(url, b, st); d.appendChild(box); load(); setInterval(() => { if (document.body.contains(st)) load(); }, 15000);
}
function solarExtras(d) {
  const box = el("div", "auxbox"); const st = el("div", "mut"); st.id = "solar-st"; st.style.whiteSpace = "pre-wrap";
  box.append(el("div", "mut", t("INA219 current meter between the panel and the charger (address 0x41 or 0x44 - 0x40 is often taken by the servo board).")), st);
  d.appendChild(box);
}
function solarText(c, s) {
  const L = [], S = s.solar || {}, n = s.night;
  if (!c.solar_on) L.push("☀️ " + t("off"));
  else if (!S.ok) L.push("☀️ " + t("no current meter found at this address"));
  else L.push("☀️ " + S.w + " W (" + S.v + " V · " + S.a + " A) · " + t("today") + " " + S.wh + " Wh · " + t("max.") + " " + S.max + " W");
  if (n) L.push((n.enough ? "🌙 " + t("Battery lasts until sunrise") : "⚠ " + t("Battery probably too low until sunrise")) + " (" + n.sunrise + "): " + n.have_h + " h / " + n.need_h + " h");
  else L.push("🌙 " + t("Night forecast: needs a battery value (Settings → Battery)"));
  return L.join("\n");
}
function solarPaint(c, s) { const st = $("#solar-st"); if (st) st.textContent = solarText(c, s); }
/*SIMMAP*/
Object.assign(I18N.de, {"iPhone shortcuts": "iPhone-Kurzbefehle",
 "sc-intro": "Jede Meldung beginnt mit einem Stichwort. Darauf kann eine Automation in der Kurzbefehle-App reagieren. Auf dem iPhone geht das mit E-Mail («E-Mail» in diesem Abschnitt einschalten) oder SMS – nicht mit Mitteilungen von Apps.",
 "sc-1": "«E-Mail» in diesem Abschnitt einrichten und eine Testmeldung schicken.",
 "sc-2": "iPhone: Kurzbefehle → Automation → «+» → «E-Mail». Absender: die Adresse von MoveEye, Betreff enthält: MW-ALARM.",
 "sc-3": "«Sofort ausführen» wählen (sonst fragt das iPhone jedes Mal).",
 "sc-4": "Aktionen hinzufügen, z. B. «Lautstärke festlegen» 100 %, «Ton abspielen», «Taschenlampe», «URL öffnen» (Live-Seite), «Szene ausführen» (Home-App).",
 "sc-5": "Für jedes Stichwort eine eigene Automation: MW-WAERME, MW-LAERM, MW-SABOTAGE …",
 "Addresses back to MoveEye (for «Get contents of URL»)": "Adressen zurück zu MoveEye (für «Inhalte von URL abrufen»)",
 "sc-key-off": "Damit ein Kurzbefehl MoveEye ohne Passwort steuern kann, braucht er einen eigenen Schlüssel. Er erlaubt nur diese wenigen Aktionen.",
 "Make a shortcut key": "Kurzbefehl-Schlüssel erstellen", "Arm": "Schutz einschalten", "Disarm": "Schutz aus", "Siren off": "Sirene aus",
 "White light on": "Weisses Licht an", "White light off": "Weisses Licht aus", "Photo now": "Foto jetzt", "Status (text)": "Status (Text)",
 "Copy": "Kopieren", "copied": "kopiert", "New key": "Neuer Schlüssel", "Switch off": "Ausschalten",
 "Make a new key? The old addresses stop working.": "Neuen Schlüssel erstellen? Die alten Adressen funktionieren dann nicht mehr.",
 "sc-key-note": "Die Adresse enthält den Schlüssel – wie ein Passwort behandeln. Von unterwegs geht es über die Tailscale-Adresse (Meldungen → «Adresse dieser Seite für Links»).",
 "Let the radar turn (in the header; the home screen icon cannot move)": "Radar kreisen lassen (in der Kopfzeile; das Symbol auf dem Startbildschirm kann sich nicht bewegen)",
 "App icon": "App-Symbol", "App icon changed": "App-Symbol geändert", "Radar": "Radar", "Radar, two rings": "Radar, zwei Ringe",
 "Radar, gaps crosswise": "Radar, Lücken über Kreuz", "Radar with afterglow": "Radar mit Nachleuchten", "Four directions": "Vier Richtungen",
 "Lens with waves": "Linse mit Wellen", "Light radar (green)": "Helles Radar (grün)", "Night radar (orange beam)": "Nacht-Radar (oranger Strahl)", "Forest with a find": "Wald mit Fund", "Thermal picture": "Wärmebild", "Field of view": "Blickfeld", "Tent watch": "Zelt-Wache", "Shield": "Schild", "Radar with finds": "Radar mit Treffern", "Classic (orange)": "Klassisch (orange)", "Done": "Erledigt", "Later": "Später",
 "icon-note": "Gilt für den Browser-Tab, die Kopfzeile und den Handy-Startbildschirm. Android holt das neue Symbol von selbst (kann einen Tag dauern). iPhone / iPad: das Symbol auf dem Startbildschirm löschen und die Seite neu «Zum Home-Bildschirm» hinzufügen.",
 "ios-icon-hint": "MoveEye hat ein neues Symbol. Das iPhone behält das alte: Symbol lange drücken → «App entfernen», dann in Safari «Teilen» → «Zum Home-Bildschirm».",
 "Get ready": "Gleich geht's los", "You are the guard: turn the camera and catch them": "Du bist Wächter: Kamera drehen und erwischen", "Caught!": "Erwischt!",
 "Power mode": "Powermodus", "Power mode on: everything on the highest performance": "Powermodus ein: alles auf Höchstleistung", "Power mode off: your settings are back": "Powermodus aus: deine Einstellungen sind zurück", "active: every picture through the AI, best picture, processor at full clock": "aktiv: jedes Bild durch die KI, bestes Bild, Prozessor auf vollem Takt", "hot": "heiss", "the highest performance (uses more current and gets warmer) - switching it off restores your settings": "Höchstleistung (braucht mehr Strom und wird wärmer) – Ausschalten stellt deine Einstellungen wieder her", "Trusted devices": "Vertrauenswürdige Geräte", "A device that has logged in once is remembered (also after updates). Remove a device here if it is lost or should log in again.": "Ein Gerät, das sich einmal angemeldet hat, wird gemerkt (auch nach Updates). Entferne hier ein Gerät, wenn es verloren ist oder sich neu anmelden soll.", "since": "seit", "Remove this device? It must log in again.": "Dieses Gerät entfernen? Es muss sich neu anmelden.", "Remove all": "Alle entfernen", "Remove all trusted devices? Every device must log in again.": "Alle vertrauenswürdigen Geräte entfernen? Jedes Gerät muss sich neu anmelden.", "Update": "Update", "New update for the simulator": "Neues Update für den Simulator", "tab Simulator": "Reiter Simulator", "sim-view-help": "Das Fenster des Simulators: Maus links ziehen = verschieben, rechts ziehen = drehen, Rad = zoomen (nach einem Klick ins Bild), Doppelklick = hinfliegen. Finger: antippen = klicken, sonst scrollt die Seite; mit ✋ bedient der Finger den Simulator (ziehen = verschieben, ⟲ = drehen, zwei Finger = zoomen). Knöpfe unten wechseln die Ansicht.", "Python world simulator (ZIP)": "MW Sim · Welt (Kevin) (ZIP)", "second simulator, needs Python on the PC": "zweiter Simulator, braucht Python auf dem PC", "Program": "Programm", "lines": "Zeilen", "Data": "Daten", "files": "Dateien", "settings": "Einstellungen", "simulator": "Simulator", "running for": "läuft seit", "memory": "Arbeitsspeicher", "days": "Tagen", "Simulators in the network": "Simulatoren im Netz", "Search now": "Jetzt suchen", "Tools": "Werkzeuge", "Simulation off": "Simulation aus", "Simulator not reachable": "Simulator nicht erreichbar", "Connected for": "Verbunden seit", "Response time": "Antwortzeit", "Camera pictures/s": "Kamera Bilder/s", "Thermal pictures/s": "Wärmebilder/s", "Messages sent": "Meldungen gesendet", "Sensor events": "Sensor-Ereignisse", "Errors": "Fehler", "Searching": "Suche", "found": "gefunden", "Last search": "Letzte Suche", "addresses in": "Adressen in", "Simulators announce themselves every 2 s. «Search now» also asks every address of the network.": "Simulatoren melden sich alle 2 s. «Jetzt suchen» fragt zusätzlich jede Adresse im Netz ab.", "seen since": "gesehen seit", "last": "zuletzt vor", "messages": "Meldungen", "found by the search": "durch die Suche gefunden", "Find the simulator in the network by itself (and take over its address)": "Simulator im Netz selbst finden (und seine Adresse übernehmen)", "Simulators in the network:": "Simulatoren im Netz:", "No simulator announces itself in the network right now.": "Im Moment meldet sich kein Simulator im Netz.", "sim-missing": "Ein Simulator fehlt? Im Simulator den Schalter «An MoveEye senden» einschalten. Läuft er auf einem PC, muss die Windows-Firewall seinen Port erlauben (8765; ein zweiter Simulator z. B. 8767).", "this device": "dieses Gerät", "Use": "Verwenden", "bad address": "ungültige Adresse", "Phone / tablet view": "Handy- / Tablet-Ansicht", "Arrange": "Anpassen", "Arrange the switches": "Schalter anpassen", "Choose and arrange the switches": "Schalter auswählen und anordnen", "Tick what you want to see, move it with ▲ ▼. Saved for everybody on this device.": "Anhaken, was du sehen willst, mit ▲ ▼ verschieben. Gilt für alle an diesem Gerät.", "Reset": "Zurücksetzen", "Saved": "Gespeichert", "viewer": "Zuschauer", "viewers": "Zuschauer", "Viewers": "Zuschauer", "web": "Web", "screen of the Pi": "Pi-Bildschirm", "Simulator control": "Simulator-Steuerung", "Load": "Laden", "Controls": "Bedienung", "running": "läuft", "Upload a file to the simulator": "Eine Datei in den Simulator hochladen", "unknown control": "unbekannter Regler", "unknown scenario": "unbekanntes Szenario", "unknown choice": "unbekannte Auswahl", "cannot be deleted": "kann nicht gelöscht werden", "Delete this scenario in the simulator?": "Dieses Szenario im Simulator löschen?", "Video scenarios": "Video-Szenarien", "A 360° video (or a normal video) instead of the drawn world: real pictures, the camera looks around in it. Simulator 3.3 or newer.": "Ein 360°-Video (oder ein normales Video) statt der gezeichneten Welt: echte Bilder, die Kamera schaut darin herum. Ab Simulator 3.3.", "also drawn visitors in the video": "zusätzlich gezeichnete Besucher im Video", "(no videos yet - upload one below)": "(noch keine Videos – unten eines hochladen)", "off - drawn world": "aus – gezeichnete Welt", "Play": "Abspielen", "Stop": "Stopp", "Delete": "Löschen", "Delete this video in the simulator?": "Dieses Video im Simulator löschen?", "uploaded": "hochgeladen", "upload interrupted": "Hochladen abgebrochen", "Upload a video into the video folder of the simulator (big 4K videos are made smaller once):": "Ein Video in den Video-Ordner des Simulators hochladen (grosse 4K-Videos werden einmal verkleinert):", "video not found": "Video nicht gefunden", "not supported - update the simulator": "geht nicht – Simulator aktualisieren", "only videos (mp4, mov, mkv, webm, avi) or .json": "nur Videos (mp4, mov, mkv, webm, avi) oder .json", "file empty or bigger than 4 GB": "Datei leer oder grösser als 4 GB", "no file": "keine Datei", "Also follow animals and other movement (when no person is in the picture)": "Auch Tieren und anderen Bewegungen folgen (wenn keine Person im Bild ist)", "Follow movement: smallest size (% of the picture)": "Bewegung folgen: kleinste Grösse (% des Bildes)", "Follow movement: must move for (seconds)": "Bewegung folgen: muss sich so lange bewegen (Sekunden)", "Save CPU during the simulation (fewer pictures, the simulator draws only what is fetched)": "CPU schonen während der Simulation (weniger Bilder, der Simulator zeichnet nur, was abgeholt wird)", "Pictures per second in the simulation (CPU saving)": "Bilder pro Sekunde in der Simulation (CPU schonen)", "Simulator": "Simulator", "Simulation": "Simulation", "SIMULATION": "SIMULATION", "Address of the simulation program": "Adresse des Simulationsprogramms", "A separate simulation program on a PC or the Pi (motionwatch_simulator.py): two cameras, thermal camera, lights, day / night, weather and sensors. The switch «Simulation» changes between the real hardware and the simulation.": "Ein separates Simulationsprogramm auf einem PC oder dem Pi (motionwatch_simulator.py): zwei Kameras, Wärmebild, Licht, Tag/Nacht, Wetter und Sensoren. Der Schalter «Simulation» wechselt zwischen echter Hardware und Simulation.", "Switch the simulation off": "Simulation ausschalten", "Switch the simulation on": "Simulation einschalten", "off - the real cameras and sensors are used": "aus – die echten Kameras und Sensoren werden benutzt", "connected": "verbunden", "night": "Nacht", "day": "Tag", "not reachable": "nicht erreichbar", "connecting …": "verbinde …", "simulator not reachable - is it running?": "Simulator nicht erreichbar – läuft er?", "simulator not reachable": "Simulator nicht erreichbar", "Simulation on / off: cameras, thermal camera and sensors from the simulation program": "Simulation ein / aus: Kameras, Wärmebild und Sensoren aus dem Simulationsprogramm", "Simulation on / off": "Simulation ein / aus", "Simulator camera 0": "Simulator-Kamera 0", "Simulator camera 1": "Simulator-Kamera 1", "Simulator thermal camera": "Simulator-Wärmebildkamera", "Search a place (e.g. Zermatt)": "Ort suchen (z. B. Zermatt)", "Aerial picture": "Luftbild", "Map": "Karte", "Load this place": "Diesen Ort laden", "Tap on the map where MoveEye stands. Drag = move, two fingers or wheel = zoom.": "Auf der Karte antippen, wo MoveEye steht. Ziehen = verschieben, zwei Finger oder Mausrad = zoomen.", "Search not possible – tap the place on the map": "Suche nicht möglich – den Ort direkt auf der Karte antippen", "Search a setting …": "Einstellung suchen …", "Simple": "Einfach", "Expert": "Experte", "Simple: only the important settings. «Expert» shows all.": "Einfach: nur die wichtigen Einstellungen. «Experte» zeigt alle.", "Nothing found": "Nichts gefunden", "Only in Switzerland": "Nur in der Schweiz", "The simulator loads the place (about a minute the first time).": "Der Simulator lädt den Ort (beim ersten Mal etwa eine Minute)."});
Object.assign(I18N.de, {"Install simulator on the Pi": "Simulator auf dem Pi installieren", "Install simulator again": "Simulator neu installieren", "Start simulator here": "Simulator hier starten", "Stop simulator": "Simulator beenden", "Download for a PC (ZIP)": "Für einen PC herunterladen (ZIP)", "Simulator installed": "Simulator installiert", "Simulator started": "Simulator gestartet", "Simulator stopped": "Simulator beendet", "the simulator runs on this Pi": "der Simulator läuft auf diesem Pi", "Install": "Installieren", "Start": "Starten"});
function simExtras(d) {
  // the settings of the section (switches, address, slider) go into a fold-out «Settings»
  const rows = [...d.children].filter(x => x.tagName !== "SUMMARY");
  const box = el("div", "auxbox"); box.id = "sim-main";
  const head = el("div", ""); head.id = "sim-head"; head.style.cssText = "font-weight:600;font-size:15px;display:flex;align-items:center;gap:8px;flex-wrap:wrap";
  const st = el("div", "mut"); st.id = "sim-st"; st.style.cssText = "white-space:pre-wrap;margin-top:2px";
  const b = el("button", "", ""); b.type = "button"; b.id = "sim-btn"; b.style.cssText = "margin-top:10px;width:100%";
  b.onclick = async () => { const on = !(QSJ && QSJ.state.sim && QSJ.state.sim.on); b.disabled = true; await mwSimSet(on, LANG); b.disabled = false; refresh(); };
  const stats = el("div", ""); stats.id = "sim-stats"; stats.style.cssText = "display:grid;grid-template-columns:repeat(auto-fill,minmax(105px,1fr));gap:6px;margin-top:10px";
  box.append(head, st, stats, b);
  // ---- search in the network ----
  const nb = el("div", "auxbox"); nb.style.marginTop = "10px";
  const nh = el("div", "", "🔎 " + t("Simulators in the network")); nh.style.fontWeight = "600";
  const srch = el("button", "sec", "🔎 " + t("Search now")); srch.type = "button"; srch.id = "sim-search"; srch.style.cssText = "margin-top:8px;width:100%";
  srch.onclick = async () => { srch.disabled = true; await post("/api/sim", {action: "search", lang: LANG}); refresh(); setTimeout(() => { srch.disabled = false; }, 2500); };
  const sl = el("div", "mut"); sl.id = "sim-scan"; sl.style.cssText = "margin-top:6px;white-space:pre-wrap";
  const fnd = el("div", ""); fnd.id = "sim-found"; fnd.style.marginTop = "6px";
  // the 3D simulator for Windows to download - right here, not hidden under Tools
  const d3 = el("a", "btn", "🎮 " + t("3D simulator for Windows (ZIP)")); d3.href = "/sim/simulator3d.zip?lang=" + (LANG || "");
  d3.style.cssText = "display:block;margin-top:8px;width:100%;text-align:center;box-sizing:border-box";
  const d3n = el("div", "mut", t("Link for the PC browser") + ": " + location.origin + "/sim/simulator3d.zip"); d3n.style.cssText = "margin-top:6px;font-size:12px;word-break:break-all";
  const dpy = el("a", "btn sec", "🌍 " + t("Python world simulator (ZIP)")); dpy.href = "/sim/simulator_py.zip?lang=" + (LANG || "");
  dpy.style.cssText = "display:block;margin-top:8px;width:100%;text-align:center;box-sizing:border-box";
  const all = el("a", "btn sec", "⚙ " + t("Everything about the simulator (tab Simulator)")); all.href = "/sim"; all.style.cssText = "display:block;margin-top:8px;width:100%";
  const pi = el("div", ""); pi.id = "sim-pi"; pi.hidden = true; pi.style.marginTop = "8px";   // 2.95.51: the 3D simulator on the Pi itself
  const pl = el("div", "trow"); pl.id = "sim-plan"; pl.hidden = true; pl.style.marginTop = "8px";      // 2.95.53: Aufstell-Planer
  const plo = el("button", "sec", "🗺 " + t("Aufstell-Planer in the simulator")); plo.type = "button";
  plo.onclick = async () => { const r = await post("/api/sim", {action: "planner_open", lang: LANG}); if (!r.ok) toast("⚠ " + (r.error || t("error"))); else toast("✓ " + t("open in the window of the simulator")); };
  const pla = el("button", "sec", "✓ " + t("Take over the patrol of the planner")); pla.type = "button";
  pla.onclick = async () => { const r = await post("/api/sim", {action: "planner_apply", lang: LANG}); if (!r.ok) toast("⚠ " + (r.error || t("error"))); else toast("✓ " + t("Patrol set") + " · " + r.planner.pct + " % " + t("of the area in view")); };
  pl.append(plo, pla);
  const rb = el("div", ""); rb.id = "sim-replay"; rb.hidden = true; rb.style.marginTop = "8px";      // 2.95.53: Alarm-Rückblick
  rb.append(el("b", "", "⏪ " + t("Alarm replay in 3D")));
  const rs = document.createElement("select"); rs.id = "sim-replay-sel"; rs.style.cssText = "width:100%;margin-top:6px";
  const rr = el("div", "trow"); rr.style.marginTop = "6px";
  const rgo = el("button", "", "▶ " + t("Play in the simulator")); rgo.type = "button";
  const rsp = document.createElement("select"); [1, 2, 4].forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v + "×"; rsp.appendChild(o); });
  rsp.style.flex = "0 0 auto";
  rgo.onclick = async () => { if (!rs.value) return; const r = await post("/api/sim", {action: "replay", id: rs.value, speed: +rsp.value, lang: LANG});
    if (!r.ok) toast("⚠ " + (r.error || t("error"))); else toast("✓ " + t("plays in the window of the simulator") + " (" + Math.round(r.replay.seconds) + " s)"); };
  const rst = el("button", "sec", "⏹"); rst.type = "button"; rst.onclick = () => post("/api/sim", {action: "replay", stop: true});
  rr.append(rgo, rsp, rst); rb.append(rs, rr, el("div", "mut", t("replay-note")));
  const dsb = el("div", ""); dsb.style.marginTop = "12px";                // 2.95.53: KI-Prüfung mit Simulator-Bildern
  dsb.append(el("b", "", "🧪 " + t("AI test with simulator pictures")), el("div", "mut", t("dset-note")));
  const dr = el("div", "trow"); dr.style.marginTop = "6px";
  const dn = document.createElement("select"); [12, 24, 48].forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v + " " + t("pictures"); dn.appendChild(o); }); { const og = document.createElement("option"); og.value = "game"; og.textContent = "🎮 " + t("missed pictures from the game (hard cases)"); dn.appendChild(og); } dn.value = "24"; dn.style.flex = "0 0 auto";
  const dgo = el("button", "", "▶ " + t("Start the test")); dgo.type = "button";
  const dout = el("div", ""); dout.id = "dset-out";
  const dpaint = j => { const D = j.dataset || j; dout.textContent = "";
    if (D.busy) { dout.appendChild(el("div", "mut", "⏳ " + D.pct + " % · " + t(D.msg))); setTimeout(async () => dpaint(await post("/api/sim", {action: "dataset"})), 2000); return; }
    if (D.msg && D.msg.startsWith("error")) dout.appendChild(el("div", "err", "⚠ " + D.msg));
    const S = D.sum; if (!S) return;
    dout.appendChild(el("div", "big", S.found + " / " + S.n + " " + t("found") + " · " + S.false + " " + t("false persons")));
    const tb = document.createElement("table"); tb.className = "tl";
    const row = (a, b) => { const tr = document.createElement("tr"); tr.append(el("td", "", a), el("td", "", b)); tb.appendChild(tr); };
    Object.entries(S.by_cond).forEach(([k, v]) => row(t(k), v.found + "/" + v.n + " · " + v.pct + " %"));
    Object.entries(S.by_kind).forEach(([k, v]) => row(t(k), v.found + "/" + v.n + " · " + v.pct + " %"));
    row(t("near (under 8 m)"), S.near + " %"); row(t("far (8 m and more)"), S.far + " %"); row(t("AI time per picture"), S.ms + " ms (" + S.where + ")");
    dout.appendChild(tb);
    const z = document.createElement("a"); z.className = "btn sec"; z.href = "/api/dataset.zip"; z.textContent = "⬇ " + t("Training pictures (ZIP)"); z.style.display = "inline-block"; z.style.marginTop = "6px"; dout.appendChild(z); };
  dgo.onclick = async () => { const r = await post("/api/sim", {action: "dataset", start: true, n: dn.value === "game" ? "game" : +dn.value, lang: LANG}); if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; } dpaint(r); };
  dr.append(dn, dgo); dsb.append(dr, dout); rb.appendChild(dsb);
  // 2.95.99: a big training set for an own AI model - made by the simulator, saved as ZIP on the desktop of its PC
  const xr = el("div", "trow"); xr.style.marginTop = "8px"; const xn = document.createElement("select");
  [200, 500, 1000, 2000].forEach(n => { const o = document.createElement("option"); o.value = n; o.textContent = n + " " + t("pictures"); if (n === 500) o.selected = true; xn.appendChild(o); });
  const xgo = el("button", "sec", "📦 " + t("Training set for an own AI model (YOLO)")); xgo.type = "button";
  const xout = el("div", "mut");
  xgo.onclick = async () => { const r = await post("/api/sim", {action: "dataset", export: true, n: +xn.value, lang: LANG}); if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; }
    xout.textContent = t("The simulator makes the pictures and saves a ZIP on the desktop of its PC (about 2 s per picture).") + " " + ((r.export || {}).msg || ""); };
  xr.append(xn, xgo); dsb.append(xr, xout);
  (async () => { const r = await post("/api/sim", {action: "dataset"}); if (r && r.ok) dpaint(r); })();
  nb.append(nh, sl, fnd, srch, pi, pl, rb, d3, d3n, dpy, all);
  // ---- settings (moved here) ----
  const set = el("details", "sub"); set.style.marginTop = "10px"; set.appendChild(el("summary", "", "⚙️ " + t("Settings")));
  const sbody = el("div", ""); sbody.style.padding = "4px 0";
  rows.forEach(x => sbody.appendChild(x));
  sbody.appendChild(el("div", "mut", t("A separate simulation program on a PC or the Pi (motionwatch_simulator.py): two cameras, thermal camera, lights, day / night, weather and sensors. The switch «Simulation» changes between the real hardware and the simulation.")));
  set.appendChild(sbody);
  // ---- tools ----
  const tl = el("details", "sub"); tl.style.marginTop = "6px"; tl.appendChild(el("summary", "", "🧰 " + t("Tools")));
  const tools = el("div", ""); tools.id = "sim-tools"; tools.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:6px;padding:6px 0";
  const mk = (id, txt, act) => { const x = el("button", "sec", txt); x.type = "button"; x.id = id;
    x.onclick = async () => { x.disabled = true; const r = await post("/api/sim", {action: act, lang: LANG}); x.disabled = false;
      toast(r.ok ? "✓ " + t({install: "Simulator installed", start: "Simulator started", stop: "Simulator stopped"}[act]) : "⚠ " + (r.error || "error")); refresh(); };
    return x; };
  const dl = el("a", "btn sec", "⬇ " + t("Download for a PC (ZIP)")); dl.href = "/sim/simulator.zip";
  const pv = el("a", "btn sec", "📱 " + t("Phone / tablet view")); pv.href = "/preview"; pv.target = "_blank";
  tools.append(mk("sim-inst", "📦 " + t("Install simulator on the Pi"), "install"), mk("sim-start", "▶ " + t("Start simulator here"), "start"),
               mk("sim-stop", "⏹ " + t("Stop simulator"), "stop"), dl, pv);
  tools.querySelectorAll("button,a").forEach(x => { x.style.fontSize = "13px"; x.style.padding = "8px"; });
  tl.appendChild(tools);
  box.append(nb, set, tl);
  // ---- remote control of the simulator: it describes its scenarios and controls itself (CONTROL protocol 1) ----
  const vb = el("div", "auxbox"); vb.id = "sim-vbox"; vb.style.marginTop = "10px"; vb.hidden = true;
  const hd = el("div", "", "🎮 " + t("Simulator control")); hd.id = "sim-chd"; hd.style.fontWeight = "600";
  const vst = el("div", "mut"); vst.id = "sim-vst"; vst.style.whiteSpace = "pre-wrap"; vst.style.marginTop = "4px";
  const srow = el("div", "btns"); srow.style.flexWrap = "wrap"; srow.style.marginTop = "6px"; srow.style.alignItems = "center";
  const sel = document.createElement("select"); sel.id = "sim-vsel"; sel.style.flex = "1 1 100%"; sel.style.minWidth = "0";
  const vk = (txt, fn, cls) => { const x = el("button", cls === undefined ? "sec" : cls, txt); x.type = "button";
    x.onclick = async () => { x.disabled = true; try { await fn(); } finally { x.disabled = false; } }; return x; };
  const ctl = async (d) => { const r = await post("/api/sim", Object.assign({action: "ctl", lang: LANG}, d)); show(r); return r; };
  const bLoad = vk("▶ " + t("Load"), () => sel.value && ctl({ctl: "scenario", id: sel.value}), "");
  const bDel = vk("🗑 " + t("Delete"), async () => { if (sel.value && confirm(t("Delete this scenario in the simulator?") + "\n" + sel.options[sel.selectedIndex].textContent)) await ctl({ctl: "delete", id: sel.value}); });
  srow.append(sel, bLoad, vk("↻", () => ctl({ctl: "get"})), bDel);
  sel.onchange = () => { const o = sel.options[sel.selectedIndex]; bDel.hidden = !(o && o.dataset.del === "1"); };
  const groups = el("div", ""); groups.id = "sim-cgroups"; groups.style.marginTop = "8px";
  const upw = el("div", ""); upw.hidden = true; upw.style.marginTop = "8px";
  const upl = el("div", "mut", ""); const up = document.createElement("input"); up.type = "file"; up.id = "sim-vup"; up.style.maxWidth = "100%";
  const prog = el("div", "mut"); prog.id = "sim-vprog"; upw.append(upl, up, prog);
  up.onchange = () => {
    const f = up.files && up.files[0]; if (!f) return;
    const x = new XMLHttpRequest(); x.open("POST", "/api/sim/upload?lang=" + LANG + "&name=" + encodeURIComponent(f.name));
    x.upload.onprogress = (e) => { if (e.lengthComputable) prog.textContent = "⬆ " + f.name + " · " + Math.round(e.loaded / e.total * 100) + " %"; };
    x.onload = () => { let r = null; try { r = JSON.parse(x.responseText); } catch (e) {}
      prog.textContent = r && r.ok ? "✓ " + t("uploaded") + ": " + (r.saved || f.name) : "⚠ " + ((r && r.error) || x.status); up.value = ""; if (r && r.ok) show(r); };
    x.onerror = () => { prog.textContent = "⚠ " + t("upload interrupted"); };
    x.send(f);
  };
  let SIG = "";
  const fmt = (c, v) => (v == null ? "–" : (Math.abs(v) >= 100 || c.step >= 1 ? Math.round(v) : (+v).toFixed(c.step < 0.1 ? 2 : 1))) + (c.unit ? " " + c.unit : "");
  const build = (r) => simCtlBuild(groups, r, ctl, fmt);      // like the panel of the simulator (simCtlBuild, 2.93.16)
  const show = (r) => {
    if (!r || !r.ok) { vst.textContent = "⚠ " + ((r && r.error) || t("simulator not reachable")); return; }
    hd.textContent = "🎮 " + t("Simulator control") + (r.name ? " · " + r.name : "");
    const sig = JSON.stringify([(r.controls || []).map(c => [c.id, c.type, c.label, c.group, c.options, c.sub]), r.upload ? r.upload.accept : null]);
    if (sig !== SIG) { SIG = sig; build(r); }
    scOn(groups, r);
    groups.querySelectorAll("[data-cid]").forEach(row => {
      const c = (r.controls || []).find(x => x.id === row.dataset.cid); const inp = row.querySelector(".simv"); if (!c || !inp || inp === document.activeElement) return;
      if (c.type === "toggle") inp.checked = !!c.value; else if (c.value != null) inp.value = c.value;
      const vv = row.querySelector(".simvv"); if (vv) vv.textContent = fmt(c, c.value);
    });
    const cur = sel.value; sel.innerHTML = "";
    (r.scenarios || []).forEach(o => { const op = document.createElement("option"); op.value = o.id; op.dataset.del = o.deletable ? "1" : "";
      op.textContent = o.name + (o.id === r.scenario ? "  ◀ " + t("running") : ""); sel.appendChild(op); });
    srow.hidden = !(r.scenarios || []).length;
    sel.value = [...sel.options].some(o => o.value === cur) ? cur : (r.scenario || (sel.options[0] && sel.options[0].value) || "");
    sel.onchange();
    vst.textContent = r.status || "";
    upw.hidden = !r.upload;
    if (r.upload) { upl.textContent = "⬆ " + (r.upload.label || t("Upload a file to the simulator")) + (r.upload.max_mb ? " (max. " + r.upload.max_mb + " MB)" : ""); up.accept = (r.upload.accept || []).join(","); }
  };
  window.simCtl = () => ctl({ctl: "get"});
  vb.append(hd, vst, srow, groups, upw);
  box.appendChild(vb); d.appendChild(box);
  setInterval(() => { const v = $("#sim-vbox"); if (v && !v.hidden && v.offsetParent !== null && !document.hidden) window.simCtl(); }, 4000);
}
  // ---- the same controls on the live view, under the picture (2.95.2): only while the simulation is on and connected ----
  (function () {
    const W = $("#lv-simw"), D = $("#lv-sim"), G = $("#lv-simg"); if (!W || !G) return;
    let LSIG = "", busy = false;
    const fmt = (c, v) => (v == null ? "–" : (Math.abs(v) >= 100 || c.step >= 1 ? Math.round(v) : (+v).toFixed(c.step < 0.1 ? 2 : 1))) + (c.unit ? " " + c.unit : "");
    const lctl = async (d) => { const r = await post("/api/sim", Object.assign({action: "ctl", lang: LANG}, d)); lpaint(r); return r; };
    const lpaint = (r) => {
      if (!r || !r.ok) { $("#lv-simst").textContent = "⚠ " + ((r && r.error) || t("simulator not reachable")); return; }
      $("#lv-simt").textContent = "🎮 " + t("Simulator control") + (r.name ? " · " + r.name : "");
      const sig = JSON.stringify((r.controls || []).map(c => [c.id, c.type, c.label, c.group, c.options, c.sub, c.expert]));
      if (sig !== LSIG) { LSIG = sig; simCtlBuild(G, r, lctl, fmt); }
      scOn(G, r);
      G.querySelectorAll("[data-cid]").forEach(row => {
        const c = (r.controls || []).find(x => x.id === row.dataset.cid); const inp = row.querySelector(".simv"); if (!c || !inp || inp === document.activeElement) return;
        if (c.type === "toggle") inp.checked = !!c.value; else if (c.value != null) inp.value = c.value;
        const vv = row.querySelector(".simvv"); if (vv) vv.textContent = fmt(c, c.value);
      });
      $("#lv-simst").textContent = r.status || "";
    };
    const tick = async () => {
      const S_ = QSJ && QSJ.state && QSJ.state.sim, on = !!(S_ && S_.on && S_.ok);
      W.hidden = !on; if (!on) { LSIG = ""; return; }
      if (busy || document.hidden || !D.open || D.offsetParent === null) return;
      busy = true; try { lpaint(await post("/api/sim", {action: "ctl", ctl: "get", lang: LANG})); } finally { busy = false; }
    };
    D.addEventListener("toggle", tick); setInterval(tick, 3000); setTimeout(tick, 1500);
    // ---- the simulator window (3D-3.18): picture + mouse / finger / keys, like sitting at the simulator ----
    const VW = $("#lv-vw"), VI = $("#lv-vimg");
    $("#lv-vhelp").textContent = t("sim-view-help") === "sim-view-help" ? "The simulator window: drag with the left mouse button = move, right = turn, wheel = zoom, double click = fly there. Finger: drag = move (⟲: turn), two fingers = zoom. The buttons at the bottom change the view." : t("sim-view-help");
    let rot = false, vOn = false, vctl = false;
    const VP = simViewPoll(VI, 8);
    try { if (typeof simQBox === "function") VW.after(simQBox(VP)); } catch (e) {}      // 2.95.81: picture quality
    const VB = simViewBind(VI, {rot: () => rot, ctl: () => vctl || VW.classList.contains("big")});
    const zoom = d => () => VB.push({t: "wheel", d: d, x: 0.5, y: 0.5}, true);
    $("#lv-vin").onclick = zoom(1); $("#lv-vout").onclick = zoom(-1);
    $("#lv-vrot").onclick = () => { rot = !rot; $("#lv-vrot").classList.toggle("on", rot); };
    $("#lv-vctl").onclick = () => { vctl = !vctl; $("#lv-vctl").classList.toggle("on", vctl); };
    simTouchPad(VI.parentElement, VB, () => vOn && (vctl || VW.classList.contains("big")));
    $("#lv-vbig").onclick = () => { VW.classList.toggle("big"); $("#lv-vbig").textContent = VW.classList.contains("big") ? "✕" : "⛶"; };
    const vtick = () => {
      const S_ = QSJ && QSJ.state && QSJ.state.sim, want = !!(S_ && S_.on && S_.ok && S_.view) && D.open && !document.hidden && !W.hidden && !document.body.classList.contains("pv-on");   // 538: the controller view has its own picture
      VW.hidden = !(S_ && S_.view);
      if (!VW.hidden) { const h = t("sim-view-help"); if (h !== "sim-view-help") $("#lv-vhelp").textContent = h; }
      if (want && !vOn) { vOn = true; VP.start(); }
      else if (!want && vOn) { vOn = false; VP.stop(); VI.removeAttribute("src"); VW.classList.remove("big"); }
    };
    D.addEventListener("toggle", vtick); document.addEventListener("visibilitychange", vtick); setInterval(vtick, 1500);
  })();
Object.assign(I18N.de, {"Clap switch": "Klatschschalter", "Bless you": "Gesundheit", "«Bless you!»": "«Gesundheit!»", "Clap 2×": "2× klatschen", "Clap 3×": "3× klatschen", "Clap 4×": "4× klatschen", "Answer": "Antwort", "Words (several: separate with |)": "Worte (mehrere mit | trennen)", "Sensitivity (higher = also softer claps)": "Empfindlichkeit (höher = auch leisere Klatscher)", "Volume of the beep": "Lautstärke des Pieptons", "Sensitivity (higher = answers more readily)": "Empfindlichkeit (höher = antwortet eher)", "Volume of the answer": "Lautstärke der Antwort", "Clap switch on": "Klatschschalter ein", "Beep when recognised": "Piepton, wenn erkannt", "Only when not armed (claps of strangers switch nothing)": "Nur wenn der Schutz aus ist (Klatscher von Fremden schalten nichts)", "Practice: only count and beep, switch nothing": "Üben: nur zählen und piepen, nichts schalten", "Say «Bless you!» after a sneeze": "Nach einem Niesen «Gesundheit!» sagen", "Quiet at night (22 to 7 o'clock)": "Nachts still (22 bis 7 Uhr)", "Test beep": "Piepton testen", "switch on and clap 2× to try it": "einschalten und zum Ausprobieren 2× klatschen", "clap 2, 3 or 4 times": "2, 3 oder 4 Mal klatschen", "counting": "zähle", "last": "zuletzt", "Hear the answer": "Antwort anhören", "Install": "Installieren", "sn-note": "Die Niesen-Erkennung nutzt ein kleines Erkennungsmodell (YAMNet von Google, etwa 4 MB). Es wird beim ersten lauten Geräusch einmal geladen. Tipp: «Gesundheit!» mit dem Handy als Sprachmemo aufnehmen und mit «Eigene Antwort» hochladen – sie wird sofort als Antwort gewählt.",
 "Own answer (sound file)": "Eigene Antwort (Tondatei)", "saved and chosen as answer": "gespeichert und als Antwort gewählt", "loading the sound recognition …": "lade die Geräusch-Erkennung …", "waiting for the first loud sound": "wartet auf das erste laute Geräusch", "needs the sound recognition program - button «Install»": "braucht das Erkennungsprogramm – Knopf «Installieren»", "model could not be loaded": "Modell konnte nicht geladen werden", "installing … (a few minutes)": "installiere … (ein paar Minuten)", "last check": "letzte Prüfung", "today": "heute", "no speech program (sudo apt install libttspico-utils)": "kein Sprachprogramm (sudo apt install libttspico-utils)", "no microphone selected (Microphone)": "kein Mikrofon gewählt (Mikrofon)", "not while armed": "nicht, solange der Schutz an ist", "too many claps": "zu viele Klatscher", "too quiet": "zu leise", "not possible": "nicht möglich"});
// ---- 2.98.7: wake-up alarm (Einstellungen → Geräte & Sensoren) and the banner while it rings ----
async function wakeDo(a) { const r = await post("/api/wake", {action: a, lang: LANG}); if (!r.ok) toast("⚠ " + (r.error || "error")); else { if (a === "away_here") toast("✓ " + t("Saved")); refresh(); } }
function wakePaint(s) {
  const W = s.wake; if (!W) return;
  const d = document.querySelector('details[data-view="sec:Wake-up alarm"]');
  if (d) { let b = document.getElementById("wk-box");
    if (!b) { b = el("div", "sevbox"); b.id = "wk-box"; b.style.cssText = "margin-top:8px;padding:8px 10px;border:1px solid var(--line);border-radius:10px;font-size:13px";
      const tx = el("div", "", ""); tx.id = "wk-t"; const row = el("div", "btns"), row2 = el("div", "btns");
      const mk = (lb, a, cls) => { const x = el("button", cls || "sec", lb); x.type = "button"; x.onclick = () => wakeDo(a); return x; };
      const zl = el("a", "btn sec", "🛏 " + t("Draw the sleeping place")); zl.href = "/zones";
      row.append(zl, mk("🧭 " + t("Look here at night"), "away_here"), mk("🌙 " + t("Good night"), "sleep_now"));
      row2.append(mk("🔔 " + t("Test now"), "test"), mk("😴 " + t("Snooze"), "snooze"), mk("⏹ " + t("Alarm off"), "stop"));
      b.append(tx, row, row2, el("div", "mut", t("wake-note"))); d.appendChild(b); }
    $("#wk-t").textContent = W.text || ""; }
  // banner while it rings / snoozes (every page of the live view)
  let bn = document.getElementById("wk-ban");
  const show = W.state === "ring" || W.state === "snooze";
  if (!show) { if (bn) bn.remove(); return; }
  if (!bn) { bn = el("div"); bn.id = "wk-ban"; bn.style.cssText = "position:fixed;left:50%;transform:translateX(-50%);bottom:calc(14px + env(safe-area-inset-bottom,0px));z-index:120;background:var(--panel);border:2px solid var(--org);border-radius:16px;padding:10px 12px;display:flex;gap:8px;align-items:center;box-shadow:0 8px 30px rgba(0,0,0,.45);max-width:94vw;flex-wrap:wrap;justify-content:center";
    const tx = el("b", "", ""); tx.id = "wk-bt"; const a = el("button", "", "😴 " + t("Snooze")), o = el("button", "sec", "⏹ " + t("Alarm off"));
    a.type = o.type = "button"; a.onclick = () => wakeDo("snooze"); o.onclick = () => wakeDo("stop"); bn.append(tx, a, o); document.body.appendChild(bn); }
  $("#wk-bt").textContent = (W.state === "ring" ? "⏰ " : "😴 ") + (W.text || "");
  bn.querySelector("button").hidden = W.state !== "ring";
}
Object.assign(I18N.de, {"Wake-up alarm": "Wecker", "Draw the sleeping place": "Schlafplatz einzeichnen", "Look here at night": "Nachts hierhin schauen", "Good night": "Gute Nacht",
  "Test now": "Jetzt testen", "Snooze": "Schlummern", "Alarm off": "Wecker aus", "Wake-up time (HH:MM)": "Weckzeit (HH:MM)", "Days": "Tage",
  "Camera looks away from (HH:MM, empty = not)": "Kamera schaut weg ab (HH:MM, leer = nie)", "Snooze (minutes)": "Schlummern (Minuten)", "Rings at most (minutes)": "Klingelt höchstens (Minuten)",
  "Wake-up alarm on": "Wecker ein", "Switch the white light on": "Weisses Licht einschalten", "Gestures: wave = snooze, sit up / get up = off": "Gesten: winken = schlummern, aufsitzen / aufstehen = aus",
  "wake-note": "So geht's: 1. Kamera auf das Bett richten, unter «Zonen» einen «Schlafplatz» einzeichnen – er ist ab dann in jedem Bild schwarz, egal wohin die Kamera schaut. 2. Kamera dorthin drehen, wohin sie nachts schauen soll (z. B. Tür), «Nachts hierhin schauen». 3. Weckzeit einstellen. Beim Wecken dreht sich MoveEye zum Bett: winken = schlummern, aufsitzen oder aufstehen = aus. Das Bild vom Bett sieht nur die Gestenerkennung, es wird nie gespeichert."});
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"wake-note": "How it works: 1. Point the camera at the bed and draw a «Sleeping place» under «Zones» - from then on it is black in every picture, wherever the camera looks. 2. Turn the camera where it should look at night (e.g. the door), «Look here at night». 3. Set the time. When the alarm rings MoveEye turns to the bed: wave = snooze, sit up or get up = off. Only the gesture detection sees the bed; it is never stored."});
function sevPaint(s) {
  const V = s.soundev; if (!V) return;
  const box = (view, id) => { const d = document.querySelector('details[data-view="sec:' + view + '"]'); if (!d) return null;
    let b = document.getElementById(id); if (!b) { b = el("div", "sevbox"); b.id = id; b.style.cssText = "margin-top:8px;padding:8px 10px;border:1px solid var(--line);border-radius:10px;font-size:13px"; d.appendChild(b); } return b; };
  const c = box("Clap switch", "sev-clap");
  if (c) { if (!c.dataset.b) { c.dataset.b = 1; const tx = el("div", "", ""); tx.id = "sev-clap-t"; const row = el("div", "btns");
      const b2 = el("button", "sec", "🔔 " + t("Test beep")); b2.type = "button"; b2.onclick = () => post("/api/soundev", {action: "test_beep", n: 2, lang: LANG});
      row.appendChild(b2); c.append(tx, row); }
    const big = V.counting ? "👏 ".repeat(Math.min(6, V.counting)) : "";
    $("#sev-clap-t").textContent = !V.mic ? t("no microphone selected (Microphone)") : !V.clap_on ? t("off") + " – " + t("switch on and clap 2× to try it")
      : (big ? big + " " + t("counting") + " " + V.counting + "×" : "👂 " + t("listening") + " – " + t("clap 2, 3 or 4 times"))
        + (V.last_n ? " · " + t("last") + ": " + V.last_n + "× → " + (V.last_act ? t(V.last_act) : "–") : ""); }
  const n = box("Bless you", "sev-sn");
  if (n) { if (!n.dataset.b) { n.dataset.b = 1; const tx = el("div", "", ""); tx.id = "sev-sn-t"; const row = el("div", "btns");
      const bt = el("button", "sec", "🔊 " + t("Hear the answer")); bt.type = "button"; bt.onclick = async () => { const r = await post("/api/soundev", {action: "test_reply", lang: LANG}); if (!r.ok) toast(r.error || "⚠"); };
      const bi = el("button", "", "📦 " + t("Install")); bi.type = "button"; bi.id = "sev-inst"; bi.onclick = async () => { bi.disabled = true; const r = await post("/api/soundev", {action: "install", lang: LANG}); if (!r.ok) toast(r.error || "⚠"); };
      const up = document.createElement("input"); up.type = "file"; up.accept = "audio/*,.m4a,.mp3,.wav"; up.hidden = true;
      const bu = el("button", "sec", "🎙 " + t("Own answer (sound file)")); bu.type = "button"; bu.onclick = () => up.click();
      up.onchange = async () => { const f = up.files && up.files[0]; if (!f) return; bu.disabled = true;
        const r = await fetch("/api/soundev/upload?lang=" + LANG, {method: "POST", body: f}).then(x => x.json()).catch(() => ({ok: false}));
        bu.disabled = false; up.value = ""; toast(r.ok ? "✓ " + t("saved and chosen as answer") + ": " + r.name : "⚠ " + (r.error || t("not possible")));
        if (r.ok) setTimeout(() => location.reload(), 1200); };
      row.append(bt, bu, bi, up); n.append(tx, row, el("div", "mut", t("sn-note"))); }
    const M = {ready: "👂 " + t("listening"), downloading: "⏳ " + t("loading the sound recognition …"), off: "👂 " + t("waiting for the first loud sound"),
      "no runtime": "⚠ " + t("needs the sound recognition program - button «Install»"), "download failed": "⚠ " + t("model could not be loaded"), error: "⚠ " + t("error")};
    $("#sev-sn-t").textContent = !V.mic ? t("no microphone selected (Microphone)") : (!V.sneeze_on ? t("off") : (V.install === "running" ? "⏳ " + t("installing … (a few minutes)") : (M[V.model] || V.model)))
      + (V.sneeze_score != null && V.sneeze_on ? " · " + t("last check") + ": " + Math.round(100 * V.sneeze_score) + " %" : "")
      + " · 🤧 " + t("today") + ": " + V.sneezes_today + "×" + (!V.tts ? " · " + t("no speech program (sudo apt install libttspico-utils)") : "");
    $("#sev-inst").hidden = V.runtime || V.install === "done"; $("#sev-inst").disabled = V.install === "running"; }
}
function simPiPaint(P) {
  const b = $("#sim-pi"); if (!b || !P) return; b.hidden = !P.possible; if (!P.possible) return;
  const key = [P.on, P.loading, P.pct, P.msg, P.version].join("|"); if (b.dataset.k === key) return; b.dataset.k = key; b.textContent = "";
  const bt = el("button", P.on ? "sec" : "", P.on ? "⏹ " + t("Stop the 3D simulator on the Pi") : "🍓 " + t("3D simulator on this Pi (HDMI / TV)"));
  bt.type = "button"; bt.style.width = "100%"; bt.disabled = P.loading;
  bt.onclick = async () => { bt.disabled = true; const r = await post("/api/sim", {action: P.on ? "pi_stop" : "pi_start", lang: LANG}); if (!r.ok) toast("⚠ " + (r.error || t("error"))); };
  b.append(bt, el("div", "mut", P.loading ? "⏳ " + t("loading") + " " + P.pct + " % (" + P.version + ")" : (P.msg ? "⚠ " + t(P.msg) : t("sim-pi-hint"))));
}
function simPaint(s) {
  simPiPaint(s.sim_pi);
  const spl = $("#sim-plan"); if (spl) spl.hidden = !((s.sim || {}).on && (s.sim || {}).ok);
  const srb = $("#sim-replay"), srs = $("#sim-replay-sel"), AT = s.alarm_tracks || [];
  if (srb) { srb.hidden = !(spl && !spl.hidden); const k = AT.map(a => a.id + a.n).join(",");
    if (srs && srs.dataset.k !== k) { srs.dataset.k = k; const cur = srs.value; srs.textContent = "";
      if (!AT.length) { const o = document.createElement("option"); o.value = ""; o.textContent = t("no alarms yet"); srs.appendChild(o); }
      AT.forEach(a => { const o = document.createElement("option"); o.value = a.id; o.textContent = new Date(a.t * 1000).toLocaleString([], {day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"}) + " · " + t(a.kind) + " · " + a.sec + " s" + (a.sim ? " · " + t("Simulator") : ""); srs.appendChild(o); });
      if ([...srs.options].some(o => o.value === cur)) srs.value = cur; } }
  const S = s.sim || {}, st = $("#sim-st"), b = $("#sim-btn"); document.body.classList.toggle("sim-on", !!S.on);
  if ($("#sim-inst")) { $("#sim-inst").textContent = "📦 " + t(S.installed ? "Install simulator again" : "Install simulator on the Pi");
    $("#sim-start").hidden = !!S.running; $("#sim-stop").hidden = !S.running; }
  if (b) b.textContent = S.on ? "⏹ " + t("Switch the simulation off") : "🧪 " + t("Switch the simulation on");
  const vb = $("#sim-vbox"); if (vb) { const vis = !!S.ok; if (vis && (vb.hidden || !vb.dataset.loaded)) { vb.dataset.loaded = "1"; window.simCtl && window.simCtl(); } vb.hidden = !vis; }
  const hd = $("#sim-head"), T = S.stats || {};
  if (hd) hd.textContent = !S.on ? "⚪ " + t("Simulation off") : (S.ok ? "🟢 " + (T.name || t("connected")) : "🔴 " + t("Simulator not reachable"));
  const sg = $("#sim-stats");
  if (sg) { const tile = (k, v) => '<div style="border:1px solid var(--line);border-radius:10px;padding:6px 8px"><div class="mut" style="font-size:11px">' + k + '</div><div style="font-weight:600">' + v + '</div></div>';
    const dur = n => n == null ? "–" : n < 60 ? n + " s" : n < 3600 ? Math.floor(n / 60) + " min" : Math.floor(n / 3600) + " h " + Math.floor(n % 3600 / 60) + " min";
    sg.hidden = !S.on;
    sg.innerHTML = tile(t("Connected for"), dur(T.since)) + tile(t("Response time"), T.rtt == null ? "–" : T.rtt + " ms") + tile(t("Camera pictures/s"), T.cam_fps == null ? "–" : T.cam_fps)
      + tile(t("Thermal pictures/s"), T.th_fps == null ? "–" : T.th_fps) + tile(t("Messages sent"), T.sent || 0) + tile(t("Sensor events"), T.events || 0) + tile(t("Errors"), T.errs || 0); }
  const sc = $("#sim-scan"), SC = S.scan || {};
  if (sc) { const ago = SC.t ? Math.round(Date.now() / 1000 - SC.t) : null;
    sc.textContent = SC.running ? "⏳ " + t("Searching") + " " + SC.net + " … " + Math.round(100 * (SC.done || 0) / Math.max(1, SC.hosts || 1)) + " % · " + (SC.found || 0) + " " + t("found")
      : (SC.t ? t("Last search") + ": " + (ago < 60 ? ago + " s" : Math.round(ago / 60) + " min") + " · " + SC.hosts + " " + t("addresses in") + " " + SC.secs + " s · " + SC.found + " " + t("found") + " (" + SC.net + ")"
        : t("Simulators announce themselves every 2 s. «Search now» also asks every address of the network.")); }
  const fb = $("#sim-found");
  if (fb) { const F = S.found || [], sig = JSON.stringify(F.map(x => [x.ip, x.port, x.name, x.host, x.count, x.ms, x.age > 5])) + S.url;
    if (fb.dataset.sig !== sig) { fb.dataset.sig = sig; fb.textContent = "";
      if (!F.length) fb.appendChild(el("div", "mut", t("No simulator announces itself in the network right now.")));
      fb.appendChild(el("div", "mut", t("sim-missing"))).style.marginTop = "6px";
      F.forEach(x => { const r = el("div"); r.style.cssText = "display:flex;align-items:center;gap:10px;padding:8px;border:1px solid var(--line);border-radius:10px;margin-top:6px";
        const cur = S.url === "http://" + x.ip + ":" + x.port;
        const info = el("div"); info.style.flex = "1";
        info.append(el("div", "", (cur ? "✅ " : "🖥 ") + x.name + (x.host ? "  ·  💻 " + x.host : "")), el("div", "mut", x.ip + ":" + x.port + (x.ip === "127.0.0.1" ? " · " + t("this device") : "") + (x.version ? " · v" + x.version : "")));
        const f = new Date((x.first || x.t) * 1000);
        info.appendChild(el("div", "mut", t("seen since") + " " + (("0" + f.getHours()).slice(-2) + ":" + ("0" + f.getMinutes()).slice(-2)) + " · " + t("last") + " " + x.age + " s · "
          + (x.count ? x.count + " " + t("messages") : t("found by the search")) + (x.ms != null ? " · " + x.ms + " ms" : "")));
        info.lastChild.style.fontSize = "12px"; r.appendChild(info);
        if (!cur) { const u = el("button", "sec", t("Use")); u.type = "button"; u.onclick = async () => { await post("/api/sim", {action: "use", ip: x.ip, port: x.port, lang: LANG}); refresh(); }; r.appendChild(u); }
        fb.appendChild(r); }); } }
  if (st) st.textContent = (!S.on ? t("off - the real cameras and sensors are used") + " · " + S.url : (S.ok ? S.url + " · " + (S.dark ? t("night") : t("day")) + " · " + S.ambient + " °C" : t(S.msg || "not reachable") + " · " + S.url))
    + (S.running ? "\n▶ " + t("the simulator runs on this Pi") : "");
  const bs = $("#b-sim"); if (bs) { bs.hidden = !S.on; const nv = S.on && S.versions && S.versions.newer;
    const pcc = S.on && S.ok && S.stats && S.stats.pc_cpu != null ? " · PC " + Math.round(S.stats.pc_cpu) + " %" : "";
    bs.textContent = "🧪 " + t("SIMULATION") + (S.on && !S.ok ? " ⚠" : "") + pcc + (nv ? " · ⟳ " + t("Update") + " " + S.versions.latest : "");
    bs.title = nv ? t("New update for the simulator") + ": " + S.versions.latest + " – " + t("tab Simulator") : ""; }
}
function gpsExtras(d) {
  const box = el("div", "auxbox"); const st = el("div", "mut"); st.id = "gpsm-st"; st.style.whiteSpace = "pre-wrap";
  box.append(el("div", "mut", t("A USB GPS receiver (e.g. u-blox, VK-162) is found by itself. It needs a view of the sky. With an LTE stick the position arrives also when the device is stolen.")), st);
  d.appendChild(box);
}
function gpsText(c, g) {
  if (!c.gpsmod_on) return t("off");
  const L = [];
  if (g.lat != null && g.age != null && g.age < 300) L.push("🛰️ " + g.lat.toFixed(5) + ", " + g.lon.toFixed(5) + (g.sats != null ? " · " + g.sats + " " + t("satellites") : "") + " · " + (g.via || ""));
  else L.push("🛰️ " + t(g.status || "off") + (g.sats != null ? " (" + g.sats + " " + t("satellites") + ")" : "") + (g.via ? " · " + g.via : ""));
  if (c.gps_theft) L.push(g.theft ? "🚨 " + t("THEFT ALARM") + (g.dist != null ? " · " + g.dist + " m" : "") : g.anchor ? "🔒 " + t("Theft tracking on guard") + (g.dist != null ? " · " + g.dist + " m" : "") : "🔓 " + t("Theft tracking starts when armed"));
  return L.join("\n");
}
function gpsPaint(c, s) { const st = $("#gpsm-st"); if (st && s.gpsmod) st.textContent = gpsText(c, s.gpsmod); }
function stormPaint(c, s) { const st = $("#storm-st"); if (st && s.storm) st.textContent = stormText(c, s.storm); }
function tpPaint(s) {
  const st = $("#tp-st"); if (!st || !s.tamper) return;
  st.textContent = "🧭 " + t("Motion sensor") + ": " + (s.tamper.sensor ? t("found") : t("not fitted")) + " · 📷 " +
    t({learning: "learning the picture", watching: "on guard"}[s.tamper.state] || s.tamper.state || "–") + (s.tamper.last ? " · ⚠ " + s.tamper.last : "");
}
// ---- backup: status + test ----
function bkExtras(d) {
  const box = el("div", "auxbox");
  box.appendChild(el("div", "mut", t("Finished alarm recordings are copied away from the device - if it is stolen or broken, the clips are safe.")));
  const st = el("div", "mut"); st.id = "bk-st"; const bt = el("div", "btns"), b = el("button", "sec", "🧪 " + t("Test the backup")); b.type = "button";
  b.onclick = async () => { b.disabled = true; st.textContent = "…"; const r = await post("/api/backup", {action: "test", lang: LANG});
    st.textContent = r.ok ? "✓ " + t("Test file copied - the settings work.") : "⚠ " + (r.error || "error"); b.disabled = false; };
  bt.appendChild(b); box.append(bt, st); d.appendChild(box);
}
function updExtras(d) {
  const box = el("div", "auxbox");
  const b = el("div", "btns"); const c = el("button", "sec", "🔄 " + t("Search versions")); c.type = "button"; c.onclick = () => updLoad(true);
  b.appendChild(c);
  const st = el("div", "mut", ""); st.id = "upd-st"; const L = el("div"); L.id = "upd-list";
  box.append(b, st, L);
  d.appendChild(box);
  setTimeout(() => updLoad(false), 500);
}
async function updLoad(check) {
  const st = $("#upd-st"); if (st && check) st.textContent = t("Searching …");
  let j;
  if (check) j = await post("/api/update", {action: "check", lang: LANG});
  else { try { j = await (await fetch("/api/update", {cache: "no-store"})).json(); } catch (e) { return; } }
  updRender(j);
}
function updRender(j) {
  const st = $("#upd-st"), L = $("#upd-list"); if (!st) return;
  const dt = x => x && x.length >= 10 ? x.slice(8, 10) + "." + x.slice(5, 7) + "." + x.slice(0, 4) + (x.length > 10 ? " " + x.slice(11, 16) : "") : (x || "");
  st.textContent = (j.error ? "⚠ " + j.error + " · " : "") + t("Running now") + ": " + j.current + (j.source ? "" : " · " + t("No update source set yet (see above)"))
    + (j.checked ? " · " + t("searched at") + " " + j.checked : "") + (j.list_time ? " · " + t("list from") + " " + dt(j.list_time) : "");
  L.textContent = "";
  (j.items || []).forEach(it => {
    const row = el("div", "updrow"), top = el("div", "row");
    const name = el("b", "", it.version); const tag = el("span", "mut", it.current ? "✓ " + t("running now") : (it.installed ? t("on the Pi") : t("available")));
    if (it.date) tag.textContent += " · " + dt(it.date);
    const okInst = it.installed || it.signed || j.unsigned_ok;
    if (it.available && !it.installed) tag.textContent += it.signed ? " · 🔏 " + t("signed") : " · ⚠ " + t("not signed");
    const left = el("span"); left.append(name, el("span", "", "  "), tag);
    top.appendChild(left);
    if (!it.current && okInst) {
      const newer = j.newer && j.newer.includes(it.version);
      const bt = el("button", newer ? "" : "sec", newer ? t("Update") : (it.installed ? t("Switch") : t("Install"))); bt.type = "button"; bt.style.padding = "4px 12px";
      bt.onclick = async () => {
        if (!confirm(t("Switch to version") + " " + it.version + "?\n\n" + t("The program restarts (about 20 seconds). Settings, recordings and zones stay."))) return;
        bt.disabled = true; st.textContent = t("Downloading and checking …");
        const r = await updInstall(it.version);
        if (!r.ok) { st.textContent = "⚠ " + (r.error || "error"); bt.disabled = false; return; }
      };
      top.appendChild(bt);
    }
    row.appendChild(top);
    if (it.notes) { const n = el("div", "mut", it.notes); n.style.fontSize = "12px"; row.appendChild(n); }
    L.appendChild(row);
  });
  // only about three versions visible, the rest scrolls
  updFit();
  if (window.ResizeObserver && !L._ro) { L._ro = new ResizeObserver(() => updFit()); L._ro.observe(L.parentNode); }
}
function updFit() {
  const L = $("#upd-list"); if (!L) return;
  const rows = L.children;
  if (rows.length <= 3) { L.style.maxHeight = ""; return; }
  const h = rows[3].getBoundingClientRect().top - rows[0].getBoundingClientRect().top;
  L.style.maxHeight = (h > 20 ? h + 2 : 260) + "px";
}
// update with a progress bar (2.95.30): download (real bytes), check, restart (as long as the last restarts took)
async function updInstall(v) {
  let ov = $("#pw-ov"); if (!ov) { ov = el("div"); ov.id = "pw-ov"; document.body.appendChild(ov); }
  ov.textContent = ""; const c = el("div", "card"); c.style.minWidth = "min(340px, 86vw)"; ov.appendChild(c);
  const ttl = el("div", "", t("Switching to version") + " " + v + " …"); ttl.style.cssText = "font-weight:700;margin:4px 0 12px";
  const tr_ = el("div"); tr_.style.cssText = "height:12px;border-radius:6px;background:var(--line);overflow:hidden";
  const fill = el("div"); fill.style.cssText = "height:100%;width:2%;background:var(--acc);border-radius:6px;transition:width .6s linear"; tr_.appendChild(fill);
  const ph = el("div", ""); ph.style.cssText = "display:flex;justify-content:space-between;gap:10px;margin-top:8px;font-size:14px";
  const pl = el("span"), pr = el("b"); ph.append(pl, pr);
  c.append(el("div", "", "🔄"), ttl, tr_, ph, el("div", "mut", t("The page reloads by itself.")));
  c.firstChild.style.fontSize = "40px";
  let est = 25, phase = "download", got = 0, size = 0, el0 = 0, tR = 0, done = false, best = 0, failed = false;
  const t0 = Date.now();
  const paint = () => {
    const now = Date.now(), elapsed = (now - t0) / 1000;
    let rem, lab;
    if (phase === "download") {
      const rate = el0 > 0.3 && got > 0 ? got / el0 : 150000;
      rem = (size > got ? (size - got) / rate : 1) + 2 + est;
      lab = "⬇ " + t("Downloading") + (size ? " " + (got / 1e6).toFixed(1) + " / " + (size / 1e6).toFixed(1) + " MB" : "");
    } else if (phase === "check") { rem = 2 + est; lab = "🔏 " + t("Checking the signature"); }
    else { const since = tR ? (now - tR) / 1000 : 0; rem = est - since; lab = "🔄 " + t("Restarting"); }
    let pct = elapsed / (elapsed + Math.max(rem, 1)); pct = Math.min(0.97, Math.max(best, pct)); best = pct;
    fill.style.width = (pct * 100).toFixed(1) + "%"; pl.textContent = lab;
    pr.textContent = rem > 1 ? t("Still about") + " " + Math.ceil(rem) + " s" : t("Takes longer than usual …");
  };
  const poll = async () => {
    if (done || failed) return;
    try {
      const r = await fetch("/api/version", {cache: "no-store"}); const j = await r.json();
      if (j.version === v) { done = true; best = 1; fill.style.width = "100%"; pl.textContent = "✓ " + t("Done"); pr.textContent = ""; setTimeout(() => location.reload(), 600); return; }
      if (j.est) est = j.est;
      const u = j.upd || {};
      if (u.phase) { phase = u.phase; got = u.got || 0; size = u.size || 0; el0 = u.el || 0; if (phase === "restart" && !tR) tR = Date.now() - (u.since || 0) * 1000; }
    } catch (e) { if (phase !== "restart") { phase = "restart"; if (!tR) tR = Date.now(); } }
    paint();
    if (Date.now() - t0 > (est + 180) * 1000) { pr.textContent = t("No answer from the Pi."); return; }
    setTimeout(poll, 800);
  };
  paint(); setTimeout(poll, 300);
  const r = await post("/api/update", {action: "install", version: v, lang: LANG});
  if (!r.ok) { failed = true; ov.remove(); }
  else if (!tR) { phase = "restart"; tR = Date.now(); }
  return r;
}
function updWait(v) {
  let ov = $("#pw-ov"); if (!ov) { ov = el("div"); ov.id = "pw-ov"; document.body.appendChild(ov); }
  ov.textContent = ""; const c = el("div", "card"); ov.appendChild(c);
  c.append(el("div", "", "🔄"), el("div", "", t("Switching to version") + " " + v + " …"), el("div", "mut", t("The page reloads by itself.")));
  c.firstChild.style.fontSize = "40px"; c.children[1].style.fontWeight = "700"; c.children[1].style.margin = "8px 0";
  const t0 = Date.now();
  const tick = async () => {
    try { const r = await fetch("/api/version", {cache: "no-store"}); const j = await r.json(); if (j.version === v) { location.reload(); return; } } catch (e) {}
    if (Date.now() - t0 > 180000) { c.lastChild.textContent = t("No answer from the Pi."); return; }
    setTimeout(tick, 2000);
  };
  setTimeout(tick, 4000);
}

// ---- shut down / restart the Pi ----
async function powerAct(action) {
  const q = action === "poweroff"
    ? t("Shut down the Raspberry Pi now?") + "\n\n" + t("A running recording is finished first. To switch it on again: unplug the power and plug it in again.")
    : t("Restart the Raspberry Pi now?");
  if (!confirm(q)) return;
  const r = await post("/api/power", {action: action, lang: LANG});
  if (!r.ok) { $("#pw-err").textContent = "⚠ " + (r.error || "error"); return; }
  $("#pw-err").textContent = "";
  powerOverlay(action);
}
async function pauseAct() {
  const sel = $("#pause-min"), lbl = sel.options[sel.selectedIndex].text;
  if (!confirm(t("Switch the program off now and start it again in") + " " + lbl + "?\n\n" + t("While paused there is no monitoring and there are no alarms."))) return;
  const r = await post("/api/pause", {minutes: Number(sel.value), lang: LANG});
  if (!r.ok) { $("#pw-err").textContent = "⚠ " + (r.error || "error"); return; }
  listenStop(); toast(t("Program is pausing …"));
  setTimeout(() => location.reload(), 4000);
}
function powerOverlay(action) {
  listenStop();
  let ov = $("#pw-ov"); if (!ov) { ov = el("div"); ov.id = "pw-ov"; document.body.appendChild(ov); }
  ov.textContent = ""; const c = el("div", "card"); ov.appendChild(c);
  const ic = el("div", "", action === "poweroff" ? "⏻" : "↻"); ic.style.fontSize = "42px";
  const msg = el("div", "", action === "poweroff" ? t("The Pi is shutting down …") : t("The Pi is restarting …"));
  msg.style.fontWeight = "700"; msg.style.fontSize = "18px"; msg.style.margin = "8px 0";
  const sub = el("div", "mut", t("Finishing the recording, saving the settings …"));
  c.append(ic, msg, sub);
  const close = () => { const b = el("button", "sec", t("Close")); b.style.marginTop = "14px"; b.onclick = () => ov.remove(); c.appendChild(b); };
  const t0 = Date.now(); let down = 0, wasDown = false;
  const tick = async () => {
    let ok = false;
    try {
      const ctl = window.AbortController ? new AbortController() : null; if (ctl) setTimeout(() => ctl.abort(), 2500);
      const r = await fetch("/api/state", {cache: "no-store", signal: ctl ? ctl.signal : undefined}); ok = r.ok;
      if (ok && !wasDown) {
        const j = await r.json();
        if (j.state && j.state.power_msg && !j.state.power) { ic.textContent = "⚠"; msg.textContent = t("The Pi was not shut down"); sub.textContent = j.state.power_msg; close(); return; }
      }
    } catch (e) { ok = false; }
    if (ok) down = 0; else { down++; wasDown = true; }
    if (action === "poweroff" && wasDown && ok) { location.reload(); return; }        // switched on again: back to the page
    if (action === "poweroff" && down >= 2) {
      ic.textContent = "✓"; msg.textContent = t("The Pi is off");
      sub.textContent = t("Wait until the green LED of the Pi stays dark (about 10 seconds), then you can unplug the power. To start it again: unplug the power and plug it in again.");
      if (!c.querySelector("button")) close();
      setTimeout(tick, 5000); return;                                                    // keep looking: the page comes back by itself
    }
    if (action === "reboot" && wasDown && ok) { location.reload(); return; }
    if (action === "reboot" && wasDown) sub.textContent = t("Waiting for the Pi … the page reloads by itself (about 1 minute).");
    if (action === "reboot" && Date.now() - t0 > 300000) { sub.textContent = t("No answer from the Pi."); close(); return; }
    setTimeout(tick, 2000);
  };
  setTimeout(tick, 3500);
}

// ---- timelapse + thermal camera: status, buttons, latest photo, videos ----
const TLTXT = () => ({"off": t("off"), "waiting: alarm has priority": t("waiting: alarm has priority"), "waiting: manual control": t("waiting: manual control"),
  "moving to the photo position": t("moving to the photo position"), "photo saved": t("photo saved"), "connected": t("connected"),
  "connecting…": t("connecting…"), "no thermal camera selected": t("no thermal camera selected"),
  "same camera as the main picture": t("same camera as the main picture"), "connection lost - reconnecting": t("connection lost - reconnecting")});
function tlTxt(s) {
  if (!s) return "";
  let m = /^next photo in (\d+) min$/.exec(s); if (m) return t("next photo in") + " " + m[1] + " min";
  m = /^making video (\d+)\/(\d+)$/.exec(s); if (m) return t("making video") + " " + m[1] + "/" + m[2];
  if (s.startsWith("video ready: ")) return t("video ready") + ": " + s.slice(12);
  m = /^taken from the phone (.*)$/.exec(s); if (m) return t("taken from the phone") + " " + m[1];
  if (s === "ok") return t("correct");
  if (s.startsWith("ok · time zone ")) return t("correct") + " · " + t("time zone") + " " + s.slice(15);
  return TLTXT()[s] || s;
}
let tlSeen = null;
function fmtDay(d) { return d.slice(6, 8) + "." + d.slice(4, 6) + "." + d.slice(0, 4); }
async function tlLoad() {
  let j; try { j = await (await fetch("/api/timelapse")).json(); } catch (e) { return; }
  const img = $("#tl-img"); if (!img) return;
  if (j.latest) { img.src = "/timelapse/" + j.latest; img.hidden = false; $("#tl-open").href = "/timelapse/" + j.latest; } else { img.hidden = true; }
  const cnt = $("#tl-count"); cnt.textContent = j.count + " " + t("photos");
  const sel = $("#tl-day"), keep = sel.value; sel.textContent = "";
  const all = el("option", "", t("All days")); all.value = ""; sel.appendChild(all);
  j.days.forEach(x => { const o = el("option", "", fmtDay(x.day) + " (" + x.count + ")"); o.value = x.day; sel.appendChild(o); });
  sel.value = keep;
  const L = $("#tl-videos"); L.textContent = "";
  j.videos.forEach(v => {
    const row = el("div", "row"); row.style.marginTop = "4px";
    const a = el("a", "", v.name); a.href = "/timelapse/" + v.name; a.target = "_blank"; a.style.color = "var(--acc2)"; a.style.wordBreak = "break-all";
    const dl = el("a", "", "⬇"); dl.href = "/timelapse/" + v.name + "?dl=1"; dl.title = t("Download"); dl.style.color = "var(--acc2)";
    const x = el("button", "sec", "✕"); x.style.padding = "2px 8px"; x.title = t("Remove");
    x.onclick = async () => { if (confirm(t("Remove this video?"))) { await post("/api/timelapse", {action: "delete_video", name: v.name}); tlLoad(); } };
    row.append(a, dl, x); L.appendChild(row);
  });
}
function tlExtras(d) {
  const st = el("div", "mut", ""); st.id = "tl-status"; st.style.margin = "6px 0";
  const btns = el("div", "btns");
  const mk = (txt, fn, cls) => { const b = el("button", cls || "sec", t(txt)); b.type = "button"; b.onclick = fn; return b; };
  btns.append(
    mk("Use current position", async () => { await post("/api/timelapse", {action: "here"}); toast(t("Saved")); }),
    mk("Show position", () => post("/api/timelapse", {action: "goto"})),
    mk("Photo now", async () => { await post("/api/timelapse", {action: "now"}); toast(t("Photo requested")); }));
  const img = el("img"); img.id = "tl-img"; img.hidden = true; img.alt = "latest timelapse photo";
  img.style.cssText = "width:100%;border-radius:10px;margin-top:8px;border:1px solid var(--line)";
  const open = el("a", ""); open.id = "tl-open"; open.target = "_blank"; open.appendChild(img);
  const cnt = el("div", "mut", ""); cnt.id = "tl-count";
  const vrow = el("div", "row"); vrow.style.marginTop = "10px";
  const sel = el("select"); sel.id = "tl-day"; sel.style.flex = "1";
  const mkv = mk("Create video", async () => {
    const r = await post("/api/timelapse", {action: "render", day: sel.value, lang: LANG});
    if (!r.ok) toast("⚠ " + (r.error || "error"));
  }, "");
  vrow.append(sel, mkv);
  const rs = el("div", "mut", ""); rs.id = "tl-render"; rs.style.marginTop = "4px";
  const vl = el("div", ""); vl.id = "tl-videos";
  d.append(st, btns, open, cnt, vrow, rs, vl);
  tlLoad(); setInterval(tlLoad, 30000);
}
function thExtras(d) {
  const st = el("div", "mut", ""); st.id = "th-status"; st.style.margin = "6px 0";
  const hint = el("div", "mut", t("The thermal camera must look in the same direction as the main camera. Choose it in the list after a camera scan (Video source).")); hint.style.marginTop = "4px";
  // three parts: alarm / picture / camera & alignment
  const parts = [["th:alarm", "🚨 " + t("Alarm"), ["thermal_alarm", "thermal_need_motion", "thermal_delta", "thermal_min_area"]],
                 ["th:view", "🎨 " + t("Picture"), ["thermal_on", "thermal_hot", "thermal_map", "thermal_alpha", "thermal_hot_pct"]],
                 ["th:cam", "📷 " + t("Camera and alignment"), ["thermal_source", "thermal_zoom", "thermal_dx", "thermal_dy"]]];
  const rowOf = k => d.querySelector(':scope > [data-key="' + k + '"]');
  parts.forEach(([view, title, keys]) => {
    const S = el("details", "sub thsub"); S.dataset.view = view; S.appendChild(el("summary", "", title));
    keys.forEach(k => { const r = rowOf(k); if (r) S.appendChild(r); });
    if (view === "th:cam") S.append(st, hint);
    if (S.children.length > 1) d.appendChild(S);
  });
}
// ---- Wi-Fi / hotspot card: search, connect, save, forget ----
let WF = null, wfOpenSsid = null, wfPoll = null, wfLost = false;
function wfBars(n) { const b = el("span", "wbars"); for (let i = 1; i <= 4; i++) b.appendChild(el("i", i <= n ? "on" : "")); return b; }
function wfErr(m) { const e = $("#wf-err"); e.textContent = m ? "⚠ " + m : ""; }
async function wfLoad() {
  let j;
  try { j = await (await fetch("/api/wifi")).json(); wfLost = false; }
  catch (e) {
    if (WF && WF.busy) { wfLost = true; wfRenderStatus(); }
    return;
  }
  WF = j; wfRender();
  if (!j.busy && wfPoll) { clearInterval(wfPoll); wfPoll = null; }
}
async function wfPost(body) {
  body.lang = LANG; wfErr("");
  let r;
  try { r = await post("/api/wifi", body); } catch (e) { r = {ok: false, error: "connection"}; }
  if (r && r.backend !== undefined) { WF = r; wfRender(); }
  if (!r.ok) wfErr(r.error || "error");
  return r;
}
function wfRenderStatus() {
  const st = $("#wf-status"); if (!st || !WF) return;
  st.textContent = "";
  if (!WF.backend) { st.textContent = t("Wi-Fi management is not available on this system (NetworkManager or wpa_supplicant missing)."); return; }
  const line1 = el("div", "", WF.connected ? t("Connected with") + " «" + (WF.ssid || "?") + "»" + (WF.ip ? " · IP " + WF.ip : "") : t("not connected"));
  line1.style.fontWeight = "600"; line1.style.color = "var(--txt)";
  st.appendChild(line1);
  if (WF.address) {
    const a = el("div", ""); a.append(document.createTextNode(t("Page address") + ": "));
    const l1 = el("a", "", WF.address); l1.href = WF.address; l1.style.color = "var(--acc2)";
    const alt = (WF.https ? "https" : "http") + "://" + WF.local_name + ":" + WF.port + "/";
    const l2 = el("a", "", alt); l2.href = alt; l2.style.color = "var(--acc2)";
    a.append(l1, document.createTextNode(" · " + t("or") + " "), l2); st.appendChild(a);
  }
  if (WF.job) {
    const j = el("div", WF.job_ok === false ? "err" : "", wfJobText(WF.job)); j.style.marginTop = "4px";
    if (WF.job_ok === true) j.style.color = "var(--grn)";
    st.appendChild(j);
  }
  if (wfLost) {
    const w = el("div", "err", t("The connection to this page was interrupted - normal while the Pi changes the network. Open the page in the new network:")
      + " " + (WF.https ? "https" : "http") + "://" + WF.local_name + ":" + WF.port + "/ " + t("(or the address from the push message)."));
    w.style.marginTop = "6px"; st.appendChild(w);
  }
}
function wfJobText(s) {
  let m = /^connecting to (.*)…$/.exec(s); if (m) return t("connecting to") + " " + m[1] + " …";
  m = /^connected to (.*)$/.exec(s); if (m) return "✓ " + t("connected to") + " " + m[1];
  m = /^failed: (.*)$/.exec(s); if (m) return t("failed") + ": " + m[1].replace(" - back on ", " - " + t("back on") + " ");
  return s;
}
function wfForm(ssid0, secure, savedId, nameInput) {
  const f = el("div", "wf-form");
  const name = () => nameInput ? nameInput.value.trim() : ssid0;
  let pw = null;
  if (secure) {
    const r = el("div", "row"); r.style.gap = "6px";
    pw = el("input"); pw.type = "password"; pw.placeholder = savedId ? t("Password (empty = keep the saved one)") : t("Password"); pw.autocomplete = "off";
    pw.style.flex = "1"; pw.style.minWidth = "0";
    const eye = el("button", "sec", "👁"); eye.type = "button"; eye.style.padding = "4px 9px"; eye.title = t("show password");
    eye.onclick = () => { pw.type = pw.type === "password" ? "text" : "password"; };
    r.append(pw, eye); f.appendChild(r);
  }
  const pr = el("label", "row"); pr.style.marginTop = "6px";
  const cb = el("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = true;
  pr.append(el("span", "mut", t("prefer this network (before other known networks)")), cb); f.appendChild(pr);
  const b = el("div", "btns");
  const go = el("button", "", t("Connect now")); go.type = "button";
  go.onclick = async () => {
    const ssid = name(); if (!ssid) { wfErr(t("Network name (SSID)") + "?"); return; }
    const msg = t("The Pi now switches to the network") + " «" + ssid + "». " + t("This page will probably lose its connection. Afterwards open it in that network at") + " "
      + (WF.https ? "https" : "http") + "://" + WF.local_name + ":" + WF.port + "/ " + t("or with the address from the push message. If it does not work, the Pi returns to the previous network after about a minute.");
    if (!confirm(msg)) return;
    const r = await wfPost({action: "connect", ssid: ssid, password: pw ? pw.value : "", preferred: cb.checked});
    if (r.ok) { wfOpenSsid = null; if (!wfPoll) wfPoll = setInterval(wfLoad, 2000); }
  };
  const sv = el("button", "sec", t("Only save (connects automatically)")); sv.type = "button";
  sv.onclick = async () => { const ssid = name(); if (!ssid) { wfErr(t("Network name (SSID)") + "?"); return; }
    const r = await wfPost({action: "save", ssid: ssid, password: pw ? pw.value : "", preferred: cb.checked}); if (r.ok) { toast(t("Saved")); wfOpenSsid = null; wfRender(); } };
  b.append(go, sv); f.appendChild(b);
  if (savedId) {
    const fg = el("button", "sec", t("Forget network")); fg.type = "button"; fg.style.marginTop = "6px"; fg.style.width = "100%";
    fg.onclick = async () => { if (confirm(t("Forget this network?") + " «" + name() + "»")) { await wfPost({action: "forget", id: savedId}); wfOpenSsid = null; wfRender(); } };
    f.appendChild(fg);
  }
  return f;
}
function wfRender() {
  wfRenderStatus();
  if (!WF) return;
  const L = $("#wf-list"), S = $("#wf-saved");
  const ae = document.activeElement;
  if (ae && ae.tagName === "INPUT" && (L.contains(ae) || S.contains(ae))) return;     // do not disturb typing
  L.textContent = ""; S.textContent = "";
  const savedBy = {}; (WF.saved || []).forEach(s => savedBy[s.ssid] = s);
  if (!WF.scan.length) L.appendChild(el("div", "mut", WF.scan_time ? t("no networks found") : t("Press 'Search networks'. Switch on the hotspot of the phone first.")));
  WF.scan.forEach(n => {
    const it = el("div", "wf-item" + (n.active ? " on" : ""));
    const head = el("div", "wf-head");
    head.append(wfBars(n.bars), el("b", "", n.ssid));
    if (n.secure) head.appendChild(el("span", "mut", "🔒"));
    const tags = el("span", "wf-tags");
    if (n.active) tags.appendChild(el("span", "badge grn", t("connected")));
    else if (savedBy[n.ssid]) tags.appendChild(el("span", "badge", t("saved")));
    tags.appendChild(el("span", "mut", n.signal + " %"));
    head.appendChild(tags);
    head.onclick = () => { wfOpenSsid = wfOpenSsid === n.ssid ? null : n.ssid; wfRender(); };
    it.appendChild(head);
    if (wfOpenSsid === n.ssid && !n.active) it.appendChild(wfForm(n.ssid, n.secure, (savedBy[n.ssid] || {}).id));
    if (wfOpenSsid === n.ssid && n.active) it.appendChild(el("div", "mut", t("The Pi is connected with this network.")));
    L.appendChild(it);
  });
  const other = el("button", "sec", t("Other / hidden network …")); other.type = "button"; other.style.marginTop = "8px"; other.style.width = "100%";
  other.onclick = () => { wfOpenSsid = wfOpenSsid === "\u0000other" ? null : "\u0000other"; wfRender(); };
  L.appendChild(other);
  if (wfOpenSsid === "\u0000other") {
    const box = el("div", "wf-item"); const nm = el("input"); nm.type = "text"; nm.placeholder = t("Network name (SSID)"); nm.style.width = "100%";
    box.appendChild(nm);
    box.appendChild(wfForm("", true, null, nm)); L.appendChild(box);
  }
  if (!(WF.saved || []).length) S.appendChild(el("div", "mut", t("none")));
  (WF.saved || []).sort((a, b) => b.prio - a.prio).forEach(s => {
    const r = el("div", "row wf-saved");
    const left = el("span", ""); left.append(el("b", "", s.ssid), document.createTextNode(s.active ? " · " + t("connected") : ""), el("span", "mut", (s.prio > 0 ? " · " + t("preferred") : "") + (s.auto ? "" : " · " + t("no auto connect"))));
    const x = el("button", "sec", "✕"); x.type = "button"; x.title = t("Forget network"); x.style.padding = "3px 9px";
    x.onclick = async () => { if (confirm(t("Forget this network?") + " «" + s.ssid + "»" + (s.active ? "\n" + t("The Pi is connected with it right now - the page may lose its connection.") : ""))) await wfPost({action: "forget", id: s.id}); };
    r.append(left, x); S.appendChild(r);
  });
}

$("#wf-scan").onclick = async () => {
  const b = $("#wf-scan"); b.disabled = true; b.textContent = t("Searching …");
  await wfPost({action: "scan"});
  b.disabled = false; b.textContent = t("Search networks");
};
$("#wf-card").addEventListener("toggle", () => { if ($("#wf-card").open) wfLoad(); });
setInterval(() => { if ($("#wf-card").open && !document.hidden) wfLoad(); }, 10000);
setTimeout(() => { if ($("#wf-card").open) wfLoad(); }, 1500);

// ---- camping / protection card + header badge ----
let PR = {campUntil: 0, hsUntil: 0};
function prText(s) {                                       // 2.98.0: one name for the state everywhere: Aus / Wachsam / Voll
  const lv = ((s.protect || {}).level === "full" || (s.protect || {}).chosen === "full") ? t("Full protection") : t("Watchful");
  if ((s.protect || {}).walk && (s.arm_state === "armed" || s.arm_state === "arming")) return ["🚶 " + t("Walk test"), "yel"];   // 2.98.15: no alarms meanwhile
  if (s.arm_state === "armed") return ["🛡 " + lv, "grn"];
  if (s.arm_state === "arming") return ["🛡 " + lv + " " + t("in") + " " + s.arm_left + " s", "yel"];
  return ["🛡 " + t("Off"), ""];
}
async function prArm(action) {
  if (action === "disarm" && ((window.__lastState || {}).protect || {}).pin) { protectOff(); return; }   // 2.95.105: with the PIN
  const r = await post("/api/arm", {action: action, lang: LANG});
  if (r && r.ok) toast((action === "disarm" ? t("Disarmed") : (r.left ? t("Armed in") + " " + r.left + " s" : t("Armed"))) + (r.forecast ? " · 🔋 " + r.forecast : ""));
}
function prHotspotMsg(r) {
  return t("The Pi now switches on its own Wi-Fi") + " «" + r.ssid + "» (" + t("password") + ": " + r.password + "). "
    + t("This page loses its connection. Connect the phone to") + " «" + r.ssid + "» " + t("and open") + " " + r.address;
}
async function prCamp(on) {
  const s = window.__lastState || {};
  if (on) {
    const hc = s.hotspot_cfg || {};
    const msg = t("Camping profile") + ":\n- " + t("own Wi-Fi") + " «" + hc.ssid + "» (" + t("password") + ": " + hc.password + ")\n- "
      + t("the camera stays where it is (no patrol, tracking or timelapse)") + "\n- " + t("alarms and recordings on") + "\n- "
      + t("armed after the countdown") + "\n\n" + t("This page loses its connection. Connect the phone to") + " «" + hc.ssid + "» " + t("and open") + " " + hc.address;
    if (!confirm(msg)) { $("#pr-camp").checked = false; return; }
  } else if (s.hotspot && s.hotspot.on && !confirm(t("End camping? The own Wi-Fi is switched off again - this page loses its connection and the Pi goes back to the known networks."))) { $("#pr-camp").checked = true; return; }
  PR.campUntil = Date.now() + 2500; PR.hsUntil = Date.now() + 2500;
  const r = await post("/api/camping", {on: on, lang: LANG});
  if (!r.ok) { $("#pr-err").textContent = "⚠ " + (r.error || "error"); return; }
  toast(on ? "⛺ " + t("Camping profile ON") : t("Camping profile OFF"));
}
async function prHotspot(on) {
  const s = window.__lastState || {}, hc = s.hotspot_cfg || {};
  if (on && !confirm(prHotspotMsg(hc))) { $("#pr-hs").checked = false; return; }
  if (!on && !confirm(t("Switch the own Wi-Fi off? This page loses its connection; the Pi goes back to the known networks."))) { $("#pr-hs").checked = true; return; }
  PR.hsUntil = Date.now() + 2500;
  const r = await post("/api/hotspot", {on: on, lang: LANG});
  if (!r.ok) { $("#pr-err").textContent = "⚠ " + (r.error || "error"); $("#pr-hs").checked = !on; }
}
// «Team gegen MoveEye» (2.95.22): the guards sit here - turn the camera with the joystick and press «Erwischt!»
// ---- iPhone shortcuts (2.95.27): keywords in the messages, e-mail as trigger, addresses back to MoveEye ----
function scPick() {
  const d = document.querySelector('details[data-view="sec:Notifications"]');
  if (!d || d.querySelector("#scbox")) return;
  const box = el("div"); box.id = "scbox"; box.style.cssText = "margin-top:10px;padding:10px 12px;border:1px solid var(--line);border-radius:12px;font-size:14px";
  d.appendChild(box);
  const paint = j => { box.innerHTML = "";
    box.appendChild(el("div", "", "📲 " + t("iPhone shortcuts")));
    box.appendChild(el("div", "mut", t("sc-intro"))).style.margin = "4px 0 8px";
    const kw = el("div"); kw.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px";
    Object.entries(j.keywords || {}).forEach(([k, v]) => { const c = el("code", "", v); c.title = t({person: "person", warm: "warm body", noise: "noise", tamper: "sabotage", prealarm: "pre-alarm", info: "info", test: "test"}[k] || k);
      c.style.cssText = "padding:2px 8px;border:1px solid var(--line);border-radius:999px;font-size:12px"; kw.appendChild(c); });
    box.appendChild(kw);
    const ol = el("ol"); ol.style.cssText = "margin:0 0 8px;padding-left:20px;line-height:1.5";
    ["sc-1", "sc-2", "sc-3", "sc-4", "sc-5"].forEach(k => ol.appendChild(el("li", "", t(k)))); box.appendChild(ol);
    const h = el("div", "", "↩ " + t("Addresses back to MoveEye (for «Get contents of URL»)")); h.style.cssText = "font-weight:600;margin-top:6px"; box.appendChild(h);
    if (!j.on) { box.appendChild(el("div", "mut", t("sc-key-off")));
      const b = el("button", "", "🔑 " + t("Make a shortcut key")); b.type = "button"; b.onclick = async () => paint(await post("/api/shortcut", {action: "new"})); box.appendChild(b); return; }
    [["arm", "Arm"], ["disarm", "Disarm"], ["siren_off", "Siren off"], ["light_on", "White light on"], ["light_off", "White light off"],
     ["photo.jpg", "Photo now"], ["status", "Status (text)"]].forEach(([a, n]) => { const u = j.base + "/k/" + j.key + "/" + a;
      const r = el("div"); r.style.cssText = "display:flex;gap:8px;align-items:center;margin:4px 0";
      const c = el("button", "sec", "📋"); c.type = "button"; c.title = t("Copy"); c.onclick = () => { try { navigator.clipboard.writeText(u); toast("✓ " + t("copied")); } catch (e) { prompt(t(n), u); } };
      const lab = el("span", "", t(n)); lab.style.minWidth = "140px"; const cd = el("code", "mut", u.replace(j.key, "•••")); cd.style.cssText = "font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1";
      r.append(c, qrBtn(u, t(n), {secret: true}), lab, cd); box.appendChild(r); });
    box.appendChild(el("div", "mut", t("sc-key-note"))).style.marginTop = "6px";
    const row = el("div", "btns"); row.style.marginTop = "6px";
    const nb = el("button", "sec", "🔄 " + t("New key")); nb.type = "button"; nb.onclick = async () => { if (confirm(t("Make a new key? The old addresses stop working."))) paint(await post("/api/shortcut", {action: "new"})); };
    const ob = el("button", "sec", "⛔ " + t("Switch off")); ob.type = "button"; ob.onclick = async () => paint(await post("/api/shortcut", {action: "off"}));
    row.append(nb, ob); box.appendChild(row); };
  fetch("/api/shortcut").then(r => r.json()).then(paint).catch(() => {});
}
// ---- app icon (2.95.23): choose it here; on an iPhone / iPad the home screen keeps the old one - a hint says what to do ----
function iconPick() {
  const d = document.querySelector('details[data-view="sec:Setup"]') || document.querySelector('details[data-view="sec:Web stream"]');
  if (!d || d.querySelector("#appicon")) return;
  const box = el("div"); box.id = "appicon"; box.style.cssText = "margin-top:10px;padding:10px 12px;border:1px solid var(--line);border-radius:12px";
  box.appendChild(el("div", "", "📱 " + t("App icon")));
  const row = el("div"); row.style.cssText = "display:flex;flex-wrap:wrap;gap:10px;margin:8px 0";
  const note = el("div", "mut", ""); note.style.fontSize = "13px";
  const paint = cur => row.querySelectorAll("button").forEach(b => { const on = b.dataset.i === cur; b.style.outline = on ? "3px solid var(--acc,#3b8cff)" : "none"; b.setAttribute("aria-pressed", on); });
  fetch("/api/appicon").then(r => r.json()).then(j => {
    (j.list || []).forEach(x => { const b = el("button", "sec"); b.type = "button"; b.dataset.i = x.id; b.title = t(x.name);
      b.style.cssText = "padding:6px;border-radius:16px;display:flex;flex-direction:column;align-items:center;gap:4px;width:92px;font-size:11px;line-height:1.2";
      const im = document.createElement("img"); im.src = "/app-icon/" + x.id + ".png?s=128"; im.alt = ""; im.width = 64; im.height = 64; im.style.borderRadius = "14px";
      b.append(im, el("span", "", t(x.name)));
      b.onclick = async () => { const r = await post("/api/appicon", {icon: x.id}); if (!r.ok) { toast("⚠ " + t(r.error || "error")); return; }
        paint(x.id); window.MW_ICON = x.id; toast("✓ " + t("App icon changed"));
        const l = document.querySelector('link[rel="icon"]'); if (l) l.href = "/icon-192.png?i=" + x.id;
        AN.list = r.animated || AN.list; hdrIcon(x.id); iconHint(true); };
      row.appendChild(b); });
    paint(j.icon); AN.on = j.anim; AN.list = j.animated || []; cb.checked = !!j.anim; });
  const AN = {on: true, list: []};
  const hdrIcon = id => document.documentElement.style.setProperty("--mw-icon", AN.on && AN.list.includes(id) ? "url(/app-icon/anim.svg?i=" + id + ")" : "url(/icon-192.png?i=" + id + ")");
  const lb = el("label", "opt"); lb.style.cssText = "display:flex;align-items:center;justify-content:space-between;gap:10px;margin:4px 0 8px";
  const cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "sw";
  cb.onchange = async () => { AN.on = cb.checked; await post("/api/appicon", {anim: cb.checked}); hdrIcon(window.MW_ICON || "radar"); };
  lb.append(el("span", "", t("Let the radar turn (in the header; the home screen icon cannot move)")), cb);
  note.textContent = t("icon-note");
  box.append(row, lb, note); d.appendChild(box);
}
function iconHint(force) {
  const standalone = navigator.standalone || (window.matchMedia && matchMedia("(display-mode: standalone)").matches);
  const ios = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  let seen = null; try { seen = localStorage.getItem("mw-icon-home"); } catch (e) {}
  const cur = window.MW_ICON || "radar";
  if (!standalone && !force) return;
  if (!ios) { try { localStorage.setItem("mw-icon-home", cur); } catch (e) {} return; }     // Android: Chrome renews the icon by itself
  if (seen === cur || (!force && seen === null && cur === "classic")) return;
  if (!standalone) return;
  let h = $("#iconhint"); if (h) h.remove();
  h = el("div"); h.id = "iconhint";
  h.style.cssText = "position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:90;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px;box-shadow:0 6px 24px rgba(0,0,0,.4);font-size:14px;display:flex;gap:12px;align-items:center";
  const im = document.createElement("img"); im.src = "/app-icon/" + cur + ".png?s=128"; im.width = 48; im.height = 48; im.alt = ""; im.style.borderRadius = "11px";
  const tx = el("div", "", t("ios-icon-hint")); tx.style.flex = "1";
  const ok = el("button", "", t("Done")); ok.type = "button"; ok.onclick = () => { try { localStorage.setItem("mw-icon-home", cur); } catch (e) {} h.remove(); };
  const later = el("button", "sec", t("Later")); later.type = "button"; later.onclick = () => h.remove();
  const bx = el("div"); bx.style.cssText = "display:flex;flex-direction:column;gap:6px"; bx.append(ok, later);
  h.append(im, tx, bx); document.body.appendChild(h);
}
setTimeout(() => iconHint(false), 2500);
function mwgPaint(s) {
  const G = (s.sim || {}).game, on = !!(G && G.mode === "mwhand" && (G.round === "play" || G.round === "countdown"));
  let b = $("#mwg");
  if (!on) { if (b) b.hidden = true; return; }
  if (!b) { b = el("div"); b.id = "mwg"; b.innerHTML = '<div id="mwg-t"></div><button type="button" id="mwg-b">🚨 <span></span></button>'; document.body.appendChild(b);
    const st = document.createElement("style"); st.textContent = "#mwg{position:fixed;left:50%;bottom:calc(14px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:80;display:flex;align-items:center;gap:10px;background:rgba(10,14,20,.88);border:1px solid var(--line);border-radius:999px;padding:6px 6px 6px 14px;box-shadow:0 4px 18px rgba(0,0,0,.45);color:#fff;font-size:13px;max-width:calc(100vw - 24px);width:max-content}#mwg-t{flex:1;min-width:0;line-height:1.3}@media(max-width:520px){#mwg{width:calc(100vw - 24px);border-radius:16px}}#mwg-b{flex:none;background:#e5383b;border:0;color:#fff;font-weight:700;font-size:16px;padding:10px 18px;border-radius:999px}#mwg-b:disabled{opacity:.5}";
    document.head.appendChild(st);
    $("#mwg-b").onclick = async () => { const r = await post("/api/sim", {action: "game_mwcatch", lang: LANG}); toast(r.ok ? (r.text || "") : "⚠ " + (r.error || t("error"))); };
    // 2.95.74: the hunter aims - a tap on a player in the live picture (the head camera) is a shot at exactly this spot
    const v = $("#video"); let down = null;
    v.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY, Date.now()]; });
    v.addEventListener("pointerup", async e => {
      const b_ = $("#mwg"); if (!b_ || b_.hidden || !down || $("#mwg-b").disabled) return;
      const [x0, y0, t0] = down; down = null;
      if (Math.hypot(e.clientX - x0, e.clientY - y0) > 12 || Date.now() - t0 > 600) return;      // a drag, not a tap
      const r_ = v.getBoundingClientRect(), nw = v.naturalWidth || 16, nh = v.naturalHeight || 9;
      const sc = Math.min(r_.width / nw, r_.height / nh), w = nw * sc, h = nh * sc;
      const x = (e.clientX - r_.left - (r_.width - w) / 2) / w, y = (e.clientY - r_.top - (r_.height - h) / 2) / h;
      if (x < 0 || x > 1 || y < 0 || y > 1) return;
      const m = el("div", "mwg-shot"); m.style.left = e.clientX + "px"; m.style.top = e.clientY + "px"; document.body.appendChild(m);
      setTimeout(() => m.remove(), 900);
      const q = await post("/api/sim", {action: "game_mwcatch", x: x, y: y, lang: LANG});
      m.classList.add(q.hit ? "hit" : "miss");
      toast(q.ok ? (q.text || "") : "⚠ " + (q.error || t("error")));
    });
    const st2 = document.createElement("style");
    st2.textContent = ".mwg-shot{position:fixed;z-index:85;width:64px;height:64px;margin:-32px 0 0 -32px;border:3px solid #ff3b30;border-radius:50%;pointer-events:none;animation:mwgs .5s ease-in forwards}"
      + ".mwg-shot::before,.mwg-shot::after{content:'';position:absolute;left:50%;top:-10px;width:2px;height:80px;margin-left:-1px;background:#ff3b30}.mwg-shot::after{transform:rotate(90deg)}"
      + ".mwg-shot.hit{border-color:#3fcf6b;box-shadow:0 0 16px #3fcf6b}.mwg-shot.miss{opacity:.4}@keyframes mwgs{0%{transform:scale(1.8);opacity:0}100%{transform:scale(.6);opacity:1}}";
    document.head.appendChild(st2); }
  b.hidden = false;
  const w = (G.mwg || {}).wait || 0;
  $("#mwg-t").textContent = "🕹 " + (G.round === "countdown" ? t("Get ready") + " " + (G.cd || "") : t("You are the guard: turn the camera and tap the players in the picture")) + " · " + ((G.mwg || {}).catches || 0) + "× ✓ · " + ((G.mwg || {}).false || 0) + "× ✗";
  $("#mwg-b").disabled = G.round !== "play" || w > 0; $("#mwg-b span").textContent = w > 0 ? w + " s" : t("Caught!");
}
// ---- 2.95.96: shoot / trigger into the simulation from the live picture (outside «Team gegen MoveEye» too) ----
const SHOOT = {on: false, hits: 0, miss: 0, vis: null, io: null};
function simShootPaint(s) {
  const S_ = s.sim || {}, G = S_.game, mwhand = !!(G && G.mode === "mwhand" && (G.round === "play" || G.round === "countdown"));
  const live = !!(S_.on && S_.ok && S_.pic !== false) && String(((QSJ && QSJ.cfg) || {}).source || "sim:").startsWith("sim:");
  let b = $("#mws");
  // 2.96.9: only while the live picture can be seen, and «off» is just a small round button at the side (it covered the settings)
  if (!SHOOT.io && $("#video") && window.IntersectionObserver) { SHOOT.io = new IntersectionObserver(es => { SHOOT.vis = es[0].isIntersecting; simShootPaint(QSJ ? QSJ.state : s); }, {threshold: 0.25}); SHOOT.io.observe($("#video")); }
  if (!live || mwhand || (!SHOOT.on && SHOOT.vis === false)) { if (b) b.hidden = true; return; }
  if (!b) {
    b = el("div"); b.id = "mws"; b.innerHTML = '<button type="button" id="mws-b">🎯 <span></span></button><span id="mws-t"></span>'; document.body.appendChild(b);
    const st = document.createElement("style");
    st.textContent = "#mws{position:fixed;left:50%;bottom:calc(14px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:79;display:flex;align-items:center;gap:10px;background:rgba(10,14,20,.88);border:1px solid var(--line);border-radius:999px;padding:6px 14px 6px 6px;box-shadow:0 4px 18px rgba(0,0,0,.45);color:#fff;font-size:13px;max-width:calc(100vw - 24px)}"
      + "#mws[hidden]{display:none}#mws:not(.on){left:auto;right:12px;transform:none;padding:4px;bottom:calc(84px + env(safe-area-inset-bottom,0px))}#mws:not(.on) #mws-b span{display:none}#mws button{border-radius:999px;padding:8px 14px;font-weight:700;background:var(--panel2,#1a2433);color:#fff;border:1px solid var(--line)}#mws.on button{background:#ff3b30;border-color:#ff3b30}#mws:not(.on) #mws-t{display:none}"
      + ".mwg-shot{position:fixed;z-index:85;width:64px;height:64px;margin:-32px 0 0 -32px;border:3px solid #ff3b30;border-radius:50%;pointer-events:none;animation:mwgs .5s ease-in forwards}"
      + ".mwg-shot::before,.mwg-shot::after{content:'';position:absolute;left:50%;top:-10px;width:2px;height:80px;margin-left:-1px;background:#ff3b30}.mwg-shot::after{transform:rotate(90deg)}"
      + ".mwg-shot.hit{border-color:#3fcf6b;box-shadow:0 0 16px #3fcf6b}.mwg-shot.miss{opacity:.4}@keyframes mwgs{0%{transform:scale(1.8);opacity:0}100%{transform:scale(.6);opacity:1}}";
    document.head.appendChild(st);
    $("#mws-b").onclick = () => { SHOOT.on = !SHOOT.on; simShootPaint(QSJ ? QSJ.state : s); toast(SHOOT.on ? "🎯 " + t("Tap into the live picture to shoot - a miss is marked as a false alarm") : t("Shooting off")); };
    const v = $("#video"); let down = null;
    v.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY, Date.now()]; });
    v.addEventListener("pointerup", async e => {
      const b_ = $("#mws"); if (!SHOOT.on || !b_ || b_.hidden || !down) return;
      const [x0, y0, t0] = down; down = null;
      if (Math.hypot(e.clientX - x0, e.clientY - y0) > 12 || Date.now() - t0 > 600) return;      // a drag, not a tap
      const r_ = v.getBoundingClientRect(), nw = v.naturalWidth || 16, nh = v.naturalHeight || 9;
      const sc = Math.min(r_.width / nw, r_.height / nh), w = nw * sc, h = nh * sc;
      const x = (e.clientX - r_.left - (r_.width - w) / 2) / w, y = (e.clientY - r_.top - (r_.height - h) / 2) / h;
      if (x < 0 || x > 1 || y < 0 || y > 1) return;
      const m = el("div", "mwg-shot"); m.style.left = e.clientX + "px"; m.style.top = e.clientY + "px"; document.body.appendChild(m);
      setTimeout(() => m.remove(), 900);
      const q = await post("/api/sim", {action: "shoot", x: x, y: y, lang: LANG});
      m.classList.add(q.hit ? "hit" : "miss");
      if (q.ok) { q.hit ? SHOOT.hits++ : SHOOT.miss++; }
      toast(q.ok ? (q.text || "") : "⚠ " + (q.error || t("error")));
      simShootPaint(QSJ ? QSJ.state : s);
    });
  }
  b.hidden = false; b.classList.toggle("on", SHOOT.on);
  $("#mws-b span").textContent = SHOOT.on ? t("Shooting on") + " · ✕" : t("Shoot");
  $("#mws-b").title = SHOOT.on ? t("Shooting off") : t("Shoot");
  $("#mws-t").textContent = t("Tap the picture") + " · " + SHOOT.hits + "× ✓ · " + SHOOT.miss + "× ✗ " + t("false alarm");
}
Object.assign(I18N.de, {"Training set for an own AI model (YOLO)": "Trainingspaket für ein eigenes KI-Modell (YOLO)", "pictures": "Bilder", "The simulator makes the pictures and saves a ZIP on the desktop of its PC (about 2 s per picture).": "Der Simulator macht die Bilder und legt ein ZIP auf den Schreibtisch seines PCs (etwa 2 s pro Bild)."});
Object.assign(I18N.de, {"Reference scan": "Referenz-Scan", "Open the assistant": "Assistent öffnen", "refscan-note": "Der Kopf fährt ein Raster von Richtungen ab und speichert Fotos als Referenz. Später vergleicht MoveEye dieselben Richtungen und zeigt im Bericht, was fehlt, neu ist oder sich verändert hat."});
Object.assign(I18N.de, {"Shoot": "Schiessen", "Shooting on": "Schiessen an", "Shooting off": "Schiessen aus", "Tap the picture": "Ins Bild tippen", "false alarm": "Fehlalarm",
  "Tap into the live picture to shoot - a miss is marked as a false alarm": "Ins Livebild tippen zum Schiessen – daneben wird als Fehlalarm markiert"});
// ---- modes (2.95.47): camping guard, campfire games, gamer, home, wildlife, night guard, transport ----
Object.assign(I18N.de, {"Stop the TV mode of the simulator": "TV-Modus des Simulators beenden", "TV mode in the 3D simulator": "TV-Modus im 3D-Simulator"});
Object.assign(I18N.de, {"Aufstell-Planer in the simulator": "Aufstell-Planer im Simulator", "open in the window of the simulator": "im Fenster des Simulators geöffnet", "Take over the patrol of the planner": "Patrouille vom Planer übernehmen", "Patrol set": "Patrouille gesetzt", "of the area in view": "des Bereichs im Blick"});
Object.assign(I18N.de, {"Alarm replay in 3D": "Alarm-Rückblick in 3D", "Play in the simulator": "Im Simulator abspielen", "plays in the window of the simulator": "läuft im Fenster des Simulators", "no alarms yet": "noch keine Alarme", "replay-note": "Zeigt im 3D-Simulator nach, wer woher kam und wohin MoveEye geschaut hat (15 s vor bis 20 s nach dem Alarm). Hilft, Fehlalarme zu verstehen. Die Positionen sind geschätzt (aus Bildposition und Grösse)."});
Object.assign(I18N.en, {"replay-note": "Shows in the 3D simulator who came from where and where MoveEye looked (15 s before to 20 s after the alarm). Helps to understand false alarms. The positions are estimated (from the spot and size in the picture)."});
Object.assign(I18N.de, {"AI test with simulator pictures": "KI-Prüfung mit Simulator-Bildern", "dset-note": "Der Simulator macht Bilder mit Person oder Tier – bei Tag, Abend, Nacht mit Infrarot, Regen und Nebel, nah und fern – und weiss, wo sie sind. MoveEye lässt seine KI (oder die PC-Rechenhilfe) darüber laufen und zählt Treffer, Fehlschläge und falsche Personen. Dauert pro Bild etwa 3 Sekunden.", "Start the test": "Prüfung starten", "found": "erkannt", "false persons": "falsche Personen", "near (under 8 m)": "nah (unter 8 m)", "far (8 m and more)": "fern (ab 8 m)", "AI time per picture": "KI-Zeit pro Bild", "Training pictures (ZIP)": "Trainingsbilder (ZIP)", "Tag": "Tag", "Abend": "Abend", "Nacht (Infrarot)": "Nacht (Infrarot)", "Regen": "Regen", "Nebel": "Nebel", "Nacht + Regen": "Nacht + Regen", "person": "Person", "fox": "Fuchs", "deer": "Reh", "dog": "Hund", "cat": "Katze", "boar": "Wildschwein", "the simulator makes the pictures …": "der Simulator macht die Bilder …", "done": "fertig"});
Object.assign(I18N.en, {"dset-note": "The simulator makes pictures with a person or an animal - by day, dusk, night with infrared, rain and fog, near and far - and knows where they are. MoveEye runs its AI (or the PC helper) on them and counts hits, misses and false persons. About 3 seconds per picture.", "Tag": "day", "Abend": "dusk", "Nacht (Infrarot)": "night (infrared)", "Regen": "rain", "Nebel": "fog", "Nacht + Regen": "night + rain"});
Object.assign(I18N.en, {"sim-pi-hint": "Runs on the Pi with simple graphics and shows on the television at the HDMI. The first time it is fetched (about 30 MB)."});
Object.assign(I18N.de, {"Stop the 3D simulator on the Pi": "3D-Simulator auf dem Pi beenden", "3D simulator on this Pi (HDMI / TV)": "3D-Simulator auf diesem Pi (HDMI / Fernseher)", "loading": "lädt", "sim-pi-hint": "Läuft auf dem Pi mit einfacher Grafik und zeigt sich am Fernseher am HDMI. Beim ersten Mal wird er geholt (etwa 30 MB).", "only on a Raspberry Pi (64 bit)": "nur auf einem Raspberry Pi (64 Bit)"});
Object.assign(I18N.de, {"Loudspeaker": "Lautsprecher", "built-in / none": "eingebaut / keiner", "no Bluetooth": "kein Bluetooth", "Disco light": "Disco-Licht", "Stop": "Aus", "Start": "Los", "with the music (microphone)": "mit der Musik (Mikrofon)", "fixed tempo": "fester Takt", "needs the white light (Lights)": "braucht das weisse Licht (Licht)", "No microphone: the fixed tempo is used.": "Kein Mikrofon: dann gilt der feste Takt.", "disco-note": "Musik über die Bluetooth-Box oder ein Handy laufen lassen – das Mikrofon hört den Takt und das weisse Licht blitzt mit (höchstens 3-mal pro Sekunde; Vorsicht bei Menschen mit Epilepsie, Rücksicht auf Nachbarn). Ein Alarm geht immer vor. Endet nach 2 Stunden von selbst."});
Object.assign(I18N.en, {"disco-note": "Play music on the Bluetooth box or a phone - the microphone hears the beat and the white light flashes along (at most 3 times a second; careful with people with epilepsy, think of the neighbours). An alarm always comes first. Ends by itself after 2 hours."});
Object.assign(I18N.en, {"tv-auto": "In the campfire and gamer mode show it on the HDMI by itself (TV at the Pi). Any screen in the same network can open the link."});
Object.assign(I18N.de, {"TV view": "TV-Anzeige", "Stop on the HDMI": "Am HDMI beenden", "Show on the HDMI": "Am HDMI zeigen", "Open the link": "Link öffnen", "Copy the link": "Link kopieren", "Link copied": "Link kopiert", "tv-auto": "Beim Lagerfeuer- und Gamer-Modus von selbst am HDMI zeigen (Fernseher am Pi). Den Link kann jeder Bildschirm im gleichen Netz öffnen.", "no browser on this device (Chromium)": "kein Browser auf diesem Gerät (Chromium)", "no desktop on the HDMI (Raspberry Pi OS with desktop needed)": "kein Desktop am HDMI (Raspberry Pi OS mit Desktop nötig)"});
Object.assign(I18N.en, {"tether-hint": "Connect a phone with the USB cable. Android: Settings \u2192 Hotspot & tethering \u2192 \u00abUSB tethering\u00bb. iPhone: switch \u00abPersonal Hotspot\u00bb on and tap \u00abTrust\u00bb. MoveEye connects by itself - the own Wi-Fi (game network) gets internet too."});
Object.assign(I18N.de, {"Internet from the phone (USB cable)": "Internet vom Handy (USB-Kabel)", "phone found, connecting …": "Handy gefunden, verbinde …",
  "the own Wi-Fi gets this internet too": "das eigene WLAN bekommt dieses Internet auch",
  "tether-hint": "Handy per USB-Kabel anschliessen. Android: Einstellungen → Hotspot & Tethering → «USB-Tethering». iPhone: «Persönlicher Hotspot» einschalten und «Vertrauen» antippen. MoveEye verbindet von selbst – auch das eigene WLAN (Spiel-Netz) bekommt dann Internet."});
Object.assign(I18N.de, {"Mode": "Modus", "Camping": "Camping", "Campfire games": "Lagerfeuer-Spiele", "Gamer": "Gamer",
  "Home / garden": "Zuhause / Garten", "Wildlife watching": "Wildbeobachtung", "Transport / rest": "Transport / Ruhe",
  "Own settings": "Eigene Einstellungen", "no mode": "kein Modus", "since": "seit",
  "Your own settings, no mode.": "Deine eigenen Einstellungen, kein Modus.",
  "Full guard: alarms, recordings, own Wi-Fi, armed after the countdown. Power saving while all is quiet.": "Volle Wache: Alarme, Aufnahmen, eigenes WLAN, Schutz an nach dem Countdown. Stromsparen, solange alles ruhig ist.",
  "The game corner is open for the phones (in the Wi-Fi MoveEye is in). The guard watches on sparingly: few pictures, the AI only at movement - an animal at the tent is still reported. Back to camping at the set time or when the battery gets low.": "Die Spielecke ist offen für die Handys (im WLAN, in dem MoveEye ist). Die Wache schaut sparsam weiter: wenige Bilder, die KI nur bei Bewegung – ein Tier am Zelt wird trotzdem gemeldet. Zur eingestellten Zeit oder wenn der Akku knapp wird, zurück zum Camping.",
  "Only with mains power: power mode, all games and the game collection, the best picture. The guard only if you want it. On battery MoveEye goes back to the campfire games by itself.": "Nur mit Netzstrom: Powermodus, alle Spiele und die Spielesammlung, bestes Bild. Die Wache nur, wenn du willst. Auf Akku wechselt MoveEye von selbst zurück zu den Lagerfeuer-Spielen.",
  "Guarding house and garden: alarms and recordings on, no own Wi-Fi, no camping profile.": "Haus und Garten bewachen: Alarme und Aufnahmen ein, kein eigenes WLAN, kein Camping-Profil.",
  "Animals: no siren, the light does not go on by itself (it would scare them), many pictures, the camera follows what moves.": "Tiere: keine Sirene, das Licht geht nicht von selbst an (es würde sie verscheuchen), viele Bilder, die Kamera folgt dem, was sich bewegt.",
  "Rest while travelling: no detection, no recordings, no alarms - only the battery, GPS theft and tamper protection stay on.": "Ruhe unterwegs: keine Erkennung, keine Aufnahmen, keine Alarme – nur Akku, GPS-Diebstahlschutz und Sabotageschutz bleiben an.",
  "Back to camping at": "Zurück zum Camping um", "or below": "oder unter", "or battery below": "oder Akku unter", "battery": "Akku", "never": "nie",
  "Guard during the games": "Wache während der Spiele", "needs mains power": "braucht Netzstrom", "Mode switched": "Modus gewechselt",
  "runs on the battery": "läuft auf Akku", "under-voltage: the power supply is too weak": "Unterspannung: das Netzteil ist zu schwach"});
const MD = {built: 0, until: 0, hover: null};
function modePaint(s) {
  const M = s.mode, g = $("#mode-grid"); if (!M || !g) return;
  if (!document.getElementById("mode-css")) { const c = document.createElement("style"); c.id = "mode-css";
    c.textContent = ".mode-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:6px}.mode-grid button{padding:8px 2px;font-size:11.5px;line-height:1.15;overflow-wrap:anywhere;hyphens:auto;min-width:0;display:flex;flex-direction:column;align-items:center;gap:3px;min-height:64px}.mode-grid button .mi{font-size:22px}.mode-grid button.on{outline:3px solid var(--acc,#3b8cff);background:rgba(59,140,255,.18)}.mode-grid button.off{opacity:.45}#mode-opts .row{margin-top:6px}"
      + "#protect-box{margin:2px 0 14px}.prt-seg{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:8px}.prt-b{display:flex;flex-direction:column;align-items:center;gap:2px;padding:10px 4px;font-size:13px;font-weight:700;min-height:58px}.prt-b .ic{font-size:20px}.prt-b.on{outline:3px solid var(--acc,#3b8cff);background:rgba(59,140,255,.2)}"
      + ".prt-what{margin-top:6px}.prt-amp{margin-top:10px;padding:10px 12px;border-radius:12px;background:rgba(255,255,255,.04)}.prt-amp.green{border-left:4px solid #3fcf6b}.prt-amp.orange{border-left:4px solid #f2a33a}.prt-amp.red{border-left:4px solid #e5484d}.prt-it{margin-top:6px;gap:8px;font-size:13px}"
      + ".prt-dev{margin-top:8px;font-size:13px}.prt-things{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}.prt-th{display:flex;flex-direction:column;align-items:center;gap:3px;font-size:12px;max-width:92px}.prt-th.miss span{color:#ff6b6b;font-weight:700}"
      + ".prt-img{width:84px;height:60px;border-radius:8px;background:#222 no-repeat;border:2px solid #3fcf6b}.prt-th.miss .prt-img{border-color:#e5484d}.prt-test{margin-top:8px;font-size:13px;line-height:1.6}"
      + ".prt-wiz{position:fixed;inset:0;z-index:90;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;padding:16px}.prt-card{background:var(--card,#161b22);border-radius:16px;padding:18px;width:min(420px,100%);display:flex;flex-direction:column;gap:8px;animation:prtin .2s ease-out}.nws-card{width:min(520px,100%);max-height:86vh;overflow:auto}.nws-tag{font-size:12px;color:#f59a4a;letter-spacing:.08em;text-transform:uppercase}.nws-list{display:flex;flex-direction:column;gap:8px}.nws-it{display:flex;gap:10px;font-size:14px;line-height:1.35}.nws-it b{flex:0 0 auto;color:#3b8cff}.nws-next{font-size:13px;opacity:.85;display:flex;flex-direction:column;gap:3px}.nws-card h4{margin:6px 0 0}"
      + ".prt-opt{display:flex;align-items:center;gap:12px;padding:12px;font-size:15px;text-align:left}.prt-opt .ic{font-size:22px}.prt-opt.on{outline:2px solid var(--acc,#3b8cff)}@keyframes prtin{from{transform:scale(.95);opacity:0}to{transform:none;opacity:1}}";
    document.head.appendChild(c); }
  const all = M.list.concat([{id: "", icon: "⚙", name: "Own settings", info: M.own_info}]);
  if (MD.built !== all.length) { g.textContent = ""; MD.built = all.length;
    all.forEach(x => { const b = el("button", "sec"); b.type = "button"; b.dataset.m = x.id;
      const i = el("span", "mi", x.icon); const n = el("span", "", t(x.name)); b.append(i, n);
      b.onclick = () => modePick(x.id); b.onmouseenter = () => { MD.hover = x.id; modePaint(window.__lastState || s); }; b.onmouseleave = () => { MD.hover = null; modePaint(window.__lastState || s); };
      g.appendChild(b); }); }
  const cur = Date.now() < MD.until ? MD.want : M.id;
  g.querySelectorAll("button").forEach(b => { b.classList.toggle("on", b.dataset.m === cur); b.classList.toggle("off", b.dataset.m === "gamer" && !M.power_ok);
    if (b.dataset.m === "gamer") b.title = M.power_ok ? "" : t("needs mains power") + ": " + t(M.power_why); });
  const me = all.find(x => x.id === cur) || all[all.length - 1];
  $("#mode-cur").textContent = cur ? me.icon + " " + t(me.name) + (M.since ? " · " + t("since") + " " + new Date(M.since * 1000).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"}) : "") : t("no mode");
  const sh = (MD.hover !== null && all.find(x => x.id === MD.hover)) || me;
  $("#mode-info").textContent = t(sh.info) + (M.msg ? "  ·  " + t(M.msg) : "");
  const bm = $("#b-mode"); if (bm) { bm.hidden = !cur; bm.textContent = cur ? me.icon : ""; bm.title = t("Mode") + ": " + t(me.name); bm.onclick = () => { const c = $("#pr-card"); if (c) { c.open = true; c.scrollIntoView({behavior: "smooth"}); } }; }
  tvPaint(s.tv); discoPaint(s.disco); btqPoll(false);
  const bq = $("#btq"); if (bq && !bq.dataset.on) { bq.dataset.on = 1; bq.ontoggle = () => { if (bq.open) btqPoll(true); }; }
  const o = $("#mode-opts"); const key = cur + "|" + M.fire_until + "|" + M.fire_min_pct + "|" + M.gamer_watch + "|" + M.fire_persons;
  if (o.dataset.k === key) return; o.dataset.k = key; o.textContent = "";
  if (cur === "fire") {
    const r = el("div", "row"); r.append(el("span", "", t("Back to camping at")));
    const ti = document.createElement("input"); ti.type = "time"; ti.value = M.fire_until || ""; ti.style.width = "120px"; ti.style.flex = "none";
    ti.onchange = () => post("/api/mode", {mode_fire_until: ti.value});
    const sp = el("span", "", t("or battery below")); const se = document.createElement("select");
    [...new Set([0, 10, 20, 30, 40, 50, +M.fire_min_pct || 0])].sort((a, b) => a - b).forEach(v => { const op = document.createElement("option"); op.value = v; op.textContent = v ? v + " %" : t("never"); se.appendChild(op); });
    se.title = t("Also under Settings → Battery, next to the battery saver");      // 2.98.15: the two battery thresholds together
    se.value = String(M.fire_min_pct); se.onchange = () => post("/api/mode", {mode_fire_min_pct: +se.value});
    r.append(ti, sp, se); o.appendChild(r);
    const r2 = el("label", "row pr-sw"); const c2 = document.createElement("input"); c2.type = "checkbox"; c2.className = "sw"; c2.checked = !!M.fire_persons;
    c2.onchange = () => post("/api/mode", {mode_fire_persons: c2.checked});
    r2.append(el("span", "", "🚶 " + t("Person alarms at the campfire (off: only animals - the people at the fire are not burglars)")), c2); o.appendChild(r2);
  } else if (cur === "gamer") {
    const r = el("label", "row pr-sw"); const cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!M.gamer_watch;
    cb.onchange = async () => { await post("/api/mode", {mode_gamer_watch: cb.checked}); if (M.id === "gamer") { await post("/api/mode", {mode: ""}); await post("/api/mode", {mode: "gamer"}); } };
    r.append(el("span", "", "👁 " + t("Guard during the games")), cb); o.appendChild(r);
  }
}
// 2.95.105: «Schutz» - one level instead of many switches, the traffic light, device protection, guarded things, assistant,
// test, PIN, escalation, presence
const PRT = {key: "", pinFor: "", until: 0};
function protectPaint(P) {
  const box = $("#protect-box"); if (!box || !P) return;
  const key = JSON.stringify([P.level, P.chosen, P.arm, P.colour, P.items, P.device, P.things, P.pin, P.presence, P.escalate.on, P.escalate.s, P.test, PRT.pinFor, LANG, P.forecast, P.walk]);
  if (key === PRT.key) { const c = $("#prt-left"); if (c) c.textContent = P.arm === "arming" ? t("starts in") + " " + P.left + " s" : (P.escalate.pending ? "🚨 " + t("siren in") + " " + P.escalate.pending + " s" : ""); return; }
  PRT.key = key; box.textContent = "";
  const head = el("div", "row"); head.style.cssText = "justify-content:space-between;align-items:center";
  head.append(el("b", "", "🛡 " + t("Protection")), el("span", "mut", "")); head.lastChild.id = "prt-left"; box.appendChild(head);
  const seg = el("div", "prt-seg");
  const walk = !!P.walk && P.level !== "off";          // 2.98.15: during the walk test the state is «Gehtest», not «Wachsam» / «Voll»
  [["off", "⚪", t("Off")], ["watch", "🟡", t("Watchful")], ["full", "🛡", t("Full protection")]].forEach(([k, ic, n]) => {
    if (walk && P.level === k) { ic = "🚶"; n = t("Walk test"); }
    const b = el("button", "prt-b" + (P.level === k ? " on" : " sec"), ""); b.type = "button"; b.append(el("span", "ic", ic), el("span", "", n));
    b.onclick = () => k === "off" ? protectOff() : protectLevel(k); seg.appendChild(b); });
  box.appendChild(seg);
  box.appendChild(el("div", "mut prt-what", walk ? "🚶 " + t("Walk test running: no alarms until it ends (afterwards the protection is as before).") : P.level === "off" ? t("prt-off") : (P.level === "watch" ? t("prt-watch") : t("prt-full"))));
  if (P.forecast) box.appendChild(el("div", "prt-what", "🔋 " + P.forecast));      // 2.98.13: battery forecast (066)
  if (PRT.pinFor) { const r = el("div", "row"); r.style.cssText = "gap:6px;margin-top:8px"; const i = document.createElement("input"); i.type = "password"; i.inputMode = "numeric";
    i.placeholder = "PIN"; i.style.flex = "1"; const ok = el("button", "", t("Switch off")); ok.type = "button"; const no = el("button", "sec", "✕"); no.type = "button";
    ok.onclick = async () => { const x = await post("/api/protect", {action: "level", level: "off", pin: i.value, lang: LANG}); if (x.ok) { PRT.pinFor = ""; toast("✓ " + t("Protection off")); } else toast("⚠ " + (x.error || t("error"))); PRT.key = ""; protectPaint(x.level ? x : P); };
    i.onkeydown = e => { if (e.key === "Enter") ok.click(); }; no.onclick = () => { PRT.pinFor = ""; PRT.key = ""; protectPaint(P); };
    r.append(i, ok, no); box.appendChild(r); setTimeout(() => i.focus(), 50); }
  const amp = el("div", "prt-amp " + P.colour);                // the traffic light
  const bad = (P.items || []).filter(x => !x.minor);
  amp.appendChild(el("div", "", (P.colour === "green" ? "🟢 " + t("All ready") : (P.colour === "red" ? "🔴 " : "🟠 ") + bad.length + " " + t("thing(s) missing"))));
  (P.items || []).forEach(x => { const r = el("div", "row prt-it"); r.appendChild(el("span", x.minor ? "mut" : "", (x.minor ? "• " : "⚠ ") + x.text)); r.firstChild.style.flex = "1";
    if (x.fix) { const f = el("button", "sec", t("Fix")); f.type = "button"; f.style.padding = "3px 10px"; f.onclick = () => protectFix(x.fix); r.appendChild(f); }
    amp.appendChild(r); });
  box.appendChild(amp);
  box.appendChild(el("div", "mut prt-dev", "🔒 " + t("Device protection") + ": " + P.device));
  if ((P.things || []).length) { const tg = el("div", "prt-things");
    P.things.forEach(x => { const c = el("div", "prt-th" + (x.missing ? " miss" : "")); const im = el("div", "prt-img");
      const [bx, by, bw, bh] = x.box; im.style.backgroundImage = "url(/refscan/file/" + x.dir + "/pos_" + String(x.pos).padStart(2, "0") + ".jpg)";
      im.style.backgroundSize = (100 / Math.max(0.05, bw)) + "% " + (100 / Math.max(0.05, bh)) + "%";
      im.style.backgroundPosition = (bw >= 1 ? 0 : bx / (1 - bw) * 100) + "% " + (bh >= 1 ? 0 : by / (1 - bh) * 100) + "%";
      c.append(im, el("span", "", (x.missing ? "⚠ " : "✓ ") + x.name)); tg.appendChild(c); });
    box.appendChild(tg); }
  const bs = el("div", "btns"); bs.style.marginTop = "8px";
  const as_ = el("button", "", "🧭 " + t("Protection assistant")); as_.type = "button"; as_.onclick = protectWizard;
  const ts = el("button", "sec", P.test.busy ? "⏳ " + t("Test runs …") : "🧪 " + t("Test the protection")); ts.type = "button"; ts.disabled = P.test.busy;
  ts.onclick = async () => { await post("/api/protect", {action: "test", lang: LANG}); PRT.key = ""; };
  const pn = el("button", "sec", "🔐 " + (P.pin ? t("Change PIN") : t("PIN for switching off"))); pn.type = "button"; pn.onclick = () => protectPin(P.pin);
  bs.append(as_, ts, pn); box.appendChild(bs);
  if ((P.test.steps || []).length) { const tl = el("div", "prt-test"); P.test.steps.forEach(x => tl.appendChild(el("div", "", (x.ok === true ? "✅ " : x.ok === false ? "❌ " : "➖ ") + x.name + (x.text ? " – " + x.text : ""))));
    box.appendChild(tl); }
  const more = document.createElement("details"); more.className = "more"; more.style.marginTop = "6px";
  const sm = document.createElement("summary"); sm.textContent = "⚙ " + t("More: siren delay, presence"); sm.style.cssText = "cursor:pointer;font-size:14px;color:var(--mut,#8a96a6)"; more.appendChild(sm);
  const e1 = el("label", "row pr-sw"); const c1 = document.createElement("input"); c1.type = "checkbox"; c1.className = "sw"; c1.checked = !!P.escalate.on;
  const sel = document.createElement("select"); [10, 20, 30, 60, 120].forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v + " s"; sel.appendChild(o); }); sel.value = String(P.escalate.s);
  c1.onchange = sel.onchange = () => post("/api/protect", {action: "escalate", on: c1.checked, s: +sel.value, lang: LANG});
  const sp1 = el("span", "", t("Siren when nobody switches off after")); e1.append(sp1, sel, c1); more.appendChild(e1);
  const e2 = el("label", "row pr-sw"); const c2 = document.createElement("input"); c2.type = "checkbox"; c2.className = "sw"; c2.checked = !!P.presence.on;
  c2.onchange = () => post("/api/protect", {action: "presence", on: c2.checked, lang: LANG});
  const sp2 = el("span", "", t("Automatic: on when my phone is gone") + (P.presence.devices ? (P.presence.here === true ? " · 🏠 " + t("here") : P.presence.here === false ? " · 🚶 " + t("away") : "") : " · " + t("choose the phone under Tools → Network")));
  e2.append(sp2, c2); more.appendChild(e2);
  // 2.98.15: one clear choice instead of two switches (auto-off at return / «Is it you?»)
  const e3 = el("div", "row"); e3.style.cssText = "gap:8px;flex-wrap:wrap;align-items:center"; e3.appendChild(el("span", "", t("When my phone comes back:")));
  const s3 = document.createElement("select"); s3.style.cssText = "flex:1;min-width:180px";
  PRES_BACK.forEach(([v, n]) => { const o = document.createElement("option"); o.value = v; o.textContent = t(n); s3.appendChild(o); }); s3.value = P.presence.back || "ask";
  s3.onchange = () => post("/api/protect", {action: "presence", back: s3.value, lang: LANG}); e3.appendChild(s3); more.appendChild(e3);
  box.appendChild(more);
}
async function protectLevel(k, answers) {
  const r = await post("/api/protect", {action: "level", level: k, answers: answers || null, lang: LANG});
  if (r.ok) toast("✓ " + (k === "full" ? t("Full protection") : t("Watchful")) + (r.arm === "arming" ? " – " + t("leave the area now") : "") + (r.forecast && k !== "off" ? " · 🔋 " + r.forecast : "")); else toast("⚠ " + (r.error || t("error")));
  PRT.key = ""; if (r.level) protectPaint(r);
}
function protectOff() {
  const P = (window.__lastState || {}).protect || {};
  if (P.pin) { PRT.pinFor = "off"; PRT.key = ""; protectPaint(P); return; }
  protectLevel("off");
}
function protectFix(f) {
  if (f === "push") post("/api/protect", {action: "fix_push", lang: LANG}).then(r => { PRT.key = ""; if (r.level) protectPaint(r); });
  else if (f === "refscan") location.href = "/tools#refscan";
  else if (f === "speaker") { const b = $("#btq"); if (b) { b.open = true; b.scrollIntoView({behavior: "smooth", block: "center"}); } }
  else if (f === "pin") protectPin(false);
  else if (f === "backup") { const q = $("#set-search") || document.querySelector("input[type=search]"); if (q) { q.value = "Backup"; q.dispatchEvent(new Event("input")); q.scrollIntoView({behavior: "smooth"}); } }
}
async function protectPin(has) {
  const old = has ? prompt(t("Current PIN")) : ""; if (has && old === null) return;
  const nw = prompt(t("New PIN (4 to 8 digits, empty = no PIN)")); if (nw === null) return;
  const r = await post("/api/protect", {action: "pin", new: nw, old: old, lang: LANG});
  toast(r.ok ? "✓ " + (nw ? t("PIN saved") : t("PIN removed")) : "⚠ " + (r.error || t("error"))); PRT.key = "";
}
async function newsCheck(force) {                    // 2.96.3: after an update - what is new, what comes next
  let r; try { r = await (await fetch("/api/news")).json(); } catch (e) { return; }
  if (!r || !(r.show || force) || document.querySelector(".nws")) return;
  const ov = el("div", "prt-wiz nws"), c = el("div", "prt-card nws-card"); ov.appendChild(c); document.body.appendChild(ov);
  c.append(el("div", "nws-tag", "MoveEye " + r.version), el("h3", "", "✨ " + t("New in this version")));
  const its = r.items.length ? r.items : [{v: r.version, t: t("No changes noted.")}];
  const ul = el("div", "nws-list"); its.forEach(x => { const d = el("div", "nws-it"); d.append(el("b", "", x.v), el("span", "", x.t)); ul.appendChild(d); }); c.appendChild(ul);
  if (r.next && r.next.length) { c.append(el("h4", "", "🔜 " + t("Next in the makeover") + " (" + r.done + "/" + r.total + ")"));
    const nx = el("div", "nws-next"); r.next.forEach(x => nx.appendChild(el("div", "", x.n + ". " + x.t))); c.appendChild(nx); }
  const ok = el("button", "", t("OK")); ok.type = "button"; ok.style.width = "100%";
  const off = el("button", "sec", t("Do not show any more")); off.type = "button";
  const close = (o) => { ov.remove(); post("/api/news", {seen: true, off: o}); };
  ok.onclick = () => close(false); off.onclick = () => close(true); ov.onclick = e => { if (e.target === ov) close(false); };
  c.append(ok, off);
}
setTimeout(newsCheck, 2500);
async function demoGo() {                             // 2.96.7: makeover 20
  const r = await post("/api/demo", {lang: LANG}); if (r.ok) location.href = "/kino"; else toast("⚠ " + (r.error || t("error")));
}
Object.assign(I18N.de, {"New in this version": "Neu in dieser Version", "Next in the makeover": "Als Nächstes im Makeover", "No changes noted.": "Keine Änderungen notiert.",
  "Do not show any more": "Nicht mehr anzeigen", "What is new?": "Was ist neu?", "Cinema mode": "Kino-Modus", "One-click demo": "Ein-Klick-Demo", "Cinema": "Kino", "Demo": "Demo"});

const PRES_BACK = [["off", "switch the protection off"], ["ask", "ask «Is it you?» (person alarms wait)"], ["none", "nothing (the protection stays on)"]];
function protectWizard() {                       // three questions, then everything is set
  const A = {what: "place", when: "now", react: "push", back: (((window.__lastState || {}).protect || {}).presence || {}).back || "ask"};
  const BQ = ["back", t("When my phone comes back?"), [["off", "⚪", t("switch the protection off")], ["ask", "❓", t("ask «Is it you?» (person alarms wait)")], ["none", "🛡", t("nothing (the protection stays on)")]]];
  const Q0 = [["what", t("What shall be protected?"), [["place", "⛺", t("The place / tent")], ["things", "🚲", t("Things like the bike")], ["device", "📷", t("The device itself")], ["all", "🛡", t("Everything")]]],
    ["when", t("When?"), [["now", "▶", t("Now")], ["night", "🌙", t("Tonight")], ["away", "🚶", t("While I am away")]]],
    ["react", t("How shall it react?"), [["push", "📱", t("Quietly: push message")], ["light", "💡", t("Light + push")], ["siren", "🚨", t("Light, push, then the siren")]]]];
  let i = 0, Q = Q0; const ov = el("div", "prt-wiz"); document.body.appendChild(ov);
  const show = () => { Q = A.when === "away" ? [Q0[0], Q0[1], BQ, Q0[2]] : Q0;   // 2.98.15: «while I am away» asks what happens at the return
    ov.textContent = ""; const c = el("div", "prt-card"); ov.appendChild(c);
    if (i < Q.length) { const [k, q, opts] = Q[i]; c.append(el("div", "mut", (i + 1) + " / " + Q.length), el("h3", "", q));
      opts.forEach(([v, ic, n]) => { const b = el("button", "prt-opt" + (A[k] === v ? " on" : ""), ""); b.type = "button"; b.append(el("span", "ic", ic), el("span", "", n));
        b.onclick = () => { A[k] = v; i++; show(); }; c.appendChild(b); });
    } else { const lv = A.react === "siren" || A.what === "all" ? "full" : "watch";
      c.append(el("h3", "", t("Ready")), el("p", "", (lv === "full" ? "🛡 " + t("Full protection") : "🟡 " + t("Watchful")) + " · " + t(A.when === "night" ? "Tonight" : A.when === "away" ? "While I am away" : "Now")));
      const go = el("button", "", "🛡 " + t("Switch on the protection")); go.type = "button"; go.style.width = "100%";
      go.onclick = () => { ov.remove(); if (A.when === "away") post("/api/protect", {action: "presence", on: true, back: A.back, lang: LANG});
        protectLevel(lv, {things: A.what === "things" || A.what === "all", device: A.what === "device" || A.what === "all", when: A.when === "night" ? "night" : "now", react: A.react}); };
      c.appendChild(go); }
    const x = el("button", "sec", i ? "‹ " + t("Back") : t("Cancel")); x.type = "button"; x.style.marginTop = "8px"; x.onclick = () => { if (i) { i--; show(); } else ov.remove(); }; c.appendChild(x); };
  show();
}
Object.assign(I18N.de, {"Protection": "Schutz", "Off": "Aus", "Watchful": "Wachsam", "Full protection": "Voll", "starts in": "startet in", "siren in": "Sirene in",
  "prt-off": "Keine Alarme. Antippen, was geschützt werden soll – oder den Schutz-Assistenten fragen.",
  "prt-watch": "Meldet Personen und Sabotage aufs Handy. Keine Sirene.",
  "prt-full": "Personen, bewachte Gegenstände, Sabotage, GPS-Ortung – und die Sirene, wenn niemand ausschaltet.",
  "Switch off": "Ausschalten", "Protection off": "Schutz aus", "All ready": "Alles bereit", "thing(s) missing": "Punkt(e) offen", "Fix": "Beheben",
  "Device protection": "Gerät", "Protection assistant": "Schutz-Assistent", "Test runs …": "Test läuft …", "Test the protection": "Schutz testen",
  "Change PIN": "PIN ändern", "PIN for switching off": "PIN zum Ausschalten", "More: siren delay, presence": "Mehr: Sirene, Abwesenheit",
  "Automatic: on when my phone is gone": "Automatisch an, wenn mein Handy weg ist", "When my phone comes back:": "Wenn mein Handy zurückkommt:",
  "When my phone comes back?": "Wenn mein Handy zurückkommt?", "switch the protection off": "Schutz ausschalten", "ask «Is it you?» (person alarms wait)": "fragen «Bist du's?» (Personen-Alarme warten)",
  "nothing (the protection stays on)": "nichts (der Schutz bleibt an)", "Walk test": "Gehtest", "Walk test running: no alarms until it ends (afterwards the protection is as before).": "Gehtest läuft: keine Alarme, bis er fertig ist (danach ist der Schutz wie vorher).",
  "Also under Settings → Battery, next to the battery saver": "Auch unter Einstellungen → Akku, neben dem Akku-Sparen",
  "Siren when nobody switches off after": "Sirene, wenn niemand ausschaltet, nach", "Automatic: on when my phone is gone, off when it is back": "Automatisch: an, wenn mein Handy weg ist, aus, wenn es zurück ist",
  "here": "da", "away": "weg", "choose the phone under Tools → Network": "Handy unter Werkzeuge → Netz wählen", "Current PIN": "Bisherige PIN",
  "New PIN (4 to 8 digits, empty = no PIN)": "Neue PIN (4 bis 8 Ziffern, leer = keine PIN)", "PIN saved": "PIN gespeichert", "PIN removed": "PIN entfernt",
  "What shall be protected?": "Was soll geschützt werden?", "The place / tent": "Der Platz / das Zelt", "Things like the bike": "Gegenstände wie das Velo",
  "The device itself": "Das Gerät selbst", "Everything": "Alles", "When?": "Wann?", "Now": "Jetzt", "Tonight": "Heute Nacht", "While I am away": "Solange ich weg bin",
  "How shall it react?": "Wie soll er reagieren?", "Quietly: push message": "Still: Push-Nachricht", "Light + push": "Licht + Push", "Light, push, then the siren": "Licht, Push, dann Sirene",
  "Ready": "Bereit", "Switch on the protection": "Schutz einschalten", "Back": "Zurück", "Cancel": "Abbrechen"});
Object.assign(I18N.en, {"prt-off": "No alarms. Tap what shall be protected - or ask the protection assistant.", "prt-watch": "Reports persons and sabotage to the phone. No siren.",
  "prt-full": "Persons, guarded things, sabotage, GPS tracking - and the siren when nobody switches off."});
// 2.95.105: the Bluetooth loudspeaker - small and quick to reach (under the modes): which one plays, connect / disconnect, search
let BTQ = {t: 0, busy: false};
async function btqPoll(force) {
  const sum = $("#btq-sum"); if (!sum) return;
  if (!force && Date.now() - BTQ.t < 20000) return; BTQ.t = Date.now();
  let j; try { j = await (await fetch("/api/bt", {cache: "no-store"})).json(); } catch (e) { return; }
  const cur = (j.devices || []).find(d => "bt:" + d.mac === j.out && d.connected);
  sum.textContent = "🔊 " + t("Loudspeaker") + ": " + (cur ? cur.name + " ✓" : (j.available ? t("built-in / none") : t("no Bluetooth")));
  const box = $("#btq-box"); if (!box || !$("#btq").open) return; box.textContent = "";
  if (!j.available) { box.appendChild(el("div", "mut", t("Bluetooth is not available (sudo apt install bluez)"))); return; }
  (j.devices || []).filter(d => d.audio || d.paired).forEach(d => {
    const r = el("div", "row"); r.style.cssText = "gap:6px;margin-top:6px";
    const used = "bt:" + d.mac === j.out && d.connected;
    r.appendChild(el("span", "", (used ? "✓ " : "• ") + d.name)); r.lastChild.style.flex = "1";
    const b = el("button", used ? "sec" : "", used ? t("Disconnect") : t("Connect")); b.type = "button"; b.style.padding = "4px 10px";
    b.onclick = async () => { b.disabled = true; b.textContent = "…"; const x = await post("/api/bt", {action: used ? "disconnect" : "connect", mac: d.mac, lang: LANG});
      if (!x.ok) toast("⚠ " + (x.error || t("error"))); else if (window.refreshEnums) refreshEnums(["audio_out"]); btqPoll(true); };
    r.appendChild(b); box.appendChild(r); });
  const sb = el("button", "sec", j.scanning ? t("Searching … put the loudspeaker into pairing mode (blue light blinking)") : "🔍 " + t("Search Bluetooth loudspeakers")); sb.type = "button";
  sb.disabled = !!j.scanning; sb.style.cssText = "margin-top:8px;width:100%;white-space:normal";
  sb.onclick = async () => { await post("/api/bt", {action: "scan", lang: LANG}); BTQ.t = 0; setTimeout(() => btqPoll(true), 1500); };
  box.appendChild(sb);
  if (j.scanning || j.busy) setTimeout(() => btqPoll(true), 1500);
}
function discoPaint(D) {                            // 2.95.54: the white light flashes with the music
  const b = $("#mode-disco"); if (!b || !D) return;
  const key = [D.on, D.mode, D.bpm, D.mic, D.white, D.on ? Math.floor(D.left / 60) : 0].join("|"); if (b.dataset.k === key) return; b.dataset.k = key; b.textContent = "";
  const r = el("div", "row"); r.style.cssText = "margin-top:8px;flex-wrap:wrap;gap:6px";
  const sm = $("#disco-sum"); if (sm) sm.textContent = "🪩 " + t("Disco light") + (D.on ? " · " + t("on") : "");   // 2.95.103: in a small sub-menu
  const go = el("button", D.on ? "" : "sec", D.on ? t("Stop") + " (" + Math.ceil(D.left / 60) + " min)" : t("Start")); go.type = "button"; go.disabled = !D.white;
  const md = document.createElement("select"); [["music", t("with the music (microphone)")], ["tempo", t("fixed tempo")]].forEach(([v, n]) => { const o = document.createElement("option"); o.value = v; o.textContent = n; md.appendChild(o); });
  md.value = D.mode; md.style.flex = "1 1 160px";
  const bp = document.createElement("select"); [80, 100, 120, 128, 140, 160].forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v + " BPM"; bp.appendChild(o); }); bp.value = String(D.bpm); bp.style.flex = "0 0 auto";
  const send = (on) => post("/api/disco", {on: on, mode: md.value, bpm: +bp.value, minutes: 120});
  go.onclick = () => send(!D.on); md.onchange = () => send(D.on); bp.onchange = () => send(D.on);
  r.append(go, md, bp); b.appendChild(r);
  b.appendChild(el("div", "mut", !D.white ? t("needs the white light (Lights)") : t("disco-note") + (D.mode === "music" && !D.mic ? " " + t("No microphone: the fixed tempo is used.") : "")));
}
function tvPaint(T) {                               // 2.95.51: the TV view (HDMI of the Pi or any screen with the link)
  const b = $("#mode-tv"); if (!b || !T) return;
  const key = [T.on, T.browser, T.auto, T.url, T.msg, T.sim, T.sim_ok].join("|"); if (b.dataset.k === key) return; b.dataset.k = key; b.textContent = "";
  const r = el("div", "row"); r.style.marginTop = "8px"; r.style.flexWrap = "wrap"; r.style.gap = "6px";
  r.append(el("b", "", "📺 " + t("TV view")));
  if (T.browser) { const bt = el("button", T.on ? "" : "sec", T.on ? t("Stop on the HDMI") : t("Show on the HDMI")); bt.type = "button";
    bt.onclick = async () => { const x = await post("/api/tv", {on: !T.on, lang: LANG}); if (!x.ok) toast("⚠ " + (x.error || t("error"))); }; r.append(bt); }
  if (T.sim_ok) { const bs = el("button", T.sim ? "" : "sec", T.sim ? t("Stop the TV mode of the simulator") : "🎮 " + t("TV mode in the 3D simulator")); bs.type = "button";
    bs.onclick = async () => { const x = await post("/api/tv", {sim: !T.sim, lang: LANG}); if (!x.ok) toast("⚠ " + (x.error || t("error"))); }; r.append(bs); }
  const a = document.createElement("a"); a.href = T.url; a.target = "_blank"; a.className = "btn sec"; a.textContent = "🔗 " + t("Open the link"); r.append(a);
  const cp = el("button", "sec", "📋"); cp.type = "button"; cp.title = t("Copy the link");
  cp.onclick = () => { try { navigator.clipboard.writeText(location.origin + T.url); toast("✓ " + t("Link copied")); } catch (e) {} }; r.append(cp, qrBtn(location.origin + T.url, t("TV view"), {secret: true}));
  b.append(r);
  const l = el("label", "row pr-sw"); const cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!T.auto;
  cb.onchange = () => post("/api/tv", {auto: cb.checked});
  l.append(el("span", "mut", t("tv-auto")), cb); b.append(l);
  if (T.msg && T.msg !== "on" && T.msg !== "off") b.append(el("div", "err", t(T.msg)));
}
async function modePick(id) {
  const s = window.__lastState || {}, M = s.mode || {}, hs = s.hotspot || {}, hc = s.hotspot_cfg || {};
  if (id === "gamer" && !M.power_ok) { toast("⚠ " + t("needs mains power") + ": " + t(M.power_why)); return; }
  if (id === M.id) return;
  // 2.95.49: the camping guard switches the own Wi-Fi on (and off when it ends) - the page loses its connection: ask first
  if (id === "camping" && !s.camping && !hs.on && hs.available !== false) {
    const msg = t("Camping profile") + ":\n- " + t("own Wi-Fi") + " «" + hc.ssid + "» (" + t("password") + ": " + hc.password + ")\n\n"
      + t("This page loses its connection. Connect the phone to") + " «" + hc.ssid + "» " + t("and open") + " " + hc.address;
    if (!confirm(msg)) return;
  } else if (M.id === "camping" && id !== "camping" && hs.on && !confirm(t("End camping? The own Wi-Fi is switched off again - this page loses its connection and the Pi goes back to the known networks."))) return;
  MD.want = id; MD.until = Date.now() + 3000; modePaint(window.__lastState || {mode: M});
  const r = await post("/api/mode", {mode: id, lang: LANG});
  $("#mode-err").textContent = r.ok ? "" : (r.error || t("error"));
  if (r.ok) toast("✓ " + t("Mode switched")); MD.until = 0;
}
function updateProtect(s) {
  window.__lastState = s;
  const [txt, cls] = prText(s);
  const b = $("#b-arm"); if (b) { badge("#b-arm", txt, cls); b.title = t("tap: arm / disarm"); }
  const st = $("#pr-state"); if (!st) return;
  st.textContent = txt; st.style.color = cls === "grn" ? "var(--grn)" : (cls === "yel" ? "var(--yel)" : "var(--mut)");
  $("#pr-left").textContent = s.arm_state === "disarmed" ? t("no alarms, no recordings") : (s.arm_state === "arming" ? t("leave the area now") : t("alarms active"));
  $("#pr-arm").hidden = s.arm_state !== "disarmed"; $("#pr-armnow").hidden = s.arm_state === "armed"; $("#pr-disarm").hidden = s.arm_state === "disarmed";
  const hs = s.hotspot || {}, hc = s.hotspot_cfg || {};
  if (Date.now() > PR.campUntil) $("#pr-camp").checked = !!s.camping;
  if (!(Date.now() < (PR.ecoUntil || 0))) $("#pr-eco").checked = s.eco !== "off";
  mwgPaint(s); simShootPaint(s); iconPick(); scPick(); modePaint(s); protectPaint(s.protect);
  const TT = s.tether || {}, te = $("#pr-teth");
  if (te) te.textContent = TT.on ? (TT.ready ? "✓ " + t("connected") + " · " + TT.kind + " · " + TT.iface + " · " + t("the own Wi-Fi gets this internet too")
      : "⏳ " + t("phone found, connecting …") + " (" + TT.iface + ")")
    : t("tether-hint");
  const TB = s.turbo || {};
  if (!(Date.now() < (PR.turboUntil || 0))) $("#pr-turbo").checked = !!TB.on;
  $("#pr-turbo-info").textContent = TB.on ? t("active: every picture through the AI, best picture, processor at full clock") + (TB.temp != null ? " · " + Math.round(TB.temp) + " °C" : "") + (TB.temp > 75 ? " ⚠ " + t("hot") : "")
    : t("the highest performance (uses more current and gets warmer) - switching it off restores your settings");
  const bt = $("#b-turbo"); if (bt) bt.hidden = !TB.on;
  $("#pr-eco-info").textContent = s.eco === "saving" ? t("active: few pictures, everything quiet") : (s.eco === "awake" ? t("full speed (something happened or somebody watches)")
    : t("off") + " · " + t("fewer pictures while all is quiet, full speed at the first movement or noise"));
  if (Date.now() > PR.hsUntil && !hs.busy) $("#pr-hs").checked = !!hs.on;
  $("#pr-hs").disabled = hs.available === false;
  const info = $("#pr-hs-info");
  if (hs.available === false) info.textContent = t("needs NetworkManager (Raspberry Pi OS Bookworm or newer)");
  else if (hs.busy) info.textContent = t("switching …");
  else if (hs.on) info.textContent = t("on") + " · «" + hs.ssid + "» · " + t("password") + " " + (hc.password || "–") + " · " + hs.clients + " "
    + (hs.clients === 1 ? t("device") : t("devices")) + " · " + (hc.address || "");
  else info.textContent = t("off") + " · " + t("name") + " «" + (hc.ssid || "") + "» · " + t("password") + " " + (hc.password || "–");
  $("#pr-err").textContent = hs.msg ? "⚠ " + hs.msg : "";
  $("#pr-time").textContent = s.time_status ? t("Clock") + ": " + tlTxt(s.time_status) : "";
  const pe = $("#pr-env");
  if (pe) { const e = s.env; pe.textContent = e ? "🌡 " + t("Outside") + ": " + e.t.toFixed(1) + " °C" + (e.h != null ? " · " + e.h + " %" : "") + (e.p ? " · " + Math.round(e.p) + " hPa" : "") + " (" + e.src + ")" : "🌡 " + t("no temperature sensor"); }
  hb("#b-env", !!s.env, s.env ? "🌡 " + s.env.t.toFixed(1) + " °C" + (s.env.h != null ? " · " + s.env.h + " %" : "") : "", "");
  const hcn = s.health; if (hcn) { hb("#b-health", hcn.bad > 0, "🩺 " + hcn.bad, "red"); const hsum = $("#h-sum");
    if (hsum) hsum.textContent = "· " + (hcn.bad ? hcn.bad + " " + t("problems") + " · " : "") + (hcn.warn ? hcn.warn + " " + t("notes") + " · " : "") + hcn.ok + " ok"; }
  const pg = $("#pr-gps");
  if (pg) { const g = s.gps; pg.textContent = "";
    if (g) { const a = el("a", "", "📍 " + g.lat.toFixed(4) + ", " + g.lon.toFixed(4)); a.href = "https://www.openstreetmap.org/?mlat=" + g.lat + "&mlon=" + g.lon + "#map=15/" + g.lat + "/" + g.lon;
      a.target = "_blank"; a.rel = "noopener"; pg.append(t("Location") + ": ", a, " · " + (g.src === "phone" ? t("from the phone") + (g.age != null ? " (" + Math.round(g.age / 60) + " min)" : "") : g.src === "module" ? t("from the GPS module") : t("fixed (settings)")));
    } else pg.textContent = t("Location") + ": " + t(window.isSecureContext ? "unknown" : "unknown – the phone shares it only over the https page"); }
}
// ---- «Guard tonight» ----
Object.assign(I18N.de, {"Picture": "Bild", "Camera and alignment": "Kamera und Ausrichtung", "Hide settings": "Einstellungen ausblenden", "Show settings": "Einstellungen einblenden", "Alarm": "Alarm", "own text": "eigener Text", "standard text": "Standardtext", "Groups only": "Nur Gruppen öffnen", "Storage": "Speicher", "Memory (RAM)": "Arbeitsspeicher (RAM)", "⏻ Switch off, restart, pause": "⏻ Ausschalten, Neustart, Pause", "🔐 Operator mode": "🔐 Bedienmodus", "🧭 Help and setup": "🧭 Hilfe und Einrichtung", "🔒 Password and settings file": "🔒 Passwort und Einstellungsdatei", "ℹ Version and status": "ℹ Version und Status", "Device name": "Gerätename", "Time": "Uhrzeit", "Date": "Datum", "Number of persons": "Anzahl Personen", "Camera": "Kamera", "Volume (dB)": "Lautstärke (dB)", "Link": "Link", "Leave a field empty for the standard text. Tap a grey button to insert a placeholder at the cursor.": "Ein Feld leer lassen = Standardtext. Graue Knöpfe antippen, um einen Platzhalter an der Cursorstelle einzufügen.", "Person": "Person", "Pre-alarm": "Voralarm", "Thermal alarm": "Wärmebild-Alarm", "Noise alarm": "Geräusch-Alarm", "Preview": "Vorschau", "Title": "Titel", "Text": "Text", "Standard text": "Standardtext"});
Object.assign(I18N.de, {"Picture for other programs (Home Assistant, recorder, VLC) with a secret address": "Bild für andere Programme (Home Assistant, Rekorder, VLC) mit geheimer Adresse", "RTSP video for recorders (needs mediamtx; uses CPU)": "RTSP-Video für Rekorder (braucht mediamtx; braucht Rechenleistung)", "New secret address": "Neue geheime Adresse", "Off – switch on «Picture for other programs» above.": "Aus – oben «Bild für andere Programme» einschalten.", "Still picture": "Standbild", "Copy": "Kopieren", "Copied": "Kopiert", "Keep these addresses secret: whoever has them sees the picture without a password.": "Diese Adressen geheim halten: Wer sie hat, sieht das Bild ohne Passwort.", "Make a new secret address? The old one stops working (other programs need the new one).": "Neue geheime Adresse erstellen? Die alte funktioniert dann nicht mehr (andere Programme brauchen die neue).", "mediamtx is not installed (see the manual: RTSP)": "mediamtx ist nicht installiert (siehe Anleitung: RTSP)"});
Object.assign(I18N.de, {"memory card": "Speicherkarte", "USB drive": "USB-Laufwerk", "drive": "Laufwerk", "chosen drive missing - recordings on the memory card": "gewähltes Laufwerk fehlt – Aufnahmen auf der Speicherkarte", "Connect the SSD / USB drive and restart, or choose another place under Settings → Recording.": "SSD / USB-Laufwerk anschliessen und neu starten, oder unter Einstellungen → Aufnahme einen anderen Ort wählen.", "An SSD / USB drive is connected: put the recordings there (Settings → Recording) - it lasts longer than a memory card.": "Ein SSD- / USB-Laufwerk ist angeschlossen: Aufnahmen dorthin legen (Einstellungen → Aufnahme) – das hält länger als eine Speicherkarte.", "Recordings stored on": "Aufnahmen speichern auf", "memory card (next to the program)": "Speicherkarte (beim Programm)", "read only": "nur lesen", "missing": "fehlt", "now": "jetzt", "no SSD / USB drive found": "kein SSD- / USB-Laufwerk gefunden", "Store the recordings there from now on? The existing ones are moved over (this can take a while).": "Aufnahmen ab jetzt dort speichern? Die bisherigen werden hinüber verschoben (das kann etwas dauern).", "moving recordings …": "Aufnahmen werden verschoben …", "drive not found": "Laufwerk nicht gefunden", "the drive cannot be written to": "auf das Laufwerk kann nicht geschrieben werden"});
Object.assign(I18N.de, {"End operator mode (PIN)": "Bedienmodus beenden (PIN)", "Operator mode is on": "Bedienmodus ist aktiv", "since": "seit", "unlocking puts everything back": "Entsperren setzt alles zurück"});
Object.assign(I18N.de, {"Switch on operator mode? Everything may be changed except Wi-Fi, password and autostart; unlocking with the PIN puts everything back.": "Bedienmodus einschalten? Alles darf verstellt werden ausser WLAN, Passwort und Autostart; beim Entsperren mit der PIN wird alles zurückgesetzt."});
Object.assign(I18N.de, {"Lock the settings now? Only the main switches stay usable. Everything changed until then is put back when unlocking with the PIN.": "Einstellungen jetzt sperren? Nur die wichtigsten Schalter bleiben bedienbar. Alles, was bis dahin verstellt wird, wird beim Entsperren mit der PIN zurückgesetzt.", "changes put back": "Änderungen zurückgesetzt"});
Object.assign(I18N.de, {"🌙 Guard tonight": "🌙 Heute Nacht bewachen", "night-desc": "schaltet ein, was es für die Nacht braucht, schaltet nach dem Countdown den Schutz ein und sagt, was noch fehlt", "Still missing:": "Fehlt noch:", "Everything ready - good night!": "Alles bereit – gute Nacht!", "Guard tonight": "Heute Nacht bewachen", "Simple": "Einfach", "Expert": "Experte", "Simple: only the important settings. «Expert» shows all of them.": "Einfach: nur die wichtigen Einstellungen. «Experte» zeigt alle."});
async function nightGuard() {
  const b = $("#pr-night"); b.disabled = true;
  const r = await post("/api/night", {lang: LANG}); b.disabled = false;
  const box = $("#night-res"); box.textContent = ""; box.hidden = false;
  if (!r || !r.ok) { box.textContent = "⚠ " + ((r && r.error) || "error"); return; }
  (r.done || []).forEach(x => box.appendChild(el("div", "nr-ok", "✓ " + x)));
  if ((r.missing || []).length) { box.appendChild(el("div", "nr-h", t("Still missing:")));
    r.missing.forEach(x => { const d = el("div", "nr-miss"); d.append(el("b", "", "⚠ " + x.icon + " " + x.title), el("span", "mut", " " + (x.text || "")));
      if (x.tip) d.appendChild(el("div", "htip", "→ " + x.tip)); box.appendChild(d); }); }
  else box.appendChild(el("div", "nr-h", t("Everything ready - good night!")));
  toast("🌙 " + t("Guard tonight"));
}
// ---- Simple / Expert ----
function simpleBar(on) {
  const w = el("div", "simplebar"), seg = el("div", "seg lseg"), a = el("button", on ? "sel-auto" : "", t("Simple")), e = el("button", on ? "" : "sel-auto", t("Expert"));
  a.type = e.type = "button"; seg.append(a, e);
  const set = v => post("/api/ui_simple", {on: v}).then(() => location.reload());
  a.onclick = () => { if (!on) set(true); }; e.onclick = () => { if (on) set(false); };
  w.appendChild(seg); if (on) w.appendChild(el("div", "mut", t("Simple: only the important settings. «Expert» shows all of them.")));
  // 2.95.70: symbols coloured (with a green dot while on) or plain (turn green) - per device
  let pl = false; try { pl = localStorage.getItem("mw-icons") === "plain"; } catch (e) {}
  const iw = el("div", "icseg"), is = el("div", "seg lseg"), ic = el("button", pl ? "" : "sel-auto", document.body.dataset.tab ? "🎨 " + t("Symbols coloured") : t("Coloured symbols")), ip = el("button", pl ? "sel-auto" : "", document.body.dataset.tab ? "◯ " + t("plain") : t("Plain symbols"));
  ic.type = ip.type = "button"; is.append(ic, ip);
  const iset = v => { try { localStorage.setItem("mw-icons", v ? "plain" : "color"); } catch (e) {} document.body.classList.toggle("icplain", v);
    ic.className = v ? "" : "sel-auto"; ip.className = v ? "sel-auto" : ""; };
  ic.onclick = () => iset(false); ip.onclick = () => iset(true);
  iw.append(el("div", "mut", t("Symbols: green dot or green symbol = switched on")), is); w.appendChild(iw);
  return w;
}
// ---- self-check: one traffic light per part ----
Object.assign(I18N.de, {"missed pictures from the game (hard cases)": "verpasste Bilder aus dem Spiel (schwierige Fälle)", "no missed pictures from the game yet - play a round with MoveEye first": "noch keine verpassten Bilder aus dem Spiel – zuerst eine Runde mit MoveEye spielen", "You are the guard: turn the camera and tap the players in the picture": "Du bist Jäger: Kamera drehen und die Spieler im Bild antippen", "Mover stick back in its place": "Mover-Stick wieder an seinem Platz", "Move (double tap: back to its place)": "Verschieben (doppelt tippen: zurück an den Platz)", "Mover stick shown": "Mover-Stick eingeblendet", "Mover stick hidden": "Mover-Stick ausgeblendet", "Show / hide the mover stick": "Mover-Stick ein- / ausblenden", "Coloured symbols": "Farbige Symbole", "Symbols coloured": "Symbole farbig", "plain": "schlicht", "Plain symbols": "Schlichte Symbole", "Symbols: green dot or green symbol = switched on": "Symbole: grüner Punkt bzw. grünes Symbol = eingeschaltet", "Download AI model": "KI-Modell herunterladen", "AI ready": "KI bereit", "downloading the AI model …": "KI-Modell wird geladen …", "🩺 Self-check": "🩺 Selbstdiagnose", "Check again": "Nochmals prüfen", "problems": "Probleme", "notes": "Hinweise"});
async function healthLoad() {
  let j; try { j = await (await fetch("/api/health?lang=" + LANG, {cache: "no-store"})).json(); } catch (e) { return; }
  const L = $("#h-list"); if (!L) return; L.textContent = "";
  j.items.forEach(x => { const r = el("div", "hrow h-" + x.level), d = el("span", "hdot"), b = el("div", "hbody");
    const top = el("div", "htop"); top.append(el("b", "", x.icon + " " + x.title), el("span", "mut", x.text || ""));
    b.appendChild(top); if (x.tip && x.level !== "ok") b.appendChild(el("div", "htip", "→ " + x.tip));
    if (x.action === "ai_dl") { const k = el("button", "", "⬇ " + t("Download AI model")); k.type = "button"; k.style.marginTop = "6px";
      k.onclick = async () => { k.disabled = true; const r = await post("/api/ai_model", {}); if (!r.ok) { toast("⚠ " + (r.error || "error")); k.disabled = false; return; }
        toast("⬇ " + t("Download AI model")); const iv = setInterval(async () => { await healthLoad(); let j = {}; try { j = await (await fetch("/api/ai_model")).json(); } catch (e) {}
          if (!j.busy) { clearInterval(iv); toast(j.msg === "ready" ? "✓ " + t("AI ready") : "⚠ " + (j.msg || "")); healthLoad(); } }, 2000); };
      b.appendChild(k); }
    if (x.link) { const a = el("a", "", "📖 " + t("Manual")); a.href = x.link; a.target = "_blank"; a.rel = "noopener"; a.style.cssText = "display:inline-block;margin-top:4px;font-size:13px"; b.appendChild(a); }
    r.append(d, b); L.appendChild(r); });
}
function healthOpen() { const c = $("#hcard"); if (!c) return; let p = c; while (p) { if (p.tagName === "DETAILS") p.open = true; p = p.parentElement; }
  healthLoad(); c.scrollIntoView({behavior: "smooth", block: "start"}); }
(function () { const c = document.getElementById("hcard"); if (!c) return;
  c.addEventListener("toggle", () => { if (c.open) healthLoad(); });
  setInterval(() => { if (c.open && !document.hidden) healthLoad(); }, 15000); })();
async function prAutostart(on) {
  PR.asUntil = Date.now() + 3000;
  const r = await post("/api/autostart", {on: on, lang: LANG});
  if (r && r.autostart) window.__autostart = r.autostart;
  if (!r.ok) { $("#pr-err").textContent = "⚠ " + (r.error || "error"); $("#pr-as").checked = !on; }
  else { $("#pr-err").textContent = r.autostart && r.autostart.msg ? "⚠ " + r.autostart.msg : ""; toast(on ? "🔁 " + t("Autostart on") : t("Autostart off")); }
}
const NETTXT = () => ({"off": "", "needs NetworkManager": t("needs NetworkManager (Raspberry Pi OS Bookworm or newer)"),
  "paused (switched by hand)": t("automatic paused (switched by hand) - choose «Automatic» again to resume"),
  "own Wi-Fi on": t("own Wi-Fi on"), "searching known networks …": t("searching known networks …"),
  "own Wi-Fi on - search postponed (a device is connected)": t("own Wi-Fi on - search postponed (a device is connected)")});
function netTxt(x) {
  if (!x) return "";
  let m = /^connected with «(.*)»$/.exec(x); if (m) return "✓ " + t("connected with") + " «" + m[1] + "»";
  m = /^no known network - own Wi-Fi in (\d+) s$/.exec(x); if (m) return t("no known network - own Wi-Fi in") + " " + m[1] + " s";
  m = /^own Wi-Fi on \+ internet from «(.*)»$/.exec(x); if (m) return "✓ " + t("own Wi-Fi on + internet from") + " «" + m[1] + "» (" + t("repeater") + ")";
  if (x === "own Wi-Fi on - the second adapter looks for known networks") return t(x);
  m = /^own Wi-Fi on - next search in (\d+) min$/.exec(x); if (m) return t("own Wi-Fi on - next search for known networks in") + " " + m[1] + " min";
  return NETTXT()[x] !== undefined ? NETTXT()[x] : x;
}
function updateAutostart(s) {
  const a = s.autostart || {}, i = $("#pr-as-info"); if (!i) return;
  if (!(Date.now() < (PR.asUntil || 0))) $("#pr-as").checked = !!a.on;
  const mode = s.net_mode || "auto";
  if (document.activeElement !== $("#pr-net") && !(Date.now() < (PR.netUntil || 0))) $("#pr-net").value = mode;
  const what = {auto: t("tries the known networks (phone hotspot), otherwise switches the own Wi-Fi on"),
                hotspot: t("switches the own Wi-Fi on"), client: t("joins the known networks")}[mode];
  i.textContent = a.on ? t("on: when the Pi boots, MoveEye starts by itself and") + " " + what
                       : t("off: nothing starts at boot, the Pi joins its known networks");
  $("#pr-net-info").textContent = netTxt(s.netauto);
}
$("#pr-net").onchange = async e => {
  PR.netUntil = Date.now() + 3000;
  const r = await post("/api/text", {key: "net_mode", value: e.target.value, lang: LANG});
  if (r.ok) toast(t("Saved")); else $("#pr-err").textContent = "⚠ " + (r.error || "error");
};
$("#pr-as").onchange = e => prAutostart(e.target.checked);
$("#pr-arm").onclick = () => prArm("arm");
$("#pr-armnow").onclick = () => prArm("arm_now");
$("#pr-disarm").onclick = () => prArm("disarm");
$("#pr-camp").onchange = e => prCamp(e.target.checked);
$("#pr-eco").onchange = async e => { PR.ecoUntil = Date.now() + 2500; if (e.target.checked && $("#pr-turbo").checked) await post("/api/turbo", {on: false});
  post("/api/set", {key: "eco_on", value: e.target.checked}); };
$("#pr-turbo").onchange = async e => { PR.turboUntil = Date.now() + 2500; const r = await post("/api/turbo", {on: e.target.checked});
  toast(e.target.checked ? "🚀 " + t("Power mode on: everything on the highest performance") : "↩ " + t("Power mode off: your settings are back")); };
$("#pr-hs").onchange = e => prHotspot(e.target.checked);
$("#b-arm").addEventListener("click", () => { const s = window.__lastState || {}; prArm(s.arm_state === "disarmed" ? "arm" : "disarm"); });

function drawWifi(hist) {
  const c = $("#wifi-spark"); if (!c) return;
  const g = c.getContext("2d"), w = c.width, h = c.height, N = 150;
  const TOP = -35, BOT = -95, y = d => 2 + (h - 4) * (TOP - Math.max(BOT, Math.min(TOP, d))) / (TOP - BOT);
  const col = d => d >= -65 ? "#3fb950" : (d >= -75 ? "#d29922" : "#ff3b3b");
  g.clearRect(0, 0, w, h);
  g.font = "9px system-ui, sans-serif"; g.textAlign = "right";
  [[-65, "#3fb950", "bottom", -1], [-75, "#d29922", "top", 1]].forEach(([d, cl, base, dy]) => {
    g.strokeStyle = THEME === "light" ? "#d0d7e2" : "#1f2a38"; g.lineWidth = 1; g.setLineDash([3, 3]);
    g.beginPath(); g.moveTo(0, y(d)); g.lineTo(w, y(d)); g.stroke(); g.setLineDash([]);
    g.textBaseline = base; g.fillStyle = cl; g.globalAlpha = 0.8; g.fillText(d + " dBm", w - 3, y(d) + dy); g.globalAlpha = 1;
  });
  g.textAlign = "left";
  if (!hist || !hist.length) return;
  const x = i => w - (hist.length - 1 - i) * (w / (N - 1));
  g.lineWidth = 2;
  for (let i = 1; i < hist.length; i++) {
    const a = hist[i - 1], b = hist[i];
    if (a == null || b == null) continue;
    g.strokeStyle = col(Math.min(a, b)); g.beginPath(); g.moveTo(x(i - 1), y(a)); g.lineTo(x(i), y(b)); g.stroke();
  }
  hist.forEach((d, i) => {
    if (d == null) { g.fillStyle = "#ff3b3b"; g.fillRect(x(i) - 1, h - 6, 2.5, 6); }                 // no connection
    else if ((i === 0 || hist[i - 1] == null) && (i === hist.length - 1 || hist[i + 1] == null)) { g.fillStyle = col(d); g.beginPath(); g.arc(x(i), y(d), 2, 0, 7); g.fill(); }
  });
}
function wifiStats(hist) {
  const v = (hist || []).filter(d => d != null);
  let drops = 0; (hist || []).forEach((d, i) => { if (d == null && (i === 0 || hist[i - 1] != null)) drops++; });
  const mins = Math.max(1, Math.round((hist || []).length * 2 / 60));
  let txt = t("Wi-Fi signal, last") + " " + mins + " " + t("min");
  if (v.length) txt += " · Ø " + Math.round(v.reduce((a, b) => a + b, 0) / v.length) + " dBm · " + t("weakest") + " " + Math.min(...v) + " dBm";
  txt += " · " + (drops ? drops + " " + (drops === 1 ? t("drop-out") : t("drop-outs")) : t("no drop-outs"));
  return txt;
}
function updateWifi(s) {
  const w = s.wifi, n = s.net || {}, b = $("#b-wifi"), box = $("#wifi-box");
  if (!b) return;
  if (!w) { b.hidden = true; box.hidden = true; return; }
  if (w.ap) {                                        // the Pi is the access point: show that instead of a signal
    const hs = s.hotspot || {};
    b.hidden = HIDDEN.has("b-wifi"); box.hidden = true;
    b.textContent = "📡 " + t("Own Wi-Fi") + " · " + (hs.clients || 0) + " " + ((hs.clients === 1) ? t("device") : t("devices"));
    b.className = "badge grn" + (HIDDEN.has("b-wifi") ? " vh" : "") + keepQ(b, "grn"); b.title = "«" + (hs.ssid || "") + "» · " + (hs.ip || "");
    return;
  }
  b.hidden = HIDDEN.has("b-wifi"); box.hidden = false;
  drawWifi(s.wifi_hist); $("#wifi-stat").textContent = wifiStats(s.wifi_hist);
  const bars = !w.connected ? 0 : (w.pct >= 75 ? 4 : w.pct >= 50 ? 3 : w.pct >= 25 ? 2 : 1);
  const cls = !w.connected ? "red" : (w.dbm >= -65 ? "grn" : (w.dbm >= -75 ? "yel" : "red"));
  const wb = el("span", "wbars"); for (let i = 1; i <= 4; i++) wb.appendChild(el("i", i <= bars ? "on" : ""));
  b.textContent = ""; b.append(wb, document.createTextNode(w.connected ? w.dbm + " dBm" : t("no Wi-Fi")));
  if (n.online === false && w.connected) b.append(document.createTextNode(" · " + t("no internet")));
  b.className = "badge " + (n.online === false ? "red" : cls) + (HIDDEN.has("b-wifi") ? " vh" : "") + keepQ(b, n.online === false ? "red" : cls);
  b.title = (w.ssid ? w.ssid + " · " : "") + w.iface + (w.rate ? " · " + w.rate : "");
  $("#wifi-big").textContent = w.connected ? w.pct + " %" : t("no Wi-Fi");
  $("#wifi-name").textContent = t("Wi-Fi") + (w.ssid ? " «" + w.ssid + "»" : "") + " · " + w.iface;
  const bar = $("#wifi-bar"); bar.style.width = (w.connected ? w.pct : 0) + "%";
  bar.style.background = cls === "grn" ? "#3fb950" : (cls === "yel" ? "#d29922" : "#ff3b3b");
  $("#wifi-info").textContent = (w.connected ? w.dbm + " dBm" + (w.rate ? " · " + w.rate : "") : t("not connected")) + " · " + t("Internet") + ": "
    + (n.online === true ? t("online") + (n.ms != null ? " (" + n.ms + " ms)" : "") : (n.online === false ? t("offline") : "…"));
}
function updateExtras(s) {
  updateWifi(s);
  const a = $("#tl-status"); if (a) a.textContent = tlTxt(s.timelapse);
  const r = $("#tl-render"); if (r) r.textContent = tlTxt(s.timelapse_render);
  if (s.timelapse_last !== tlSeen) { if (tlSeen !== null) tlLoad(); tlSeen = s.timelapse_last; }
  if ((s.timelapse_render || "").startsWith("video ready") && r && !r.dataset.done) { r.dataset.done = "1"; tlLoad(); }
  if (!(s.timelapse_render || "").startsWith("video ready") && r) delete r.dataset.done;
  const h = $("#th-status"); if (h) h.textContent = tlTxt(s.thermal) + (s.thermal === "connected" && s.thermal_res ? " · " + s.thermal_res : "")
    + (s.thermal === "connected" && s.thermal_max != null ? " · max " + s.thermal_max.toFixed(1) + " °C" : "");
}

function drawSpark(hist) {
  const c = $("#cpu-spark"), g = c.getContext("2d"), w = c.width, h = c.height;
  g.clearRect(0, 0, w, h);
  g.strokeStyle = THEME === "light" ? "#d0d7e2" : "#1f2a38"; g.lineWidth = 1;
  [25, 50, 75].forEach(p => { const y = h - h * p / 100; g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); });
  if (!hist || hist.length < 2) return;
  const last = hist[hist.length - 1];
  g.strokeStyle = last < 60 ? "#3fb950" : (last < 85 ? "#d29922" : "#ff3b3b");
  g.lineWidth = 2; g.beginPath();
  hist.forEach((v, i) => {
    const x = w - (hist.length - 1 - i) * (w / 59), y = h - 2 - (h - 4) * v / 100;
    i ? g.lineTo(x, y) : g.moveTo(x, y);
  });
  g.stroke();
}

async function refresh() {
  let j;
  try { j = await (await fetch("/api/state?lang=" + LANG)).json(); }
  catch (e) { badge("#b-conn", t("Pi not reachable"), "red"); return; }
  badge("#b-conn", t("Pi connected"), "grn");
  const s = j.state, c = j.cfg, rel = j.relays || [], rs = s.relay_states || [];
  applyRole(s.me);
  if (s.me && s.me.role === "admin" && !window.USERS_DONE && $("#users-box")) { window.USERS_DONE = true; usersLoad(); }
  try { mainPaint(j); } catch (e) {}
  try { qsPaint(j); } catch (e) {}
  try { chainPaint(c, s); } catch (e) {}
  badge("#b-person", s.persons ? s.persons + " " + (s.persons > 1 ? t("PERSONS DETECTED") : t("PERSON DETECTED")) : t("No person"), s.persons ? "red" : "");
  badge("#b-obj", s.objects + " " + (s.objects === 1 ? t("object") : t("objects")), s.objects ? "org" : "");
  badge("#b-rain", s.rain_mode ? t("RAIN MODE") : t("No rain"), s.rain_mode ? "blu" : "");
  badge("#b-wind", t("Wind") + ": " + t(s.wind_level), (s.wind_level !== "calm" && s.wind_level !== "off") ? "yel" : "");
  badge("#b-rec", s.recording ? "● " + t("REC") : t("Idle"), s.recording ? "red" : "");
  const on = rs.filter(Boolean).length;
  badge("#b-relay", t("Relays") + ": " + on + "/" + rel.length, on ? "grn" : "");
  badge("#b-light", s.lowlight ? t("LOW LIGHT") : t("Light ok") + " (" + s.brightness + ")", s.lowlight ? "yel" : "");
  $("#sys-info").textContent = t("Settings") + ": " + (s.settings_status_txt || s.settings_status) + " · " + t("recordings") + ": " + s.rec_dir_mb + " MB · " + t("viewers") + ": " + s.web_viewers
      + (s.notify_status !== "off" ? " · " + t("notify") + ": " + s.notify_status : "");
  $("#v-pan").textContent = Math.round(c.pan); $("#v-tilt").textContent = Math.round(c.tilt);
  showPos(c.pan, c.tilt);
  $("#patrol-st").textContent = ((s.manual ? t("Manual control - tracking / patrol paused") : s.tracking ? t("Tracking person")
      : ((c.patrol || (s.kopf && s.kopf.owner === "round")) ? t("Patrol") + ": " + psText(s.patrol_status) : (s.kopf && s.kopf.text ? "⟲ " + s.kopf.text : ""))) + (j.waypoints.length ? " · " + t("waypoints") + " (↔/↕): " + j.waypoints.map(w => Math.round(w[0]) + "/" + Math.round(w[1])).join(", ") : "")).replace(/^ · /, "");
  wpPaint(j.waypoints, c);
  if (window.pipAlarm) pipAlarm(s.persons || 0);
  renderRelays(rel, rs, c.ai_enabled && !/no model|error/.test(s.ai_status));
  const ssrc = s.source_status || "";
  badge("#b-src", t("Source") + ": " + (s.source_label || "–").slice(0, 26), ssrc === "connected" ? "grn" : (ssrc.startsWith("failed") ? "red" : "yel"));
  badge("#b-sched", t("Schedule") + ": " + ((s.sched_active || []).length ? s.sched_active.join(", ") : "–"), (s.sched_active || []).length ? "blu" : "");
  renderSourceStatus(s);
  if (s.source_id !== lastSrcId) { lastSrcId = s.source_id; loadSources(false); }
  // 2.95.72: another video source (simulation off -> webcam, other camera): fetch the live picture anew - the old stream can
  // stand still on the last picture of the old source (seen on the iPhone), only a reload of the page helped
  { const k = (s.source_label || "") + "|" + (s.source_res || "") + "|" + ssrc;
    if (window._vKey !== undefined && k !== window._vKey && ssrc === "connected") { const v = $("#video"); if (v && v.mwRestart) setTimeout(() => v.mwRestart(), 300); }
    window._vKey = k; }
  renderSchedules(j.schedules || [], s);
  $("#v-rec").hidden = !s.recording; $("#v-src").hidden = !s.source_label; $("#v-src").textContent = s.source_label || "";
  $("#b-sec").hidden = !s.web_open;
  updateExtras(s); updateProtect(s); tpPaint(s); sensPaint(c, s); stormPaint(c, s); gpsPaint(c, s); simPaint(s); moverPaint(s); sevPaint(s); wakePaint(s); solarPaint(c, s); dtPaint(s); mqPaint(s); updateAutostart(s); updateAudio(s.audio); renderLights(s.light_cfg, s); updateSecurity(s); tidyHeader(s, c);
  badge("#b-pres", t("Presence") + ": " + t(s.presence || "unknown"), s.presence === "home" ? "grn" : (s.presence === "away" ? "org" : ""));
  $("#b-pres").hidden = !(s.presence === "home" || s.presence === "away") || HIDDEN.has("b-pres");


  if (s.cpu === null || s.cpu === undefined) {
    badge("#b-cpu", "CPU n/a", ""); $("#cpu-big").textContent = "n/a";
  } else {
    const cls = s.cpu < 60 ? "grn" : (s.cpu < 85 ? "yel" : "red");
    const tp = s.cpu_temp;
    const tcls = tp == null ? "" : (tp >= 80 ? "red" : (tp >= 70 ? "yel" : "grn"));
    const worst = [cls, tcls].includes("red") ? "red" : ([cls, tcls].includes("yel") ? "yel" : cls);
    badge("#b-cpu", "CPU " + Math.round(s.cpu) + "%" + (tp != null ? " · " + Math.round(tp) + " °C" : ""), worst);
    $("#cpu-big").textContent = s.cpu.toFixed(0) + " %";
    const bar = $("#cpu-bar"); bar.style.width = s.cpu + "%";
    bar.style.background = s.cpu < 60 ? "#3fb950" : (s.cpu < 85 ? "#d29922" : "#ff3b3b");
    $("#cpu-info").textContent = (s.cpu_temp != null ? s.cpu_temp.toFixed(1) + " °C · " : "") + s.cpu_count + " " + t("cores");
  }
  drawSpark(s.cpu_hist);
  const mm = s.mem, rb = $("#ram-bar");
  if (rb) { if (mm) { rb.style.width = mm.pct + "%"; rb.style.background = mm.pct < 70 ? "#3fb950" : (mm.pct < 90 ? "#d29922" : "#ff3b3b");
      $("#ram-info").textContent = (mm.used / 1024).toFixed(1) + " / " + (mm.total / 1024).toFixed(1) + " GB · " + Math.round(mm.pct) + " %" + (mm.swap > 50 ? " · swap " + mm.swap + " MB" : ""); }
    else $("#ram-info").textContent = "n/a"; }
  const dk = s.disk || {}, db = $("#dsk-bar");
  if (db && dk.total_mb) { const used = (dk.total_mb - dk.free_mb) / dk.total_mb * 100; db.style.width = used + "%";
    db.style.background = dk.free_mb > 4096 ? "#3fb950" : (dk.free_mb > 1024 ? "#d29922" : "#ff3b3b");
    $("#dsk-name").textContent = ({sd: t("memory card"), ssd: "SSD", usb: t("USB drive")})[dk.kind] || t("Storage");
    $("#dsk-info").textContent = (dk.free_mb / 1024).toFixed(1) + " GB " + t("free") + " / " + (dk.total_mb / 1024).toFixed(0) + " GB" + (s.rec_dir_mb != null ? " · " + t("recordings") + " " + (s.rec_dir_mb >= 1024 ? (s.rec_dir_mb / 1024).toFixed(1) + " GB" : s.rec_dir_mb + " MB") : ""); }

  for (const k in ctrl) {
    if (k === editing || !(k in c)) continue;
    const x = ctrl[k];
    if (x.type === "bool") x.input.checked = !!c[k];
    else if (document.activeElement !== x.input) { x.input.value = c[k]; x.val.textContent = Math.round(c[k] * 100) / 100; }
  }
  const log = $("#log"); log.textContent = "";
  const IC = {person: "🔴", rec: "🎬", sys: "⚙", web: "🌐", sched: "🗓"};
  j.events.forEach(e => { const tx = el("span", e.dim ? "t" : "", (IC[e.kind] || "•") + " " + e.text + "\n");
    log.append(el("span", "t", (e.d && e.d !== TODAY ? e.d.slice(8) + "." + e.d.slice(5, 7) + ". " : "") + e.t + "  "), tx); });
  if (!j.events.length) log.appendChild(el("span", "t", t("Nothing important yet – everything else is in the whole log.")));
}

let hold = null;
document.querySelectorAll("button.dp").forEach(b => {
  const stop = () => { clearInterval(hold); hold = null; };
  b.addEventListener("pointerdown", e => {
    e.preventDefault(); move(b.dataset.dir);
    if (b.dataset.dir !== "center") hold = setInterval(() => move(b.dataset.dir), 160);
  });
  ["pointerup", "pointerleave", "pointercancel"].forEach(ev => b.addEventListener(ev, stop));
});
// ---- mover (2.94.0): second stick = tracked vehicle; up = forward, down = back, sideways = turn on the spot ----
(function () {
  const pad = $("#mstick"), knob = $("#mknob"); if (!pad || !knob) return;
  let id = null, v = 0, w = 0, timer = null, busy = false, ox = 0, oy = 0;
  const show = (px, py) => { knob.style.transform = "translate(" + px + "px," + py + "px)"; };
  const send = () => { if (busy) return; busy = true; post("/api/mover", {v: v, w: w}).then(r => { busy = false; if (r && r.l != null) moverBars(r.l, r.r); }); };
  function track(e) {
    const R = pad.clientWidth / 2 - knob.clientWidth / 2;
    let dx = e.clientX - ox, dy = e.clientY - oy; const m = Math.hypot(dx, dy);
    if (m > R) { dx *= R / m; dy *= R / m; }
    show(dx, dy);
    const dz = R * 0.12, mm = Math.min(m, R), k = mm <= dz ? 0 : (mm - dz) / (R - dz) / (mm || 1) * R;
    w = Math.round(dx * k / R * 1000) / 1000; v = Math.round(-dy * k / R * 1000) / 1000;
  }
  function release() { if (id === null) return; id = null; v = w = 0; clearInterval(timer); timer = null; pad.classList.remove("on"); show(0, 0); busy = false; send(); }
  pad.addEventListener("pointerdown", e => { if (id !== null) return; e.preventDefault(); id = e.pointerId; pad.setPointerCapture(id);
    ox = e.clientX; oy = e.clientY; pad.classList.add("on"); track(e); busy = false; send(); timer = setInterval(send, 100); mvWake(); });
  pad.addEventListener("pointermove", e => { if (e.pointerId === id) { e.preventDefault(); track(e); mvWake(); } });
  ["pointerup", "pointercancel", "lostpointercapture"].forEach(ev => pad.addEventListener(ev, e => { if (e.pointerId === id) release(); }));
  window.addEventListener("blur", release); document.addEventListener("visibilitychange", () => { if (document.hidden) release(); });
})();
// 2.95.82: move the mover stick in full screen
(function () {
  const box = $("#vo-mctl"), g = $("#vo-mgrip"); if (!box || !g) return;
  const key = () => "mw-mvpos-" + (document.body.classList.contains("swapside") ? "l" : "r");
  const place = () => { let p = null; try { p = JSON.parse(localStorage.getItem(key()) || "null"); } catch (e) {}
    const W = box.offsetParent;
    if (!p || !W) { box.style.left = box.style.top = box.style.right = box.style.bottom = ""; return; }
    const w = W.clientWidth, h = W.clientHeight, bw = box.offsetWidth, bh = box.offsetHeight;
    box.style.left = Math.max(4, Math.min(w - bw - 4, p.x * w)) + "px"; box.style.top = Math.max(4, Math.min(h - bh - 4, p.y * h)) + "px";
    box.style.right = "auto"; box.style.bottom = "auto"; };
  let drag = null, lastTap = 0;
  g.addEventListener("pointerdown", e => { e.preventDefault(); e.stopPropagation();
    if (Date.now() - lastTap < 350) { try { localStorage.removeItem(key()); } catch (x) {} place(); lastTap = 0; toast("✥ " + t("Mover stick back in its place")); return; }
    lastTap = Date.now();
    const W = box.offsetParent; if (!W) return; const r = box.getBoundingClientRect();
    drag = {id: e.pointerId, dx: e.clientX - r.left, dy: e.clientY - r.top}; try { g.setPointerCapture(e.pointerId); } catch (x) {}
    box.classList.add("drag"); mvWake(); });
  g.addEventListener("pointermove", e => { if (!drag || e.pointerId !== drag.id) return; e.preventDefault();
    const W = box.offsetParent, wr = W.getBoundingClientRect();
    const x = Math.max(4, Math.min(wr.width - box.offsetWidth - 4, e.clientX - wr.left - drag.dx)), y = Math.max(4, Math.min(wr.height - box.offsetHeight - 4, e.clientY - wr.top - drag.dy));
    box.style.left = x + "px"; box.style.top = y + "px"; box.style.right = "auto"; box.style.bottom = "auto"; mvWake(); });
  const end = e => { if (!drag || (e && e.pointerId !== drag.id)) return; drag = null; box.classList.remove("drag");
    const W = box.offsetParent; if (!W) return;
    try { localStorage.setItem(key(), JSON.stringify({x: box.offsetLeft / W.clientWidth, y: box.offsetTop / W.clientHeight})); } catch (x) {} };
  ["pointerup", "pointercancel", "lostpointercapture"].forEach(n => g.addEventListener(n, end));
  addEventListener("resize", () => setTimeout(place, 120));
  new MutationObserver(() => setTimeout(place, 60)).observe(document.body, {attributes: true, attributeFilter: ["class"]});   // full screen on, ⇆ side
})();
let mvIdleT = null;
function mvWake() { const c = $("#vo-mctl"); if (!c) return; c.classList.remove("idle"); clearTimeout(mvIdleT); mvIdleT = setTimeout(() => c.classList.add("idle"), 3000); }
function moverBars(l, r) {
  const f = (el_, x) => { if (!el_) return; const h = Math.min(50, Math.abs(x) * 50); el_.style.height = h + "%"; el_.style.top = x >= 0 ? (50 - h) + "%" : "50%"; el_.style.background = x >= 0 ? "var(--grn)" : "var(--org)"; };
  f($("#mtl"), l); f($("#mtr"), r);
}
function moverPaint(s) {
  const m = s.mover || {}, av = !!m.avail;
  let show = false; try { show = localStorage.getItem("mw-mover-show") === "1"; } catch (e) {}   // 2.95.73: hidden unless switched on
  const on = av && show;
  if (document.body.classList.contains("moveravail") !== av) document.body.classList.toggle("moveravail", av);
  const mt = $("#mv-tog"); if (mt) { mt.classList.toggle("on", show); if (!mt.onclick) mt.onclick = () => {
    let v = false; try { v = localStorage.getItem("mw-mover-show") !== "1"; localStorage.setItem("mw-mover-show", v ? "1" : "0"); } catch (e) {}
    toast("🚜 " + t(v ? "Mover stick shown" : "Mover stick hidden")); moverPaint(s); }; }
  if (document.body.classList.contains("mover") !== on) document.body.classList.toggle("mover", on);
  const tx = $("#mstick-txt");
  if (tx && on) tx.textContent = "🚜 " + ((Math.abs(m.l) > 0.02 || Math.abs(m.r) > 0.02) ? "L " + Math.round(m.l * 100) + " % · R " + Math.round(m.r * 100) + " %" : t("Mover") + (m.test ? " (" + t("test only - nothing moves") + ")" : m.sim ? " (" + t("simulated") + ")" : ""));
  if (on) moverBars(m.l || 0, m.r || 0);
  const st = $("#mover-st"); if (st) st.textContent = (on ? "✅ " : "⚪ ") + (m.msg || "");
}
function moverExtras(d) {
  const box = el("div", "auxbox"); const st = el("div", "mut"); st.id = "mover-st"; st.style.whiteSpace = "pre-wrap";
  box.append(el("div", "mut", t("A tracked vehicle under MoveEye: the second stick drives it (up = forward, down = back, sideways = turn on the spot). The motor driver (Motor HAT with PCA9685 + TB6612 on I2C) is found by itself - without it the stick stays hidden. Without a new command for 0.6 s both tracks stop.")), st);
  d.appendChild(box);
}
// ---- joystick: deflection is sent ~10x per second, the server moves the camera proportionally ----
(function () {
  const pad = $("#stick"), knob = $("#knob");
  let id = null, vx = 0, vy = 0, timer = null, busy = false, ox = 0, oy = 0;
  const radius = () => pad.clientWidth / 2 - knob.clientWidth / 2;
  function show(px, py) { knob.style.transform = "translate(" + px + "px," + py + "px)"; }
  function send() {
    if (busy) return;
    busy = true;
    post("/api/stick", {x: vx, y: vy, speed: parseFloat($("#stick-speed").value)}).then(r => { busy = false; if (r && r.ok) showPos(r.pan, r.tilt); });
  }
  // the point where the finger lands is the middle (a finger never hits the exact centre - and phones report the touch a bit
  // above the finger): only the movement from there counts; a small dead zone keeps the camera still while the finger rests
  function track(e) {
    const R = radius();
    let dx = e.clientX - ox, dy = e.clientY - oy;
    const m = Math.hypot(dx, dy);
    if (m > R) { dx *= R / m; dy *= R / m; }
    show(dx, dy);
    const dz = R * 0.12, mm = Math.min(m, R);
    const k = mm <= dz ? 0 : (mm - dz) / (R - dz) / (mm || 1) * R;
    vx = Math.round(dx * k / R * 1000) / 1000; vy = Math.round(-dy * k / R * 1000) / 1000;      // up is positive
  }
  function release() {
    if (id === null) return;
    id = null; vx = vy = 0; clearInterval(timer); timer = null;
    pad.classList.remove("on"); show(0, 0);
    busy = false; send();                                       // tell the server the stick is back in the middle
  }
  pad.addEventListener("pointerdown", e => {
    if (id !== null) return;
    e.preventDefault(); id = e.pointerId; pad.setPointerCapture(id);
    ox = e.clientX; oy = e.clientY;
    pad.classList.add("on"); track(e); busy = false; send();
    timer = setInterval(send, 100);
  });
  pad.addEventListener("pointermove", e => { if (e.pointerId === id) { e.preventDefault(); track(e); } });
  ["pointerup", "pointercancel", "lostpointercapture"].forEach(ev => pad.addEventListener(ev, e => { if (e.pointerId === id) release(); }));
  addEventListener("blur", release);
  document.addEventListener("visibilitychange", () => { if (document.hidden) release(); });
  pad.addEventListener("contextmenu", e => e.preventDefault());
  $("#stick-center").addEventListener("click", () => move("center"));
  try { const s = localStorage.getItem("mw-stick-speed"); if (s) $("#stick-speed").value = s; } catch (e) {}
  $("#stick-speed").addEventListener("change", e => { try { localStorage.setItem("mw-stick-speed", e.target.value); } catch (x) {} });
  document.body.classList.remove("padmode");                       // only the joystick now
  try { localStorage.removeItem("mw-ctl"); } catch (e) {}
})();

// ---- phone / tablet upright: small live picture in a corner while the big one is scrolled away ----
// The picture element itself moves into the corner and back (no second stream, no extra data). Tap: back to the big
// picture. Drag: into another corner (kept per device). ✕: away until the big picture was in view again.
(function () {
  const pip = $("#pip"), slot = pip && pip.querySelector(".pip-in"), img = $("#video"), wrap = img && img.parentNode;
  if (!pip || !img || !wrap || !("IntersectionObserver" in window)) return;
  const mq = matchMedia("(max-width: 960px)");
  let closed = false, seen = true;
  try { pip.dataset.c = localStorage.getItem("mw-pip-corner") || "br"; } catch (e) {}
  img.draggable = false;
  function show(on) {
    on = !!on && mq.matches && !videoOnly && !closed && wrap.offsetParent !== null;
    if (on === !pip.hidden) return;
    if (on) { wrap.style.minHeight = wrap.offsetHeight + "px"; slot.appendChild(img); pip.hidden = false; }
    else { pip.hidden = true; wrap.insertBefore(img, wrap.firstChild); wrap.style.minHeight = ""; }
  }
  window.pipShow = show;
  new IntersectionObserver(es => es.forEach(e => {
    seen = e.isIntersecting && e.intersectionRatio > 0.2;
    if (seen) closed = false;
    show(!seen);
  }), {threshold: [0, 0.2, 0.5, 1]}).observe(wrap);
  const re = () => show(!seen);
  mq.addEventListener ? mq.addEventListener("change", re) : mq.addListener(re);
  $("#pip-x").addEventListener("pointerdown", e => e.stopPropagation());
  $("#pip-x").addEventListener("click", e => { e.stopPropagation(); closed = true; show(false); });
  let st = null;
  pip.addEventListener("pointerdown", e => { if (e.target.id === "pip-x") return; st = {x: e.clientX, y: e.clientY, moved: false};
    try { pip.setPointerCapture(e.pointerId); } catch (x) {} });
  pip.addEventListener("pointermove", e => { if (!st) return; const dx = e.clientX - st.x, dy = e.clientY - st.y;
    if (Math.hypot(dx, dy) > 10) st.moved = true;
    if (st.moved) pip.style.transform = "translate(" + dx + "px," + dy + "px)"; });
  pip.addEventListener("pointerup", e => {
    if (!st) return; const moved = st.moved; st = null; pip.style.transform = "";
    if (!moved) { $("#vcard").scrollIntoView({behavior: "smooth", block: "start"}); return; }
    const c = (e.clientY < innerHeight / 2 ? "t" : "b") + (e.clientX < innerWidth / 2 ? "l" : "r");
    pip.dataset.c = c; try { localStorage.setItem("mw-pip-corner", c); } catch (x) {}
  });
  pip.addEventListener("pointercancel", () => { st = null; pip.style.transform = ""; });
  window.pipAlarm = n => pip.classList.toggle("alarm", n > 0);
})();

// ---- phone: stick directly under the picture (portrait) or right next to it (landscape) ----
(function () {
  const left = $("#ctl-left"), home = left.parentNode, slot = $("#mctl");
  const allb = $("#allbtns"), allHome = allb.parentNode, mb = $("#mbtns");
  const mqPhone = matchMedia("(max-width: 760px), (max-height: 520px) and (orientation: landscape)");
  const mqLand = matchMedia("(orientation: landscape) and (max-height: 520px)");
  let was = null;
  function place() {
    const live = document.body.dataset.tab === "live";                              // 2.98.26: the Live tab arranges itself (part 536)
    const phone = mqPhone.matches && !live, land = phone && mqLand.matches;
    if (phone && left.parentNode !== slot) slot.appendChild(left);
    if (!phone && left.parentNode !== home) home.insertBefore(left, home.firstChild);
    const sr = $("#srch");                                                          // phone, tablet, computer: two symbols next to the search
    if (sr && allb.parentNode !== sr) sr.insertBefore(allb, $("#srch-none"));
    if (!sr && allb.parentNode !== allHome) allHome.insertBefore(allb, allHome.firstChild);
    if (sr) sr.classList.add("withall");
    document.body.classList.toggle("mobctl", phone); document.body.classList.toggle("mobland", land);
    if (land && was !== "land") landFit();                                          // picture + stick fill the screen
    was = land ? "land" : (phone ? "phone" : "desk");
  }
  // after turning the phone the browser settles its size and scroll position in several steps (address bar, restored scroll),
  // so the picture is put in the middle of the screen a few times during the first second
  let fitUntil = 0;
  function fitNow() {
    if (!document.body.classList.contains("mobland") || videoOnly) return;
    const c = $("#vcard").getBoundingClientRect(), vh = (window.visualViewport ? visualViewport.height : innerHeight);
    const y = scrollY + c.top - Math.max(0, (vh - c.height) / 2);
    if (Math.abs(y - scrollY) > 2) scrollTo(0, Math.max(0, y));
  }
  function landFit() { fitUntil = Date.now() + 1200; [60, 250, 500, 900, 1300].forEach(ms => setTimeout(fitNow, ms)); }
  addEventListener("resize", () => { if (Date.now() < fitUntil) fitNow(); });
  if (window.visualViewport) visualViewport.addEventListener("resize", () => { if (Date.now() < fitUntil) fitNow(); });
  addEventListener("orientationchange", () => setTimeout(() => { place(); if (document.body.classList.contains("mobland")) landFit(); }, 50));
  [mqPhone, mqLand].forEach(m => m.addEventListener ? m.addEventListener("change", place) : m.addListener(place));
  place();
})();

const KEYS = {ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down", Home: "center"};
addEventListener("keydown", e => {
  if (e.key === "F11") { e.preventDefault(); pageFullscreen(); return; }
  if (e.key === "Escape" && videoOnly) { setVideoOnly(false); return; }
  if (KEYS[e.key] && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); move(KEYS[e.key]); }
});

// remember which cards are open (per browser)
function secKey(d) { return "mw-open:" + (d.dataset.view || d.querySelector("summary").textContent); }
function initSections() {
  document.querySelectorAll("details.card, details.sub:not(.inline), details.adv").forEach(d => {
    try { const v = localStorage.getItem(secKey(d)); if (v !== null) d.open = (v === "1"); } catch (e) {}
    d.addEventListener("toggle", () => { try { localStorage.setItem(secKey(d), d.open ? "1" : "0"); } catch (e) {} });
  });
}
// ---- setup assistant: first start (and System -> "Setup assistant"): language, name, push (ntfy with QR code), password, QR codes ----
const WZ = {"What is MoveEye for?": "Wofür brauchst du MoveEye?", "Choose what fits - «Simple» then shows only the settings you need. You can change it later (Settings → Setup).": "Wähle, was passt – «Einfach» zeigt dann nur die Einstellungen, die du brauchst. Später änderbar (Einstellungen → Setup).",
  "Camping: tent, caravan": "Camping: Zelt, Wohnwagen", "House and garden": "Haus und Garten", "Watching animals": "Tiere beobachten", "Holiday house, alpine hut": "Ferienhaus, Maiensäss",
  "In the room: wake-up alarm": "Im Zimmer: Wecker", "everything (not chosen)": "alles (nichts gewählt)", "Welcome to MoveEye": "Willkommen bei MoveEye", "Set up in three short steps - takes about 3 minutes.": "In drei kurzen Schritten eingerichtet – dauert etwa 3 Minuten.",
  "Language": "Sprache", "Name of this device (optional)": "Name dieses Geräts (freiwillig)", "e.g. camper, garden": "z. B. Wohnmobil, Garten",
  "Push messages to the phone": "Push-Nachrichten aufs Handy", "1. Install the free app «ntfy» (App Store / Play Store).": "1. Die kostenlose App «ntfy» installieren (App Store / Play Store).",
  "2. In the app: + → enter the topic below (and the server, if it is not the default one) - or open this code with the phone camera.":
    "2. In der App: + → das Thema unten eintragen (und den Server, falls nicht der Standard) – oder diesen Code mit der Handy-Kamera öffnen.",
  "Server": "Server", "Topic (like a secret channel name)": "Thema (wie ein geheimer Kanalname)", "Send test message": "Test-Nachricht senden",
  "Sent - did it arrive on the phone?": "Gesendet – ist sie auf dem Handy angekommen?", "Skip": "Überspringen", "Next": "Weiter", "Back": "Zurück",
  "Password for this page": "Passwort für diese Seite", "Without a password everybody in the same network (and with the link) can watch and switch everything.":
    "Ohne Passwort kann jeder im gleichen Netz (und mit dem Link) zuschauen und alles schalten.", "Password (6-64 characters)": "Passwort (6–64 Zeichen)",
  "Repeat password": "Passwort wiederholen", "Continue without a password (not recommended)": "Ohne Passwort weiter (nicht empfohlen)",
  "The passwords are not the same": "Die Passwörter sind nicht gleich", "A password is set already. Enter a new one only to change it.":
    "Es ist schon ein Passwort gesetzt. Nur zum Ändern ein neues eingeben.", "The password was given on the command line (--web-password).":
    "Das Passwort wurde beim Start angegeben (--web-password).", "Done!": "Fertig!",
  "Open MoveEye on other devices with these codes. On the phone: Share → «Add to Home Screen» - then it starts like an app.":
    "Mit diesen Codes öffnest du MoveEye auf weiteren Geräten. Auf dem Handy: Teilen → «Zum Home-Bildschirm» – dann startet es wie eine App.",
  "Home network": "Heimnetz", "Own Wi-Fi of the device": "Eigenes WLAN des Geräts", "On the road (Tailscale)": "Unterwegs (Tailscale)",
  "🖨 Quick start card with QR codes": "🖨 Kurzanleitung mit QR-Codes", "Let's go": "Los geht's", "Later": "Später",
  "After this the page asks for the new password once (user name: anything).": "Danach fragt die Seite einmal nach dem neuen Passwort (Benutzername: beliebig)."};
const wt = s => (LANG === "de" && WZ[s]) || (window.LX ? LX(s) : "") || (LANG === "rm" && WZ[s]) || s;
async function setupWizard(force) {
  let S; try { S = await (await fetch("/api/setup", {cache: "no-store"})).json(); } catch (e) { return; }
  if (S.locked || (S.done && !force)) return;
  const qrs = {};
  const qr = async u => { if (!qrs[u]) { try { qrs[u] = await (await fetch("/api/qr?t=" + encodeURIComponent(u))).text(); } catch (e) { qrs[u] = ""; } } return qrs[u]; };
  for (const a of S.addresses || []) await qr(a.url);                      // load before the password is set
  let ov = $("#wiz"); if (ov) ov.remove();
  ov = el("div"); ov.id = "wiz"; document.body.appendChild(ov);
  const card = el("div", "card"); ov.appendChild(card);
  let step = 0, pwNew = false;
  const nt = (S.notify_type === "ntfy" && /^https:\/\/[^/]+\/[^/]+$/.test(S.notify_url || "")) ? S.notify_url : "";
  let server = nt ? nt.replace(/\/[^/]+$/, "") : "https://ntfy-me.com";
  let topic = nt ? nt.replace(/^.*\//, "") : "mw-" + Array.from(crypto.getRandomValues(new Uint8Array(8)), b => "abcdefghijkmnpqrstuvwxyz23456789"[b % 32]).join("");
  let name = S.device_name || "";
  const close = () => ov.remove();
  async function render() {
    card.textContent = "";
    const later = el("button", "later", wt("Later")); later.type = "button";
    later.onclick = async () => { await post("/api/setup", {step: "skip", lang: LANG}); close(); };
    const dots = el("div", "dots"); for (let i = 0; i < 5; i++) { const d = el("i"); if (i <= step) d.classList.add("on"); dots.appendChild(d); }
    card.append(later, dots);
    const nav = el("div", "wnav"), back = el("button", "sec", wt("Back")), next = el("button", "", wt("Next"));
    back.type = next.type = "button"; back.onclick = () => { step--; render(); };
    const err = el("div", "err");
    if (step === 0) {
      card.append(el("h2", "", "👋 " + wt("Welcome to MoveEye")), el("p", "mut", wt("Set up in three short steps - takes about 3 minutes.")));
      card.appendChild(el("label", "", wt("Language")));
      const lg = el("div", "seg lang");
      Object.keys(LANGN).forEach(k => { const b = el("button", LANG === k ? "on" : "", LANGN[k]); b.type = "button";
        b.onclick = () => {
          if (["fr", "it", "rm"].includes(k) || ["fr", "it", "rm"].includes(LANG)) { langSet(k); return; }   // needs its translation file
          try { localStorage.setItem("mw-lang", k); } catch (e) {} LANG = k; applyI18n(); render(); }; lg.appendChild(b); });
      card.appendChild(lg);
      card.appendChild(el("label", "", wt("Name of this device (optional)")));
      const ni = el("input"); ni.type = "text"; ni.maxLength = 40; ni.value = name; ni.placeholder = wt("e.g. camper, garden"); ni.oninput = () => { name = ni.value; };
      card.appendChild(ni);
      next.onclick = async () => { const r = await post("/api/setup", {step: "basics", ui_lang: LANG, device_name: name.trim(), lang: LANG});
        if (!r.ok) { err.textContent = r.error || "error"; return; } step = 1; render(); };
      nav.append(next);
    } else if (step === 1) {                      // 2.98.9: what is MoveEye for? - «Simple» shows only what fits
      card.append(el("h2", "", "🧭 " + wt("What is MoveEye for?")), el("p", "mut", wt("Choose what fits - «Simple» then shows only the settings you need. You can change it later (Settings → Setup).")));
      const L = [["camping", "⛺", "Camping: tent, caravan"], ["home", "🏡", "House and garden"], ["wild", "🦌", "Watching animals"],
                 ["holiday", "🏔", "Holiday house, alpine hut"], ["room", "⏰", "In the room: wake-up alarm"], ["", "🧰", "everything (not chosen)"]];
      const g = el("div", "usegrid");
      L.forEach(([v, ic, n]) => { const b = el("button", "sec useopt" + ((S.use_case || "") === v ? " on" : ""), ""); b.type = "button";
        b.append(el("span", "ic", ic), el("span", "", wt(n)));
        b.onclick = async () => { const r = await post("/api/setup", {step: "usecase", use: v, lang: LANG}); if (!r.ok) { err.textContent = r.error || "error"; return; }
          S.use_case = v; step = 2; render(); }; g.appendChild(b); });
      card.appendChild(g);
      const skip = el("button", "sec", wt("Skip")); skip.type = "button"; skip.onclick = () => { step = 2; render(); };
      nav.append(back, skip);
    } else if (step === 2) {
      card.append(el("h2", "", "🔔 " + wt("Push messages to the phone")), el("p", "", wt("1. Install the free app «ntfy» (App Store / Play Store).")),
                  el("p", "", wt("2. In the app: + → enter the topic below (and the server, if it is not the default one) - or open this code with the phone camera.")));
      const box = el("div", "qr");
      const upd = async () => { box.innerHTML = await qr(server.replace(/\/+$/, "") + "/" + topic); };
      card.appendChild(el("label", "", wt("Topic (like a secret channel name)")));
      const ti = el("input"); ti.type = "text"; ti.value = topic; ti.maxLength = 64; ti.oninput = () => { topic = ti.value.trim().replace(/[^A-Za-z0-9_-]/g, ""); };
      ti.onchange = upd; card.appendChild(ti);
      card.appendChild(el("label", "", wt("Server")));
      const si = el("input"); si.type = "text"; si.value = server; si.oninput = () => { server = si.value.trim(); }; si.onchange = upd; card.appendChild(si);
      card.appendChild(box); upd();
      const st = el("div", "mut"), tb = el("button", "sec", "📨 " + wt("Send test message")); tb.type = "button";
      const save = async () => { const r = await post("/api/setup", {step: "push", url: server.replace(/\/+$/, "") + "/" + topic, lang: LANG});
        if (!r.ok) { err.textContent = r.error || "error"; } return r.ok; };
      tb.onclick = async () => { if (!(await save())) return; const r = await post("/api/notify_test", {lang: LANG});
        st.textContent = r.ok ? "✓ " + wt("Sent - did it arrive on the phone?") : "⚠ " + (r.error || "error"); };
      const bt = el("div", "btns"); bt.appendChild(tb); card.append(bt, st);
      const skip = el("button", "sec", wt("Skip")); skip.type = "button"; skip.onclick = () => { step = 3; render(); };
      next.onclick = async () => { if (topic.length < 3) { step = 3; render(); return; } if (await save()) { step = 3; render(); } };
      nav.append(back, skip, next);
    } else if (step === 3) {
      card.append(el("h2", "", "🔒 " + wt("Password for this page")), el("p", "mut", wt("Without a password everybody in the same network (and with the link) can watch and switch everything.")));
      if (S.pw_cmdline) { card.appendChild(el("p", "", "✓ " + wt("The password was given on the command line (--web-password)."))); }
      else {
        if (S.has_pw) card.appendChild(el("p", "", "✓ " + wt("A password is set already. Enter a new one only to change it.")));
        card.appendChild(el("label", "", wt("Password (6-64 characters)")));
        const p1 = el("input"); p1.type = "password"; p1.autocomplete = "new-password"; card.appendChild(p1);
        card.appendChild(el("label", "", wt("Repeat password")));
        const p2 = el("input"); p2.type = "password"; p2.autocomplete = "new-password"; card.appendChild(p2);
        let without = null;
        if (!S.has_pw) { const l = el("label", "row"); l.style.fontWeight = "400"; without = el("input"); without.type = "checkbox";
          l.append(el("span", "", wt("Continue without a password (not recommended)")), without); card.appendChild(l); }
        card.appendChild(el("p", "mut", wt("After this the page asks for the new password once (user name: anything).")));
        next.onclick = async () => {
          const pw = p1.value;
          if (pw !== p2.value) { err.textContent = wt("The passwords are not the same"); return; }
          if (!pw && !S.has_pw && !(without && without.checked)) { err.textContent = wt("Password (6-64 characters)"); p1.focus(); return; }
          const r = await post("/api/setup", {step: "finish", password: pw, lang: LANG});
          if (!r.ok) { err.textContent = r.error || "error"; return; }
          pwNew = !!pw; step = 4; render();
        };
      }
      if (S.pw_cmdline) next.onclick = async () => { await post("/api/setup", {step: "finish", lang: LANG}); step = 4; render(); };
      nav.append(back, next);
    } else {
      card.append(el("h2", "", "✅ " + wt("Done!")), el("p", "mut", wt("Open MoveEye on other devices with these codes. On the phone: Share → «Add to Home Screen» - then it starts like an app.")));
      const g = el("div", "qrs");
      for (const a of S.addresses || []) {
        const c = el("div"), b = el("div", "qr"); b.innerHTML = qrs[a.url] || "";
        c.append(el("b", "", wt({lan: "Home network", hotspot: "Own Wi-Fi of the device", tailscale: "On the road (Tailscale)"}[a.kind] || a.kind)), b, el("div", "mut", a.url));
        g.appendChild(c);
      }
      card.appendChild(g);
      const lk = el("a", "btn sec", wt("🖨 Quick start card with QR codes")); lk.href = "/setup-card?lang=" + LANG; lk.target = "_blank";
      const bt = el("div", "btns"); bt.appendChild(lk); card.appendChild(bt);
      next.textContent = wt("Let's go"); next.onclick = () => { close(); if (pwNew) location.reload(); };
      nav.append(next);
    }
    card.append(err, nav);
  }
  render();
}
function allGroups() {                     // overview: every group open, the topics inside closed
  document.querySelectorAll("#settings details.grp").forEach(d => { if (!d.open) d.open = true; });
  document.querySelectorAll("#settings details.sub:not(.inline), #settings details.adv").forEach(d => { if (d.open) d.open = false; });
}
function allSections(open) { document.querySelectorAll("details.card, details.sub:not(.inline)").forEach(d => { if (d.open !== open) d.open = open; }); }

$("#video").addEventListener("dblclick", () => setVideoOnly(!videoOnly));
keepStream($("#video"));
let fsWas = false;
const fsChange = () => {                     // browser full screen ended (back gesture, Esc): leave video mode too
  const now = !!fsEl();
  if (fsWas && !now && videoOnly) { videoOnly = false; document.body.classList.remove("videoonly"); voStick(false); }
  fsWas = now;
};
document.addEventListener("fullscreenchange", fsChange);
document.addEventListener("webkitfullscreenchange", fsChange);
(async () => {
  applyHidden();
  if (!LANG || !THEME) {
    try { const a = await (await fetch("/api/appearance")).json(); LANG = LANG || a.lang; THEME = THEME || a.theme; }
    catch (e) { LANG = LANG || "en"; THEME = THEME || "dark"; }
  }
  applyTheme(); applyI18n();
  await build(); regroup(); applyHidden(); initSections(); refresh(); setInterval(refresh, 700);
  setTimeout(() => setupWizard(false), 600);
})();
/*ALERTS*/
</script></body></html>
"""


SIMTOOLS_JS = r"""
// ---- simulator tools in the tab Simulator (2.95.53): Aufstell-Planer, alarm replay, AI test ----
Object.assign(I18N.de, {"Training set for an own AI model (YOLO)": "Trainingspaket für ein eigenes KI-Modell (YOLO)", "Make the training pack": "Trainingspaket machen",
  "The simulator makes the pictures and saves a ZIP on the desktop of its PC (about 2 s per picture).": "Der Simulator macht die Bilder und legt ein ZIP auf den Schreibtisch seines PCs (etwa 2 s pro Bild).",
  "Variety: normal": "Vielfalt: normal", "Variety: high": "Vielfalt: hoch", "Variety: high (recommended)": "Vielfalt: hoch (empfohlen)", "Delete old AI data": "Alte KI-Daten löschen", "days": "Tage",
  "Delete all training packs on the PC of the simulator except the newest one? The AI model stays.": "Alle Trainingspakete auf dem PC des Simulators ausser dem neuesten löschen? Das KI-Modell bleibt.",
  "Cleaned up by itself: after every new pack the newest 3 stay, nothing older than 30 days (the newest always stays). The AI model is never deleted.": "Aufräumen von selbst: nach jedem neuen Paket bleiben die neuesten 3, nichts älter als 30 Tage (das neueste bleibt immer). Das KI-Modell wird nie gelöscht."});
Object.assign(I18N.de, {"pictures": "Bilder", "Tag": "Anhänger", "Aufstell-Planer in the simulator": "Aufstell-Planer im Simulator", "open in the window of the simulator": "im Fenster des Simulators geöffnet", "Take over the patrol of the planner": "Patrouille vom Planer übernehmen", "Patrol set": "Patrouille gesetzt", "of the area in view": "des Bereichs im Blick", "Alarm replay in 3D": "Alarm-Rückblick in 3D", "Play in the simulator": "Im Simulator abspielen", "plays in the window of the simulator": "läuft im Fenster des Simulators", "no alarms yet": "noch keine Alarme", "replay-note": "Zeigt im 3D-Simulator nach, wer woher kam und wohin MoveEye geschaut hat (15 s vor bis 20 s nach dem Alarm). Hilft, Fehlalarme zu verstehen. Die Positionen sind geschätzt (aus Bildposition und Grösse).", "AI test with simulator pictures": "KI-Prüfung mit Simulator-Bildern", "dset-note": "Der Simulator macht Bilder mit Person oder Tier – bei Tag, Abend, Nacht mit Infrarot, Regen und Nebel, nah und fern – und weiss, wo sie sind. MoveEye lässt seine KI (oder die PC-Rechenhilfe) darüber laufen und zählt Treffer, Fehlschläge und falsche Personen. Dauert pro Bild etwa 3 Sekunden.", "Start the test": "Prüfung starten", "found": "erkannt", "false persons": "falsche Personen", "near (under 8 m)": "nah (unter 8 m)", "far (8 m and more)": "fern (ab 8 m)", "AI time per picture": "KI-Zeit pro Bild", "Training pictures (ZIP)": "Trainingsbilder (ZIP)", "Abend": "Abend", "Nacht (Infrarot)": "Nacht (Infrarot)", "Regen": "Regen", "Nebel": "Nebel", "Nacht + Regen": "Nacht + Regen", "person": "Person", "fox": "Fuchs", "deer": "Reh", "dog": "Hund", "cat": "Katze", "boar": "Wildschwein", "the simulator makes the pictures …": "der Simulator macht die Bilder …", "done": "fertig", "Simulator tools": "Simulator-Werkzeuge"});
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"replay-note": "Shows in the 3D simulator who came from where and where MoveEye looked (15 s before to 20 s after the alarm). Helps to understand false alarms. The positions are estimated (from the spot and size in the picture).", "dset-note": "The simulator makes pictures with a person or an animal - by day, dusk, night with infrared, rain and fog, near and far - and knows where they are. MoveEye runs its AI (or the PC helper) on them and counts hits, misses and false persons. About 3 seconds per picture.", "Tag": "day", "Abend": "dusk", "Nacht (Infrarot)": "night (infrared)", "Regen": "rain", "Nebel": "fog", "Nacht + Regen": "night + rain"});
(async function () {
  for (let i = 0; i < 30 && !LANG; i++) await new Promise(r => setTimeout(r, 100));     // after the language is known
  const box = document.getElementById("st-box"); if (!box) return;
  const P = (d) => post("/api/sim", Object.assign({lang: LANG}, d));
  const pl = el("div", "btns");
  const plo = el("button", "sec", "🗺 " + t("Aufstell-Planer in the simulator")); plo.type = "button";
  plo.onclick = async () => { const r = await P({action: "planner_open"}); toast(r.ok ? "✓ " + t("open in the window of the simulator") : "⚠ " + (r.error || t("error"))); };
  const pla = el("button", "sec", "✓ " + t("Take over the patrol of the planner")); pla.type = "button";
  pla.onclick = async () => { const r = await P({action: "planner_apply"}); toast(r.ok ? "✓ " + t("Patrol set") + " · " + r.planner.pct + " % " + t("of the area in view") : "⚠ " + (r.error || t("error"))); };
  pl.append(plo, pla);
  const rb = el("div", ""); rb.style.marginTop = "14px"; rb.append(el("b", "", "⏪ " + t("Alarm replay in 3D")));
  const rs = document.createElement("select"); rs.style.cssText = "width:100%;margin-top:6px";
  const rr = el("div", "btns"); const rgo = el("button", "", "▶ " + t("Play in the simulator")); rgo.type = "button";
  const rsp = document.createElement("select"); [1, 2, 4].forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v + "×"; rsp.appendChild(o); });
  rgo.onclick = async () => { if (!rs.value) return; const r = await P({action: "replay", id: rs.value, speed: +rsp.value}); toast(r.ok ? "✓ " + t("plays in the window of the simulator") : "⚠ " + (r.error || t("error"))); };
  const rst = el("button", "sec", "⏹"); rst.type = "button"; rst.onclick = () => P({action: "replay", stop: true});
  rr.append(rgo, rsp, rst); rb.append(rs, rr, el("div", "mut", t("replay-note")));
  const db = el("div", ""); db.style.marginTop = "14px"; db.append(el("b", "", "🧪 " + t("AI test with simulator pictures")), el("div", "mut", t("dset-note")));
  const dr = el("div", "btns"); const dn = document.createElement("select"); [12, 24, 48].forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v + " " + t("pictures"); dn.appendChild(o); }); { const og = document.createElement("option"); og.value = "game"; og.textContent = "🎮 " + t("missed pictures from the game (hard cases)"); dn.appendChild(og); } dn.value = "24";
  const dgo = el("button", "", "▶ " + t("Start the test")); dgo.type = "button"; const dout = el("div", "");
  const dpaint = j => { const D = (j && j.dataset) || {}; dout.textContent = "";
    if (D.busy) { dout.appendChild(el("div", "mut", "⏳ " + D.pct + " % · " + t(D.msg))); setTimeout(async () => dpaint(await P({action: "dataset"})), 2000); return; }
    if (D.msg && D.msg.startsWith("error")) dout.appendChild(el("div", "err", "⚠ " + D.msg));
    const S = D.sum; if (!S) return;
    dout.appendChild(el("div", "", S.found + " / " + S.n + " " + t("found") + " · " + S.false + " " + t("false persons")));
    const tb = document.createElement("table"); const row = (a, b) => { const tr = document.createElement("tr"); tr.append(el("td", "", a), el("td", "", b)); tb.appendChild(tr); };
    Object.entries(S.by_cond).forEach(([k, v]) => row(t(k), v.found + "/" + v.n + " · " + v.pct + " %"));
    Object.entries(S.by_kind).forEach(([k, v]) => row(t(k), v.found + "/" + v.n + " · " + v.pct + " %"));
    row(t("near (under 8 m)"), S.near + " %"); row(t("far (8 m and more)"), S.far + " %"); row(t("AI time per picture"), S.ms + " ms (" + S.where + ")"); dout.appendChild(tb);
    const z = document.createElement("a"); z.className = "btn sec"; z.href = "/api/dataset.zip"; z.textContent = "⬇ " + t("Training pictures (ZIP)"); dout.appendChild(z); };
  dgo.onclick = async () => { const r = await P({action: "dataset", start: true, n: dn.value === "game" ? "game" : +dn.value}); if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; } dpaint(r); };
  dr.append(dn, dgo); db.append(dr, dout);
  // KI-Daten (197): a training pack (YOLO) with «Vielfalt» like in the simulator; the packs on its PC, «Delete old AI data»
  const xb = el("div", ""); xb.style.marginTop = "14px"; xb.append(el("b", "", "📦 " + t("Training set for an own AI model (YOLO)")));
  const xr = el("div", "btns"), xn = document.createElement("select"), xvf = document.createElement("select");
  [200, 500, 1000, 2000].forEach(n => { const o = document.createElement("option"); o.value = n; o.textContent = n + " " + t("pictures"); if (n === 500) o.selected = true; xn.appendChild(o); });
  [["hoch", "Variety: high (recommended)"], ["normal", "Variety: normal"]].forEach(([v, l]) => { const o = document.createElement("option"); o.value = v; o.textContent = t(l); xvf.appendChild(o); });
  const xgo = el("button", "", "📦 " + t("Make the training pack")); xgo.type = "button"; const xout = el("div", "mut");
  const kd = el("div", ""); kd.id = "kidata-box"; kd.style.marginTop = "8px"; const kdl = el("div", ""), kdr = el("div", "mut", t("Cleaned up by itself: after every new pack the newest 3 stay, nothing older than 30 days (the newest always stays). The AI model is never deleted."));
  const kdb = el("button", "sec", "🧹 " + t("Delete old AI data")); kdb.type = "button"; kdb.style.marginTop = "6px";
  const kdPaint = r => { kdl.textContent = ""; if (!r || !r.ok) { kdl.appendChild(el("div", "mut", "⚠ " + ((r && r.error) || t("error")))); kdb.hidden = true; return; }
    kdl.appendChild(el("div", "", r.text || "")); kdb.hidden = (r.packs || []).length < 2;
    (r.packs || []).forEach(p => kdl.appendChild(el("div", "mut", (p.newest ? "⭐ " : "· ") + p.name + " · " + p.mb + " MB · " + p.age_days + " " + t("days") + (p.vielfalt === "hoch" ? " · " + t("Variety: high") : "")))); };
  const kdLoad = async () => kdPaint(await P({action: "dataset", packs: true}));
  xgo.onclick = async () => { xgo.disabled = true; const r = await P({action: "dataset", export: true, n: +xn.value, vielfalt: xvf.value}); xgo.disabled = false;
    if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; }
    xout.textContent = t("The simulator makes the pictures and saves a ZIP on the desktop of its PC (about 2 s per picture).") + " " + ((r.export || {}).msg || ""); };
  kdb.onclick = async () => { if (!confirm(t("Delete all training packs on the PC of the simulator except the newest one? The AI model stays."))) return;
    kdb.disabled = true; const r = await P({action: "dataset", clean: true}); kdb.disabled = false; kdPaint(r); };
  xr.append(xn, xvf, xgo); kd.append(kdl, kdb, kdr); xb.append(xr, xout, kd);
  document.getElementById("c-tools").addEventListener("toggle", e => { if (e.target.open) kdLoad(); });
  box.append(pl, rb, db, xb); kdLoad();
  let K = "";
  const poll = async () => { try { const st = (await (await fetch("/api/state", {cache: "no-store"})).json()).state || {};
      const S = st.sim || {}; document.getElementById("c-tools").hidden = !(S.on && S.ok);
      const AT = st.alarm_tracks || [], k = AT.map(a => a.id + a.n).join(",");
      if (k !== K || !rs.options.length) { K = k; const cur = rs.value; rs.textContent = "";
        if (!AT.length) { const o = document.createElement("option"); o.value = ""; o.textContent = t("no alarms yet"); rs.appendChild(o); }
        AT.forEach(a => { const o = document.createElement("option"); o.value = a.id; o.textContent = new Date(a.t * 1000).toLocaleString([], {day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"}) + " · " + t(a.kind) + " · " + a.sec + " s"; rs.appendChild(o); });
        if ([...rs.options].some(o => o.value === cur)) rs.value = cur; } } catch (e) {}
    setTimeout(poll, 5000); };
  setTimeout(poll, 800);
  (async () => { const r = await P({action: "dataset"}); if (r && r.ok && r.dataset && (r.dataset.sum || r.dataset.busy)) dpaint(r); })();
})();
"""
SIMTUN_JS = r"""Object.assign(I18N.de, {"Simulator behind a firewall": "Simulator hinter einer Firewall", "tunnel-note": "Läuft der Simulator auf einem PC oder einer virtuellen Maschine ohne Administratorrechte, lässt dessen Firewall MoveEye nicht hinein. Dann verbindet sich der Simulator selbst nach aussen zu MoveEye (Port 8766) – das erlaubt jede Firewall. Im Simulator einmal die Adresse von MoveEye und diesen Code eintragen.", "Code": "Code", "code": "Code", "In the simulator: Verbindung → «Tunnel zu MoveEye»: address": "Im Simulator: Verbindung → «Tunnel zu MoveEye»: Adresse", "Simulator connected through the tunnel": "Simulator über den Tunnel verbunden", "no simulator through the tunnel yet": "noch kein Simulator über den Tunnel", "Switch off": "Ausschalten", "Switch on": "Einschalten", "New code": "Neuer Code", "off": "aus",
  "port": "Port", "MoveEye listens on port": "MoveEye wartet auf Port", "could not open port": "Port kann nicht geöffnet werden", "In the simulator the field shows": "Im Simulator muss dasselbe stehen",
  "last try from": "Letzter Versuch von", "ago": "vor", "code accepted": "Code richtig", "wrong code": "Code falsch – im Simulator den Code von hier eintragen", "no try yet": "Noch kein Versuch eines Simulators angekommen – stimmt die Adresse? Ist «Tunnel verwenden» im Simulator an?",
  "announces itself but does not answer - its firewall or security software blocks MoveEye: use the tunnel": "meldet sich im Netz, antwortet aber nicht – die Firewall oder Sicherheitssoftware des PCs sperrt MoveEye: den Tunnel verwenden (unten)",
  "Direct connection": "Direkte Verbindung", "MoveEye fetches the pictures from the simulator on port": "Ohne Tunnel holt MoveEye die Bilder beim Simulator auf Port"});
I18N.en = I18N.en || {}; Object.assign(I18N.en, {"tunnel-note": "If the simulator runs on a PC or a virtual machine without admin rights, its firewall does not let MoveEye in. Then the simulator itself connects out to MoveEye (port 8766) - every firewall allows that. Enter the address of MoveEye and this code once in the simulator."});

// ---- tunnel (2.95.54) ----
(async function () {
  for (let i = 0; i < 30 && !LANG; i++) await new Promise(r => setTimeout(r, 100));
  const box = document.getElementById("tun-box"); if (!box) return; let K = "";
  const paint = j => { const T = j.tunnel, k = JSON.stringify([T, j.address]); if (k === K) return; K = k; box.textContent = "";
    const big = el("div", ""); big.style.cssText = "font-size:22px;font-weight:700;margin:4px 0";
    big.textContent = T.on ? t("Code") + ": " + T.code : t("off"); box.appendChild(big);
    const host = (j.address || "").replace(/^https?:\/\//, "").replace(/[:\/].*$/, "");
    if (T.on) box.appendChild(el("div", "", t("In the simulator: Verbindung → «Tunnel zu MoveEye»: address") + " " + host + ", " + t("code") + " " + T.code));
    if (T.on) box.appendChild(qrBtn(j.address || location.origin + "/", qrT("Simulator connection (tunnel)"), {secret: true, note: t("Code") + ": " + T.code + " · " + qrT("In the simulator (Verbindung → «Tunnel zu MoveEye») paste the address and type the code.")}));   // 585
    if (T.on) {                                                         // 2.95.60: the ports, to compare with the simulator
      const pt = el("div", T.listen && T.listen !== "ok" ? "" : "mut");
      pt.textContent = T.listen && T.listen !== "ok" ? "⚠ " + t("could not open port") + " " + T.port + ": " + T.listen
        : "🔌 " + t("MoveEye listens on port") + " " + T.port + " · " + t("In the simulator the field shows") + " «" + host + ":" + T.port + "»";
      box.appendChild(pt);
      const tr_ = T.try;
      box.appendChild(el("div", tr_ && !tr_.ok ? "" : "mut", tr_ ? (tr_.ok ? "✓ " : "✗ ") + t("last try from") + " " + tr_.peer + " (" + t("ago") + " " + tr_.ago + " s): " + t(tr_.ok ? "code accepted" : "wrong code") : "… " + t("no try yet")));
      box.appendChild(el("div", "mut", t("Direct connection") + ": " + t("MoveEye fetches the pictures from the simulator on port") + " " + T.sim_port));
    }
    box.appendChild(el("div", T.active ? "" : "mut", T.active ? "🟢 " + t("Simulator connected through the tunnel") + " (" + T.peer + ") · " + T.mb + " MB" : "⚪ " + t("no simulator through the tunnel yet")));
    const r = el("div", "btns");
    const b1 = el("button", "sec", T.on ? t("Switch off") : t("Switch on")); b1.type = "button"; b1.onclick = async () => paint(await post("/api/tunnel", {on: !T.on}));
    const b2 = el("button", "sec", "🔄 " + t("New code")); b2.type = "button"; b2.onclick = async () => paint(await post("/api/tunnel", {new_code: true}));
    r.append(b1, b2); box.appendChild(r); };
  const poll = async () => { try { paint(await (await fetch("/api/tunnel", {cache: "no-store"})).json()); } catch (e) {} setTimeout(poll, 4000); };
  poll();
})();
"""
SIM_PAGE = SIM_PAGE.replace("/*SIMMAP*/", SIMMAP_JS + SIMTOOLS_JS + SIMTUN_JS)
WEB_PAGE = WEB_PAGE.replace("/*SIMMAP*/", SIMMAP_JS)


