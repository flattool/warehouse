from gi.repository import Adw, Gtk, GLib, Gio, Gdk
from .host_info import HostInfo
from .error_toast import ErrorToast
from .app_row import AppRow
from .snapshots_list_page import SnapshotsListPage
from .sidebar_button import SidebarButton
from .loading_status import LoadingStatus
from .new_snapshot_dialog import NewSnapshotDialog
from .tar_worker import TarWorker
from .attempt_install_dialog import AttemptInstallDialog
import os, subprocess

class LeftoverSnapshotRow(Adw.ActionRow):
    __gtype_name__ = "LeftoverSnapshotRow"
    
    def idle_stuff(self):
        self.set_title(self.name)
        icon = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        icon.set_icon_size(Gtk.IconSize.LARGE)
        self.add_prefix(icon)
        self.add_suffix(self.check_button)
        
    def gesture_handler(self, *args):
        self.on_long_press(self)
        
    def __init__(self, folder, on_long_press, **kwargs):
        super().__init__(**kwargs)
        
        # Extra Object Creation
        self.folder = folder
        self.check_button = Gtk.CheckButton(visible=False)
        self.on_long_press = on_long_press
        self.rclick_gesture = Gtk.GestureClick(button=3)
        self.long_press_gesture = Gtk.GestureLongPress()
        
        # Apply
        self.add_controller(self.rclick_gesture)
        self.add_controller(self.long_press_gesture)
        self.check_button.add_css_class("selection-mode")
        self.name = self.folder.split('.')[-1]
        self.set_activatable(True)
        GLib.idle_add(lambda *_: self.idle_stuff())
        
        # Connections
        self.rclick_gesture.connect("released", self.gesture_handler)
        self.long_press_gesture.connect("pressed", self.gesture_handler)
        
