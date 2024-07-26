from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/snapshot_page.ui")
class SnapshotPage(Adw.BreakpointBin):
    __gtype_name__ = "SnapshotPage"
    gtc = Gtk.Template.Child

    instance = None

    def start_loading(self):
        pass

    def end_loading(self):
        pass

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        self.__class__.instance = self