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

    def isListApplicable(self):
        self.apply_button.set_sensitive(True)

        if not self.filter_list[0] == True and not self.filter_list[1] == True:
            self.apply_button.set_sensitive(False)
            return

        if self.filter_list[3] == []:
            self.apply_button.set_sensitive(False)
            return

        if self.filter_list[4] == []:
            self.apply_button.set_sensitive(False)
            return

        if self.apps_switch.get_active() and\
          (not self.runtimes_switch.get_active()) and\
          (not self.remotes_expander_switch.get_active()) and\
          (not self.runtimes_expander_switch.get_active()):
            self.apply_button.set_sensitive(False)
            return

    def appsHandler(self, switch, _a):
        self.filter_list[0] = switch.get_active()
        self.isListApplicable()

    def runtimesHandler(self, switch, _a):
        self.filter_list[1] = switch.get_active()
        self.isListApplicable()

    def remotesEnableHandler(self, switch, is_enabled):
        self.remotes_expander.set_enable_expansion(is_enabled)

        for i in range(len(self.remote_checkboxes)):
            self.remote_checkboxes[i].set_active(not is_enabled)

    def remoteCheckHandler(self, checkbox, install_type, remote):
        install_type = self.my_utils.getInstallType(install_type)
        if checkbox.get_active():
            self.filter_list[2].append(install_type)
            self.filter_list[3].append(remote)
        else:
            self.filter_list[2].remove(install_type)
            self.filter_list[3].remove(remote)

        self.isListApplicable()

    def runtimesEnableHandler(self, switch, is_enabled):
        self.runtimes_expander.set_enable_expansion(is_enabled)
        
        for i in range(len(self.runtime_checkboxes)):
            self.runtime_checkboxes[i].set_active(not is_enabled)

        self.isListApplicable()

    def runtimeCheckHandler(self, checkbox, runtime):
        if checkbox.get_active():
            if self.filter_list[4] == "all":
                self.filter_list[4] = []
            self.filter_list[4].append(runtime)
        else:
            self.filter_list[4].remove(runtime)
        
        self.isListApplicable()

    def generateList(self):
        self.remotes_expander_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.runtimes_expander_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        
        dependent_runtimes = self.my_utils.getDependentRuntimes()

        if len(self.host_remotes) < 2: # Don't give the ability to filter by remotes if there is only 1
            self.remotes_expander.set_visible(False)

        if len(dependent_runtimes) < 2: # Don't give the ability to filter by runtimes if there is only 1
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
                remote_check.connect("toggled", self.remoteCheckHandler, install_type, name)
                self.remote_checkboxes.append(remote_check)
                remote_check.set_active(True)
            except:
                print("Could not make remote row")
        if total < 2:
            self.remotes_expander.set_visible(False)
        self.remotes_expander_switch.connect("state-set", self.remotesEnableHandler)
        self.remotes_expander.add_suffix(self.remotes_expander_switch)

        self.runtime_checkboxes = []
        for i in range(len(dependent_runtimes)):
            current = dependent_runtimes[i]
            runtime_row = Adw.ActionRow(title=current)
            runtime_check = Gtk.CheckButton()
            runtime_check.connect("toggled", self.runtimeCheckHandler, current)
            runtime_check.set_active(True)
            self.runtime_checkboxes.append(runtime_check)
            runtime_row.add_suffix(runtime_check)
            runtime_row.set_activatable_widget(runtime_check)
            self.runtimes_expander.add_row(runtime_row)
        self.runtimes_expander_switch.connect("state-set", self.runtimesEnableHandler)
        self.runtimes_expander.add_suffix(self.runtimes_expander_switch)

    def setHas_apply_button_been_clicked(self, is_clicked):
        self.has_apply_button_been_clicked = is_clicked
        if not self.remotes_expander_switch.get_active():
            self.filter_list[3] = "all"
        if not self.runtimes_expander_switch.get_active():
            self.filter_list[4] = "all" 

    def disableFilterToggle(self, _widget):
        self.app_window.filter_button.set_active(self.has_apply_button_been_clicked)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.host_remotes = self.my_utils.getHostRemotes()
        self.host_flatpaks = main_window.host_flatpaks
        self.filter_list = [False, False, [], [], []]
        event_controller = Gtk.EventControllerKey()
        self.app_window = main_window
        self.has_apply_button_been_clicked = False

        # Window Things
        self.set_transient_for(main_window)
        self.add_controller(event_controller)

        # Connections
        self.apply_button.connect("clicked", lambda *_: self.setHas_apply_button_been_clicked(True))
        self.apply_button.connect("clicked", lambda *_: main_window.applyFilter(self.filter_list))
        self.apply_button.connect("clicked", lambda *_: self.close())

        self.cancel_button.connect("clicked", lambda *_: self.close())

        self.connect("close-request", self.disableFilterToggle)

        self.apps_switch.connect("state-set", self.appsHandler)
        self.runtimes_switch.connect("state-set", self.runtimesHandler)
        event_controller.connect("key-pressed", self.key_handler)

        # Calls
        self.apps_switch.set_active(True)
        self.set_size_request(260, 230)
        if not self.host_remotes[0][0] == '':
            self.generateList()
        else:
            self.remotes_expander.set_visible(False)
            self.runtimes_expander.set_visible(False)
            self.filter_list[2] = "all"
            self.filter_list[3] = "all"
            self.filter_list[4] = "all"


