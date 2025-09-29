from __future__ import annotations
import json, os, subprocess, configparser
from pathlib import Path
from typing import Optional, List, Tuple
from gi.repository import GLib

CONFIG_DIR = Path(GLib.get_user_config_dir()) / "clamui"
CONFIG_PATH = CONFIG_DIR / "config.json"
CONF_USER = CONFIG_DIR / "clamui.conf"
CONF_ETC = Path("/etc/clamui.conf")

# prefs (small json for last-used log etc.)

def load_prefs() -> dict:
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text())
    except Exception:
        pass
    return {}

def save_prefs(prefs: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(prefs, indent=2))
    except Exception:
        pass

# ini config (clamui.conf)

def load_conf() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg["paths"] = {
        "clamdscan": "clamdscan",
        "daemon_service": "clamav-daemon.service",
        "quarantine_dir": "/var/quarantine",
        "log": "/var/log/clamav/clamav.log",
    }
    cfg["scan"] = {
        "periodic_dirs": "",
    }
    cfg["ui"] = {
        "bg_color": "#2a0e2f",
        "bg_gradient": "#431245",
        "card_bg": "#5b1c5f",
        "accent": "#a855f7",
    }
    files: List[str] = []
    u = str(CONF_USER.expanduser())
    if os.path.exists(u): files.append(u)
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

