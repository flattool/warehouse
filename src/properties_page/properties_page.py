from gi.repository import Adw, Gtk,GLib#, Gio, Pango
from .error_toast import ErrorToast
import subprocess, os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/properties_page/properties_page.ui")
class PropertiesPage(Adw.NavigationPage):
    __gtype_name__ = 'PropertiesPage'
    gtc = Gtk.Template.Child
    toast_overlay = gtc()
    header_bar = gtc()
    scrolled_window = gtc()
    app_icon = gtc()
    name = gtc()
    description = gtc()
    open_app_button = gtc()
    uninstall_button = gtc()
    
    pin_row = gtc()
    data_row = gtc()
    open_data_button = gtc()
    trash_data_button = gtc()
    data_spinner = gtc()
    version_row = gtc()
    mask_label = gtc()
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

    def set_properties(self, package, refresh=False):
        if package == self.package and not refresh:
            # Do not update the ui if the same app row is clicked
            print("skip")
            return
        
        self.package = package
        self.set_title(_("{} Properties").format(package.info["name"]))
        self.name.set_label(package.info["name"])
        pkg_description = package.info["description"]
        self.description.set_visible(pkg_description != "")
        self.description.set_label(pkg_description)

        if package.icon_path:
            GLib.idle_add(lambda *_: self.app_icon.set_from_file(package.icon_path))
        else:
            GLib.idle_add(lambda *_: self.app_icon.set_from_icon_name("application-x-executable-symbolic"))

        self.pin_row.set_visible(package.is_runtime)
        self.open_app_button.set_visible(package.is_runtime)
        self.open_app_button.set_visible(not package.is_runtime)
        if not package.is_runtime:
            has_path = os.path.exists(package.data_path)
            self.trash_data_button.set_sensitive(has_path)
            self.open_data_button.set_sensitive(has_path)

            if has_path:
                self.trash_data_button.set_visible(False)
                self.open_data_button.set_visible(False)
                self.data_spinner.set_visible(True)
                self.data_row.set_subtitle(_("Loading User Data"))

                def callback(size):
                    self.trash_data_button.set_visible(True)
                    self.open_data_button.set_visible(True)
                    self.data_spinner.set_visible(False)
                    self.data_row.set_subtitle(size)

                self.package.get_data_size(lambda size: callback(size))
            else:
                self.data_row.set_subtitle(_("No User Data"))

        cli_info = None
        try:
            cli_info = package.get_cli_info()
        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not get properties"), str(e)).toast)
            return

        for key, row in self.info_rows.items():
            row.set_visible(False)

            try:
                subtitle = cli_info[key]
                row.set_subtitle(subtitle)
                row.set_visible(True)
            except KeyError:
                if key == "version":
                    row.set_visible(True)
                    row.set_subtitle(_("No version information found"))
                continue
            except Exception as e:
                self.toast_overlay.add_toast(ErrorToast(_("Could not get properties"), str(e)).toast)
                continue

        self.mask_label.set_visible(package.is_masked)

    def ask_confirmation(self, title, description):
        pass

    def open_data_handler(self, *args):
        if error := self.package.open_data():
            self.toast_overlay.add_toast(ErrorToast(_("Could not open data"), str(error)).toast)

    def trash_data_handler(self, *args):
        try:
            self.package.trash_data()
            self.set_properties(self.package, refresh=True)
            self.toast_overlay.add_toast(Adw.Toast.new("Trashed User Data"))
        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not trash data"), str(e)).toast)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.main_window = main_window
        self.info_rows = {
            "version": self.version_row,
            "installed": self.installed_size_row,

            "id": self.id_row,
            "ref": self.ref_row,
            "arch": self.arch_row,
            "branch": self.branch_row,
            "license": self.license_row,

            "runtime": self.runtime_row,
            "sdk": self.sdk_row,
            "origin": self.origin_row,
            "collection": self.collection_row,
            "installation": self.installation_row,

            "commit": self.commit_row,
            "parent": self.parent_row,
            "subject": self.subject_row,
            "date": self.date_row,
        }

        # Connections
        self.open_data_button.connect("clicked", self.open_data_handler)
        self.scrolled_window.get_vadjustment().connect("value-changed", lambda adjustment: self.header_bar.set_show_title(not adjustment.get_value() == 0))
        self.trash_data_button.connect("clicked", self.trash_data_handler)