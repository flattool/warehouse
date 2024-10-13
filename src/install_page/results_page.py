from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .result_row import ResultRow
from .loading_status import LoadingStatus
import subprocess

class AddedPackage:
    def __eq__(self, other):
        return (
            self.name == other.name
            and self.app_id == other.app_id
            and self.branch == other.branch
            and self.version == other.version
            and self.remote == other.remote
            and self.installation == other.installation
        )

    def is_similar(self, other):
        return (
            self.app_id == other.app_id
            and self.branch == other.branch
            and self.version == other.version
        )

    def __init__(self, name, app_id, branch, version, remote, installation):
        self.name = name
        self.app_id = app_id
        self.branch = branch
        self.version = version
        self.remote = remote
        self.installation = installation

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/results_page.ui")
class ResultsPage(Adw.NavigationPage):
    __gtype_name__ = "ResultsPage"
    gtc = Gtk.Template.Child
    
    search_entry = gtc()
    results_list = gtc()
    stack = gtc()
    new_search = gtc()
    too_many = gtc()
    results_view= gtc()
    no_results = gtc()
    
    def show_remote(self, row, remote, installation, nav_view=None):
        self.remote = remote
        self.installation = installation
        self.set_title(_("Search {}").format(remote.title))
        self.search_entry.set_text("")
        self.search_entry.grab_focus()
        if nav_view:
            nav_view.push(self)
            
    def add_package_row(self, row):
        self.pending_page.add_package_row(row)
        if not self.install_page is None:
            self.install_page.package_added()
            
    def on_search(self, *args):
        self.packages.clear()
        self.stack.set_visible_child(self.loading)
        self.results_list.remove_all()
        search_text = self.search_entry.get_text()
        if search_text == "":
            self.stack.set_visible_child(self.new_search)
            return
            
        def thread(*args):
            installation = ""
            if self.installation == "user" or self.installation == "system":
                installation = f"--{self.installation}"
            else:
                installation = f"--installation={self.installation}"
                
            try:
                output = subprocess.run(
                    ['flatpak-spawn', '--host', 'flatpak', 'search', '--columns=all', installation, self.search_entry.get_text()],
                    check=True, text=True, capture_output=True
                ).stdout.split('\n')
                if len(output) > 100:
                    GLib.idle_add(lambda *_: self.stack.set_visible_child(self.too_many))
                    return
                    
                for line in output:
                    line = line.strip()
                    
                    info = line.split('\t')
                    if len(info) != 6:
                        continue
                        
                    remotes = info[5].split(',')
                    if not self.remote.name in remotes:
                        continue
                        
                    package = AddedPackage(info[0], info[2], info[4], info[3], self.remote, self.installation)
                    row = ResultRow(package, ResultRow.PackageState.NEW, self.results_list)
                    for item in self.pending_page.added_packages:
                        if package.is_similar(item):
                            row.set_state(ResultRow.PackageState.SELECTED)
                            
                    if package.app_id in HostInfo.id_to_flatpak:
                        installed_package = HostInfo.id_to_flatpak[package.app_id]
                        if installed_package.info["id"] == package.app_id and installed_package.info["branch"] == package.branch:
                            row.set_state(ResultRow.PackageState.INSTALLED)
                            
                    row.connect("activated", self.add_package_row)
                    self.packages.append(package)
                    GLib.idle_add(lambda *_, _row=row: self.results_list.append(_row))
                    
                if len(self.packages) > 0:
                    GLib.idle_add(lambda *_: self.stack.set_visible_child(self.results_view))
                else:
                    GLib.idle_add(lambda *_: self.stack.set_visible_child(self.no_results))
                    
            except subprocess.CalledProcessError as cpe:
                print(cpe)
                
        Gio.Task().run_in_thread(thread)
        
    def on_back(self, *args):
        self.results_list.remove_all()
        self.stack.set_visible_child(self.new_search)
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Extra Object Creation
        self.remote = None
        self.installation = None
        self.packages = []
        self.pending_page = None
        self.loading = LoadingStatus(_("Searching"), _("This should only take a moment"))
        self.install_page = None
        
        # Connections
        self.search_entry.connect("search-changed", self.on_search)
        
        # Apply
        self.stack.add_child(self.loading)
