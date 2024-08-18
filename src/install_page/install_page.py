from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .app_row import AppRow
from .snapshots_list_page import SnapshotsListPage
import os, subprocess

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

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    current_installation = ""
    current_remote = None

    def start_loading(self):
        pass

    def end_loading(self):
        for installation in HostInfo.installations:
            for remote in HostInfo.remotes[installation]:
                if remote.disabled:
                    continue
                row = Adw.ActionRow(title=remote.title, subtitle=_("Installation: {}").format(installation), activatable=True)
                row.add_suffix(Gtk.Image(icon_name="right-large-symbolic"))
                row.connect("activated", self.remote_selected, installation, remote)
                self.remotes_group.add(row)

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
                for line in output:
                    info = line.split("\t")
                    if len(info) != 6:
                        continue
                    
                    name = GLib.markup_escape_text(info[0])
                    description = GLib.markup_escape_text(info[1])
                    app_id = GLib.markup_escape_text(info[2])
                    version = GLib.markup_escape_text(info[3])
                    branch = GLib.markup_escape_text(info[4])
                    remotes = GLib.markup_escape_text(info[5])
                    row = Adw.ActionRow(title=name, subtitle=app_id)

                    self.results_list.append(row)
                    
            except Exception as e:
                print(e)
            except subprocess.CalledProcessError as cpe:
                print(cpe)

        thread()

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.instance = self
        self.back_button.connect("clicked", lambda *_: self.sb_page_view.pop())
        # self.search_entry.connect("search-changed", self.on_search)
        self.search_entry.connect("activate", self.on_search)
        self.search_apply_button.connect("clicked", self.on_search)