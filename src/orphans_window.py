from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib


@Gtk.Template(resource_path="/io/github/flattool/Warehouse/../data/ui/orphans.ui")
class OrphansWindow(Adw.Window):
    __gtype_name__ = "OrphansWindow"

    list_of_data = Gtk.Template.Child()
    install_button = Gtk.Template.Child()
    trash_button = Gtk.Template.Child()
    select_all_button = Gtk.Template.Child()
    main_overlay = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    no_data = Gtk.Template.Child()
    no_results = Gtk.Template.Child()
    action_bar = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    oepn_folder_button = Gtk.Template.Child()
    installing = Gtk.Template.Child()
    main_box = Gtk.Template.Child()

    window_title = _("Manage Leftover Data")
    host_home = str(pathlib.Path.home())
    user_data_path = host_home + "/.var/app/"
    should_select_all = False
    selected_remote = ""
    selected_remote_install_type = ""
    no_close_id = 0
    is_result = False

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def selection_handler(self, widget, dir_name):
        if widget.get_active():
            self.selected_dirs.append(dir_name)
        else:
            self.selected_dirs.remove(dir_name)

        if len(self.selected_dirs) == 0:
            self.set_title(
                self.window_title
            )  # Set the window title back to what it was when there are no selected dirs
        else:
            self.set_title(
                ("{} selected").format(str(len(self.selected_dirs)))
            )  # Set the window title to the amount of selected dirs

        if len(self.selected_dirs) == 0:
            self.install_button.set_sensitive(False)
            self.trash_button.set_sensitive(False)
        else:
            self.install_button.set_sensitive(True)
            self.trash_button.set_sensitive(True)

    def select_all_handler(self, button):
        self.should_select_all = button.get_active()
        if not button.get_active():
            self.install_button.set_sensitive(False)
            self.trash_button.set_sensitive(False)
        self.generate_list()

    def install_callback(self, *_args):
        self.generate_list()
        self.progress_bar.set_visible(False)
        self.app_window.refresh_list_of_flatpaks(self, False)
        self.disconnect(self.no_close_id)  # Make window able to close
        self.search_button.set_sensitive(True)
        if self.my_utils.install_success:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Installed successfully")))
        else:
            self.toast_overlay.add_toast(
                Adw.Toast.new(_("Could not install some apps"))
            )

    def install_handler(self):
        self.main_stack.set_visible_child(self.installing)
        self.search_button.set_sensitive(False)
        self.set_title(self.window_title)
        self.keep_checking = True
        task = Gio.Task.new(None, None, self.install_callback)
        task.run_in_thread(
            lambda _task, _obj, _data, _cancellable, id_list=self.selected_dirs, remote=self.selected_remote, app_type=self.selected_remote_type, progress_bar=self.progress_bar: self.my_utils.install_flatpak(
                id_list, remote, app_type, progress_bar
            )
        )

    def install_button_handler(self, button):
        def remote_select_handler(button, index):
            if not button.get_active():
                return
            self.selected_remote = self.host_remotes[index][0]
            self.selected_remote_type = self.my_utils.get_install_type(
                self.host_remotes[index][7]
            )

        def on_response(dialog, response_id, _function):
            if response_id == "cancel":
                return
            self.install_handler()
            self.progress_bar.set_visible(True)
            self.action_bar.set_visible(False)
            self.no_close_id = self.connect(
                "close-request", lambda event: True
            )  # Make window unable to close

        dialog = Adw.MessageDialog.new(
            self,
            _("Attempt to Install?"),
            _("Warehouse will attempt to install apps matching the selected data."),
        )
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Install"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)

        height = 65 * len(self.host_remotes)
        max = 400
        if height > max:
            height = max
        remotes_scroll = Gtk.ScrolledWindow(vexpand=True, min_content_height=height)
        remote_list = Gtk.ListBox(selection_mode="none", valign="start")
        remotes_scroll.set_child(remote_list)
        remote_list.add_css_class("boxed-list")

        total_added = 0
        remote_select_buttons = []
        for i in range(len(self.host_remotes)):
            title = self.host_remotes[i][1]
            name = self.host_remotes[i][0]
            type_arr = self.host_remotes[i][7]
            if "disabled" in type_arr:
                continue
            remote_row = Adw.ActionRow(title=title)
            remote_select = Gtk.CheckButton()
            remote_select_buttons.append(remote_select)
            remote_select.connect("toggled", remote_select_handler, i)
            remote_row.set_activatable_widget(remote_select)

            type = self.my_utils.get_install_type(type_arr)
            if type == "user":
                remote_row.set_subtitle(_("User wide"))
            elif type == "system":
                remote_row.set_subtitle(_("System wide"))
            else:
                remote_row.set_subtitle(_("Unknown install type"))

            if remote_row.get_title() == "-":
                remote_row.set_title(self.host_remotes[i][0])

            if total_added > 0:
                remote_select.set_group(remote_select_buttons[0])

            remote_row.add_prefix(remote_select)
            remote_list.append(remote_row)
            total_added += 1

        remote_select_buttons[0].set_active(True)

        if total_added > 1:
            dialog.set_extra_child(remotes_scroll)

        dialog.connect("response", on_response, dialog.choose_finish)
        dialog.present()

    def trash_handler(self, button):
        def on_response(dialog, response_id, _function):
            if response_id == "cancel":
                return
            for i in range(len(self.selected_dirs)):
                path = self.user_data_path + self.selected_dirs[i]
                self.my_utils.trash_folder(path)
            self.select_all_button.set_active(False)
            self.generate_list()

        dialog = Adw.MessageDialog.new(
            self, _("Trash folders?"), _("These folders will be sent to the trash.")
        )
        dialog.connect("response", on_response, dialog.choose_finish)
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Continue"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.present()

    def open_button_handler(self, _widget, path=user_data_path):
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{path}", None)
        except GLib.GError:
            properties_toast_overlay.add_toast(
                Adw.Toast.new(_("Could not open folder"))
            )

    def size_callback(self, row_index):
        row = self.list_of_data.get_row_at_index(row_index)
        row.set_subtitle(f"~{self.data_rows[row_index][1]}")

    def size_thread(self, index, path):
        size = self.my_utils.get_size_with_format(path)
        self.data_rows[index].append(size)

    # Create the list of folders in the window
    def generate_list(self):
        self.data_rows = []
        self.host_flatpaks = self.my_utils.get_host_flatpaks()

        if self.host_flatpaks == [["", ""]]:
            self.app_window.toast_overlay.add_toast(
                Adw.Toast.new(_("Could not manage data"))
            )
            self.this_just_crashes_the_window_so_it_doesnt_open()
            return

        self.list_of_data.remove_all()
        self.selected_dirs = []
        self.set_title(self.window_title)
        dir_list = os.listdir(self.user_data_path)

        # This is a list that only holds IDs of install flatpaks
        id_list = []
        for i in range(len(self.host_flatpaks)):
            try:
                id_list.append(self.host_flatpaks[i][2])
            except:
                print("Could not get data")

        for i in range(len(dir_list)):
            dir_name = dir_list[i]

            # Skip item if it has a matching flatpak
            if dir_name in id_list:
                continue

            # Create row element
            dir_row = Adw.ActionRow(title=dir_name)
            self.data_rows.append([dir_row])
            path = self.user_data_path + dir_name
            index = len(self.data_rows) - 1
            task = Gio.Task.new(
                None, None, lambda *_, index=index: self.size_callback(index)
            )
            task.run_in_thread(
                lambda _task, _obj, _data, _cancellable, *_, index=index: self.size_thread(
                    index, path
                )
            )

            open_row_button = Gtk.Button(
                icon_name="document-open-symbolic",
                valign=Gtk.Align.CENTER,
                tooltip_text=_("Open User Data Folder"),
            )
            open_row_button.add_css_class("flat")
            open_row_button.connect(
                "clicked", self.open_button_handler, (self.user_data_path + dir_name)
            )
            dir_row.add_suffix(open_row_button)

            select_button = Gtk.CheckButton(tooltip_text=_("Select"))
            select_button.add_css_class("selection-mode")
            select_button.connect("toggled", self.selection_handler, dir_name)
            select_button.set_active(self.should_select_all)
            dir_row.add_suffix(select_button)
            dir_row.set_activatable_widget(select_button)

            # Add row to list
            self.list_of_data.append(dir_row)

        if self.list_of_data.get_row_at_index(0) == None:
            self.main_stack.set_visible_child(self.no_data)
            self.action_bar.set_visible(False)
        else:
            self.main_stack.set_visible_child(self.main_box)
            self.action_bar.set_visible(True)

    def filter_func(self, row):
        if self.search_entry.get_text().lower() in row.get_title().lower():
            self.is_result = True
            return True

    def on_invalidate(self, row):
        if self.list_of_data.get_row_at_index(0) == None:
            self.main_stack.set_visible_child(self.no_data)
            self.action_bar.set_visible(False)
        else:
            self.main_stack.set_visible_child(self.main_box)
            self.action_bar.set_visible(True)

        self.is_result = False
        self.list_of_data.invalidate_filter()
        if self.is_result == False:
            self.main_stack.set_visible_child(self.no_results)
            self.action_bar.set_visible(False)

    def on_change(self, prop, prop2):
        if self.search_bar.get_search_mode() == False:
            if self.list_of_data.get_row_at_index(0) == None:
                self.main_stack.set_visible_child(self.no_data)
                self.action_bar.set_visible(False)
            else:
                self.main_stack.set_visible_child(self.main_box)
                self.action_bar.set_visible(True)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(
            self
        )  # Access common utils and set the window to this window
        self.host_remotes = self.my_utils.get_host_remotes()
        self.host_flatpaks = self.my_utils.get_host_flatpaks()

        self.progress_bar = Gtk.ProgressBar(visible=False)
        self.progress_bar.add_css_class("osd")
        self.app_window = main_window

        self.set_modal(True)
        self.set_transient_for(main_window)
        self.set_size_request(260, 230)
        self.generate_list()

        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)

        self.install_button.connect("clicked", self.install_button_handler)
        if self.host_remotes[0][0] == "":
            self.install_button.set_visible(False)
        self.trash_button.connect("clicked", self.trash_handler)
        self.select_all_button.connect("toggled", self.select_all_handler)
        self.main_overlay.add_overlay(self.progress_bar)

        self.list_of_data.set_filter_func(self.filter_func)
        self.search_entry.connect("search-changed", self.on_invalidate)
        self.search_bar.connect("notify", self.on_change)
        self.search_bar.connect_entry(self.search_entry)
        self.oepn_folder_button.connect("clicked", self.open_button_handler)
