from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .app_row import AppRow
from .snapshots_list_page import SnapshotsListPage
from .result_row import ResultRow
import os, subprocess

class AddedPackage:
    def __eq__(self, other):
        return (
            self.name == other.name and \
            self.app_id == other.app_id and \
            self.branch == other.branch and \
            self.version == other.version and \
            self.remote == other.remote and \
            self.installation == other.installation
        )

    def is_similar(self, other):
        return (
            self.app_id == other.app_id and \
            self.branch == other.branch and \
            self.version == other.version
        )

    def __init__(self, name, app_id, branch, version, remote, installation):
        self.name = name
        self.app_id = app_id
        self.branch = branch
        self.version = version
        self.remote = remote
        self.installation = installation

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

    remotes_group = gtc()
    sb_page_view = gtc()
    results = gtc()
    search_entry = gtc()
    search_apply_button = gtc()
    results_list = gtc()
    added_pref_page = gtc()
    results_action_bar = gtc()
    pending_action_bar = gtc()
    review_button = gtc()
    split_view = gtc()
    sidebar_button = gtc()
    pending_stack = gtc()
    no_added_packages_status = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    current_installation = ""
    current_remote = None

    def start_loading(self):
        self.pending_stack.set_visible_child(self.no_added_packages_status)
        self.added_packages.clear()

        for row in self.remote_rows:
            self.remotes_group.remove(row)
        self.remote_rows.clear()
        
        for _, group in self.added_package_groups.items():
            self.added_pref_page.remove(group)
        self.added_package_groups.clear()

        self.results_action_bar.set_revealed(False)
        self.pending_action_bar.set_revealed(False)
        self.search_entry.set_text("")
        self.results_list.remove_all()
        self.sb_page_view.pop()

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
        self.search_entry.grab_focus()
        self.search_entry.set_text("")
        self.results_list.remove_all()

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
                for line in output:
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

                    current = AddedPackage(name, app_id, branch, version, self.current_remote, self.current_installation)
                    row = ResultRow(current)
                    row.connect("activated", self.add_package)
                    self.results_list.append(row)
                    
                    for other in self.added_packages:
                        if current.is_similar(other):
                            row.set_is_added(True)
                            break

            
            except subprocess.CalledProcessError as cpe:
                print(cpe.stderr)
            except Exception as e:
                print(e)
        
        thread()

    def add_package(self, row):
        row.set_is_added(True)
        self.added_packages.append(row.package)
        self.list_focus_grabber(row)
        added_row = ResultRow(row.package, True)
        self.results_action_bar.set_revealed(True)
        self.pending_action_bar.set_revealed(True)
        try:
            key = f"{row.package.remote}<>{row.package.installation}"
            group = self.added_package_groups[key]
            group.add_row(added_row)
        except KeyError:
            group = AddedGroup(row.package.remote, row.package.installation)
            group.add_row(added_row)
            self.added_package_groups[key] = group
            self.added_pref_page.add(group)

        added_row.connect("activated", self.rem_package, group)
        self.pending_stack.set_visible_child(self.added_pref_page)

    def rem_package(self, row, group):
        if not row.package in self.added_packages:
            return

        self.added_packages.remove(row.package)
        if len(self.added_packages) == 0:
            self.results_action_bar.set_revealed(False)
            self.pending_action_bar.set_revealed(False)

        i = 0
        while rover := self.results_list.get_row_at_index(i):
            i += 1
            if not rover.is_added:
                continue

            if row.package.is_similar(rover.package):
                rover.set_is_added(False)
                break

        group.rem_row(row)
        if len(group.package_rows) == 0:
            self.added_pref_page.remove(group)
            self.added_package_groups.pop(f'{row.package.remote}<>{row.package.installation}', None)

        if len(self.added_package_groups) == 0:
            self.pending_stack.set_visible_child(self.no_added_packages_status)
        
    def list_focus_grabber(self, row):
        i = 0
        prev_unadded_row = None
        while rover := self.results_list.get_row_at_index(i):
            i += 1
            if rover is row:
                break
                
            if not rover.is_added:
                prev_unadded_row = rover

        while rover := self.results_list.get_row_at_index(i):
            i += 1
            if not rover.is_added:
                rover.grab_focus()
                return

        if prev_unadded_row:
            prev_unadded_row.grab_focus()

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.instance = self
        self.main_window = main_window
        self.remote_rows = []
        self.added_packages = []
        self.added_package_groups = {} # remote<>installation
        # self.back_button.connect("clicked", lambda *_: self.sb_page_view.pop())
        # self.search_entry.connect("search-changed", self.on_search)
        self.search_entry.connect("activate", self.on_search)
        self.search_apply_button.connect("clicked", self.on_search)
        self.review_button.connect("clicked", lambda *_: self.split_view.set_show_content(True))

        ms = main_window.main_split
        ms.connect("notify::show-sidebar", lambda *_: self.sidebar_button.set_active(ms.get_show_sidebar()))
        self.sidebar_button.connect("toggled", lambda *_: ms.set_show_sidebar(self.sidebar_button.get_active()))
