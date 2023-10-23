# main.py
#
# Copyright 2023 Heliguy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
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

import sys
import gi

# import subprocess

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Gio, Adw, GLib
from .window import WarehouseWindow
from .remotes_window import RemotesWindow
from .orphans_window import OrphansWindow

class WarehouseApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.flattool.Warehouse",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("search", self.on_search_action, ["<primary>f"])
        self.create_action("manage-data-folders", self.manage_data_shortcut)
        self.create_action("toggle-batch-mode", self.batch_mode_shortcut, ["<primary>b", "<primary>Return"])
        self.create_action("toggle-batch-mode-keypad", self.batch_mode_shortcut, ["<primary>KP_Enter"]) # This action is not added to the shortcuts window
        self.create_action("manage-data-folders", self.manage_data_shortcut, ["<primary>d"])
        self.create_action("refresh-list", self.refresh_list_shortcut, ["<primary>r", "F5"])
        self.create_action("show-remotes-window", self.show_remotes_shortcut, ["<primary>m"])
        self.create_action("set-filter", self.filters_shortcut, ["<primary>t"])
        self.create_action("install-from-file", self.install_from_file, ["<primary>o"])
        self.create_action("open-menu", self.main_menu_shortcut, ["F10"])

    def batch_mode_shortcut(self, widget, _):
        button = self.props.active_window.batch_mode_button
        button.set_active(not button.get_active())

    def manage_data_shortcut(self, widget, _):
        OrphansWindow(self.props.active_window).present()

    def refresh_list_shortcut(self, widget, _):
        self.props.active_window.refresh_list_of_flatpaks(widget, True)

    def show_remotes_shortcut(self, widget, _):
        RemotesWindow(self.props.active_window).present()

    def filters_shortcut(self, widget, _):
        window = self.props.active_window
        window.filterWindowKeyboardHandler(window)

    def main_menu_shortcut(self, widget, _):
        window = self.props.active_window
        window.main_menu.set_active(True)

    def file_callback(self, object, result):
        window = self.props.active_window
        try:
            file = object.open_finish(result)
            window.install_file(file.get_path())
        except GLib.GError:
            pass

    def install_from_file(self, widget, _a):
        window = self.props.active_window

        filter = Gtk.FileFilter(name=_("Flatpaks"))
        filter.add_suffix("flatpak")
        filter.add_suffix("flatpakref")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter)
        file_chooser = Gtk.FileDialog()
        file_chooser.set_filters(filters)
        file_chooser.set_default_filter(filter)
        file_chooser.open(window, None, self.file_callback)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = WarehouseWindow(application=self)
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Warehouse",
            application_icon="io.github.flattool.Warehouse",
            developer_name="Heliguy",
            version="1.3.0",
            developers=["Heliguy https://github.com/heliguy4599", "kramo https://kramo.hu"],
            artists=["Heliguy https://github.com/heliguy4599", "kramo https://kramo.hu", "eryn https://github.com/hericiumvevo"],
            copyright='© 2023 Heliguy',
            license_type=Gtk.License.GPL_3_0_ONLY,
            website='https://github.com/flattool/warehouse',
            support_url='https://matrix.to/#/#warehouse-development:matrix.org',
            issue_url='https://github.com/flattool/warehouse/issues')
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print("app.preferences action activated")

    def on_search_action(self, widget, _):
        self.props.active_window.search_bar.set_search_mode(not self.props.active_window.search_bar.get_search_mode())

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

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


def main(version):
    """The application's entry point."""
    app = WarehouseApplication()
    return app.run(sys.argv)
