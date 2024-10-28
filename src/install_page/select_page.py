from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .results_page import ResultsPage
from .sidebar_button import SidebarButton
from .file_install_dialog import FileInstallDialog

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/select_page.ui")
class SelectPage(Adw.NavigationPage):
    __gtype_name__ = "SelectPage"
    gtc = Gtk.Template.Child
    
    nav_view = gtc()
    results_page = gtc()
    remotes_group = gtc()
    add_remote_row = gtc()
    open_row = gtc()
    
    def start_loading(self):
        self.nav_view.pop()
        for row in self.remote_rows:
            self.remotes_group.remove(row)
        self.remote_rows.clear()
        
    def end_loading(self):
        for installation, remotes in HostInfo.remotes.items():
            for remote in remotes:
                if remote.disabled:
                    continue
                    
                row = Adw.ActionRow(title=remote.title, subtitle=_("Installation: {}").format(installation), activatable=True)
                row.add_suffix(Gtk.Image(icon_name="right-large-symbolic"))
                row.connect("activated", self.results_page.show_remote, remote, installation, self.nav_view)
                self.remotes_group.add(row)
                self.remote_rows.append(row)
                
        self.remotes_group.set_visible(len(self.remote_rows) != 0)
        
    def local_install_apply_callback(self, installation, file_names):
        install_page = HostInfo.main_window.pages[HostInfo.main_window.install_row]
        requests = []
        for file in file_names:
            # sadly flatpak doesn't support multiple local installs in one command :(
            requests.append({
                "remote": "local_file",
                "installation": installation,
                "package_names": [file.get_path()],
                "extra_flags": [],
            })
            
        install_page.install_packages(requests)
        
    def file_dialog_handler(self, files):
        FileInstallDialog(self, files, self.local_install_apply_callback).present(HostInfo.main_window)
        
    def file_choose_callback(self, object, result):
        try:
            files = object.open_multiple_finish(result)
            if not files:
                HostInfo.main_window.toast_overlay.add_toast(ErrorToast(_("Could not add files"), _("No files were found to install")))
                return
                
            self.file_dialog_handler(files)
            
        except GLib.GError as gle:
            if not (gle.domain == "gtk-dialog-error-quark" and gle.code == 2):
                HostInfo.main_window.toast_overlay.add_toast(ErrorToast(_("Could not add files"), str(gle)).toast)
                
    def on_open(self, *args):
        file_filter = Gtk.FileFilter(name=_("Flatpaks"))
        file_filter.add_suffix("flatpak")
        file_filter.add_suffix("flatpakref")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)
        file_chooser = Gtk.FileDialog()
        file_chooser.set_filters(filters)
        file_chooser.set_default_filter(file_filter)
        file_chooser.open_multiple(HostInfo.main_window, None, self.file_choose_callback)
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Extra Object Creation
        self.remote_rows = []
        
        # Connections
        self.add_remote_row.connect("activated", lambda *_: HostInfo.main_window.activate_row(HostInfo.main_window.remotes_row))
        self.nav_view.connect("popped", self.results_page.on_back)
        self.open_row.connect("activated", self.on_open)
