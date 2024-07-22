from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/add_remote_dialog.ui")
class AddRemoteDialog(Adw.Dialog):
    __gtype_name__ = "AddRemoteDialog"
    gtc = Gtk.Template.Child

    apply_button = gtc()
    title_row = gtc()
    name_row = gtc()
    url_row = gtc()
    installation_row = gtc()

    def on_apply(self, *args):
        print(self.installation_row.get_selected_item().get_string())

    def __init__(self, main_window, remote_info=None, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.string_list = Gtk.StringList(strings=HostInfo.installations)

        # Apply
        self.installation_row.set_model(self.string_list)

        # Connections
        self.apply_button.connect("clicked", self.on_apply)