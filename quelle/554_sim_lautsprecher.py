#@ MoveEye – Teil 554: Lautsprecher im Simulator – Sirene, Wecker-Melodie und Stimme gehen auch im Test-Postfach-Betrieb an den 3D-Simulator (der echte Lautsprecher bleibt still), eigene Töne zählen nicht für Lärm-Alarm und Klatschschalter. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Daniel (30.10.2026, «Sirene im Test-Postfach»): siren_quiet() (250) held the siren back whenever the test inbox
#   takes the messages (simulation with the switch, game round, drill, demo) - so the simulator never got «sound» and its
#   visitors never fled from the siren (help 540 promises «Licht und Sirene im Simulator»). And without a loudspeaker on the
#   PC (out_selected() False) nothing played at all. Now:
#   * the simulator is the loudspeaker («simulated loudspeaker»): sim_speaker() = simulation on and connected. siren_alarm
#     (250), the escalation (135) and every sound_play() go on; sound_play() plays only virtually (sim_sound_play) when the
#     test inbox is active (the REAL loudspeaker stays silent there - also when one is connected) or when there is no real
#     one. Exception: reason «test» (somebody pressed «Test» by hand) with a real loudspeaker plays for real.
#   * SOUND["kind"] = what plays (siren / two-tone / chime / tts …) -> sim_state «sound» (290) + «sound_vol» (here). The
#     simulator (simint.gd) plays simple tones on the PC (own volume, mute) and adds the sound to its microphone level and
#     - for beeps / bangs - to its short sounds (claps).
#   * «ignore the own siren»: the noise alarm already ignored the microphone while SOUND["playing"] and 2 s after it
#     (AudioMonitor.mute_until, 250 - also with the virtual loudspeaker, same variables). New: the claps / sneezes of the
#     simulator (sim_sound_events, 250) are ignored too while MoveEye plays a sound itself and 2 s after it (like the real
#     microphone path SoundEvents.feed), counted in SOUNDEV["own_ignored"].
# Translations: part 557 (with the other new texts of this round).
# ----------------------------------------------------------------------------
SOUND.setdefault("kind", "")
SOUND.setdefault("virt", False)
SOUNDEV_OWN = {"n": 0, "t": 0.0}


def sim_speaker():
    """the 3D simulator is connected: it is the loudspeaker of MoveEye (the simulated device has one)"""
    return bool(CFG.get("sim_on")) and bool(SIM.get("ok")) and time.time() - float(SIM.get("t") or 0.0) < 5.0


def speaker_ok():
    """a loudspeaker to play on: a real one or the simulator"""
    return out_selected() or sim_speaker()


def sim_speaker_only(reason="test"):
    """play only in the simulator (not on the real loudspeaker)?"""
    if not sim_speaker():
        return False
    if not out_selected():
        return True
    return siren_quiet() and reason != "test"


def own_sound_now(now=None):
    """MoveEye plays a sound itself right now or played one in the last 2 s (echo of the room)"""
    now = time.time() if now is None else now
    return bool(SOUND.get("playing")) or (AUDIO is not None and now < float(getattr(AUDIO, "mute_until", 0.0)))


