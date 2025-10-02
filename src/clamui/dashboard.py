from __future__ import annotations
import gi
import subprocess
import os
gi.require_version('Gtk', '4.0'); gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gio, GLib

from .widgets import Card, IconSideBar, CommonStatusBadge, SimpleList, install_css
from .log_parser import parse_freshclam_log, parse_infected_files_from_text
from .utils import load_conf, try_run

APP_TITLE = "ClamAV"

class Dashboard(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application):
        super().__init__(application=app)
        self.set_title(APP_TITLE); self.set_default_size(820, 600)

        self.conf = load_conf(); 
        self.clamd_log = self.conf.get("logs", "clamd-log")
        self.freshclam_log = self.conf.get("logs", "freshclam-log")
        self.clamav = self.conf.get("paths", "clamav")

        self.clamscan = self.clamav + "/clamscan"
                
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        install_css(root); self.set_child(root)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        root.append(row)
        row.set_hexpand(True)

        grid = Gtk.Grid(column_spacing=12, row_spacing=12)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        grid.set_hexpand(True)
        grid.set_halign(Gtk.Align.CENTER)
        row.append(grid)

        # Top row
        self.card_health = Card("HEALTH"); 
        self.card_health.set_size_request(60, -1)
        self.health_badge = CommonStatusBadge() 
        self.health_badge.set_status("unknown", "Unknown")
        self.card_health.body.append(self.health_badge)
        
        self.card_watch = Card("WATCH LIST"); 
        self.card_watch.set_size_request(400, -1)
        self.lbl_watch = Gtk.Label(xalign=0); 
        self.card_watch.body.append(self.lbl_watch)

        self.card_system = Card("SYSTEM"); 
        self.card_system.set_size_request(300, -1)
        
        clamav_version = self.get_clamav_version()
        
        lbl_sys_ver = Gtk.Label()
        lbl_sys_ver.set_markup(
            f"\n<b>PACKAGE:</b> ClamAV\n<b>VERSION:</b> {clamav_version}\n")
        lbl_sys_ver.set_halign(Gtk.Align.START)

        lbl_db_tag = Gtk.Label()
        lbl_db_tag.set_markup(f"<b>VIRUS DATABASE</b>")
        lbl_db_tag.set_halign(Gtk.Align.CENTER)

        self.lbl_db_info = Gtk.Label()
        self.lbl_db_info.set_halign(Gtk.Align.START)
        
        self.card_system.body.append(lbl_sys_ver)
        self.card_system.body.append(lbl_db_tag)
        self.card_system.body.append(self.lbl_db_info)        

        grid.attach(self.card_health, 0, 0, 1, 1)
        grid.attach(self.card_watch, 1, 0, 1, 2)
        grid.attach(self.card_system, 2, 0, 1, 2)

        self.card_daemon = Card("DAEMON STATUS"); 
        grid.attach(self.card_daemon, 0, 1, 1, 1)
        self.daemon_badge = CommonStatusBadge() 
        self.daemon_badge.set_status("offline", "Offline")
        self.card_daemon.body.append(self.daemon_badge)
                
        self.card_infected = Card("INFECTED FILES"); 
        grid.attach(self.card_infected, 0, 2, 4, 1)
        self.list_infected = SimpleList(height=200); 
        self.card_infected.set_size_request(-1, 240)
        self.card_infected.body.append(self.list_infected)

        self.card_logs = Card("DAEMON LOG"); 
        grid.attach(self.card_logs, 0, 3, 4, 1)
        self.list_logs = SimpleList(height=250); 
        self.card_logs.set_size_request(-1, 240)
        self.card_logs.body.append(self.list_logs)

        actionbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actionbar.add_css_class("actionbar"); 
        root.append(actionbar)
        self.btn_scan = Gtk.Button(label="Scan"); 
        self.btn_scan.add_css_class("action-btn")
        self.btn_scan.set_halign(Gtk.Align.CENTER)
        self.btn_scan.set_hexpand(True) 
        actionbar.append(self.btn_scan)

        self.btn_scan.connect("clicked",  lambda btn: self.on_scan())
        self.refresh()

    def refresh(self):
        rc, out, err2 = try_run(["systemctl", "is-active", "clamav-daemon.service"])
        log = ["(unable to read daemon log)"]
        infected_files = ["(service not active)"]
        db_info = ["<b>LAST UPDATE:</b> Not found!"]
        if rc==0 and out == "active":
            self.daemon_badge.set_status("running", "Running")
            try:
                with open(self.clamd_log, "r", errors="ignore") as fh:
                    text = fh.read()
                    infected_files = parse_infected_files_from_text(text)

                    if len(infected_files):
                        self.health_badge.set_status("infected", "Infected")
                    else:
                        self.health_badge.set_status("healthy", "No threats detected")
                        
                    fh.seek(0)
                    log = fh.readlines()[-200:]

                with open(self.freshclam_log, "r", errors="ignore") as fd:
                    fc_log = fd.readlines()
                    db_info = parse_freshclam_log(fc_log)
                
            except Exception:
                print(f"Unable to read log file")
            
        else:
            self.daemon_badge.set_status("offline", "Offline")
            self.health_badge.set_status("unknown", "Unknown")
            
        self.list_logs.set_items([l.rstrip() for l in log])
        self.list_infected.set_items([l.rstrip() for l in infected_files])
        self.lbl_db_info.set_markup("\n".join(db_info))

    def get_clamav_version(self):
        try:
            print(self.clamscan)
            if not os.path.exists(self.clamscan):
                return "Unknown"
            
            result = subprocess.run(
                [self.clamscan, '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        
        except subprocess.CalledProcessError as e:
            return "Unknown"
        except Exception as e:
            return "Unknown"
            

    def on_scan(self):
        """Simple method to select either file or folder"""
        file_dlg = Gtk.FileDialog()
        file_dlg.set_title("Select File to Scan")
        file_dlg.open(self, None, self._on_path_selected)

    def _on_path_selected(self, dialog, result):
        """Handle the selected path"""
        try:
            file = dialog.open_finish(result)
            if file is not None:
                path = file.get_path()
                print(f"Selected: {path}")
                self.run_scan(path)
        except Exception as e:
            print("Selection cancelled")


    def _show_scan_report(self, title: str, message: str) -> bool:
        dlg = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.CLOSE,
            text=title,
            secondary_text=message,
        )
        dlg.connect("response", lambda d, _r: d.destroy())
        dlg.present()
        return False
    
    def run_scan(self, path: str):
        scanning_dlg = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.NONE,
            text="Scanning...",
            secondary_text=f"Scanning: {path}\n\nThis may take a few moments...",
        )

        scanning_dlg.present()

        proc = Gio.Subprocess.new(
            [self.clamscan, "--stdout", "-r", "--infected", path],
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
        )

        proc.communicate_utf8_async(None, None, self._on_scan_complete, (scanning_dlg, path))

    def _on_scan_complete(self, proc, result, data):
        scanning_dlg, path = data

        try:
            success, stdout, stderr = proc.communicate_utf8_finish(result)
            result_text = stdout if success else f"Error: {stderr}"
            scanning_dlg.destroy()
            self._show_scan_report("Scan Result", result_text)

        except Exception as e:
            print(f"Scan error: {e}")
            scanning_dlg.destroy()
            self._show_scan_report("Scan Error", str(e))

    def _on_io(self, din: Gio.DataInputStream, stream, cond):
        if cond & GLib.IOCondition.IN:
            try: line, _ = din.read_line_utf8(None)
            except GLib.Error: line = None
            if line is not None:
                self._captured += line + "\n"
                return True
        return False

