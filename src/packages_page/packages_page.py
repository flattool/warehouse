from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo
from .app_row import AppRow

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/packages_page/packages_page.ui")
class PackagesPage(Adw.BreakpointBin):
    __gtype_name__ = 'PackagesPage'
    gtc = Gtk.Template.Child
    packages_list_box = gtc()
    sidebar_button = gtc()

    package_rows = []

    def generate_list(self, *args):
        for package in HostInfo.flatpaks:
            self.packages_list_box.append(AppRow(package))

    def row_select_handler(self, list_box, row):
        print(row.get_title())

    def sidebar_button_visibility_handler(self):
        self.sidebar_button.set_visible(self.main_window.main_split.get_collapsed() or not self.main_window.main_split.get_show_sidebar())

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.main_window = main_window
        HostInfo.get_flatpaks(self.generate_list)
        self.sidebar_button.connect("clicked", lambda *_: main_window.main_split.set_show_sidebar(True))
        main_window.main_split.connect("notify::show-sidebar", lambda sidebar, *_: self.sidebar_button.set_visible(sidebar.get_collapsed() or not sidebar.get_show_sidebar()))
        main_window.main_split.connect("notify::collapsed", lambda sidebar, *_: self.sidebar_button.set_visible)
        # self.packages_list_box.connect("row-selected", self.row_select_handler)
