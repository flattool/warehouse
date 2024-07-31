from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .error_toast import ErrorToast
from .data_box import DataBox
from .data_subpage import DataSubpage
from .host_info import HostInfo
import os, subprocess

import time

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/user_data_page.ui")
class UserDataPage(Adw.BreakpointBin):
    __gtype_name__ = 'UserDataPage'
    gtc = Gtk.Template.Child
    bpt = gtc()
    header_bar = gtc()
    switcher_bar = gtc()
    sidebar_button = gtc()
    search_button = gtc()
    select_button = gtc()
    sort_button = gtc()
    search_bar = gtc()
    search_entry = gtc()
    toast_overlay = gtc()
    stack = gtc()
    revealer = gtc()
    
    sort_ascend = gtc()
    sort_descend = gtc()
    sort_name = gtc()
    sort_id = gtc()
    sort_size = gtc()
    
    select_all_button = gtc()
    copy_button = gtc()
    trash_button = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    def sort_data(self, *args):
        self.data_flatpaks.clear()
        self.active_data.clear()
        self.leftover_data.clear()
        # paks = dict(HostInfo.id_to_flatpak)

        if not os.path.exists(f"{HostInfo.home}/.var/app"):
            return

        for folder in os.listdir(f"{HostInfo.home}/.var/app"):
            try:
                self.data_flatpaks.append(HostInfo.id_to_flatpak[folder])
                self.active_data.append(folder)
            except KeyError:
                self.leftover_data.append(folder)

    def start_loading(self, *args):
        self.select_button.set_active(False)
        self.adp.set_visible_child(self.adp.loading_data)
        self.adp.size_label.set_label("Loading Size")
        self.adp.spinner.set_visible(True)
        self.adp.flow_box.remove_all()
        self.ldp.set_visible_child(self.ldp.loading_data)
        self.ldp.size_label.set_label("Loading Size")
        self.ldp.spinner.set_visible(True)
        self.ldp.flow_box.remove_all()

    def end_loading(self, *args):
        def callback(*args):
            self.adp.generate_list(self.data_flatpaks, self.active_data)
            self.ldp.generate_list([], self.leftover_data)
        
        Gio.Task.new(None, None, callback).run_in_thread(self.sort_data)

    def sorter(self, button=None):
        if button and not button.get_active():
            return

        if self.sort_name.get_active():
            self.adp.sort_mode = "name"
            self.ldp.sort_mode = "name"
        elif self.sort_id.get_active():
            self.adp.sort_mode = "id"
            self.ldp.sort_mode = "id"
        elif self.sort_size.get_active():
            self.adp.sort_mode = "size"
            self.ldp.sort_mode = "size"
        
        self.adp.sort_ascend = self.sort_ascend.get_active()
        self.ldp.sort_ascend = self.sort_ascend.get_active()

        self.adp.flow_box.invalidate_sort()
        self.ldp.flow_box.invalidate_sort()

    def view_change_handler(self, *args):
        child = self.stack.get_visible_child()
        if child.total_size == 0:
            self.search_button.set_active(False)
            self.search_button.set_sensitive(False)
            self.select_button.set_active(False)
            self.select_button.set_sensitive(False)
            self.sort_button.set_active(False)
            self.sort_button.set_sensitive(False)
            self.search_entry.set_editable(False)
        else:
            self.search_button.set_sensitive(True)
            self.select_button.set_sensitive(True)
            self.sort_button.set_sensitive(True)
            self.search_entry.set_editable(True)

        has_selected = len(child.selected_boxes) > 0
        self.copy_button.set_sensitive(has_selected)
        self.trash_button.set_sensitive(has_selected)
        
    def select_toggle_handler(self, *args):
        active = self.select_button.get_active()
        self.adp.set_selection_mode(active)
        self.ldp.set_selection_mode(active)
        if not active:
            self.copy_button.set_sensitive(False)
            self.trash_button.set_sensitive(False)

    def select_all_handler(self, *args):
        child = self.stack.get_visible_child()
        child.select_all_handler()

    def copy_handler(self, *args):
        child = self.stack.get_visible_child()
        to_copy = ""
        for box in child.selected_boxes:
            to_copy += "\n" + box.data_path
        
        if len(to_copy) == 0:
            self.toast_overlay.add_toast(ErrorToast(_("Could not copy paths"), _("No boxes were selected")).toast)
        else:
            HostInfo.clipboard.set(to_copy.replace("\n", "", 1))
            self.toast_overlay.add_toast(Adw.Toast(title=_("Copied paths")))

    def trash_handler(self, *args):
        error = [None]

        def thread(path):
            cmd = ['gio', 'trash'] + path
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as cpe:
                error[0] = cpe.stderr
            except Exception as e:
                error[0] = e

        def callback(*args):
            self.start_loading()
            self.end_loading()
            if error[0]:
                self.toast_overlay.add_toast(ErrorToast(_("Could not trash data"), str(error[0])).toast)
            else:
                self.toast_overlay.add_toast(Adw.Toast(title=_("Trashed data")))

        child = self.stack.get_visible_child()
        to_trash = []
        for box in child.selected_boxes:
            to_trash.append(box.data_path)
        
        if len(to_trash) == 0:
            self.toast_overlay.add_toast(ErrorToast(_("Could not trash data"), _("No boxes were selected")).toast)
            return
        
        self.select_button.set_active(False)
        child.set_visible_child(child.loading_data)
        Gio.Task.new(None, None, callback).run_in_thread(lambda *_: thread(to_trash))
        
        # self.toast_overlay.add_toast(Adw.Toast(title=_("Trashed data")))

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.__class__.instance = self
        # self.adj = self.scrolled_window.get_vadjustment()
        self.adp = DataSubpage(_("Active Data"), self, True, main_window)
        self.ldp = DataSubpage(_("Leftover Data"), self, False, main_window)
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
        ms.connect("notify::show-sidebar", lambda *_: self.sidebar_button.set_active(ms.get_show_sidebar()))
        self.sidebar_button.connect("toggled", lambda *_: ms.set_show_sidebar(self.sidebar_button.get_active()))
        self.stack.connect("notify::visible-child", self.view_change_handler)

        self.select_button.connect("toggled", self.select_toggle_handler)
        
        self.select_all_button.connect("clicked", self.select_all_handler)
        self.copy_button.connect("clicked", self.copy_handler)
        self.trash_button.connect("clicked", self.trash_handler)

        self.sort_ascend.connect("clicked", self.sorter)
        self.sort_descend.connect("clicked", self.sorter)
        self.sort_name.connect("clicked", self.sorter)
        self.sort_id.connect("clicked", self.sorter)
        self.sort_size.connect("clicked", self.sorter)

        # Apply again
        self.search_bar.set_key_capture_widget(main_window)
        self.sorter()