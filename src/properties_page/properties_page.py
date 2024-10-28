from gi.repository import Adw, Gtk, GLib, Gio
from .error_toast import ErrorToast
from .host_info import HostInfo
from .change_version_page import ChangeVersionPage
from .uninstall_dialog import UninstallDialog
from .loading_status import LoadingStatus
from .package_install_worker import PackageInstallWorker
import subprocess, os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/properties_page/properties_page.ui")
class PropertiesPage(Adw.NavigationPage):
	__gtype_name__ = 'PropertiesPage'
	gtc = Gtk.Template.Child
	stack = gtc()
	error_tbv = gtc()
	loading_tbv = gtc()
	
	more_menu = gtc()
	more_list = gtc()
	
	nav_view = gtc()
	inner_nav_page = gtc()
	toast_overlay = gtc()
	header_bar = gtc()
	scrolled_window = gtc()
	app_icon = gtc()
	name = gtc()
	description = gtc()
	eol_box = gtc()
	open_app_button = gtc()
	uninstall_button = gtc()
	
	pin_row = gtc()
	pin_switch = gtc()
	data_row = gtc()
	open_data_button = gtc()
	trash_data_button = gtc()
	data_spinner = gtc()
	version_row = gtc()
	mask_label = gtc()
	mask_row = gtc()
	mask_switch = gtc()
	change_version_row = gtc()
	installed_size_row = gtc()
	runtime_row = gtc()
	eol_package_package_status_icon = gtc()
	
	id_row = gtc()
	ref_row = gtc()
	arch_row = gtc()
	branch_row = gtc()
	license_row = gtc()
	
	sdk_row = gtc()
	origin_row = gtc()
	collection_row = gtc()
	installation_row = gtc()
	
	commit_row = gtc()
	parent_row = gtc()
	subject_row = gtc()
	date_row = gtc()
	
	package = None
	
	def set_properties(self, package, refresh=False):
		if package == self.package and not refresh:
			# Do not update the ui if the same app row is clicked
			return
			
		self.reinstall_did_error = False
		self.package = package
		pkg_name = package.info["name"]
		if pkg_name != "":
			self.inner_nav_page.set_title(_("{} Properties").format(package.info["name"]))
			self.name.set_visible(True)
			self.name.set_label(pkg_name)
		else:
			self.name.set_visible(False)
			self.inner_nav_page.set_title(_("Properties"))
			
		if package.icon_path:
			GLib.idle_add(lambda *_: self.app_icon.set_from_file(package.icon_path))
		else:
			GLib.idle_add(lambda *_: self.app_icon.set_from_icon_name("application-x-executable-symbolic"))
			
		self.eol_box.set_visible(package.is_eol)
		self.pin_row.set_visible(package.is_runtime)
		self.open_app_button.set_visible(package.is_runtime)
		self.open_app_button.set_visible(not package.is_runtime)
		self.data_row.set_visible(not package.is_runtime)
		self.uninstall_button.set_sensitive(self.package.info['id'] != "io.github.flattool.Warehouse")
		if package.is_runtime:
			self.runtime_row.set_visible(False)
		else:
			has_path = os.path.exists(package.data_path)
			self.trash_data_button.set_sensitive(has_path and self.package.info['id'] != "io.github.flattool.Warehouse")
			self.open_data_button.set_sensitive(has_path)
			
			if not self.package.dependent_runtime is None:
				self.runtime_row.set_visible(True)
				self.runtime_row.set_subtitle(self.package.dependent_runtime.info["name"])
				self.eol_package_package_status_icon.set_visible(self.package.dependent_runtime.is_eol)
				
			if has_path:
				self.trash_data_button.set_visible(False)
				self.open_data_button.set_visible(False)
				self.data_spinner.set_visible(True)
				self.data_row.set_subtitle(_("Loading User Data"))
				
				def callback(size):
					self.trash_data_button.set_visible(True)
					self.open_data_button.set_visible(True)
					self.data_spinner.set_visible(False)
					self.data_row.set_subtitle(size)
					
				self.package.get_data_size(lambda size: callback(size))
			else:
				self.data_row.set_subtitle(_("No User Data"))
				self.data_spinner.set_visible(False)
				
		cli_info = None
		try:
			cli_info = package.get_cli_info()
			pkg_description = package.cli_info["description"]
			self.description.set_visible(pkg_description != "")
			self.description.set_label(pkg_description)
		except Exception as e:
			self.toast_overlay.add_toast(ErrorToast(_("Could not get properties"), str(e)).toast)
			return
			
		for key, row in self.info_rows.items():
			row.set_visible(False)
			
			try:
				subtitle = cli_info[key]
				row.set_subtitle(subtitle)
				row.set_visible(True)
			except KeyError:
				if key == "version":
					row.set_visible(True)
					row.set_subtitle(_("No version information found"))
				continue
			except Exception as e:
				self.toast_overlay.add_toast(ErrorToast(_("Could not get properties"), str(e)).toast)
				continue
				
		self.mask_label.set_visible(package.is_masked)
		self.mask_switch.set_active(package.is_masked)
		self.pin_switch.set_active(package.is_pinned)
		GLib.idle_add(lambda *_: self.stack.set_visible_child(self.nav_view))
		self.more_list.remove_all()
		if self.open_app_button.get_visible():
			self.more_list.append(self.view_snapshots)
			self.more_list.append(self.copy_launch_command)
			
		self.more_list.append(self.show_details)
		self.more_list.append(self.reinstall)
		
	def open_data_handler(self, *args):
		if error := self.package.open_data():
			self.toast_overlay.add_toast(ErrorToast(_("Could not open data"), str(error)).toast)
			
	def trash_data_handler(self, *args):
		def on_choice(dialog, response):
			if response != 'continue':
				return
			try:
				self.package.trash_data()
				self.set_properties(self.package, refresh=True)
				self.toast_overlay.add_toast(Adw.Toast.new("Trashed User Data"))
				user_data_page = HostInfo.main_window.pages[HostInfo.main_window.user_data_row]
				user_data_page.start_loading()
				user_data_page.end_loading()
				snapshot_list_page = HostInfo.main_window.pages[HostInfo.main_window.snapshots_row].list_page
				snapshot_list_package = snapshot_list_page.package_or_folder
				if not snapshot_list_package is None:
					snapshot_list_page.set_snapshots(snapshot_list_package, True)
					
			except subprocess.CalledProcessError as cpe:
				self.toast_overlay.add_toast(ErrorToast(_("Could not trash data"), cpe.stderr).toast)
			except Exception as e:
				self.toast_overlay.add_toast(ErrorToast(_("Could not trash data"), str(e)).toast)
				
		dialog = Adw.AlertDialog(
			heading=_("Send {}'s User Data to the Trash?").format(self.package.info["name"]),
			body=_("Your settings and data for this app will be sent to the trash")
		)
		dialog.add_response('cancel', _("Cancel"))
		dialog.add_response('continue', _("Trash Data"))
		dialog.connect("response", on_choice)
		dialog.set_response_appearance('continue', Adw.ResponseAppearance.DESTRUCTIVE)
		dialog.present(self.main_window)
		
	def set_mask_handler(self, *args):
		state = not self.mask_switch.get_active()
		def callback(*args):
			if fail := self.package.failed_mask:
				response = _("Could not Disable Updates") if state else _("Could not Enable Updates")
				fail = fail.stderr if type(fail) is subprocess.CalledProcessError else fail
				self.toast_overlay.add_toast(ErrorToast(response, str(fail)).toast)
				GLib.idle_add(lambda *_: self.mask_switch.set_active(not state))
				GLib.idle_add(lambda *_: self.mask_label.set_visible(not state))
			else:
				response = _("Disabled Updates") if state else _("Enabled Updates")
				self.toast_overlay.add_toast(Adw.Toast(title=response))
				GLib.idle_add(lambda *_: self.mask_switch.set_active(state))
				GLib.idle_add(lambda *_: self.mask_label.set_visible(state))
				self.package.app_row.masked_status_icon.set_visible(state)
				
		self.package.set_mask(state, callback)
		
	def set_pin_handler(self, *args):
		state = not self.pin_switch.get_active()
		def callback(*args):
			if fail := self.package.failed_pin:
				response = _("Could not Disable Autoremoval") if state else _("Could not Enable Autoremoval")
				fail = fail.stderr if type(fail) is subprocess.CalledProcessError else fail
				self.toast_overlay.add_toast(ErrorToast(response, str(fail)).toast)
				GLib.idle_add(lambda *_: self.pin_switch.set_active(not state))
			else:
				response = _("Disabled Autoremoval") if state else _("Enabled Autoremoval")
				self.toast_overlay.add_toast(Adw.Toast(title=response))
				GLib.idle_add(lambda *_: self.pin_switch.set_active(state))
				self.package.app_row.pinned_status_icon.set_visible(state)
				
		self.package.set_pin(state, callback)
		
	def uninstall_handler(self, *args):
		def on_choice(should_trash):
			self.packages_page.set_status(self.packages_page.uninstalling)
			self.package.uninstall(callback)
			if should_trash:
				try:
					self.package.trash_data()
					self.set_properties(self.package, refresh=True)
				except subprocess.CalledProcessError as cpe:
					self.toast_overlay.add_toast(ErrorToast(_("Could not trash data"), cpe.stderr).toast)
				except Exception as e:
					self.toast_overlay.add_toast(ErrorToast(_("Could not trash data"), str(e)).toast)
					
		def callback(*args):
			if fail := self.package.failed_uninstall:
				fail = fail.stderr if type(fail) is subprocess.CalledProcessError else fail
				self.toast_overlay.add_toast(ErrorToast(_("Could not uninstall"), str(fail)).toast)
				self.packages_page.set_status(self.packages_page.scrolled_window)
			else:
				self.main_window.refresh_handler()
				HostInfo.main_window.toast_overlay.add_toast(Adw.Toast(title=_("Uninstalled {}").format(self.package.info["name"])))
				
		dialog = UninstallDialog(on_choice, os.path.exists(self.package.data_path), self.package.info["name"])
		dialog.present(self.main_window)
		
	def runtime_row_handler(self, *args):
		new_page = self.__class__()
		new_page.packages_page = self.packages_page
		new_page.set_properties(self.package.dependent_runtime)
		self.nav_view.push(new_page)
		
	def open_app_handler(self, *args):
		self.toast_overlay.add_toast(Adw.Toast(title=_("Opening {}…").format(self.package.info["name"])))
		
		def callback(*args):
			if fail := self.package.failed_app_run:
				fail = fail.stderr if type(fail) is subprocess.CalledProcessError else fail
				self.toast_overlay.add_toast(ErrorToast(_("Could not open {}").format(self.package.info["name"]), str(fail)).toast)
				
		self.package.open_app(callback)
		
	def copy_handler(self, row):
		HostInfo.clipboard.set(row.get_subtitle())
		self.toast_overlay.add_toast(Adw.Toast(title=_("Copied {}").format(row.get_title())))
		
	def change_version_handler(self, row):
		page = ChangeVersionPage(self.packages_page, self.package)
		self.nav_view.push(page)
		
	def reinstall_callback(self):
		HostInfo.main_window.refresh_handler()
		if not self.reinstall_did_error:
			HostInfo.main_window.toast_overlay.add_toast(Adw.Toast(title=_("Reinstalled {}").format(self.package.info['name'])))
			
	def reinstall_error_callback(self, user_facing_label, error_message):
		self.reinstall_did_error = True
		GLib.idle_add(lambda *_: HostInfo.main_window.toast_overlay.add_toast(ErrorToast(user_facing_label, error_message).toast))
		
	def reinstall_handler(self):
		def on_response(dialog, response):
			if response != "continue":
				return
				
			self.reinstall_did_error = False
			PackageInstallWorker.install(
				[{
					"installation": self.package.info['installation'],
					"remote": self.package.info['origin'],
					"package_names": [self.package.info['ref']],
					"extra_flags": ["--reinstall"],
				}],
				self.packages_page.reinstalling,
				self.reinstall_callback,
				self.reinstall_error_callback,
			)
			self.packages_page.set_status(self.packages_page.reinstalling)
			
		dialog = Adw.AlertDialog(
			heading=_("Reinstall {}?").format(self.package.info['name']),
			body=_("This package will be uninstalled, and then reinstalled from the same remote and installation.")
		)
		dialog.add_response("cancel", _("Cancel"))
		dialog.add_response("continue", _("Reinstall"))
		dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
		dialog.connect("response", on_response)
		dialog.present(HostInfo.main_window)
		
	def more_menu_handler(self, listbox, row):
		self.more_menu.popdown()
		match row.get_child():
			case self.view_snapshots:
				snapshots_row = HostInfo.main_window.snapshots_row
				snapshots_page = HostInfo.main_window.pages[snapshots_row]
				HostInfo.main_window.activate_row(snapshots_row)
				snapshots_page.show_snapshot(self.package)
				
			case self.copy_launch_command:
				try:
					HostInfo.clipboard.set(f"flatpak run {self.package.info['ref']}")
					self.toast_overlay.add_toast(Adw.Toast.new(_("Copied launch command")))
				except Exception as e:
					self.toast_overlay.add_toast(ErrorToast(_("Could not copy launch command"), str(e)).toast)
					
			case self.show_details:
				try:
					Gio.AppInfo.launch_default_for_uri(f"appstream://{self.package.info['id']}", None)
				except Exception as e:
					self.toast_overlay.add_toast(ErrorToast(_("Could not show details"), str(e)).toast)
					
			case self.reinstall:
				self.reinstall_handler()
				
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		# Extra Object Creation
		self.main_window = HostInfo.main_window
		self.info_rows = {
			"version": self.version_row,
			"installed": self.installed_size_row,
			
			"id": self.id_row,
			"ref": self.ref_row,
			"arch": self.arch_row,
			"branch": self.branch_row,
			"license": self.license_row,
			
			"sdk": self.sdk_row,
			"origin": self.origin_row,
			"collection": self.collection_row,
			"installation": self.installation_row,
			
			"commit": self.commit_row,
			"parent": self.parent_row,
			"subject": self.subject_row,
			"date": self.date_row,
		}
		self.loading_tbv.set_content(LoadingStatus(_("Loading Properties"), _("This should only take a moment")))
		self.packages_page = None # To be set in packages page
		self.__class__.main_window = self.main_window
		self.view_snapshots = Gtk.Label(halign=Gtk.Align.START, label=_("View Snapshots"))
		self.copy_launch_command = Gtk.Label(halign=Gtk.Align.START, label=_("Copy Launch Command"))
		self.show_details = Gtk.Label(halign=Gtk.Align.START, label=_("Show Details"))
		self.reinstall = Gtk.Label(halign=Gtk.Align.START, label=_("Reinstall"))
		self.reinstall_did_error = False
		
		# Apply
		
		# Connections
		self.more_list.connect("row-activated", self.more_menu_handler)
		self.open_data_button.connect("clicked", self.open_data_handler)
		self.scrolled_window.get_vadjustment().connect("value-changed", lambda adjustment: self.header_bar.set_show_title(not adjustment.get_value() == 0))
		self.trash_data_button.connect("clicked", self.trash_data_handler)
		self.runtime_row.connect("activated", self.runtime_row_handler)
		self.open_app_button.connect("clicked", self.open_app_handler)
		self.uninstall_button.connect("clicked", self.uninstall_handler)
		self.mask_row.connect("activated", self.set_mask_handler)
		self.pin_row.connect("activated", self.set_pin_handler)
		self.change_version_row.connect("activated", self.change_version_handler)
		for key, row in self.info_rows.items():
			if type(row) is Adw.ActionRow:
				row.connect("activated", self.copy_handler)
