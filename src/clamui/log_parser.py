from __future__ import annotations
import re, time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

INFECTED_PATTERN = re.compile(r"^.*->\s+([^:]+):.*FOUND$")

import re

def parse_freshclam_log(log_text):
    summary = {
        'last_update': '',
        'components': {}
    }
    summary_str = []
    
    update_time_pattern = r'^(\w+ \w+ \s*\d+ \d{2}:\d{2}:\d{2} \d{4}) -> ClamAV update process started'
    component_pattern = r'-> (\w+\.\w+) database is (up-to-date|outdated) \(version: (\d+), sigs: ([\d,]+), f-level: (\d+), builder: (\w+)\)'
    
    reversed_lines = list(reversed(log_text))
    
    component_log = reversed_lines[0:3]
    
    for i, line in enumerate(reversed_lines[3:]):
        update_time_match = re.search(update_time_pattern, line)
        if update_time_match:
            summary_str.append(f"<b>UPDATER:</b> FreshClam")
            summary_str.append(f"<b>LAST UPDATE:</b> {update_time_match.group(1)}")
            break
        else:
            component_log.append(line)
    
    # Find all component statuses
    component_matches = re.findall(component_pattern, "\n".join(component_log))
    
    for match in component_matches:
        component_name, status, version, _signatures, _f_level, _builder = match
        summary['components'][component_name] = {
            'status': status,
            'version': version,
        }
        
    if summary['components']:
        summary_str.append("\n<b>COMPONENTS:</b>")
        for component, details in summary['components'].items():
            status_icon = "✅ " if details['status'] == 'up-to-date' else "❌"
            summary_str.append(f"{status_icon} {component}  (Version: {details['version']})")

    if len(summary_str) == 0:             
        summary_str.append("Last Update: Not found in log")
        
    return summary_str


def parse_infected_files_from_text(text: str) -> List[str]:
    """Parse infected file paths from clamdscan output text."""
    infected: List[str] = []
    for line in text.splitlines():
        m = INFECTED_PATTERN.match(line.strip())
        if m:
            infected.append(m.group(1))
    return infected
