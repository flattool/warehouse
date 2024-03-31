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
import re
import time

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
# from .properties_window import PropertiesWindow
from .filter_window import FilterWindow
from .common import myUtils
from .remotes_window import RemotesWindow
from .downgrade_window import DowngradeWindow
from .snapshots_window import SnapshotsWindow
from .const import Config

from .app_row_widget import AppRow


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/../data/ui/window.ui")
class WarehouseWindow(Adw.ApplicationWindow):
    __gtype_name__ = "WarehouseWindow"
    main_window_title = "Warehouse"
    flatpaks_list_box = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    no_flatpaks = Gtk.Template.Child()
    no_results = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    batch_mode_button = Gtk.Template.Child()
    batch_mode_bar = Gtk.Template.Child()
    batch_select_all_button = Gtk.Template.Child()
    batch_uninstall_button = Gtk.Template.Child()
    batch_clean_button = Gtk.Template.Child()
    batch_copy_button = Gtk.Template.Child()
    batch_snapshot_button = Gtk.Template.Child()
    main_box = Gtk.Template.Child()
    main_overlay = Gtk.Template.Child()
    main_toolbar_view = Gtk.Template.Child()
    filter_button = Gtk.Template.Child()
    scrolled_window = Gtk.Template.Child()
    main_menu = Gtk.Template.Child()
    installing = Gtk.Template.Child()
    uninstalling = Gtk.Template.Child()
    snapshotting = Gtk.Template.Child()
    loading_flatpaks = Gtk.Template.Child()
    no_matches = Gtk.Template.Child()
    reset_filters_button = Gtk.Template.Child()
    uninstalling_status = Gtk.Template.Child()
    refreshing = Gtk.Template.Child()

    main_progress_bar = Gtk.ProgressBar(visible=False, can_target=False)
    main_progress_bar.add_css_class("osd")
    clipboard = Gdk.Display.get_default().get_clipboard()
    host_home = str(pathlib.Path.home())
    user_data_path = host_home + "/.var/app/"
    in_batch_mode = False
    should_select_all = False
    host_flatpaks = None
    install_success = True
    no_close = None
    re_get_flatpaks = False
    currently_uninstalling = False
    is_result = False
    is_empty = False
    total_selected = 0

    def filter_func(self, row):
        if (self.search_entry.get_text().lower() in row.get_title().lower()) or (
            self.search_entry.get_text().lower() in row.get_subtitle().lower()
        ):
            self.is_result = True
            return True

    def uninstall_buttons_enable(self, should_enable):
        if self.currently_uninstalling:
            return
        if not should_enable:
            self.batch_uninstall_button.set_sensitive(False)

    def uninstall_flatpak_callback(self, _a, _b):
        self.currently_uninstalling = False
        self.refresh_list_of_flatpaks(_a)
        self.main_toolbar_view.set_sensitive(True)
        self.disconnect(self.no_close)
        self.uninstall_buttons_enable(True)
        self.main_stack.set_visible_child(self.main_box)
        self.search_button.set_sensitive(True)
        self.batch_actions_enable(False)
        if self.my_utils.uninstall_success:
            self.refresh_list_of_flatpaks(self)
            self.toast_overlay.add_toast(Adw.Toast.new(_("Uninstalled successfully")))
        else:
            self.toast_overlay.add_toast(
                Adw.Toast.new(_("Could not uninstall some apps"))
            )

    def uninstall_flatpak_thread(self, ref_arr, id_arr, type_arr, should_trash):
        self.my_utils.uninstall_flatpak(
            ref_arr,
            type_arr,
            should_trash,
            self.main_progress_bar,
            self.uninstalling_status,
        )

    def uninstall_flatpak(self, should_trash):
        ref_arr = []
        id_arr = []
        type_arr = []
        self.currently_uninstalling = True
        i = 0
        while self.flatpaks_list_box.get_row_at_index(i) != None:
            current = self.flatpaks_list_box.get_row_at_index(i)
            if current.tickbox.get_active() == True:
                ref_arr.append(current.app_ref)
                id_arr.append(current.app_id)
                type_arr.append(current.install_type)
            i += 1
        self.set_title(self.main_window_title)
        task = Gio.Task.new(None, None, self.uninstall_flatpak_callback)
        task.run_in_thread(
            lambda _task, _obj, _data, _cancellable, ref_arr=ref_arr, id_arr=id_arr, type_arr=type_arr, should_trash=should_trash: self.uninstall_flatpak_thread(
                ref_arr, id_arr, type_arr, should_trash
            )
        )

    def batch_uninstall_button_handler(self, _widget):
        has_user_data = False

        def batch_uninstall_response(_idk, response_id, _widget):
            if response_id == "cancel":
                return 1

            try:
                should_trash = trash_check.get_active()
            except:
                should_trash = False

            self.uninstall_buttons_enable(False)

            self.no_close = self.connect(
                "close-request", lambda event: True
            )  # Make window unable to close
            self.main_stack.set_visible_child(self.uninstalling)
            self.search_button.set_sensitive(False)
            self.uninstall_flatpak(should_trash)

        # Create Widgets
        dialog = Adw.AlertDialog.new(
            _("Uninstall Selected Apps?"),
            _("It will not be possible to use these apps after removal."),
        )

        # Check to see if at least one app in the list has user data
        i = 0
        while True:
            current = self.flatpaks_list_box.get_row_at_index(i)
            i += 1
            if current == None:
                break
            if current.tickbox.get_active() and os.path.exists(
                f"{self.user_data_path}{current.app_id}"
            ):
                has_user_data = True
                break

        if has_user_data:
            # Create Widgets
            options_box = Gtk.Box(orientation="vertical")
            header = Gtk.Label(
                label=_("App Settings & Data"), halign="start", margin_top=10
            )
            options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
            keep_data = Adw.ActionRow(
                title=_("Keep"),
                subtitle=_("Allow restoring these apps' settings and content"),
            )
            trash_data = Adw.ActionRow(
                title=_("Trash"),
                subtitle=_("Send these apps' settings and content to the trash"),
            )
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
        dialog.connect("response", batch_uninstall_response, dialog.choose_finish)

        # Calls
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Uninstall"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.present(self)

    def uninstall_button_handler(self, row, name, ref, id):
        if self.currently_uninstalling:
            self.toast_overlay.add_toast(
                Adw.Toast.new(_("Cannot uninstall while already uninstalling"))
            )
            return

        def uninstall_response(_idk, response_id, _widget):
            if response_id == "cancel":
                return 1

            try:
                should_trash = trash_check.get_active()
            except:
                should_trash = False

            if response_id == "purge":
                should_trash = True

            self.uninstall_buttons_enable(False)

            self.no_close = self.connect(
                "close-request", lambda event: True
            )  # Make window unable to close
            self.main_stack.set_visible_child(self.uninstalling)
            self.search_button.set_sensitive(False)
            self.uninstall_flatpak(should_trash)

        row.tickbox.set_active(True)

        # Create Widgets
        dialog = Adw.AlertDialog.new(
            _("Uninstall {}?").format(name),
            _("It will not be possible to use {} after removal.").format(name),
        )

        if os.path.exists(f"{self.user_data_path}{id}"):
            # Create Widgets for Trash
            options_box = Gtk.Box(orientation="vertical")
            header = Gtk.Label(
                label=_("App Settings & Data"), halign="start", margin_top=10
            )
            options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
            keep_data = Adw.ActionRow(
                title=_("Keep"),
                subtitle=_("Allow restoring this app's settings and content"),
            )
            trash_data = Adw.ActionRow(
                title=_("Trash"),
                subtitle=_("Send this app's settings and content to the trash"),
            )
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
        dialog.connect("response", uninstall_response, dialog.choose_finish)
        dialog.present(self)

    def window_set_empty(self, is_empty):
        self.batch_mode_button.set_sensitive(not is_empty)
        self.search_button.set_sensitive(not is_empty)
        self.filter_button.set_sensitive(not is_empty)
        self.is_empty = is_empty

        if is_empty:
            self.batch_mode_button.set_active(False)
            self.main_stack.set_visible_child(self.no_flatpaks)
            self.search_button.set_sensitive(False)
        else:
            self.main_stack.set_visible_child(self.main_box)
            self.search_button.set_sensitive(True)

    def create_row(self, index):
        row = AppRow(self, self.host_flatpaks, index)
        if row.app_id == "io.github.flattool.Warehouse":
            row.tickbox.set_sensitive(False)
        self.flatpaks_list_box.insert(row, index)

    def generate_list_of_flatpaks(self):
        self.host_flatpaks = self.my_utils.get_host_flatpaks()
        self.dependent_runtimes = self.my_utils.get_dependent_runtimes()
        self.set_title(self.main_window_title)
        self.eol_list = []
        self.system_mask_list = self.my_utils.get_host_masks("system")
        self.user_mask_list = self.my_utils.get_host_masks("user")

        for index in range(len(self.host_flatpaks)):
            try:
                if "eol" in self.host_flatpaks[index][12]:
                    self.eol_list.append(self.host_flatpaks[index][8])
            except:
                print("Could not find EOL")

        for index in range(len(self.host_flatpaks)):
            self.create_row(index)

        # self.windowSetEmpty(not self.flatpaks_list_box.get_row_at_index(0))
        self.batch_actions_enable(False)
        self.main_stack.set_visible_child(self.main_box)
        self.apply_filter()

        # Stop list window from opening with the list at the bottom by focusing the first visible row item
        for index in range(len(self.host_flatpaks)):
            if self.flatpaks_list_box.get_row_at_index(index).is_visible():
                self.flatpaks_list_box.get_row_at_index(index).grab_focus()
                break

    def refresh_list_of_flatpaks(self, widget):
        if self.currently_uninstalling:
            return

        # I hate this so much...
        def callback(*args):
            self.flatpaks_list_box.remove_all()
            self.generate_list_of_flatpaks()
            self.batch_mode_button.set_active(False)
            self.total_selected = 0

        def runner(*args):
            import time
            time.sleep(0.2)

        self.main_stack.set_visible_child(self.refreshing)
        task = Gio.Task.new(None, None, callback)
        task.run_in_thread(runner)

    def reset_filters(self):
        settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        for key in settings.list_keys():
            settings.reset(key)
        self.apply_filter()

    def apply_filter(self):
        self.batch_mode_button.set_active(False)
        settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        show_apps = settings.get_boolean("show-apps")
        show_runtimes = settings.get_boolean("show-runtimes")
        remotes_list = settings.get_string("remotes-list").split(",")
        runtimes_list = settings.get_string("runtimes-list").split(",")
        total_visible = 0
        i = 0
        while self.flatpaks_list_box.get_row_at_index(i) != None:
            current = self.flatpaks_list_box.get_row_at_index(i)
            id = current.app_id
            dependant = current.dependent_runtime
            remote = f"{current.origin_remote}<>{current.install_type};"
            is_runtime = current.is_runtime

            visible = True
            if (not show_apps) and (not is_runtime):
                visible = False

            if (not show_runtimes) and is_runtime:
                visible = False

            if (not "all" in remotes_list) and (not remote in remotes_list):
                visible = False

            if (not "all" in runtimes_list) and (not dependant in runtimes_list):
                visible = False

            current.set_is_visible(visible)
            total_visible += visible
            i += 1
        if (total_visible == 0) or (runtimes_list != ["all"] and show_runtimes):
            self.window_set_empty(True)
            self.main_stack.set_visible_child(self.no_matches)
        else:
            self.window_set_empty(False)
            self.main_stack.set_visible_child(self.main_box)

    def open_data_folder(self, path):
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{path}", None)
        except GLib.GError:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not open folder")))

    def trash_data(self, name, id, index):
        def on_continue(dialog, response):
            if response == "cancel":
                return
            result = self.my_utils.trash_folder(f"{self.user_data_path}{id}")
            if result != 0:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("Could not trash user data"))
                )
                return
            self.lookup_action(f"open-data{index}").set_enabled(False)
            self.lookup_action(f"trash{index}").set_enabled(False)
            self.toast_overlay.add_toast(Adw.Toast.new(_("Trashed user data")))

        dialog = Adw.AlertDialog.new(
            _("Send {}'s User Data to the Trash?").format(name)
        )
        dialog.set_body(
            _("Your files and data for this app will be sent to the trash.")
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.set_close_response("cancel")
        dialog.add_response("continue", _("Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_continue)
        dialog.present(self)

    def mask_flatpak(self, row):
        is_masked = (
            row.mask_label.get_visible()
        )  # Check the visibility of the mask label to see if the flatpak is masked
        result = []

        def callback():
            if result[0] == 1:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(
                        _("Could not disable updates for {}").format(row.app_name)
                    )
                )
                return
            row.set_masked(not is_masked)
            self.lookup_action(f"mask{row.index}").set_enabled(is_masked)
            self.lookup_action(f"unmask{row.index}").set_enabled(not is_masked)

        def on_continue(dialog, response):
            if response == "cancel":
                return
            task = Gio.Task.new(None, None, lambda *_: callback())
            task.run_in_thread(
                lambda *_: result.append(
                    self.my_utils.mask_flatpak(row.app_id, row.install_type, is_masked)
                )
            )

        if is_masked:
            on_continue(self, None)
        else:
            dialog = Adw.AlertDialog.new(
                _("Disable Updates for {}?").format(row.app_name)
            )
            dialog.set_body(
                _(
                    "This will mask {} ensuring it will never recieve any feature or security updates."
                ).format(row.app_name)
            )
            dialog.add_response("cancel", _("Cancel"))
            dialog.set_close_response("cancel")
            dialog.add_response("continue", _("Disable Updates"))
            dialog.connect("response", on_continue)
            dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.present(self)

    def pin_flatpak(self, row):
        def thread(*args):
            command = f"flatpak-spawn --host flatpak pin --{row.install_type} runtime/{row.app_ref}"
            if row.is_pinned:
                command += " --remove"
            response = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True
            ).stderr
            if response != "" and row.is_pinned:
                GLib.idle_add(self.toast_overlay.add_toast(Adw.Toast.new(_("Could not enable auto removal"))))
                return
            elif response != "":
                GLib.idle_add(self.toast_overlay.add_toast(Adw.Toast.new(_("Could not disable auto removal"))))
                return
            row.is_pinned = not row.is_pinned
            GLib.idle_add(lambda *_, row=row: self.lookup_action(f"pin{row.index}").set_enabled(not row.is_pinned))
            GLib.idle_add(lambda *_, row=row: self.lookup_action(f"unpin{row.index}").set_enabled(row.is_pinned))
            GLib.idle_add(lambda *_, row=row: row.pin_label.set_visible(row.is_pinned))
            GLib.idle_add(lambda *_, row=row: row.info_button_show_or_hide())

        def callback(*args):
            print("done")

        def on_continue(dialog, response):
            if response == "cancel":
                return

            task = Gio.Task.new(None, None, None)
            task.run_in_thread(thread)

        if row.is_pinned:
            on_continue(self, None)
        else:
            dialog = Adw.AlertDialog.new(
                _(
                    "Disable Automatic Removal for {}?"
                ).format(row.app_name),
                _(
                    "This will pin {} ensuring it well never be removed automatically, even if no app depends on it."
                ).format(row.app_name),
            )
            dialog.add_response("cancel", _("Cancel"))
            dialog.set_close_response("cancel")
            dialog.connect("response", on_continue)
            dialog.add_response("continue", _("Disable Auto Removal"))
            dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
            dialog.present(self)

    def copy_item(self, to_copy, to_toast=None):
        self.clipboard.set(to_copy)
        if to_toast:
            self.toast_overlay.add_toast(Adw.Toast.new(to_toast))

    def run_callback(self, _a, _b):
        if not self.my_utils.run_app_error:
            return

        error = self.my_utils.run_app_error_message
        dialog = Adw.AlertDialog.new(_("Could not Run App"), error)
        copy_button = Gtk.Button(
            label=_("Copy"), halign=Gtk.Align.CENTER, margin_top=12
        )
        copy_button.add_css_class("pill")
        copy_button.add_css_class("suggested-action")
        copy_button.connect("clicked", lambda *_: self.clipboard.set(error))
        dialog.set_extra_child(copy_button)
        dialog.add_response("ok", _("OK"))
        dialog.set_close_response("ok")
        dialog.present(self)

    def run_app_thread(self, ref, to_toast=None):
        self.run_app_error = False
        task = Gio.Task.new(None, None, self.run_callback)
        task.run_in_thread(lambda *_: self.my_utils.run_app(ref))
        if to_toast:
            self.toast_overlay.add_toast(Adw.Toast.new(to_toast))

    def batch_mode_handler(self, widget):
        batch_mode = widget.get_active()
        i = 0
        while self.flatpaks_list_box.get_row_at_index(i) != None:
            current = self.flatpaks_list_box.get_row_at_index(i)
            current.set_selectable(batch_mode)
            i += 1
        self.in_batch_mode = batch_mode
        self.batch_mode_bar.set_revealed(batch_mode)

        if not widget.get_active():
            self.batch_select_all_button.set_active(False)

    def key_handler(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_w and state == Gdk.ModifierType.CONTROL_MASK:
            self.close()
        if keyval == Gdk.KEY_Escape:
            self.batch_mode_button.set_active(False)

    def batch_actions_enable(self, should_enable):
        self.batch_copy_button.set_sensitive(should_enable)
        self.batch_clean_button.set_sensitive(should_enable)
        self.batch_snapshot_button.set_sensitive(should_enable)
        if not self.currently_uninstalling:
            self.batch_uninstall_button.set_sensitive(should_enable)

    def on_batch_clean_response(self, dialog, response, _a):
        if response == "cancel":
            return
        i = 0
        trashReturnCodes = 0
        while True:
            current = self.flatpaks_list_box.get_row_at_index(i)
            i += 1
            if current == None:
                break
            if current.tickbox.get_active() == False:
                continue
            trash = self.my_utils.trash_folder(f"{self.user_data_path}{current.app_id}")
            if trash == 1:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("{} has no data to trash").format(current.app_name))
                )
                continue
            if trash == 2:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(
                        _("Could not trash {}'s data").format(current.app_name)
                    )
                )
                continue
            self.lookup_action(f"open-data{current.index}").set_enabled(
                False
            )  # Disable the Open User Data dropdown option when the data was deleted
            self.lookup_action(f"trash{current.index}").set_enabled(
                False
            )  # Disable the Trash User Data dropdown option when the data was deleted
        self.batch_actions_enable(False)
        self.batch_mode_button.set_active(False)

    def batch_clean_handler(self, widget):
        dialog = Adw.AlertDialog.new(
            _("Trash Selected Apps' User Data?"),
            _("Your files and data for these apps will be sent to the trash."),
        )
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_batch_clean_response, dialog.choose_finish)
        dialog.present(self)

    def select_all_handler(self, widget):
        self.set_select_all(widget.get_active())

    def batch_snapshot_handler(self, widget):
        def batch_snapshot_response(dialog, response, _a):
            if response == "cancel":
                return
            i = 0
            snapshots_path = (
                self.host_home
                + "/.var/app/io.github.flattool.Warehouse/data/Snapshots/"
            )
            snapshot_arr = []
            app_ver_arr = []
            app_data_arr = []
            epoch = int(time.time())
            self.no_close = self.connect(
                "close-request", lambda event: True
            )  # Make window unable to close
            while self.flatpaks_list_box.get_row_at_index(i) != None:
                current = self.flatpaks_list_box.get_row_at_index(i)
                i += 1
                if current.tickbox.get_active() == False:
                    continue
                if not os.path.exists(f"{self.user_data_path}{current.app_id}"):
                    continue
                snapshot_arr.append(snapshots_path + current.app_id + "/")
                app_ver_arr.append(current.app_version)
                app_data_arr.append(f"{self.user_data_path}{current.app_id}")

            def thread():
                capture = self.my_utils.snapshot_apps(
                    epoch,
                    snapshot_arr,
                    app_ver_arr,
                    app_data_arr,
                    self.main_progress_bar,
                )
                if capture != 0:
                    GLib.idle_add(
                        lambda *_: self.toast_overlay.add_toast(
                            Adw.Toast.new(_("Could not snapshot some apps"))
                        )
                    )

            def callback(*args):
                self.main_stack.set_visible_child(self.main_box)
                self.disconnect(self.no_close)
                self.search_button.set_sensitive(True)

            self.search_button.set_sensitive(False)
            self.batch_actions_enable(False)
            self.batch_mode_button.set_active(False)
            self.main_stack.set_visible_child(self.snapshotting)
            task = Gio.Task.new(None, None, callback)
            task.run_in_thread(lambda *_: thread())

        dialog = Adw.AlertDialog.new(
            _("Create Snapshots?"),
            _(
                "Snapshots are backups of the app's user data. They can be reapplied at any time. This could take a while."
            ),
        )
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Create Snapshots"))
        dialog.connect("response", batch_snapshot_response, dialog.choose_finish)
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
        dialog.present(self)

    def set_select_all(self, should_select_all):
        i = 0
        while self.flatpaks_list_box.get_row_at_index(i) != None:
            current = self.flatpaks_list_box.get_row_at_index(i)
            if (current.get_visible() == True) and (
                current.app_id != "io.github.flattool.Warehouse"
            ):
                current.tickbox.set_active(should_select_all)
            i += 1

    def row_select_handler(self, tickbox):
        if tickbox.get_active() == True:
            self.total_selected += 1
        else:
            self.total_selected -= 1

        if self.total_selected == 0:
            buttons_enable = False
            self.set_title(self.main_window_title)
            self.batch_actions_enable(False)
        else:
            self.set_title(f"{self.total_selected} Selected")
            self.batch_actions_enable(True)

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

    def copy_names(self, widget, _a):
        to_copy = ""
        i = 0
        while True:
            current = self.flatpaks_list_box.get_row_at_index(i)
            i += 1
            if current == None:
                break
            if current.tickbox.get_active():
                to_copy += f"{current.app_name}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app names")))
        self.batch_actions_enable(False)
        self.batch_mode_button.set_active(False)

    def copy_IDs(self, widget, _a):
        to_copy = ""
        i = 0
        while True:
            current = self.flatpaks_list_box.get_row_at_index(i)
            i += 1
            if current == None:
                break
            if current.tickbox.get_active():
                to_copy += f"{current.app_id}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app IDs")))
        self.batch_actions_enable(False)
        self.batch_mode_button.set_active(False)

    def copy_refs(self, widget, _a):
        to_copy = ""
        i = 0
        while True:
            current = self.flatpaks_list_box.get_row_at_index(i)
            i += 1
            if current == None:
                break
            if current.tickbox.get_active():
                to_copy += f"{current.app_ref}\n"
        self.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast.new(_("Copied selected app refs")))
        self.batch_actions_enable(False)
        self.batch_mode_button.set_active(False)

    def install_callback(self, _a, _b):
        self.main_stack.set_visible_child(self.main_box)
        self.search_button.set_sensitive(True)
        if self.my_utils.install_success:
            self.refresh_list_of_flatpaks(self)
            self.toast_overlay.add_toast(Adw.Toast.new(_("Installed successfully")))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not install app")))

    def install_thread(self, filepath, user_or_system):
        self.my_utils.install_flatpak(
            [filepath], None, user_or_system, self.main_progress_bar
        )

    def install_file(self, filepath):
        def response(dialog, response, _a):
            if response == "cancel":
                return

            self.main_stack.set_visible_child(self.installing)
            self.search_button.set_sensitive(False)
            user_or_system = "user"
            if system_check.get_active():
                user_or_system = "system"

            task = Gio.Task.new(None, None, self.install_callback)
            task.run_in_thread(lambda *_: self.install_thread(filepath, user_or_system))

        name = filepath.split("/")
        name = name[len(name) - 1]

        dialog = Adw.AlertDialog.new(_("Install {}?").format(name))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Install"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", response, dialog.choose_finish)

        # Create Widgets
        options_box = Gtk.Box(orientation="vertical")
        options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
        user_row = Adw.ActionRow(
            title=_("User"), subtitle=_("The app will be available to only you")
        )
        system_row = Adw.ActionRow(
            title=_("System"),
            subtitle=_("The app will be available to every user on the system"),
        )
        user_check = Gtk.CheckButton()
        system_check = Gtk.CheckButton()

        # Apply Widgets
        user_row.add_prefix(user_check)
        user_row.set_activatable_widget(user_check)
        system_row.add_prefix(system_check)
        system_row.set_activatable_widget(system_check)
        user_check.set_group(system_check)
        options_list.append(user_row)
        options_list.append(system_row)
        options_box.append(options_list)
        dialog.set_extra_child(options_box)

        # Calls
        user_check.set_active(True)
        options_list.add_css_class("boxed-list")
        dialog.present(self)

    def drop_callback(self, target, _x, _y, _data):
        filepath = target.get_value().get_path()
        if filepath.endswith(".flatpak") or filepath.endswith(".flatpakref"):
            self.install_file(filepath)
        elif filepath.endswith(".flatpakrepo"):
            remotes_window = RemotesWindow(self)
            remotes_window.present()
            remotes_window.add_remote_file(filepath)
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(_("File type not supported")))

    def on_invalidate(self, row):
        if self.is_empty:
            self.batch_mode_button.set_active(False)
            self.main_stack.set_visible_child(self.no_flatpaks)
            self.search_button.set_sensitive(False)
        else:
            self.main_stack.set_visible_child(self.main_box)
            self.search_button.set_sensitive(True)

        self.is_result = False
        self.flatpaks_list_box.invalidate_filter()
        if self.is_result == False:
            self.main_stack.set_visible_child(self.no_results)
            self.search_button.set_sensitive(False)

    def on_change(self, prop, prop2):
        if self.search_bar.get_search_mode() == False:
            if self.is_empty:
                self.batch_mode_button.set_active(False)
                self.main_stack.set_visible_child(self.no_flatpaks)
                self.search_button.set_sensitive(False)
            else:
                self.main_stack.set_visible_child(self.main_box)
                self.search_button.set_sensitive(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(self)
        self.set_size_request(0, 360)
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse")
        self.settings.bind(
            "window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "is-fullscreen", self, "fullscreened", Gio.SettingsBindFlags.DEFAULT
        )

        self.system_pins = self.my_utils.get_host_system_pins()
        self.user_pins = self.my_utils.get_host_user_pins()

        self.new_env = dict(os.environ)
        self.new_env["LC_ALL"] = "C"

        if self.host_flatpaks == [["", ""]]:
            self.window_set_empty(True)
            return

        self.flatpaks_list_box.set_filter_func(self.filter_func)

        task = Gio.Task()
        task.run_in_thread(
            lambda *_: GLib.idle_add(lambda *_: self.generate_list_of_flatpaks())
        )

        self.search_entry.connect("search-changed", self.on_invalidate)
        self.search_bar.connect_entry(self.search_entry)
        self.search_bar.connect("notify", self.on_change)
        self.filter_button.connect("clicked", lambda *_: FilterWindow(self))
        self.batch_mode_button.connect("toggled", self.batch_mode_handler)
        self.batch_clean_button.connect("clicked", self.batch_clean_handler)
        self.batch_uninstall_button.connect(
            "clicked", self.batch_uninstall_button_handler
        )
        self.batch_select_all_button.connect("clicked", self.select_all_handler)
        self.batch_snapshot_button.connect("clicked", self.batch_snapshot_handler)
        self.reset_filters_button.connect("clicked", lambda *_: self.reset_filters())
        self.batch_actions_enable(False)
        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)
        self.main_overlay.add_overlay(self.main_progress_bar)

        self.create_action("copy-names", self.copy_names)
        self.create_action("copy-ids", self.copy_IDs)
        self.create_action("copy-refs", self.copy_refs)

        file_drop = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        file_drop.connect("drop", self.drop_callback)
        self.scrolled_window.add_controller(file_drop)

        if Config.DEVEL:
            self.add_css_class("devel")
