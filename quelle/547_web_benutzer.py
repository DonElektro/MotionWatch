#@ MoveEye – Teil 547: Web-Karte «Benutzer» (Einstellungen → Sicherheit): Rollen Kind / Freund / Familie / Nur ansehen / Eigene Rechte, Zeitfenster, Ablaufdatum, Push pro Benutzer, «Handy verknüpfen» (QR) und Geräte pro Benutzer. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# Server: 040 (Rechte), 041 (Zeitfenster, Einmal-Link, Push, Geräte). Deutsch der Seite: Teil 623 (/*USRDE*/), fr / it / rm über /i18n/<lang>.js.
USERS_JS = r"""
<script>
Object.assign(I18N.de, /*USRDE*/{});
const USER_ROLES_UI = [["kid", "🧒", "Child"], ["friend", "🤝", "Friend"], ["family", "🏠", "Family"], ["view", "👁", "View only"], ["custom", "⚙", "Own rights"]];
const USER_PERMS_UI = [["live", "📺", "Live picture"], ["rec", "🎞", "Recordings"], ["arm", "🛡", "Protection on / off"], ["light", "💡", "Light"],
  ["siren", "🚨", "Siren"], ["games", "🎲", "Games / game corner"], ["talk", "🎙", "Talk"], ["head", "🕹", "Steer the head"], ["settings", "⚙", "Settings"]];
const USER_PUSH_UI = [["alarm", "🚨", "Alarms"], ["info", "ℹ️", "Infos"], ["games", "🎲", "Game invitations"]];
const USER_DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
function userRoleName(r) { const x = USER_ROLES_UI.find(z => z[0] === r); return x ? t(x[2]) : (r === "operate" ? t("Family") : r); }
async function usersLoad() {
  const box = $("#users-box"); if (!box) return;
  let j = {users: [], pw: false}; try { j = await (await fetch("/api/users", {cache: "no-store"})).json(); } catch (e) { return; }
  const open = new Set([...box.querySelectorAll("details.us-more[open]")].map(d => d.dataset.u));
  box.textContent = "";
  box.appendChild(el("div", "mut", t("Each person gets an own access: a role decides what they may do, a phone is linked with a QR code (no password needed). The web password stays the administrator. The log shows who switched what.")));
  box.appendChild(el("div", "mut", "🎟 " + t("For short visits the guest link is enough (Live → Guest access). For people who come again and again, better create a user here.")));
  if (!j.pw) { box.appendChild(el("div", "err", "⚠ " + t("set the web password first (it is the administrator)"))); return; }
  const err = el("div", "err");
  const go = async b => { b.lang = LANG; const r = await post("/api/users", b); err.textContent = r.ok ? "" : "⚠ " + (r.error || "error"); if (r.ok && !b.keep) usersLoad(); return r; };
  const roleSel = v => { const s = el("select"); USER_ROLES_UI.forEach(([k, ic, l]) => { const o = el("option", "", ic + " " + t(l)); o.value = k; s.appendChild(o); }); s.value = v; return s; };
  const chip = (txt, on) => { const c = el("span", "", txt); c.style.cssText = "display:inline-block;font-size:12px;padding:2px 8px;margin:3px 4px 0 0;border-radius:99px;border:1px solid var(--line);" + (on ? "" : "opacity:.45;text-decoration:line-through"); return c; };
  const d2 = n => { if (!n) return "–"; const d = new Date(n * 1000); return d.toLocaleDateString() + " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2); };
  (j.users || []).forEach(u => {
    const row = el("div", "sens-card us-card"), r1 = el("div", "row"); row.dataset.u = u.name;
    const del = el("button", "sec", "✕"), pwb = el("button", "sec", "🔑"); del.type = pwb.type = "button";
    pwb.title = t("New password"); del.title = t("Remove");
    del.onclick = () => { if (confirm(t("Remove this user?") + "\n" + u.name)) go({action: "remove", name: u.name}); };
    pwb.onclick = () => { const p = prompt(t("New password for") + " " + u.name + " (6–64)"); if (p) go({action: "password", name: u.name, password: p}).then(r => { if (r.ok) toast("✓ " + t("Saved")); }); };
    const nm = el("b", "", "👤 " + u.name); nm.style.flex = "1";
    const st = el("span", "mut", u.active ? "✓ " + t("active") : "🌙 " + t("not active right now")); st.style.fontSize = "12px";
    r1.append(nm, st, pwb, del); row.appendChild(r1);
    const rs = roleSel(u.role); rs.style.cssText = "width:100%;margin-top:6px"; rs.onchange = () => go({action: "update", name: u.name, role: rs.value}); row.appendChild(rs);
    const perms = el("div", "us-perms");
    if (u.role === "custom") {
      USER_PERMS_UI.forEach(([k, ic, l]) => { const lb = el("label", ""), cb = el("input"); cb.type = "checkbox"; cb.checked = u.perms.includes(k); cb.dataset.p = k;
        lb.style.cssText = "display:inline-flex;gap:4px;align-items:center;margin:4px 10px 0 0;font-size:13px"; lb.append(cb, document.createTextNode(ic + " " + t(l)));
        cb.onchange = () => go({action: "update", name: u.name, keep: true, perms: [...perms.querySelectorAll("input:checked")].map(x => x.dataset.p)}); perms.appendChild(lb); });
    } else USER_PERMS_UI.forEach(([k, ic, l]) => perms.appendChild(chip(ic + " " + t(l), u.perms.includes(k))));
    row.appendChild(perms);
    // access time, expiry, messages
    const more = el("details", "us-more"); more.dataset.u = u.name; more.open = open.has(u.name); more.style.marginTop = "8px";
    const sm = el("summary", "", "⏰ " + t("Access time and messages")); sm.style.cssText = "cursor:pointer;font-size:13px"; more.appendChild(sm);
    const w = u.win || null, wl = el("label", ""), wc = el("input"); wc.type = "checkbox"; wc.checked = !!w; wl.style.cssText = "display:flex;gap:6px;align-items:center;margin-top:6px";
    wl.append(wc, document.createTextNode(t("Only at certain times")));
    const wr = el("div", "row"); wr.style.cssText = "gap:6px;margin-top:4px;flex-wrap:wrap"; const f = el("input"), to = el("input"); f.type = to.type = "time";
    f.value = w ? w.from : "08:00"; to.value = w ? w.to : "20:00"; f.style.width = to.style.width = "110px"; wr.append(f, el("span", "", "–"), to);
    const dy = el("div", ""); const days = new Set(w ? w.days : [0, 1, 2, 3, 4, 5, 6]);
    USER_DAYS.forEach((d, i) => { const lb = el("label", ""), cb = el("input"); cb.type = "checkbox"; cb.checked = days.has(i); cb.dataset.d = i;
      lb.style.cssText = "display:inline-flex;gap:3px;align-items:center;margin:4px 8px 0 0;font-size:13px"; lb.append(cb, document.createTextNode(t(d))); dy.appendChild(lb); });
    const wbox = el("div", ""); wbox.append(wr, dy); wbox.hidden = !wc.checked; wc.onchange = () => { wbox.hidden = !wc.checked; };
    const ur = el("div", "row"); ur.style.cssText = "gap:6px;margin-top:8px;align-items:center;flex-wrap:wrap"; const un = el("input"); un.type = "date"; un.value = u.until || "";
    const uc = el("button", "sec", "✕"); uc.type = "button"; uc.title = t("no end"); uc.onclick = () => { un.value = ""; };
    ur.append(el("span", "", t("Valid until") + ":"), un, uc);
    const pb = el("div", ""); pb.style.marginTop = "8px"; pb.appendChild(el("div", "mut", t("Push messages for this person:")));
    USER_PUSH_UI.forEach(([k, ic, l]) => { const lb = el("label", ""), cb = el("input"); cb.type = "checkbox"; cb.checked = (u.push || []).includes(k); cb.dataset.k = k;
      lb.style.cssText = "display:inline-flex;gap:4px;align-items:center;margin:4px 10px 0 0;font-size:13px"; lb.append(cb, document.createTextNode(ic + " " + t(l))); pb.appendChild(lb); });
    pb.appendChild(el("div", "mut", "🌐 " + t("Browser push") + ": " + (u.webpush ? u.webpush + " " + t("device(s)") : t("none yet - the person switches it on in their own browser (Settings → Notifications)"))));
    const nt = el("input"); nt.type = "text"; nt.maxLength = 120; nt.placeholder = t("own ntfy topic (optional)") + (u.ntfy ? " · " + t("now") + " " + u.ntfy : ""); nt.style.cssText = "width:100%;margin-top:6px"; nt.autocomplete = "off";
    pb.appendChild(nt);
    const sv = el("button", "", "✓ " + t("Save")); sv.type = "button"; sv.style.marginTop = "8px";
    sv.onclick = () => { const b = {action: "update", name: u.name, until: un.value || "", push: [...pb.querySelectorAll("input[data-k]:checked")].map(x => x.dataset.k),
      win: wc.checked ? {from: f.value || "00:00", to: to.value || "00:00", days: [...dy.querySelectorAll("input:checked")].map(x => +x.dataset.d)} : null};
      if (nt.value.trim()) b.ntfy = nt.value.trim();
      go(b).then(r => { if (r.ok) toast("✓ " + t("Saved")); }); };
    const ntc = el("button", "sec", t("Remove own ntfy topic")); ntc.type = "button"; ntc.style.margin = "8px 0 0 6px"; ntc.hidden = !u.ntfy;
    ntc.onclick = () => go({action: "update", name: u.name, ntfy: ""});
    more.append(wl, wbox, ur, pb, sv, ntc); row.appendChild(more);
    // phones
    const lk = el("button", "sec", "📱 " + t("Link a phone")); lk.type = "button"; lk.style.marginTop = "8px"; lk.className = "sec us-link";
    lk.onclick = async () => { const r = await go({action: "link", name: u.name, keep: true}); if (!r.ok) return;
      const note = t("Scan with the camera of the phone of") + " " + u.name + ". " + t("Valid 10 minutes, only once. The phone is then logged in without a password.") + (r.secure ? "" : " ⚠ " + t("Without the secure page (https) the link goes unencrypted through the Wi-Fi."));
      if (window.qrShow) { const ov = qrShow(r.url, "📱 " + t("Link a phone") + " – " + u.name, {secret: true, note: note});
        const tick = setInterval(() => { if (!document.body.contains(ov)) { clearInterval(tick); usersLoad(); } }, 1500); }
      else prompt(note, r.url); };
    row.appendChild(lk);
    if (u.nopw) row.appendChild(el("div", "mut", "🔑 " + t("No own password - logs in only with a linked phone.")));
    (u.devices || []).forEach(x => { const r = el("div", "row"); r.style.marginTop = "6px";
      const tx = el("div", ""); tx.style.flex = "1"; tx.append(el("div", "", "📱 " + x.name + (x.me ? " (" + t("this device") + ")" : "") + (x.via === "link" ? " · QR" : "")),
        el("div", "mut", t("since") + " " + d2(x.t0) + " · " + t("last") + " " + d2(x.seen) + (x.ip ? " · " + x.ip : "")));
      const b = el("button", "sec", "✕"); b.type = "button"; b.title = t("Remove"); b.className = "sec us-dev-del";
      b.onclick = () => { if (confirm(t("Remove this device? It is logged out at once.") + "\n" + x.name)) go({action: "device_remove", name: u.name, id: x.id}); };
      r.append(tx, b); row.appendChild(r); });
    box.appendChild(row);
  });
  const add = el("div", "sens-card"), nm = el("input"), pw = el("input"), rs = roleSel("family"), ab = el("button", "", "+ " + t("Add user"));
  nm.type = "text"; nm.maxLength = 24; nm.placeholder = t("Name"); nm.id = "us-name"; pw.type = "password"; pw.maxLength = 64; pw.placeholder = t("Password (optional, 6–64)"); pw.autocomplete = "new-password"; pw.id = "us-pw";
  rs.id = "us-role"; ab.id = "us-add";
  [nm, pw, rs].forEach(x => { x.style.cssText = "width:100%;margin-top:6px"; }); ab.type = "button"; ab.style.marginTop = "8px";
  ab.onclick = () => go({action: "add", name: nm.value, password: pw.value, role: rs.value});
  add.append(el("b", "", "+ " + t("New user")), nm, pw, rs, el("div", "mut", t("Without a password the person logs in only with a linked phone (QR code).")), ab);
  box.append(add, err);
  if (typeof trustLoad === "function") trustLoad(box);
}
</script>
"""
WEB_PAGE = WEB_PAGE.replace("</body>", USERS_JS + "</body>", 1)
