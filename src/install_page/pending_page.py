from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/pending_page.ui")
class PendingPage(Adw.NavigationPage):
    __gtype_name__ = "PendingPage"
    gtc = Gtk.Template.Child

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
