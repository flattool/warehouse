from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshots.ui")
class SnapshotsWindow(Adw.Window):
    __gtype_name__ = "SnapshotsWindow"
    
    new_env = dict( os.environ )
    new_env['LC_ALL'] = 'C'

    def __init__(self, parent_window, flatpak_row, **kwargs):
        super().__init__(**kwargs)

        self.present()