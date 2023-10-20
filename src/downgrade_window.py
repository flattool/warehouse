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
    versions_listbox = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    mask_row = Gtk.Template.Child()

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

    def commitsResponse(self):
        self.progress_bar.set_visible(False)
        self.should_pulse = False
        for i in range(len(self.versions)):
            version = self.versions[i]
            row = Adw.ActionRow(title=version[2], subtitle=version[1])
            select = Gtk.CheckButton()
            select.connect("toggled", self.selectionHandler, i)
            
            if i > 0:
                select.set_group(self.versions[i-1][3])

            version.append(select)
            row.set_activatable_widget(select)
            row.add_prefix(select)
            self.versions_listbox.append(row)

    def generateList(self):
        task = Gio.Task.new(None, None, lambda *_: self.commitsResponse())
        task.run_in_thread(lambda *_: self.getCommits())

    def __init__(self, parent_window, flatpak_row_item, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.app_name = flatpak_row_item[0]
        self.app_id = flatpak_row_item[2]
        self.remote = flatpak_row_item[6]
        self.install_type = flatpak_row_item[7]
        self.app_ref = flatpak_row_item[8]
        self.versions = []
        self.should_pulse = True
        self.commit_to_use = ""
        event_controller = Gtk.EventControllerKey()

        # Connections
        event_controller.connect("key-pressed", self.key_handler)
        self.cancel_button.connect("clicked", lambda *_: self.close())

        # Apply
        self.pulser()
        self.add_controller(event_controller)
        self.set_title(_("Downgrade {}").format(self.app_name))
        self.set_transient_for(parent_window)
        # print(self.mask_row.get_active())

        self.generateList()

        self.present()