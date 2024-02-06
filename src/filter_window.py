from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/../data/ui/filter.ui")
class FilterWindow(Adw.Window):
    __gtype_name__ = "FilterWindow"

    cancel_button = Gtk.Template.Child()
    apply_button = Gtk.Template.Child()
    show_apps_switch = Gtk.Template.Child()
    show_runtimes_switch = Gtk.Template.Child()
    remotes_expander = Gtk.Template.Child()
    runtimes_expander = Gtk.Template.Child()
    reset_button = Gtk.Template.Child()

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def is_list_applicable(self):
        self.apply_button.set_sensitive(True)

        show_apps = self.show_apps_switch.get_active()
        show_runtimes = self.show_runtimes_switch.get_active()
        filter_by_remotes = self.remotes_switch.get_active()
        filter_by_runtimes = self.runtimes_switch.get_active()

        if (not show_apps) and (not show_runtimes):
            self.apply_button.set_sensitive(False)
            return

        if show_runtimes and filter_by_runtimes:
            self.apply_button.set_sensitive(False)
            return

        if filter_by_remotes and self.remotes_string_staging == ["all"]:
            self.apply_button.set_sensitive(False)
            return

        if filter_by_runtimes and self.runtimes_string_staging == ["all"]:
            self.apply_button.set_sensitive(False)
            return

        if(show_apps == self.settings.get_boolean("show-apps")) and (show_runtimes == self.settings.get_boolean("show-runtimes")) and (self.remotes_string_staging == self.settings.get_string("remotes-list").split(',')) and (self.runtimes_string_staging == self.settings.get_string("runtimes-list").split(',')):
            self.apply_button.set_sensitive(False)
            return

    def show_apps_handler(self, switch, state):
        self.is_list_applicable()
        self.show_apps_staging = state

    def show_runtimes_handler(self, switch, state):
        self.is_list_applicable()
        self.show_runtimes_staging = state

    def remote_handler(self, remote, should_add):
        the_list = self.remotes_string_staging
        if should_add:
            the_list.append(remote)
            if "all" in the_list and len(the_list) > 1:
                the_list.remove("all")
        else:
            the_list.remove(remote)
            if len(the_list) < 1:
                the_list.append("all")

        self.is_list_applicable()

    def runtime_handler(self, runtime, should_add):
        the_list = self.runtimes_string_staging
        if should_add:
            the_list.append(runtime)
            if "all" in the_list and len(the_list) > 1:
                the_list.remove("all")
        else:
            the_list.remove(runtime)
            if len(the_list) < 1:
                the_list.append("all")

        self.is_list_applicable()

    def remotes_switch_handler(self, switch, state):
        self.is_list_applicable()
        for box in self.remote_checkboxes:
            box.set_sensitive(state)
            box.set_active(False)
        self.remotes_expander.set_enable_expansion(state)
        if not state:
            self.remotes_string_staging = ["all"]

    def runtimes_switch_handler(self, switch, state):
        self.is_list_applicable()
        for box in self.runtime_checkboxes:
            box.set_sensitive(state)
            box.set_active(False)
        self.runtimes_expander.set_enable_expansion(state)
        if not state:
            self.runtimes_string_staging = ["all"]

    def reset_filter_gsettings(self):
        self.show_apps_switch.set_active(True)
        self.show_runtimes_switch.set_active(False)
        self.remotes_switch.set_active(False)
        self.runtimes_switch.set_active(False)

    def on_apply(self):
        self.settings.set_boolean("show-apps", self.show_apps_staging)
        self.settings.set_boolean("show-runtimes", self.show_runtimes_staging)
        self.settings.set_string("remotes-list", ",".join(self.remotes_string_staging))
        self.settings.set_string(
            "runtimes-list", ",".join(self.runtimes_string_staging)
        )
        self.main_window.apply_filter()
        self.close()

    def generate_list(self):

        dependent_runtimes = self.my_utils.get_dependent_runtimes()

        if (
            len(self.host_remotes) < 2
        ):  # Don't give the ability to filter by remotes if there is only 1
            self.remotes_expander.set_visible(False)

        if (
            len(dependent_runtimes) < 2
        ):  # Don't give the ability to filter by runtimes if there is only 1
            self.runtimes_expander.set_visible(False)

        self.remote_checkboxes = []
        remotes_list = self.remotes_string_staging
        total = 0
        self.remotes_switch.connect("state-set", self.remotes_switch_handler)
        self.remotes_expander.add_suffix(self.remotes_switch)
        self.remotes_switch.set_active(remotes_list[0] != "all")
        for i in range(len(self.host_remotes)):
            try:
                name = self.host_remotes[i][0]
                title = self.host_remotes[i][1]
                url = self.host_remotes[i][2]
                install_type = self.host_remotes[i][7]
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
                remote_check.set_active(name in remotes_list)
                remote_check.connect(
                    "toggled",
                    lambda button=remote_check, remote=name: self.remote_handler(
                        remote, button.get_active()
                    ),
                )

                if "user" in install_type:
                    remote_row.set_subtitle(_("User wide"))
                elif "system" in install_type:
                    remote_row.set_subtitle(_("System wide"))
                else:
                    remote_row.set_subtitle(_("Unknown install type"))

                remote_row.add_suffix(remote_check)
                remote_row.set_activatable_widget(remote_check)
                self.remote_checkboxes.append(remote_check)
            except Exception as e:
                print(
                    "error at filter_window.generate_list: Could not make remote row. error",
                    e,
                )

        if total < 2:
            self.remotes_expander.set_visible(False)

        self.runtime_checkboxes = []
        runtimes_list = self.runtimes_string_staging
        self.runtimes_switch.connect("state-set", self.runtimes_switch_handler)
        self.runtimes_expander.add_suffix(self.runtimes_switch)
        self.runtimes_switch.set_active(runtimes_list[0] != "all")
        for current in dependent_runtimes:
            runtime_row = Adw.ActionRow(title=current)
            runtime_check = Gtk.CheckButton()
            runtime_check.set_active(current in runtimes_list)
            runtime_check.connect(
                "toggled",
                lambda button=runtime_check, runtime=current: self.runtime_handler(
                    runtime, button.get_active()
                ),
            )
            self.runtime_checkboxes.append(runtime_check)
            runtime_row.add_suffix(runtime_check)
            runtime_row.set_activatable_widget(runtime_check)
            self.runtimes_expander.add_row(runtime_row)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        event_controller = Gtk.EventControllerKey()
        self.remotes_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.runtimes_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.main_window = main_window
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        self.my_utils = myUtils(self)
        self.host_remotes = self.my_utils.get_host_remotes()
        self.show_apps_staging = self.settings.get_boolean("show-apps")
        self.show_runtimes_staging = self.settings.get_boolean("show-runtimes")
        self.remotes_string_staging = self.settings.get_string("remotes-list").split(
            ","
        )
        self.runtimes_string_staging = self.settings.get_string("runtimes-list").split(
            ","
        )

        # Window Things
        self.set_transient_for(main_window)
        self.add_controller(event_controller)
        self.set_size_request(260, 230)

        # Connections
        event_controller.connect("key-pressed", self.key_handler)
        self.show_runtimes_switch.connect("state-set", self.show_runtimes_handler)
        self.show_apps_switch.connect("state-set", self.show_apps_handler)
        self.apply_button.connect("clicked", lambda *_: self.on_apply())
        self.cancel_button.connect("clicked", lambda *_: self.close())
        self.reset_button.connect("clicked", lambda *_: self.reset_filter_gsettings())

        # Calls
        if not self.host_remotes[0][0] == "":
            self.generate_list()
        else:
            self.remotes_expander.set_visible(False)
            self.runtimes_expander.set_visible(False)

        self.show_apps_switch.set_active(self.show_apps_staging)
        self.show_runtimes_switch.set_active(self.show_runtimes_staging)
        self.present()
