from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
from .popular_remotes_window import PopularRemotesWindow
import subprocess
import os
import re

class RemotesWindow(Adw.Window):
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
        self.remotes_list.remove_all()
        self.host_remotes = self.my_utils.getHostRemotes()
        self.host_flatpaks = self.get_host_flatpaks()

        def rowCopyHandler(widget, to_copy):
            self.app_window.clipboard.set(to_copy)
            self.make_toast(_("Copied {}").format(to_copy))

        if self.host_remotes[0][0] == '':
            no_remotes = Adw.StatusPage(icon_name="error-symbolic", title=_("No Remotes"), description=_("Warehouse cannot see the list of remotes or the system has no remotes added"))
            self.stack.add_child(no_remotes)
            self.stack.set_visible_child(no_remotes)
            return
        else:
            self.stack.set_visible_child(self.scroll)

        for i in range(len(self.host_remotes)):
            name = self.host_remotes[i][0]
            title = self.host_remotes[i][1]
            install_type = self.host_remotes[i][7]
            url = self.host_remotes[i][2]
            remote_row = Adw.ActionRow(title=title, subtitle=url)
            if title == "-":
                remote_row.set_title(name)
            self.remotes_list.append(remote_row)
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

    def showPopularRemotes(self, widget):

        remotes = [
            ["elementary", "https://flatpak.elementary.io/repo.flatpakrepo", _("ElementoryOS's Apps")],
            ["flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo", _("The biggest repository of Flatpaks")],
            ["flathub-beta", "https://flathub.org/beta-repo/flathub-beta.flatpakrepo", _("The beta branch of the biggest repository of Flatpaks")],
            ["fedora", "oci+https://registry.fedoraproject.org", _("Flatpaks packaged by Fedora Linux")],
            ["gnome-nightly", "https://nightly.gnome.org/gnome-nightly.flatpakrepo", _("Beta GNOME Apps and Runtimes")],
            ["kdeapps", "https://distribute.kde.org/kdeapps.flatpakrepo", _("Beta KDE Apps and Runtimes")],
        ]

        non_added_remotes = []

        host_remotes = self.my_utils.getHostRemotes()
        host_remotes_urls = []

        for i in range(len(self.host_remotes)):
            host_remotes_urls.append(self.host_remotes[i][2])

        for i in range(len(remotes)):
            if remotes[i][2] not in host_remotes_urls:
                non_added_remotes.append(remotes[i])

        if len(non_added_remotes) > 0:
            PopularRemotesWindow(self).present()
        else:
            PopularRemotesWindow(self).add_handler(widget)
    
    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.window_title = _("Manage Remotes")
        self.host_remotes = []
        self.host_flatpaks = []
        self.new_env = dict( os.environ )
        self.new_env['LC_ALL'] = 'C' 

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
        self.new_env = dict( os.environ )
        self.new_env['LC_ALL'] = 'C' 
        
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
        self.app_window = main_window

        self.add_button.connect("clicked", self.showPopularRemotes)

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