from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/snapshots_list_page.ui")
class SnapshotsListPage(Adw.NavigationPage):
    __gtype_name__ = "SnapshotsListPage"
    gtc = Gtk.Template.Child