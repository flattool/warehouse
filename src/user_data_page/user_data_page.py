from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .error_toast import ErrorToast
from .data_box import DataBox
from .data_subpage import DataSubpage
from .host_info import HostInfo
import os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/user_data_page.ui")
class UserDataPage(Adw.BreakpointBin):
    __gtype_name__ = 'UserDataPage'
    gtc = Gtk.Template.Child
    bpt = gtc()
    header_bar = gtc()
    switcher_bar = gtc()
    sidebar_button = gtc()
    search_button = gtc()
    active_select_button = gtc()
    active_sort_button = gtc()
    leftover_select_button = gtc()
    leftover_sort_button = gtc()
    search_entry = gtc()
    toast_overlay = gtc()
    stack = gtc()
    revealer = gtc()
    
    active_asc = gtc()
    active_dsc = gtc()
    active_sort_name = gtc()
    active_sort_id = gtc()
    active_sort_size = gtc()

    leftover_asc = gtc()
    leftover_dsc = gtc()
    leftover_sort_name = gtc()
    leftover_sort_id = gtc()
    leftover_sort_size = gtc()
    

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    def sort_data(self, *args):
        self.data_flatpaks.clear()
        self.active_data.clear()
        self.leftover_data.clear()
        # paks = dict(HostInfo.id_to_flatpak)

        for folder in os.listdir(f"{HostInfo.home}/.var/app"):
            try:
                self.data_flatpaks.append(HostInfo.id_to_flatpak[folder])
                self.active_data.append(folder)
            except KeyError:
                self.leftover_data.append(folder)

    def start_loading(self, *args):
        self.adp.size_label.set_label("Loading Size…")
        self.adp.spinner.set_visible(True)
        self.adp.flow_box.remove_all()
        self.ldp.size_label.set_label("Loading Size…")
        self.ldp.spinner.set_visible(True)
        self.ldp.flow_box.remove_all()

    def end_loading(self, *args):
        def callback(*args):
            self.adp.generate_list(self.data_flatpaks, self.active_data)
            self.ldp.generate_list([], self.leftover_data)
            self.search_button.grab_focus()
        
        Gio.Task.new(None, None, callback).run_in_thread(self.sort_data)

    def switch_view_handler(self, page):
        self.active_select_button.set_visible(page is self.adp)
        self.active_sort_button.set_visible(page is self.adp)
        self.leftover_select_button.set_visible(page is self.ldp)
        self.leftover_sort_button.set_visible(page is self.ldp)
        self.active_select_button.set_active(False)
        self.leftover_select_button.set_active(False)
        self.revealer_handler()

    def revealer_handler(self, *args):
        self.revealer.set_reveal_child(self.active_select_button.get_active() or self.leftover_select_button.get_active())

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.__class__.instance = self
        # self.adj = self.scrolled_window.get_vadjustment()
        self.adp = DataSubpage(_("Active Data"), self, main_window)
        self.ldp = DataSubpage(_("Leftover Data"), self, main_window)
        self.data_flatpaks = []
        self.active_data = []
        self.leftover_data = []
        self.total_items = 0
        ms=main_window.main_split

        # Apply
        self.stack.add_titled_with_icon(
            child=self.adp,
            name="active",
            title=_("Active Data"),
            icon_name="file-manager-symbolic",
        )
        self.stack.add_titled_with_icon(
            child=self.ldp,
            name="leftover",
            title=_("Leftover Data"),
            icon_name="folder-templates-symbolic",
        )
        self.sidebar_button.set_active(ms.get_show_sidebar())

        # Connections
        # self.sidebar_button.connect("clicked", lambda *_, ms=main_window.main_split: ms.set_show_sidebar(not ms.get_show_sidebar() if not ms.get_collapsed() else True))
        main_window.main_split.connect("notify::show-sidebar", lambda *_: self.sidebar_button.set_active(ms.get_show_sidebar()))
        self.sidebar_button.connect("toggled", lambda *_: ms.set_show_sidebar(self.sidebar_button.get_active()))
        self.stack.connect("notify::visible-child", lambda *_: self.switch_view_handler(self.stack.get_visible_child()))
        self.active_select_button.connect("toggled", self.revealer_handler)
        self.leftover_select_button.connect("toggled", self.revealer_handler)
        
        def sorter(button=None):
            if button and not button.get_active():
                return

            if self.active_sort_name.get_active():
                self.adp.sort_mode = "name"
            elif self.active_sort_id.get_active():
                self.adp.sort_mode = "id"
            elif self.active_sort_size.get_active():
                self.adp.sort_mode = "size"
            
            if self.leftover_sort_name.get_active():
                self.ldp.sort_mode = "name"
            elif self.leftover_sort_id.get_active():
                self.ldp.sort_mode = "id"
            elif self.leftover_sort_size.get_active():
                self.ldp.sort_mode = "size"

            self.adp.sort_ascend = self.active_asc.get_active()
            self.ldp.sort_ascend = self.leftover_asc.get_active()

            self.adp.flow_box.invalidate_sort()
            self.ldp.flow_box.invalidate_sort()

        self.active_asc.connect("clicked", sorter)
        self.active_dsc.connect("clicked", sorter)
        self.active_sort_name.connect("clicked", sorter)
        self.active_sort_id.connect("clicked", sorter)
        self.active_sort_size.connect("clicked", sorter)

        self.leftover_asc.connect("clicked", sorter)
        self.leftover_dsc.connect("clicked", sorter)
        self.leftover_sort_name.connect("clicked", sorter)
        self.leftover_sort_id.connect("clicked", sorter)
        self.leftover_sort_size.connect("clicked", sorter)

        sorter()