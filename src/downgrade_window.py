from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/../data/ui/downgrade.ui")
class DowngradeWindow(Adw.Dialog):
    __gtype_name__ = "DowngradeWindow"

    new_env = dict(os.environ)
    new_env["LC_ALL"] = "C"

    apply_button = Gtk.Template.Child()
    versions_group = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    mask_row = Gtk.Template.Child()
    main_toolbar_view = Gtk.Template.Child()
    loading = Gtk.Template.Child()
    loading_label = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    outerbox = Gtk.Template.Child()

    def key_handler(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape or (
            keyval == Gdk.KEY_w and state == Gdk.ModifierType.CONTROL_MASK
        ):
            self.close()

    def selection_handler(self, button, index):
        self.apply_button.set_sensitive(True)
        if button.get_active():
            self.commit_to_use = self.versions[index][0]

    def get_commits(self):
        output = subprocess.run(
            [
                "flatpak-spawn", "--host", "sh", "-c",
                f"LC_ALL=C flatpak remote-info --log {self.remote} {self.app_ref} --{self.install_type}"
            ],
            capture_output=True,
            text=True
        ).stdout
        print(output)
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row[0].strip())

        commits = []
        changes = []
        dates = []
        for i in range(len(data)):
            line = data[i]

            if "Commit:" in line:
                commits.append(line.replace("Commit: ", ""))

            if "Subject:" in line:
                changes.append(line.replace("Subject: ", ""))

            if "Date:" in line:
                dates.append(line.replace("Date: ", ""))

        for i in range(len(commits)):
            self.versions.append([commits[i], changes[i], dates[i]])

    def commits_callback(self):
        group_button = Gtk.CheckButton(visible=False)
        self.versions_group.add(group_button)
        for i in range(len(self.versions)):
            version = self.versions[i]
            date_time = version[2].split(" ")
            date = date_time[0].split("-")
            offset = date_time[2][:3] + ":" + date_time[2][3:]
            time = date_time[1].split(":")
            display_time = GLib.DateTime.new(
                GLib.TimeZone.new(offset),
                int(date[0]),
                int(date[1]),
                int(date[2]),
                int(time[0]),
                int(time[1]),
                int(time[2]),
            )
            display_time = display_time.format("%x %X")
            change = version[1].split("(")
            row = Adw.ActionRow(
                title=GLib.markup_escape_text(change[0]), subtitle=str(display_time)
            )
            row.set_tooltip_text(_("Commit Hash: {}").format(version[0]))
            select = Gtk.CheckButton()
            select.connect("toggled", self.selection_handler, i)
            select.set_group(group_button)

            version.append(select)
            row.set_activatable_widget(select)
            row.add_prefix(select)
            self.versions_group.add(row)
        self.main_stack.set_visible_child(self.outerbox)
        self.apply_button.set_visible(True)

    def generate_list(self):
        task = Gio.Task.new(None, None, lambda *_: self.commits_callback())
        task.run_in_thread(lambda *_: self.get_commits())

    def downgrade_callack(self):
        self.set_can_close(True)

        if self.response != 0:
            self.toast_overlay.add_toast(
                Adw.Toast.new(_("Could not downgrade {}").format(self.app_name))
            )
            self.apply_button.set_sensitive(True)
            return

        if self.mask_row.get_active():
            if self.my_utils.mask_flatpak(self.app_id, self.install_type) != 0:
                self.parent_window.toast_overlay.add_toast(
                    Adw.Toast.new(
                        _("Could not disable updates for {}").format(self.app_name)
                    )
                )

        self.parent_window.refresh_list_of_flatpaks(self, False)
        print(self.response)
        self.close()

    def downgrade_thread(self):
        self.response = self.my_utils.downgrade_flatpak(
            self.app_ref, self.commit_to_use, self.install_type
        )

    def on_apply(self):
        self.loading_label.set_label(_("Downgrading…"))
        self.set_can_close(False)
        self.main_stack.set_visible_child(self.loading)
        self.apply_button.set_visible(False)

        task = Gio.Task.new(None, None, lambda *_: self.downgrade_callack())
        task.run_in_thread(lambda *_: self.downgrade_thread())

    def __init__(self, parent_window, flatpak_row, index, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.app_name = flatpak_row[0]
        self.app_id = flatpak_row[2]
        self.remote = flatpak_row[6]
        self.install_type = flatpak_row[7]
        self.app_ref = flatpak_row[8]
        self.versions = []
        self.commit_to_use = ""
        self.parent_window = parent_window
        self.flatpak_row = flatpak_row
        self.response = 0
        self.window_title = _("Downgrade {}").format(self.app_name)
        self.index = index
        event_controller = Gtk.EventControllerKey()

        # Connections
        event_controller.connect("key-pressed", self.key_handler)
        self.apply_button.connect("clicked", lambda *_: self.on_apply())

        # Apply
        self.add_controller(event_controller)
        self.mask_row.set_subtitle(
            _("Ensure that {} will never be updated to a newer version").format(
                self.app_name
            )
        )

        self.set_title(self.window_title)

        self.generate_list()

        self.present(parent_window)
