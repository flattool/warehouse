from gi.repository import Gtk, Adw, GLib, Gdk, Gio
import subprocess
import re

class RemotesWindow(Adw.Window):

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def make_toast(self, text):
        self.toast_overlay.add_toast(Adw.Toast.new(text))

    def get_host_flatpaks(self):
        output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "list", "--columns=all"], capture_output=True, text=True).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row)
        return data

    def get_host_remotes(self):
        output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "remotes", "--columns=all"], capture_output=True, text=True).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row)
        return data

    def on_add_response(self, _dialog, response_id, _function):
        if response_id == "cancel":
            return

        install_type = "--user"
        if not self.add_as_user:
            install_type = "--system"

        self.name_to_add = self.name_to_add.strip()
        self.url_to_add = self.url_to_add.strip()

        command = ['flatpak-spawn', '--host', 'flatpak', 'remote-add', '--if-not-exists', self.name_to_add, self.url_to_add, install_type]
        try:
            subprocess.run(command, capture_output=True, check=True)
        except Exception as e:
            self.make_toast(_("Could not add {}").format(self.name_to_add))
            print(e)
        self.generate_list()

    def add_handler(self, _widget):
        dialog = Adw.MessageDialog.new(self, _("Add Flatpak Remote"))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Add"))
        dialog.set_response_enabled("continue", False)
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.SUGGESTED)

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
        name_entry.connect("changed", name_update)

        url_entry = Adw.EntryRow(title=_("URL"))
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

    def remove_on_response(self, _dialog, response_id, _function, index):
        if response_id == "cancel":
            return

        name = self.host_remotes[index][0]
        title = self.host_remotes[index][1]
        install_type = self.host_remotes[index][7]
        command = ['flatpak-spawn', '--host', 'flatpak', 'remote-delete', '--force', name, f'--{install_type}']
        try:
            subprocess.run(command, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            self.make_toast(_("Could not remove {}").format(title))
        self.generate_list()

    def remove_handler(self, _widget, index):
        def remove_apps_check_handler(button):
            if button.get_active():
                apps_box.prepend(apps_scroll)
                apps_box.prepend(label)
            else:
                apps_box.remove(label)
                apps_box.remove(apps_scroll)
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

        label = Gtk.Label(label=_("These apps will be uninstalled"))
        remove_apps = Gtk.CheckButton(label=_("Uninstall apps from this remote"))
        remove_apps.connect("toggled", remove_apps_check_handler)

        height = 400
        apps_box = Gtk.Box(orientation="vertical")
        apps_scroll = Gtk.ScrolledWindow(vexpand=True, min_content_height=height, margin_top=6, margin_bottom=6)
        apps_list = Gtk.ListBox(selection_mode="none", valign="start")
        apps_list.add_css_class("boxed-list")
        apps_box.append(remove_apps)
        #apps_box.append(apps_scroll)
        
        for i in range(len(self.host_flatpaks)):
            if self.host_flatpaks[i][6] != name:
                continue
            if self.host_flatpaks[i][7] != install_type:
                continue
            
            app_row = Adw.ActionRow(title=self.host_flatpaks[i][0])
            apps_list.append(app_row)






        apps_scroll.set_child(apps_list)
        dialog.set_extra_child(apps_box)
        dialog.present()

    def generate_list(self):
        self.remotes_list.remove_all()
        self.host_remotes = self.get_host_remotes()
        self.host_flatpaks = self.get_host_flatpaks()
        if len(self.host_remotes) < 1:
            no_remotes = Adw.StatusPage(icon_name="error-symbolic", title=_("No Remotes"), description=_("Warehouse cannot see the list of remotes or the system has no remotes added"))
            self.stack.add_child(no_remotes)
            self.stack.set_visible_child(no_remotes)
            return
        for i in range(len(self.host_remotes)):
            name = self.host_remotes[i][0]
            title = self.host_remotes[i][1]
            install_type = self.host_remotes[i][7]
            url = self.host_remotes[i][2]
            remote_row = Adw.ActionRow(title=title, subtitle=url)
            if title == "-":
                remote_row.set_title(name)
            self.remotes_list.append(remote_row)
            label = Gtk.Label(label=("{} wide").format(install_type))
            label.add_css_class("subtitle")
            remote_row.add_suffix(label)
            remove_button = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Remove {}").format(name))
            remove_button.add_css_class("flat")
            remove_button.connect("clicked", self.remove_handler, i)
            remote_row.add_suffix(remove_button)
    
    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.window_title = _("Manage Remotes")
        self.host_remotes = []
        self.host_flatpaks = []

        # Create Widgets
        self.scroll = Gtk.ScrolledWindow()
        self.toast_overlay = Adw.ToastOverlay()
        self.outer_box = Gtk.Box(orientation="vertical", vexpand=True)
        self.clamp = Adw.Clamp()
        self.toolbar = Adw.ToolbarView()
        self.headerbar = Gtk.HeaderBar()
        self.remotes_list = Gtk.ListBox(selection_mode="none", margin_top=6, margin_bottom=12, margin_start=12, margin_end=12)
        self.user_data_row = Adw.ActionRow(title="No User Data")
        self.add_button = Gtk.Button(icon_name="plus-large-symbolic", tooltip_text="Add Remote")
        self.stack = Gtk.Stack()
        
        # Apply Widgets
        self.toolbar.set_content(self.toast_overlay)
        self.toolbar.add_top_bar(self.headerbar)
        self.headerbar.pack_start(self.add_button)
        self.toast_overlay.set_child(self.stack)
        self.stack.add_child(self.scroll)
        self.stack.set_visible_child(self.scroll)
        self.scroll.set_child(self.clamp)
        self.clamp.set_child(self.outer_box)
        self.outer_box.append(self.remotes_list)
        self.remotes_list.append(self.user_data_row)
        self.remotes_list.add_css_class("boxed-list")

        self.add_button.connect("clicked", self.add_handler)

        # Window Stuffs
        self.set_title(self.window_title)
        self.set_default_size(500, 450)
        self.set_size_request(260, 230)
        self.set_modal(True)
        self.set_resizable(True)
        self.set_content(self.toolbar)
        self.generate_list()

        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)

        self.set_transient_for(main_window)