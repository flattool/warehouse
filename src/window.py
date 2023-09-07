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
from .show_properties_window import show_properties_window

@Gtk.Template(resource_path="/io/github/heliguy4599/FlattoolGUI/window.ui")
class FlattoolGuiWindow(Adw.ApplicationWindow):
    __gtype_name__ = "FlattoolGuiWindow"
    main_window_title = "Flattool"
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

    main_progress_bar = Gtk.ProgressBar(visible=False, pulse_step=0.7)
    main_progress_bar.add_css_class("osd")
    clipboard = Gdk.Display.get_default().get_clipboard()
    host_home = str(pathlib.Path.home())
    user_data_path = host_home + "/.var/app/"
    show_runtimes = False
    in_batch_mode = False
    should_select_all = False
    host_flatpaks = None
    uninstall_success = True
    install_success = True
    should_pulse = True

    icon_theme = Gtk.IconTheme.new()
    icon_theme.add_search_path("/var/lib/flatpak/exports/share/icons/")
    icon_theme.add_search_path(host_home + "/.local/share/flatpak/exports/share/icons")

    def main_pulser(self):
        if self.should_pulse:
            self.main_progress_bar.pulse()
            GLib.timeout_add(500, self.main_pulser)

    def filter_func(self, row):
        if (self.search_entry.get_text().lower() in row.get_title().lower()) or (self.search_entry.get_text().lower() in row.get_subtitle().lower()):
            return True

    def trash_folder(self, _a, path):
        if not os.path.exists(path):
            return 1
        try:
            subprocess.run(["flatpak-spawn", "--host", "gio", "trash", path], capture_output=True, check=True)
            return 0
        except subprocess.CalledProcessError:
            return 2

    def get_size_format(self, b):
        factor = 1024
        suffix = "B"
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.1f}{unit}{suffix}"
            b /= factor
        return f"{b:.1f}{suffix}"

    def get_directory_size(self, directory):
        """Returns the `directory` size in bytes."""
        total = 0
        try:
            # print("[+] Getting the size of", directory)
            for entry in os.scandir(directory):
                if entry.is_symlink():
                    continue  # Skip symlinks
                if entry.is_file():
                    # if it's a file, use stat() function
                    total += entry.stat().st_size
                elif entry.is_dir():
                    # if it's a directory, recursively call this function
                    try:
                        total += self.get_directory_size(entry.path)
                    except FileNotFoundError:
                        pass
        except NotADirectoryError:
            # if `directory` isn't a directory, get the file size then
            return os.path.getsize(directory)
        except PermissionError:
            # if for whatever reason we can't open the folder, return 0
            return 0
        return total

    def uninstall_response(self, widget, response_id, _c, index):
        app_id = self.host_flatpaks[index][2]
        ref = self.host_flatpaks[index][8]
        name = self.host_flatpaks[index][0]
        command = ["flatpak-spawn", "--host", "flatpak", "remove", ref, "-y"]
        if response_id == "cancel":
            self.should_pulse = False
            return 1
        if response_id == "purge":
            subprocess.run(['flatpak-spawn', '--host', 'gio', 'trash', f"{self.user_data_path}{app_id}"])

        handler_id = self.connect('close-request', lambda event: True) # Make window unable to close
        self.main_progress_bar.set_visible(True)
        self.main_toolbar_view.set_sensitive(False)

        def uninstall_callback(*_args):
            if self.uninstall_success:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Uninstalled {}").format(name)))
            else:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Could not uninstall {}").format(name)))
            
            self.main_progress_bar.set_visible(False)
            self.should_pulse = False
            self.refresh_list_of_flatpaks(None, False)
            self.disconnect(handler_id)
            self.main_toolbar_view.set_sensitive(True)

        def thread_func(*_args):
            try:
                subprocess.run(command, capture_output=True, check=True)
            except subprocess.CalledProcessError:
                self.uninstall_success = False

        task = Gio.Task.new(None, None, uninstall_callback)
        task.run_in_thread(thread_func)

    def uninstall_flatpak(self, _widget, index):
        self.should_pulse = True
        self.main_pulser()
        self.uninstall_success = True
        name = self.host_flatpaks[index][0]
        id = self.host_flatpaks[index][2]
        dialog = Adw.MessageDialog.new(self, _("Uninstall {}?").format(name), _("The app will be removed from your system."))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Uninstall"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)

        if os.path.exists(f"{self.user_data_path}{id}"):
            dialog.set_body(_("The app will be removed from your system. Optionally, you can also trash its user data."))
            dialog.add_response("purge", _("Uninstall and Trash Data"))
            dialog.set_response_appearance("purge", Adw.ResponseAppearance.DESTRUCTIVE)

        dialog.connect("response", self.uninstall_response, dialog.choose_finish, index)
        Gtk.Window.present(dialog)

    
    selected_host_flatpak_indexes = []

    def find_app_icon(self, app_id):
        try:
            icon_path = (self.icon_theme.lookup_icon(app_id, None, 512, 1, self.get_direction(), 0).get_file().get_path())
        except GLib.GError:
            icon_path = None
        if icon_path:
            image = Gtk.Image.new_from_file(icon_path)
            image.set_icon_size(Gtk.IconSize.LARGE)
            image.add_css_class("icon-dropshadow")
        else:
            image = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
            image.set_icon_size(Gtk.IconSize.LARGE)
        return image

    def generate_list_of_flatpaks(self):
        self.set_title(self.main_window_title)
        self.batch_actions_enable(False)
        self.selected_host_flatpak_indexes = []
        self.should_select_all = self.batch_select_all_button.get_active()

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
        if self.host_flatpaks == [[""]]:
            self.main_stack.set_visible_child(self.no_flatpaks)
            self.search_button.set_visible(False)
            self.search_bar.set_visible(False)
            self.batch_mode_button.set_visible(False)
            return

        for index in range(len(self.host_flatpaks)):
            app_name = self.host_flatpaks[index][0]
            app_id = self.host_flatpaks[index][2]
            app_ref = self.host_flatpaks[index][8]
            flatpak_row = Adw.ActionRow(title=GLib.markup_escape_text(app_name), subtitle=app_ref)
            flatpak_row.add_prefix(self.find_app_icon(app_id))

            if (not self.show_runtimes) and "runtime" in self.host_flatpaks[index][12]:
                continue

            if os.path.exists(f"{self.user_data_path}{app_id}"):
                has_data_icon = Gtk.Image.new_from_icon_name("paper-filled-symbolic")
                has_data_icon.set_tooltip_text("This App Has User Data")
                has_data_icon.set_opacity(0.5)
                has_data_icon.set_margin_end(10)
                flatpak_row.add_suffix(has_data_icon)

            trash_button = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Uninstall {}").format(app_name))
            trash_button.add_css_class("flat")
            trash_button.connect("clicked", self.uninstall_flatpak, index)
            flatpak_row.add_suffix(trash_button)

            properties_button = Gtk.Button(icon_name="info-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("View Properties"))
            properties_button.add_css_class("flat")
            properties_button.connect("clicked", show_properties_window, index, self)
            flatpak_row.add_suffix(properties_button)

            select_flatpak_tickbox = Gtk.CheckButton(halign=Gtk.Align.CENTER)
            select_flatpak_tickbox.add_css_class("flat")
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

    def refresh_list_of_flatpaks(self, widget, should_toast):
        self.list_of_flatpaks.remove_all()
        self.generate_list_of_flatpaks()
        if should_toast:
            self.toast_overlay.add_toast(Adw.Toast.new(_("List refreshed")))

    def show_runtimes_toggle_handler(self, state):
        if state:
            self.show_runtimes = True
        else:
            self.show_runtimes = False
        self.refresh_list_of_flatpaks(None, False)
        self.selected_host_flatpak_indexes.clear()

    def batch_mode_handler(self, widget):
        self.batch_select_all_button.set_active(False)
        if widget.get_active():
            self.in_batch_mode = True
        else:
            self.in_batch_mode = False
        self.refresh_list_of_flatpaks(None, False)
        self.batch_actions_enable(False)

    def batch_actions_enable(self, should_enable):
        self.batch_copy_button.set_sensitive(should_enable)
        self.batch_clean_button.set_sensitive(should_enable)
        self.batch_uninstall_button.set_sensitive(should_enable)

    def batch_copy_handler(self, widget):
        to_copy = ""
        for i in range(len(self.selected_host_flatpak_indexes)):
            host_flatpak_index = self.selected_host_flatpak_indexes[i]
            to_copy += f"{(self.host_flatpaks[host_flatpak_index][2])}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app IDs")))

    def on_batch_clean_response(self, dialog, response, _a):
        if response == "cancel":
            return 1
        show_success = True
        for i in range(len(self.selected_host_flatpak_indexes)):
            app_id = self.host_flatpaks[self.selected_host_flatpak_indexes[i]][2]
            app_name = self.host_flatpaks[self.selected_host_flatpak_indexes[i]][0]
            path = f"{self.user_data_path}{app_id}"
            trash = self.trash_folder(None, path)
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
        dialog = Adw.MessageDialog.new(self, _("Delete Selected User Data?"), _("This user data will be sent to the trash."))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_batch_clean_response, dialog.choose_finish)
        Gtk.Window.present(dialog)

    def batch_select_all_handler(self, widget):
        self.should_select_all = widget.get_active()
        self.refresh_list_of_flatpaks(widget, False)

    def batch_uninstall_on_response(self, widget, response_id, _c):
        total_to_uninstall = len(self.selected_host_flatpak_indexes)
        delete_data = False
        if response_id == "cancel":
            self.should_pulse = False
            return 1
        if response_id == "purge":
            delete_data = True

        handler_id = self.connect('close-request', lambda event: True) # Make window unable to close
        self.main_toolbar_view.set_sensitive(False)
        self.main_progress_bar.set_visible(True)
        def batch_thread_func(command):
            try:
                subprocess.run(command, capture_output=False, check=True)
            except subprocess.CalledProcessError:
                self.uninstall_success = False

        def batch_uninstall_callback(*_args):
            nonlocal total_to_uninstall
            total_to_uninstall = total_to_uninstall - 1
            if total_to_uninstall == 0:
                if self.uninstall_success:
                    self.toast_overlay.add_toast(Adw.Toast.new(_("Uninstalled all apps")))
                else:
                    self.toast_overlay.add_toast(Adw.Toast.new(_("Some apps didn't uninstall")))
        
                self.main_progress_bar.set_visible(False)
                self.should_pulse = False
                self.main_progress_bar.set_visible(False)
                self.refresh_list_of_flatpaks(None, False)
                self.disconnect(handler_id)
                self.main_toolbar_view.set_sensitive(True)
            
        for i in range(len(self.selected_host_flatpak_indexes)):
            app_id = self.host_flatpaks[self.selected_host_flatpak_indexes[i]][2]
            ref = self.host_flatpaks[self.selected_host_flatpak_indexes[i]][8]
            name = self.host_flatpaks[self.selected_host_flatpak_indexes[i]][0]
            command = ["flatpak-spawn", "--host", "flatpak", "remove", ref, "-y"]
            if delete_data:
                subprocess.run(['flatpak-spawn', '--host', 'gio', 'trash', f"{self.user_data_path}{app_id}"])

            '''try:
                subprocess.run(command, capture_output=False, check=True)
            except subprocess.CalledProcessError:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Can't uninstall {}").format(name)))'''

            task = Gio.Task.new(None, None, batch_uninstall_callback)
            task.run_in_thread(lambda _task, _obj, _data, _cancellable, cmd=command: batch_thread_func(cmd))

    def batch_uninstall_handler(self, widget):
        self.should_pulse = True
        self.main_pulser()
        self.uninstall_success = True
        dialog = Adw.MessageDialog.new(self, _("Uninstall Selected Apps?"), _("Optionally, you can also trash their user data"))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Uninstall"))
        dialog.add_response("purge", _("Uninstall and Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_response_appearance("purge", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.batch_uninstall_on_response, dialog.choose_finish)
        Gtk.Window.present(dialog)

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.list_of_flatpaks.set_filter_func(self.filter_func)
        self.generate_list_of_flatpaks()
        self.search_entry.connect("search-changed", lambda *_: self.list_of_flatpaks.invalidate_filter())
        self.search_bar.connect_entry(self.search_entry)
        self.refresh_button.connect("clicked", self.refresh_list_of_flatpaks, True)
        self.batch_mode_button.connect("toggled", self.batch_mode_handler)
        self.batch_copy_button.connect("clicked", self.batch_copy_handler)
        self.batch_clean_button.connect("clicked", self.batch_clean_handler)
        self.batch_clean_button.add_css_class("destructive-action")
        self.batch_uninstall_button.connect("clicked", self.batch_uninstall_handler)
        self.batch_uninstall_button.add_css_class("destructive-action")
        self.batch_select_all_button.connect("clicked", self.batch_select_all_handler)
        self.batch_actions_enable(False)
        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.batch_key_handler)
        self.add_controller(event_controller)
        self.main_overlay.add_overlay(self.main_progress_bar)
