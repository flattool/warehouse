from gi.repository import Adw, Gtk, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .snapshot_box import SnapshotBox
from .loading_status import LoadingStatus
from .new_snapshot_dialog import NewSnapshotDialog
import os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/snapshots_list_page.ui")
class SnapshotsListPage(Adw.NavigationPage):
	__gtype_name__ = "SnapshotsListPage"
	gtc = Gtk.Template.Child
	
	toolbar_view = gtc()
	listbox = gtc()
	toast_overlay = gtc()
	open_button = gtc()
	new_button = gtc()
	
	def thread(self, *args):
		is_leftover = type(self.package_or_folder) is str
		for snapshot in os.listdir(folder := f"{self.snapshots_path}{self.current_folder}/"):
			if snapshot.endswith(".json"):
				continue
				
			row = SnapshotBox(self, snapshot, folder, self.toast_overlay)
			row.apply_button.set_sensitive(not is_leftover)
			self.snapshots_rows.append(row)
			if is_leftover:
				row.apply_button.set_tooltip_text(_("App not Installed"))
				
	def callback(self, *args):
		if len(self.snapshots_rows) == 0:
			self.parent_page.refresh()
			return
			
		for i, row in enumerate(self.snapshots_rows):
			self.listbox.append(row)
			self.listbox.get_row_at_index(i).set_activatable(False)
			
	def set_snapshots(self, package_or_folder, refresh=False):
		if package_or_folder == self.package_or_folder and not refresh:
			return
			
		folder = None
		self.package_or_folder = package_or_folder
		if type(package_or_folder) is str:
			self.set_title(package_or_folder)
			folder = package_or_folder
			self.new_button.set_sensitive(False)
			self.new_button.set_tooltip_text(_("App not Installed"))
		else:
			folder = package_or_folder.info["id"]
			self.set_title(_("{} Snapshots").format(package_or_folder.info["name"]))
			if os.path.exists(package_or_folder.data_path):
				self.new_button.set_sensitive(True)
				self.new_button.set_tooltip_text(None)
			else:
				self.new_button.set_sensitive(False)
				self.new_button.set_tooltip_text(_("No Data Found to Snapshot"))
				
		self.current_folder = folder
		self.snapshots_rows.clear()
		self.listbox.remove_all()
		
		Gio.Task.new(None, None, self.callback).run_in_thread(self.thread)
		
	def open_snapshots_folder(self, button):
		path = f"{self.snapshots_path}{self.current_folder}/"
		try:
			if not os.path.exists(path):
				raise Exception(f"error: File '{path}' does not exist")
				
			Gio.AppInfo.launch_default_for_uri(f"file://{path}", None)
			self.toast_overlay.add_toast(Adw.Toast.new(_("Opened snapshots folder")))
		except Exception as e:
			self.toast_overlay.add_toast(ErrorToast(_("Could not open folder"), str(e)).toast)
			
	def on_done(self):
		self.parent_page.status_stack.set_visible_child(self.parent_page.split_view)
		self.set_snapshots(self.package_or_folder, refresh=True)
			
	def on_new(self, button):
		self.parent_page.new_snapshot_dialog = NewSnapshotDialog(self.parent_page, self.parent_page.snapshotting_status, self.on_done, [self.package_or_folder])
		self.parent_page.new_snapshot_dialog.present(HostInfo.main_window)
		
	def sort_func(self, row1, row2):
		row1 = row1.get_child()
		row2 = row2.get_child()
		return row1.epoch > row2.epoch
		
	def on_trash(self):
		self.set_snapshots(self.package_or_folder, refresh=True)
		
	def __init__(self, parent_page, **kwargs):
		super().__init__(**kwargs)
		
		# Extra Object Creation
		self.parent_page = parent_page
		self.snapshots_path = HostInfo.snapshots_path
		self.current_folder = None
		self.package_or_folder = None
		self.snapshots_rows = []
		
		# Connections
		self.open_button.connect("clicked", self.open_snapshots_folder)
		self.new_button.connect("clicked", self.on_new)
		
		# Apply
		self.listbox.set_sort_func(self.sort_func)
