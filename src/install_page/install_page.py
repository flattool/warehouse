from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .select_page import SelectPage
from .pending_page import PendingPage
from .sidebar_button import SidebarButton
from .loading_status import LoadingStatus

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/install_page.ui")
class InstallPage(Adw.BreakpointBin):
    __gtype_name__ = "InstallPage"
    gtc = Gtk.Template.Child

    break_point = gtc()
    split_view = gtc()
    multi_view = gtc()
    select_page = gtc()
    pending_page = gtc()
    status_stack = gtc()
    loading_view = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None
    page_name = "install"

    current_installation = ""
    current_remote = None

    def start_loading(self):
        self.status_stack.set_visible_child(self.loading_view)
        self.select_page.start_loading()
    
    def end_loading(self):
        self.select_page.end_loading()
        self.status_stack.set_visible_child(self.multi_view)

    def breakpoint_handler(self, bp, is_applied):
        self.select_page.results_page.action_bar.set_revealed(is_applied)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.instance = self

        # Extra Object Creation
        # ======== self.select_page = SelectPage()
        # ======== self.pending_page = PendingPage()

        # Connections
        self.break_point.connect("apply", self.breakpoint_handler, True)
        self.break_point.connect("unapply", self.breakpoint_handler, False)
        self.select_page.results_page.review_button.connect("clicked", lambda *_: self.split_view.set_show_content(True))

        # Apply
        # ======== self.split_view.set_sidebar(self.select_page)
        # ======== self.split_view.set_content(self.pending_page)
        self.select_page.results_page.pending_page = self.pending_page
        self.loading_view.set_content(LoadingStatus(_("Loading Installation Options"), _("This should only take a moment")))
