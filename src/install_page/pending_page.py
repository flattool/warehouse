from gi.repository import Adw, Gtk
from src.host_info import HostInfo
from src.install_page.result_row import ResultRow
import gettext

_ = gettext.gettext


class AddedGroup(Adw.PreferencesGroup):
	__gtype_name__ = "AddedGroup"

	def add_row(self, row):
		self.rows.append(row)
		self.add(row)

	def rem_row(self, row):
		if row in self.rows:
			self.rows.remove(row)
			self.remove(row)

	def remove_all(self, *args):
		while len(self.rows) > 0 and (row := self.rows[0]):
			row.activate()

	def __init__(self, remote, installation, **kwargs):
		super().__init__(**kwargs)

		self.remote = remote
		self.installation = installation
		self.rows = []

		self.set_title(f"{remote.title}")
		self.set_description(_("Installation: {}").format(installation))

		remove_all = Gtk.Button(
			child=Adw.ButtonContent(
				icon_name="warehouse:list-remove-all-symbolic",
				label=_("Remove All"),
			),
			valign=Gtk.Align.CENTER,
		)
		remove_all.add_css_class("flat")
		remove_all.connect("clicked", self.remove_all)
		self.set_header_suffix(remove_all)


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/install_page/pending_page.ui")
class PendingPage(Adw.NavigationPage):
	__gtype_name__ = "PendingPage"
	gtc = Gtk.Template.Child

	stack = gtc()
	main_view = gtc()
	none_pending = gtc()
	preferences_page = gtc()
	install_button = gtc()

	def add_package_row(self, row):
		self.added_packages.append(row.package)
		row.set_state(ResultRow.PackageState.SELECTED)
		key = f"{row.package.remote}<>{row.package.installation}"
		added_row = ResultRow(row.package, ResultRow.PackageState.ADDED, row.origin_list_box)
		group = None
		try:
			group = self.groups[key]
			group.add_row(added_row)
		except KeyError:
			group = AddedGroup(added_row.package.remote, added_row.package.installation)
			group.add_row(added_row)
			self.groups[key] = group
			self.preferences_page.add(group)

		added_row.connect("activated", self.remove_package_row, group)
		self.stack.set_visible_child(self.main_view)

	def remove_package_row(self, row, group):
		# row.origin_row.set_state(ResultRow.PackageState.NEW)
		for item in row.origin_list_box:
			if item.state == ResultRow.PackageState.SELECTED and item.package.is_similar(row.package):
				item.set_state(ResultRow.PackageState.NEW)
				break

		group.rem_row(row)
		if row.package in self.added_packages:
			self.added_packages.remove(row.package)

		if len(group.rows) == 0:
			key = f"{row.package.remote}<>{row.package.installation}"
			self.groups.pop(key, None)
			self.preferences_page.remove(group)

		if len(self.added_packages) == 0:
			self.stack.set_visible_child(self.none_pending)

		install_page = HostInfo.main_window.pages[HostInfo.main_window.install_row]
		install_page.package_removed()

	def on_install(self, *args):
		package_requests = []
		for key, group in self.groups.items():
			item = {
				"remote": group.remote.name,
				"installation": group.installation,
				"package_names": [],
				"extra_flags": [],
			}
			for row in group.rows:
				item["package_names"].append(row.package.app_id)

			package_requests.append(item)

		install_page = HostInfo.main_window.pages[HostInfo.main_window.install_row]
		install_page.install_packages(package_requests)

	def reset(self):
		for key, group in self.groups.items():
			self.preferences_page.remove(group)

		self.groups.clear()
		self.added_packages.clear()
		self.stack.set_visible_child(self.none_pending)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		# Extra Object Creation
		self.groups = {}  # remote<>installation: adw.preference_group
		self.added_packages = []

		# Connections
		self.install_button.connect("clicked", self.on_install)

		# Apply
