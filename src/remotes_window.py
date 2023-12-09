from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import re

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/../data/ui/remotes.ui")
class RemotesWindow(Adw.Window):
    __gtype_name__ = "RemotesWindow"

    remotes_list = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    main_group = Gtk.Template.Child()
    no_remotes = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    popular_remotes_list = Gtk.Template.Child()
    add_from_file = Gtk.Template.Child()
    custom_remote = Gtk.Template.Child()
    refresh = Gtk.Template.Child()
    # progress_bar = Gtk.Template.Child()

    rows_in_list = []
    rows_in_popular_list = []

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def make_toast(self, text):
        self.toast_overlay.add_toast(Adw.Toast.new(text))

    def get_host_flatpaks(self):
        output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "list", "--columns=all"], capture_output=True, text=True, env=self.new_env).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row)
        return data

    def remove_on_response(self, _dialog, response_id, _function, index):
        if response_id == "cancel":
            return

        name = self.host_remotes[index][0]
        title = self.host_remotes[index][1]
        install_type = self.host_remotes[index][7]
        command = ['flatpak-spawn', '--host', 'flatpak', 'remote-delete', '--force', name, f'--{install_type}']
        try:
            subprocess.run(command, capture_output=True, check=True, env=self.new_env)
        except subprocess.CalledProcessError as e:
            self.make_toast(_("Could not remove {}").format(title))
        self.generate_list()

    def remove_handler(self, _widget, index):
        name = self.host_remotes[index][0]
        title = self.host_remotes[index][1]
        install_type = self.host_remotes[index][7]

        body_text = _("Any installed apps from {} will stop receiving updates").format(name)
        dialog = Adw.MessageDialog.new(self, _("Remove {}?").format(name), body_text)
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Remove"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.remove_on_response, dialog.choose_finish, index)
        dialog.present()

    def generate_list(self):
        self.host_remotes = self.my_utils.getHostRemotes()
        self.host_flatpaks = self.get_host_flatpaks()
        for i in range(len(self.rows_in_list)):
            self.remotes_list.remove(self.rows_in_list[i])

        self.rows_in_list = []

        def rowCopyHandler(widget, to_copy):
            self.app_window.clipboard.set(to_copy)
            self.make_toast(_("Copied {}").format(to_copy))

        if self.host_remotes[0][0] == '':
            self.stack.set_visible_child(self.no_remotes)
            return
        else:
            self.stack.set_visible_child(self.main_group)

        for i in range(len(self.host_remotes)):
            try:
                name = self.host_remotes[i][0]
                title = self.host_remotes[i][1]
                install_type = self.host_remotes[i][7]
                url = self.host_remotes[i][2]
                remote_row = Adw.ActionRow(title=title, subtitle=name)
                if title == "-":
                    remote_row.set_title(name)
                self.remotes_list.add(remote_row)
                label = Gtk.Label(label=("{} wide").format(install_type), valign=Gtk.Align.CENTER)
                label.add_css_class("subtitle")
                remote_row.add_suffix(label)
                copy_button = Gtk.Button(icon_name="edit-copy-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Copy remote name"))
                copy_button.add_css_class("flat")
                copy_button.connect("clicked", rowCopyHandler, name)
                remove_button = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Remove {}").format(name))
                remove_button.add_css_class("flat")
                remove_button.connect("clicked", self.remove_handler, i)
                remote_row.add_suffix(copy_button)
                remote_row.add_suffix(remove_button)
                self.rows_in_list.append(remote_row)
            except Exception as e:
                print("Could not get remote. Error:", e)

        # Popular remotes
        for i in range(len(self.rows_in_popular_list)):
            self.popular_remotes_list.remove(self.rows_in_popular_list[i])
        
        self.rows_in_popular_list = []

        remotes = [
          # [Name to show in GUI, Name of remote for system, Link to repo to add, Description of remote]
            ["AppCenter", "appcenter", "https://flatpak.elementary.io/repo.flatpakrepo", _("The open source, pay-what-you-want app store from elementary")],
            ["Flathub", "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo", _("Central repository of Flatpak applications")],
            ["Flathub beta", "flathub-beta", "https://flathub.org/beta-repo/flathub-beta.flatpakrepo", _("Beta builds of Flatpak applications")],
            ["Fedora", "fedora", "oci+https://registry.fedoraproject.org", _("Flatpaks packaged by Fedora Linux")],
            ["GNOME Nightly", "gnome-nightly", "https://nightly.gnome.org/gnome-nightly.flatpakrepo", _("The latest beta GNOME Apps and Runtimes")],
            ["KDE Testing Applications", "kdeapps", "https://distribute.kde.org/kdeapps.flatpakrepo", _("Beta KDE Apps and Runtimes")],
            ["WebKit Developer SDK", "webkit-sdk", "https://software.igalia.com/flatpak-refs/webkit-sdk.flatpakrepo", _("Central repository of the WebKit Developer and Runtime SDK")],
        ]

        host_remotes = self.my_utils.getHostRemotes()
        host_remotes_names = []

        total_added = 0

        for i in range(len(self.host_remotes)):
            host_remotes_names.append(self.host_remotes[i][0])

        for i in range(len(remotes)):
            if remotes[i][1] in host_remotes_names:
                continue
            
            total_added += 1
            row = Adw.ActionRow(title=remotes[i][0], subtitle=(remotes[i][2]), activatable=True)
            row.connect("activated", self.add_handler, remotes[i][1], remotes[i][2])
            row.add_suffix(Gtk.Image.new_from_icon_name("right-large-symbolic"))
            self.rows_in_popular_list.append(row)
            self.popular_remotes_list.add(row)

        self.popular_remotes_list.set_visible(total_added > 0)

    def addRemoteCallback(self, _a, _b):
        self.generate_list()

    def addRemoteThread(self, command):
        try:
            subprocess.run(command, capture_output=True, check=True, env=self.new_env)
        except subprocess.CalledProcessError as e:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not add {}").format(self.name_to_add)))
            print(e)

    def on_add_response(self, _dialog, response_id, _function, row):
        if response_id == "cancel":
            self.should_pulse = False
            return

        install_type = "--user"
        if not self.add_as_user:
            install_type = "--system"

        self.name_to_add = self.name_to_add.strip()
        self.url_to_add = self.url_to_add.strip()

        command = ['flatpak-spawn', '--host', 'flatpak', 'remote-add', '--if-not-exists', self.name_to_add, self.url_to_add, install_type]
        task = Gio.Task.new(None, None, self.addRemoteCallback)
        task.run_in_thread(lambda _task, _obj, _data, _cancellable: self.addRemoteThread(command))

    def add_handler(self, row, name="", link=""):
        dialog = Adw.MessageDialog.new(self, _("Add Flatpak Remote"))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Add"))
        dialog.set_response_enabled("continue", False)
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_transient_for(self)

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
        dialog.connect("response", self.on_add_response, dialog.choose_finish, row)
        Gtk.Window.present(dialog)

        if name != "":
            name_update(name_entry)
        if link != "":
            url_update(url_entry)

    def addRemoteFromFileThread(self, filepath, system_or_user, name):
        try:
            subprocess.run(['flatpak-spawn', '--host', 'flatpak', 'remote-add', '--if-not-exists', name, filepath, f"--{system_or_user}"], capture_output=True, check=True, env=self.new_env)
            self.toast_overlay.add_toast(Adw.Toast.new(_("{} successfully added").format(name)))
        except subprocess.CalledProcessError as e:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not add {}").format(self.name_to_add)))
            print(e)

    def addRemoteFromFile(self, filepath):
        def response(dialog, response, _a):
            if response == "cancel":
                self.should_pulse = False
                return

            user_or_system = "user"
            if system_check.get_active():
                user_or_system = "system"

            task = Gio.Task.new(None, None, self.addRemoteCallback)
            task.run_in_thread(lambda *_: self.addRemoteFromFileThread(filepath, user_or_system, name_row.get_text()))

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

            dialog.set_response_enabled("continue", is_enabled)

        self.should_pulse = True

        name = filepath.split('/')
        name = name[len(name) - 1]

        dialog = Adw.MessageDialog.new(self, _("Add {}?").format(name))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Add"))
        dialog.set_response_enabled("continue", False)
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", response, dialog.choose_finish)

        # Create Widgets
        options_box = Gtk.Box(orientation="vertical")
        options_list = Gtk.ListBox(selection_mode="none", margin_top=15)
        name_row = Adw.EntryRow(title=_("Name"))
        name_row.connect("changed", name_update)
        user_row = Adw.ActionRow(title=_("User"), subtitle=_("Remote will be available to only you"))
        system_row = Adw.ActionRow(title=_("System"), subtitle=_("Remote will be available to every user on the system"))
        user_check = Gtk.CheckButton()
        system_check = Gtk.CheckButton()

        # Apply Widgets
        user_row.add_prefix(user_check)
        user_row.set_activatable_widget(user_check)
        system_row.add_prefix(system_check)
        system_row.set_activatable_widget(system_check)
        user_check.set_group(system_check)
        options_list.append(name_row)
        options_list.append(user_row)
        options_list.append(system_row)
        options_box.append(options_list)
        dialog.set_extra_child(options_box)

        # Calls
        user_check.set_active(True)
        options_list.add_css_class("boxed-list")
        Gtk.Window.present(dialog)
    
    def file_callback(self, object, result):
        try:
            file = object.open_finish(result)
            self.addRemoteFromFile(file.get_path())
        except GLib.GError:
            pass

    def addFromFileHandler(self, widet):
        filter = Gtk.FileFilter(name=_("Flatpak Repos"))
        filter.add_suffix("flatpakrepo")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter)
        file_chooser = Gtk.FileDialog()
        file_chooser.set_filters(filters)
        file_chooser.set_default_filter(filter)
        file_chooser.open(self, None, self.file_callback)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.host_remotes = []
        self.host_flatpaks = []
        self.app_window = main_window
        self.new_env = dict( os.environ )
        self.new_env['LC_ALL'] = 'C'
        self.should_pulse = False

        # Window Stuffs
        self.set_size_request(260, 230)
        self.set_modal(True)
        self.set_resizable(True)

        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)
        self.refresh.connect("clicked", lambda *_: self.generate_list())
        self.set_transient_for(main_window)

        self.add_from_file.add_suffix(Gtk.Image.new_from_icon_name("right-large-symbolic"))
        self.add_from_file.connect("activated", self.addFromFileHandler)
        self.custom_remote.add_suffix(Gtk.Image.new_from_icon_name("right-large-symbolic"))
        self.custom_remote.connect("activated", self.add_handler)

        # Calls
        self.generate_list()
        # self.show_new_remote_options()