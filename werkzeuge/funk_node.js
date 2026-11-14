// Hilfe für werkzeuge/funk_test.py: führt den Code der Seite «Morse-Funk» des Besitzers in node aus - unverändert aus der Seite
// geschnitten (Decoder zwischen /*DECODER-START*/ und /*DECODER-END*/, die Funktionen prepTx und transmit), die Prüfsummen
// prüft funk_test.py. Dazu der Teil V2 von MoveEye (/*FUNK-V2-START*/ … /*FUNK-V2-END*/: Schlüssel, Audiodatei, Datei lesen).
// Kein Browser nötig: AudioContext und die Knöpfe sind nachgebaut, transmit schreibt jeden Ton als Liste.
//   node funk_node.js SEITE keystream SCHLUESSEL N                  -> JSON: die ersten N Werte seines Schlüsselstroms (V1, nur noch Vergleich)
//   node funk_node.js SEITE transmit  CFG_JSON SCHLUESSEL TEXT [NONCE] -> JSON: [[start s, Frequenz Hz, Länge s, Lautstärke], ...]
//                                                                     (mit Schlüssel: V2 wie der Knopf «Senden» - txPlan + sendPlanned)
//   node funk_node.js SEITE beeps     CFG_JSON SCHLUESSEL TEXT [NONCE] -> JSON: beepsOf (die Töne der Audiodatei) [[start, Hz, Länge], ...]
//   node funk_node.js SEITE wav       CFG_JSON SCHLUESSEL TEXT NONCE DATEI -> schreibt die Audiodatei der Seite (WAV, 22050 Hz)
//   node funk_node.js SEITE decode    CFG_JSON SCHLUESSEL RAW SR      -> JSON: [[Text, Modus], ...] (RAW = float32, Rate SR; wie «Audiodatei
//                                                                     einlesen»: decodeSamples, V2 geöffnet; Fehler als «!bad» / «!nokey»)
//   node funk_node.js SEITE v2seal    SCHLUESSEL NONCE KLARTEXT       -> JSON: die Zeichen nach dem Versionszeichen
//   node funk_node.js SEITE v2open    SCHLUESSEL ZEICHEN              -> JSON: {text, err}
"use strict";
const fs = require("fs"), vm = require("vm");
const [, , page, cmd, a1, a2, a3, a4, a5] = process.argv;
const src = fs.readFileSync(page, "utf8");
const cut = (a, b) => { const i = src.indexOf(a), j = src.indexOf(b, i); if (i < 0 || j < 0) throw new Error("not found: " + a); return src.slice(i, j); };
const fn = head => { const i = src.indexOf(head), j = src.indexOf("\n}\n", i); if (i < 0 || j < 0) throw new Error("not found: " + head); return src.slice(i, j + 3); };
const decoder = cut("/*DECODER-START*/", "/*DECODER-END*/") + "/*DECODER-END*/";
const v2 = cut("/*FUNK-V2-START*/", "/*FUNK-V2-END*/") + "/*FUNK-V2-END*/";
const prepTx = fn("function prepTx(");                     // (each function up to its closing brace at the start of a line)
const transmit = fn("async function transmit(");
const ctxObj = {TextEncoder, crypto: globalThis.crypto, console, Math, Uint8Array, Float32Array, DataView, ArrayBuffer, setTimeout: () => 0};
vm.createContext(ctxObj);
vm.runInContext("var cfg, key, ks = null, ctx, sendNodes = [], sendingUntil = 0, $, ensureCtx;\n" + decoder + "\n" + v2 + "\n" + prepTx + transmit
  + "\n;globalThis.__d={makeKeystream,makeDecoder,normText,ALPHA,PCODE,NA,v2Seal,v2Open,txPlan,sendPlanned,beepsOf,wavOf,decodeSamples,transmit};", ctxObj);
const D = ctxObj.__d;
(async () => {
  if (cmd === "keystream") {
    const ks = await D.makeKeystream(a1, +a2);
    process.stdout.write(JSON.stringify(ks || [])); return;
  }
  if (cmd === "v2seal") { process.stdout.write(JSON.stringify(await D.v2Seal(a3, a1, a2))); return; }
  if (cmd === "v2open") { process.stdout.write(JSON.stringify(await D.v2Open(a2 || "", a1))); return; }
  const cfg = JSON.parse(a1);
  vm.runInContext("cfg = " + JSON.stringify(cfg) + "; key = " + JSON.stringify(a2 || "") + ";", ctxObj);
  if (cmd === "transmit") {
    const beeps = [];
    // the AudioContext of the page, rebuilt: an oscillator + gain per beep; the gain ramps tell start and length
    const mk = {currentTime: 0, destination: {}, createOscillator() { const o = {frequency: {}, type: "", connect() {}, start(t) { o.t0 = t; }, stop(t) { o.t1 = t; }}; mk._o = o; return o; },
      createGain() { const g = {gain: {setValueAtTime(v, t) { (g.ev = g.ev || []).push([t, v]); }, linearRampToValueAtTime(v, t) { (g.ev = g.ev || []).push([t, v]); }}, connect() { const o = mk._o; beeps.push({o, g}); }}; return g; }};
    const els = {txIn: {value: a3}, txGo: {textContent: "", disabled: false}};
    Object.assign(ctxObj, {ctx: mk, $: id => els[id] || {}, ensureCtx: async () => {}});
    if (a2 && cfg.mode === "prot") { const p = await D.txPlan(a3, a4 || undefined); await D.sendPlanned(p); }   // V2: like transmitUI
    else await D.transmit();
    const out = beeps.map(({o, g}) => { const ev = g.ev; const t0 = ev[0][0], t1 = ev[ev.length - 1][0]; return [t0, o.frequency.value, t1 - t0, cfg.vol]; });
    process.stdout.write(JSON.stringify(out)); return;
  }
  if (cmd === "beeps" || cmd === "wav") {
    const p = await D.txPlan(a3, a4 || undefined);
    const b = D.beepsOf(p.codes);
    if (cmd === "wav") { fs.writeFileSync(a5, Buffer.from(D.wavOf(b, 22050))); process.stdout.write(JSON.stringify(b.beeps.length)); return; }
    process.stdout.write(JSON.stringify(b.beeps)); return;
  }
  if (cmd === "decode") {
    const buf = fs.readFileSync(a3), sr = +a4;
    const x = new Float32Array(buf.buffer, buf.byteOffset, Math.floor(buf.length / 4));
    const got = [];
    for (const [t, m, isV2] of await D.decodeSamples(x, sr)) {
      if (m === "prot" && isV2 && t[0] === "□") { const r = await D.v2Open(t.slice(1), a2 || ""); got.push([r.err ? "!" + r.err : r.text, m]); }
      else got.push([t, m]);
    }
    process.stdout.write(JSON.stringify(got)); return;
  }
  throw new Error("unknown command " + cmd);
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(2); });
