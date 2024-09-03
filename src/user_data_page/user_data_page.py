from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .error_toast import ErrorToast
from .data_box import DataBox
from .data_subpage import DataSubpage
from .host_info import HostInfo
from .sidebar_button import SidebarButton
import os, subprocess

import time

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/user_data_page.ui")
class UserDataPage(Adw.BreakpointBin):
    __gtype_name__ = 'UserDataPage'
    gtc = Gtk.Template.Child
    bpt = gtc()
    header_bar = gtc()
    switcher_bar = gtc()
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
    page_name = "user-data"

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
        self.header_bar.set_sensitive(False)
        self.search_button.set_active(False)
        self.search_entry.set_editable(False)
        self.select_button.set_active(False)
        self.adp.set_visible_child(self.adp.loading_data)
        self.adp.size_label.set_label("Loading Size")
        self.adp.spinner.set_visible(True)
        self.ldp.set_visible_child(self.ldp.loading_data)
        self.ldp.size_label.set_label("Loading Size")
        self.ldp.spinner.set_visible(True)

    def end_loading(self, *args):
        def callback(*args):
            self.adp.generate_list(self.data_flatpaks, self.active_data)
            self.ldp.generate_list([], self.leftover_data)
            self.header_bar.set_sensitive(True)
            self.search_entry.set_editable(True)
        
        Gio.Task.new(None, None, callback).run_in_thread(self.sort_data)

    def sort_button_handler(self, button):
        if button in {self.sort_ascend, self.sort_descend}:
            self.settings.set_boolean("sort-ascend", self.sort_ascend.get_active())
        else:
            self.settings.set_string("sort-mode", self.buttons_to_sort_modes[button])

        self.adp.update_sort_mode()
        self.ldp.update_sort_mode()

    def load_sort_settings(self):
        mode = self.settings.get_string("sort-mode")
        ascend = self.settings.get_boolean("sort-ascend")
        self.sort_modes_to_buttons[mode].set_active(True)
        (self.sort_ascend if ascend else self.sort_descend).set_active(True)
        self.adp.update_sort_mode()
        self.ldp.update_sort_mode()

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

        def on_response(dialog, response):
            if response != "continue":
                return
                
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

        dialog = Adw.AlertDialog(heading=_("Trash Data?"), body=_("Data will be sent to the trash"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Continue"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response)
        dialog.present(ErrorToast.main_window)
        
    def breakpoint_handler(self, bpt, is_applied):
        self.adp.label_box.set_orientation(Gtk.Orientation.VERTICAL if is_applied else Gtk.Orientation.HORIZONTAL)
        self.ldp.label_box.set_orientation(Gtk.Orientation.VERTICAL if is_applied else Gtk.Orientation.HORIZONTAL)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.__class__.instance = self
        self.adp = DataSubpage(_("Active Data"), self, True, main_window)
        self.ldp = DataSubpage(_("Leftover Data"), self, False, main_window)
        self.data_flatpaks = []
        self.active_data = []
        self.leftover_data = []
        self.total_items = 0
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse.data_page")

        self.sort_modes_to_buttons = {
            "name": self.sort_name,
            "id": self.sort_id,
            "size": self.sort_size,
        }
        self.buttons_to_sort_modes = {}
        for key, button in self.sort_modes_to_buttons.items():
            self.buttons_to_sort_modes[button] = key

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

        # Connections
        self.stack.connect("notify::visible-child", self.view_change_handler)
        self.select_button.connect("toggled", self.select_toggle_handler)
        self.select_all_button.connect("clicked", self.select_all_handler)
        self.copy_button.connect("clicked", self.copy_handler)
        self.trash_button.connect("clicked", self.trash_handler)
        self.sort_ascend.connect("clicked", self.sort_button_handler)
        self.sort_descend.connect("clicked", self.sort_button_handler)
        self.sort_name.connect("clicked", self.sort_button_handler)
        self.sort_id.connect("clicked", self.sort_button_handler)
        self.sort_size.connect("clicked", self.sort_button_handler)
        self.bpt.connect("apply", self.breakpoint_handler, True)
        self.bpt.connect("unapply", self.breakpoint_handler, False)

        # Apply again
        self.search_bar.set_key_capture_widget(main_window)
        self.load_sort_settings()
