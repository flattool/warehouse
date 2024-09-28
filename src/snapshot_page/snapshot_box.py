from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .tar_worker import TarWorker
import os, subprocess, json, re

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
                else:
                    self.title.set_label(_("No Name Set"))
                
        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not write data"), str(e)).toast)

    def on_rename(self, widget):
        if not self.valid_checker():
            return

        self.update_json('name', self.rename_entry.get_text().strip())
        self.load_from_json()
        self.rename_menu.popdown()

    def valid_checker(self, *args):
        text = self.rename_entry.get_text().strip()
        valid = not ("/" in text or "\0" in text) and len(text) > 0
        self.apply_rename.set_sensitive(valid)
        if valid:
            self.rename_entry.remove_css_class("error")
        else:
            self.rename_entry.add_css_class("error")
            
        return valid

    def on_trash(self, button):
        error = [None]
        path = f"{self.snapshots_path}{self.folder}"
        def thread(*args):
            try:
                subprocess.run(['gio', 'trash', path], capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as cpe:
                error[0] = cpe.stderr
            except Exception as e:
                error[0] = str(e)

        def callback(*args):
            if not error[0] is None:
                self.toast_overlay.add_toast(ErrorToast(_("Could not trash snapshot"), error[0]).toast)
                return

            self.parent_page.on_trash()
            self.toast_overlay.add_toast(Adw.Toast.new(_("Trashed snapshot")))

        def on_response(_, response):
            if response != "continue":
                return

            Gio.Task.new(None, None, callback).run_in_thread(thread)

        dialog = Adw.AlertDialog(heading=_("Trash Snapshot?"), body=_("This snapshot will be moved to the trash"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Trash"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response)
        dialog.present(HostInfo.main_window)
        
    def get_fraction(self):
        loading_status = self.snapshot_page.snapshotting_status
        loading_status.progress_bar.set_fraction(self.worker.fraction)
        if self.worker.stop:
            self.snapshot_page.status_stack.set_visible_child(self.snapshot_page.split_view)
            self.parent_page.set_snapshots(self.parent_page.package_or_folder, True)
            return False # Stop the timeout
        else:
            return True # Continue the timeout
        
    def on_apply(self, button):
        def on_response(dialog, response):
            if response != "continue":
                return
                
            self.snapshot_page.snapshotting_status.title_label.set_label(_("Applying Snapshot"))
            self.snapshot_page.snapshotting_status.progress_label.set_visible(False)
            self.snapshot_page.snapshotting_status.progress_bar.set_fraction(0.0)
            self.snapshot_page.status_stack.set_visible_child(self.snapshot_page.snapshotting_view)
            self.worker.extract()
            GLib.timeout_add(200, self.get_fraction)
        
        has_data = os.path.exists(self.worker.new_path)
        dialog = Adw.AlertDialog(
            heading=_("Apply Snapshot?"),
            body=_("Any current user data for this app will be trashed") if has_data else "",
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Apply"))
        dialog.connect("response", on_response)
        dialog.present(HostInfo.main_window)
        
    def __init__(self, parent_page, folder, snapshots_path, toast_overlay, **kwargs):
        super().__init__(**kwargs)

        self.snapshot_page = parent_page.parent_page
        self.toast_overlay = toast_overlay
        self.app_id = snapshots_path.split('/')[-2].strip()
        self.worker = TarWorker(
            existing_path=f"{snapshots_path}{folder}",
            new_path=f"{HostInfo.home}/.var/app/{self.app_id}/",
            file_name=self.app_id,
        )

        split_folder = folder.split('_')
        if len(split_folder) < 2:
            return

        self.parent_page = parent_page
        self.folder = folder
        self.snapshots_path = snapshots_path
        self.epoch = int(split_folder[0])
        date_data = GLib.DateTime.new_from_unix_local(self.epoch).format("%x %X")
        self.date.set_label(date_data)
        self.version.set_label(_("Version: {}").format(split_folder[1].replace(".tar.zst", "")))
        self.json_path = f"{snapshots_path}{folder.replace('tar.zst', 'json')}"
        self.load_from_json()
        self.apply_button.connect("clicked", self.on_apply)
        self.apply_rename.connect("clicked", self.on_rename)
        self.rename_entry.connect("activate", self.on_rename)
        self.rename_entry.connect("changed", self.valid_checker)
        self.trash_button.connect("clicked", self.on_trash)
