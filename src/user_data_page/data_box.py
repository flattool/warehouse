from gi.repository import Adw, Gtk, GLib, Gio
from src.host_info import HostInfo
from src.gtk.error_toast import ErrorToast
from src.gtk.attempt_install_dialog import AttemptInstallDialog
import subprocess
import gettext

_ = gettext.gettext

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/data_box.ui")
class DataBox(Gtk.ListBox):
	__gtype_name__ = "DataBox"
	gtc = Gtk.Template.Child

	row = gtc()
	image = gtc()
	title_label = gtc()
	subtitle_label = gtc()
	spinner = gtc()
	size_label = gtc()

	copy_button = gtc()
	open_button = gtc()
	install_button = gtc()
	trash_button = gtc()
	check_button = gtc()

	def human_readable_size(self):
		working_size = self.size
		units = ["KB", "MB", "GB", "TB"]
		# size *= 1024
		for unit in units:
			if working_size < 1024:
				return f"~ {round(working_size)} {unit}"
			working_size /= 1024
		return f"~ {round(working_size)} PB"

	def get_size(self, *args):
		self.size = int(subprocess.run(["du", "-s", self.data_path], capture_output=True, text=True).stdout.split("\t")[0])

	def show_size(self):
		def callback(*args):
			self.size_label.set_label(self.human_readable_size())
			self.spinner.set_visible(False)
			if self.callback:
				self.callback(self.size)

		Gio.Task.new(None, None, callback).run_in_thread(self.get_size)

	def idle_stuff(self):
		self.title_label.set_label(self.title)
		self.subtitle_label.set_label(self.subtitle)
		self.install_button.set_visible(self.is_leftover)
		if self.icon_path:
			self.image.add_css_class("icon-dropshadow")
			self.image.set_from_file(self.icon_path)

	def copy_handler(self, *args):
		try:
			HostInfo.clipboard.set(self.data_path)
			self.toast_overlay.add_toast(Adw.Toast.new(_("Copied data path")))
		except Exception as e:
			self.toast_overlay.add_toast(ErrorToast(_("Could not copy data path"), str(e)).toast)

	def open_handler(self, *args):
		try:
			Gio.AppInfo.launch_default_for_uri(f"file://{self.data_path}", None)
			self.toast_overlay.add_toast(Adw.Toast.new(_("Opened data folder")))
		except GLib.GError as e:
			self.toast_overlay.add_toast(ErrorToast(_("Could not open folder"), str(e)).toast)

	def install_handler(self, *args):
		self.parent_page.should_rclick = False

		def why_cant_this_just_be_a_lambda(*args):
			self.parent_page.should_rclick = True

		AttemptInstallDialog([self.subtitle], why_cant_this_just_be_a_lambda)

	def trash_handler(self, *args):
		self.failed_trash = False

		def thread(*args):
			try:
				subprocess.run(["gio", "trash", self.data_path], check=True, text=True, capture_output=True)
				properties_page = HostInfo.main_window.pages[HostInfo.main_window.packages_row].properties_page
				properties_package = properties_page.package
				if not properties_package is None:
					properties_page.set_properties(properties_package, True)

				snapshot_list_page = HostInfo.main_window.pages[HostInfo.main_window.snapshots_row].list_page
				snapshot_list_package = snapshot_list_page.package_or_folder
				if not snapshot_list_package is None:
					snapshot_list_page.set_snapshots(snapshot_list_package, True)

			except subprocess.CalledProcessError as cpe:
				self.failed_trash = cpe.stderr
			except Exception as e:
				self.failed_trash = e

		def callback(*args):
			if self.failed_trash:
				self.toast_overlay.add_toast(ErrorToast(_("Could not trash data"), str(self.failed_trash)).toast)
			else:
				self.toast_overlay.add_toast(Adw.Toast.new("Trashed data"))
				if self.trash_callback:
					self.trash_callback(self)

		def on_response(_, response):
			self.parent_page.should_rclick = True
			if response != "continue":
				return

			Gio.Task.new(None, None, callback).run_in_thread(thread)

		self.parent_page.should_rclick = False
		dialog = Adw.AlertDialog(heading=_("Trash {}'s Data?").format(self.title), body=_("{}'s data will be sent to the trash").format(self.title))
		dialog.add_response("cancel", _("Cancel"))
		dialog.add_response("continue", _("Continue"))
		dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
		dialog.connect("response", on_response)
		dialog.present(HostInfo.main_window)

	def __init__(self, parent_page, toast_overlay, is_leftover, title, subtitle, data_path, icon_path=None, callback=None, trash_callback=None, **kwargs):
		super().__init__(**kwargs)

		# Extra Object Creation
		self.parent_page = parent_page
		self.toast_overlay = toast_overlay
		self.is_leftover = is_leftover
		self.title = title
		self.subtitle = subtitle
		self.icon_path = icon_path
		self.data_path = data_path
		self.callback = callback
		self.trash_callback = trash_callback
		self.size = None
		self.failed_trash = None

		# Apply
		self.idle_stuff()
		self.show_size()
		if subtitle == "io.github.flattool.Warehouse":
			self.check_button.set_active = lambda *_: None
			self.check_button.set_sensitive(False)
			self.trash_button.set_sensitive(False)

		# Connections
		self.copy_button.connect("clicked", self.copy_handler)
		self.open_button.connect("clicked", self.open_handler)
		self.install_button.connect("clicked", self.install_handler)
		self.trash_button.connect("clicked", self.trash_handler)
