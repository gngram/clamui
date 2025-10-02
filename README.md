# ClamUI — ClamAV Health Monitor (GTK4)
- Shows health based on the latest **SCAN SUMMARY** in ClamAV logs
- Lets you scan a file/folder with `clamdscan` (async, live output)

## Dev install
pip install -e .

## Run
clamui

## System deps
- GTK4 runtime
- ClamAV (`clamd`, `clamdscan`) running
- PyGObject (pip) or system packages (e.g., `python3-gi`, `gir1.2-gtk-4.0`)

