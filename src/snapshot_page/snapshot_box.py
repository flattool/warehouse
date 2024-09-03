from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
import os, json

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/snapshot_box.ui")
class SnapshotBox(Gtk.Box):
    __gtype_name__ = "SnapshotBox"
    gtc = Gtk.Template.Child

    title = gtc()
    date = gtc()
    version = gtc()
    apply_button = gtc()
    rename_button = gtc()
    trash_button = gtc()

    def create_json(self):
        try:
            data = {
                'snapshot_version': 1,
                'name': '',
            }
            with open(self.json_path, 'w') as file:
                json.dump(data, file, indent=4)
                return None
        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not write data"), str(e)).toast)

    def update_json(self):
        try:
            with open(self.json_path, 'r+') as file:
                data = json.load(file)
                data['name'] = "updated"
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()

        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not write data"), str(e)).toast)

    def json_handler(self, *args):
        if not os.path.exists(self.json_path):
            self.create_json()

        self.update_json()

    def __init__(self, folder, snapshots_path, toast_overlay, **kwargs):
        super().__init__(**kwargs)

        self.toast_overlay = toast_overlay

        split_folder = folder.split('_')
        if len(split_folder) < 2:
            return

        date_data = GLib.DateTime.new_from_unix_local(int(split_folder[0])).format("%x %X")
        self.date.set_label(date_data)
        self.version.set_label(split_folder[1].replace(".tar.zst", ""))
        
        self.json_path = f"{snapshots_path}{folder.replace('tar.zst', 'json')}"
        
        self.rename_button.connect("clicked", self.json_handler)
        