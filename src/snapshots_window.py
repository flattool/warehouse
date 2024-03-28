from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib
import time


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/../data/ui/snapshots.ui")
class SnapshotsWindow(Adw.Dialog):
    __gtype_name__ = "SnapshotsWindow"

    new_env = dict(os.environ)
    new_env["LC_ALL"] = "C"
    host_home = str(pathlib.Path.home())
    user_data_path = host_home + "/.var/app/"
    snapshots_path = (
        host_home + "/.var/app/io.github.flattool.Warehouse/data/Snapshots/"
    )

    snapshots_group = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    no_snapshots = Gtk.Template.Child()
    new_snapshot = Gtk.Template.Child()
    open_folder_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    outerbox = Gtk.Template.Child()
    loading = Gtk.Template.Child()
    loading_label = Gtk.Template.Child()
    action_bar = Gtk.Template.Child()

    def show_list_or_empty(self):
        # Make window able to close
        self.set_can_close(True)

        self.action_bar.set_revealed(True)
        if os.path.exists(self.snapshots_of_app_path):
            if len(os.listdir(self.snapshots_of_app_path)) > 0:
                self.main_stack.set_visible_child(self.outerbox)
                return "list"
        self.open_folder_button.set_sensitive(False)
        self.main_stack.set_visible_child(self.no_snapshots)
        return "empty"

    def generate_list(self):
        if not os.path.exists(self.app_user_data):
            self.new_snapshot.set_sensitive(False)
            self.new_snapshot.set_tooltip_text(_("There is no User Data to Snapshot"))

        if self.show_list_or_empty() == "empty":
            return

        snapshot_files = os.listdir(self.snapshots_of_app_path)
        to_trash = []

        for i in range(len(snapshot_files)):
            if not snapshot_files[i].endswith(".tar.zst"):
                # Find all files that aren't snapshots
                to_trash.append(snapshot_files[i])

        for i in range(len(to_trash)):
            # Trash all files that aren't snapshots
            a = self.my_utils.trash_folder(f"{self.snapshots_of_app_path}{to_trash[i]}")
            if a == 0:
                snapshot_files.remove(to_trash[i])

        if len(snapshot_files) == 0:
            self.main_stack.set_visible_child(self.no_snapshots)
            return

        for i in range(len(snapshot_files)):
            self.create_row(snapshot_files[i])

    def create_row(self, file):
        def size_thread(*args):
            size = self.my_utils.get_size_with_format(self.snapshots_of_app_path + file)
            GLib.idle_add(lambda *_a: row.set_subtitle(f"~{size}"))

        split_file = file.removesuffix(".tar.zst").split("_")
        time = GLib.DateTime.new_from_unix_local(int(split_file[0])).format("%x %X")
        row = Adw.ActionRow(title=time)

        task = Gio.Task()
        task.run_in_thread(size_thread)

        label = Gtk.Label(
            label=_("Version {}").format(split_file[1]),
            hexpand=True,
            wrap=True,
            justify=Gtk.Justification.RIGHT,
        )
        row.add_suffix(label)

        apply = Gtk.Button(icon_name="check-plain-symbolic", valign=Gtk.Align.CENTER)
        apply.set_tooltip_text(_("Apply Snapshot"))
        apply.connect("clicked", self.apply_snapshot, file, row)
        apply.add_css_class("flat")
        row.add_suffix(apply)

        trash = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER)
        trash.set_tooltip_text(_("Trash Snapshot"))
        trash.connect("clicked", self.trash_snapshot, file, row)
        trash.add_css_class("flat")
        row.add_suffix(trash)
        self.snapshots_group.insert(row, 0)
        self.main_stack.set_visible_child(self.outerbox)
        self.open_folder_button.set_sensitive(True)

    def trash_snapshot(self, button, file, row):
        def on_response(dialog, response, func):
            if response == "cancel":
                return
            a = self.my_utils.trash_folder(self.snapshots_of_app_path + file)
            if a == 0:
                self.snapshots_group.remove(row)
                if not self.snapshots_group.get_row_at_index(0):
                    self.my_utils.trash_folder(self.snapshots_of_app_path)
                    self.show_list_or_empty()
            else:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("Could not trash snapshot"))
                )

        dialog = Adw.AlertDialog.new(
            _("Trash Snapshot?"),
            _("This snapshot and its contents will be sent to the trash."),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.set_close_response("cancel")
        dialog.add_response("continue", _("Trash Snapshot"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response, dialog.choose_finish)
        dialog.present(self)

    def create_snapshot(self):
        epoch = int(time.time())

        def thread():
            response = self.my_utils.snapshot_apps(
                epoch,
                [self.snapshots_of_app_path],
                [self.app_version],
                [self.app_user_data],
            )
            if response != 0:
                GLib.idle_add(
                    self.toast_overlay.add_toast(
                        Adw.Toast.new(_("Could not create snapshot"))
                    )
                )
                return
            if self.show_list_or_empty() == "list":
                self.create_row(f"{epoch}_{self.app_version}.tar.zst")

        # Make window unable to close
        self.set_can_close(False)
        self.loading_label.set_label(_("Creating Snapshot…"))
        self.action_bar.set_revealed(False)
        self.main_stack.set_visible_child(self.loading)

        task = Gio.Task()
        task.run_in_thread(lambda *_: thread())

    def apply_snapshot(self, button, file, row):
        self.applied = False

        def thread():
            try:
                subprocess.run(
                    [
                        "tar",
                        "--zstd",
                        "-xvf",
                        f"{self.snapshots_of_app_path}{file}",
                        "-C",
                        f"{self.app_user_data}",
                    ],
                    check=True,
                    env=self.new_env,
                )
                self.applied = True
            except subprocess.CalledProcessError as e:
                print(
                    "error in snapshots_window.apply_snapshot.thread: CalledProcessError:",
                    e,
                )

        def callback():
            if not self.applied:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("Could not apply snapshot"))
                )
            else:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Snapshot applied")))

            self.new_snapshot.set_tooltip_text("")
            self.show_list_or_empty()

        def on_response(dialog, response, func):
            if response == "cancel":
                return
            to_apply = self.snapshots_of_app_path + file
            to_trash = self.app_user_data
            if os.path.exists(to_trash):
                a = self.my_utils.trash_folder(to_trash)
                if a != 0:
                    self.toast_overlay.add_toast(
                        Adw.Toast.new(_("Could not apply snapshot"))
                    )
                    return
            data = Gio.File.new_for_path(self.app_user_data)
            data.make_directory()
            if not os.path.exists(data.get_path()):
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("Could not apply snapshot"))
                )
                return

            # Make window unable to close
            self.set_can_close(False)
            self.loading_label.set_label(_("Applying Snapshot…"))
            self.action_bar.set_revealed(False)
            self.main_stack.set_visible_child(self.loading)

            task = Gio.Task.new(None, None, lambda *_: callback())
            task.run_in_thread(lambda *_: thread())

        dialog = Adw.AlertDialog.new(
            _("Apply Snapshot?"),
            _("Applying this snapshot will trash any current user data for {}.").format(
                self.app_name
            ),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.set_close_response("cancel")
        dialog.add_response("continue", _("Apply Snapshot"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response, dialog.choose_finish)
        dialog.present(self)

    def open_button_handler(self, widget, path):
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{path}", None)
        except GLib.GError:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not open folder")))

    def __init__(self, parent_window, flatpak_row, **kwargs):
        super().__init__(**kwargs)

        # Variables
        self.my_utils = myUtils(self)
        self.app_name = flatpak_row[0]
        self.app_id = flatpak_row[2]
        self.app_version = flatpak_row[3]
        self.app_ref = flatpak_row[8]
        self.snapshots_of_app_path = self.snapshots_path + self.app_id + "/"
        self.app_user_data = self.user_data_path + self.app_id + "/"
        self.parent_window = parent_window

        if (
            self.app_version == ""
            or self.app_version == "-"
            or self.app_version == None
        ):
            self.app_version = 0.0

        if not os.path.exists(self.snapshots_path):
            # Create snapshots folder if none exists
            file = Gio.File.new_for_path(self.snapshots_path)
            file.make_directory()

        # Calls
        self.generate_list()
        self.open_folder_button.connect(
            "clicked", self.open_button_handler, self.snapshots_of_app_path
        )
        self.new_snapshot.connect("clicked", lambda *_: self.create_snapshot())

        # Window stuffs
        self.set_title(_("{} Snapshots").format(self.app_name))
        self.present(parent_window)
