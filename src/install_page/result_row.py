from gi.repository import Adw, Gtk, GLib
from enum import Enum


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/result_row.ui")
class ResultRow(Adw.ActionRow):
	__gtype_name__ = "ResultRow"
	gtc = Gtk.Template.Child

	version_label = gtc()
	branch_label = gtc()
	add_image = gtc()
	sub_image = gtc()
	selected_image = gtc()
	installed_image = gtc()

	class PackageState(Enum):
		NEW = 0
		SELECTED = 1
		ADDED = 2
		INSTALLED = 3

	def idle_stuff(self):
		self.set_title(GLib.markup_escape_text(self.package.name))
		self.set_subtitle(self.package.app_id)
		self.version_label.set_label(GLib.markup_escape_text(self.package.version))
		self.branch_label.set_label(GLib.markup_escape_text(self.package.branch))
		self.version_label.set_visible(len(self.version_label.get_label()) != 0)
		self.branch_label.set_visible(len(self.branch_label.get_label()) != 0)

	def set_state(self, state):
		if state == self.state:
			return

		self.state = state
		self.add_image.set_visible(False)
		self.sub_image.set_visible(False)
		self.selected_image.set_visible(False)
		self.installed_image.set_visible(False)
		match state:
			case self.PackageState.NEW:
				self.set_sensitive(True)
				self.set_tooltip_text(_("Add Package to Queue"))
				self.add_image.set_visible(True)
			case self.PackageState.SELECTED:
				self.set_sensitive(False)
				self.set_tooltip_text(_("Package has been Added to Queue"))
				self.selected_image.set_visible(True)
			case self.PackageState.ADDED:
				self.set_sensitive(True)
				self.set_tooltip_text(_("Remove Package from Queue"))
				self.sub_image.set_visible(True)
			case self.PackageState.INSTALLED:
				self.set_sensitive(False)
				self.set_tooltip_text(_("This Package is Already Installed"))
				self.installed_image.set_visible(True)

	def __init__(self, package, package_state, origin_list_box, **kwargs):
		super().__init__(**kwargs)

		# Extra Object Creation
		self.state = None
		self.package = package
		self.origin_list_box = origin_list_box

		# Connections

		# Apply
		GLib.idle_add(self.idle_stuff)
		self.set_state(package_state)
