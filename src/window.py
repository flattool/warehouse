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

@Gtk.Template(resource_path="/io/github/heliguy4599/Warehouse/window.ui")
class WarehouseWindow(Adw.ApplicationWindow):
    __gtype_name__ = "WarehouseWindow"
    main_window_title = "Warehouse"
    list_of_flatpaks = Gtk.Template.Child()
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

    main_progress_bar = Gtk.ProgressBar(visible=False, pulse_step=0.7)
    main_progress_bar.add_css_class("osd")
    clipboard = Gdk.Display.get_default().get_clipboard()
    host_home = str(pathlib.Path.home())
    user_data_path = host_home + "/.var/app/"
    show_runtimes = False
    in_batch_mode = False
    should_select_all = False
    host_flatpaks = None
    install_success = True
    should_pulse = True
    no_close = None

    def main_pulser(self):
        if self.should_pulse:
            self.main_progress_bar.pulse()
            GLib.timeout_add(500, self.main_pulser)

    def filter_func(self, row):
        if (self.search_entry.get_text().lower() in row.get_title().lower()) or (self.search_entry.get_text().lower() in row.get_subtitle().lower()):
            return True

    def uninstall_flatpak_callback(self, _a, _b):
        self.main_progress_bar.set_visible(False)
        self.should_pulse = False
        self.refresh_list_of_flatpaks(_a, False)
        self.main_toolbar_view.set_sensitive(True)
        self.disconnect(self.no_close)
        if self.my_utils.uninstall_success:
            if self.in_batch_mode:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Uninstalled selected apps")))
            else:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Uninstalled app")))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not uninstall some apps")))

    def uninstall_flatpak_thread(self, ref_arr, id_arr, type_arr, should_trash):
        self.my_utils.uninstallFlatpak(ref_arr, type_arr, should_trash)

    def uninstall_flatpak(self, index_arr, should_trash):
        ref_arr = []
        id_arr = []
        type_arr = []
        for i in range(len(index_arr)):
            ref = self.host_flatpaks[index_arr[i]][8]
            id = self.host_flatpaks[index_arr[i]][2]
            app_type = self.host_flatpaks[index_arr[i]][7]
            ref_arr.append(ref)
            id_arr.append(id)
            type_arr.append(app_type)
        task = Gio.Task.new(None, None, self.uninstall_flatpak_callback)
        task.run_in_thread(lambda _task, _obj, _data, _cancellable, ref_arr=ref_arr, id_arr=id_arr, type_arr=type_arr ,should_trash=should_trash: self.uninstall_flatpak_thread(ref_arr, id_arr, type_arr, should_trash))

    def batch_uninstall_button_handler(self, _widget):
        self.should_pulse = True
        self.main_pulser()

        def batch_uninstall_response(_idk, response_id, _widget):
            if response_id == "cancel":
                self.should_pulse = False
                return 1

            should_trash = False
            if response_id == "purge":
                should_trash = True

            self.main_toolbar_view.set_sensitive(False)
            self.no_close = self.connect("close-request", lambda event: True)  # Make window unable to close
            self.main_progress_bar.set_visible(True)
            self.uninstall_flatpak(self.selected_host_flatpak_indexes, should_trash)

        dialog = Adw.MessageDialog.new(self, _("Uninstall Selected Apps?"), _("The app will be removed from your system. Optionally, you can also trash its user data."))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Uninstall"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.add_response("purge", _("Uninstall and Trash Data"))
        dialog.set_response_appearance("purge", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", batch_uninstall_response, dialog.choose_finish)
        Gtk.Window.present(dialog)

    def uninstall_button_handler(self, _widget, index):
        name = self.host_flatpaks[index][0]
        ref = self.host_flatpaks[index][8]
        id = self.host_flatpaks[index][2]
        self.should_pulse = True
        self.main_pulser()

        def uninstall_response(_idk, response_id, _widget):
            if response_id == "cancel":
                self.should_pulse = False
                return 1

            should_trash = False
            if response_id == "purge":
                should_trash = True

            self.main_toolbar_view.set_sensitive(False)
            self.no_close = self.connect("close-request", lambda event: True)  # Make window unable to close
            self.main_progress_bar.set_visible(True)
            self.uninstall_flatpak([index], should_trash)

        dialog = Adw.MessageDialog.new(self, _("Uninstall {}?").format(name), _("The app will be removed from your system."))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Uninstall"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        if os.path.exists(f"{self.user_data_path}{id}"):
            dialog.set_body(_("The app will be removed from your system. Optionally, you can also trash its user data."))
            dialog.add_response("purge", _("Uninstall and Trash Data"))
            dialog.set_response_appearance("purge", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", uninstall_response, dialog.choose_finish)
        Gtk.Window.present(dialog)

    selected_host_flatpak_indexes = []

    def generate_list_of_flatpaks(self):
        self.set_title(self.main_window_title)
        self.batch_actions_enable(False)
        self.selected_host_flatpak_indexes = []
        self.should_select_all = self.batch_select_all_button.get_active()
        self.main_stack.set_visible_child(self.main_box)












        def get_host_flatpaks():
            output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "list", "--columns=all"], capture_output=True, text=True).stdout
            lines = output.strip().split("\n")
            columns = lines[0].split("\t")
            data = [columns]
            for line in lines[1:]:
                row = line.split("\t")
                data.append(row)
            return data

        self.host_flatpaks = get_host_flatpaks()


        def windowSetEmpty(has_row):
            self.batch_mode_button.set_sensitive(has_row)
            self.search_button.set_sensitive(has_row)

            if has_row:
                self.main_stack.set_visible_child(self.main_box)
            else:
                self.batch_mode_button.set_active(False)
                self.main_stack.set_visible_child(self.no_flatpaks)





        # Setting up filter stuff
        self.show_apps = self.filter_list[0]
        self.show_runtimes = self.filter_list[1]
        self.filter_install_type = self.filter_list[2]
        self.filter_remotes_list = self.filter_list[3]

        for index in range(len(self.host_flatpaks)):
            app_name = self.host_flatpaks[index][0]
            app_id = self.host_flatpaks[index][2]
            app_ref = self.host_flatpaks[index][8]
            flatpak_row = Adw.ActionRow(title=GLib.markup_escape_text(app_name))
            flatpak_row.add_prefix(self.my_utils.findAppIcon(app_id))
            flatpak_row.set_subtitle(app_id)

            # Check the filter and skip row if it does not meet the filter
            if (not self.show_apps) and (not "runtime" in self.host_flatpaks[index][12]):
                continue

            if (not self.show_runtimes) and "runtime" in self.host_flatpaks[index][12]:
                continue

            if (not 'all' in self.filter_install_type) and (not self.host_flatpaks[index][7] in self.filter_install_type):
                continue

            if (not 'all' in self.filter_remotes_list) and (not self.host_flatpaks[index][6] in self.filter_remotes_list):
                continue

            # Change the subtitle from id to ref if the list is set to show runtimes
            if self.show_runtimes:
                flatpak_row.set_subtitle(app_ref)

            properties_button = Gtk.Button(icon_name="info-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("View Properties"))
            properties_button.add_css_class("flat")
            properties_button.connect("clicked", show_properties_window, index, self)
            flatpak_row.add_suffix(properties_button)

            trash_button = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Uninstall {}").format(app_name))
            trash_button.add_css_class("flat")
            trash_button.connect("clicked", self.uninstall_button_handler, index)
            flatpak_row.add_suffix(trash_button)

            select_flatpak_tickbox = Gtk.CheckButton(halign=Gtk.Align.CENTER)
            select_flatpak_tickbox.add_css_class("selection-mode")
            select_flatpak_tickbox.connect("toggled", self.flatpak_row_select_handler, index)
            flatpak_row.add_suffix(select_flatpak_tickbox)

            if self.in_batch_mode:
                trash_button.set_visible(False)
                flatpak_row.set_activatable_widget(select_flatpak_tickbox)
                if self.should_select_all:
                    select_flatpak_tickbox.set_active(True)
                self.batch_mode_bar.set_revealed(True)
            else:
                select_flatpak_tickbox.set_visible(False)
                self.batch_mode_bar.set_revealed(False)

            self.list_of_flatpaks.append(flatpak_row)

        windowSetEmpty(self.list_of_flatpaks.get_row_at_index(0))

    def refresh_list_of_flatpaks(self, widget, should_toast):
        self.list_of_flatpaks.remove_all()
        self.generate_list_of_flatpaks()
        if should_toast:
            self.toast_overlay.add_toast(Adw.Toast.new(_("List refreshed")))

    def batch_mode_handler(self, widget):
        self.batch_select_all_button.set_active(False)
        if widget.get_active():
            self.in_batch_mode = True
            self.list_of_flatpaks.set_margin_bottom(6)
        else:
            self.in_batch_mode = False
            self.list_of_flatpaks.set_margin_bottom(24)
        self.refresh_list_of_flatpaks(None, False)
        self.batch_actions_enable(False)

    def batch_actions_enable(self, should_enable):
        self.batch_copy_button.set_sensitive(should_enable)
        self.batch_clean_button.set_sensitive(should_enable)
        self.batch_uninstall_button.set_sensitive(should_enable)

    def on_batch_clean_response(self, dialog, response, _a):
        if response == "cancel":
            return 1
        show_success = True
        for i in range(len(self.selected_host_flatpak_indexes)):
            app_id = self.host_flatpaks[self.selected_host_flatpak_indexes[i]][2]
            app_name = self.host_flatpaks[self.selected_host_flatpak_indexes[i]][0]
            path = f"{self.user_data_path}{app_id}"
            trash = self.my_utils.trash_folder(None, path)
            if trash == 1:
                show_success = False
                self.toast_overlay.add_toast(Adw.Toast.new(_("No user data for {}").format(app_name)))
            elif trash == 2:
                show_success = False
                self.toast_overlay.add_toast(Adw.Toast.new(_("Can't trash user data for {}").format(app_name)))
        if show_success:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Trashed user data")))
        self.refresh_list_of_flatpaks(_a, False)

    def batch_clean_handler(self, widget):
        dialog = Adw.MessageDialog.new(self, _("Trash Selected Apps' User Data?"), _("This user data will be sent to the trash."))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_batch_clean_response, dialog.choose_finish)
        Gtk.Window.present(dialog)

    def batch_select_all_handler(self, widget):
        self.should_select_all = widget.get_active()
        self.refresh_list_of_flatpaks(widget, False)

    def batch_key_handler(self, _b, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.batch_mode_button.set_active(False)

    def flatpak_row_select_handler(self, tickbox, index):
        if tickbox.get_active():
            self.selected_host_flatpak_indexes.append(index)
        else:
            self.selected_host_flatpak_indexes.remove(index)

        buttons_enable = True
        if len(self.selected_host_flatpak_indexes) == 0:
            buttons_enable = False
            self.set_title(self.main_window_title)
        else:
            self.set_title(f"{len(self.selected_host_flatpak_indexes)} Selected")

        self.batch_actions_enable(buttons_enable)

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
        for i in range(len(self.selected_host_flatpak_indexes)):
            host_flatpak_index = self.selected_host_flatpak_indexes[i]
            to_copy += f"{(self.host_flatpaks[host_flatpak_index][0])}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app names")))

    def copyIDs(self, widget, _a):
        to_copy = ""
        for i in range(len(self.selected_host_flatpak_indexes)):
            host_flatpak_index = self.selected_host_flatpak_indexes[i]
            to_copy += f"{(self.host_flatpaks[host_flatpak_index][2])}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app IDs")))

    def copyRefs(self, widget, _a):
        to_copy = ""
        for i in range(len(self.selected_host_flatpak_indexes)):
            host_flatpak_index = self.selected_host_flatpak_indexes[i]
            to_copy += f"{(self.host_flatpaks[host_flatpak_index][8])}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app refs")))

    def filterWindowHandler(self, widget):
        if widget.get_active():
            filtwin = FilterWindow(self)
            filtwin.present()
        else:
            old_list = self.filter_list
            self.resetFilterList()
            if old_list != self.filter_list:
                self.refresh_list_of_flatpaks(self, False)
                self.toast_overlay.add_toast(Adw.Toast.new(_("Filter reset")))

    def filterWindowKeyboardHandler(self, widget):
        self.filter_button.set_active(not self.filter_button.get_active())

    def resetFilterList(self):
        self.filter_list = [True, False, ["all"], ["all"]]

    def updateFilter(self, filter):
        self.filter_list = filter
        self.refresh_list_of_flatpaks(self, False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(self)
        self.filter_list = []
        self.resetFilterList()

        self.list_of_flatpaks.set_filter_func(self.filter_func)
        self.set_size_request(0, 230)
        self.generate_list_of_flatpaks()
        self.search_entry.connect("search-changed", lambda *_: self.list_of_flatpaks.invalidate_filter())
        self.search_bar.connect_entry(self.search_entry)
        self.refresh_button.connect("clicked", self.refresh_list_of_flatpaks, True)
        self.batch_mode_button.connect("toggled", self.batch_mode_handler)
        self.batch_clean_button.connect("clicked", self.batch_clean_handler)
        self.batch_uninstall_button.connect("clicked", self.batch_uninstall_button_handler)
        self.batch_select_all_button.connect("clicked", self.batch_select_all_handler)
        self.batch_actions_enable(False)
        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.batch_key_handler)
        self.add_controller(event_controller)
        self.main_overlay.add_overlay(self.main_progress_bar)

        self.create_action("copy-names", self.copyNames)
        self.create_action("copy-ids", self.copyIDs)
        self.create_action("copy-refs", self.copyRefs)

        self.filter_button.connect("toggled", self.filterWindowHandler)


