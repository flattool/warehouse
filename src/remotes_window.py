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
    adding = Gtk.Template.Child()
    show_disabled_button = Gtk.Template.Child()
    show_disabled_button_button_content = Gtk.Template.Child()
    show_disabled = False

    rows_in_list = []
    rows_in_popular_list = []

    def key_handler(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape or (keyval == Gdk.KEY_w and state == Gdk.ModifierType.CONTROL_MASK):
            self.close()
        if keyval == Gdk.KEY_o and state == Gdk.ModifierType.CONTROL_MASK:
            self.add_file_handler()
        if keyval == Gdk.KEY_n and state == Gdk.ModifierType.CONTROL_MASK:
            self.add_handler(None)

    def make_toast(self, text):
        self.toast_overlay.add_toast(Adw.Toast.new(text))

    def get_host_flatpaks(self):
        output = subprocess.run(
            ["flatpak-spawn", "--host", "flatpak", "list", "--columns=all"],
            capture_output=True,
            text=True,
            env=self.new_env,
        ).stdout
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
        if "user" in install_type:
            install_type = "user"
        if "system" in install_type:
            install_type = "system"
        command = [
            "flatpak-spawn",
            "--host",
            "flatpak",
            "remote-delete",
            "--force",
            name,
            f"--{install_type}",
        ]
        try:
            subprocess.run(command, capture_output=True, check=True, env=self.new_env)
        except subprocess.CalledProcessError as e:
            self.make_toast(_("Could not remove {}").format(title))
            print("error in remotes_window.remove_on_response: CalledProcessError:", e)
        self.generate_list()

    def remove_handler(self, _widget, index, popoever):
        popoever.popdown()
        name = self.host_remotes[index][0]
        title = self.host_remotes[index][1]
        install_type = self.host_remotes[index][7]

        body_text = _("Any installed apps from {} will stop receiving updates").format(
            name
        )
        dialog = Adw.MessageDialog.new(self, _("Remove {}?").format(title), body_text)
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Remove"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.remove_on_response, dialog.choose_finish, index)
        dialog.present()

    def enable_handler(self, button, index):
        name = self.host_remotes[index][0]
        typeArr = self.host_remotes[index][7]
        type = ""
        if "system" in typeArr:
            type = "system"
        else:
            type = "user"

        try:
            command = [
                "flatpak-spawn",
                "--host",
                "flatpak",
                "remote-modify",
                name,
                f"--{type}",
                "--enable",
            ]
            subprocess.run(command, capture_output=False, check=True, env=self.new_env)
        except subprocess.CalledProcessError as e:
            self.toast_overlay.add_toast(
                Adw.Toast.new(_("Could not enable {}").format(name))
            )
            print(
                f"error in remotes_window.enable_handler: could not enable remote {name}:",
                e,
            )

        self.generate_list()

    def disable_handler(self, button, index, popoever):
        def disable_response(_a, response, _b):
            if response == "cancel":
                return
            try:
                command = [
                    "flatpak-spawn",
                    "--host",
                    "flatpak",
                    "remote-modify",
                    name,
                    f"--{type}",
                    "--disable",
                ]
                subprocess.run(
                    command, capture_output=False, check=True, env=self.new_env
                )
            except subprocess.CalledProcessError as e:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("Could not disable {}").format(name))
                )
                print(
                    f"error in remotes_window.enable_handler: could not disable remote {name}:",
                    e,
                )

            self.generate_list()

        name = self.host_remotes[index][0]
        title = self.host_remotes[index][1]
        typeArr = self.host_remotes[index][7]
        type = ""
        if "system" in typeArr:
            type = "system"
        else:
            type = "user"

        popoever.popdown()

        body_text = _("Any installed apps from {} will stop receiving updates").format(
            name
        )
        dialog = Adw.MessageDialog.new(self, _("Disable {}?").format(title), body_text)
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Disable"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", disable_response, dialog.choose_finish)
        dialog.present()

    def view_paks(self, type, remote):
        if "user" in type:
            type = "user"
        elif "system" in type:
            type = "system"
        else:
            self.make_toast(_("Could not view apps").format(to_copy))
            print(
                "error in remotes_window.view_apps(): remote installation type is not either system or user. type is:",
                type,
            )
            return
        settings = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        for key in settings.list_keys():
            settings.reset(key)
        settings.set_string("remotes-list", f"{remote}<>{type}")
        self.main_window.apply_filter()
        self.close()

    def generate_list(self):
        if self.show_disabled_button.get_active():
            self.show_disabled_button_button_content.set_icon_name(
                "eye-open-negative-filled-symbolic"
            )
        else:
            self.show_disabled_button_button_content.set_icon_name(
                "eye-not-looking-symbolic"
            )

        self.host_remotes = self.my_utils.get_host_remotes()
        self.host_flatpaks = self.get_host_flatpaks()
        for i in range(len(self.rows_in_list)):
            self.remotes_list.remove(self.rows_in_list[i])

        self.rows_in_list = []

        def rowCopyHandler(widget, to_copy):
            self.main_window.clipboard.set(to_copy)
            self.make_toast(_("Copied {}").format(to_copy))

        self.no_remotes.set_visible(True)

        has_disabled = False
        for i in range(len(self.host_remotes)):
            try:
                name = self.host_remotes[i][0]
                title = self.host_remotes[i][1]
                install_type = self.host_remotes[i][7]
                remote_row = Adw.ActionRow(title=title)

                more = Gtk.MenuButton(
                    icon_name="view-more-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("View More")
                )
                more.add_css_class("flat")
                options = Gtk.Popover()
                options_box = Gtk.Box(
                    halign=Gtk.Align.CENTER,
                    valign=Gtk.Align.CENTER,
                    orientation=Gtk.Orientation.VERTICAL,
                )

                filter_button = Gtk.Button()
                filter_button.set_child(
                    Adw.ButtonContent(
                        icon_name="funnel-symbolic", label=_("Set Filter")
                    )
                )
                filter_button.add_css_class("flat")
                filter_button.connect(
                    "clicked",
                    lambda *_, i=i: self.view_paks(
                        self.host_remotes[i][7], self.host_remotes[i][0]
                    ),
                )

                enable_button = Gtk.Button(visible=False)
                enable_button.set_child(
                    Adw.ButtonContent(
                        icon_name="eye-open-negative-filled-symbolic", label=_("Enable")
                    )
                )
                enable_button.add_css_class("flat")
                enable_button.connect("clicked", self.enable_handler, i)

                disable_button = Gtk.Button()
                disable_button.set_child(
                    Adw.ButtonContent(
                        icon_name="eye-not-looking-symbolic", label=_("Disable")
                    )
                )
                disable_button.add_css_class("flat")
                disable_button.connect("clicked", self.disable_handler, i, options)

                remove_button = Gtk.Button()
                remove_button.set_child(
                    Adw.ButtonContent(
                        icon_name="user-trash-symbolic", label=_("Remove")
                    )
                )
                remove_button.add_css_class("flat")
                remove_button.connect("clicked", self.remove_handler, i, options)

                options_box.append(filter_button)
                options_box.append(enable_button)
                options_box.append(disable_button)
                options_box.append(remove_button)
                options.set_child(options_box)
                more.set_popover(options)

                copy_button = Gtk.Button(
                    icon_name="edit-copy-symbolic",
                    valign=Gtk.Align.CENTER,
                    tooltip_text=_("Copy remote name"),
                )
                copy_button.add_css_class("flat")
                copy_button.connect("clicked", rowCopyHandler, name)

                remote_row.add_suffix(copy_button)
                remote_row.add_suffix(more)

                install_type = self.my_utils.get_install_type(install_type)
                if install_type == "disabled":
                    has_disabled = True
                    if not self.show_disabled_button.get_active():
                        continue

                    remote_row.set_subtitle(_("Disabled"))
                    enable_button.set_visible(True)
                    disable_button.set_visible(False)
                    remote_row.add_css_class("warning")
                elif install_type == "user":
                    remote_row.set_subtitle(_("User wide"))
                elif install_type == "system":
                    remote_row.set_subtitle(_("System wide"))
                else:
                    remote_row.set_subtitle(_("Unknown install type"))

                url = self.host_remotes[i][2]
                if title == "-":
                    remote_row.set_title(name)
                self.remotes_list.add(remote_row)
                # subprocess.run(['wget', f'{self.host_remotes[i][11]}'])  Idea to display remote icons... Need internet connection. Not sure if that is worth it
                self.rows_in_list.append(remote_row)
                self.no_remotes.set_visible(False)
            except Exception as e:
                print(
                    "error in remotes_window.generate_list: could not add remote. error:",
                    e,
                )
        self.show_disabled_button.set_visible(has_disabled)

        # Popular remotes
        for i in range(len(self.rows_in_popular_list)):
            self.popular_remotes_list.remove(self.rows_in_popular_list[i])

        self.rows_in_popular_list = []

        remotes = [
            # [Name to show in GUI, Name of remote for system, Link to repo to add, Description of remote]
            [
                "AppCenter",
                "appcenter",
                "https://flatpak.elementary.io/repo.flatpakrepo",
                _("The open source, pay-what-you-want app store from elementary"),
            ],
            [
                "Flathub",
                "flathub",
                "https://dl.flathub.org/repo/flathub.flatpakrepo",
                _("Central repository of Flatpak applications"),
            ],
            [
                "Flathub beta",
                "flathub-beta",
                "https://flathub.org/beta-repo/flathub-beta.flatpakrepo",
                _("Beta builds of Flatpak applications"),
            ],
            [
                "Fedora",
                "fedora",
                "oci+https://registry.fedoraproject.org",
                _("Flatpaks packaged by Fedora Linux"),
            ],
            [
                "GNOME Nightly",
                "gnome-nightly",
                "https://nightly.gnome.org/gnome-nightly.flatpakrepo",
                _("The latest beta GNOME Apps and Runtimes"),
            ],
            [
                "KDE Testing Applications",
                "kdeapps",
                "https://distribute.kde.org/kdeapps.flatpakrepo",
                _("Beta KDE Apps and Runtimes"),
            ],
            [
                "WebKit Developer SDK",
                "webkit-sdk",
                "https://software.igalia.com/flatpak-refs/webkit-sdk.flatpakrepo",
                _("Central repository of the WebKit Developer and Runtime SDK"),
            ],
        ]

        host_remotes = self.my_utils.get_host_remotes()
        host_remotes_names = []

        total_added = 0

        for i in range(len(self.host_remotes)):
            host_remotes_names.append(self.host_remotes[i][0])

        for i in range(len(remotes)):
            if remotes[i][1] in host_remotes_names:
                continue

            total_added += 1
            row = Adw.ActionRow(
                title=remotes[i][0], subtitle=(remotes[i][2]), activatable=True
            )
            row.connect("activated", self.add_handler, remotes[i][1], remotes[i][2])
            row.add_suffix(Gtk.Image.new_from_icon_name("right-large-symbolic"))
            self.rows_in_popular_list.append(row)
            self.popular_remotes_list.add(row)

        self.popular_remotes_list.set_visible(total_added > 0)

    def addRemoteCallback(self, _a, _b):
        self.generate_list()
        self.stack.set_visible_child(self.main_group)

    def addRemoteThread(self, command):
        try:
            subprocess.run(command, capture_output=True, check=True, env=self.new_env)
        except subprocess.CalledProcessError as e:
            self.toast_overlay.add_toast(
                Adw.Toast.new(_("Could not add {}").format(self.name_to_add))
            )
            print(
                "error in remotes_window.addRemoteThread: could not add remote. error:",
                e,
            )

    def on_add_response(self, _dialog, response_id, _function, row):
        if response_id == "cancel":
            self.should_pulse = False
            return

        self.stack.set_visible_child(self.adding)

        install_type = "--user"
        if not self.add_as_user:
            install_type = "--system"

        self.name_to_add = self.name_to_add.strip()
        self.url_to_add = self.url_to_add.strip()

        command = [
            "flatpak-spawn",
            "--host",
            "flatpak",
            "remote-add",
            "--if-not-exists",
            self.name_to_add,
            self.url_to_add,
            install_type,
        ]
        task = Gio.Task.new(None, None, self.addRemoteCallback)
        task.run_in_thread(
            lambda _task, _obj, _data, _cancellable: self.addRemoteThread(command)
        )

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
            name_pattern = re.compile(r"^[a-zA-Z0-9\-._]+$")
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
            url_pattern = re.compile(r"^[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;=]+$")
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

        user_row = Adw.ActionRow(
            title=_("User"), subtitle=_("Remote will be available to only you")
        )
        user_check = Gtk.CheckButton(active=True)
        user_check.connect("toggled", set_user)
        user_row.add_prefix(user_check)
        user_row.set_activatable_widget(user_check)

        system_row = Adw.ActionRow(
            title=_("System"),
            subtitle=_("Remote will be available to every user on the system"),
        )
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

    def add_remote_file_thread(self, filepath, system_or_user, name):
        try:
            subprocess.run(
                [
                    "flatpak-spawn",
                    "--host",
                    "flatpak",
                    "remote-add",
                    "--if-not-exists",
                    name,
                    filepath,
                    f"--{system_or_user}",
                ],
                capture_output=True,
                check=True,
                env=self.new_env,
            )
            self.toast_overlay.add_toast(
                Adw.Toast.new(_("{} successfully added").format(name))
            )
        except subprocess.CalledProcessError as e:
            self.toast_overlay.add_toast(
                Adw.Toast.new(_("Could not add {}").format(self.name_to_add))
            )
            print(
                "error in remotes_window.addRemoteFromFileThread: could not add remote. error:",
                e,
            )

    def add_remote_file(self, filepath):
        def response(dialog, response, _a):
            if response == "cancel":
                self.should_pulse = False
                return

            user_or_system = "user"
            if system_check.get_active():
                user_or_system = "system"

            task = Gio.Task.new(None, None, self.addRemoteCallback)
            task.run_in_thread(
                lambda *_: self.add_remote_file_thread(
                    filepath, user_or_system, name_row.get_text()
                )
            )

        def name_update(widget):
            is_enabled = True
            self.name_to_add = widget.get_text()
            name_pattern = re.compile(r"^[a-zA-Z\-]+$")
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

        name = filepath.split("/")
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
        user_row = Adw.ActionRow(
            title=_("User"), subtitle=_("Remote will be available to only you")
        )
        system_row = Adw.ActionRow(
            title=_("System"),
            subtitle=_("Remote will be available to every user on the system"),
        )
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
            self.add_remote_file(file.get_path())
        except GLib.GError:
            pass

    def add_file_handler(self):
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
        self.main_window = main_window
        self.new_env = dict(os.environ)
        self.new_env["LC_ALL"] = "C"
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

        self.add_from_file.add_suffix(
            Gtk.Image.new_from_icon_name("right-large-symbolic")
        )
        self.add_from_file.connect("activated", lambda *_: self.add_file_handler())
        self.custom_remote.add_suffix(
            Gtk.Image.new_from_icon_name("right-large-symbolic")
        )
        self.custom_remote.connect("activated", self.add_handler)
        self.show_disabled_button.connect("clicked", lambda *_: self.generate_list())

        # Calls
        self.generate_list()
        # self.show_new_remote_options()
