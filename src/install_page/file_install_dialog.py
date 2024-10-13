from gi.repository import Adw, Gtk

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/file_install_dialog.ui")
class FileInstallDialog(Adw.Dialog):
	__gtype_name__ = "FileInstallDialog"
	gtc = Gtk.Template.Child
	
	packages_group = gtc()
	installation_chooser = gtc()
	cancel_button = gtc()
	apply_button = gtc()
	
	def generate_list(self):
		for file in self.files:
			row = Adw.ActionRow(title=file.get_basename())
			row.add_prefix(Gtk.Image(icon_name="flatpak-symbolic"))
			self.packages_group.add(row)
			
	def on_response(self, *args):
		self.on_add(self.installation_chooser.get_installation(), self.files)
		self.close()
		
	def __init__(self, parent_page, files, on_add, **kwargs):
		super().__init__(**kwargs)
		
		# Extra Object Creation
		self.parent_page = parent_page
		self.files = files
		self.on_add = on_add
		
		# Apply
		self.generate_list()
		if len(files) > 1:
			self.set_title(_("Install Packages"))
			# self.packages_group.set_title(_("Review Packages"))
			self.packages_group.set_description(_("The following packages will be installed"))
			self.installation_chooser.set_content_strings(_("Packages"), True)
		else:
			self.set_title(_("Install a Package"))
			# self.packages_group.set_title(_("Review Package"))
			self.packages_group.set_description(_("The following package will be installed"))
			self.installation_chooser.set_content_strings(_("package"), False)
		
		# Connections
		self.cancel_button.connect("clicked", lambda *_: self.close())
		self.apply_button.connect("clicked", self.on_response)
