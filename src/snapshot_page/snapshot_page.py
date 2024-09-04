from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .app_row import AppRow
from .snapshots_list_page import SnapshotsListPage
from .sidebar_button import SidebarButton
from .loading_status import LoadingStatus
import os, subprocess

class LeftoverSnapshotRow(Adw.ActionRow):
    __gtype_name__ = "LeftoverSnapshotRow"

    def idle_stuff(self):
        self.set_title(self.folder.split('.')[-1])
        icon = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        icon.set_icon_size(Gtk.IconSize.LARGE)
        self.add_prefix(icon)
        self.add_suffix(self.check_button)

    def __init__(self, folder, **kwargs):
        super().__init__(**kwargs)
        
        self.set_activatable(True)
        self.folder = folder
        self.check_button = Gtk.CheckButton(visible=False)
        self.check_button.add_css_class("selection-mode")
        GLib.idle_add(lambda *_: self.idle_stuff())

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/snapshot_page.ui")
class SnapshotPage(Adw.BreakpointBin):
    __gtype_name__ = "SnapshotPage"
    gtc = Gtk.Template.Child

    toast_overlay = gtc()
    active_box = gtc()
    active_listbox = gtc()
    leftover_box = gtc()
    leftover_listbox = gtc()
    split_view = gtc()
    stack = gtc()
    no_snapshots = gtc()
    no_results = gtc()
    scrolled_window = gtc()
    open_button = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None
    page_name = "snapshots"
    
    snapshots_path = f"{HostInfo.home}/.var/app/io.github.flattool.Warehouse/data/Snapshots/"

    def sort_snapshots(self, *args):
        self.active_snapshot_paks.clear()
        self.leftover_snapshots.clear()
        bad_folders = []

        if not os.path.exists(self.snapshots_path):
            try:
                os.makedirs(self.snapshots_path)
            except Exception as e:
                self.toast_overlay.add_toast(ErrorToast(_("Could not load Snapshots"), str(e)).toast)
                return
        
        for folder in os.listdir(self.snapshots_path):
            if folder.count('.') < 2 or ' ' in folder:
                bad_folders.append(folder)
                continue
            
            has_tar = False
            for file in os.listdir(f"{self.snapshots_path}{folder}"):
                if file.endswith(".tar.zst"):
                    has_tar = True
                    break
            
            if not has_tar:
                bad_folders.append(folder)
                continue

            try:
                pak = HostInfo.id_to_flatpak[folder]
                self.active_snapshot_paks.append(pak)
            except KeyError:
                self.leftover_snapshots.append(folder)

        for folder in bad_folders:
            try:
                subprocess.run(['gio', 'trash', f'{self.snapshots_path}{folder}'])
            except Exception:
                pass

    def generate_active_list(self):
        for pak in self.active_snapshot_paks:
            row = AppRow(pak)
            self.active_listbox.append(row)
            
        if len(self.active_snapshot_paks) > 0:
            self.active_box.set_visible(True)
            first_row = self.active_listbox.get_row_at_index(0)
            self.active_listbox.select_row(first_row)
        else:
            self.active_box.set_visible(False)

    def generate_leftover_list(self):
        for folder in self.leftover_snapshots:
            row = LeftoverSnapshotRow(folder)
            self.leftover_listbox.append(row)            

        if len(self.leftover_snapshots) > 0:
            self.leftover_box.set_visible(True)
            if len(self.active_snapshot_paks) == 0:
                self.stack.set_visible_child(self.scrolled_window)
                first_row = self.leftover_listbox.get_row_at_index(0)
                self.leftover_listbox.select_row(first_row)
        else:
            self.leftover_box.set_visible(False)

    def active_select_handler(self, listbox, row):
        self.leftover_listbox.select_row(None)
        self.list_page.set_snapshots(row.package.info["id"], row.get_title())

    def leftover_select_handler(self, listbox, row):
        self.active_listbox.select_row(None)
        self.list_page.set_snapshots(row.folder, row.get_title())

    def start_loading(self):
        self.active_box.set_visible(True)
        self.active_listbox.remove_all()
        self.leftover_box.set_visible(True)
        self.leftover_listbox.remove_all()
        self.stack.set_visible_child(self.loading_snapshots)

    def end_loading(self):
        def callback(*args):
            self.generate_active_list()
            self.generate_leftover_list()
            if (not self.active_box.get_visible()) and (not self.leftover_box.get_visible()):
                GLib.idle_add(lambda *_: self.stack.set_visible_child(self.no_snapshots))
            else:
                GLib.idle_add(lambda *_: self.stack.set_visible_child(self.scrolled_window))

        Gio.Task.new(None, None, callback).run_in_thread(self.sort_snapshots)

    def open_snapshots_folder(self, button):
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{self.snapshots_path}", None)
            self.toast_overlay.add_toast(Adw.Toast.new(_("Opened snapshots folder")))
        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not open folder"), str(e)).toast)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.__class__.instance = self
        self.main_window = main_window
        self.loading_snapshots = LoadingStatus(_("Loading Snapshots"), _("This should only take a moment"))
        self.active_snapshot_paks = []
        # self.active_rows = []
        self.leftover_snapshots = []
        # self.leftover_rows = []
        self.list_page = SnapshotsListPage(self)

        # Connections
        self.active_listbox.connect("row-activated", self.active_select_handler)
        self.leftover_listbox.connect("row-activated", self.leftover_select_handler)
        self.open_button.connect("clicked", self.open_snapshots_folder)

        # Apply
        self.stack.add_child(self.loading_snapshots)
        self.split_view.set_content(self.list_page)
