from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/packages_page/app_row.ui")
class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'
    gtc = Gtk.Template.Child
    image = gtc()
    eol_package_package_status_icon = gtc()
    eol_runtime_status_icon = gtc()
    pinned_status_icon = gtc()
    masked_status_icon = gtc()
    check_button = gtc()

    def idle_stuff(self):
        if self.package.icon_path:
            self.image.add_css_class("icon-dropshadow")
            self.image.set_from_file(self.package.icon_path)
        
        if self.callback:
            self.callback()

    def __init__(self, package, callback=None, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.package = package
        self.callback = callback

        # Apply
        GLib.idle_add(lambda *_: self.set_title(package.info["name"]))
        GLib.idle_add(lambda *_: self.set_subtitle(package.info["id"]))
        GLib.idle_add(lambda *_: self.idle_stuff())

        # Connections