#@ MoveEye – Teil 197: KI-Daten aufräumen – Trainingspaket mit «Vielfalt», Liste der Pakete, alte Pakete löschen (Web und Fenster). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch Daniel (29.10.2026, «KI-Daten aufräumen»):
#   * «Trainingspaket für ein eigenes KI-Modell (YOLO)» (Reiter Simulator und Fenster) hat dieselbe Wahl wie der Simulator:
#     «Vielfalt: normal / hoch» (dataset.gd / kitrain.gd, Name «vielfalt» wie dort).
#   * Die Pakete (Ordner user://trainingsbilder/<Zeit> + ZIP «MoveEye-Trainingsbilder_….zip», bis 3D-4.21 «MW-…», auf dem Schreibtisch) liegen auf dem
#     Rechner des Simulators (PC oder Pi). Der Simulator räumt nach jedem neuen Paket selbst auf (kidaten.gd): die neuesten 3
#     bleiben, nichts älter als 30 Tage; das neueste Paket bleibt immer. Der Knopf «Alte KI-Daten löschen» löscht alle
#     ausser dem neuesten. Das KI-Modell (models/moveeye_model.*, frozen_inference_graph.pb) wird nie angefasst.
# ----------------------------------------------------------------------------
KIDATA_VF = ("normal", "hoch")
KIDATA_SIZES = (200, 500, 1000, 2000)


def kidata_export(n, vielfalt=None):
    """a training pack in the simulator; vielfalt "normal" / "hoch" (else the choice of the simulator)"""
    try:
        n = int(n or 500)
    except (TypeError, ValueError):
        n = 500
    q = {"action": "dataset", "op": "export", "n": max(10, min(5000, n))}
    if str(vielfalt or "") in KIDATA_VF:
        q["vielfalt"] = str(vielfalt)
    return sim_control(q)


def kidata_packs(clean=False, lang=None):
    """the packs on the PC of the simulator; clean=True: delete all except the newest. ValueError for an old simulator."""
    r = sim_control({"action": "dataset", "op": "clean" if clean else "packs"})
    if not isinstance(r, dict) or "packs" not in r:
        raise ValueError("not supported - update the simulator")
    if not r.get("ok", True):
        raise ValueError(str(r.get("error") or "busy"))
    if clean:
        log_event("ai", f"Old AI data deleted: {int(r.get('deleted') or 0)} packs, {float(r.get('freed_mb') or 0):.0f} MB")
    r["text"] = kidata_text(r, lang)
    return r


def kidata_text(r, lang=None):
    ps = r.get("packs") or []
    t = (f"📦 {len(ps)} " + tr("training packs", lang) + f" · {float(r.get('total_mb') or 0):.0f} MB") if ps else "📦 " + tr("no training packs", lang)
    if r.get("deleted"):
        t += " · 🧹 " + trf("{n} deleted ({mb} MB)", lang, n=int(r["deleted"]), mb=f"{float(r.get('freed_mb') or 0):.0f}")
    return t


def kidata_tk_build(app, parent):
    """the window (section Simulator): size, «Vielfalt», «Trainingspaket», «Alte KI-Daten löschen» + one status line"""
    ttk.Label(parent, text="📦 " + tr("Training set for an own AI model (YOLO)"), style="Mut.TLabel").pack(anchor="w", pady=(8, 0))
    fr = ttk.Frame(parent); fr.pack(fill="x", pady=(2, 0))
    n_var = tk.StringVar(value="500")
    ttk.Combobox(fr, textvariable=n_var, values=[str(x) for x in KIDATA_SIZES], width=6, state="readonly").pack(side="left", padx=(0, 4))
    vf_names = {"hoch": tr("Variety: high (recommended)"), "normal": tr("Variety: normal")}
    vf_var = tk.StringVar(value=vf_names["hoch"])
    ttk.Combobox(fr, textvariable=vf_var, values=[vf_names["hoch"], vf_names["normal"]], state="readonly", width=24).pack(side="left", fill="x", expand=True)
    lbl = ttk.Label(parent, text="", style="Mut.TLabel", wraplength=330, justify="left")

    def run(fn):
        def work():
            try:
                txt = fn()
            except ValueError as e:
                txt = "⚠ " + tr_err(str(e))
            except Exception:
                txt = "⚠ " + tr_err("simulator not reachable")
            try:
                app.root.after(0, lambda: lbl.config(text=txt))
            except Exception:
                pass
        threading.Thread(target=work, daemon=True, name="kidata").start()

    def export():
        vf = "normal" if vf_var.get() == vf_names["normal"] else "hoch"
        r = kidata_export(n_var.get(), vf)
        return tr("The simulator makes the pictures and saves a ZIP on the desktop of its PC (about 2 s per picture).") + " " + str((r or {}).get("msg") or "")

    def clean():
        if not messagebox.askyesno("MoveEye", tr("Delete all training packs on the PC of the simulator except the newest one? The AI model stays.")):
            return
        run(lambda: kidata_packs(True)["text"])
    bf = ttk.Frame(parent); bf.pack(fill="x", pady=(4, 0))
    ttk.Button(bf, text="📦 " + tr("Make the training pack"), command=lambda: run(export)).pack(side="left", expand=True, fill="x", padx=(0, 4))
    ttk.Button(bf, text="🧹 " + tr("Delete old AI data"), command=clean).pack(side="left", expand=True, fill="x")
    lbl.pack(anchor="w", pady=(4, 0))
    ttk.Label(parent, text=tr("Cleaned up by itself: after every new pack the newest 3 stay, nothing older than 30 days (the newest always stays). The AI model is never deleted."), style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w")
    run(lambda: kidata_packs(False)["text"])
