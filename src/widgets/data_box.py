from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/widgets/data_box.ui")
class DataBox(Gtk.ListBox):
    __gtype_name__ = 'DataBox'
    gtc = Gtk.Template.Child

    title_label = gtc()
    check_button = gtc()

    def __init__(self, main_window, path, **kwargs):
        super().__init__(**kwargs)