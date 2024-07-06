from gi.repository import Adw, Gtk#, GLib, Gio, Pango
from .host_info import HostInfo
from .app_row import AppRow
from .error_toast import ErrorToast

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/packages_page/packages_page.ui")
class PackagesPage(Adw.BreakpointBin):
    __gtype_name__ = 'PackagesPage'
    gtc = Gtk.Template.Child
    packages_toast_overlay = gtc()
    sidebar_button = gtc()
    refresh_button = gtc()
    search_entry = gtc()
    packages_list_box = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    def generate_list(self, *args):
        self.packages_list_box.remove_all()
        for package in HostInfo.flatpaks:
            self.packages_list_box.append(AppRow(package))

    def row_select_handler(self, list_box, row):
        print(row.get_title())

    def filter_func(self, row):
        search_text = self.search_entry.get_text().lower()
        title = row.get_title().lower()
        subtitle = row.get_subtitle().lower()
        if search_text in title or search_text in subtitle:
            return True

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.main_window = main_window

        # Apply
        HostInfo.get_flatpaks(callback=self.generate_list)
        self.packages_list_box.set_filter_func(self.filter_func)
        self.__class__.instance = self

        # Connections
        main_window.main_split.connect("notify::show-sidebar", lambda sidebar, *_: self.sidebar_button.set_visible(sidebar.get_collapsed() or not sidebar.get_show_sidebar()))
        main_window.main_split.connect("notify::collapsed", lambda sidebar, *_: self.sidebar_button.set_visible(sidebar.get_collapsed() or not sidebar.get_show_sidebar()))
        self.sidebar_button.connect("clicked", lambda *_: main_window.main_split.set_show_sidebar(True))
        self.refresh_button.connect("clicked", lambda *_: HostInfo.get_flatpaks(callback=self.generate_list))
        self.search_entry.connect("search-changed", lambda *_: self.packages_list_box.invalidate_filter())
        # self.packages_list_box.connect("row-selected", self.row_select_handler)

