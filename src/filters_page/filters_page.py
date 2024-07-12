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

    test_button = gtc()

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

        remotes_string = self.settings.get_string("remotes-list")
        for i, installation in enumerate(HostInfo.installations):
            try:
                for remote in HostInfo.remotes[installation]:
                    row = FilterRow(remote, installation)
                    row.set_title(remote.title)
                    row.set_subtitle(_("Installation: {}").format(installation))
                    row.check_button.set_active(f"{remote.name}<>{installation}" in remotes_string)
                    row.set_visible(False)
                    self.remote_rows.append(row)
                    self.remotes_group.add(row)
            except KeyError:
                pass
        self.all_remotes_button.set_active("all" != remotes_string)

        runtimes_string = self.settings.get_string("runtimes-list")
        for j, ref in enumerate(HostInfo.dependant_runtime_refs):
            row = FilterRow(ref)
            row.set_title(ref)
            row.check_button.set_active(ref in runtimes_string)
            row.set_visible(False)
            self.runtime_rows.append(row)
            self.runtimes_group.add(row)
        self.all_runtimes_button.set_active("all" != runtimes_string)

    def all_remotes_handler(self, switch, state):
        for row in self.remote_rows:
            row.set_visible(state)
            row.set_sensitive(state)

    def all_runtimes_handler(self, switch, state):
        for row in self.runtime_rows:
            row.set_visible(state)
            row.set_sensitive(state)

    def test(self, *args):
        print(self.settings.get_boolean("show-apps"))
        print(self.settings.get_boolean("show-runtimes"))
        print(self.settings.get_string("remotes-list"))
        print(self.settings.get_string("runtimes-list"))

    def __init__(self, main_window, packages_page, **kwargs):
        super().__init__(**kwargs)

        # Extra Objects Creation
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")

        # Apply

        # Connections
        self.test_button.connect("clicked", self.test)

        self.all_remotes_button.connect("state-set", self.all_remotes_handler)
        self.all_runtimes_button.connect("state-set", self.all_runtimes_handler)