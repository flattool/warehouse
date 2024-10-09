from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import error_toast

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/file_install_dialog.ui")
class FileInstallDialog(Adw.Dialog):
	__gtype_name__ = "FileInstallDialog"
	gtc = Gtk.Template.Child
	
	cancel_button = gtc()
	apply_button = gtc()
	toast_overlay = gtc()
	content_page = gtc()
	list_box = gtc()
	
	def generate_list(self):
		for file in self.files:
			row = Adw.ActionRow(title=file.get_basename())
			self.list_box.append(row)
			
	def __init__(self, parent_page, files, **kwargs):
		super().__init__(**kwargs)
		
		# Extra Object Creation
		self.parent_page = parent_page
		self.files = files
		
		# Apply
		self.generate_list()
		
		# Connections
