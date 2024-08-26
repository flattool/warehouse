from gi.repository import Adw, Gtk, Gdk, GLib
from .host_info import HostInfo

class SidebarButton(Gtk.ToggleButton):
    __gtype_name__ = "SidebarButton"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Extra Object Creation
        main_split = HostInfo.main_window.main_split

        # Connections
        main_split.connect("notify::show-sidebar", lambda *_: self.set_active(main_split.get_show_sidebar()))
        self.connect("toggled", lambda *_: main_split.set_show_sidebar(self.get_active()))

        # Apply
        self.set_icon_name("dock-left-symbolic")
        self.set_tooltip_text(_("Show Sidebar"))