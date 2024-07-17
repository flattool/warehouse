from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .error_toast import ErrorToast
from .active_data_page import ActiveDataPage
from .leftover_data_page import LeftoverDataPage

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/user_data_page.ui")
class UserDataPage(Adw.BreakpointBin):
    __gtype_name__ = 'UserDataPage'
    gtc = Gtk.Template.Child
    bpt = gtc()
    header_bar = gtc()
    switcher_bar = gtc()
    sidebar_button = gtc()
    select_button = gtc()
    stack = gtc()
    sort_pop = gtc()
    sort_list = gtc()
    sort_name = gtc()
    sort_id = gtc()
    sort_size = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    def sort_handler(self, button):
        if button.get_active() == False:
            return
        self.sort_name.set_active(self.sort_name is button)
        self.sort_id.set_active(self.sort_id is button)
        self.sort_size.set_active(self.sort_size is button)
        if button is self.sort_name:
            self.sort_id.grab_focus()
        else:
            self.sort_name.grab_focus()

    # def bpt_handler(self, _, is_applied):
    #     if is_applied and self.adj.get_value() == 0:
    #         self.header_bar.set_show_title(False)
    #     else:
    #         self.header_bar.set_show_title(True)

    # def show_title_handler(self, *args):
    #     if self.adj.get_value() != 0:
    #         self.header_bar.set_show_title(True)
    #     elif self.switcher_bar.get_reveal():
    #         self.header_bar.set_show_title(False)

    def start_loading(self, *args):
        pass

    def end_loading(self, *args):
        pass

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.__class__.instance = self
        # self.adj = self.scrolled_window.get_vadjustment()

        # Apply
        self.stack.add_titled_with_icon(
            child=ActiveDataPage(main_window, self),
            name="active",
            title=_("Active Data"),
            icon_name="file-manager-symbolic",
        )
        self.stack.add_titled_with_icon(
            child=LeftoverDataPage(main_window, self),
            name="leftover",
            title=_("Leftover Data"),
            icon_name="folder-templates-symbolic",
        )

        # Connections
        self.sidebar_button.connect("clicked", lambda *_, ms=main_window.main_split: ms.set_show_sidebar(not ms.get_show_sidebar() if not ms.get_collapsed() else True))
        # self.adj.connect("value-changed", self.show_title_handler)
        self.sort_name.connect("toggled", self.sort_handler)
        self.sort_id.connect("toggled", self.sort_handler)
        self.sort_size.connect("toggled", self.sort_handler)
        # self.bpt.connect("apply", self.bpt_handler, True)
        # self.bpt.connect("unapply", self.bpt_handler, False)