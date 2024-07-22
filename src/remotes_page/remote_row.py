from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo
from .error_toast import ErrorToast
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/remote_row.ui")
class RemoteRow(Adw.ActionRow):
    __gtype_name__ = 'RemoteRow'
    gtc = Gtk.Template.Child

    suffix_label = gtc()
    filter_button = gtc()
    menu_pop = gtc()
    menu_listbox = gtc()

    copy_title = gtc()
    copy_name = gtc()
    enable_remote = gtc()
    disable_remote = gtc()
    remove = gtc()

    def enable_remote_handler(self, *args):
        def idle_stuff(*args):
            self.remove_css_class("warning")
            self.set_subtitle(_("Installation: {}").format(self.installation))
            self.remote.disabled = False
            self.parent_page.toast_overlay.add_toast(Adw.Toast(title=_("Enabled remote")))
            self.menu_listbox.get_row_at_index(2).set_visible(False)
            self.menu_listbox.get_row_at_index(3).set_visible(True)

        if not self.remote.disabled:
            self.parent_page.toast_overlay.add_toast(ErrorToast(_("Could not enable remote"), _("Remote is already enabled")).toast)
            return

        cmd = ['flatpak-spawn', '--host', 'flatpak', 'remote-modify', '--enable', self.remote.name]
        if self.installation == "user" or self.installation == "system":
            cmd.append(f"--{self.installation}")
        else:
            cmd.append(f"--installation={self.installation}")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as cpe:
            GLib.idle_add(lambda *args, cpe=cpe: self.parent_page.toast_overlay.add_toast(ErrorToast(_("Could not enable remote"), str(cpe.stderr)).toast))
            return
        except Exception as e:
            GLib.idle_add(lambda *args, e=e: self.parent_page.toast_overlay.add_toast(ErrorToast(_("Could not enable remote"), str(e)).toast))
            return

        idle_stuff()

    def disable_remote_handler(self, *args):
        def callback(*args):
            self.add_css_class("warning")
            self.set_subtitle(_("Disabled"))
            self.remote.disabled = True
            self.parent_page.toast_overlay.add_toast(Adw.Toast(title=_("Disabled remote")))
            self.menu_listbox.get_row_at_index(2).set_visible(True)
            self.menu_listbox.get_row_at_index(3).set_visible(False)

        def thread():
            if self.remote.disabled:
                self.parent_page.toast_overlay.add_toast(ErrorToast(_("Could not disable remote"), _("Remote is already disabled")).toast)
                return

            cmd = ['flatpak-spawn', '--host', 'flatpak', 'remote-modify', '--disable', self.remote.name]
            if self.installation == "user" or self.installation == "system":
                cmd.append(f"--{self.installation}")
            else:
                cmd.append(f"--installation={self.installation}")

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as cpe:
                GLib.idle_add(lambda *args, cpe=cpe: self.parent_page.toast_overlay.add_toast(ErrorToast(_("Could not disable remote"), str(cpe.stderr)).toast))
                return
            except Exception as e:
                GLib.idle_add(lambda *args, e=e: self.parent_page.toast_overlay.add_toast(ErrorToast(_("Could not disable remote"), str(e)).toast))
                return

        def on_response(_, response):
            if response != "continue":
                return
                
            Gio.Task.new(None, None, callback).run_in_thread(thread)

        dialog = Adw.AlertDialog(heading=_("Disable {}?").format(self.remote.title), body=_("Any installed apps from {} will stop receiving updates").format(self.remote.name))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Remove"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response)
        dialog.present(self.parent_page.main_window)

    def on_menu_action(self, listbox, row):
        row = row.get_child()
        match row:
            case self.copy_title:
                HostInfo.clipboard.set(self.get_title())
                self.parent_page.toast_overlay.add_toast(Adw.Toast(title=_("Copied title")))
            case self.copy_name:
                HostInfo.clipboard.set(self.get_subtitle())
                self.parent_page.toast_overlay.add_toast(Adw.Toast(title=_("Copied name")))
            case self.enable_remote:
                Gio.Task().run_in_thread(self.enable_remote_handler)
            case self.disable_remote:
                self.disable_remote_handler()
            case self.remove:
                self.parent_page.remove_remote(self)

        self.menu_pop.popdown()

    def idle_stuff(self):
        self.set_title(self.remote.title)
        if self.remote.disabled:
            self.set_subtitle(_("Disabled"))
            self.add_css_class("warning")
        else:
            self.set_subtitle(_("Installation: {}").format(self.installation))
        self.suffix_label.set_label(self.remote.name)

    def __init__(self, parent_page, installation, remote, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.parent_page = parent_page
        self.remote = remote
        self.installation = installation

        # Apply
        GLib.idle_add(lambda *_: self.idle_stuff())

        ## Show / Hide the Enable / Disable actions depending on remote status
        self.menu_listbox.get_row_at_index(2).set_visible(remote.disabled)
        self.menu_listbox.get_row_at_index(3).set_visible(not remote.disabled)

        # Connections
        self.menu_listbox.connect("row-activated", self.on_menu_action)
        self.filter_button.connect("clicked", lambda *_: parent_page.filter_remote(self))