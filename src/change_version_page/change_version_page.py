from gi.repository import Adw, Gtk,GLib, Gio
from .error_toast import ErrorToast
from .host_info import HostInfo
import subprocess, os

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/change_version_page/change_version_page.ui")
class ChangeVersionPage(Adw.NavigationPage):
    __gtype_name__ = 'ChangeVersionPage'
    gtc = Gtk.Template.Child
    toast_overlay = gtc()
    scrolled_window = gtc()
    root_group_check_button = gtc()
    mask_group = gtc()
    mask_row = gtc()
    versions_group = gtc()
    action_bar = gtc()

    selected_commit = None
    failure = None

    def get_commits(self, *args):
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
        try:
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
        except subprocess.CalledProcessError as cpe:
            self.failure = cpe.stderr
            return
        except Exception as e:
            self.failure = str(e)
            return

        if not (len(commits) == len(changes) == len(dates)):
            self.failure = "Commits, Changes, and Dates are not of equivalent length"
            return

        def idle(*args):
            for index, commit in enumerate(commits):
                row = Adw.ActionRow(title=GLib.markup_escape_text(changes[index]), subtitle=f"{GLib.markup_escape_text(commit)}\n{GLib.markup_escape_text(dates[index])}")
                check = Gtk.CheckButton()
                check.connect("activate", lambda *_, comm=commit: self.set_commit(comm))
                check.set_group(self.root_group_check_button)
                row.set_activatable_widget(check)
                row.add_prefix(check)
                self.versions_group.add(row)

        GLib.idle_add(idle)

    def set_commit(self, commit):
        self.selected_commit = commit

    def callback(self, *args):
        if not self.failure is None:
            self.toast_overlay.add_toast(ErrorToast(_("Could not get versions"), self.failure).toast)
        else:
            print("yay")


    def __init__(self, main_window, package, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.package = package

        # Apply
        pkg_name = package.info["name"]
        self.set_title(_("{} Versions").format(pkg_name))
        self.mask_row.set_subtitle(_("Ensure that {} will never be updated to a newer version").format(pkg_name))
        
        Gio.Task.new(None, None, self.callback).run_in_thread(self.get_commits)

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