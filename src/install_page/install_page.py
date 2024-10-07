from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .select_page import SelectPage
from .pending_page import PendingPage
from .sidebar_button import SidebarButton
from .loading_status import LoadingStatus
from .package_install_worker import PackageInstallWorker
from .error_toast import ErrorToast

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
    installing_view = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None
    page_name = "install"

    current_installation = ""
    current_remote = None
    did_error = False

    def start_loading(self):
        self.status_stack.set_visible_child(self.loading_view)
        self.select_page.start_loading()
    
    def end_loading(self):
        self.select_page.end_loading()
        self.status_stack.set_visible_child(self.multi_view)
        
    def install_callback(self):
        HostInfo.main_window.refresh_handler()
        if not self.did_error:
            HostInfo.main_window.toast_overlay.add_toast(Adw.Toast(title=_("Installed Packages")))
        
    def install_error_callback(self, user_facing_label, error_message):
        self.did_error = True
        GLib.idle_add(lambda *_: HostInfo.main_window.toast_overlay.add_toast(ErrorToast(user_facing_label, error_message).toast))
        
    def install_packages(self, package_requests):
        print(package_requests)
        self.did_error = False
        if PackageInstallWorker.install(package_requests, self.installing_status, self.install_callback, self.install_error_callback):
            self.status_stack.set_visible_child(self.installing_view)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.instance = self

        # Extra Object Creation
        self.installing_status = LoadingStatus(_("Installing Packages"), _("This could take a while"), True, PackageInstallWorker.cancel)

        # Connections

        # Apply
        self.select_page.results_page.pending_page = self.pending_page
        self.loading_view.set_content(LoadingStatus(_("Loading Installation Options"), _("This should only take a moment")))
        self.installing_status.button.set_label(_("Cancel"))
        self.installing_view.set_content(self.installing_status)
