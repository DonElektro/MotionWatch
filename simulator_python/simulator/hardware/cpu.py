"""How busy the computer is, for the UDP announcement (Motion Watch shows it in its list of simulators):
pc_cpu = the whole computer, sim_cpu = this simulator's share of the whole computer, both in % (0 .. 100).
Uses psutil when it is installed, otherwise /proc/stat (Raspberry Pi, Linux) or GetSystemTimes (Windows).
A value that cannot be measured is None and is left out."""
import os
import sys
import time

try:
    import psutil
except ImportError:
    psutil = None


def _idle_total():
    """(idle, total) CPU time of the whole computer so far, or None."""
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/stat") as f:
                v = [float(x) for x in f.readline().split()[1:]]
            return v[3] + (v[4] if len(v) > 4 else 0.0), sum(v[:8])
        except (OSError, ValueError, IndexError):
            return None
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        idle, kern, user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)):
            return None
        val = lambda ft: (ft.dwHighDateTime << 32) | ft.dwLowDateTime
        return float(val(idle)), float(val(kern) + val(user))     # kernel time already contains the idle time
    return None


class CpuMeter:
    def __init__(self):
        self.cores = os.cpu_count() or 1
        self._proc = (time.time(), time.process_time())
        self._sys = None if psutil else _idle_total()
        if psutil:
            psutil.cpu_percent(None)

    def read(self):
        """(pc_cpu, sim_cpu) since the last call, rounded to 0.1 %; None where unknown."""
        now, pt = time.time(), time.process_time()
        t0, p0 = self._proc
        self._proc = (now, pt)
        sim = None
        if now - t0 > 0.2:
            sim = round(max(0.0, min(100.0, (pt - p0) / (now - t0) / self.cores * 100.0)), 1)
        pc = None
        if psutil:
            pc = round(float(psutil.cpu_percent(None)), 1)
        else:
            cur, old = _idle_total(), self._sys
            self._sys = cur
            if cur and old and cur[1] > old[1]:
                pc = round(max(0.0, min(100.0, 100.0 * (1.0 - (cur[0] - old[0]) / (cur[1] - old[1])))), 1)
        return pc, sim
