from gi.repository import Adw, Gtk, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .loading_status import LoadingStatus
from .installation_chooser import InstallationChooser
import subprocess, re

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/add_remote_dialog.ui")
class AddRemoteDialog(Adw.Dialog):
	__gtype_name__ = "AddRemoteDialog"
	gtc = Gtk.Template.Child

	toast_overlay = gtc()
	cancel_button = gtc()
	apply_button = gtc()
	content_page = gtc()
	title_row = gtc()
	name_row = gtc()
	url_row = gtc()
	installation_chooser = gtc()
	is_open = False

	def on_apply(self, *args):
		self.parent_page.status_stack.set_visible_child(self.parent_page.adding_view)
		self.apply_button.set_sensitive(False)
		error = [None]
		def thread(*args):
			HostInfo.main_window.add_refresh_lockout("adding remote")
			cmd = [
				'flatpak-spawn', '--host',
				'flatpak', 'remote-add',
				f'--title={self.title_row.get_text()}',
				self.name_row.get_text(),
				self.url_row.get_text(),
			]
			installation = self.installation_chooser.get_installation()
			if installation == "user" or installation == "system":
				cmd.append(f"--{installation}")
			else:
				cmd.append(f"--installation={installation}")

			try:
				subprocess.run(cmd, check=True, capture_output=True, text=True)
			except subprocess.CalledProcessError as cpe:
				error[0] = cpe.stderr
			except Exception as e:
				error[0] = e

		def callback(*args):
			HostInfo.main_window.remove_refresh_lockout("adding remote")
			if error[0]:
				self.parent_page.status_stack.set_visible_child(self.parent_page.main_view)
				self.apply_button.set_sensitive(True)
				self.parent_page.toast_overlay.add_toast(ErrorToast(_("Could not add remote"), str(error[0])).toast)
			else:
				self.main_window.refresh_handler()
				self.parent_page.toast_overlay.add_toast(Adw.Toast(title=_("Added {}").format(self.title_row.get_text())))

		Gio.Task.new(None, None, callback).run_in_thread(thread)
		self.close()

	def check_entries(self, row):
		is_passing = re.match(self.rexes[row], row.get_text())
		if is_passing:
			row.remove_css_class("error")
		else:
			row.add_css_class("error")

		match row:
			case self.title_row:
				self.title_passes = bool(is_passing)
			case self.name_row:
				self.name_passes = bool(is_passing)
			case self.url_row:
				self.url_passes = bool(is_passing)

		self.apply_button.set_sensitive(self.title_passes and self.name_passes and self.url_passes)

	def present(self, *args, **kwargs):
		if self.__class__.is_open:
			return

		self.__class__.is_open = True
		super().present(*args, **kwargs)

	def on_close(self, *args):
		self.__class__.is_open = False

	def __init__(self, main_window, parent_page, remote_info=None, **kwargs):
		super().__init__(**kwargs)

		# Extra Object Creation
		self.string_list = Gtk.StringList(strings=HostInfo.installations)
		self.main_window = main_window
		self.parent_page = parent_page

		self.rexes = {
			self.title_row: r"^(?=.*[A-Za-z0-9])[A-Za-z0-9._-]+( +[A-Za-z0-9._-]+)*$",
			self.name_row: r"^[a-zA-Z0-9\-._]+$",
			self.url_row: r"^[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;= ]+$",
		}
		self.title_passes = False
		self.name_passes = False
		self.url_passes = False

		# Apply
		self.installation_chooser.set_content_strings(_("remote"), False)
		if remote_info:
			self.title_row.set_text(remote_info["title"])
			self.name_row.set_text(remote_info["name"])
			self.url_row.set_text(remote_info["link"])
			if remote_info["description"] == "local file":
				self.check_entries(self.title_row)
				self.check_entries(self.name_row)
				self.check_entries(self.url_row)
				self.url_row.set_editable(False)
			else:
				self.title_row.set_editable(False)
				self.name_row.set_editable(False)
				self.url_row.set_editable(False)
				self.apply_button.set_sensitive(True)
		else:
			self.apply_button.set_sensitive(False)

		# Connections
		self.connect("closed", self.on_close)
		self.cancel_button.connect("clicked", lambda *_: self.close())
		self.apply_button.connect("clicked", self.on_apply)
		self.title_row.connect("changed", self.check_entries)
		self.name_row.connect("changed", self.check_entries)
		self.url_row.connect("changed", self.check_entries)
