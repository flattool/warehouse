from gi.repository import Gtk
from .host_info import HostInfo

class SidebarButton(Gtk.Button):
    __gtype_name__ = "SidebarButton"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Extra Object Creation
        main_split = HostInfo.main_window.main_split

        # Connections
        main_split.connect("notify::collapsed", lambda *_: self.set_visible(main_split.get_collapsed()))
        self.connect("clicked", lambda *_: main_split.set_show_sidebar(True))

        # Apply
        self.set_icon_name("dock-left-symbolic")
        self.set_tooltip_text(_("Show Sidebar"))
