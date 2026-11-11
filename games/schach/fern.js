/* Schach für MoveEye – Teil «Fern»: zwei Handys spielen eine Partie über MoveEye (der Pi vermittelt nur).
   Lizenz: GPL-3.0-or-later (siehe LIESMICH.txt).

   Der Pi (MoveEye, Teil 639zzr) hält je Spiel nur Startstellung + Zugliste und prüft jeden Zug (wer dran ist, ob er erlaubt
   ist). Diese Datei ist nur die Leitung dorthin:
     - Adresse: gleicher Ursprung wie die Spielseite. Aus «…/g/schach/» bzw. «…/games/schach/» wird «…/schachfern/»
       (Spiele-Port, Hauptadresse mit Anmeldung, Gäste-Link /p/<schlüssel>/, /spiele).
     - Neues Spiel -> kurzer Code + geheimer Sitz-Schlüssel (Token). Der Token bleibt in localStorage («moveeye-schach-fern»)
       und geht nie in einen Link oder QR-Code; der QR-Code enthält nur die Adresse der Seite + den Code.
     - Verbindung: «Long Polling» – eine Anfrage wartet auf dem Pi bis zu 15 s auf eine Änderung, danach sofort die nächste.
       Antwortet der Pi gleich (kein Warten möglich), wird daraus ein kurzes Abfragen alle 1,2 s. Nach einem Fehler neu nach
       1–2 s; wird die Seite wieder sichtbar (Handy wach), sofort. Kein WebSocket, kein Dienst im Internet. */
(function (global) {
  "use strict";
  var K = "moveeye-schach-fern";

  function basis() {
    var m = location.pathname.match(/^(.*?)\/(?:g|games)\/schach\//);
    return m ? m[1] + "/schachfern" : null;
  }
  function seite() { return location.origin + location.pathname.replace(/index\.html$/, ""); }

  function lies() { try { var t = localStorage.getItem(K); var o = t ? JSON.parse(t) : null; return o && typeof o.code === "string" ? o : null; } catch (e) { return null; } }
  function schreib(o) { try { localStorage.setItem(K, JSON.stringify(o)); return true; } catch (e) { return false; } }
  function weg() { try { localStorage.removeItem(K); } catch (e) {} }

  /** eine Anfrage an den Pi: Promise {st, j} (st 0 = keine Verbindung) */
  function frage(methode, op, daten, ms, signal) {
    var b = basis();
    if (!b) return Promise.resolve({ st: 0, j: { ok: false, fehler: "kein_pi" } });
    var ctrl = signal ? null : (global.AbortController ? new AbortController() : null), t = null;
    var o = { method: methode, cache: "no-store", credentials: "same-origin", signal: signal || (ctrl && ctrl.signal) };
    var url = b + "/" + op;
    if (methode === "POST") { o.headers = { "Content-Type": "application/json" }; o.body = JSON.stringify(daten || {}); }
    else if (daten) url += "?" + Object.keys(daten).map(function (k) { return k + "=" + encodeURIComponent(daten[k]); }).join("&");
    if (ctrl) t = setTimeout(function () { ctrl.abort(); }, ms || 12000);
    return fetch(url, o).then(function (r) {
      return r.json().then(function (j) { return { st: r.status, j: j || {} }; }, function () { return { st: r.status, j: { ok: false, fehler: "antwort" } }; });
    }, function () { return { st: 0, j: { ok: false, fehler: "netz" } }; }).then(function (x) { if (t) clearTimeout(t); return x; });
  }

  /** dauernde Verbindung für eine Sitzung {code, token}: ruft cb.zustand(v), cb.status("ok"|"weg"), cb.fehler(x) */
  function Verbindung(s, cb) {
    this.s = s; this.cb = cb; this.seq = -1; this.lauf = 0; this.fehler = 0; this.ctrl = null; this.timer = null;
    var self = this;
    this._wach = function () { if (!document.hidden) self.jetzt(); };
    document.addEventListener("visibilitychange", this._wach);
    global.addEventListener("pageshow", this._wach);
    global.addEventListener("online", this._wach);
    global.addEventListener("focus", this._wach);
  }
  Verbindung.prototype.start = function () { this.lauf++; this._runde(this.lauf, true); };
  Verbindung.prototype.stopp = function () {
    this.lauf++; if (this.ctrl) try { this.ctrl.abort(); } catch (e) {} clearTimeout(this.timer);
    document.removeEventListener("visibilitychange", this._wach); global.removeEventListener("pageshow", this._wach);
    global.removeEventListener("online", this._wach); global.removeEventListener("focus", this._wach);
  };
  Verbindung.prototype.jetzt = function () {                      // sofort neu fragen (Handy wieder wach, Seite sichtbar)
    var nr = ++this.lauf; if (this.ctrl) try { this.ctrl.abort(); } catch (e) {} clearTimeout(this.timer);
    this._runde(nr, true);
  };
  Verbindung.prototype._runde = function (nr, sofort) {
    var self = this;
    if (nr !== this.lauf) return;
    var t0 = Date.now(), alt = this.seq;
    this.ctrl = global.AbortController ? new AbortController() : null;
    var c = this.ctrl, wd = setTimeout(function () { if (c) c.abort(); }, 25000);
    var q = { code: this.s.code, seq: sofort ? -1 : this.seq, warte: sofort ? 0 : 1 };
    if (this.s.token) q.token = this.s.token;
    frage("GET", "zustand", q, 0, c ? c.signal : undefined).then(function (x) {
      clearTimeout(wd);
      if (nr !== self.lauf) return;
      if (x.st === 200 && x.j.ok) {
        self.fehler = 0; self.seq = x.j.seq;
        self.cb.status("ok"); self.cb.zustand(x.j);
        var schnell = !sofort && Date.now() - t0 < 400 && x.j.seq === alt;        // der Pi hat nicht gewartet: kurz abfragen
        self.timer = setTimeout(function () { self._runde(nr, false); }, schnell ? 1200 : 0);
      } else if (x.st === 404 || x.st === 403) {
        self.cb.fehler(x);                                     // Spiel weg / Schlüssel falsch / Spielecke zu: nicht endlos fragen
      } else {
        self.fehler++; self.cb.status("weg");
        self.timer = setTimeout(function () { self._runde(nr, true); }, self.fehler < 3 ? 1000 : 2000);
      }
    });
  };

  global.Fern = {
    basis: basis, seite: seite, sitzung: { lies: lies, schreib: schreib, weg: weg },
    info: function () { return frage("GET", "info", null, 6000); },
    neu: function (farbe) { return frage("POST", "neu", { farbe: farbe }); },
    beitreten: function (code, token) { return frage("POST", "beitreten", token ? { code: code, token: token } : { code: code }); },
    zustand: function (s) { return frage("GET", "zustand", s.token ? { code: s.code, token: s.token } : { code: s.code }); },
    zug: function (s, uci, n) { return frage("POST", "zug", { code: s.code, token: s.token, uci: uci, n: n }); },
    aktion: function (s, art, mehr) { var d = { code: s.code, token: s.token, art: art }; for (var k in (mehr || {})) d[k] = mehr[k]; return frage("POST", "aktion", d); },
    qr: function (code) { return basis() + "/qr?code=" + encodeURIComponent(code) + "&u=" + encodeURIComponent(seite()); },
    link: function (code) { return seite() + "?fern=" + code; },
    Verbindung: Verbindung,
    ABC: "ACDEFHJKMNPQRTUVWXY3479"
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
