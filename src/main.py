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
from .const import Config
from .error_toast import ErrorToast

class WarehouseApplication(Adw.Application):
    """The main application singleton class."""
    
    troubleshooting = "OS: {os}\nWarehouse version: {wv}\nGTK: {gtk}\nlibadwaita: {adw}\nApp ID: {app_id}\nProfile: {profile}\nLanguage: {lang}"
    version = Config.VERSION
    
    def __init__(self):
        super().__init__(
            application_id="io.github.flattool.Warehouse",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("open-menu", lambda *_: self.props.active_window.main_menu.popup(), ["F10"])
        self.create_action("refresh", lambda *_: self.props.active_window.refresh_handler(), ["<primary>r", "F5"])
        self.create_action("open-files", self.on_open_files_shortcut, ["<primary>o"])
        
        self.create_action("show-packages-page", lambda *_: self.props.active_window.switch_page_shortcut_handler("p"), ["<primary>p"])
        self.create_action("show-remotes-page", lambda *_: self.props.active_window.switch_page_shortcut_handler("m"), ["<primary>m"])
        self.create_action("show-user-data-page", lambda *_: self.props.active_window.switch_page_shortcut_handler("d"), ["<primary>d"])
        self.create_action("show-snapshots-page", lambda *_: self.props.active_window.switch_page_shortcut_handler("s"), ["<primary>s"])
        self.create_action("show-install-page", lambda *_: self.props.active_window.switch_page_shortcut_handler("i"), ["<primary>i"])
        
        self.create_action("toggle-select-mode", self.on_toggle_select_mode_shortcut, ["<primary>b", "<primary>Return"])
        self.create_action("toggle-selection-kp-enter", self.on_toggle_select_mode_shortcut, ["<primary>KP_Enter"]) # Doesn't show in the shortcuts window
        self.create_action("search-mode", self.on_search_mode_shortcut, ["<primary>f"])
        self.create_action("filter", self.on_filter_shortcut, ["<primary>t"])
        self.create_action("new", self.on_new_shortcut, ["<primary>n"])
        self.create_action("active-data-view", lambda *_: self.on_data_view_shortcut(True), ["<Alt>1"])
        self.create_action("leftover-data-view", lambda *_: self.on_data_view_shortcut(False), ["<Alt>2"])
        
        self.is_dialog_open = False
        
        gtk_version = (
            str(Gtk.MAJOR_VERSION)
            + "."
            + str(Gtk.MINOR_VERSION)
            + "."
            + str(Gtk.MICRO_VERSION)
        )
        adw_version = (
            str(Adw.MAJOR_VERSION)
            + "."
            + str(Adw.MINOR_VERSION)
            + "."
            + str(Adw.MICRO_VERSION)
        )
        os_string = GLib.get_os_info("NAME") + " " + GLib.get_os_info("VERSION")
        lang = GLib.environ_getenv(GLib.get_environ(), "LANG")
        
        self.troubleshooting = self.troubleshooting.format(
            os=os_string,
            wv=self.version,
            gtk=gtk_version,
            adw=adw_version,
            profile=Config.PROFILE,
            app_id=self.get_application_id(),
            lang=lang,
        )
        
    def on_open_files_shortcut(self, *args):
        window = self.props.active_window
        
        def file_choose_callback(object, result):
            try:
                files = object.open_multiple_finish(result)
                if not files:
                    window.toast_overlay.add_toast(ErrorToast(_("Could not add files"), _("No files were found")).toast)
                    return
                    
                window.on_file_drop(None, files, None, None)
            except GLib.GError as gle:
                if not (gle.domain == "gtk-dialog-error-quark" and gle.code == 2):
                    window.toast_overlay.add_toast(ErrorToast(_("Could not add files"), str(gle)).toast)
                    
        file_filter = Gtk.FileFilter(name=_("Flatpaks & Remotes"))
        file_filter.add_suffix("flatpak")
        file_filter.add_suffix("flatpakref")
        file_filter.add_suffix("flatpakrepo")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)
        file_chooser = Gtk.FileDialog()
        file_chooser.set_filters(filters)
        file_chooser.set_default_filter(file_filter)
        file_chooser.open_multiple(window, None, file_choose_callback)
        
    def on_toggle_select_mode_shortcut(self, *args):
        try:
            button = self.props.active_window.stack.get_visible_child().select_button
            button.set_active(not button.get_active())
        except AttributeError:
            pass
            
    def on_search_mode_shortcut(self, *args):
        try:
            button = self.props.active_window.stack.get_visible_child().search_button
            button.set_active(True)
        except AttributeError:
            pass
            
    def on_filter_shortcut(self, *args):
        try:
            button = self.props.active_window.stack.get_visible_child().filter_button
            button.set_active(not button.get_active())
        except AttributeError:
            pass
            
        try:
            button = self.props.active_window.stack.get_visible_child().sort_button
            button.set_active(True)
        except AttributeError:
            pass
            
        try:
            button = self.props.active_window.stack.get_visible_child().show_disabled_button
            if button.get_visible():
                button.set_active(not button.get_active())
        except AttributeError:
            pass
            
    def on_new_shortcut(self, *args):
        page = self.props.active_window.stack.get_visible_child()
        try:
            page.new_custom_handler()
        except AttributeError:
            pass
            
        try:
            page.on_new()
        except AttributeError:
            pass
            
    def on_delete_shortcut(self, *args):
        page = self.props.active_window.stack.get_visible_child()
        try:
            if not page.select_button.get_active():
                return
                
            page.select_trash_handler()
        except AttributeError:
            pass
            
    def on_data_view_shortcut(self, is_active):
        page = self.props.active_window.stack.get_visible_child()
        try:
            adp = page.adp
            ldp = page.ldp
            page.stack.set_visible_child(adp if is_active else ldp)
        except AttributeError:
            pass
            
    def do_activate(self):
        """Called when the application is activated.
        
        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = WarehouseWindow(application=self)
        win.present()
        
    def on_about_action(self, widget, _a):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name="Warehouse",
            application_icon="io.github.flattool.Warehouse",
            developer_name="Heliguy",
            version=self.version,
            developers=[
                "Heliguy https://github.com/heliguy4599",
                "kramo https://kramo.page",
            ],
            artists=[
                "Heliguy https://github.com/heliguy4599",
                "kramo https://kramo.page",
                "Amy https://github.com/AtiusAmy",
                "eryn https://github.com/hericiumvevo",
            ],
            copyright="© 2023 Heliguy",
            license_type=Gtk.License.GPL_3_0_ONLY,
            debug_info=self.troubleshooting,
            # Translators: do one of the following, one per line: Your Name, Your Name <email@email.org>, Your Name https://websi.te
            translator_credits=_("translator-credits"),
            debug_info_filename="{}.txt".format(self.get_application_id()),
            website="https://github.com/flattool/warehouse",
            support_url="https://matrix.to/#/#warehouse-development:matrix.org",
            issue_url="https://github.com/flattool/warehouse/issues",
        )
        about.add_link(_("Donate"), "https://ko-fi.com/heliguy")
        about.add_credit_section(
            _("Contributors"),
            [
                # Contributors: do one of the following, one per line: Your Name, Your Name <email@email.org>, Your Name https://websi.te
                "Win <winsdominoes2018@gmail.com>",
                "Óscar Fernández Díaz",
                "Runar https://github.com/runarcn",
                "skøldis <warehouse@turtle.garden>",
                "Maxim Therrien <maxim@mtsd.ca>",
            ],
        )
        about.present(self.props.active_window)
        
    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print("app.preferences action activated")
        
    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.
        
        Args:
            name: the name of the action
            callback: the function to be called when the action is activated
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
