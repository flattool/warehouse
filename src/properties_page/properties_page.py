from gi.repository import Adw, Gtk#, GLib, Gio, Pango
from .error_toast import ErrorToast

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/properties_page/properties_page.ui")
class PropertiesPage(Adw.NavigationPage):
    __gtype_name__ = 'PropertiesPage'
    gtc = Gtk.Template.Child
    toast_overlay = gtc()
    app_icon = gtc()
    name = gtc()
    description = gtc()
    open_app_button = gtc()
    uninstall_button = gtc()
    
    pin_row = gtc()
    data_row = gtc()
    open_data_button = gtc()
    trash_data_button = gtc()
    version_row = gtc()
    mask_row = gtc()
    downgrade_row = gtc()
    installed_size_row = gtc()
    
    id_row = gtc()
    ref_row = gtc()
    arch_row = gtc()
    branch_row = gtc()
    license_row = gtc()

    runtime_row = gtc()
    sdk_row = gtc()
    origin_row = gtc()
    collection_row = gtc()
    installation_row = gtc()
    
    commit_row = gtc()
    parent_row = gtc()
    subject_row = gtc()
    date_row = gtc()

    package = None

    def set_properties(self, package):
        if package == self.package:
            # Do not update the ui if the same app row is clicked
            return
        
        self.package = package
        self.set_title(package.info["id"])
        self.name.set_label(package.info["name"])
        pkg_description = package.info["description"]
        self.description.set_visible(pkg_description != "")
        self.description.set_label(pkg_description)

        if package.icon_path:
            self.app_icon.set_from_file(package.icon_path)
        else:
            self.app_icon.set_from_icon_name("application-x-executable-symbolic")

    def open_data_handler(self, *args):
        if error := self.package.open_data():
            self.toast_overlay.add_toast(ErrorToast(_("Could not open data"), str(error), self.main_window).toast)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.main_window = main_window

        # Connections
        self.open_data_button.connect("clicked", self.open_data_handler)