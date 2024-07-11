from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo

class FilterRow(Adw.ActionRow):
    __gtype_name__ = 'FilterRow'
    def __init__(self, item=None, installation=None, **kwargs):
        super().__init__(**kwargs)
        self.item = item
        self.installation = installation
        self.check_button = Gtk.CheckButton()
        self.check_button.add_css_class("selection-mode")
        self.add_suffix(self.check_button)
        self.set_activatable_widget(self.check_button)

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/filters_page/filters_page.ui")
class FiltersPage(Adw.NavigationPage):
    __gtype_name__ = 'FiltersPage'
    gtc = Gtk.Template.Child
    app_check = gtc()
    runtime_check = gtc()
    remotes_group = gtc()
    runtimes_group = gtc()
    all_remotes_button = gtc()
    all_runtimes_button = gtc()

    remote_rows = []
    runtime_rows = []

    def generate_list(self):
        for row in self.remote_rows:
            self.remotes_group.remove(row)

        for row in self.runtime_rows:
            self.runtimes_group.remove(row)

        self.remote_rows.clear()
        self.runtime_rows.clear()

        self.app_check.set_active(self.settings.get_boolean("show-apps"))
        self.runtime_check.set_active(self.settings.get_boolean("show-runtimes"))

        remotes_string = self.settings.get_string("runtimes-list")
        self.all_remotes_button.set_active("all" == remotes_string)
        for installation in HostInfo.installations:
            try:
                for remote in HostInfo.remotes[installation]:
                    row = FilterRow(remote, installation)
                    row.set_title(remote.title)
                    row.set_subtitle(_("Installation: {}").format(installation))
                    row.check_button.set_active(self.all_remotes_button.get_active())
                    self.remote_rows.append(row)
                    self.remotes_group.add(row)
            except KeyError:
                pass

        runtimes_string = self.settings.get_string("runtimes-list")
        self.all_runtimes_button.set_active("all" == runtimes_string)
        for ref in HostInfo.dependant_runtime_refs:
            row = FilterRow(ref)
            row.set_title(ref)
            row.check_button.set_active(self.all_runtimes_button.get_active())
            self.runtime_rows.append(row)
            self.runtimes_group.add(row)

    def select_all_handler(self, rows, button):
        for row in rows:
            row.check_button.set_active(button.get_active())

    def __init__(self, main_window, packages_page, **kwargs):
        super().__init__(**kwargs)

        # Extra Objects Creation
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")

        # Apply

        # Connections
        self.all_remotes_button.connect("toggled", lambda *_: self.select_all_handler(self.remote_rows, self.all_remotes_button))
        self.all_runtimes_button.connect("toggled", lambda *_: self.select_all_handler(self.runtime_rows, self.all_runtimes_button))