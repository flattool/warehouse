from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
import os, subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/result_row.ui")
class ResultRow(Adw.ActionRow):
    __gtype_name__ = "ResultRow"
    gtc = Gtk.Template.Child

    version_label = gtc()
    branch_label = gtc()
    add_image = gtc()
    sub_image = gtc()

    def idle_stuff(self):
        self.set_title(GLib.markup_escape_text(self.name))
        self.set_subtitle(self.app_id)
        self.version_label.set_label(GLib.markup_escape_text(self.version))
        self.branch_label.set_label(GLib.markup_escape_text(self.branch))
        self.version_label.set_visible(len(self.version_label.get_label()) != 0)
        self.branch_label.set_visible(len(self.branch_label.get_label()) != 0)
        self.sub_image.set_visible(bool(self.original_row))
        self.add_image.set_visible(not bool(self.original_row))
        self.set_tooltip_text(_("Remove Package from Queue") if bool(self.original_row) else _("Add Package to Queue"))

    def __init__(self, name, app_id, branch, version, original_row=None, **kwargs):
        super().__init__(**kwargs)

        self.name = name
        self.app_id = app_id
        self.branch = branch
        self.version = version
        self.original_row = original_row

        GLib.idle_add(self.idle_stuff)