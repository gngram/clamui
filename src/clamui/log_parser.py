from __future__ import annotations
import re, time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

LOG_SUMMARY_SEP = re.compile(r"^-+ SCAN SUMMARY -+$")
KV_LINE = re.compile(r"^([^:]+):\s*(.*)$")
INFECTED_PATTERN = re.compile(r"^(.*?):.*?FOUND$")

@dataclass
class ScanSummary:
    engine: Optional[str] = None
    known_viruses: Optional[int] = None
    scanned_dirs: Optional[int] = None
    scanned_files: Optional[int] = None
    infected: Optional[int] = None
    data_scanned: Optional[str] = None
    data_read: Optional[str] = None
    time_taken: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    when: Optional[datetime] = None

    @property
    def ok(self) -> Optional[bool]:
        return None if self.infected is None else self.infected == 0

def _to_int(v: Optional[str]) -> Optional[int]:
    try:
        return int(v.replace(",", "")) if v is not None else None
    except Exception:
        return None

def parse_scan_summary_block(block_lines: List[str]) -> ScanSummary:
    kv: dict[str, str] = {}
    for line in block_lines:
        m = KV_LINE.match(line.strip())
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            kv[key] = val
    when = None
    if "End Date" in kv:
        try:
            when = datetime.fromtimestamp(
                time.mktime(time.strptime(kv["End Date"], "%a %b %d %H:%M:%S %Y"))
            )
        except Exception:
            pass
    return ScanSummary(
        engine=kv.get("Engine version"),
        known_viruses=_to_int(kv.get("Known viruses")),
        scanned_dirs=_to_int(kv.get("Scanned directories")),
        scanned_files=_to_int(kv.get("Scanned files")),
        infected=_to_int(kv.get("Infected files")),
        data_scanned=kv.get("Data scanned"),
        data_read=kv.get("Data read"),
        time_taken=kv.get("Time"),
        start_date=kv.get("Start Date"),
        end_date=kv.get("End Date"),
        when=when,
    )

def parse_latest_summary_from_log(log_path: str) -> Tuple[Optional[ScanSummary], Optional[str]]:
    try:
        content = Path(log_path).read_text(errors="ignore")
    except Exception as e:
        return None, f"Failed to read log: {e}"
    lines = content.splitlines()

    blocks: List[List[str]] = []
    i = 0
    while i < len(lines):
        if LOG_SUMMARY_SEP.match(lines[i].strip()):
            j = i + 1
            block: List[str] = []
            while j < len(lines) and not LOG_SUMMARY_SEP.match(lines[j].strip()):
                block.append(lines[j]); j += 1
            blocks.append(block); i = j
        else:
            i += 1
    if not blocks:
        return None, "No SCAN SUMMARY found in log. Run a scan to generate one."
    return parse_scan_summary_block(blocks[-1]), None

def parse_infected_files_from_text(text: str) -> List[str]:
    """Parse infected file paths from clamdscan output text."""
    infected: List[str] = []
    for line in text.splitlines():
        m = INFECTED_PATTERN.match(line.strip())
        if m:
            infected.append(m.group(1))
    return infected
