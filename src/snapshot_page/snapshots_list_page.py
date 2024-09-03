from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .snapshot_box import SnapshotBox
import os


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/snapshots_list_page.ui")
class SnapshotsListPage(Adw.NavigationPage):
    __gtype_name__ = "SnapshotsListPage"
    gtc = Gtk.Template.Child

    listbox = gtc()
    toast_overlay = gtc()

    snapshots_path = f"{HostInfo.home}/.var/app/io.github.flattool.Warehouse/data/Snapshots/"

    def thread(self, *args):
        for snapshot in os.listdir(folder := f"{self.snapshots_path}{self.current_folder}/"):
            if snapshot.endswith(".json"):
                continue
            
            row = SnapshotBox(snapshot, folder, self.toast_overlay)
            self.snapshots_rows.append(row)

    def callback(self, *args):
        for i, row in enumerate(self.snapshots_rows):
            self.listbox.append(row)
            self.listbox.get_row_at_index(i).set_activatable(False)

    def set_snapshots(self, folder, title):
        if self.current_folder == folder:
            return
            
        self.current_folder = folder
        self.set_title(_("{} Snapshots").format(title))
        self.snapshots_rows.clear()
        self.listbox.remove_all()

        Gio.Task.new(None, None, self.callback).run_in_thread(self.thread)

    def __init__(self, parent_page, **kwargs):
        super().__init__(**kwargs)

        self.current_folder = None
        self.snapshots_rows = []
