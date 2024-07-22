from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/add_remote_dialog.ui")
class AddRemoteDialog(Adw.Dialog):
    __gtype_name__ = "AddRemoteDialog"
    gtc = Gtk.Template.Child

    apply_button = gtc()
    title_row = gtc()
    name_row = gtc()
    url_row = gtc()
    installation_row = gtc()

    def on_apply(self, *args):
        self.close()
        self.parent_page.stack.set_visible_child(self.parent_page.loading_remotes)
        error = [None]
        def thread(*args):
            cmd = [
                'flatpak-spawn', '--host',
                'flatpak', 'remote-add', '--if-not-exists',
                f'--title={self.title_row.get_text()}',
                self.name_row.get_text(),
                self.url_row.get_text()
            ]
            installation = self.installation_row.get_selected_item().get_string()
            if installation == "user" or installation == "system":
                cmd.append(f"--{installation}")
            else:
                cmd.append(f"--installation={installation}")
            
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as cpe:
                error[0] = cpe.stderr
            except Exception as e:
                error[0] = e
        
        def callback(*args):
            if error[0]:
                self.parent_page.toast_overlay.add_toast(ErrorToast(_("Could not add remote"), str(error[0])))
            else:
                self.main_window.refresh_handler()
                self.parent_page.toast_overlay.add_toast(Adw.Toast(title=_("Added {}").format(self.name_row.get_text())))

        Gio.Task.new(None, None, callback).run_in_thread(thread)

    def __init__(self, main_window, parent_page, remote_info=None, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.string_list = Gtk.StringList(strings=HostInfo.installations)
        self.main_window = main_window
        self.parent_page = parent_page

        # Apply
        self.installation_row.set_model(self.string_list)
        if remote_info:
            self.title_row.set_text(remote_info["title"])
            self.title_row.set_editable(False)
            self.name_row.set_text(remote_info["name"])
            self.name_row.set_editable(False)
            self.url_row.set_text(remote_info["link"])
            self.url_row.set_editable(False)
            self.apply_button.set_sensitive(True)

        # Connections
        self.apply_button.connect("clicked", self.on_apply)