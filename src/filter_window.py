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
    apps_switch = Gtk.Template.Child()
    runtimes_switch = Gtk.Template.Child()
    remotes_expander = Gtk.Template.Child()
    runtimes_expander = Gtk.Template.Child()

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    # Unused for now. !!!! Don't forget!
    def is_list_applicable(self):
        # self.apply_button.set_sensitive(True)

        # if not self.filter_list[0] == True and not self.filter_list[1] == True:
        #     self.apply_button.set_sensitive(False)
        #     return

        # if self.filter_list[3] == []:
        #     self.apply_button.set_sensitive(False)
        #     return

        # if self.filter_list[4] == []:
        #     self.apply_button.set_sensitive(False)
        #     return

        # if (
        #     self.apps_switch.get_active()
        #     and (not self.runtimes_switch.get_active())
        #     and (not self.remotes_expander_switch.get_active())
        #     and (not self.runtimes_expander_switch.get_active())
        # ):
        #     self.apply_button.set_sensitive(False)
        #     return
        pass

    def gschema_bool_setter(key, state):
        self.settings.set_boolean(key, state)
        self.is_list_applicable()

    def gschema_string_setter(key, state):
        self.settings.set_string(key, state)
        self.is_list_applicable()
    
    def generate_list(self):
        self.remotes_expander_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.runtimes_expander_switch = Gtk.Switch(valign=Gtk.Align.CENTER)

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
        total = 0
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

                if "user" in install_type:
                    remote_row.set_subtitle(_("User wide"))
                elif "system" in install_type:
                    remote_row.set_subtitle(_("System wide"))
                else:
                    remote_row.set_subtitle(_("Unknown install type"))

                remote_row.add_suffix(remote_check)
                remote_row.set_activatable_widget(remote_check)
                # remote_check.connect(
                #     "toggled", self.remotes_check_handler, install_type, name
                # )
                self.remote_checkboxes.append(remote_check)
            except Exception as e:
                print("error at filter_window.generate_list: Could not make remote row. error", e)

        if total < 2:
            self.remotes_expander.set_visible(False)

        self.remotes_expander.add_suffix(self.remotes_expander_switch)

        self.runtime_checkboxes = []
        for i in range(len(dependent_runtimes)):
            current = dependent_runtimes[i]
            runtime_row = Adw.ActionRow(title=current)
            runtime_check = Gtk.CheckButton()
            # runtime_check.connect(
            #     "toggled", self.runtimes_check_handler, current
            # )
            runtime_check.set_active(True)
            self.runtime_checkboxes.append(runtime_check)
            runtime_row.add_suffix(runtime_check)
            runtime_row.set_activatable_widget(runtime_check)
            self.runtimes_expander.add_row(runtime_row)
        
        self.runtimes_expander.add_suffix(self.runtimes_expander_switch)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.present()



        

        self.settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")

        self.apps_switch.set_active(self.settings.get_boolean("show-apps"))
        self.apps_switch.connect("state-set", lambda switch, state: gschema_bool_setter("show-apps", state))
        self.runtimes_switch.set_active(self.settings.get_boolean("show-runtimes"))
        self.runtimes_switch.connect("state-set", lambda switch, state: gschema_bool_setter("show-runtimes", state))



        # Create Variables
        event_controller = Gtk.EventControllerKey()
        self.my_utils = myUtils(self)
        self.host_remotes = self.my_utils.get_host_remotes()
        self.host_flatpaks = main_window.host_flatpaks
        self.filter_list = [False, False, [], [], []]
        self.app_window = main_window
        self.has_apply_button_been_clicked = False

        # Window Things
        self.set_transient_for(main_window)
        self.add_controller(event_controller)

        # Connections
        self.apply_button.connect(
            "clicked", lambda *_: self.set_has_apply_button_been_clicked(True)
        )
        # self.apply_button.connect(
        #     "clicked", lambda *_: main_window.apply_filter(self.filter_list)
        # )
        # self.apply_button.connect("clicked", lambda *_: self.close())

        self.cancel_button.connect("clicked", lambda *_: self.close())

        # self.apps_switch.connect("state-set", self.apps_handler)
        # self.runtimes_switch.connect("state-set", self.runtimes_handler)
        event_controller.connect("key-pressed", self.key_handler)

        # Calls
        self.set_size_request(260, 230)
        if not self.host_remotes[0][0] == "":
            self.generate_list()
        else:
            self.remotes_expander.set_visible(False)
            self.runtimes_expander.set_visible(False)
            self.filter_list[2] = "all"
            self.filter_list[3] = "all"
            self.filter_list[4] = "all"
