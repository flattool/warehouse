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
    remotes_search = gtc()
    remotes_listbox = gtc()
    runtimes_group = gtc()
    runtimes_search = gtc()
    runtimes_listbox = gtc()
    all_remotes_button = gtc()
    all_runtimes_button = gtc()

    remote_rows = []
    runtime_rows = []

    def generate_list(self):
        self.remotes_search.set_text("")
        self.runtimes_search.set_text("")

        self.remotes_listbox.remove_all()
        self.runtimes_listbox.remove_all()

        self.remote_rows.clear()
        self.runtime_rows.clear()

        self.app_check.set_active(self.settings.get_boolean("show-apps"))
        self.runtime_check.set_active(self.settings.get_boolean("show-runtimes"))

        remotes_string = self.settings.get_string("runtimes-list")
        self.all_remotes_button.set_active("all" != remotes_string)
        for i, installation in enumerate(HostInfo.installations):
            try:
                for remote in HostInfo.remotes[installation]:
                    row = FilterRow(remote, installation)
                    row.set_title(remote.title)
                    row.set_subtitle(_("Installation: {}").format(installation))
                    self.remote_rows.append(row)
                    self.remotes_listbox.append(row)
            except KeyError:
                pass
        self.remotes_search.set_visible(i > 5)

        runtimes_string = self.settings.get_string("runtimes-list")
        self.all_runtimes_button.set_active("all" != runtimes_string)
        for j, ref in enumerate(HostInfo.dependant_runtime_refs):
            row = FilterRow(ref)
            row.set_title(ref)
            self.runtime_rows.append(row)
            self.runtimes_listbox.append(row)
        self.runtimes_search.set_visible(j > 5)

    def all_remotes_handler(self, switch, state):
        self.remotes_group.set_description(_("Show packages from these remotes") if state else _("Showing packages from all remotes"))

    def all_runtimes_handler(self, switch, state):
        self.runtimes_group.set_description(_("Show apps using these runtimes") if state else _("Showing packages using any runtime"))

    def remotes_filter_func(self, row):
        search_text = self.remotes_search.get_text().lower()
        return search_text in row.get_title().lower()

    def runtimes_filter_func(self, row):
        search_text = self.runtimes_search.get_text().lower()
        return search_text in row.get_title().lower()

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
        self.remotes_listbox.set_filter_func(self.remotes_filter_func)
        self.runtimes_listbox.set_filter_func(self.runtimes_filter_func)

        # Connections
        self.test_button.connect("clicked", self.test)

        self.remotes_search.connect("search-changed", lambda *_: self.remotes_listbox.invalidate_filter())
        self.runtimes_search.connect("search-changed", lambda *_: self.runtimes_listbox.invalidate_filter())
        self.all_remotes_button.connect("state-set", self.all_remotes_handler)
        self.all_runtimes_button.connect("state-set", self.all_runtimes_handler)