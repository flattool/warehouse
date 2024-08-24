from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .result_row import ResultRow

class AddedGroup(Adw.PreferencesGroup):
    __gtype_name__ = "AddedGroup"

    def add_row(self, row):
        self.rows.append(row)
        self.add(row)

    def rem_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
            self.remove(row)

    def __init__(self, remote, installation, **kwargs):
        super().__init__(**kwargs)

        self.remote = remote
        self.installation = installation
        self.rows = []

        self.set_title(f"{remote.title}")
        self.set_description(_("Installation: {}").format(installation))

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/pending_page.ui")
class PendingPage(Adw.NavigationPage):
    __gtype_name__ = "PendingPage"
    gtc = Gtk.Template.Child

    stack = gtc()
    none_pending = gtc()
    preferences_page = gtc()

    def add_package(self, row):
        key = f"{row.package.remote}<>{row.package.installation}"
        row = ResultRow(row.package, ResultRow.PackageState.ADDED)
        row.connect("activated", self.remove_package, group)
        try:
            group = self.groups[key]
            group.add_row(row)
        except KeyError:
            group = AddedGroup(row.package.remote, row.package.installation)
            group.add_row(row)
            self.groups[key] = group
            self.preferences_page.append(group)

    def remove_package(self, row, group):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.groups = {} # remote<>installation: adw.preference_group

        # Connections

        # Apply
