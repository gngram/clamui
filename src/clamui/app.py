from __future__ import annotations
import sys, gi
gi.require_version('Gtk', '4.0'); gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gio
from .dashboard import Dashboard

APP_ID = "ghaf.io"
class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.example.ClamAVDesktop", flags=Gio.ApplicationFlags.FLAGS_NONE)
    def do_activate(self, *args):
        Dashboard(self).present()

def main(argv=None):
    app = App()
    return app.run(sys.argv if argv is None else argv)

if __name__ == "__main__":
    raise SystemExit(main())

