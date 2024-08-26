from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .app_row import AppRow
from .error_toast import ErrorToast
from .properties_page import PropertiesPage
from .filters_page import FiltersPage
from .sidebar_button import SidebarButton
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/packages_page/packages_page.ui")
class PackagesPage(Adw.BreakpointBin):
    __gtype_name__ = 'PackagesPage'
    gtc = Gtk.Template.Child
    packages_bpt = gtc()
    packages_toast_overlay = gtc()
    status_stack = gtc()
    scrolled_window = gtc()
    uninstalling = gtc()
    loading_packages = gtc()
    no_filter_results = gtc()
    reset_filters_button = gtc()
    no_packages = gtc()
    no_results = gtc()
    filter_button = gtc()
    search_bar = gtc()
    search_entry = gtc()
    packages_split = gtc()
    packages_list_box = gtc()
    select_button = gtc()
    packages_navpage = gtc()
    select_all_button = gtc()
    content_stack = gtc()
    copy_button = gtc()
    copy_pop = gtc()
    copy_menu = gtc()
    copy_names = gtc()
    copy_ids = gtc()
    copy_refs = gtc()
    uninstall_button = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None
    page_name = "packages"

    def set_status(self, to_set):
        
        if to_set is self.scrolled_window:
            self.properties_page.stack.set_visible_child(self.properties_page.nav_view)
            self.select_button.set_sensitive(True)
            self.filter_button.set_sensitive(True)
            self.filters_page.set_sensitive(True)
        else:
            self.select_button.set_sensitive(False)

        if to_set is self.loading_packages or to_set is self.uninstalling:
            self.properties_page.stack.set_visible_child(self.properties_page.loading_tbv)
            self.filter_button.set_sensitive(False)
            self.filters_page.set_sensitive(False)
            self.select_button.set_active(False)

        if to_set is self.no_packages:
            self.properties_page.stack.set_visible_child(self.properties_page.error_tbv)
            self.filter_button.set_sensitive(False)
            self.filter_button.set_active(False)
        
        if to_set is self.no_filter_results:
            self.properties_page.stack.set_visible_child(self.properties_page.error_tbv)
            self.filter_button.set_sensitive(True)
            self.filters_page.set_sensitive(True)
            if not self.packages_split.get_collapsed():
                self.filter_button.set_active(True)

        if to_set is self.no_results:
            self.filters_page.set_sensitive(False)

        self.status_stack.set_visible_child(to_set)

    def apply_filters(self):
        i = 0
        show_apps = self.filter_settings.get_boolean("show-apps")
        show_runtimes = self.filter_settings.get_boolean("show-runtimes")
        remotes_list = self.filter_settings.get_string("remotes-list")
        runtimes_list = self.filter_settings.get_string("runtimes-list")
        total_visible = 0
        while row := self.packages_list_box.get_row_at_index(i):
            i += 1
            visible = True
            if row.package.is_runtime and not show_runtimes:
                visible = False
            if (not row.package.is_runtime) and (not show_apps):
                visible = False
            if remotes_list != "all" and not f"{row.package.info['origin']}<>{row.package.info['installation']}" in remotes_list:
                visible = False
            if runtimes_list != "all" and (row.package.is_runtime or row.package.dependant_runtime and not row.package.dependant_runtime.info["ref"] in runtimes_list):
                visible = False
            
            row.set_visible(visible)
            if visible:
                total_visible += 1
            else:
                row.check_button.set_active(False)

        if total_visible == 0:
            self.set_status(self.no_filter_results)
        else:
            GLib.idle_add(lambda *_: self.set_status(self.scrolled_window))

    def row_select_handler(self, row):
        if row.check_button.get_active():
            self.selected_rows.append(row)
        else:
            self.selected_rows.remove(row)
            
        if (total := len(self.selected_rows)) > 0:
            self.packages_navpage.set_title(_("{} Selected").format(total))
            self.copy_button.set_sensitive(True)
            self.uninstall_button.set_sensitive(True)
        else:
            self.packages_navpage.set_title(_("Packages"))
            self.copy_button.set_sensitive(False)
            self.uninstall_button.set_sensitive(False)

    def select_all_handler(self, *args):
        i = 0
        while row := self.packages_list_box.get_row_at_index(i):
            i += 1
            row.check_button.set_active(row.get_visible())

    def row_rclick_handler(self, row):
        self.select_button.set_active(True)
        GLib.idle_add(lambda *_, button=row.check_button: button.set_active(not button.get_active()))

    def generate_list(self, *args):
        self.packages_list_box.remove_all()
        GLib.idle_add(lambda *_: self.filters_page.generate_filters())
        self.copy_button.set_sensitive(False)
        self.uninstall_button.set_sensitive(False)
        if len(HostInfo.flatpaks) == 0:
            self.set_status(self.no_packages)
            return

        for package in HostInfo.flatpaks:
            row = AppRow(package, self.row_rclick_handler)
            package.app_row = row
            row.masked_status_icon.set_visible(package.is_masked)
            row.pinned_status_icon.set_visible(package.is_pinned)
            row.eol_package_package_status_icon.set_visible(package.is_eol)
            row.check_button.set_visible(self.select_button.get_active())
            row.check_button.connect("toggled", lambda *_, row=row: self.row_select_handler(row))
            try:
                if not package.is_runtime:
                    row.eol_runtime_status_icon.set_visible(package.dependant_runtime.is_eol)
            except Exception as e:
                self.packages_toast_overlay.add_toast(ErrorToast(_("Error getting Flatpak '{}'").format(package.info["name"]), str(e)).toast)
                
            self.packages_list_box.append(row)

        self.apply_filters()
        first_visible_row = None
        i = 0
        while row := self.packages_list_box.get_row_at_index(i):
            i += 1
            if row.get_visible():
                first_visible_row = row
                break
        
        if not first_visible_row is None:
            self.packages_list_box.select_row(first_visible_row)
            self.properties_page.set_properties(first_visible_row.package)

        self.scrolled_window.set_vadjustment(Gtk.Adjustment.new(0,0,0,0,0,0)) # Scroll list to top

    def row_activate_handler(self, list_box, row):
        self.properties_page.set_properties(row.package)
        self.properties_page.nav_view.pop()
        self.packages_split.set_show_content(True)
        self.filter_button.set_active(False)

    def filter_func(self, row):
        search_text = self.search_entry.get_text().lower()
        title = row.get_title().lower()
        subtitle = row.get_subtitle().lower()
        if search_text in title or search_text in subtitle:
            self.is_result = True
            return True

    def set_selection_mode(self, is_enabled):
        i = 0
        while row := self.packages_list_box.get_row_at_index(i):
            i += 1
            GLib.idle_add(row.check_button.set_active, False)
            GLib.idle_add(row.check_button.set_visible, is_enabled)

    def selection_copy(self, box, row):
        self.copy_pop.popdown()
        info = ""
        feedback = ""
        match row.get_child():
            case self.copy_names:
                info = "name"
                feedback = _("Names")
            case self.copy_ids:
                info = "id"
                feedback = _("IDs")
            case self.copy_refs:
                info = "ref"
                feedback = _("Refs")

        to_copy = []
        for row in self.selected_rows:
            to_copy.append(row.package.info[info])
            to_copy += ['\n']
        try:
            HostInfo.clipboard.set("".join(to_copy[:-1]))
            self.packages_toast_overlay.add_toast(Adw.Toast(title=_("Copied {}").format(feedback)))
        except Exception as e:
            self.packages_toast_overlay.add_toast(ErrorToast(_("Could not copy {}").format(feedback), str(e)).toast)

    def selection_uninstall(self, *args):
        def on_response(alert_dialog, response):
            if response != "continue":
                return
            
            GLib.idle_add(lambda *_: self.set_status(self.uninstalling))
            error = [None]
            def thread(*args):
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                except subprocess.CalledProcessError as cpe:
                    error[0] = cpe
                except Exception as e:
                    error[0] = e

            def callback(*args):
                if err := error[0]:
                    details = err.stderr if type(err) == subprocess.CalledProcessError else str(err)
                    self.packages_toast_overlay.add_toast(ErrorToast(_("Could not uninstall packages"), details).toast)
                else:
                    self.main_window.refresh_handler()
                    GLib.idle_add(lambda *__: self.packages_toast_overlay.add_toast(Adw.Toast(title=_("Uninstalled Packages"))))

            Gio.Task.new(None, None, callback).run_in_thread(thread)
        
        cmd = ['flatpak-spawn', '--host', 'flatpak', 'uninstall', '-y']
        for row in self.selected_rows:
            cmd.append(row.package.info["ref"])
        
        dialog = Adw.AlertDialog(heading=_("Uninstall Packages?"), body=_("It will not be possible to use these packages after removal"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Uninstall"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response)
        dialog.present(self.main_window)

    def start_loading(self):
        self.packages_navpage.set_title(_("Packages"))
        self.selected_rows.clear()
        self.select_button.set_active(False)
        self.set_status(self.loading_packages)

    def end_loading(self):
        GLib.idle_add(lambda *_: self.generate_list())

    def select_button_handler(self, button):
        self.set_selection_mode(button.get_active())

    def filter_button_handler(self, button):
        if button.get_active():
            self.content_stack.set_visible_child(self.filters_page)
            self.packages_split.set_show_content(True)
        else:
            self.content_stack.set_visible_child(self.properties_page)

    def filter_page_handler(self, *args):
        if self.packages_split.get_collapsed() and not self.packages_split.get_show_content():
            self.filter_button.set_active(False)

    def on_invalidate(self, row):
        current_status = self.status_stack.get_visible_child()
        if not current_status is self.no_results:
            self.prev_status = current_status

        self.is_result = False
        self.packages_list_box.invalidate_filter()
        if self.is_result:
            self.set_status(self.prev_status)
        else:
            self.set_status(self.no_results)

    def sort_func(self, row1, row2):
        return row1.package.info["name"].lower() > row2.package.info["name"].lower()

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.main_window = main_window
        self.properties_page = PropertiesPage(main_window, self)
        self.filters_page = FiltersPage(main_window, self)
        self.filter_settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        self.is_result = False
        self.prev_status = None
        self.selected_rows = []

        # Apply
        # self.set_status("loading_packages")
        self.packages_list_box.set_filter_func(self.filter_func)
        self.packages_list_box.set_sort_func(self.sort_func)
        self.content_stack.add_child(self.properties_page)
        self.content_stack.add_child(self.filters_page)
        self.__class__.instance = self

        # Connections

        self.search_entry.connect("search-changed", self.on_invalidate)
        self.search_bar.set_key_capture_widget(main_window)
        self.packages_list_box.connect("row-activated", self.row_activate_handler)
        self.select_button.connect("toggled", self.select_button_handler)
        self.filter_button.connect("toggled", self.filter_button_handler)
        self.reset_filters_button.connect("clicked", lambda *_: self.filters_page.reset_filters())
        self.packages_split.connect("notify::show-content", self.filter_page_handler)
        self.packages_bpt.connect("apply", self.filter_page_handler)
        self.select_all_button.connect("clicked", self.select_all_handler)

        self.copy_menu.connect("row-activated", self.selection_copy)
        self.uninstall_button.connect("clicked", self.selection_uninstall)