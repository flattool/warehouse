from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/../data/ui/filter.ui")
class FilterWindow(Adw.Window):
    __gtype_name__ = "FilterWindow"

    show_apps_switch = Gtk.Template.Child()
    show_runtimes_switch = Gtk.Template.Child()
    remotes_expander = Gtk.Template.Child()
    runtimes_expander = Gtk.Template.Child()
    reset_button = Gtk.Template.Child()

    def key_handler(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape or (
            keyval == Gdk.KEY_w and state == Gdk.ModifierType.CONTROL_MASK
        ):
            self.close()

    def gsettings_bool_set(self, key, value):
        self.settings.set_boolean(key, value)
        self.check_is_resetable()
        self.main_window.apply_filter()

    def check_is_resetable(self):
        if not self.show_apps_switch.get_active():
            self.reset_button.set_sensitive(True)
            return
        if self.show_runtimes_switch.get_active():
            self.reset_button.set_sensitive(True)
            return
        if self.total_remotes_selected != 0:
            self.reset_button.set_sensitive(True)
            return
        if self.total_runtimes_selected != 0:
            self.reset_button.set_sensitive(True)
            return
        self.reset_button.set_sensitive(False)

    def row_subtitle_updater(self):
        if self.total_runtimes_selected > 0:
            self.runtimes_expander.set_subtitle(
                _("{} selected").format(self.total_runtimes_selected)
            )
        else:
            self.runtimes_expander.set_subtitle("")
        if self.total_remotes_selected > 0:
            self.remotes_expander.set_subtitle(
                _("{} selected").format(self.total_remotes_selected)
            )
        else:
            self.remotes_expander.set_subtitle("")

    def reset_filter_gsettings(self):
        self.show_apps_switch.set_active(True)
        self.show_runtimes_switch.set_active(False)
        for button in self.remote_checkboxes:
            button.set_active(False)
        for button in self.runtime_checkboxes:
            button.set_active(False)
        for key in self.settings.list_keys():
            self.settings.reset(key)
        self.total_remotes_selected = 0
        self.total_runtimes_selected = 0
        self.row_subtitle_updater()
        self.reset_button.set_sensitive(False)

    def runtime_handler(self, button, runtime):
        if button.get_active():
            self.total_runtimes_selected += 1
            self.runtimes_string = self.runtimes_string.replace("all", "")
            self.runtimes_string += f"{runtime},"
        else:
            self.total_runtimes_selected -= 1
            self.runtimes_string = self.runtimes_string.replace(f"{runtime},", "")
            if len(self.runtimes_string) < 1:
                self.runtimes_string += "all"
        self.settings.set_string("runtimes-list", self.runtimes_string)
        self.check_is_resetable()
        self.row_subtitle_updater()
        self.main_window.apply_filter()

    def remote_handler(self, button, remote, install_type):
        if button.get_active():
            self.total_remotes_selected += 1
            self.remotes_string = self.remotes_string.replace("all", "")
            self.remotes_string += f"{remote}<>{install_type};"
        else:
            self.total_remotes_selected -= 1
            self.remotes_string = self.remotes_string.replace(
                f"{remote}<>{install_type};", ""
            )
            if len(self.remotes_string) < 1:
                self.remotes_string += "all"
        self.settings.set_string("remotes-list", self.remotes_string)
        self.check_is_resetable()
        self.row_subtitle_updater()
        self.main_window.apply_filter()

    def generate_remotes(self):
        if (
            len(self.host_remotes) < 2
        ):  # Don't give the ability to filter by remotes if there is only 1
            self.remotes_expander.set_visible(False)

        total = 0
        for i in range(len(self.host_remotes)):
            try:
                name = self.host_remotes[i][0]
                title = self.host_remotes[i][1]
                url = self.host_remotes[i][2]
                install_type = self.my_utils.get_install_type(self.host_remotes[i][7])
                remote_row = Adw.ActionRow(title=title)
                if "disabled" in install_type:
                    continue
                total += 1
                if title == "-":
                    remote_row.set_title(name)
                self.remotes_expander.add_row(remote_row)
                label = Gtk.Label(label=("{} wide").format(install_type))
                label.add_css_class("subtitle")
                remote_check = Gtk.CheckButton()
                if name in self.remotes_string:
                    remote_check.set_active(True)
                    self.total_remotes_selected += 1
                remote_check.connect(
                    "toggled",
                    lambda button=remote_check, remote=name, install_type=install_type: self.remote_handler(
                        button, remote, install_type
                    ),
                )
                self.remote_checkboxes.append(remote_check)

                if "user" in install_type:
                    remote_row.set_subtitle(_("User wide"))
                elif "system" in install_type:
                    remote_row.set_subtitle(_("System wide"))
                else:
                    remote_row.set_subtitle(_("Unknown install type"))

                remote_row.add_suffix(remote_check)
                remote_row.set_activatable_widget(remote_check)
            except Exception as e:
                print(
                    "error at filter_window.generate_remotes: Could not make remote row. error",
                    e,
                )

        self.row_subtitle_updater()
        if total < 2:
            self.remotes_expander.set_visible(False)

    def generate_runtimes(self):
        if (
            len(self.dependent_runtimes) < 2
        ):  # Don't give the ability to filter by runtimes if there is only 1
            self.runtimes_expander.set_visible(False)

        for current in self.dependent_runtimes:
            runtime_row = Adw.ActionRow(title=current)
            runtime_check = Gtk.CheckButton()
            if current in self.runtimes_string:
                runtime_check.set_active(True)
                self.total_runtimes_selected += 1
            runtime_check.connect(
                "toggled",
                lambda button=runtime_check, runtime=current: self.runtime_handler(
                    button, runtime
                ),
            )
            self.runtime_checkboxes.append(runtime_check)
            runtime_row.add_suffix(runtime_check)
            runtime_row.set_activatable_widget(runtime_check)
            self.runtimes_expander.add_row(runtime_row)
        self.row_subtitle_updater()

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        event_controller = Gtk.EventControllerKey()
        self.main_window = main_window
        self.my_utils = myUtils(self)
        self.host_remotes = self.my_utils.get_host_remotes()
        self.dependent_runtimes = self.my_utils.get_dependent_runtimes()
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        self.remotes_string = self.settings.get_string("remotes-list")
        self.runtimes_string = self.settings.get_string("runtimes-list")
        self.remote_checkboxes = []
        self.runtime_checkboxes = []
        self.total_remotes_selected = 0
        self.total_runtimes_selected = 0

        # Window Things
        self.set_transient_for(main_window)
        self.add_controller(event_controller)
        self.set_size_request(260, 230)

        self.show_apps_switch.set_active(self.settings.get_boolean("show-apps"))
        self.show_runtimes_switch.set_active(self.settings.get_boolean("show-runtimes"))

        # Connections
        event_controller.connect("key-pressed", self.key_handler)
        self.show_apps_switch.connect(
            "state-set",
            lambda button, state: self.gsettings_bool_set("show-apps", state),
        )
        self.show_runtimes_switch.connect(
            "state-set",
            lambda button, state: self.gsettings_bool_set("show-runtimes", state),
        )
        self.reset_button.connect("clicked", lambda *_: self.reset_filter_gsettings())

        # Calls
        if self.host_remotes[0][0] == "":
            self.remotes_expander.set_visible(False)
        else:
            self.generate_remotes()

        if self.dependent_runtimes == []:
            self.runtimes_expander.set_visible(False)
        else:
            self.generate_runtimes()
        self.check_is_resetable()
        self.present()
