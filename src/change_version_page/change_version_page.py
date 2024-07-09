from gi.repository import Adw, Gtk,GLib#, Gio, Pango
from .error_toast import ErrorToast
from .host_info import HostInfo
import subprocess, os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/change_version_page/change_version_page.ui")
class ChangeVersionPage(Adw.NavigationPage):
    __gtype_name__ = 'ChangeVersionPage'
    gtc = Gtk.Template.Child
    scrolled_window = gtc()
    root_group_check_button = gtc()
    mask_group = gtc()
    mask_row = gtc()
    versions_group = gtc()
    action_bar = gtc()

    def get_commits(self):
        cmd = ['flatpak-spawn', '--host', 'sh', '-c'] 
        script = f"LC_ALL=C flatpak remote-info --log {self.package.info['origin']} {self.package.info['ref']} "
        installation = self.package.info["installation"]
        if installation == "user" or installation == "system":
            script += f"--{installation}"
        else:
            script += f"--installation={installation}"
        
        cmd.append(script)
        
        commits = []
        changes = []
        dates   = []
        output = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
        lines = output.strip().split('\n')
        for line in lines:
            line = line.strip().split(": ", 1)
            if len(line) < 2:
                continue
            elif line[0].startswith("Commit"):
                commits.append(line[1])
            elif line[0].startswith("Subject"):
                changes.append(line[1])
            elif line[0].startswith("Date"):
                dates.append(line[1])

        if not (len(commits) == len(changes) == len(dates)):
            return

        for index, element in enumerate(changes):
            row = Adw.ActionRow(title=GLib.markup_escape_text(element), subtitle=GLib.markup_escape_text(dates[index]))
            self.versions_group.add(row)

    def __init__(self, main_window, package, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.package = package

        # Apply
        pkg_name = package.info["name"]
        self.set_title(_("{} Versions").format(pkg_name))
        self.mask_row.set_subtitle(_("Ensure that {} will never be updated to a newer version").format(pkg_name))
        self.get_commits()

        # for i in range(10):
        #     row = Adw.ActionRow(title=f"Update to {i}.0", subtitle="Some dumb nerd shit I don't care about", activatable=True)
        #     check_button = Gtk.CheckButton()
        #     check_button.set_group(self.root_group_check_button)
        #     prev_check = check_button
        #     row.add_prefix(check_button)
        #     row.set_activatable_widget(check_button)
        #     self.versions_group.add(row)

        # Connections
        self.root_group_check_button.connect("toggled", lambda *_: self.action_bar.set_revealed(True))