from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .loading_status import LoadingStatus
from .app_row import AppRow
from .tar_worker import TarWorker
import subprocess, os, time

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/new_snapshot_dialog.ui")
class NewSnapshotDialog(Adw.Dialog):
    __gtype_name__ = "NewSnapshotDialog"
    gtc = Gtk.Template.Child
    
    nav_page = gtc()
    list_cancel_button = gtc()
    search_button = gtc()
    create_button = gtc()
    search_entry = gtc()
    name_entry = gtc()
    listbox = gtc()
    select_all_button = gtc()
    total_selected_label = gtc()
    
    def row_gesture_handler(self, row):
        row.check_button.set_active(not row.check_button.get_active())
    
    def row_select_handler(self, row):
        if row.check_button.get_active():
            self.selected_rows.append(row)
        else:
            self.selected_rows.remove(row)
        
        total = len(self.selected_rows)
        self.total_selected_label.set_label(_("{} Selected").format(total))
        self.total_selected_label.set_visible(total > 0)
        self.valid_checker()
    
    def generate_list(self, *args):
        for package in HostInfo.flatpaks:
            if package.is_runtime or not os.path.exists(package.data_path):
                continue
            row = AppRow(package, self.row_gesture_handler)
            row.check_button.set_visible(True)
            row.check_button.connect("toggled", lambda *_, row=row: self.row_select_handler(row))
            row.set_activatable(True)
            row.set_activatable_widget(row.check_button)
            self.listbox.append(row)
    
    def sort_func(self, row1, row2):
        return row1.package.info["name"].lower() > row2.package.info["name"].lower()
        
    def filter_func(self, row):
        title = row.get_title().lower()
        subtitle = row.get_subtitle().lower()
        search = self.search_entry.get_text().lower()
        return search in title or search in subtitle
        
    def on_close(self, *args):
        self.search_button.set_active(False)
        for row in self.selected_rows.copy():
            row.check_button.set_active(False)
    
    def valid_checker(self):
        valid = len(self.selected_rows) > 0 and len(self.name_entry.get_text().strip()) > 0
        self.create_button.set_sensitive(valid)
        
    def get_total_fraction(self):
        total = 0
        stopped_workers_amount = 0
        for worker in self.workers:
            total += worker.fraction
            if worker.stop:
                stopped_workers_amount += 1
            
            if stopped_workers_amount == len(self.workers):
                return False
            
        print(f"{total / len(self.workers):.2f}")
        return True
        
    def on_create(self, button):
        self.workers.clear()
        for row in self.selected_rows:
            package = row.package
            worker = TarWorker(
                existing_path=package.data_path,
                new_path=f"{HostInfo.snapshots_path}{package.info['id']}",
                file_name=f"{int(time.time())}_{package.info["version"]}",
                name=self.name_entry.get_text(),
            )
            self.workers.append(worker)
            worker.compress()
        
    def on_invalidate(self, search_entry):
        self.listbox.invalidate_filter()
        
    def on_select_all(self, button):
        i = 0
        while row := self.listbox.get_row_at_index(i):
            i += 1
            row.check_button.set_active(True)
            
    def set_single(self, package):
        row = AppRow(package)
        row.set_activatable(False)
        self.selected_rows.append(row)
        self.listbox.append(row)
        
    def present(self, *args, **kwargs):
        super().present(*args, **kwargs)
        self.name_entry.grab_focus()
    
    def __init__(self, parent_page, package=None, **kwargs):
        super().__init__(**kwargs)
        
        # Extra Object Creations
        self.rows = []
        self.selected_rows = []
        self.workers = []
        
        # Connections
        self.connect("closed", self.on_close)
        self.create_button.connect("clicked", self.on_create)
        self.search_entry.connect("search-changed", self.on_invalidate)
        self.list_cancel_button.connect("clicked", lambda *_: self.close())
        self.name_entry.connect("changed", lambda *_: self.valid_checker())
        self.select_all_button.connect("clicked", self.on_select_all)
        
        # Apply
        self.listbox.set_sort_func(self.sort_func)
        self.listbox.set_filter_func(self.filter_func)
        if not package is None:
            self.search_entry.set_editable(False)
            self.search_button.set_visible(False)
            self.nav_page.set_title(_("New Snapshot"))
            self.name_entry.set_title(_("Name this Snapshot"))
            self.set_single(package)
        else:
            self.nav_page.set_title(_("New Snapshots"))
            self.name_entry.set_title(_("Name these Snapshots"))
            self.generate_list()