@Gtk.Template(resource_path="/io/github/flattool/Warehouse/snapshot_page/snapshot_page.ui")
class SnapshotPage(Adw.BreakpointBin):
    __gtype_name__ = "SnapshotPage"
    gtc = Gtk.Template.Child
    
    toast_overlay = gtc()
    sidebar_navpage = gtc()
    search_button = gtc()
    select_button = gtc()
    search_entry = gtc()
    search_bar = gtc()
    active_box = gtc()
    active_listbox = gtc()
    leftover_box = gtc()
    leftover_listbox = gtc()
    split_view = gtc()
    stack = gtc()
    no_snapshots = gtc()
    no_results = gtc()
    scrolled_window = gtc()
    open_button = gtc()
    status_open_button = gtc()
    status_new_button = gtc()
    new_button = gtc()
    status_stack = gtc()
    loading_view = gtc()
    snapshotting_view = gtc()
    select_all_button = gtc()
    copy_button = gtc()
    more_button = gtc()
    more_popover = gtc()
    more_menu = gtc()
    new_snapshots = gtc()
    apply_snapshots = gtc()
    install_from_snapshots = gtc()
    trash_snapshots = gtc()
    
    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None
    page_name = "snapshots"
    is_trash_dialog_open = False
    
    def sort_snapshots(self, *args):
        self.active_snapshot_paks.clear()
        self.leftover_snapshots.clear()
        bad_folders = []
        
        if not os.path.exists(HostInfo.snapshots_path):
            try:
                os.makedirs(HostInfo.snapshots_path)
            except Exception as e:
                self.toast_overlay.add_toast(ErrorToast(_("Could not load Snapshots"), str(e)).toast)
                return
                
        for folder in os.listdir(HostInfo.snapshots_path):
            if folder.count('.') < 2 or ' ' in folder:
                bad_folders.append(folder)
                continue
                
            has_tar = False
            for file in os.listdir(f"{HostInfo.snapshots_path}{folder}"):
                if file.endswith(".tar.zst"):
                    has_tar = True
                    break
                    
            if not has_tar:
                bad_folders.append(folder)
                continue
                
            try:
                pak = HostInfo.id_to_flatpak[folder]
                self.active_snapshot_paks.append(pak)
            except KeyError:
                self.leftover_snapshots.append(folder)
                
        for folder in bad_folders:
            try:
                subprocess.run(['gio', 'trash', f'{HostInfo.snapshots_path}{folder}'])
            except Exception:
                pass
                
    def long_press_handler(self, row):
        self.select_button.set_active(True)
        row.check_button.set_active(not row.check_button.get_active())
        
    def generate_active_list(self):
        for pak in self.active_snapshot_paks:
            row = AppRow(pak, self.long_press_handler)
            row.check_button.connect("toggled", lambda *_, _row=row: self.row_select_handler(_row))
            self.active_listbox.append(row)
            
        if len(self.active_snapshot_paks) > 0:
            self.active_box.set_visible(True)
            # first_row = self.active_listbox.get_row_at_index(0)
            # self.active_listbox.select_row(first_row)
        else:
            self.active_box.set_visible(False)
            
    def generate_leftover_list(self):
        for folder in self.leftover_snapshots:
            row = LeftoverSnapshotRow(folder, self.long_press_handler)
            row.check_button.connect("toggled", lambda *_, _row=row: self.row_select_handler(_row))
            self.leftover_listbox.append(row)
            
        if len(self.leftover_snapshots) > 0:
            self.leftover_box.set_visible(True)
            if len(self.active_snapshot_paks) == 0:
                self.stack.set_visible_child(self.scrolled_window)
                # first_row = self.leftover_listbox.get_row_at_index(0)
                # self.leftover_listbox.select_row(first_row)
        else:
            self.leftover_box.set_visible(False)
            
    def active_select_handler(self, listbox, row, should_show_content=True, refresh=False):
        self.leftover_listbox.select_row(None)
        self.list_page.set_snapshots(row.package, refresh)
        self.split_view.set_show_content(should_show_content)
        
    def leftover_select_handler(self, listbox, row, should_show_content=True, refresh=False):
        self.active_listbox.select_row(None)
        self.list_page.set_snapshots(row.folder, refresh)
        self.split_view.set_show_content(should_show_content)
        
    def select_first_row(self):
        if row := self.active_listbox.get_row_at_index(0):
            self.active_listbox.select_row(row)
            self.active_select_handler(None, row, False, True)
        elif row := self.leftover_listbox.get_row_at_index(0):
            self.leftover_listbox.select_row(row)
            self.leftover_select_handler(None, row, False, True)
            
    def show_snapshot(self, package):
        i = 0
        while row := self.active_listbox.get_row_at_index(i):
            i += 1
            if row.package is package:
                self.active_listbox.select_row(row)
                self.active_select_handler(None, row, True)
                self.toast_overlay.add_toast(Adw.Toast(title=_("Showing snapshots for {}").format(package.info['name'])))
                break
        else:
            dialog = NewSnapshotDialog(self, self.snapshotting_status, self.refresh, [package])
            toast = Adw.Toast(title=_("No snapshots for {}").format(package.info['name']), button_label=_("New"))
            toast.connect("button-clicked", lambda *_: dialog.present(HostInfo.main_window))
            self.toast_overlay.add_toast(toast)
            
    def start_loading(self):
        self.search_button.set_active(False)
        self.workers.clear()
        self.select_button.set_active(False)
        self.status_stack.set_visible_child(self.loading_view)
        self.active_box.set_visible(True)
        self.active_listbox.remove_all()
        self.leftover_box.set_visible(True)
        self.leftover_listbox.remove_all()
        self.selected_active_rows.clear()
        self.selected_leftover_rows.clear()
        
    def end_loading(self):
        def callback(*args):
            self.generate_active_list()
            self.generate_leftover_list()
            if (not self.active_box.get_visible()) and (not self.leftover_box.get_visible()):
                GLib.idle_add(lambda *_: self.status_stack.set_visible_child(self.no_snapshots))
            else:
                self.select_first_row()
                GLib.idle_add(lambda *_: self.stack.set_visible_child(self.scrolled_window))
                GLib.idle_add(lambda *_: self.status_stack.set_visible_child(self.split_view))
                
            data_path = f"{HostInfo.home}/.var/app"
            total_data = 0
            for folder in os.listdir(data_path):
                if folder == "io.github.flattool.Warehouse":
                    continue
                    
                total_data += 1
                break
                
            if total_data > 0:
                self.new_button.set_sensitive(True)
                self.new_button.set_tooltip_text(None)
                self.status_new_button.set_sensitive(True)
                self.status_new_button.set_tooltip_text(None)
            else:
                self.new_button.set_sensitive(False)
                self.new_button.set_tooltip_text(_("No Data Found to Snapshot"))
                self.status_new_button.set_sensitive(False)
                self.status_new_button.set_tooltip_text(_("No Data Found to Snapshot"))
                
        Gio.Task.new(None, None, callback).run_in_thread(self.sort_snapshots)
        
    def open_snapshots_folder(self, button):
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{HostInfo.snapshots_path}", None)
            self.toast_overlay.add_toast(Adw.Toast.new(_("Opened snapshots folder")))
        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not open folder"), str(e)).toast)
            
    def on_cancel(self):
        for worker in self.workers:
            worker.do_cancel("manual_cancel")
            
        if self.new_snapshot_dialog is None:
            return
            
        for worker in self.new_snapshot_dialog.workers:
            worker.do_cancel("manual_cancel")
            
    def on_new(self, *args):
        self.new_snapshot_dialog = NewSnapshotDialog(self, self.snapshotting_status, self.refresh)
        self.new_snapshot_dialog.present(HostInfo.main_window)
        
    def refresh(self):
        self.start_loading()
        self.end_loading()
        
    def on_search(self, search_entry):
        text = search_entry.get_text().lower()
        i = 0
        total_active_visible = 0
        while row := self.active_listbox.get_row_at_index(i):
            i += 1
            row.set_visible(False)
            if text in row.get_title().lower():
                row.set_visible(True)
                total_active_visible += 1
        self.active_box.set_visible(total_active_visible > 0)
        
        i = 0
        total_leftover_visible = 0
        while row := self.leftover_listbox.get_row_at_index(i):
            i += 1
            row.set_visible(False)
            if text in row.get_title().lower():
                row.set_visible(True)
                total_leftover_visible += 1
        self.leftover_box.set_visible(total_leftover_visible > 0)
        
        if total_active_visible > 0 or total_leftover_visible > 0:
            self.stack.set_visible_child(self.scrolled_window)
        else:
            self.stack.set_visible_child(self.no_results)
            
    def sort_func(self, row1, row2):
        if type(row1) is AppRow:
            return row1.package.info['name'].lower() > row2.package.info['name'].lower()
        else:
            return row1.name.lower() > row2.name.lower()
            
    def set_selection_mode(self, *args):
        enable = self.select_button.get_active()
        i = 0
        while row := self.active_listbox.get_row_at_index(i):
            i += 1
            row.check_button.set_visible(enable)
            if not enable:
                row.check_button.set_active(False)
                
        i = 0
        while row := self.leftover_listbox.get_row_at_index(i):
            i += 1
            row.check_button.set_visible(enable)
            if not enable:
                row.check_button.set_active(False)
                
    def select_all_handler(self, *args):
        i = 0
        while row := self.active_listbox.get_row_at_index(i):
            i += 1
            row.check_button.set_active(True)
                
        i = 0
        while row := self.leftover_listbox.get_row_at_index(i):
            i += 1
            row.check_button.set_active(True)
            
    def row_select_handler(self, row):
        if type(row) is AppRow:
            if row.check_button.get_active():
                self.selected_active_rows.append(row)
            elif row in self.selected_active_rows:
                self.selected_active_rows.remove(row)
        elif type(row) is LeftoverSnapshotRow:
            if row.check_button.get_active():
                self.selected_leftover_rows.append(row)
            elif row in self.selected_leftover_rows:
                self.selected_leftover_rows.remove(row)
                
        total_active = len(self.selected_active_rows)
        total_leftover = len(self.selected_leftover_rows)
        total = total_active + total_leftover
        self.sidebar_navpage.set_title(_("{} Selected").format(total_active + total_leftover) if total > 0 else _("Snapshots"))
        self.new_snapshots.set_visible(total_active > 0)
        self.copy_button.set_sensitive(total > 0)
        self.more_button.set_sensitive(total > 0)
        i = 0
        while row := self.more_menu.get_row_at_index(i):
            i += 1
            match row.get_child():
                case self.new_snapshots:
                    row.set_visible(total_active > 0 and total_leftover == 0)
                case self.apply_snapshots:
                    row.set_visible(total_active > 0 and total_leftover == 0)
                case self.install_from_snapshots:
                    row.set_visible(total_active == 0 and total_leftover > 0)
        
    def select_copy_handler(self, *args):
        to_copy = ""
        i = 0
        while row := self.active_listbox.get_row_at_index(i):
            i += 1
            if row.check_button.get_active():
                to_copy += f"{HostInfo.snapshots_path}{row.package.info['id']}\n"
                
        i = 0
        while row := self.leftover_listbox.get_row_at_index(i):
            i += 1
            if row.check_button.get_active():
                to_copy += f"{HostInfo.snapshots_path}{row.folder}\n"
                
        to_copy = to_copy[0:-1]
        HostInfo.clipboard.set(to_copy)
        self.toast_overlay.add_toast(Adw.Toast(title=_("Copied Snapshot Paths")))
        
    def select_new_handler(self):
        packages = []
        for row in self.selected_active_rows:
            if os.path.exists(row.package.data_path):
                packages.append(row.package)
                
        if len(packages) == 0:
            self.toast_overlay.add_toast(Adw.Toast(title=_("No apps in your selection can be snapshotted")))
            return
            
        self.new_snapshot_dialog = NewSnapshotDialog(self, self.snapshotting_status, self.refresh, packages)
        self.new_snapshot_dialog.present(HostInfo.main_window)
        
    def get_snapshots_from_entry(self, app_ids):
        id_to_tar = {}
        for app_id in app_ids:
            path = f"{HostInfo.snapshots_path}{app_id}"
            if not os.path.exists(path):
                continue
                
            tarlist = []
            for file in os.listdir(path):
                if file.endswith(".tar.zst"):
                    tarlist.append(file)
                    
            id_to_tar[app_id] = tarlist
            if len(tarlist) < 1:
                id_to_tar.pop(app_id, None)
                
        return id_to_tar
        
    def get_total_fraction(self):
        total = 0
        stopped_workers_amount = 0
        for worker in self.workers:
            total += worker.fraction
            if worker.stop:
                stopped_workers_amount += 1
                
            if stopped_workers_amount == len(self.workers):
                self.snapshotting_status.progress_bar.set_fraction(1)
                self.snapshotting_status.progress_label.set_label(f"{len(self.workers)} / {len(self.workers)}")
                HostInfo.main_window.refresh_handler()
                self.workers.clear()
                return False
                
        self.snapshotting_status.progress_label.set_label(f"{stopped_workers_amount + 1} / {len(self.workers)}")
        self.snapshotting_status.progress_bar.set_fraction(total / len(self.workers))
        return True
        
    def on_apply_response(self, dialog, response):
        if response != "continue":
            return
            
        app_ids = []
        for row in self.selected_active_rows:
            app_ids.append(row.package.info['id'])
            
        for row in self.selected_leftover_rows:
            app_ids.append(row.folder)
            
        id_to_tar = self.get_snapshots_from_entry(app_ids)
        for app_id in id_to_tar:
            biggest = 0
            biggest_tar = ""
            for tar in id_to_tar[app_id]:
                epoch = int(tar.split('_')[0])
                if epoch > biggest:
                    biggest = epoch
                    biggest_tar = tar
                    
            id_to_tar[app_id] = tar
            
        for app_id, tar in id_to_tar.items():
            worker = TarWorker(
                existing_path=f"{HostInfo.snapshots_path}{app_id}/{tar}",
                new_path=f"{HostInfo.home}/.var/app/{app_id}/",
                toast_overlay=self.toast_overlay,
            )
            self.workers.append(worker)
            worker.extract()
            
        if len(self.workers) > 0:
            self.snapshotting_status.title_label.set_label(_("Applying Snapshots"))
            self.snapshotting_status.progress_bar.set_fraction(0.0)
            self.snapshotting_status.progress_label.set_visible(len(self.workers) > 1)
            self.status_stack.set_visible_child(self.snapshotting_view)
            GLib.timeout_add(200, self.get_total_fraction)
        else:
            self.toast_overlay.add_toast(ErrorToast(_("No snapshots to extract"), _("No snapshots were found to extract")))
            
    def select_apply_handler(self):
        dialog = Adw.AlertDialog(heading=_("Apply These Snapshots?"), body=_("This will trash the current apps' user data, and apply their newest snapshot"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Continue"))
        dialog.connect("response", self.on_apply_response)
        dialog.present(HostInfo.main_window)
        
    def install_handler(self):
        package_names = []
        for row in self.selected_leftover_rows:
            package_names.append(row.folder)
            
        AttemptInstallDialog(package_names, lambda is_valid: self.select_button.set_active(not is_valid))
        
    def selection_trash_handler(self):
        if (
            len(self.selected_active_rows) + len(self.selected_leftover_rows) < 1
            or self.is_trash_dialog_open
        ):
            return
            
        def on_response(dialog, response):
            self.is_trash_dialog_open = False
            to_trash = []
            if response != "continue":
                return
                
            for row in self.selected_active_rows:
                to_trash.append(f"{HostInfo.snapshots_path}{row.package.info['id']}")
                
            for row in self.selected_leftover_rows:
                to_trash.append(f"{HostInfo.snapshots_path}{row.folder}")
                
            try:
                subprocess.run(['gio', 'trash'] + to_trash, check=True, text=True, capture_output=True)
                self.start_loading()
                self.end_loading()
                self.toast_overlay.add_toast(Adw.Toast(title=_("Trashed snapshots")))
            except subprocess.CalledProcessError as cpe:
                self.toast_overlay.add_toast(ErrorToast(_("Could not trash snapshots"), cpe.stderr).toast)
                
        self.is_trash_dialog_open = True
        dialog = Adw.AlertDialog(heading=_("Trash Snapshots?"), body=_("These apps' snapshots will be sent to the trash"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Trash"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response)
        dialog.present(HostInfo.main_window)
        
    def more_menu_handler(self, listbox, row):
        self.more_popover.popdown()
        row = row.get_child()
        match row:
            case self.new_snapshots:
                self.select_new_handler()
            case self.apply_snapshots:
                self.select_apply_handler()
            case self.install_from_snapshots:
                self.install_handler()
            case self.trash_snapshots:
                self.selection_trash_handler()
                
    def key_handler(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.select_button.set_active(False)
            
    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        
        # Extra Object Creation
        self.__class__.instance = self
        self.main_window = main_window
        self.active_snapshot_paks = []
        self.selected_active_rows = []
        self.selected_leftover_rows = []
        self.workers = []
        self.leftover_snapshots = []
        self.list_page = SnapshotsListPage(self)
        self.snapshotting_status = LoadingStatus("Initial Title", _("This could take a while"), True, self.on_cancel)
        self.new_snapshot_dialog = None
        self.on_backspace_handler = self.selection_trash_handler
        event_controller = Gtk.EventControllerKey()
        
        # Apply
        self.add_controller(event_controller)
        self.search_bar.set_key_capture_widget(HostInfo.main_window)
        self.loading_view.set_content(LoadingStatus(_("Loading Snapshots"), _("This should only take a moment")))
        self.snapshotting_view.set_content(self.snapshotting_status)
        self.split_view.set_content(self.list_page)
        self.active_listbox.set_sort_func(self.sort_func)
        self.leftover_listbox.set_sort_func(self.sort_func)
        
        # Connections
        event_controller.connect("key-pressed", self.key_handler)
        self.active_listbox.connect("row-activated", self.active_select_handler)
        self.leftover_listbox.connect("row-activated", self.leftover_select_handler)
        self.open_button.connect("clicked", self.open_snapshots_folder)
        self.status_open_button.connect("clicked", self.open_snapshots_folder)
        self.status_new_button.connect("clicked", self.on_new)
        self.new_button.connect("clicked", self.on_new)
        self.search_entry.connect("search-changed", self.on_search)
        self.select_button.connect("toggled", self.set_selection_mode)
        self.select_all_button.connect("clicked", self.select_all_handler)
        self.copy_button.connect("clicked", self.select_copy_handler)
        self.more_menu.connect("row-activated", self.more_menu_handler)
