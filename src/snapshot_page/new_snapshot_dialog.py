from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .loading_status import LoadingStatus
from .app_row import AppRow
import subprocess, os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/new_snapshot_dialog.ui")
class NewSnapshotDialog(Adw.Dialog):
    __gtype_name__ = "NewSnapshotDialog"
    gtc = Gtk.Template.Child
    
    nav_view = gtc()
    
    app_list_page = gtc()
    list_cancel_button = gtc()
    next_button = gtc()
    listbox = gtc()
    
    details_page = gtc()
    create_button = gtc()
    
    def row_gesture_handler(self, row):
        row.check_button.set_active(not row.check_button.get_active())
    
    def row_select_handler(self, row):
        if row.check_button.get_active():
            self.selected_rows.append(row)
        else:
            self.selected_rows.remove(row)
            
        if (total := len(self.selected_rows)) > 0:
            self.app_list_page.set_title(_("{} Selected").format(total))
        else:
            self.app_list_page.set_title(_("Choose Applications"))
    
    def generate_list(self, *args):
        for package in HostInfo.flatpaks:
            if package.is_runtime or not os.path.exists(package.data_path):
                continue
            row = AppRow(package, self.row_gesture_handler)
            row.check_button.set_visible(True)
            row.check_button.connect("toggled", lambda *_, row=row: self.row_select_handler(row))
            row.set_activatable(True)
            row.set_activatable_widget(row.check_button)
            GLib.idle_add(lambda *_, row=row: self.listbox.append(row))
    
    def sort_func(self, row1, row2):
        return row1.get_title().lower() > row2.get_title().lower()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Extra Object Creations
        self.rows = []
        self.selected_rows = []
        
        # Connections
        self.list_cancel_button.connect("clicked", lambda *_: self.close())
        self.next_button.connect("clicked", lambda *_: self.nav_view.push(self.details_page))
        
        # Apply
        Gio.Task.new(None, None, None).run_in_thread(self.generate_list)
        self.listbox.set_sort_func(self.sort_func)
