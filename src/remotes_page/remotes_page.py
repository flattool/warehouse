from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .remote_row import RemoteRow
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/remotes_page.ui")
class RemotesPage(Adw.NavigationPage):
    __gtype_name__ = 'RemotesPage'
    gtc = Gtk.Template.Child

    sidebar_button = gtc()
    search_bar = gtc()
    toast_overlay = gtc()
    stack = gtc()
    current_remotes_group = gtc()
    new_remotes_group = gtc()

    # Statuses
    loading_remotes = gtc()
    no_remotes = gtc()
    content_page = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None
    
    def start_loading(self):
        self.stack.set_visible_child(self.loading_remotes)
        for row in self.current_remote_rows:
            self.current_remotes_group.remove(row)
        self.current_remote_rows.clear()

    def end_loading(self):
        self.stack.set_visible_child(self.content_page)
        for install in HostInfo.installations:
            for remote in HostInfo.remotes[install]:
                row = RemoteRow(self, install, remote)
                self.current_remotes_group.add(row)
                self.current_remote_rows.append(row)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.__class__.instance = self
        ms = main_window.main_split
        self.search_bar.set_key_capture_widget(main_window)
        self.current_remote_rows = []

        # Connections
        ms.connect("notify::show-sidebar", lambda *_: self.sidebar_button.set_active(ms.get_show_sidebar()))
        self.sidebar_button.connect("toggled", lambda *_: ms.set_show_sidebar(self.sidebar_button.get_active()))