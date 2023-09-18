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


class WarehouseApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="io.github.heliguy4599.Warehouse",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("search", self.on_search_action, ["<primary>f"])
        self.create_action("manage-data-folders", self.on_manage_data_folders_action)
        self.create_action(
            "toggle-batch-mode",
            self.batch_mode_shortcut,
            ["<primary>b", "<primary>Return"],
        )
        self.create_action(
            "select-all-in-batch-mode", self.select_all_shortcut, ["<primary>a"]
        )
        self.create_action(
            "manage-data-folders", self.manage_data_shortcut, ["<primary>d"]
        )
        self.create_action(
            "refresh-list", self.refresh_list_shortcut, ["<primary>r", "F5"]
        )
        self.create_action("show-runtimes", self.show_runtimes_shortcut, ["<primary>t"])

        self.show_runtimes_stateful = Gio.SimpleAction.new_stateful(
            "show-runtimes", None, GLib.Variant.new_boolean(False)
        )
        self.show_runtimes_stateful.connect("activate", self.on_show_runtimes_action)
        self.add_action(self.show_runtimes_stateful)

    def batch_mode_shortcut(self, widget, _):
        button = self.props.active_window.batch_mode_button
        button.set_active(not button.get_active())

    def select_all_shortcut(self, widget, _):
        batch_button = self.props.active_window.batch_mode_button
        batch_button.set_active(True)
        select_button = self.props.active_window.batch_select_all_button
        select_button.set_active(not select_button.get_active())
        self.props.active_window.batch_select_all_handler(select_button)

    def manage_data_shortcut(self, widget, _):
        self.props.active_window.orphans_window()

    def refresh_list_shortcut(self, widget, _):
        self.props.active_window.refresh_list_of_flatpaks(widget, True)

    def show_runtimes_shortcut(self, widget, _):
        window = self.props.active_window
        window.show_runtimes_toggle_handler(window, not window.show_runtimes)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = WarehouseWindow(application=self)
        win.present()
        # try:
        # subprocess.run(['flattool', 'id', 'abcdefg'], check=True)
        # except subprocess.CalledProcessError:
        # print("Not found")

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Warehouse",
            application_icon="io.github.heliguy4599.Warehouse",
            developer_name="Heliguy",
            version="0.3.0",
            developers=[
                "Heliguy https://github.com/heliguy4599",
                "kramo https://kramo.hu",
            ],
            artists=[
                "Heliguy https://github.com/heliguy4599",
                "kramo https://kramo.hu",
                "eryn https://github.com/hericiumvevo",
            ],
            copyright='© 2023 The Files Authors\n\nThis application comes with absolutely no warranty. See the <a href="https://www.gnu.org/licenses/gpl-3.0.html">GNU General Public License, version 3 only</a> for details.',
        )
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print("app.preferences action activated")

    def on_search_action(self, widget, _):
        self.props.active_window.search_bar.set_search_mode(
            not self.props.active_window.search_bar.get_search_mode()
        )

    def on_manage_data_folders_action(self, widget, _):
        self.props.active_window.orphans_window()

    def on_show_runtimes_action(self, widget, _):
        self.show_runtimes_stateful.set_state(
            GLib.Variant.new_boolean(
                state := (
                    not self.show_runtimes_stateful.get_property("state").get_boolean()
                )
            )
        )
        self.props.active_window.show_runtimes_toggle_handler(state)

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
