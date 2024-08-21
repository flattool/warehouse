from gi.repository import Adw, Gtk, GLib, Gio, Gdk
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
    selected_image = gtc()

    def idle_stuff(self):
        self.set_title(GLib.markup_escape_text(self.package.name))
        self.set_subtitle(self.package.app_id)
        self.version_label.set_label(GLib.markup_escape_text(self.package.version))
        self.branch_label.set_label(GLib.markup_escape_text(self.package.branch))
        self.version_label.set_visible(len(self.version_label.get_label()) != 0)
        self.branch_label.set_visible(len(self.branch_label.get_label()) != 0)
        if self.is_added:
            self.set_tooltip_text(_("Remove Package from Queue"))

    def set_is_added(self, is_added):
        self.is_added = is_added
        self.set_sensitive(not is_added)
        self.add_image.set_visible(not is_added)
        self.selected_image.set_visible(is_added)
        self.set_tooltip_text(_("This package is queued") if is_added else _("Add Package to Queue"))

    def __init__(self, package, is_added=False, **kwargs):
        super().__init__(**kwargs)

        self.is_added = is_added
        self.package = package

        self.sub_image.set_visible(is_added)
        self.add_image.set_visible(not is_added)

        GLib.idle_add(self.idle_stuff)
