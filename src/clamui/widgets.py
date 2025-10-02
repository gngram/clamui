from __future__ import annotations
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
from typing import Optional, Iterable

#.sidebar  { background: rgba(0,0,0,0.12); border-radius: 16px; padding: 12px; }
#.sidebar .btn { margin: 6px 0; }
# ---------- CSS (purple gradient + cards) ----------
CSS = b"""
.app-root { background-image: linear-gradient(135deg, #2a0e2f, #431245); }

.card { background: #5b1c5f; color: #fff; border-radius: 16px; padding: 12px; }
.card-title { font-weight: 700; letter-spacing: .06em; margin-bottom: 12px; }
.card-footer { margin-top: 12px; }

.status-badge.ok { color: #16a34a; }
.status-badge.bad { color: #ef4444; }
.status-badge.unknown { color: #9ca3af; }

.action-btn { background: rgba(255,255,255,0.18); color: #fff; border-radius: 10px; padding: 8px 10px; }
.action-btn:hover { background: rgba(255,255,255,0.26); }

.actionbar { background: rgba(0,0,0,0.12); border-radius: 12px; padding: 6px 10px; }
"""

def install_css(widget: Gtk.Widget):
    provider = Gtk.CssProvider(); provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    widget.add_css_class("app-root")

# ---------- Reusable UI ----------
class Card(Gtk.Box):
    def __init__(self, title: str):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add_css_class("card")
        title_lbl = Gtk.Label(label=title, xalign=0.5)
        title_lbl.add_css_class("card-title")
        self.append(title_lbl)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.append(self.body)
        self.footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.footer.add_css_class("card-footer")
        self.append(self.footer)

class IconSideBar(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add_css_class("sidebar")
        for icon in ["emblem-ok-symbolic", "emblem-synchronizing-symbolic", "emblem-system-symbolic"]:
            b = Gtk.Button(); b.add_css_class("btn")
            b.set_child(Gtk.Image.new_from_icon_name(icon))
            self.append(b)

class SimpleList(Gtk.ScrolledWindow):
    def __init__(self, height = 300):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.listbox = Gtk.ListBox()
        self.set_size_request(-1, height)
        self.set_child(self.listbox)

    def set_items(self, items: Iterable[str]):
        # GTK4: remove children via first/next
        child = self.listbox.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.listbox.remove(child)
            child = nxt
        for s in items:
            self.listbox.append(Gtk.Label(label=s, xalign=0))
        self.listbox.show()

class CommonStatusBadge(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.set_margin_top(2)
        self.set_margin_bottom(2)
        self.set_halign(Gtk.Align.CENTER)
        
        # Large emoji on top
        self.emoji_label = Gtk.Label()
        self.emoji_label.set_markup('<span size="300%">🛡️</span>')  # Very large emoji
        
        # Details below that
        self.details_label = Gtk.Label()
        self.details_label.set_halign(Gtk.Align.CENTER)
        self.details_label.set_opacity(0.8)
        
        self.append(self.emoji_label)
        self.append(self.details_label)
        
        self.set_status("unknown")
    
    def set_status(self, status, details=""):
        status_config = {
            "running": ("🟢"),
            "offline": ("🔴"),
            "healthy": ("🛡️"),
            "infected": ("💀"),
            "warning": ("⚠️"),
            "offline": ("🔌"),
            "scanning": ("🔍"),
            "unknown": ("❓")
        }
        
        emoji = status_config.get(status, status_config["unknown"])
        self.emoji_label.set_markup(f'<span size="300%">{emoji}</span>')
        self.details_label.set_text(details)        
