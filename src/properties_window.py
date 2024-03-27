from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/../data/ui/properties.ui")
class PropertiesWindow(Adw.Dialog):
    __gtype_name__ = "PropertiesWindow"

    new_env = dict(os.environ)
    new_env["LC_ALL"] = "C"
    host_home = str(pathlib.Path.home())
    user_data_path = host_home + "/.var/app/"

    toast_overlay = Gtk.Template.Child()
    upper = Gtk.Template.Child()
    app_icon = Gtk.Template.Child()
    data_row = Gtk.Template.Child()
    open_data = Gtk.Template.Child()
    trash_data = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    details = Gtk.Template.Child()
    view_apps = Gtk.Template.Child()
    runtime = Gtk.Template.Child()
    runtime_properties = Gtk.Template.Child()
    runtime_copy = Gtk.Template.Child()
    lower = Gtk.Template.Child()
    eol_app_banner = Gtk.Template.Child()
    eol_runtime_banner = Gtk.Template.Child()
    mask_banner = Gtk.Template.Child()

    def key_handler(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape or (
            keyval == Gdk.KEY_w and state == Gdk.ModifierType.CONTROL_MASK
        ):
            self.close()

    def copy_item(self, to_copy, to_toast=None):
        self.get_clipboard().set(to_copy)
        if to_toast:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Copied {}").format(to_toast)))

    def open_button_handler(self, widget):
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{self.user_data_path}", None)
        except GLib.GError:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not open folder")))

    def show_details(self, widget):
        try:
            Gio.AppInfo.launch_default_for_uri(f"appstream://{self.app_id}", None)
        except GLib.GError:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not show details")))

    def get_size_callback(self, *args):
        self.open_data.set_visible(True)
        self.open_data.connect("clicked", self.open_button_handler)
        self.trash_data.set_visible(True)
        self.data_row.set_title(_("User Data"))
        self.data_row.set_subtitle(f"~{self.size}")
        self.spinner.set_visible(False)

    def get_size_thread(self, *args):
        self.size = self.my_utils.get_size_with_format(self.user_data_path)

    def generate_upper(self):
        image = self.my_utils.find_app_icon(self.app_id)
        self.runtime.set_subtitle(self.current_flatpak[13])
        if image.get_paintable() == None:
            self.app_icon.set_from_icon_name(image.get_icon_name())
        else:
            self.app_icon.set_from_paintable(image.get_paintable())

        if os.path.exists(self.user_data_path):
            task = Gio.Task.new(None, None, self.get_size_callback)
            task.run_in_thread(self.get_size_thread)
        else:
            self.data_row.set_title("")
            self.data_row.set_subtitle(_("No User Data"))
            self.spinner.set_visible(False)

        if "runtime" in self.current_flatpak[12]:
            # Pak is a runtime
            self.runtime.set_visible(False)
            if self.app_ref in self.parent_window.dependent_runtimes:
                self.view_apps.set_visible(True)

    def generate_lower(self):
        column_headers = [
            _("Name"),
            _("Description"),
            _("App ID"),
            _("Version"),
            _("Branch"),
            _("Arch"),
            _("Origin"),
            _("Installation"),
            _("Ref"),
            _("Active Commit"),
            _("Latest Commit"),
            _("Installed Size"),
            _("Options"),
        ]

        for i in range(len(column_headers)):
            if self.current_flatpak[i] == "":
                continue

            row = Adw.ActionRow(
                title=column_headers[i], tooltip_text=_("Copy"), activatable=True
            )
            row.add_suffix(Gtk.Image.new_from_icon_name("edit-copy-symbolic"))
            row.set_subtitle(GLib.markup_escape_text(self.current_flatpak[i]))
            row.add_css_class("property")
            row.connect(
                "activated",
                lambda *_a, row=row: self.copy_item(
                    row.get_subtitle(), row.get_title()
                ),
            )
            self.lower.add(row)

    def view_apps_handler(self, widget):
        settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        for key in settings.list_keys():
            settings.reset(key)
        settings.set_string("runtimes-list", f"{self.app_ref},")
        self.parent_window.apply_filter()
        self.close()

    def show_properties_handler(self):
        runtime = self.current_flatpak[13]
        for i in range(len(self.host_flatpaks)):
            # open the properties when the flatpak matches the runtime *and* installation type
            if runtime in self.host_flatpaks[i][8] and self.install_type in self.host_flatpaks[i][12]:
                PropertiesWindow(i, self.host_flatpaks, self.parent_window)
                self.close()
                return
        self.toast_overlay.add_toast(Adw.Toast.new(_("Could not show properties")))

    def trash_data_handler(self):
        def on_response(_none, response, widget):
            if response == "cancel":
                return

            if self.my_utils.trash_folder(self.user_data_path) == 0:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Trashed user data")))
                self.data_row.set_title(_("No User Data"))
                self.data_row.set_subtitle("")
                self.open_data.set_visible(False)
                self.trash_data.set_visible(False)
            else:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("Could not trash user data"))
                )

        dialog = Adw.MessageDialog.new(
            self, _("Send {}'s User Data to the Trash?").format(self.app_name)
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.set_close_response("cancel")
        dialog.add_response("continue", _("Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response, dialog.choose_finish)
        dialog.present()

    def __init__(self, flatpak_index, host_flatpaks, parent_window, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(self)
        self.current_flatpak = host_flatpaks[flatpak_index]
        self.parent_window = parent_window
        self.host_flatpaks = host_flatpaks
        self.flatpak_index = flatpak_index

        self.app_name = self.current_flatpak[0]
        self.app_id = self.current_flatpak[2]
        self.origin_remote = self.current_flatpak[6]
        self.install_type = self.current_flatpak[7]
        self.app_ref = self.current_flatpak[8]
        self.user_data_path += self.app_id

        self.details.connect("activated", self.show_details)
        self.runtime_copy.connect(
            "clicked",
            lambda *_: self.copy_item(
                self.runtime.get_subtitle(), self.runtime.get_title()
            ),
        )
        self.runtime_properties.connect(
            "clicked", lambda *_: self.show_properties_handler()
        )
        self.view_apps.connect("activated", self.view_apps_handler)
        self.trash_data.connect("clicked", lambda *_: self.trash_data_handler())

        if "eol" in self.current_flatpak[12]:
            self.eol_app_banner.set_revealed(True)
            self.eol_app_banner.set_title(
                _(
                    "{} has reached its End of Life and will not receive any security updates"
                ).format(self.app_name)
            )

        if self.current_flatpak[13] in parent_window.eol_list:
            self.eol_runtime_banner.set_revealed(True)
            self.eol_runtime_banner.set_title(
                _(
                    "{}'s runtime has reached its End of Life and will not receive any security updates"
                ).format(self.app_name)
            )

        if self.app_id in self.my_utils.get_host_masks(
            "system"
        ) or self.app_id in self.my_utils.get_host_masks("user"):
            self.mask_banner.set_revealed(True)
            self.mask_banner.set_title(
                _("{} is masked and will not be updated").format(self.app_name)
            )

        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)

        self.generate_upper()
        self.generate_lower()

        self.set_title(_("{} Properties").format(self.app_name))
        self.present(parent_window)
