from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo
from .error_toast import ErrorToast
from .data_box import DataBox

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/leftover_data_page.ui")
class LeftoverDataPage(Gtk.ScrolledWindow):
    __gtype_name__ = 'LeftoverDataPage'
    gtc = Gtk.Template.Child

    def __init__(self, main_window, data_page, **kwargs):
        super().__init__(**kwargs)

    # Extra Object Creation

    # Apply

    # Connections