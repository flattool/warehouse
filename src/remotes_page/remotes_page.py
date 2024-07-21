from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/remotes_page.ui")
class RemotesPage(Adw.NavigationPage):
    __gtype_name__ = 'RemotesPage'
    gtc = Gtk.Template.Child

    sidebar_button = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        ms = main_window.main_split

        # Connections
        ms.connect("notify::show-sidebar", lambda *_: self.sidebar_button.set_active(ms.get_show_sidebar()))
        self.sidebar_button.connect("toggled", lambda *_: ms.set_show_sidebar(self.sidebar_button.get_active()))