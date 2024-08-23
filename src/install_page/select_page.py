from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .results_page import ResultsPage

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/select_page.ui")
class SelectPage(Adw.NavigationPage):
    __gtype_name__ = "SelectPage"
    gtc = Gtk.Template.Child

    nav_view = gtc()
    sidebar_button = gtc()
    results_page = gtc()
    remotes_group = gtc()
    add_remote_row = gtc()

    test = gtc()

    def start_loading(self):
        pass

    def end_loading(self):
        total_remotes = 0
        for installation, remotes in HostInfo.remotes.items():
            for remote in remotes:
                if remote.disabled:
                    continue

                row = Adw.ActionRow(title=remote.title, subtitle=_("Installation: {}").format(installation), activatable=True)
                row.add_suffix(Gtk.Image(icon_name="right-large-symbolic"))
                row.connect("activated", self.results_page.show_remote, remote, installation, self.nav_view)
                self.remotes_group.add(row)
                total_remotes += 1

        self.remotes_group.set_visible(total_remotes != 0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        ms = HostInfo.main_window.main_split

        # Connections
        ms.connect("notify::show-sidebar", lambda *_: self.sidebar_button.set_active(ms.get_show_sidebar()))
        self.sidebar_button.connect("toggled", lambda *_: ms.set_show_sidebar(self.sidebar_button.get_active()))
        self.add_remote_row.connect("activated", lambda *_: HostInfo.main_window.activate_row(HostInfo.main_window.remotes_row))
        self.nav_view.connect("popped", self.results_page.on_back)

        self.test.connect("clicked", lambda *_: self.nav_view.push(self.results_page))

        # Apply
