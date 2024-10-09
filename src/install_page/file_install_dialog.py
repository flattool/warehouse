from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .installation_chooser import InstallationChooser

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/file_install_dialog.ui")
class FileInstallDialog(Adw.AlertDialog):
	__gtype_name__ = "FileInstallDialog"
	gtc = Gtk.Template.Child
	
	packages_group = gtc()
	installation_chooser = gtc()
	
	def generate_list(self):
		for file in self.files:
			row = Adw.ActionRow(title=file.get_basename())
			row.add_prefix(Gtk.Image(icon_name="flatpak-symbolic"))
			self.packages_group.add(row)
			
	def on_response(self, dialog, response):
		if response != "continue":
			return
			
		# self.installation_row.get_selected_item().get_string()
		self.on_add(self.installation_chooser.get_installation(), self.files)
			
	def __init__(self, parent_page, files, on_add, **kwargs):
		super().__init__(**kwargs)
		
		# Extra Object Creation
		self.parent_page = parent_page
		self.files = files
		self.on_add = on_add
		
		# Apply
		self.generate_list()
		if len(files) > 1:
			self.set_heading(_("Review Packages"))
			self.set_body(_("The following packages will be added to the queue"))
			self.installation_chooser.set_content_strings(_("Packages"), True)
		else:
			self.set_heading(_("Review Package"))
			self.set_body(_("The following package will be added to the queue"))
			self.installation_chooser.set_content_strings(_("package"), False)
		
		# Connections
		self.connect("response", self.on_response)
