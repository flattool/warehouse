from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo

class FilterRow(Adw.ActionRow):
    __gtype_name__ = 'FilterRow'
    def __init__(self, item=None, installation=None, **kwargs):
        super().__init__(**kwargs)
        self.item = item
        self.installation = installation
        self.check_button = Gtk.CheckButton()
        self.add_suffix(self.check_button)
        self.set_activatable_widget(self.check_button)

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/packages_page/filters_page.ui")
class FiltersPage(Adw.NavigationPage):
    __gtype_name__ = 'FiltersPage'
    gtc = Gtk.Template.Child
    app_check = gtc()
    runtime_check = gtc()
    remotes_group = gtc()
    all_remotes_switch = gtc()
    runtimes_group = gtc()
    all_runtimes_switch = gtc()
    action_bar = gtc()
    reset_button = gtc()

    remote_rows = []
    runtime_rows = []

    def reset_filters(self):
        self.settings.reset("show-apps")
        self.settings.reset("show-runtimes")
        self.settings.reset("remotes-list")
        self.settings.reset("runtimes-list")
        self.generate_filters()
        self.packages_page.apply_filters()

    def is_defaulted(self):
        default = True
        if not self.app_check.get_active():
            default = False
        if self.runtime_check.get_active():
            default = False
        if self.all_remotes_switch.get_active():
            default = False
        if self.all_runtimes_switch.get_active():
            default = False
        self.action_bar.set_revealed(not default)

    def update_gsettings(self):
        self.is_defaulted()
        if not self.is_settings_settable:
            return
        self.settings.set_boolean("show-apps", self.show_apps)
        self.settings.set_boolean("show-runtimes", self.show_runtimes)
        self.settings.set_string("remotes-list", self.remotes_string)
        self.settings.set_string("runtimes-list", self.runtimes_string)
        self.packages_page.apply_filters()

    def app_check_handler(self, *args):
        self.show_apps = self.app_check.get_active()
        self.update_gsettings()
        
    def runtime_check_handler(self, *args):
        self.show_runtimes = self.runtime_check.get_active()
        self.update_gsettings()

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
                self.runtimes_string += f"{row.item};"
            elif state:
                self.runtimes_string.replace(f"{row.item};", "")
        
        self.update_gsettings()

    def remote_row_check_handler(self, row):
        if row.check_button.get_active():
            self.remotes_string += f"{row.item.name}<>{row.installation};"
        else:
            self.remotes_string = self.remotes_string.replace(f"{row.item.name}<>{row.installation};", "")
        self.update_gsettings()

    def runtime_row_check_handler(self, row):
        if row.check_button.get_active():
            self.runtimes_string += f"{row.item};"
        else:
            self.runtimes_string = self.runtimes_string.replace(f"{row.item};", "")
        self.update_gsettings()

    def generate_remote_filters(self):
        for row in self.remote_rows:
            self.remotes_group.remove(row)

        self.remote_rows.clear()
        for installation, remotes in HostInfo.remotes.items():
            for remote in remotes:
                if remote.disabled:
                    continue

                row = FilterRow(remote, installation)
                row.set_title(remote.title)
                row.set_subtitle(_("Installation: {}").format(installation))
                row.check_button.set_active(f"{remote.name}<>{installation}" in self.remotes_string)
                row.check_button.connect("toggled", lambda *_, row=row: self.remote_row_check_handler(row))
                row.set_visible(self.all_remotes_switch.get_active())
                self.remote_rows.append(row)
                self.remotes_group.add(row)

        self.remotes_group.set_visible(len(self.remote_rows) > 1)
        self.all_remotes_switch.set_active("all" != self.remotes_string)

    def generate_runtime_filters(self):
        for row in self.runtime_rows:
            self.runtimes_group.remove(row)
        self.runtime_rows.clear()
        if len(HostInfo.dependant_runtime_refs) < 2:
            self.runtimes_group.set_visible(False)
            if self.runtimes_string != "all":
                self.runtimes_string = "all"
                self.settings.set_string("runtimes-list", self.runtimes_string)
                self.packages_page.apply_filters()

            return

        for j, ref in enumerate(HostInfo.dependant_runtime_refs):
            row = FilterRow(ref)
            row.set_title(ref)
            row.check_button.set_active(ref in self.runtimes_string)
            row.check_button.connect("toggled", lambda *_, row=row: self.runtime_row_check_handler(row))
            row.set_visible(self.all_runtimes_switch.get_active())
            self.runtime_rows.append(row)
            self.runtimes_group.add(row)

        self.runtimes_group.set_visible(len(self.runtime_rows) > 1)
        self.all_runtimes_switch.set_active("all" != self.runtimes_string)

    def generate_filters(self):
        self.is_settings_settable = False
        self.show_apps = self.settings.get_boolean("show-apps")
        self.show_runtimes = self.settings.get_boolean("show-runtimes")
        self.remotes_string = self.settings.get_string("remotes-list")
        self.runtimes_string = self.settings.get_string("runtimes-list")
        
        self.app_check.set_active(self.show_apps)
        self.runtime_check.set_active(self.show_runtimes)

        self.generate_remote_filters()
        self.generate_runtime_filters()

        self.is_settings_settable = True

    def __init__(self, main_window, packages_page, **kwargs):
        super().__init__(**kwargs)

        # Extra Objects Creation
        self.packages_page = packages_page
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        self.is_settings_settable = False

        self.show_apps = self.settings.get_boolean("show-apps")
        self.show_runtimes = self.settings.get_boolean("show-runtimes")
        self.remotes_string = self.settings.get_string("remotes-list")
        self.runtimes_string = self.settings.get_string("runtimes-list")

        # Apply
        if "," in self.runtimes_string:
            # Convert Warehouse 1.X runtimes filter string from , to ; for item seperationg
            self.runtimes_string = self.runtimes_string.replace(",", ";")
            self.settings.set_string("runtimes-list", self.runtimes_string)

        # Connections
        self.app_check.connect("toggled", self.app_check_handler)
        self.runtime_check.connect("toggled", self.runtime_check_handler)
        self.all_remotes_switch.connect("state-set", self.all_remotes_handler)
        self.all_runtimes_switch.connect("state-set", self.all_runtimes_handler)
        self.reset_button.connect("clicked", lambda *_: self.reset_filters())