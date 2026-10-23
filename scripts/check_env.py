"""Check this machine against configs/pins.json. Exit code 0 = ready, 1 = something must be fixed.

Run from the repo root:  conda run -n collusion-lab python scripts/check_env.py
"""
from __future__ import annotations

import ctypes
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT, load_pins  # noqa: E402
from core.llm import OllamaTransport, TransportError, gpu_name  # noqa: E402

WANT_PYTHON = "3.11.17"
WANT_ENV = "collusion-lab"


def free_ram_gb() -> str:
    try:
        if platform.system() == "Windows":
            class MEMSTAT(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            s = MEMSTAT()
            s.dwLength = ctypes.sizeof(MEMSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
            return f"{s.ullAvailPhys / 1e9:.1f} GB free of {s.ullTotalPhys / 1e9:.1f} GB"
        if platform.system() == "Linux":
            info = dict(re.findall(r"(\w+):\s+(\d+)", Path("/proc/meminfo").read_text()))
            return f"{int(info['MemAvailable']) / 1e6:.1f} GB free of {int(info['MemTotal']) / 1e6:.1f} GB"
        if platform.system() == "Darwin":
            vm = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
            page = int(re.search(r"page size of (\d+)", vm).group(1))
            pages = sum(int(re.search(rf"{k}:\s+(\d+)", vm).group(1)) for k in ("Pages free", "Pages inactive"))
            return f"{pages * page / 1e9:.1f} GB free (approx.)"
    except Exception as e:  # informational only
        return f"unknown ({type(e).__name__})"
    return "unknown"


def main(transport=None) -> int:
    pins = load_pins()
    problems = []

    def line(label, value, status=""):
        print(f"  {label:<32} {value:<40} {status}")

    print("collusion-evidence-lab environment check")
    py = platform.python_version()
    line("Python", py, "MATCH" if py == WANT_PYTHON else f"MISMATCH (want {WANT_PYTHON})")
    if py != WANT_PYTHON:
        problems.append("python")
    env = os.environ.get("CONDA_DEFAULT_ENV") or Path(sys.prefix).name
    line("Conda env", env, "MATCH" if env == WANT_ENV else f"MISMATCH (want {WANT_ENV})")
    if env != WANT_ENV:
        problems.append("conda env")
    harness = REPO_ROOT / "external" / "llm-trust-breaking" / "src" / "endogenous" / "core" / "prompt_builders.py"
    line("Harness (external/)", "present" if harness.exists() else "missing", "OK" if harness.exists() else "MISSING")
    if not harness.exists():
        problems.append("harness")
    line("GPU", gpu_name())
    line("RAM", free_ram_gb())

    t = transport or OllamaTransport()
    try:
        version, tags = t.version(), t.tags()
    except TransportError as e:
        line("Ollama", "not reachable", f"ERROR ({e}) - is the Ollama app / `ollama serve` running?")
        print("RESULT: NOT READY (Ollama not reachable)")
        return 1
    want_v = pins["ollama_version"]
    line("Ollama version", version, "MATCH" if version == want_v else f"MISMATCH (want {want_v})")
    if version != want_v:
        problems.append("ollama version")
    for tag, spec in pins["models"].items():
        got = tags.get(tag)
        if got is None:
            status = "MISSING" + ("" if spec["required"] else " (optional on this machine)")
            if spec["required"]:
                problems.append(f"{tag} missing")
        elif got == spec["digest"]:
            status = "MATCH"
        else:
            status = f"MISMATCH (want {spec['digest'][:12]}...)"
            problems.append(f"{tag} digest")
        line(f"{tag} [{spec['role']}]", (got or "-")[:16] + ("..." if got else ""), status)
    print("RESULT: READY" if not problems else f"RESULT: NOT READY ({', '.join(problems)})")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
