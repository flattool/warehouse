from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
import os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/snapshot_box.ui")
class SnapshotBox(Gtk.Box):
    __gtype_name__ = "SnapshotBox"

    def __init__(self, folder, **kwargs):
        super().__init__(**kwargs)

        print(folder)