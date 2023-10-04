# window.py
#
# Copyright 2023 Heliguy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-only

import os
import pathlib
import subprocess

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from .properties_window import show_properties_window
from .filter_window import FilterWindow
from .common import myUtils

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/window.ui")
class WarehouseWindow(Adw.ApplicationWindow):
    __gtype_name__ = "WarehouseWindow"
    main_window_title = "Warehouse"
    flatpaks_list_box = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    refresh_button = Gtk.Template.Child()
    no_flatpaks = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    batch_mode_button = Gtk.Template.Child()
    batch_mode_bar = Gtk.Template.Child()
    batch_select_all_button = Gtk.Template.Child()
    batch_uninstall_button = Gtk.Template.Child()
    batch_clean_button = Gtk.Template.Child()
    batch_copy_button = Gtk.Template.Child()
    main_box = Gtk.Template.Child()
    main_overlay = Gtk.Template.Child()
    main_toolbar_view = Gtk.Template.Child()
    filter_button = Gtk.Template.Child()

    main_progress_bar = Gtk.ProgressBar(visible=False, pulse_step=0.7, can_target=False)
    main_progress_bar.add_css_class("osd")
    clipboard = Gdk.Display.get_default().get_clipboard()
    host_home = str(pathlib.Path.home())
    user_data_path = host_home + "/.var/app/"
    in_batch_mode = False
    should_select_all = False
    host_flatpaks = None
    install_success = True
    should_pulse = True
    no_close = None
    re_get_flatpaks = False
    currently_uninstalling = False
    selected_rows = []
    flatpak_rows = []
    # ^ {Row visibility, Row selected, the row itself, properties, trash, select, the flatpak row from `flatpak list`}

    def mainPulser(self):
        if self.should_pulse:
            self.main_progress_bar.pulse()
            GLib.timeout_add(500, self.mainPulser)

    def filter_func(self, row):
        if (self.search_entry.get_text().lower() in row.get_title().lower()) or (self.search_entry.get_text().lower() in row.get_subtitle().lower()):
            return True

    def removeRow(self, row):
        row[5].set_active(False)
        row[0] = False
        row[2].set_visible(False)

    def uninstallButtonsEnable(self, should_enable):
        if self.currently_uninstalling:
            return
        self.refresh_button.set_sensitive(should_enable)
        for i in range(len(self.flatpak_rows)):
            self.flatpak_rows[i][4].set_sensitive(should_enable)
        if not should_enable:
            self.batch_uninstall_button.set_sensitive(False)

    def uninstallFlatpakCallback(self, _a, _b):
        self.currently_uninstalling = False
        self.main_progress_bar.set_visible(False)
        self.should_pulse = False
        self.refresh_list_of_flatpaks(_a, False)
        self.main_toolbar_view.set_sensitive(True)
        self.disconnect(self.no_close)
        self.uninstallButtonsEnable(True)
        if self.my_utils.uninstall_success:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Uninstalled successfully")))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not uninstall some apps")))

    def uninstallFlatpakThread(self, ref_arr, id_arr, type_arr, should_trash):
        self.my_utils.uninstallFlatpak(ref_arr, type_arr, should_trash)

    def uninstallFlatpak(self, should_trash):
        ref_arr = []
        id_arr = []
        type_arr = []
        self.currently_uninstalling = True
        for i in range(len(self.flatpak_rows)):
            if not self.flatpak_rows[i][1]:
                continue # Skip if not selected
            ref = self.flatpak_rows[i][6][8]
            id = self.flatpak_rows[i][6][2]
            app_type = self.flatpak_rows[i][6][7]
            ref_arr.append(ref)
            id_arr.append(id)
            type_arr.append(app_type)
            self.removeRow(self.flatpak_rows[i])
        task = Gio.Task.new(None, None, self.uninstallFlatpakCallback)
        task.run_in_thread(lambda _task, _obj, _data, _cancellable, ref_arr=ref_arr, id_arr=id_arr, type_arr=type_arr ,should_trash=should_trash: self.uninstallFlatpakThread(ref_arr, id_arr, type_arr, should_trash))

    def batchUninstallButtonHandler(self, _widget):
        self.should_pulse = True
        self.mainPulser()
        has_user_data = [] # This is only an array so I can edit it in a sub-function without using nonlocal prefix

        def batchUninstallResponse(_idk, response_id, _widget):
            if response_id == "cancel":
                self.should_pulse = False
                return 1                    

            try:
                should_trash = trash_check.get_active()
            except:
                should_trash = False

            #self.main_toolbar_view.set_sensitive(False)

            self.uninstallButtonsEnable(False)

            self.no_close = self.connect("close-request", lambda event: True)  # Make window unable to close
            self.main_progress_bar.set_visible(True)
            self.uninstallFlatpak(should_trash)

        # Create Widgets
        dialog = Adw.MessageDialog.new(self, _("Uninstall Selected Apps?"), _("It will not be possible to use these apps after removal."))

        # Check to see if at least one app in the list has user data
        for i in range(len(self.flatpak_rows)):
            if not self.flatpak_rows[1]:
                continue # Skip if not selected
            if os.path.exists(f"{self.user_data_path}{self.flatpak_rows[i][6][2]}"):
                has_user_data.append(True)
                break

        if len(has_user_data) > 0:
            # Create Widgets
            options_box = Gtk.Box(orientation="vertical")
            header = Gtk.Label(label=_("App Settings & Data"), halign="start", margin_top=10)
            options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
            keep_data = Adw.ActionRow(title=_("Keep"), subtitle=_("Allow restoring app settings and content"))
            trash_data = Adw.ActionRow(title=_("Trash"), subtitle=_("Send app settings and content to the trash"))
            keep_check = Gtk.CheckButton()
            trash_check = Gtk.CheckButton()

            # Apply Widgets
            keep_data.add_prefix(keep_check)
            keep_data.set_activatable_widget(keep_check)
            trash_data.add_prefix(trash_check)
            trash_data.set_activatable_widget(trash_check)
            keep_check.set_group(trash_check)
            options_list.append(keep_data)
            options_list.append(trash_data)
            options_box.append(header)
            options_box.append(options_list)
            dialog.set_extra_child(options_box)

            # Calls
            keep_check.set_active(True)
            options_list.add_css_class("boxed-list")
            header.add_css_class("heading")
            header.add_css_class("h4")

        # Connections
        dialog.connect("response", batchUninstallResponse, dialog.choose_finish)

        # Calls
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Uninstall"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        Gtk.Window.present(dialog)

    def uninstallButtonHandler(self, _widget, index):
        name = self.host_flatpaks[index][0]
        ref = self.host_flatpaks[index][8]
        id = self.host_flatpaks[index][2]
        self.should_pulse = True
        self.mainPulser()
        self.flatpak_rows[index][1] = True

        def uninstallResponse(_idk, response_id, _widget):
            try:
                should_trash = trash_check.get_active()
            except:
                should_trash = False
            
            if response_id == "cancel":
                self.should_pulse = False
                return 1

            if response_id == "purge":
                should_trash = True

            self.uninstallButtonsEnable(False)

            #self.main_toolbar_view.set_sensitive(False)
            self.no_close = self.connect("close-request", lambda event: True)  # Make window unable to close
            self.main_progress_bar.set_visible(True)
            self.uninstallFlatpak(should_trash)

        # Create Widgets
        dialog = Adw.MessageDialog.new(self, _("Uninstall {}?").format(name), _("It will not be possible to use {} after removal.").format(name))

        if os.path.exists(f"{self.user_data_path}{id}"):
            # Create Widgets for Trash
            options_box = Gtk.Box(orientation="vertical")
            header = Gtk.Label(label=_("App Settings & Data"), halign="start", margin_top=10)
            options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
            keep_data = Adw.ActionRow(title=_("Keep"), subtitle=_("Allow restoring app settings and content"))
            trash_data = Adw.ActionRow(title=_("Trash"), subtitle=_("Send app settings and content to the trash"))
            keep_check = Gtk.CheckButton(active=True)
            trash_check = Gtk.CheckButton()

            # Apply Widgets for Trash
            keep_data.add_prefix(keep_check)
            keep_data.set_activatable_widget(keep_check)
            trash_data.add_prefix(trash_check)
            trash_data.set_activatable_widget(trash_check)
            keep_check.set_group(trash_check)
            dialog.set_extra_child(options_box)
            options_list.append(keep_data)
            options_list.append(trash_data)
            options_box.append(header)
            options_box.append(options_list)
            options_list.add_css_class("boxed-list")

        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Uninstall"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", uninstallResponse, dialog.choose_finish)
        Gtk.Window.present(dialog)

    def windowSetEmpty(self, is_empty):
        self.batch_mode_button.set_sensitive(not is_empty)
        self.search_button.set_sensitive(not is_empty)
        self.filter_button.set_sensitive(not is_empty)

        if is_empty:
            self.batch_mode_button.set_active(False)
            self.main_stack.set_visible_child(self.no_flatpaks)
        else:
            self.main_stack.set_visible_child(self.main_box)
    
    def generate_list_of_flatpaks(self):
        self.set_title(self.main_window_title)
        self.flatpak_rows = []
        self.should_select_all = self.batch_select_all_button.get_active()
        self.main_stack.set_visible_child(self.main_box)
        self.batch_select_all_button.set_active(False)
        self.eol_list = []

        for index in range(len(self.host_flatpaks)):
            if "eol" in self.host_flatpaks[index][12]:
                self.eol_list.append(self.host_flatpaks[index][8])

        for index in range(len(self.host_flatpaks)):
            app_name = self.host_flatpaks[index][0]
            app_id = self.host_flatpaks[index][2]
            app_ref = self.host_flatpaks[index][8]
            flatpak_row = Adw.ActionRow(title=GLib.markup_escape_text(app_name))
            flatpak_row.add_prefix(self.my_utils.findAppIcon(app_id))
            flatpak_row.set_subtitle(app_id)

            if "eol" in self.host_flatpaks[index][12]:
                eol_runtime_label = Gtk.Label(label=_("Flatpak EOL"), tooltip_text=_("This Flatpak has reached its End of Life and will not receive any security updates"))
                eol_runtime_label.add_css_class("subtitle")
                eol_runtime_label.add_css_class("error")
                flatpak_row.add_suffix(eol_runtime_label)

            if self.host_flatpaks[index][13] in self.eol_list:
                eol_app_label = Gtk.Label(label=_("Runtime EOL"), tooltip_text=_("The runtime used by this app has reached its End of Life and will not receive any security updates"))
                eol_app_label.add_css_class("subtitle")
                eol_app_label.add_css_class("error")
                flatpak_row.add_suffix(eol_app_label)

            properties_button = Gtk.Button(icon_name="info-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("View Properties"))
            properties_button.add_css_class("flat")
            properties_button.connect("clicked", show_properties_window, index, self)
            flatpak_row.add_suffix(properties_button)

            trash_button = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Uninstall {}").format(app_name), visible=not self.in_batch_mode)
            trash_button.add_css_class("flat")
            trash_button.connect("clicked", self.uninstallButtonHandler, index)
            flatpak_row.add_suffix(trash_button)

            select_flatpak_tickbox = Gtk.CheckButton(visible=self.in_batch_mode)
            select_flatpak_tickbox.add_css_class("selection-mode")
            select_flatpak_tickbox.connect("toggled", self.rowSelectHandler, index)
            flatpak_row.add_suffix(select_flatpak_tickbox)

            if self.in_batch_mode:
                flatpak_row.set_activatable_widget(select_flatpak_tickbox)

            self.flatpaks_list_box.append(flatpak_row)
            #                         {Row visibility, Row selected, the row itself, properties, trash, select, the flatpak row from `flatpak list`}
            self.flatpak_rows.append([True, False, flatpak_row, properties_button, trash_button, select_flatpak_tickbox, self.host_flatpaks[index]])

        self.windowSetEmpty(not self.flatpaks_list_box.get_row_at_index(0))
        self.applyFilter(self.filter_list)
        self.batchActionsEnable(False)

    def refresh_list_of_flatpaks(self, widget, should_toast):
        if self.currently_uninstalling:
            return
        self.flatpaks_list_box.remove_all()
        self.host_flatpaks = self.my_utils.getHostFlatpaks()
        self.generate_list_of_flatpaks()
        if should_toast:
            self.toast_overlay.add_toast(Adw.Toast.new(_("List refreshed")))

    def batch_mode_handler(self, widget):
        for i in range(len(self.flatpak_rows)):
            adw_row = self.flatpak_rows[i][2]
            trash_button = self.flatpak_rows[i][4]
            select_tick = self.flatpak_rows[i][5]

            select_tick.set_visible(widget.get_active())
            trash_button.set_visible(not widget.get_active())

            if widget.get_active():
                adw_row.set_activatable(True)
                adw_row.set_activatable_widget(select_tick)
            else:
                select_tick.set_active(False)
                adw_row.set_activatable(False)

        self.in_batch_mode = widget.get_active()
        self.batch_mode_bar.set_revealed(widget.get_active())

        if widget.get_active():
            self.flatpaks_list_box.set_margin_bottom(6)
        else:
            self.flatpaks_list_box.set_margin_bottom(24)
            self.batch_select_all_button.set_active(False)

    def batchActionsEnable(self, should_enable):
        self.batch_copy_button.set_sensitive(should_enable)
        self.batch_clean_button.set_sensitive(should_enable)
        if not self.currently_uninstalling:
            self.batch_uninstall_button.set_sensitive(should_enable)

    def onBatchCleanResponse(self, dialog, response, _a):
        if response == "cancel":
            return 1
        show_success = True
        for i in range(len(self.flatpak_rows)):
            if not self.flatpak_rows[i][1]:
                continue # Skip if not selected
            app_id = self.flatpak_rows[i][6][2]
            app_name = self.flatpak_rows[i][6][0]
            path = f"{self.user_data_path}{app_id}"
            trash = self.my_utils.trashFolder(path)
            if trash == 1:
                show_success = False
                self.toast_overlay.add_toast(Adw.Toast.new(_("No user data for {}").format(app_name)))
            elif trash == 2:
                show_success = False
                self.toast_overlay.add_toast(Adw.Toast.new(_("Can't trash user data for {}").format(app_name)))
        if show_success:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Trashed user data")))
        #self.refresh_list_of_flatpaks(_a, False)

    def batchCleanHandler(self, widget):
        dialog = Adw.MessageDialog.new(self, _("Trash Selected Apps' User Data?"), _("Your user files and data for these apps will be sent to the trash."))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.onBatchCleanResponse, dialog.choose_finish)
        Gtk.Window.present(dialog)

    def batchSelectAllHandler(self, widget):
        for i in range(len(self.flatpak_rows)):
            if self.flatpak_rows[i][0]:
                self.flatpak_rows[i][5].set_active(widget.get_active())

    def batchKeyHandler(self, _b, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.batch_mode_button.set_active(False)

    def rowSelectHandler(self, tickbox, index):
        self.flatpak_rows[index][1] = tickbox.get_active()

        total_selected = 0
        for i in range(len(self.flatpak_rows)):
            if self.flatpak_rows[i][1]:
                total_selected += 1

        if total_selected == 0:
            buttons_enable = False
            self.set_title(self.main_window_title)
            self.batchActionsEnable(False)
        else:
            self.set_title(f"{total_selected} Selected")
            self.batchActionsEnable(True)

    def create_action(self, name, callback, shortcuts=None):
        """Add a window action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def copyNames(self, widget, _a):
        to_copy = ""
        for i in range(len(self.flatpak_rows)):
            if self.flatpak_rows[i][1]:
                to_copy += f"{(self.flatpak_rows[i][6][0])}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app names")))

    def copyIDs(self, widget, _a):
        to_copy = ""
        for i in range(len(self.flatpak_rows)):
            if self.flatpak_rows[i][1]:
                to_copy += f"{(self.flatpak_rows[i][6][2])}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app IDs")))

    def copyRefs(self, widget, _a):
        to_copy = ""
        for i in range(len(self.flatpak_rows)):
            if self.flatpak_rows[i][1]:
                to_copy += f"{(self.flatpak_rows[i][6][8])}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app refs")))

    def filterWindowHandler(self, widget):
        for i in range(len(self.flatpak_rows)):
            self.flatpak_rows[i][5].set_active(False)
        self.batch_select_all_button.set_active(False)
        if widget.get_active():
            filtwin = FilterWindow(self)
            filtwin.present()
        else:
            self.applyFilter()

    def filterWindowKeyboardHandler(self, widget):
        self.filter_button.set_active(not self.filter_button.get_active())

    def resetFilterList(self):
        self.filter_list = [True, False, ["all"], ["all"]]

    def applyFilter(self, filter=[True, False, ["all"], ["all"]]):
        self.filter_list = filter
        show_apps = filter[0]
        show_runtimes = filter[1]
        filter_install_type = filter[2]
        filter_remotes_list = filter[3]
        total_visible = 0

        for i in range(len(self.flatpak_rows)):
            self.flatpak_rows[i][0] = True

            if (not show_apps) and (not "runtime" in self.flatpak_rows[i][6][12]):
                self.flatpak_rows[i][0] = False

            if (not show_runtimes) and "runtime" in self.flatpak_rows[i][6][12]:
                self.flatpak_rows[i][0] = False

            if (not 'all' in filter_install_type) and (not self.host_flatpaks[i][7] in filter_install_type):
                self.flatpak_rows[i][0] = False

            if (not 'all' in filter_remotes_list) and (not self.host_flatpaks[i][6] in filter_remotes_list):
                self.flatpak_rows[i][0] = False

            self.flatpak_rows[i][2].set_visible(self.flatpak_rows[i][0])

            if self.flatpak_rows[i][0]:
                total_visible += 1

        if total_visible > 0:
            #self.main_stack.set_visible_child(self.main_box)
            self.windowSetEmpty(False)
        else:
            # self.main_stack.set_visible_child(self.no_flatpaks)
            self.windowSetEmpty(True)
            self.filter_button.set_sensitive(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(self)
        self.filter_list = [True, False, ["all"], ["all"]]
        self.host_flatpaks = self.my_utils.getHostFlatpaks()
        self.set_size_request(0, 230)
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse")
        self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-fullscreen", self, "fullscreened", Gio.SettingsBindFlags.DEFAULT)

        if self.host_flatpaks == [['', '']]:
            self.windowSetEmpty(True)
            return

        self.flatpaks_list_box.set_filter_func(self.filter_func)
        self.generate_list_of_flatpaks()
        self.search_entry.connect("search-changed", lambda *_: self.flatpaks_list_box.invalidate_filter())
        self.search_bar.connect_entry(self.search_entry)
        self.refresh_button.connect("clicked", self.refresh_list_of_flatpaks, True)
        self.batch_mode_button.connect("toggled", self.batch_mode_handler)
        self.batch_clean_button.connect("clicked", self.batchCleanHandler)
        self.batch_uninstall_button.connect("clicked", self.batchUninstallButtonHandler)
        self.batch_select_all_button.connect("clicked", self.batchSelectAllHandler)
        self.batchActionsEnable(False)
        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.batchKeyHandler)
        self.add_controller(event_controller)
        self.main_overlay.add_overlay(self.main_progress_bar)

        self.create_action("copy-names", self.copyNames)
        self.create_action("copy-ids", self.copyIDs)
        self.create_action("copy-refs", self.copyRefs)

        self.filter_button.connect("toggled", self.filterWindowHandler)



