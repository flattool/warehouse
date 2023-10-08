from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib
import re

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/popular_remotes.ui")
class PopularRemotesWindow(Adw.Window):
    __gtype_name__ = "PopularRemotesWindow"

    list_of_remotes = Gtk.Template.Child()
    custom_list = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def addRemoteCallback(self, _a, _b):
        self.parent_window.generate_list()

    def addRemoteThread(self, command):
        try:
            subprocess.run(command, capture_output=True, check=True, env=self.new_env)
        except Exception as e:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not add {}").format(self.name_to_add)))
            print(e)

    def on_add_response(self, _dialog, response_id, _function):
        if response_id == "cancel":
            return

        install_type = "--user"
        if not self.add_as_user:
            install_type = "--system"

        self.name_to_add = self.name_to_add.strip()
        self.url_to_add = self.url_to_add.strip()

        command = ['flatpak-spawn', '--host', 'flatpak', 'remote-add', '--if-not-exists', self.name_to_add, self.url_to_add, install_type]
        task = Gio.Task.new(None, None, self.addRemoteCallback)
        task.run_in_thread(lambda _task, _obj, _data, _cancellable: self.addRemoteThread(command))
        self.close()

    def add_handler(self, _widget, name="", link=""):
        dialog = Adw.MessageDialog.new(self, _("Add Flatpak Remote"))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Add"))
        dialog.set_response_enabled("continue", False)
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_transient_for(self.parent_window)

        def name_update(widget):
            is_enabled = True
            self.name_to_add = widget.get_text()
            name_pattern = re.compile(r'^[a-zA-Z\-]+$')
            if not name_pattern.match(self.name_to_add):
                is_enabled = False

            if is_enabled:
                widget.remove_css_class("error")
            else:
                widget.add_css_class("error")

            if len(self.name_to_add) == 0:
                is_enabled = False

            confirm_enabler(is_enabled)

        def url_update(widget):
            is_enabled = True
            self.url_to_add = widget.get_text()
            url_pattern = re.compile(r'^[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;=]+$')
            if not url_pattern.match(self.url_to_add):
                is_enabled = False

            if is_enabled:
                widget.remove_css_class("error")
            else:
                widget.add_css_class("error")

            if len(self.url_to_add) == 0:
                is_enabled = False

            confirm_enabler(is_enabled)

        def confirm_enabler(is_enabled):
            if len(self.name_to_add) == 0 or len(self.url_to_add) == 0:
                is_enabled = False
            dialog.set_response_enabled("continue", is_enabled)

        def set_user(widget):
            self.add_as_user = widget.get_active()

        self.name_to_add = ""
        self.url_to_add = ""
        self.add_as_user = True

        info_box = Gtk.Box(orientation="vertical")
        entry_list = Gtk.ListBox(selection_mode="none", margin_bottom=12)
        entry_list.add_css_class("boxed-list")
        
        name_entry = Adw.EntryRow(title=_("Name"))
        name_entry.set_text(name)
        name_entry.connect("changed", name_update)

        url_entry = Adw.EntryRow(title=_("URL"))
        url_entry.set_text(link)
        url_entry.connect("changed", url_update)

        entry_list.append(name_entry)
        entry_list.append(url_entry)
        info_box.append(entry_list)

        install_type_list = Gtk.ListBox(selection_mode="none")
        install_type_list.add_css_class("boxed-list")

        user_row = Adw.ActionRow(title=_("User"), subtitle=_("Remote will be available to only you"))
        user_check = Gtk.CheckButton(active=True)
        user_check.connect("toggled", set_user)
        user_row.add_prefix(user_check)
        user_row.set_activatable_widget(user_check)

        system_row = Adw.ActionRow(title=_("System"), subtitle=_("Remote will be available to every user on the system"))
        system_check = Gtk.CheckButton()
        system_row.add_prefix(system_check)
        system_check.set_group(user_check)
        system_row.set_activatable_widget(system_check)

        install_type_list.append(user_row)
        install_type_list.append(system_row)

        info_box.append(install_type_list)

        dialog.set_extra_child(info_box)
        dialog.connect("response", self.on_add_response, dialog.choose_finish)
        Gtk.Window.present(dialog)

        if name != "":
            name_update(name_entry)
        if link != "":
            url_update(url_entry)

    def generate_list(self):
        self.host_remotes = self.my_utils.getHostRemotes()
        self.list_of_remotes.remove_all()
        self.custom_list.remove_all()
        host_remotes_names = []

        for i in range(len(self.remotes)):
            remote_row = Adw.ActionRow(activatable=True)
            remote_row.set_title(self.remotes[i][0])
            remote_row.set_subtitle(self.remotes[i][3])
            image = Gtk.Image.new_from_icon_name("right-large-symbolic")
            remote_row.add_suffix(image)
            remote_row.connect("activated", self.add_handler, self.remotes[i][1], self.remotes[i][2])
            self.list_of_remotes.append(remote_row)

        image2 = Gtk.Image.new_from_icon_name("right-large-symbolic")
        custom_remote = Adw.ActionRow(activatable=True)
        custom_remote.set_title(_("Add a Custom Remote"))
        custom_remote.add_suffix(image2)
        custom_remote.connect("activated", self.add_handler)
        self.custom_list.append(custom_remote)

        if not self.list_of_remotes.get_row_at_index(0):
            self.list_of_remotes.set_visible(False)

    def __init__(self, parent_window, remotes, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(self)
        self.parent_window = parent_window
        self.set_size_request(260, 230)
        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)
        self.remotes = remotes

        self.new_env = dict( os.environ ) 
        self.new_env['LC_ALL'] = 'C' 

        self.set_modal(True)
        self.set_transient_for(parent_window)
        self.generate_list()
