from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib
import re

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/popular_remotes.ui")
class PopularRemotesWindow(Adw.Window):
    __gtype_name__ = "PopularRemotesWindow"

    list_of_remotes = Gtk.Template.Child()
    custom_list = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def generate_list(self):
        self.host_remotes = self.my_utils.getHostRemotes()
        self.list_of_remotes.remove_all()
        self.custom_list.remove_all()
        host_remotes_names = []

        for i in range(len(self.remotes)):
            remote_row = Adw.ActionRow(activatable=True)
            remote_row.set_title(self.remotes[i][0])
            remote_row.set_subtitle(self.remotes[i][3])
            image = Gtk.Image.new_from_icon_name("right-large-symbolic")
            remote_row.add_suffix(image)
            remote_row.connect("activated", self.parent_window.add_handler, self.remotes[i][1], self.remotes[i][2])
            remote_row.connect("activated", lambda *_: self.close())
            self.list_of_remotes.append(remote_row)

        image2 = Gtk.Image.new_from_icon_name("right-large-symbolic")
        custom_remote = Adw.ActionRow(activatable=True)
        custom_remote.set_title(_("Add a Custom Remote"))
        custom_remote.add_suffix(image2)
        custom_remote.connect("activated", self.parent_window.add_handler)
        custom_remote.connect("activated", lambda *_: self.close())
        self.custom_list.append(custom_remote)

        if not self.list_of_remotes.get_row_at_index(0):
            self.list_of_remotes.set_visible(False)

    def __init__(self, parent_window, remotes, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(self)
        self.parent_window = parent_window
        self.set_size_request(260, 230)
        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)
        self.remotes = remotes

        self.new_env = dict( os.environ ) 
        self.new_env['LC_ALL'] = 'C' 

        self.set_modal(True)
        self.set_transient_for(parent_window)
        self.generate_list()
