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

        if response_id == "user":
            install_type = "--user"

        if response_id == "system":
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
        dialog = Adw.MessageDialog.new(self, _("Add a New Flatpak Remote"))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("system", _("Add System Wide"))
        dialog.add_response("user", _("Add User Wide"))
        dialog.set_response_enabled("system", False)
        dialog.set_response_enabled("user", False)
        dialog.set_response_appearance("user", Adw.ResponseAppearance.SUGGESTED)

        def name_update(widget):
            is_enabled = True
            self.name_to_add = widget.get_text()
            name_pattern = re.compile(r'^[a-zA-Z]+$')
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
            dialog.set_response_enabled("user", is_enabled)
            dialog.set_response_enabled("system", is_enabled)

        self.name_to_add = ""
        self.url_to_add = ""

        entry_list = Gtk.ListBox(selection_mode="none")
        entry_list.add_css_class("boxed-list")
        name_entry = Adw.EntryRow(title=_("Enter Remote Name"))
        name_entry.connect("changed", name_update)
        url_entry = Adw.EntryRow(title=_("Enter URL Name"))
        url_entry.connect("changed", url_update)
        entry_list.append(name_entry)
        entry_list.append(url_entry)

        dialog.set_extra_child(entry_list)
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
        name = self.host_remotes[index][0]
        title = self.host_remotes[index][1]
        install_type = self.host_remotes[index][7]
        dialog = Adw.MessageDialog.new(self, _("Remove {}?").format(name), _("This cannot be undone, and any installed apps from remote {} will stop receiving updates").format(name))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Remove"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.remove_on_response, dialog.choose_finish, index)
        dialog.present()

    def generate_list(self):
        self.remotes_list.remove_all()
        self.host_remotes = self.get_host_remotes()
        self.host_flatpaks = self.get_host_flatpaks()
        for i in range(len(self.host_remotes)):
            name = self.host_remotes[i][0]
            title = self.host_remotes[i][1]
            install_type = self.host_remotes[i][7]
            remote_row = Adw.ActionRow(title=title, subtitle=name)
            self.remotes_list.append(remote_row)
            label = Gtk.Label(label=install_type)
            label.add_css_class("subtitle")
            remote_row.add_suffix(label)
            remove_button = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Remove remote"))
            remove_button.add_css_class("flat")
            remove_button.connect("clicked", self.remove_handler, i)
            remote_row.add_suffix(remove_button)

            # for i in range(len(self.host_flatpaks)):
            #     if name == self.host_flatpaks[i][6] and install_type == self.host_flatpaks[i][7]:
            #         remove_button.set_sensitive(False)
            #         remove_button.set_tooltip_text(_("There are apps installed from this remote"))
            #         break
    

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
        self.add_button = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Add Remote")
        self.add_button.add_css_class("flat")
        self.add_button.add_css_class("suggested-action")
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
        self.set_size_request(250, 230)
        self.set_modal(True)
        self.set_resizable(True)
        self.set_content(self.toolbar)
        self.generate_list()

        if len(self.host_remotes) == 0:
            no_remotes = Adw.StatusPage(icon_name="error-symbolic", title=_("No Remotes"), description=_("Warehouse cannot see the list of remotes or the system has no remotes added"))
            self.stack.add_child(no_remotes)
            self.stack.set_visible_child(no_remotes)

        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", self.key_handler)
        self.add_controller(event_controller)

        self.set_transient_for(main_window)