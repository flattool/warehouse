from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo
from .error_toast import ErrorToast
from .data_box import DataBox
import pathlib, os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/active_data_page.ui")
class ActiveDataPage(Gtk.ScrolledWindow):
    __gtype_name__ = 'ActiveDataPage'
    gtc = Gtk.Template.Child

    flow_box = gtc()

    def generate_list(self, *args):
        data = f"{HostInfo.home}/.var/app"
        for folder in os.listdir(data):
            print(folder)

    def __init__(self, main_window, data_page, **kwargs):
        super().__init__(**kwargs)

        self.generate_list()

        # self.select_button.connect("toggled", lambda *_: self.set_selection_mode(self.select_button.get_active()))
        # self.flow_box.connect("child-activated", lambda _, item: (cb := (row := item.get_child()).check_button).set_active((not cb.get_active()) if row.get_activatable() else False))

        # Extra Object Creation

        # Apply

        # Connections