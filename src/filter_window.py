from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib

@Gtk.Template(resource_path="/io/github/heliguy4599/Warehouse/filter.ui")
class FilterWindow(Adw.Window):
    __gtype_name__ = "FilterWindow"

    cancel_button = Gtk.Template.Child()
    apply_button = Gtk.Template.Child()
    remotes_list = Gtk.Template.Child()
    runtimes_row = Gtk.Template.Child()

    def runtimesHandler(self, switch, _a):
        print(switch.get_active())

    def generateList(self):
        for i in range(len(self.host_remotes)):
            name = self.host_remotes[i][0]
            title = self.host_remotes[i][1]
            install_type = self.host_remotes[i][7]
            url = self.host_remotes[i][2]
            remote_row = Adw.SwitchRow(title=title, subtitle=url)
            if title == "-":
                remote_row.set_title(name)
            self.remotes_list.append(remote_row)
            label = Gtk.Label(label=("{} wide").format(install_type))
            label.add_css_class("subtitle")
            remote_row.add_suffix(label)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.host_remotes = self.my_utils.getHostRemotes()
        self.filter_list = "the guh"

        # Window Things
        self.set_transient_for(main_window)

        # Connections
        self.apply_button.connect("clicked", lambda *_: main_window.updateFilter(self.filter_list))
        self.apply_button.connect("clicked", lambda *_: self.close())
        self.cancel_button.connect("clicked", lambda *_: self.close())
        self.runtimes_row.connect("notify::active", self.runtimesHandler)

        # Calls
        self.generateList()

