"""Builds MotionWatchSimulator.zip - everything somebody else needs, nothing personal.

Included: START SIMULATOR.bat, INSTALL.bat, requirements.txt, README.md, motion_sim.py, simulator/, my_maps/.
Left out: data/ (start window choices, old recordings / settings), old sim_data/, caches. Motion Watch itself is not part of it.

Next to it: MotionWatchSimulator.json with version, size and checksum - what Motion Watch needs to offer the zip for
download (EIGENEN_SIMULATOR_ANBINDEN.md, section 6).

    python make_package.py
"""
import hashlib
import json
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "MotionWatchSimulator.zip")
INFO = os.path.join(HERE, "MotionWatchSimulator.json")
FILES = ["START SIMULATOR.bat", "INSTALL.bat", "requirements.txt", "README.md", "motion_sim.py", "make_package.py",
         os.path.join("data", "README.txt")]
FOLDERS = ["simulator", "my_maps"]
SKIP_DIRS = {"__pycache__"}
SKIP_NAMES = {".guide_seen"}


def main():
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            p = os.path.join(HERE, f)
            if os.path.isfile(p):
                z.write(p, os.path.join("MotionWatchSimulator", f)); n += 1
        for d in FOLDERS:
            for root, dirs, files in os.walk(os.path.join(HERE, d)):
                dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
                for f in files:
                    if f in SKIP_NAMES or f.endswith(".pyc"):
                        continue
                    p = os.path.join(root, f)
                    z.write(p, os.path.join("MotionWatchSimulator", os.path.relpath(p, HERE))); n += 1
    print(f"{OUT}: {n} files, {os.path.getsize(OUT) / 1e6:.1f} MB")
    with open(os.path.join(HERE, "simulator", "__init__.py"), encoding="utf-8") as f:
        version = re.search(r'^VERSION = "([^"]+)"', f.read(), re.M).group(1)
    with open(OUT, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    with open(INFO, "w", encoding="utf-8") as f:
        json.dump({"version": version, "file": os.path.basename(OUT), "size": os.path.getsize(OUT), "sha256": sha}, f, indent=1)
    print(f"{INFO}: version {version}")


if __name__ == "__main__":
    main()
