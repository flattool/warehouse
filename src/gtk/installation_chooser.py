from gi.repository import Adw, Gtk
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/gtk/installation_chooser.ui")
class InstallationChooser(Adw.PreferencesGroup):
	__gtype_name__ = 'InstallationChooser'
	gtc = Gtk.Template.Child
	
	user_row = gtc()
	system_row = gtc()
	single_row = gtc()
	choice_row = gtc()
	user_check = gtc()
	system_check = gtc()
	single_check = gtc()
	choice_check = gtc()
	
	def get_installation(self):
		for button, func in self.check_buttons.items():
			if button.get_active():
				HostInfo.main_window.toast_overlay.add_toast(Adw.Toast(title=func()))
				return func()
				
		return "" # Case for when no button is active (which shouldn't happen)
		
	def set_content_strings(self, content_name, is_plural):
		if is_plural:
			self.user_row.set_subtitle(_("These {} will only be available to you").format(content_name))
			self.system_row.set_subtitle(_("These {} will be available to everyone").format(content_name))
		else:
			self.user_row.set_subtitle(_("This {} will only be available to you").format(content_name))
			self.system_row.set_subtitle(_("This {} will be available to everyone").format(content_name))
		
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.check_buttons = {
			self.user_check  : lambda: "user",
			self.system_check: lambda: "system",
			self.single_check: self.single_row.get_title,
			self.choice_check: lambda: self.choice_row.get_selected_item().get_string(),
		}
		
		# Apply
		custom_installations = []
		for installation in HostInfo.installations:
			if installation.startswith("user") or installation.startswith("system"):
				continue
				
			custom_installations.append(installation)
			
		if len(custom_installations) == 1:
			self.single_row.set_visible(True)
			self.single_row.set_title(custom_installations[0])
		elif len(custom_installations) > 1:
			self.choice_row.set_visible(True)
			self.choice_row.set_model(Gtk.StringList(strings=custom_installations))
			
		# Connections
		self.choice_row.connect("notify::css-classes", lambda *_: self.choice_check.activate())