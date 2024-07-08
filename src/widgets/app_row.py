from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/widgets/app_row.ui")
class AppRow(Adw.ActionRow):
    __gtype_name__ = 'AppRow'
    gtc = Gtk.Template.Child
    image = gtc()
    eol_package_package_status_icon = gtc()
    eol_runtime_status_icon = gtc()
    pinned_status_icon = gtc()
    masked_status_icon = gtc()
    check_button = gtc()

    def __init__(self, package, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.package = package

        # Apply
        GLib.idle_add(lambda *_: self.set_title(package.info["name"]))
        GLib.idle_add(lambda *_: self.set_subtitle(package.info["id"]))
        if package.icon_path:
            GLib.idle_add(lambda *_: self.image.add_css_class("icon-dropshadow"))
            GLib.idle_add(lambda *_: self.image.set_from_file(package.icon_path))

        # Connections