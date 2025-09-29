from __future__ import annotations
import gi
gi.require_version('Gtk', '4.0'); gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gio, GLib

from .widgets import Card, IconSideBar, CommonStatusBadge, SimpleList, install_css
from .log_parser import parse_latest_summary_from_log, parse_infected_files_from_text
from .utils import load_conf, load_prefs, save_prefs, try_run

APP_TITLE = "ClamAV"

class Dashboard(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application):
        super().__init__(application=app)
        self.set_title(APP_TITLE); self.set_default_size(820, 600)

        self.conf = load_conf(); 
        self.clamav_log = self.conf.get("logs", "clamav-log", "/var/log/clamav/clamav.log")
        self.freshclam_log_ = self.conf.get("logs", "freshclam-log", "/var/log/clamav/fresclam.log")
        self.clamav = self.conf.get("paths", "clamav", "/run/current-system/sw/bin/")

        self.clamdscan = self.conf.get("paths", "clamdscan", fallback="clamdscan")
        self.prefs["log_path"] = self.log_path; save_prefs(self.prefs)

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
        row.append(grid)

        # Top row
        self.card_health = Card("Health"); 
        self.card_health.set_size_request(60, -1)
        self.badge = CommonStatusBadge() 
        self.badge.set_status("healthy", "No threats detected")
        self.card_health.body.append(self.badge)

        self.card_quarantined = Card("Quarantined"); 
        self.card_quarantined.set_size_request(200, -1)

        self.card_watch = Card("Watch list"); 
        self.card_watch.set_size_request(200, -1)
        self.lbl_sys = Gtk.Label(xalign=0); 
        self.card_watch.body.append(self.lbl_sys)

        self.card_system = Card("System"); 
        self.lbl_sys = Gtk.Label(xalign=1); 
        self.card_system.set_size_request(200, -1)

        grid.attach(self.card_health, 0, 0, 1, 1)
        grid.attach(self.card_quarantined, 1, 0, 1, 2)
        grid.attach(self.card_watch, 2, 0, 1, 2)
        grid.attach(self.card_system, 3, 0, 1, 1)


        # Bottom row
        self.card_daemon = Card("Daemon Status"); 
        grid.attach(self.card_daemon, 0, 1, 1, 1)
        self.dbadge = CommonStatusBadge() 
        self.dbadge.set_status("running", "Running")
        self.card_daemon.body.append(self.dbadge)
        
        self.card_virus_db = Card("Virus Database"); 
        grid.attach(self.card_virus_db, 3, 1, 1, 1)

        self.card_logs = Card("Last Scan summary"); 
        grid.attach(self.card_logs, 0, 2, 4, 1)
        self.list_logs = SimpleList(); 
        self.card_logs.set_size_request(-1, 240)
        self.card_logs.body.append(self.list_logs)

        # Bottom action bar (user scan)
        actionbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actionbar.add_css_class("actionbar"); 
        root.append(actionbar)
        self.btn_scan = Gtk.Button(label="Scan"); 
        self.btn_scan.add_css_class("action-btn")
        self.btn_scan.set_halign(Gtk.Align.CENTER)
        self.btn_scan.set_hexpand(True) 
        actionbar.append(self.btn_scan)

        self.btn_scan.connect("clicked", self.on_scan)

        self.refresh()

    def refresh(self):
        summary, err = parse_latest_summary_from_log(self.log_path)
        if err or not summary:
            self.badge.set_status("healthy", "No threats detected")
        else:
            self.badge.set_status(summary.ok)
            self.lbl_sys.set_text(
                f"ClamAV Engine: {summary.engine or 'Unknown'}\n"
                f"Last scan: {summary.end_date or '—'}\n"
                f"Known viruses: {summary.known_viruses or '—'}"
            )
        rc, out, err2 = try_run(["systemctl", "is-active", self.daemon_service])

        try:
            with open(self.log_path, "r", errors="ignore") as fh:
                tail = fh.readlines()[-200:]
        except Exception:
            tail = ["(unable to read daemon log)"]
        self.list_logs.set_items([l.rstrip() for l in tail])

    def on_update(self, _btn):
        # TODO: wire to freshclam / your updater
        pass

    def on_stop(self, _btn):
        # TODO: stop clamd (systemctl stop …) if appropriate/allowed
        pass

    def on_scan(self, _btn):
        dlg = Gtk.FileDialog()
        def done(dialog, res):
            try:
                gf = dialog.open_finish(res)
                if gf and (path := gf.get_path()):
                    self.run_scan(path)
            except GLib.Error:
                pass
        dlg.open(self, None, done)

    def run_scan(self, path: str):
        proc = Gio.Subprocess.new(
            [self.clamdscan, "--multiscan", "--fdpass", "--infected", "--allmatch", path],
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
        )
        out = Gio.DataInputStream.new(proc.get_stdout_pipe())
        err = Gio.DataInputStream.new(proc.get_stderr_pipe())
        self._captured = ""

        GLib.io_add_watch(proc.get_stdout_pipe(), GLib.IOCondition.IN | GLib.IOCondition.HUP,
                          lambda s, c: self._on_io(out, s, c))
        GLib.io_add_watch(proc.get_stderr_pipe(), GLib.IOCondition.IN | GLib.IOCondition.HUP,
                          lambda s, c: self._on_io(err, s, c))

        def done(p, res, data):
            try: p.wait_check_finish(res)
            except GLib.Error: pass
            infected = parse_infected_files_from_text(self._captured)
            if infected:
                self.card_health.body.append(Gtk.Label(label=f"Infected: {len(infected)}", xalign=0))
            self.refresh()
        proc.wait_check_async(None, done, None)

    def _on_io(self, din: Gio.DataInputStream, stream, cond):
        if cond & GLib.IOCondition.IN:
            try: line, _ = din.read_line_utf8(None)
            except GLib.Error: line = None
            if line is not None:
                self._captured += line + "\n"
                return True
        return False

