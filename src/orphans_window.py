from gi.repository import Gtk, Adw, GLib, Gdk, Gio
import subprocess
import os

class OrphansWindow:
    window_title = _("Manage Leftover Data")
    orphans_window = Adw.Window(title=window_title)
    orphans_window.set_default_size(350, 450)
    orphans_window.set_modal(True)
    orphans_window.set_resizable(True)
    orphans_scroll = Gtk.ScrolledWindow()
    orphans_toast_overlay = Adw.ToastOverlay()
    orphans_stack = Gtk.Stack()
    orphans_overlay = Gtk.Overlay()
    orphans_stack.add_child(orphans_overlay)
    orphans_toast_overlay.set_child(orphans_stack)

    orphans_progress_bar = Gtk.ProgressBar(visible=False, pulse_step=0.7)
    orphans_progress_bar.add_css_class("osd")
    orphans_overlay.add_overlay(orphans_progress_bar)

    orphans_overlay.set_child(orphans_scroll)
    orphans_toolbar_view = Adw.ToolbarView()
    orphans_title_bar = Gtk.HeaderBar()
    orphans_action_bar = Gtk.ActionBar()
    orphans_toolbar_view.add_top_bar(orphans_title_bar)
    orphans_toolbar_view.add_bottom_bar(orphans_action_bar)
    orphans_toolbar_view.set_content(orphans_toast_overlay)
    orphans_window.set_content(orphans_toolbar_view)
    orphans_list = Gtk.ListBox(selection_mode="none", valign=Gtk.Align.START, margin_top=6, margin_bottom=6, margin_start=12, margin_end=12)
    orphans_list.add_css_class("boxed-list")
    orphans_scroll.set_child(orphans_list)
    no_data = Adw.StatusPage(icon_name="check-plain-symbolic", title=_("No Data"), description=_("There is no leftover user data"))
    orphans_stack.add_child(no_data)
    total_selected = 0
    selected_rows = []
    should_pulse = False
    total_to_install = 0

    def __init__(self, window):
        self.orphans_window.set_transient_for(window)
        self.generate_list(window, False)
        self.orphans_window.present()

    def orphans_pulser(self):
        self.should_pulse
        if should_pulse:
            self.orphans_progress_bar.pulse()
            GLib.timeout_add(500, self.orphans_pulser)

    def toggle_button_handler(self, button):
        if button.get_active():
            generate_list(button, True)
        else:
            generate_list(button, False)

    def generate_list(self, widget, is_select_all):
        orphans_window.set_title(window_title)
        total_selected = 0
        selected_rows = []
        trash_button.set_sensitive(False)
        install_button.set_sensitive(False)

        orphans_list.remove_all()
        file_list = os.listdir(window.user_data_path)
        id_list = []

        for i in range(len(window.host_flatpaks)):
            id_list.append(window.host_flatpaks[i][2])

        row_index = -1
        for i in range(len(file_list)):
            if not file_list[i] in id_list:
                row_index += 1
                select_orphans_tickbox = Gtk.CheckButton(halign=Gtk.Align.CENTER)
                orphans_row = Adw.ActionRow(title=GLib.markup_escape_text(file_list[i]), subtitle=_("~") + window.get_size_format(window.get_directory_size(f"{window.user_data_path}{file_list[i]}")))
                orphans_row.add_suffix(select_orphans_tickbox)
                orphans_row.set_activatable_widget(select_orphans_tickbox)
                select_orphans_tickbox.connect("toggled", selection_handler, orphans_row.get_title())
                if is_select_all == True:
                    select_orphans_tickbox.set_active(True)
                orphans_list.append(orphans_row)
        if not orphans_list.get_row_at_index(0):
            orphans_stack.set_visible_child(no_data)
            orphans_action_bar.set_revealed(False)

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            orphans_window.close()
        elif event == Gdk.KEY_Delete or event == Gdk.KEY_BackSpace:
            trash_button_handler(event)

    def trash_button_handler(self, widget):
        if total_selected == 0:
            return 1
        show_success = True
        for i in range(len(selected_rows)):
            path = f"{window.user_data_path}{selected_rows[i]}"
            try:
                subprocess.run(["flatpak-spawn", "--host", "gio", "trash", path], capture_output=False, check=True)
            except:
                orphans_toast_overlay.add_toast(Adw.Toast.new(_("Can't trash {}").format(selected_rows[i])))
                show_success = False
        select_all_button.set_active(False)

        if show_success:
            orphans_toast_overlay.add_toast(Adw.Toast.new(_("Trashed data")))

        generate_list(widget, False)

    handler_id = 0
    def install_callback(self, *_args):
        total_to_install = total_to_install - 1
            
        if total_to_install == 0:
            if window.install_success:
                orphans_toast_overlay.add_toast(Adw.Toast.new(_("Installed all apps")))
            else:
                orphans_toast_overlay.add_toast(Adw.Toast.new(_("Some apps didn't install")))
            select_all_button.set_active(False)
            self.orphans_progress_bar.set_visible(False)
            should_pulse = False
            window.refresh_list_of_flatpaks(None, False)
            generate_list(None, False)
            orphans_toolbar_view.set_sensitive(True)
            orphans_window.disconnect(handler_id) # Make window able to close

    def thread_func(self, command):
        try:
            subprocess.run(command, capture_output=False, check=True)
        except subprocess.CalledProcessError:
            window.install_success = False

        def install_on_response(_a, response_id, _b):
            if response_id == "cancel":
                should_pulse = False
                self.orphans_progress_bar.set_visible(False)
                return 1

            orphans_toast_overlay.add_toast(Adw.Toast.new(_("This could take some time")))
            orphans_toolbar_view.set_sensitive(False)
            handler_id = orphans_window.connect('close-request', lambda event: True) # Make window unable to close
            total_to_install = len(selected_rows)

            self.orphans_progress_bar.set_visible(True)
            for i in range(len(selected_rows)):
                remote = response_id.split("_")
                command = ["flatpak-spawn", "--host", "flatpak", "install", "-y", remote[0]]
                if "user" in remote[1]:
                    command.append("--user")
                else:
                    command.append("--system")
                command.append(selected_rows[i])

                task = Gio.Task.new(None, None, install_callback)
                task.run_in_thread(lambda _task, _obj, _data, _cancellable, cmd=command: thread_func(cmd))

    def install_button_handler(self, widget):
        window.install_success = True
        should_pulse = True
        self.orphans_pulser()

        def get_host_remotes():
            output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "remotes"], capture_output=True, text=True).stdout
            lines = output.strip().split("\n")
            columns = lines[0].split("\t")
            data = [columns]
            for line in lines[1:]:
                row = line.split("\t")
                data.append(row)
            return data

        host_remotes = get_host_remotes()

        dialog = Adw.MessageDialog.new(window, _("Choose a Remote"))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.connect("response", install_on_response, dialog.choose_finish)
        dialog.set_transient_for(orphans_window)
        if len(host_remotes) > 1:
            dialog.set_body(_("Choose the Flatpak Remote Repository where attempted app downloads will be from."))
            for i in range(len(host_remotes)):
                remote_name = host_remotes[i][0]
                remote_option = host_remotes[i][1]
                dialog.add_response(f"{remote_name}_{remote_option}", f"{remote_name} {remote_option}")
                dialog.set_response_appearance(f"{remote_name}_{remote_option}", Adw.ResponseAppearance.SUGGESTED,)
        else:
            remote_name = host_remotes[0][0]
            remote_option = host_remotes[0][1]
            dialog.set_heading("Attempt to Install Matching Flatpaks?")
            dialog.add_response(f"{remote_name}_{remote_option}", _("Continue"))
        Gtk.Window.present(dialog)

    event_controller = Gtk.EventControllerKey()
    event_controller.connect("key-pressed", key_handler)
    orphans_window.add_controller(event_controller)

    select_all_button = Gtk.ToggleButton(label=_("Select All"))
    select_all_button.connect("toggled", toggle_button_handler)
    orphans_action_bar.pack_start(select_all_button)

    trash_button = Gtk.Button(label="Trash", valign=Gtk.Align.CENTER, tooltip_text=_("Trash Selected"))
    trash_button.add_css_class("destructive-action")
    trash_button.connect("clicked", trash_button_handler)
    orphans_action_bar.pack_end(trash_button)

    install_button = Gtk.Button(label="Install", valign=Gtk.Align.CENTER, tooltip_text=_("Attempt to Install Selected"))
    install_button.connect("clicked", install_button_handler)
    install_button.set_visible(False)
    orphans_action_bar.pack_end(install_button)
    test = subprocess.run(["flatpak-spawn", "--host", "flatpak", "remotes"], capture_output=True, text=True).stdout
    for char in test:
        if char.isalnum():
            install_button.set_visible(True)

    def selection_handler(self, tickbox, file):
        global total_selected
        global selected_rows
        if tickbox.get_active() == True:
            total_selected += 1
            selected_rows.append(file)
        else:
            total_selected -= 1
            to_find = file
            selected_rows.remove(to_find)

        if total_selected == 0:
            orphans_window.set_title(window_title)
            trash_button.set_sensitive(False)
            install_button.set_sensitive(False)
            select_all_button.set_active(False)
        else:
            orphans_window.set_title(_("{} Selected").format(total_selected))
            trash_button.set_sensitive(True)
            install_button.set_sensitive(True)
