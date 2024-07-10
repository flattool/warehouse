from gi.repository import Adw, Gtk, GLib#, Gio, Pango
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/filters_page/filters_page.ui")
class FiltersPage(Adw.NavigationPage):
    __gtype_name__ = 'FiltersPage'
    gtc = Gtk.Template.Child

    def __init__(self, main_window, packages_page, **kwargs):
        super().__init__(**kwargs)
        # self.connect("hidden", lambda *_: packages_page.filter_button.set_active(False))