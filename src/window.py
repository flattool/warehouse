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

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from .properties_window import PropertiesWindow
from .filter_window import FilterWindow
from .common import myUtils
from .remotes_window import RemotesWindow
from .downgrade_window import DowngradeWindow
from .snapshots_window import SnapshotsWindow

from .app_row_widget import AppRow

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
    no_results = Gtk.Template.Child()
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
    scrolled_window = Gtk.Template.Child()
    main_menu = Gtk.Template.Child()
    installing = Gtk.Template.Child()
    uninstalling = Gtk.Template.Child()

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
    selected_rows = []
    flatpak_rows = []
    # ^ {Row visibility, Row selected, the row itself, properties, row menu, select, the flatpak row from `flatpak list`, mask label}

    def filter_func(self, row):
        if (self.search_entry.get_text().lower() in row.get_title().lower()) or (self.search_entry.get_text().lower() in row.get_subtitle().lower()):
            self.is_result = True
            return True

    def removeRow(self, row):
        row[5].set_active(False)
        row[0] = False
        row[2].set_visible(False)

    def uninstallButtonsEnable(self, should_enable):
        if self.currently_uninstalling:
            return
        self.refresh_button.set_sensitive(should_enable)
        if not should_enable:
            self.batch_uninstall_button.set_sensitive(False)

    def uninstallFlatpakCallback(self, _a, _b):
        self.currently_uninstalling = False
        self.refresh_list_of_flatpaks(_a, False)
        self.main_toolbar_view.set_sensitive(True)
        self.disconnect(self.no_close)
        self.uninstallButtonsEnable(True)
        self.main_stack.set_visible_child(self.main_box)
        if self.my_utils.uninstall_success:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Uninstalled successfully")))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not uninstall some apps")))

    def uninstallFlatpakThread(self, ref_arr, id_arr, type_arr, should_trash):
        self.my_utils.uninstallFlatpak(ref_arr, type_arr, should_trash, self.main_progress_bar)

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
        task.run_in_thread(lambda _task, _obj, _data, _cancellable, ref_arr=ref_arr, id_arr=id_arr, type_arr=type_arr, should_trash=should_trash: self.uninstallFlatpakThread(ref_arr, id_arr, type_arr, should_trash))

    def batchUninstallButtonHandler(self, _widget):
        has_user_data = False

        def batchUninstallResponse(_idk, response_id, _widget):
            if response_id == "cancel":
                return 1                    

            try:
                should_trash = trash_check.get_active()
            except:
                should_trash = False

            self.uninstallButtonsEnable(False)

            self.no_close = self.connect("close-request", lambda event: True)  # Make window unable to close
            self.main_stack.set_visible_child(self.uninstalling)
            self.uninstallFlatpak(should_trash)

        # Create Widgets
        dialog = Adw.MessageDialog.new(self, _("Uninstall Selected Apps?"), _("It will not be possible to use these apps after removal."))

        # Check to see if at least one app in the list has user data
        for i in range(len(self.flatpak_rows)):
            if not self.flatpak_rows[1]:
                continue # Skip if not selected
            if os.path.exists(f"{self.user_data_path}{self.flatpak_rows[i][6][2]}"):
                has_user_data = True
                break

        if has_user_data:
            # Create Widgets
            options_box = Gtk.Box(orientation="vertical")
            header = Gtk.Label(label=_("App Settings & Data"), halign="start", margin_top=10)
            options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
            keep_data = Adw.ActionRow(title=_("Keep"), subtitle=_("Allow restoring these apps' settings and content"))
            trash_data = Adw.ActionRow(title=_("Trash"), subtitle=_("Send these apps' settings and content to the trash"))
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
        if self.currently_uninstalling:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Cannot uninstall while already uninstalling")))
            return

        name = self.host_flatpaks[index][0]
        ref = self.host_flatpaks[index][8]
        id = self.host_flatpaks[index][2]
        self.flatpak_rows[index][1] = True

        def uninstallResponse(_idk, response_id, _widget):
            if response_id == "cancel":
                return 1

            try:
                should_trash = trash_check.get_active()
            except:
                should_trash = False

            if response_id == "purge":
                should_trash = True

            self.uninstallButtonsEnable(False)

            self.no_close = self.connect("close-request", lambda event: True)  # Make window unable to close
            self.main_stack.set_visible_child(self.uninstalling)
            self.uninstallFlatpak(should_trash)

        # Create Widgets
        dialog = Adw.MessageDialog.new(self, _("Uninstall {}?").format(name), _("It will not be possible to use {} after removal.").format(name))

        if os.path.exists(f"{self.user_data_path}{id}"):
            # Create Widgets for Trash
            options_box = Gtk.Box(orientation="vertical")
            header = Gtk.Label(label=_("App Settings & Data"), halign="start", margin_top=10)
            options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
            keep_data = Adw.ActionRow(title=_("Keep"), subtitle=_("Allow restoring this app's settings and content"))
            trash_data = Adw.ActionRow(title=_("Trash"), subtitle=_("Send this app's settings and content to the trash"))
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
        self.is_empty = is_empty

        if is_empty:
            self.batch_mode_button.set_active(False)
            self.main_stack.set_visible_child(self.no_flatpaks)
        else:
            self.main_stack.set_visible_child(self.main_box)

    def creat_row(self, index):
        app_name = self.host_flatpaks[index][0]
        app_id = self.host_flatpaks[index][2]
        install_type = self.host_flatpaks[index][7]
        app_ref = self.host_flatpaks[index][8]
        flatpak_row = Adw.ActionRow(title=GLib.markup_escape_text(app_name))
        flatpak_row.add_prefix(self.my_utils.findAppIcon(app_id))
        flatpak_row.set_subtitle(app_id)

        if "eol" in self.host_flatpaks[index][12]:
            # EOL = End Of Life, meaning the app will not be updated
            eol_app_label = Gtk.Label(label=_("App EOL"), hexpand=True, wrap=True, justify=Gtk.Justification.RIGHT, valign=Gtk.Align.CENTER, tooltip_text=_("{} has reached its End of Life and will not receive any security updates").format(app_name))
            eol_app_label.add_css_class("error")
            flatpak_row.add_suffix(eol_app_label)

        if self.host_flatpaks[index][13] in self.eol_list:
            # EOL = End Of Life, meaning the runtime will not be updated
            eol_runtime_label = Gtk.Label(label=_("Runtime EOL"), hexpand=True, wrap=True, justify=Gtk.Justification.RIGHT, valign=Gtk.Align.CENTER, tooltip_text=_("{}'s runtime has reached its End of Life and will not receive any security updates").format(app_name))
            eol_runtime_label.add_css_class("error")
            flatpak_row.add_suffix(eol_runtime_label)

        mask_label = Gtk.Label(label=_("Updates Disabled"), hexpand=True, wrap=True, justify=Gtk.Justification.RIGHT, valign=Gtk.Align.CENTER, tooltip_text=_("{} is masked and will not be updated").format(app_name), visible=False)
        mask_label.add_css_class("warning")
        flatpak_row.add_suffix(mask_label)
        # ^ This is up here as we need to add this to flatpak_rows regardless of if its visible or not

        properties_button = Gtk.Button(icon_name="info-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("View Properties"))
        properties_button.add_css_class("flat")
        properties_button.connect("clicked", lambda *_, index=index: PropertiesWindow(index, self.host_flatpaks, self))
        flatpak_row.add_suffix(properties_button)

        select_flatpak_tickbox = Gtk.CheckButton(visible=self.in_batch_mode)
        select_flatpak_tickbox.add_css_class("selection-mode")
        select_flatpak_tickbox.connect("toggled", self.rowSelectHandler, index)
        flatpak_row.add_suffix(select_flatpak_tickbox)

        row_menu = Gtk.MenuButton(icon_name="view-more-symbolic", valign=Gtk.Align.CENTER, visible=not self.in_batch_mode)
        row_menu.add_css_class("flat")
        row_menu_model = Gio.Menu()
        copy_menu_model = Gio.Menu()
        advanced_menu_model = Gio.Menu()

        self.flatpak_rows.append([True, False, flatpak_row, properties_button, row_menu, select_flatpak_tickbox, self.host_flatpaks[index], mask_label])
        # {Row visibility, Row selected, the row itself, properties, menu button, select, the flatpak row from `flatpak list`, mask label, the dropdown menu model}

        #

        self.create_action(("copy-name" + str(index)), lambda *_, name=app_name, toast=_("Copied name"): self.copyItem(name, toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy Name"), f"win.copy-name{index}"))

        self.create_action(("copy-id" + str(index)), lambda *_, id=app_id, toast=_("Copied ID"): self.copyItem(id, toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy ID"), f"win.copy-id{index}"))

        self.create_action(("copy-ref" + str(index)), lambda *_, ref=app_ref, toast=_("Copied ref"): self.copyItem(ref, toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy Ref"), f"win.copy-ref{index}"))

        self.create_action(("copy-command" + str(index)), lambda *_, ref=app_ref, toast=_("Copied launch command"): self.copyItem(f"flatpak run {ref}", toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy Launch Command"), f"win.copy-command{index}"))

        row_menu_model.append_submenu(_("Copy"), copy_menu_model)

        if "runtime" not in self.host_flatpaks[index][12]:
            self.create_action(("run" + str(index)), lambda *_a, ref=app_ref, name=app_name: self.runAppThread(ref, _("Opened {}").format(name)))
            run_item = Gio.MenuItem.new(_("Open"), f"win.run{index}")
            row_menu_model.append_item(run_item)

        self.create_action(("uninstall" + str(index)), lambda *_, index=index: self.uninstallButtonHandler(self, index))
        uninstall_item = Gio.MenuItem.new(_("Uninstall"), f"win.uninstall{index}")
        row_menu_model.append_item(uninstall_item)

        self.create_action(("mask" + str(index)), lambda *_, id=app_id, type=install_type, index=index: self.maskFlatpak(id, type, index))
        mask_item = Gio.MenuItem.new(_("Disable Updates"), f"win.mask{index}")
        mask_item.set_attribute_value("hidden-when", GLib.Variant.new_string("action-disabled"))
        advanced_menu_model.append_item(mask_item)

        self.create_action(("unmask" + str(index)), lambda *_, id=app_id, type=install_type, index=index: self.maskFlatpak(id, type, index))
        unmask_item = Gio.MenuItem.new(_("Enable Updates"), f"win.unmask{index}")
        unmask_item.set_attribute_value("hidden-when", GLib.Variant.new_string("action-disabled"))
        advanced_menu_model.append_item(unmask_item)

        if app_id in self.system_mask_list or app_id in self.user_mask_list:
            mask_label.set_visible(True)
            self.lookup_action(f"mask{index}").set_enabled(False)
        else:
            self.lookup_action(f"unmask{index}").set_enabled(False)

        if os.path.exists(self.user_data_path + app_id):
            data_menu_model = Gio.Menu()

            self.create_action(("open-data" + str(index)), lambda *_, path=(self.user_data_path + app_id): self.openDataFolder(path))
            open_data_item = Gio.MenuItem.new(_("Open User Data Folder"), f"win.open-data{index}")
            open_data_item.set_attribute_value("hidden-when", GLib.Variant.new_string("action-disabled"))
            data_menu_model.append_item(open_data_item)

            self.create_action(("trash" + str(index)), lambda *_, name=app_name, id=app_id, index=index: self.trashData(name, id, index))
            trash_item = Gio.MenuItem.new(_("Trash User Data"), f"win.trash{index}")
            trash_item.set_attribute_value("hidden-when", GLib.Variant.new_string("action-disabled"))
            data_menu_model.append_item(trash_item)

            row_menu_model.append_section(None, data_menu_model)

        if "runtime" not in self.host_flatpaks[index][12]:
            self.create_action(("snapshot" + str(index)), lambda *_, row=self.flatpak_rows[index][6]: SnapshotsWindow(self, row).present())
            snapshot_item = Gio.MenuItem.new(_("Manage Snapshots"), f"win.snapshot{index}")
            advanced_menu_model.append_item(snapshot_item)

        self.create_action(("downgrade" + str(index)), lambda *_, row=self.flatpak_rows[index]: DowngradeWindow(self, row))
        downgrade_item = Gio.MenuItem.new(_("Downgrade"), f"win.downgrade{index}")
        advanced_menu_model.append_item(downgrade_item)

        row_menu_model.append_section(None, advanced_menu_model)

        row_menu.set_menu_model(row_menu_model)
        flatpak_row.add_suffix(row_menu)

        if self.in_batch_mode:
            flatpak_row.set_activatable_widget(select_flatpak_tickbox)

        self.flatpaks_list_box.insert(flatpak_row, index)
    
    def generate_list_of_flatpaks(self):
        self.set_title(self.main_window_title)
        self.flatpak_rows = []
        self.should_select_all = self.batch_select_all_button.get_active()
        self.main_stack.set_visible_child(self.main_box)
        self.batch_select_all_button.set_active(False)
        self.eol_list = []
        self.system_mask_list = self.my_utils.getHostMasks("system")
        self.user_mask_list = self.my_utils.getHostMasks("user")

        for index in range(len(self.host_flatpaks)):
            try:
                if "eol" in self.host_flatpaks[index][12]:
                    self.eol_list.append(self.host_flatpaks[index][8])
            except:
                print("Could not find EOL")

        for index in range(len(self.host_flatpaks)):
            try:
                self.creat_row(index)
            except:
                print("Could not create row")

        self.windowSetEmpty(not self.flatpaks_list_box.get_row_at_index(0))
        self.applyFilter(self.filter_list)
        self.batchActionsEnable(False)

        cool_row = AppRow(self, self.host_flatpaks, 7)
        self.flatpaks_list_box.append(cool_row)
        cool_row.set_selectable(True)
        cool_row.select_flatpak_tickbox.set_active(True)

    def openDataFolder(self, path):
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{path}", None)
        except GLib.GError:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not open folder")))

    def trashData(self, name, id, index):
        def onContinue(dialog, response):
            if response == "cancel":
                return
            result = self.my_utils.trashFolder(f"{self.user_data_path}{id}")
            if result != 0:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Could not trash user data")))
                return
            self.lookup_action(f"open-data{index}").set_enabled(False)
            self.lookup_action(f"trash{index}").set_enabled(False)
            self.toast_overlay.add_toast(Adw.Toast.new(_("Trashed user data")))

        dialog = Adw.MessageDialog.new(self,_("Send {}'s User Data to the Trash?").format(name))
        dialog.set_body(_("Your files and data for this app will be sent to the trash."))
        dialog.add_response("cancel", _("Cancel"))
        dialog.set_close_response("cancel")
        dialog.add_response("continue", _("Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", onContinue)
        dialog.present()

    def maskFlatpak(self, id, type, index):
        is_masked = self.flatpak_rows[index][7].get_visible() # Check the visibility of the mask label to see if the flatpak is masked
        result = []
        name = self.host_flatpaks[index][0]

        def callback():
            if result[0] == 1:
                self.toast_overlay.add_toast(Adw.Toast.new(_("Could disable updates for {}").format(name)))
                return
            self.flatpak_rows[index][7].set_visible(not is_masked)
            self.lookup_action(f"mask{index}").set_enabled(is_masked)
            self.lookup_action(f"unmask{index}").set_enabled(not is_masked)

        def onContinue(dialog, response):
            if response == "cancel":
                return
            task = Gio.Task.new(None, None, lambda *_: callback())
            task.run_in_thread(lambda *_: result.append(self.my_utils.maskFlatpak(id, type, is_masked)))

        if is_masked:
            onContinue(self, None)
        else:
            dialog = Adw.MessageDialog.new(self, _("Disable Updates for {}?").format(name))
            dialog.set_body(_("This will mask {} ensuring it will never recieve any feature or security updates.").format(name))
            dialog.add_response("cancel", _("Cancel"))
            dialog.set_close_response("cancel")
            dialog.add_response("continue", _("Disable Updates"))
            dialog.connect("response", onContinue)
            dialog.present()

    def copyItem(self, to_copy, to_toast=None):
        self.clipboard.set(to_copy)
        if to_toast:
            self.toast_overlay.add_toast(Adw.Toast.new(to_toast))

    def runCallback(self, _a, _b):
        if not self.my_utils.run_app_error:
            return
        
        error = self.my_utils.run_app_error_message
        dialog = Adw.MessageDialog.new(self, _("Could not Run App"), error)
        copy_button = Gtk.Button(label=_("Copy"), halign=Gtk.Align.CENTER, margin_top=12)
        copy_button.add_css_class("pill")
        copy_button.add_css_class("suggested-action")
        copy_button.connect("clicked", lambda *_: self.clipboard.set(error))
        dialog.set_extra_child(copy_button)
        dialog.add_response("ok", _("OK"))
        dialog.set_close_response("ok")
        dialog.present()

    def runAppThread(self, ref, to_toast=None):
        self.run_app_error = False
        task = Gio.Task.new(None, None, self.runCallback)
        task.run_in_thread(lambda *_: self.my_utils.runApp(ref))
        if to_toast:
            self.toast_overlay.add_toast(Adw.Toast.new(to_toast))

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
            menu_button = self.flatpak_rows[i][4]
            select_tick = self.flatpak_rows[i][5]

            menu_button.set_visible(not widget.get_active())
            select_tick.set_visible(widget.get_active())

            if widget.get_active():
                adw_row.set_activatable(True)
                adw_row.set_activatable_widget(select_tick)
            else:
                select_tick.set_active(False)
                adw_row.set_activatable(False)

        self.in_batch_mode = widget.get_active()
        self.batch_mode_bar.set_revealed(widget.get_active())

        if not widget.get_active():
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
                self.toast_overlay.add_toast(Adw.Toast.new(_("Could not trash user data")))
        if show_success:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Trashed user data")))
        #self.refresh_list_of_flatpaks(_a, False)

    def batchCleanHandler(self, widget):
        dialog = Adw.MessageDialog.new(self, _("Trash Selected Apps' User Data?"), _("Your files and data for these apps will be sent to the trash."))
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
        if widget.get_active() and self.should_open_filter_window:
            filtwin = FilterWindow(self)
            filtwin.present()
        else:
            self.applyFilter()

    def filterWindowKeyboardHandler(self, widget):
        self.filter_button.set_active(not self.filter_button.get_active())

    def resetFilterList(self):
        self.filter_list = [True, False, ["all"], ["all"], ["all"]]

    def applyFilter(self, filter=[True, False, ["all"], ["all"], ["all"]]):
        self.filter_list = filter
        show_apps = filter[0]
        show_runtimes = filter[1]
        filter_install_type = filter[2]
        filter_remotes_list = filter[3]
        filter_runtimes_list = filter[4]
        total_visible = 0

        for i in range(len(self.flatpak_rows)):
            self.flatpak_rows[i][0] = True

            if (not show_apps) and (not "runtime" in self.flatpak_rows[i][6][12]):
                self.flatpak_rows[i][0] = False

            if (not show_runtimes) and "runtime" in self.flatpak_rows[i][6][12]:
                self.flatpak_rows[i][0] = False

            if (not 'all' in filter_install_type) and (not self.flatpak_rows[i][6][7] in filter_install_type):
                self.flatpak_rows[i][0] = False

            if (not 'all' in filter_remotes_list) and (not self.flatpak_rows[i][6][6] in filter_remotes_list):
                self.flatpak_rows[i][0] = False

            if (not 'all' in filter_runtimes_list) and (not self.flatpak_rows[i][6][13] in filter_runtimes_list):
                self.flatpak_rows[i][0] = False

            self.flatpak_rows[i][2].set_visible(self.flatpak_rows[i][0])

            if self.flatpak_rows[i][0]:
                total_visible += 1

        if total_visible > 0:
            self.windowSetEmpty(False)
        else:
            self.windowSetEmpty(True)
            self.filter_button.set_sensitive(True)

    def installCallback(self, _a, _b):
        self.main_stack.set_visible_child(self.main_box)
        if self.my_utils.install_success:
            self.refresh_list_of_flatpaks(self, False)
            self.toast_overlay.add_toast(Adw.Toast.new(_("Installed successfully")))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not install app")))

    def installThread(self, filepath, user_or_system):
        self.my_utils.installFlatpak([filepath], None, user_or_system, self.main_progress_bar)

    def install_file(self, filepath):
        def response(dialog, response, _a):
            if response == "cancel":
                return

            self.main_stack.set_visible_child(self.installing)
            user_or_system = "user"
            if system_check.get_active():
                user_or_system = "system"

            task = Gio.Task.new(None, None, self.installCallback)
            task.run_in_thread(lambda *_: self.installThread(filepath, user_or_system))

        name = filepath.split('/')
        name = name[len(name) - 1]

        dialog = Adw.MessageDialog.new(self, _("Install {}?").format(name))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Install"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", response, dialog.choose_finish)

        # Create Widgets
        options_box = Gtk.Box(orientation="vertical")
        options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
        user_row = Adw.ActionRow(title=_("User"), subtitle=_("The app will be available to only you"))
        system_row = Adw.ActionRow(title=_("System"), subtitle=_("The app will be available to every user on the system"))
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
        Gtk.Window.present(dialog)

    def drop_callback(self, target, _x, _y, _data):
        filepath = target.get_value().get_path()
        if filepath.endswith(".flatpak") or filepath.endswith(".flatpakref"):
            self.install_file(filepath)
        elif filepath.endswith(".flatpakrepo"):
            remotes_window = RemotesWindow(self)
            remotes_window.present()
            remotes_window.addRemoteFromFile(filepath)
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(_("File type not supported")))

    def on_invalidate(self, row):
        if self.is_empty:
            self.batch_mode_button.set_active(False)
            self.main_stack.set_visible_child(self.no_flatpaks)
        else:
            self.main_stack.set_visible_child(self.main_box)

        self.is_result = False
        self.flatpaks_list_box.invalidate_filter()
        if self.is_result == False:
            self.main_stack.set_visible_child(self.no_results)

    def on_change(self, prop, prop2):
        if self.search_bar.get_search_mode() == False:
            if self.is_empty:
                self.batch_mode_button.set_active(False)
                self.main_stack.set_visible_child(self.no_flatpaks)
            else:
                self.main_stack.set_visible_child(self.main_box)



    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(self)
        self.filter_list = [True, False, ["all"], ["all"], ["all"]]
        self.host_flatpaks = self.my_utils.getHostFlatpaks()
        self.set_size_request(0, 230)
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse")
        self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-fullscreen", self, "fullscreened", Gio.SettingsBindFlags.DEFAULT)

        self.new_env = dict( os.environ )
        self.new_env['LC_ALL'] = 'C'

        if self.host_flatpaks == [['', '']]:
            self.windowSetEmpty(True)
            return

        self.flatpaks_list_box.set_filter_func(self.filter_func)
        self.generate_list_of_flatpaks()
        self.search_entry.connect("search-changed", self.on_invalidate)
        self.search_bar.connect_entry(self.search_entry)
        self.search_bar.connect("notify", self.on_change)
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
        self.should_open_filter_window = True

        self.create_action("copy-names", self.copyNames)
        self.create_action("copy-ids", self.copyIDs)
        self.create_action("copy-refs", self.copyRefs)

        self.filter_button.connect("toggled", self.filterWindowHandler)

        file_drop = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        file_drop.connect("drop", self.drop_callback)
        self.scrolled_window.add_controller(file_drop)




