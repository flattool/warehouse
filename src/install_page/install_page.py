from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .app_row import AppRow
from .snapshots_list_page import SnapshotsListPage
from .result_row import ResultRow
import os, subprocess

class AddedPackage:
    def __init__(self, name, app_id, branch, version, remote, installation):
        self.name = name
        self.app_id = app_id
        self.branch = branch
        self.version = version
        self.remote = remote
        self.installation = installation

class AddedGroup(Adw.PreferencesGroup):
    __gtype_name__ = "AddedGroup"

    package_rows = []

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

        self.set_title(f"{remote.title}")
        self.set_description(_("Installation: {}").format(installation))

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/install_page.ui")
class InstallPage(Adw.BreakpointBin):
    __gtype_name__ = "InstallPage"
    gtc = Gtk.Template.Child

    remotes_group = gtc()
    sb_page_view = gtc()
    results = gtc()
    back_button = gtc()
    search_entry = gtc()
    search_apply_button = gtc()
    results_list = gtc()
    added_pref_page = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    current_installation = ""
    current_remote = None

    def start_loading(self):
        for row in self.remote_rows:
            self.remotes_group.remove(row)
        self.remote_rows.clear()
        self.added_packages.clear()
        self.added_package_groups.clear()

    def end_loading(self):
        for installation in HostInfo.installations:
            for remote in HostInfo.remotes[installation]:
                if remote.disabled:
                    continue
                row = Adw.ActionRow(title=remote.title, subtitle=_("Installation: {}").format(installation), activatable=True)
                row.add_suffix(Gtk.Image(icon_name="right-large-symbolic"))
                row.connect("activated", self.remote_selected, installation, remote)
                self.remotes_group.add(row)
                self.remote_rows.append(row)

    def remote_selected(self, row, installation, remote):
        self.current_installation = installation
        self.current_remote = remote
        self.results.set_title(_("Search {}").format(remote.title))
        self.sb_page_view.push(self.results)
        self.search_entry.set_text("firefox")
        self.search_entry.grab_focus()

    def on_search(self, _):
        text = self.search_entry.get_text().strip().lower().replace(" ", "")
        if not text:
            return

        results = []
        def thread(*args):
            installation = ""
            self.results_list.remove_all()
            if self.current_installation == "user" or self.current_installation == "system":
                installation = f"--{self.current_installation}"
            else:
                installation = f"--installation={self.current_installation}"
        
            try:
                output = subprocess.run(['flatpak-spawn', '--host', 'flatpak', 'search', '--columns=all', installation, text], text=True, check=True, capture_output=True).stdout.split("\n")
                for i, line in enumerate(output):
                    info = line.split("\t")
                    if len(info) != 6:
                        continue
                    
                    name = GLib.markup_escape_text(info[0])
                    description = GLib.markup_escape_text(info[1])
                    app_id = GLib.markup_escape_text(info[2])
                    version = GLib.markup_escape_text(info[3])
                    branch = GLib.markup_escape_text(info[4])
                    remotes = info[5]

                    if not self.current_remote.name in remotes.split(','):
                        continue

                    is_added = False
                    try:
                        for package in self.added_packages:
                            if package.name == name and package.app_id == app_id and package.version == version and package.branch == branch:
                                is_added = True
                                break

                    except KeyError:
                        print("passing key error")

                    if not is_added:
                        row = ResultRow(name, app_id, branch, version)
                        row.connect("activated", self.add_package, i, name, app_id, branch, version)
                        self.results_list.append(row)
            
            except Exception as e:
                print(e)
            except subprocess.CalledProcessError as cpe:
                print(cpe)

        thread()

    def list_focus_grabber(self, row):
        i = 0
        prev_visible_row = None
        while rover := self.results_list.get_row_at_index(i):
            i += 1
            if rover is row:
                break

            if rover.get_visible():
                prev_visible_row = rover

        while rover := self.results_list.get_row_at_index(i):
            i += 1
            if rover.get_visible():
                rover.grab_focus()
                return

        if prev_visible_row:
            prev_visible_row.grab_focus()

    def add_package(self, row, index, name, app_id, branch, version):
        key = f"{self.current_remote}<>{self.current_installation}"
        package = AddedPackage(name, app_id, branch, version, self.current_remote, self.current_installation)
        added_row = ResultRow(name, app_id, branch, version, row)
        self.added_packages.append(package)
        group = None
        try:
            group = self.added_package_groups[key]
            group.add_row(added_row)
        except KeyError:
            group = AddedGroup(self.current_remote, self.current_installation)
            self.added_package_groups[key] = group
            self.added_pref_page.add(group)
            group.add_row(added_row)
        except Exception as e:
            print(e)
            return
        added_row.connect("activated", self.remove_package, group)
        row.set_visible(False)
        self.list_focus_grabber(row)

    def remove_package(self, row, group):
        row.original_row.set_visible(True)
        group.rem_row(row)
        if len(group.package_rows) == 0:
            group.set_visible(False)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.instance = self
        self.main_window = main_window
        self.remote_rows = []
        self.added_packages = [] # remote<>installation
        self.added_package_groups = {} # remote<>installation
        self.back_button.connect("clicked", lambda *_: self.sb_page_view.pop())
        # self.search_entry.connect("search-changed", self.on_search)
        self.search_entry.connect("activate", self.on_search)
        self.search_apply_button.connect("clicked", self.on_search)