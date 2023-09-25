from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/orphans.ui")
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
    action_bar = Gtk.Template.Child()

    window_title = _("Manage Leftover Data")
    host_home = str(pathlib.Path.home())
    user_data_path = host_home + "/.var/app/"
    should_select_all = False
    selected_remote = ""
    selected_remote_install_type = ""
    should_pulse = False
    no_close_id = 0

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def pulser(self):
        if self.should_pulse:
            self.progress_bar.pulse()
            GLib.timeout_add(500, self.pulser)
    
    def selectionHandler(self, widget, dir_name):
        if widget.get_active():
            self.selected_dirs.append(dir_name)
        else:
            self.selected_dirs.remove(dir_name)

        if len(self.selected_dirs) == 0:
            self.set_title(self.window_title) # Set the window title back to what it was when there are no selected dirs
        else:
            self.set_title(("{} selected").format(str(len(self.selected_dirs)))) # Set the window title to the amount of selected dirs

        if len(self.selected_dirs) == 0:
            self.install_button.set_sensitive(False)
            self.trash_button.set_sensitive(False)
        else:
            self.install_button.set_sensitive(True)
            self.trash_button.set_sensitive(True)

    def selectAllHandler(self, button):
        self.should_select_all = button.get_active()
        if not button.get_active():
            self.install_button.set_sensitive(False)
            self.trash_button.set_sensitive(False)
        self.generateList()

    def installCallback(self, *_args):
        self.set_title(self.window_title)
        self.generateList()
        self.should_pulse = False
        self.progress_bar.set_visible(False)
        self.set_sensitive(True)
        self.app_window.refresh_list_of_flatpaks(self, False)
        self.disconnect(self.no_close_id) # Make window able to close
        if self.my_utils.install_success:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Installed successfully")))
        else:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Some apps didn't install")))

    def installHandler(self):
        self.set_title(_("Installing... This could take a while"))
        task = Gio.Task.new(None, None, self.installCallback)
        task.run_in_thread(lambda _task, _obj, _data, _cancellable, id_list=self.selected_dirs, remote=self.selected_remote, app_type=self.selected_remote_type: self.my_utils.installFlatpak(id_list, remote, app_type))

    def installButtonHandler(self, button):
        remote_select_buttons = []
        self.should_pulse = True
        self.pulser()

        def remote_select_handler(button):
            if not button.get_active():
                return
            remote_index = remote_select_buttons.index(button)
            self.selected_remote = self.host_remotes[remote_index][0]
            self.selected_remote_type = self.host_remotes[remote_index][7]

        def onResponse(dialog, response_id, _function):
            if response_id == "cancel":
                self.should_pulse = False
                return
            self.installHandler()
            self.progress_bar.set_visible(True)
            self.set_sensitive(False)
            self.no_close_id = self.connect("close-request", lambda event: True)  # Make window unable to close
            
        dialog = Adw.MessageDialog.new(self, _("Attempt to Install?"), _("Warehouse will attempt to install apps matching the selected data."))
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

        for i in range(len(self.host_remotes)):
            remote_row = Adw.ActionRow(title=self.host_remotes[i][1])
            label = Gtk.Label(label=_("{} wide").format(self.host_remotes[i][7]))
            remote_select = Gtk.CheckButton()
            remote_select_buttons.append(remote_select)
            remote_select.connect("toggled", remote_select_handler)
            remote_row.set_activatable_widget(remote_select)

            if remote_row.get_title() == '-':
                remote_row.set_title(self.host_remotes[i][0])

            if i > 0:
                remote_select.set_group(remote_select_buttons[i-1])

            remote_row.add_prefix(remote_select)
            remote_row.add_suffix(label)
            remote_list.append(remote_row)

        remote_select_buttons[0].set_active(True)
            
        if len(self.host_remotes) > 1:
            dialog.set_extra_child(remotes_scroll)

        dialog.connect("response", onResponse, dialog.choose_finish)
        dialog.present()

    def trashHandler(self, button):

        def onResponse(dialog, response_id, _function):
            if response_id == "cancel":
                return
            for i in range(len(self.selected_dirs)):
                path = self.user_data_path + self.selected_dirs[i]
                self.my_utils.trashFolder(path)
            self.select_all_button.set_active(False)
            self.generateList()
            
        dialog = Adw.MessageDialog.new(self, _("Trash folders?"), _("These folders will be sent to the trash."))
        dialog.connect("response", onResponse, dialog.choose_finish)
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Continue"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.present()

    # Create the list of folders in the window
    def generateList(self):

        self.host_flatpaks = self.my_utils.getHostFlatpaks()
        self.list_of_data.remove_all()
        self.selected_dirs = []
        self.set_title(self.window_title)
        self.should_pulse = False
        dir_list = os.listdir(self.user_data_path)

        # This is a list that only holds IDs of install flatpaks
        id_list = []
        for i in range(len(self.host_flatpaks)):
            id_list.append(self.host_flatpaks[i][2])

        for i in range(len(dir_list)):
            dir_name = dir_list[i]

            # Skip item if it has a matching flatpak
            if dir_name in id_list:
                continue

            # Create row element
            dir_row = Adw.ActionRow(title=dir_name)
            dir_row.set_subtitle(self.my_utils.getSizeWithFormat(self.user_data_path + dir_name))

            select_button = Gtk.CheckButton()
            select_button.add_css_class("selection-mode")
            select_button.connect("toggled", self.selectionHandler, dir_name)
            select_button.set_active(self.should_select_all)
            dir_row.add_suffix(select_button)
            dir_row.set_activatable_widget(select_button)

            # Add row to list
            self.list_of_data.append(dir_row)
        if self.list_of_data.get_row_at_index(0) == None:
            self.main_stack.set_visible_child(self.no_data)
            self.action_bar.set_visible(False)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(self) # Access common utils and set the window to this window
        self.host_remotes = self.my_utils.getHostRemotes()
        self.host_flatpaks = self.my_utils.getHostFlatpaks()

        self.progress_bar = Gtk.ProgressBar(visible=False, pulse_step=0.7)
        self.progress_bar.add_css_class("osd")
        self.app_window = main_window

        self.set_modal(True)
        self.set_transient_for(main_window)
        self.set_size_request(260, 230)
        self.generateList()

        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)

        self.install_button.connect("clicked", self.installButtonHandler)
        if self.host_remotes[0][0] == '':
            self.install_button.set_visible(False)
        self.trash_button.connect("clicked", self.trashHandler)
        self.select_all_button.connect("toggled", self.selectAllHandler)
        self.main_overlay.add_overlay(self.progress_bar)