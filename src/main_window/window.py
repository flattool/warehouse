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
from .host_info import HostInfo
from .packages_page import PackagesPage
from .remotes_page import RemotesPage
from .user_data_page import UserDataPage
from .snapshot_page import SnapshotPage
from .install_page import InstallPage
from .const import Config
from .error_toast import ErrorToast

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/main_window/window.ui")
class WarehouseWindow(Adw.ApplicationWindow):
    __gtype_name__ = "WarehouseWindow"
    gtc = Gtk.Template.Child
    main_breakpoint = gtc()
    toast_overlay = gtc()
    main_split = gtc()
    stack = gtc()
    refresh_button = gtc()
    navigation_row_listbox = gtc()
    packages_row = gtc()
    remotes_row = gtc()
    user_data_row = gtc()
    snapshots_row = gtc()
    install_row = gtc()

    def key_handler(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_w and state == Gdk.ModifierType.CONTROL_MASK:
            self.close()

        # if keyval == Gdk.KEY_Escape:
        #     self.batch_mode_button.set_active(False)

    def start_loading(self, *args):
        for _, page in self.pages.items():
            if page.instance:
                page.instance.start_loading()

    def end_loading(self, *args):
        for _, page in self.pages.items():
            if page.instance:
                page.instance.end_loading()
                
        self.refresh_button.set_sensitive(True)
        self.refresh_requested = False
        
    def do_refresh(self):
        self.start_loading()
        self.refresh_button.set_sensitive(False)
        HostInfo.get_flatpaks(callback=self.end_loading)

    def refresh_handler(self, *args):
        if len(self.refresh_lockouts) == 0:
            self.do_refresh()
        else:
            self.refresh_requested = True
            
    def add_refresh_lockout(self, reason):
        self.refresh_lockouts.append(reason)
        self.refresh_button.set_sensitive(False)
        
    def remove_refresh_lockout(self, reason):
        if reason in self.refresh_lockouts:
            self.refresh_lockouts.remove(reason)
            
        if len(self.refresh_lockouts) == 0:
            if self.refresh_requested:
                self.do_refresh()
            else:
                self.refresh_button.set_sensitive(True)

    def navigation_handler(self, _, row):
        row = row.get_child()
        page = self.pages[row]
        self.stack.set_visible_child(page)
        self.settings.set_string("page-shown", page.page_name)
        if self.main_split.get_collapsed():
            self.main_split.set_show_sidebar(False)

    def activate_row(self, nav_row):
        idx = 0
        while row := self.navigation_row_listbox.get_row_at_index(idx):
            idx += 1
            if row.get_child() is nav_row:
                row.activate()
                nav_row.grab_focus()
                break

    def save_sidebar_state(self, *args):
        state = self.main_split.get_show_sidebar()
        self.settings.set_boolean("sidebar-shown", state)
        print(self.settings.get_boolean("sidebar-shown"))

    def show_saved_page(self):
        page_to_show = self.settings.get_string("page-shown")
        page_found = False
        for row, page in self.pages.items():
            self.stack.add_child(page)

            if page.page_name == page_to_show:
                page_found = True
                self.activate_row(row)

        if not page_found:
            self.navigation_row_listbox.get_row_at_index(0).activate()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        HostInfo.main_window = self
        ErrorToast.main_window = self
        self.settings = Gio.Settings.new("io.github.flattool.Warehouse")
        event_controller = Gtk.EventControllerKey()
        file_drop = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        self.pages = {
            self.packages_row: PackagesPage(main_window=self),
            self.remotes_row: RemotesPage(main_window=self),
            self.user_data_row: UserDataPage(main_window=self),
            self.snapshots_row: SnapshotPage(main_window=self),
            self.install_row: InstallPage(main_window=self),
        }
        self.navigation_row_listbox.connect("row-activated", self.navigation_handler)
        self.show_saved_page()
        self.refresh_lockouts = []
        self.refresh_requested = False

        # Apply
        self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-fullscreen", self, "fullscreened", Gio.SettingsBindFlags.DEFAULT)
        self.add_controller(event_controller)
        # self.scrolled_window.add_controller(file_drop)
        # self.main_split.set_content(PackagesPage(self))
        if Config.DEVEL:
            self.add_css_class("devel")

        # Connections
        event_controller.connect("key-pressed", self.key_handler)
        # file_drop.connect("drop", self.drop_callback)
        self.refresh_button.connect("clicked", self.refresh_handler)
        
        # self.activate_row(self.user_data_row)
        # self.main_split.set_show_sidebar(self.settings.get_boolean("sidebar-shown"))
        # GLib.idle_add(lambda *_: self.main_split.set_show_sidebar(False))
        # print(self.settings.get_boolean("sidebar-shown"))
        # self.main_split.connect("notify::show-sidebar", self.save_sidebar_state)

        self.start_loading()
        HostInfo.get_flatpaks(callback=self.end_loading)
        # GLib.idle_add(lambda *_: self.main_split.set_show_sidebar(False))
