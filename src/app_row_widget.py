import os
import pathlib
import subprocess
import re

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from .properties_window import PropertiesWindow
from .downgrade_window import DowngradeWindow
from .snapshots_window import SnapshotsWindow
from .filter_window import FilterWindow
from .common import myUtils

class AppRow(Adw.ActionRow):

    def set_selectable(self, is_selectable):
        self.tickbox.set_active(False)
        self.tickbox.set_visible(is_selectable)
        self.row_menu.set_visible(not is_selectable)
        self.set_activatable(is_selectable)

    def set_is_visible(self, is_visible):
        self.set_visible(is_visible)
        self.set_selectable(False)

    def info_button_show_or_hide(self):
        self.info_button.set_visible(False)

        if self.mask_label.get_visible() == True:
            self.info_button.set_visible(True)

        if self.eol_app_label.get_visible() == True:
            self.info_button.set_visible(True)

        if self.eol_runtime_label.get_visible() == True:
            self.info_button.set_visible(True)

    def set_masked(self, is_masked):
        self.mask_label.set_visible(is_masked)
        self.info_button_show_or_hide()

    def __init__(self, parent_window, host_flatpaks, index, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(parent_window)

        current_flatpak = host_flatpaks[index]

        self.index = index
        self.app_name = current_flatpak[0]
        self.app_id = current_flatpak[2]
        self.app_version = current_flatpak[3]
        self.origin_remote = current_flatpak[6]
        self.install_type = current_flatpak[7]
        self.app_ref = current_flatpak[8]
        self.dependent_runtime = current_flatpak[13]

        self.set_title(self.app_name)
        self.set_subtitle(self.app_id)
        self.add_prefix(self.my_utils.findAppIcon(self.app_id))

        self.is_runtime = False
        if len(current_flatpak[13]) == 0:
            self.is_runtime = True

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER, hexpand=True, vexpand=True, spacing=6)

        # justify=Gtk.Justification.RIGHT
        self.mask_label = Gtk.Label(label=_("Updates Disabled"), visible=False, hexpand=True, wrap=True, valign=Gtk.Align.CENTER, tooltip_text=_("{} is masked and will not be updated").format(self.app_name))
        self.mask_label.add_css_class("warning")

        self.eol_app_label = Gtk.Label(label=_("App EOL"), visible=False, hexpand=True, wrap=True, valign=Gtk.Align.CENTER, tooltip_text=_("{} has reached its End of Life and will not receive any security updates").format(self.app_name))
        self.eol_app_label.add_css_class("error")
        info_box.append(self.eol_app_label)
        if "eol" in parent_window.host_flatpaks[index][12]:
            # EOL = End Of Life, meaning the app will not be updated
            # justify=Gtk.Justification.RIGHT
            self.eol_app_label.set_visible(True)

        self.eol_runtime_label = Gtk.Label(label=_("Runtime EOL"), visible=False, hexpand=True, wrap=True, valign=Gtk.Align.CENTER, tooltip_text=_("{}'s runtime has reached its End of Life and will not receive any security updates").format(self.app_name))
        self.eol_runtime_label.add_css_class("error")
        info_box.append(self.eol_runtime_label)
        if current_flatpak[13] in parent_window.eol_list:
            # EOL = End Of Life, meaning the runtime will not be updated
            # justify=Gtk.Justification.RIGHT
            self.eol_runtime_label.set_visible(True)

        info_pop = Gtk.Popover()
        info_pop.set_child(info_box)
        self.info_button = Gtk.MenuButton(visible=False, valign=Gtk.Align.CENTER, popover=info_pop, icon_name="software-update-urgent-symbolic")
        self.info_button.add_css_class("flat")

        info_box.append(self.mask_label)
        self.add_suffix(self.info_button)

        properties_button = Gtk.Button(icon_name="info-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("View Properties"))
        properties_button.add_css_class("flat")
        properties_button.connect("clicked", lambda *_: PropertiesWindow(index, host_flatpaks, parent_window))
        self.add_suffix(properties_button)
        
        self.tickbox = Gtk.CheckButton(visible=False) # visible=self.in_batch_mode
        self.tickbox.add_css_class("selection-mode")
        self.tickbox.connect("toggled", parent_window.rowSelectHandler)
        self.add_suffix(self.tickbox)
        self.set_activatable_widget(self.tickbox)
        self.set_activatable(False)

        self.row_menu = Gtk.MenuButton(icon_name="view-more-symbolic", valign=Gtk.Align.CENTER) # visible=not self.in_batch_mode
        self.row_menu.add_css_class("flat")
        row_menu_model = Gio.Menu()
        copy_menu_model = Gio.Menu()
        advanced_menu_model = Gio.Menu()
        self.add_suffix(self.row_menu)

        parent_window.create_action(("copy-name" + str(index)), lambda *_, name=self.app_name, toast=_("Copied name"): parent_window.copyItem(name, toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy Name"), f"win.copy-name{index}"))

        parent_window.create_action(("copy-id" + str(index)), lambda *_, id=self.app_id, toast=_("Copied ID"): parent_window.copyItem(id, toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy ID"), f"win.copy-id{index}"))

        parent_window.create_action(("copy-ref" + str(index)), lambda *_, ref=self.app_ref, toast=_("Copied ref"): parent_window.copyItem(ref, toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy Ref"), f"win.copy-ref{index}"))

        parent_window.create_action(("copy-command" + str(index)), lambda *_, ref=self.app_ref, toast=_("Copied launch command"): parent_window.copyItem(f"flatpak run {ref}", toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy Launch Command"), f"win.copy-command{index}"))

        row_menu_model.append_submenu(_("Copy"), copy_menu_model)

        if "runtime" not in parent_window.host_flatpaks[index][12]:
            parent_window.create_action(("run" + str(index)), lambda *_a, ref=self.app_ref, name=self.app_name: parent_window.runAppThread(ref, _("Opened {}").format(name)))
            run_item = Gio.MenuItem.new(_("Open"), f"win.run{index}")
            row_menu_model.append_item(run_item)

        parent_window.create_action(("uninstall" + str(index)), lambda *_: parent_window.uninstallButtonHandler(self, self.app_name, self.app_ref, self.app_id))
        uninstall_item = Gio.MenuItem.new(_("Uninstall"), f"win.uninstall{index}")
        row_menu_model.append_item(uninstall_item)

        data_menu_model = Gio.Menu()

        parent_window.create_action(("open-data" + str(index)), lambda *_, path=(parent_window.user_data_path + self.app_id): parent_window.openDataFolder(path))
        open_data_item = Gio.MenuItem.new(_("Open User Data Folder"), f"win.open-data{index}")
        open_data_item.set_attribute_value("hidden-when", GLib.Variant.new_string("action-disabled"))
        data_menu_model.append_item(open_data_item)

        parent_window.create_action(("trash" + str(index)), lambda *_, name=self.app_name, id=self.app_id, index=index: parent_window.trashData(name, id, index))
        trash_item = Gio.MenuItem.new(_("Trash User Data"), f"win.trash{index}")
        trash_item.set_attribute_value("hidden-when", GLib.Variant.new_string("action-disabled"))
        data_menu_model.append_item(trash_item)

        row_menu_model.append_section(None, data_menu_model)
        
        if not os.path.exists(parent_window.user_data_path + self.app_id):
            parent_window.lookup_action(f"open-data{self.index}").set_enabled(False)
            parent_window.lookup_action(f"trash{self.index}").set_enabled(False)

        parent_window.create_action(("mask" + str(index)), lambda *_, id=self.app_id, type=self.install_type, index=index: parent_window.maskFlatpak(self))
        mask_item = Gio.MenuItem.new(_("Disable Updates"), f"win.mask{index}")
        mask_item.set_attribute_value("hidden-when", GLib.Variant.new_string("action-disabled"))
        advanced_menu_model.append_item(mask_item)

        parent_window.create_action(("unmask" + str(index)), lambda *_, id=self.app_id, type=self.install_type, index=index: parent_window.maskFlatpak(self))
        unmask_item = Gio.MenuItem.new(_("Enable Updates"), f"win.unmask{index}")
        unmask_item.set_attribute_value("hidden-when", GLib.Variant.new_string("action-disabled"))
        advanced_menu_model.append_item(unmask_item)

        if "runtime" not in parent_window.host_flatpaks[index][12]:
            parent_window.create_action(("snapshot" + str(index)), lambda *_, row=current_flatpak: SnapshotsWindow(parent_window, row).present())
            snapshot_item = Gio.MenuItem.new(_("Manage Snapshots"), f"win.snapshot{index}")
            advanced_menu_model.append_item(snapshot_item)

        parent_window.create_action(("downgrade" + str(index)), lambda *_, row=current_flatpak, index=index: DowngradeWindow(parent_window, row, index))
        downgrade_item = Gio.MenuItem.new(_("Downgrade"), f"win.downgrade{index}")
        advanced_menu_model.append_item(downgrade_item)

        if self.app_id in parent_window.system_mask_list or self.app_id in parent_window.user_mask_list:
            self.mask_label.set_visible(True)
            parent_window.lookup_action(f"mask{index}").set_enabled(False)
        else:
            parent_window.lookup_action(f"unmask{index}").set_enabled(False)

        row_menu_model.append_section(None, advanced_menu_model)
        self.row_menu.set_menu_model(row_menu_model)

        self.info_button_show_or_hide()
