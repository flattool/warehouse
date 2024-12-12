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

from gi.repository import Adw, Gdk, Gio, Gtk
from .host_info import HostInfo
from .packages_page import PackagesPage
from .remotes_page import RemotesPage
from .user_data_page import UserDataPage
from .snapshot_page import SnapshotPage
from .install_page import InstallPage
from .error_toast import ErrorToast
from .const import Config


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/main_window/window.ui")
class WarehouseWindow(Adw.ApplicationWindow):
	__gtype_name__ = "WarehouseWindow"
	gtc = Gtk.Template.Child
	main_breakpoint = gtc()
	toast_overlay = gtc()
	file_drop_revealer = gtc()
	main_split = gtc()
	file_drop_view = gtc()
	stack = gtc()
	refresh_button = gtc()
	main_menu = gtc()
	navigation_row_listbox = gtc()
	packages_row = gtc()
	remotes_row = gtc()
	user_data_row = gtc()
	snapshots_row = gtc()
	install_row = gtc()

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
		self.remove_refresh_lockout("refresh handler direct")

	def do_refresh(self):
		self.start_loading()
		self.refresh_button.set_sensitive(False)
		HostInfo.get_flatpaks(callback=self.end_loading)

	def refresh_handler(self, *args):
		if len(self.refresh_lockouts) == 0:
			self.add_refresh_lockout("refresh handler direct")
			self.do_refresh()
		elif "refresh handler direct" in self.refresh_lockouts:
			return
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
		if self.main_split.get_collapsed():
			self.main_split.set_show_sidebar(False)

		row = row.get_child()
		page = self.pages[row]
		self.stack.set_visible_child(page)
		self.settings.set_string("page-shown", page.page_name)

	def activate_row(self, nav_row):
		idx = 0
		while row := self.navigation_row_listbox.get_row_at_index(idx):
			idx += 1
			if row.get_child() is nav_row:
				row.activate()
				break

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

	def on_file_drop(self, drop_target, value, x, y):
		# needed for X11
		self.on_drop_leave()

		try:
			paks = []
			remotes = []
			for file in value:
				path = file.get_path()
				if path.endswith(".flatpak") or path.endswith(".flatpakref"):
					paks.append(Gio.File.new_for_path(path))
				elif path.endswith(".flatpakrepo"):
					remotes.append(path)
				else:
					dialog = Adw.AlertDialog(
						heading=_("Unsupported Filetype"),
						body=_("Only .flatpak, .flatpakref, and .flatpakrepo files are supported."),
					)
					dialog.add_response("continue", _("OK"))
					dialog.present(self)
					return

			if len(remotes) > 0 and len(paks) > 0:
				dialog = Adw.AlertDialog(
					heading=_("Mixed Filetypes"),
					body=_("Flatpaks and remotes cannot be installed at the same time."),
				)
				dialog.add_css_class("error")
				dialog.add_response("continue", _("OK"))
				dialog.present(self)
				return

			if len(remotes) > 1:
				dialog = Adw.AlertDialog(
					heading=_("Too Many Remotes"),
					body=_("Only one remote at a time is supported."),
				)
				dialog.add_response("continue", _("OK"))
				dialog.present(self)
				return

			if len(remotes) == 1:
				# Adding a remote
				self.activate_row(self.remotes_row)
				remotes_page = self.pages[self.remotes_row]
				remotes_page.local_file_handler(remotes[0])
			elif len(paks) > 0:
				# Add packages
				self.activate_row(self.install_row)
				install_page = self.pages[self.install_row]
				install_page.select_page.file_dialog_handler(paks)

		except Exception as e:
			self.toast_overlay.add_toast(ErrorToast(_("Could not open files"), str(e)).toast)

	def on_drop_enter(self, *args):
		self.main_split.add_css_class("blurred")
		self.file_drop_revealer.set_reveal_child(True)
		return 1

	def on_drop_leave(self, *args):
		self.main_split.remove_css_class("blurred")
		self.file_drop_revealer.set_reveal_child(False)

	def switch_page_shortcut_handler(self, letter):
		self.activate_row(self.shortcut_to_pages[letter])

	def key_handler(self, controller, keyval, keycode, state):
		page = self.stack.get_visible_child()
		if keyval == Gdk.KEY_BackSpace or keyval == Gdk.KEY_Delete:
			try:
				if page.select_button.get_active():
					page.on_backspace_handler()
			except AttributeError:
				pass
		elif keyval == Gdk.KEY_Escape:
			try:
				page.on_escape_handler()
			except AttributeError:
				pass

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		# Extra Object Creation
		HostInfo.main_window = self
		ErrorToast.main_window = self
		self.settings = Gio.Settings.new("io.github.flattool.Warehouse")
		self.pages = {
			self.packages_row: PackagesPage(main_window=self),
			self.remotes_row: RemotesPage(main_window=self),
			self.user_data_row: UserDataPage(main_window=self),
			self.snapshots_row: SnapshotPage(main_window=self),
			self.install_row: InstallPage(main_window=self),
		}
		self.shortcut_to_pages = {
			"p": self.packages_row,
			"m": self.remotes_row,
			"d": self.user_data_row,
			"s": self.snapshots_row,
			"i": self.install_row,
		}
		self.navigation_row_listbox.connect("row-activated", self.navigation_handler)
		self.show_saved_page()
		self.refresh_lockouts = []
		self.refresh_requested = False
		file_drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
		event_controller = Gtk.EventControllerKey()

		# Apply
		self.add_controller(file_drop)
		self.add_controller(event_controller)
		self.settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.DEFAULT)
		self.settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.DEFAULT)
		self.settings.bind("is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT)
		self.settings.bind("is-fullscreen", self, "fullscreened", Gio.SettingsBindFlags.DEFAULT)
		if Config.DEVEL:
			self.add_css_class("devel")

		# Connections
		file_drop.connect("drop", self.on_file_drop)
		file_drop.connect("enter", self.on_drop_enter)
		file_drop.connect("leave", self.on_drop_leave)
		event_controller.connect("key-pressed", self.key_handler)
		self.refresh_button.connect("clicked", self.refresh_handler)

		# Apply again
		self.start_loading()
		HostInfo.get_flatpaks(callback=self.end_loading)
