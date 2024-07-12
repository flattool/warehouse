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

    def update_gsettings(self):
        if not self.is_settings_settable:
            return
        self.settings.set_boolean("show-apps", self.show_apps)
        self.settings.set_boolean("show-runtimes", self.show_runtimes)
        self.settings.set_string("remotes-list", self.remotes_string)
        self.settings.set_string("runtimes-list", self.runtimes_string)
        self.total_sets += 1
        self.test()

    def remote_row_check_handler(self, row):
        if row.check_button.get_active():
            self.remotes_string += f"{row.item.name}<>{row.installation};"
        else:
            self.remotes_string = self.remotes_string.replace(f"{row.item.name}<>{row.installation};", "")
        self.update_gsettings()

    def runtime_row_check_handler(self, row):
        if row.check_button.get_active():
            self.runtimes_string += f"{row.item},"
        else:
            self.runtimes_string = self.runtimes_string.replace(f"{row.item},", "")
        self.update_gsettings()

    def generate_list(self):
        self.is_settings_settable = False

        for row in self.remote_rows:
            self.remotes_group.remove(row)

        for row in self.runtime_rows:
            self.runtimes_group.remove(row)

        self.remote_rows.clear()
        self.runtime_rows.clear()

        self.app_check.set_active(self.show_apps)
        self.runtime_check.set_active(self.show_runtimes)

        for i, installation in enumerate(HostInfo.installations):
            try:
                for remote in HostInfo.remotes[installation]:
                    row = FilterRow(remote, installation)
                    row.set_title(remote.title)
                    row.set_subtitle(_("Installation: {}").format(installation))
                    row.check_button.set_active(f"{remote.name}<>{installation}" in self.remotes_string)
                    row.check_button.connect("toggled", lambda *_, row=row: self.remote_row_check_handler(row))
                    row.set_visible(self.all_remotes_button.get_active())
                    self.remote_rows.append(row)
                    self.remotes_group.add(row)
            except KeyError:
                pass
        self.all_remotes_button.set_active("all" != self.remotes_string)

        for j, ref in enumerate(HostInfo.dependant_runtime_refs):
            row = FilterRow(ref)
            row.set_title(ref)
            row.check_button.set_active(ref in self.runtimes_string)
            row.check_button.connect("toggled", lambda *_, row=row: self.runtime_row_check_handler(row))
            row.set_visible(self.all_runtimes_button.get_active())
            self.runtime_rows.append(row)
            self.runtimes_group.add(row)
        self.all_runtimes_button.set_active("all" != self.runtimes_string)
        self.is_settings_settable = True

    def all_remotes_handler(self, switch, state):
        self.remotes_string = ""
        if not state:
            self.remotes_string = "all"

        for row in self.remote_rows:
            row.set_visible(state)
            if state and row.check_button.get_active():
                self.remotes_string += f"{row.item.name}<>{row.installation};"
            elif state:
                self.remotes_string.replace(f"{row.item.name}<>{row.installation};", "")
        
        self.update_gsettings()

    def all_runtimes_handler(self, switch, state):
        self.runtimes_string = ""
        if not state:
            self.runtimes_string = "all"
        
        for row in self.runtime_rows:
            row.set_visible(state)
            if state and row.check_button.get_active():
                self.runtimes_string += row.item
            elif state:
                self.runtimes_string.replace
        
        self.update_gsettings()

    def test(self, *args):
        print('\n-------------------------------------')
        print(self.settings.get_boolean("show-apps"))
        print(self.settings.get_boolean("show-runtimes"))
        print(self.settings.get_string("remotes-list"))
        print(self.settings.get_string("runtimes-list"))
        print("total sets:", self.total_sets)

    def app_check_handler(self, *args):
        self.show_apps = self.app_check.get_active()
        self.update_gsettings()
        
    def runtime_check_handler(self, *args):
        self.show_runtimes = self.runtime_check.get_active()
        self.update_gsettings()

    def __init__(self, main_window, packages_page, **kwargs):
        super().__init__(**kwargs)

        # Extra Objects Creation
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        self.is_settings_settable = False
        self.show_apps = self.settings.get_boolean("show-apps")
        self.show_runtimes = self.settings.get_boolean("show-runtimes")
        self.remotes_string = self.settings.get_string("remotes-list")
        self.runtimes_string = self.settings.get_string("runtimes-list")
        self.total_sets = 0

        # Apply

        # Connections
        self.test_button.connect("clicked", self.test)

        self.app_check.connect("toggled", self.app_check_handler)
        self.runtime_check.connect("toggled", self.runtime_check_handler)
        self.all_remotes_button.connect("state-set", self.all_remotes_handler)
        self.all_runtimes_button.connect("state-set", self.all_runtimes_handler)