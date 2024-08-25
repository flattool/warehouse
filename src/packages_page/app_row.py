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

    def gest(self, *args):
        self.on_long_press(self)

    def __init__(self, package, on_long_press=None, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.package = package
        self.on_long_press = on_long_press
        self.rclick_gesture = Gtk.GestureClick()
        self.long_press_gesture = Gtk.GestureLongPress()

        # Apply
        GLib.idle_add(lambda *_: self.set_title(package.info["name"]))
        GLib.idle_add(lambda *_: self.set_subtitle(package.info["id"]))
        GLib.idle_add(lambda *_: self.idle_stuff())
        self.rclick_gesture.set_button(3)
        self.add_controller(self.rclick_gesture)

        # Connections
        self.rclick_gesture.connect("released", self.gest)
        self.long_press_gesture.connect("pressed", self.gest)