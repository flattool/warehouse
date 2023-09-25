from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib

@Gtk.Template(resource_path="org/neocities/heliguy/Warehouse/filter.ui")
class FilterWindow(Adw.Window):
    __gtype_name__ = "FilterWindow"

    cancel_button = Gtk.Template.Child()
    apply_button = Gtk.Template.Child()
    remotes_list = Gtk.Template.Child()
    apps_switch = Gtk.Template.Child()
    runtimes_switch = Gtk.Template.Child()
    header_label = Gtk.Template.Child()

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def isListApplicable(self):
        self.apply_button.set_sensitive(False)

        if self.filter_list[0] == True or self.filter_list[1] == True:
            if not self.filter_list[3] == []:
                self.apply_button.set_sensitive(True)

    def appsHandler(self, switch, _a):
        self.filter_list[0] = switch.get_active()
        self.isListApplicable()

    def runtimesHandler(self, switch, _a):
        self.filter_list[1] = switch.get_active()
        self.isListApplicable()

    def remoteCheckHandler(self, checkbox, install_type, remote):
        if checkbox.get_active():
            self.filter_list[2].append(install_type)
            self.filter_list[3].append(remote)
        else:
            self.filter_list[2].remove(install_type)
            self.filter_list[3].remove(remote)

        self.isListApplicable()

    def generateList(self):
        Gtk.Label.set_markup(self.header_label, ("<b>{}</b>").format(self.header_label.get_label()))

        for i in range(len(self.host_remotes)):
            name = self.host_remotes[i][0]
            title = self.host_remotes[i][1]
            install_type = self.host_remotes[i][7]
            url = self.host_remotes[i][2]
            remote_row = Adw.ActionRow(title=title, subtitle=url)
            if title == "-":
                remote_row.set_title(name)
            self.remotes_list.append(remote_row)
            label = Gtk.Label(label=("{} wide").format(install_type))
            label.add_css_class("subtitle")
            remote_check = Gtk.CheckButton()
            remote_row.add_suffix(label)
            remote_row.add_suffix(remote_check)
            remote_row.set_activatable_widget(remote_check)

            remote_check.connect("toggled", self.remoteCheckHandler, install_type, name)
            remote_check.set_active(True)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.host_remotes = self.my_utils.getHostRemotes()
        self.filter_list = [False, False, [], []]
        event_controller = Gtk.EventControllerKey()
        self.app_window = main_window

        # Window Things
        self.set_transient_for(main_window)
        self.add_controller(event_controller)

        # Connections
        self.apply_button.connect("clicked", lambda *_: main_window.updateFilter(self.filter_list))
        self.apply_button.connect("clicked", lambda *_: self.close())

        self.cancel_button.connect("clicked", lambda *_: main_window.filter_button.set_active(False))
        self.cancel_button.connect("clicked", lambda *_: self.close())

        self.apps_switch.connect("state-set", self.appsHandler)
        self.runtimes_switch.connect("state-set", self.runtimesHandler)
        event_controller.connect("key-pressed", self.key_handler)

        # Calls
        self.apps_switch.set_active(True)
        self.set_size_request(260, 230)
        if not self.host_remotes[0][0] == '':
            self.generateList()
        else:
            self.header_label.set_visible(False)
            self.remotes_list.set_visible(False)
            self.filter_list[2] = "all"
            self.filter_list[3] = "all"


