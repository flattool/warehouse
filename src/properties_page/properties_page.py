from gi.repository import Adw, Gtk#, GLib, Gio, Pango

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/properties_page/properties_page.ui")
class PropertiesPage(Adw.NavigationPage):
    __gtype_name__ = 'PropertiesPage'
    gtc = Gtk.Template.Child
    app_icon = gtc()
    name = gtc()
    description = gtc()

    def set_properties(self, package):
        self.set_title(package.info["id"])
        self.name.set_label(package.info["name"])
        pkg_description = package.info["description"]
        self.description.set_visible(pkg_description != "")
        self.description.set_label(pkg_description)
        if package.icon_path:
            self.app_icon.set_from_file(package.icon_path)
        else:
            self.app_icon.set_from_icon_name("application-x-executable-symbolic")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)