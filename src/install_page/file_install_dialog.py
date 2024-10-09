from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/file_install_dialog.ui")
class FileInstallDialog(Adw.AlertDialog):
	__gtype_name__ = "FileInstallDialog"
	gtc = Gtk.Template.Child
	
	packages_group = gtc()
	installation_row = gtc()
	
	def generate_list(self):
		for file in self.files:
			row = Adw.ActionRow(title=file.get_basename())
			row.add_prefix(Gtk.Image(icon_name="flatpak-symbolic"))
			self.packages_group.add(row)
			
	def on_response(self, dialog, response):
		if response != "continue":
			return
			
		# self.installation_row.get_selected_item().get_string()
		self.on_add("user", self.files)
			
	def __init__(self, parent_page, files, on_add, **kwargs):
		super().__init__(**kwargs)
		
		# Extra Object Creation
		self.parent_page = parent_page
		self.files = files
		self.on_add = on_add
		
		# Apply
		self.generate_list()
		self.installation_row.set_model(Gtk.StringList(strings=HostInfo.installations))
		if len(files) > 1:
			self.set_heading(_("Add These Packages?"))
			self.set_body(_("Queue these packages to be installed"))
		else:
			self.set_heading(_("Add This Package?"))
			self.set_body(_("Queue this package to be installed"))
			
		# Connections
		self.connect("response", self.on_response)
