from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/downgrade.ui")
class DowngradeWindow(Adw.Window):
    __gtype_name__ = "DowngradeWindow"
    
    new_env = dict( os.environ )
    new_env['LC_ALL'] = 'C'

    cancel_button = Gtk.Template.Child()
    apply_button = Gtk.Template.Child()
    versions_group = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    mask_row = Gtk.Template.Child()
    main_toolbar_view = Gtk.Template.Child()

    def pulser(self):
        if self.should_pulse:
            self.progress_bar.pulse()
            GLib.timeout_add(500, self.pulser)

    def key_handler(self, _a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            self.close()

    def selectionHandler(self, button, index):
        self.apply_button.set_sensitive(True)
        if button.get_active():
            self.commit_to_use = self.versions[index][0]

    def getCommits(self):
        output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "remote-info", "--log", self.remote, self.app_ref, f"--{self.install_type}"], capture_output=True, text=True, env=self.new_env).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row[0].strip())
        
        commits = []
        changes = []
        dates = []
        for i in range(len(data)):
            line = data[i]

            if "Commit:" in line:
                commits.append(line.replace("Commit: ", ""))

            if "Subject:" in line:
                changes.append(line.replace("Subject: ", ""))

            if "Date:" in line:
                dates.append(line.replace("Date: ", ""))

        for i in range(len(commits)):
            self.versions.append([commits[i], changes[i], dates[i]])

    def commitsCallback(self):
        self.progress_bar.set_visible(False)
        self.should_pulse = False
        for i in range(len(self.versions)):
            version = self.versions[i]
            date_time = version[2].split(' ')
            date = date_time[0].split('-')
            offset = date_time[2][:3] + ":" + date_time[2][3:]
            time = date_time[1].split(':')
            display_time = GLib.DateTime.new(GLib.TimeZone.new(offset), int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]), int(time[2]))
            display_time = display_time.format("%x %X")
            change = version[1].split('(')
            row = Adw.ActionRow(title=GLib.markup_escape_text(change[0]), subtitle=str(display_time))
            row.set_tooltip_text(_("Commit Hash: {}").format(version[0]))
            select = Gtk.CheckButton()
            select.connect("toggled", self.selectionHandler, i)
            
            if i > 0:
                select.set_group(self.versions[i-1][3])

            version.append(select)
            row.set_activatable_widget(select)
            row.add_prefix(select)
            self.versions_group.add(row)
        self.set_title(self.window_title)

    def generateList(self):
        task = Gio.Task.new(None, None, lambda *_: self.commitsCallback())
        task.run_in_thread(lambda *_: self.getCommits())

    def downgradeCallack(self):
        self.progress_bar.set_visible(False)
        self.should_pulse = False
        self.disconnect(self.no_close)
        self.main_toolbar_view.set_sensitive(True)
        self.progress_bar.set_visible = False

        if self.response != 0:
            self.toast_overlay.add_toast(Adw.Toast.new(_("Could not downgrade {}").format(self.app_name)))
            return
        
        if self.mask_row.get_active():
            if self.my_utils.maskFlatpak(self.app_id, self.install_type) == 0:
                self.flatpak_row[7].set_visible(True)
            else:
                self.parent_window.toast_overlay.add_toast(Adw.Toast.new(_("Could not mask {}").format(self.app_name)))

        self.close()

    def downgradeThread(self):
        self.response = self.my_utils.downgradeFlatpak(self.app_ref, self.commit_to_use, self.install_type)

    def onApply(self):
        self.set_title(_("Downgrading..."))
        self.no_close = self.connect("close-request", lambda event: True)
        self.main_toolbar_view.set_sensitive(False)
        self.should_pulse = True
        self.progress_bar.set_visible(True)
        self.pulser()
        
        task = Gio.Task.new(None, None, lambda *_: self.downgradeCallack())
        task.run_in_thread(lambda *_: self.downgradeThread())

    def __init__(self, parent_window, flatpak_row, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.app_name = flatpak_row[6][0]
        self.app_id = flatpak_row[6][2]
        self.remote = flatpak_row[6][6]
        self.install_type = flatpak_row[6][7]
        self.app_ref = flatpak_row[6][8]
        self.versions = []
        self.should_pulse = True
        self.commit_to_use = ""
        self.parent_window = parent_window
        self.flatpak_row = flatpak_row
        self.response = 0
        self.window_title = _("Downgrade {}").format(self.app_name)
        event_controller = Gtk.EventControllerKey()

        # Connections
        event_controller.connect("key-pressed", self.key_handler)
        self.cancel_button.connect("clicked", lambda *_: self.close())
        self.apply_button.connect("clicked", lambda *_: self.onApply())

        # Apply
        self.pulser()
        self.add_controller(event_controller)
        self.set_title(_("Fetching Releases..."))
        self.set_transient_for(parent_window)

        self.generateList()

        self.present()