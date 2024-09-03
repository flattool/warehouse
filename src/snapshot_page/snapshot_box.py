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
    rename_menu = gtc()
    rename_entry = gtc()
    apply_rename = gtc()
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

    def update_json(self, key, value):
        try:
            with open(self.json_path, 'r+') as file:
                data = json.load(file)
                data[key] = value
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()

        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not write data"), str(e)).toast)

    def load_from_json(self):
        if not os.path.exists(self.json_path):
            self.create_json()
        
        try:
            with open(self.json_path, 'r') as file:
                data = json.load(file)
                name = data['name']
                if name != "":
                    self.title.set_label(GLib.markup_escape_text(name))
                
        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not write data"), str(e)).toast)

    def on_rename(self, widget):
        self.update_json('name', self.rename_entry.get_text().strip())
        self.load_from_json()
        self.rename_menu.popdown()
            
    def __init__(self, folder, snapshots_path, toast_overlay, **kwargs):
        super().__init__(**kwargs)

        self.toast_overlay = toast_overlay

        split_folder = folder.split('_')
        if len(split_folder) < 2:
            return

        date_data = GLib.DateTime.new_from_unix_local(int(split_folder[0])).format("%x %X")
        self.date.set_label(date_data)
        self.version.set_label(_("Version: {}").format(split_folder[1].replace(".tar.zst", "")))
        self.json_path = f"{snapshots_path}{folder.replace('tar.zst', 'json')}"
        self.load_from_json()
        self.apply_rename.connect("clicked", self.on_rename)
        self.rename_entry.connect("activate", self.on_rename)
