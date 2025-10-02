from __future__ import annotations
import json, os, subprocess, configparser
from pathlib import Path
from typing import Optional, List, Tuple
from gi.repository import GLib

CONF_ETC = Path("/home/code/clamui/clamui.conf")

def load_conf() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    files: List[str] = []
    if CONF_ETC.exists(): files.append(str(CONF_ETC))
    if files:
        cfg.read(files)
    return cfg

# helpers

def which(cmd: str) -> Optional[str]:
    for p in os.environ.get("PATH", "").split(":"):
        full = os.path.join(p, cmd)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return full
    return None

def try_run(cmd: List[str], timeout: float = 3.0) -> Tuple[int, str, str]:
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return cp.returncode, cp.stdout.strip(), cp.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

