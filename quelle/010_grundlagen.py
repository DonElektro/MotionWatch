#@ Motion Watch – Teil 010: Importe, Version (APP_VERSION), Ordner für Einstellungen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
import argparse, atexit, random, functools, glob, hashlib, hmac, ipaddress, json, secrets, math, os, queue, re, shutil, signal, subprocess, sys, tempfile, threading, time, urllib.request, uuid, zipfile
from collections import deque
from datetime import datetime, timedelta

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "2.98.74"


def default_data_dir():
    """Settings, log and certificate live in ONE fixed folder, independent of where the script is saved:
    ~/.config/motionwatch  (with sudo: the folder of the user who called sudo). MOTIONWATCH_HOME or --config override it.
    So a new version, saved anywhere, keeps all settings."""
    env = os.environ.get("MOTIONWATCH_HOME", "").strip()
    if env:
        return os.path.abspath(os.path.expanduser(env))
    home = os.path.expanduser("~")
    if os.environ.get("SUDO_USER") and hasattr(os, "geteuid") and os.geteuid() == 0:
        try:
            import pwd
            home = pwd.getpwnam(os.environ["SUDO_USER"]).pw_dir
        except (ImportError, KeyError):
            pass
        return os.path.join(home, ".config", "motionwatch")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config"), "motionwatch")


DATA_DIR = default_data_dir()
SETTINGS_NAME = "motionwatch_settings.json"
SETTINGS_FILE = os.path.join(DATA_DIR, SETTINGS_NAME)
LOG_FILE = os.path.join(DATA_DIR, "motionwatch.log")


def set_data_dir(path):
    """Use this folder for settings / log / certificate (creates it). Falls back to the script folder if it cannot be written."""
    global DATA_DIR, SETTINGS_FILE, LOG_FILE
    path = os.path.abspath(os.path.expanduser(path))
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
    except OSError as e:
        print(f"Settings folder {path} is not writable ({e}) - using the script folder instead")
        path = HERE
    DATA_DIR = path
    SETTINGS_FILE = os.path.join(path, SETTINGS_NAME)
    LOG_FILE = os.path.join(path, "motionwatch.log")
    _LOGDAY["d"] = ""                                    # check the (new) log file for an old day at the next line
    return path


def _settings_saved_time(p):
    try:
        with open(p) as f:
            d = json.load(f)
        if not isinstance(d, dict) or not isinstance(d.get("cfg"), dict):
            return None
        return d.get("saved") or datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds")
    except (OSError, ValueError):
        return None


def find_old_settings():
    """Settings files of older versions (next to their script). Looks in the script folder, the current folder, the home
    folder and two levels below it (e.g. ~/Downloads/v1.4/), and in the folders next to the script folder. Newest first."""
    home = os.path.expanduser("~")
    if os.environ.get("SUDO_USER"):
        try:
            import pwd
            home = pwd.getpwnam(os.environ["SUDO_USER"]).pw_dir
        except (ImportError, KeyError):
            pass
    pats = [os.path.join(HERE, SETTINGS_NAME), os.path.join(os.getcwd(), SETTINGS_NAME), os.path.join(home, SETTINGS_NAME),
            os.path.join(home, "*", SETTINGS_NAME), os.path.join(home, "*", "*", SETTINGS_NAME),
            os.path.join(os.path.dirname(HERE), "*", SETTINGS_NAME), "/home/*/" + SETTINGS_NAME, "/home/*/*/" + SETTINGS_NAME]
    found = {}
    for pat in pats:
        for p in glob.glob(pat)[:200]:
            p = os.path.abspath(p)
            if p == os.path.abspath(SETTINGS_FILE) or p in found:
                continue
            t = _settings_saved_time(p)
            if t:
                found[p] = t
    return sorted(found, key=lambda p: found[p], reverse=True)


def prepare_settings_file():
    """Called once at start: take over the settings of an older version (first start of 1.5.3 or newer), keep a backup copy
    of the last good settings, move the HTTPS certificate along. Returns a short message for the log."""
    msg = ""
    if not os.path.isfile(SETTINGS_FILE):
        old = find_old_settings()
        if old:
            try:
                shutil.copy2(old[0], SETTINGS_FILE)
                os.chmod(SETTINGS_FILE, 0o600)
                msg = f"Settings taken over from the older version: {old[0]}"
            except OSError as e:
                msg = f"Could not take over old settings from {old[0]}: {e}"
    if os.path.isfile(SETTINGS_FILE) and _settings_saved_time(SETTINGS_FILE):
        try:                                             # backup of the last good file (before this version changes it)
            shutil.copy2(SETTINGS_FILE, os.path.join(DATA_DIR, "motionwatch_settings.backup.json"))
        except OSError:
            pass
    for name in ("motionwatch_cert.pem", "motionwatch_key.pem"):
        src, dst = os.path.join(HERE, name), os.path.join(DATA_DIR, name)
        if os.path.isfile(src) and not os.path.isfile(dst) and DATA_DIR != HERE:
            try:
                shutil.copy2(src, dst)
            except OSError:
                pass
    return msg

