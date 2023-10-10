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
    add_from_file = Gtk.Template.Child()
    custom_remote = Gtk.Template.Child()

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def file_callback(self, object, result):
        try:
            file = object.open_finish(result)
            self.parent_window.addRemoteFromFile(file.get_path())
            self.close()
        except GLib.GError:
            pass

    def addFromFileHandler(self, widet):
        filter = Gtk.FileFilter(name=_("Flatpaks Repos"))
        filter.add_suffix("flatpakrepo")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter)
        file_chooser = Gtk.FileDialog()
        file_chooser.set_filters(filters)
        file_chooser.set_default_filter(filter)
        file_chooser.open(self, None, self.file_callback)

    def generate_list(self):
        self.host_remotes = self.my_utils.getHostRemotes()
        self.list_of_remotes.remove_all()
        host_remotes_names = []

        for i in range(len(self.remotes)):
            remote_row = Adw.ActionRow(activatable=True)
            remote_row.set_title(self.remotes[i][0])
            remote_row.set_subtitle(self.remotes[i][3])
            remote_row.add_suffix(Gtk.Image.new_from_icon_name("right-large-symbolic"))
            remote_row.connect("activated", self.parent_window.add_handler, self.remotes[i][1], self.remotes[i][2])
            remote_row.connect("activated", lambda *_: self.close())
            self.list_of_remotes.append(remote_row)

        self.add_from_file.add_suffix(Gtk.Image.new_from_icon_name("right-large-symbolic"))
        self.add_from_file.connect("activated", self.addFromFileHandler)
        #self.add_from_file.connect("activated", lambda *_: self.close())

        self.custom_remote.add_suffix(Gtk.Image.new_from_icon_name("right-large-symbolic"))
        self.custom_remote.connect("activated", self.parent_window.add_handler)
        self.custom_remote.connect("activated", lambda *_: self.close())

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
