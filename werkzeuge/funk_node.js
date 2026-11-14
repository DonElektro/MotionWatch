// Hilfe für werkzeuge/funk_test.py: führt den Code der Seite «Morse-Funk» des Besitzers in node aus - unverändert aus der Seite
// geschnitten (Decoder zwischen /*DECODER-START*/ und /*DECODER-END*/, die Funktionen prepTx und transmit), die Prüfsummen
// prüft funk_test.py. Kein Browser nötig: AudioContext und die Knöpfe sind nachgebaut, transmit schreibt jeden Ton als Liste.
//   node funk_node.js SEITE keystream SCHLUESSEL N            -> JSON: die ersten N Werte des Schlüsselstroms
//   node funk_node.js SEITE transmit  CFG_JSON SCHLUESSEL TEXT -> JSON: [[start s, Frequenz Hz, Länge s, Lautstärke], ...]
//   node funk_node.js SEITE decode    CFG_JSON SCHLUESSEL RAW SR -> JSON: [[Text, Modus], ...] (RAW = float32, Rate SR, Blöcke 512)
"use strict";
const fs = require("fs"), vm = require("vm");
const [, , page, cmd, a1, a2, a3, a4] = process.argv;
const src = fs.readFileSync(page, "utf8");
const cut = (a, b) => { const i = src.indexOf(a), j = src.indexOf(b, i); if (i < 0 || j < 0) throw new Error("not found: " + a); return src.slice(i, j); };
const fn = head => { const i = src.indexOf(head), j = src.indexOf("\n}\n", i); if (i < 0 || j < 0) throw new Error("not found: " + head); return src.slice(i, j + 3); };
const decoder = cut("/*DECODER-START*/", "/*DECODER-END*/") + "/*DECODER-END*/";
const prepTx = fn("function prepTx(");                     // (each function up to its closing brace at the start of a line)
const transmit = fn("async function transmit(");
const ctxObj = {TextEncoder, crypto: globalThis.crypto, console, Math, Uint8Array, Float32Array, setTimeout: () => 0};
vm.createContext(ctxObj);
vm.runInContext(decoder + "\n;globalThis.__d={makeKeystream,makeDecoder,normText,ALPHA,PCODE,NA};", ctxObj);
(async () => {
  if (cmd === "keystream") {
    const ks = await ctxObj.__d.makeKeystream(a1, +a2);
    process.stdout.write(JSON.stringify(ks || [])); return;
  }
  const cfg = JSON.parse(a1);
  const ks = a2 ? await ctxObj.__d.makeKeystream(a2, 4096) : null;
  if (cmd === "transmit") {
    const beeps = [];
    // the AudioContext of the page, rebuilt: an oscillator + gain per beep; the gain ramps tell start and length
    const mk = {currentTime: 0, destination: {}, createOscillator() { const o = {frequency: {}, type: "", connect() {}, start(t) { o.t0 = t; }, stop(t) { o.t1 = t; }}; mk._o = o; return o; },
      createGain() { const g = {gain: {setValueAtTime(v, t) { (g.ev = g.ev || []).push([t, v]); }, linearRampToValueAtTime(v, t) { (g.ev = g.ev || []).push([t, v]); }}, connect() { const o = mk._o; beeps.push({o, g}); }}; return g; }};
    const els = {txIn: {value: a3}, txGo: {textContent: "", disabled: false}};
    vm.runInContext(prepTx + transmit + "\n;globalThis.__tx={prepTx,transmit};", Object.assign(ctxObj, {
      cfg, ks, ctx: mk, sendNodes: [], sendingUntil: 0, $: id => els[id] || {}, ensureCtx: async () => {}, key: a2 || "", setTimeout: () => 0}));
    await ctxObj.__tx.transmit();
    const out = beeps.map(({o, g}) => { const ev = g.ev; const t0 = ev[0][0], t1 = ev[ev.length - 1][0]; return [t0, o.frequency.value, t1 - t0, cfg.vol]; });
    process.stdout.write(JSON.stringify(out)); return;
  }
  if (cmd === "decode") {
    const buf = fs.readFileSync(a3), sr = +a4;
    const x = new Float32Array(buf.buffer, buf.byteOffset, Math.floor(buf.length / 4));
    const got = [];
    const dec = ctxObj.__d.makeDecoder({sr, N: 512, getCfg: () => cfg, onUpdate: () => {}, onMessage: (t, m) => got.push([t, m])});
    dec.ks = ks;
    for (let i = 0; i + 512 <= x.length; i += 512) dec.frame(x.subarray(i, i + 512), false);
    process.stdout.write(JSON.stringify(got)); return;
  }
  throw new Error("unknown command " + cmd);
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(2); });
