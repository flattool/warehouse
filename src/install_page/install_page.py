from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .select_page import SelectPage
from .pending_page import PendingPage

class AddedGroup(Adw.PreferencesGroup):
    __gtype_name__ = "AddedGroup"

    def add_row(self, row):
        self.package_rows.append(row)
        self.add(row)
        self.set_visible(True)

    def rem_row(self, row):
        if row in self.package_rows:
            self.package_rows.remove(row)
            self.remove(row)

    def __init__(self, remote, installation, **kwargs):
        super().__init__(**kwargs)

        self.remote = remote
        self.installation = installation
        self.package_rows = []

        self.set_title(f"{remote.title}")
        self.set_description(_("Installation: {}").format(installation))

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/install_page.ui")
class InstallPage(Adw.BreakpointBin):
    __gtype_name__ = "InstallPage"
    gtc = Gtk.Template.Child

    break_point = gtc()
    select_page = gtc()
    split_view = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    current_installation = ""
    current_remote = None

    def start_loading(self):
        self.select_page.start_loading()
    
    def end_loading(self):
        self.select_page.end_loading()

    def breakpoint_handler(self, bp, is_applied):
        self.select_page.results_page.action_bar.set_revealed(is_applied)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.instance = self

        # Extra Object Creation

        # Connections
        self.break_point.connect("apply", self.breakpoint_handler, True)
        self.break_point.connect("unapply", self.breakpoint_handler, False)
        self.select_page.results_page.review_button.connect("clicked", lambda *_: self.split_view.set_show_content(True))

        # Apply