def sim_sound_play(kind, seconds, volume, reason="test"):
    """the virtual loudspeaker: the same state as a real one (SOUND playing, kind, the microphone muted), nothing reaches
    the sound card. The simulator hears it through sim_state «sound» (290) and plays it on the PC."""
    kind = kind or CFG["siren_sound"] or "siren"
    if kind not in SOUND_KINDS + ("marmot", "chime", "birds", "tts", "beep1", "beep2", "beep3", "beep4", "beeplow") and not kind.startswith("file:"):
        kind = "siren"
    seconds = max(0.5, min(120.0, float(seconds if seconds is not None else CFG["siren_seconds"])))
    vol = max(0.0, min(100.0, float(volume if volume is not None else CFG["siren_volume"])))
    sound_stop(); talk_stop()
    with _SOUND_LOCK:
        SOUND["gen"] += 1; gen = SOUND["gen"]
        SOUND.update(playing=True, msg="", kind=kind, virt=True, vol=vol)
    if AUDIO is not None:
        AUDIO.mute_until = time.time() + seconds + 2.0

    def work():
        time.sleep(seconds)
        with _SOUND_LOCK:
            if gen == SOUND["gen"]:
                SOUND.update(playing=False, proc=None, virt=False)
        if AUDIO is not None:
            AUDIO.mute_until = max(float(AUDIO.mute_until), time.time() + 2.0)
    threading.Thread(target=work, daemon=True, name="sound-sim").start()
    if reason != "test":
        log_event("sys", f"Loudspeaker (simulator only, test inbox): {kind} for {seconds:.0f} s ({reason})")
    return True, ""


_sim_state_290_554 = sim_state


def sim_state():                                          # + 554: what plays, how loud (the simulator plays it and hears it)
    d = _sim_state_290_554()
    try:
        if SOUND.get("playing"):
            d["sound"] = str(SOUND.get("kind") or CFG.get("siren_sound") or "siren")
            d["sound_vol"] = round(float(SOUND.get("vol", CFG.get("siren_volume", 80))), 1)
            d["sound_virtual"] = bool(SOUND.get("virt"))
    except (TypeError, ValueError):
        pass
    return d


def own_sound_ignored(kind):
    """a clap / sneeze of the simulator while MoveEye plays something itself: ignored (noted for the page and the test)"""
    SOUNDEV_OWN["n"] += 1; SOUNDEV_OWN["t"] = time.time()
    SOUNDEV.update(last_act=tr("own sound ignored"), last_act_t=time.time())


_soundev_state_250 = soundev_state


def soundev_state():                                      # + 554: how often the own sound was ignored (page, tests)
    d = _soundev_state_250()
    d["own_ignored"] = SOUNDEV_OWN["n"]
    d["spk_sim"] = bool(sim_speaker()) and not out_selected()
    return d


def sim_sound_selftest():
    """virtual loudspeaker: plays only in the simulator in test-inbox mode, the state goes to the simulator, the own sound
    mutes the noise alarm and the claps of the simulator"""
    keep = {k: CFG.get(k) for k in ("sim_on", "audio_out", "notify_sandbox")}
    keep_sim = {k: SIM.get(k) for k in ("ok", "t")}
    G = globals(); keep_log = G["log_event"]
    try:
        G["log_event"] = lambda *a, **k: None
        CFG.update(sim_on=True, audio_out="", notify_sandbox=True); SIM.update(ok=True, t=time.time())
        assert sim_speaker() and speaker_ok() and sim_speaker_only("person alarm")
        ok, _ = sound_play("two-tone", 0.6, 50, reason="selftest")
        assert ok and SOUND["playing"] and SOUND["virt"] and SOUND["kind"] == "two-tone"
        d = sim_state()
        assert d["sound"] == "two-tone" and d["sound_virtual"] and abs(d["sound_vol"] - 50) < 0.1
        assert own_sound_now()
        if AUDIO is not None and AUDIO.proc is None:
            n0 = SOUNDEV_OWN["n"]; _SIM_SND["seen"] = 0
            sim_sound_events([{"id": 10 ** 9, "kind": "clap", "n": 3, "db": -5.0}], 10 ** 9)
            assert SOUNDEV_OWN["n"] == n0 + 1, "own sound not ignored"
        sound_stop()
        assert not SOUND["playing"]
        CFG.update(sim_on=False)
        assert not sim_speaker_only("person alarm")
    finally:
        sound_stop(); CFG.update(keep); SIM.update(keep_sim); G["log_event"] = keep_log
        _SIM_SND["seen"] = 0
    return True


SELFTEST_EXTRA.append(("Loudspeaker in the simulator: siren also in test-inbox mode, own sound ignored (554)", sim_sound_selftest))
