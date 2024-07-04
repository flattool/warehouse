import gi, subprocess, os, pathlib

gi.require_version('Gtk', '4.0')

from gi.repository import Gio, Gtk, GLib

home = f"{pathlib.Path.home()}"
icon_theme = Gtk.IconTheme.new()
icon_theme.add_search_path(f"{home}/.local/share/flatpak/exports/share/icons")
direction = Gtk.Image().get_direction()

class Flatpak:
    def __init__(self, columns):
        self.is_runtime = "runtime" in columns[12]
        self.info = {
            "name":           columns[0],
            "description":    columns[1],
            "id":             columns[2],
            "version":        columns[3],
            "branch":         columns[4],
            "arch":           columns[5],
            "origin":         columns[6],
            "ref":            columns[8],
            "installed_size": columns[11],
            "options":        columns[12],
        }
        self.data_path = f"{home}/{columns[2]}"
        installation = columns[7]
        if len(i := installation.split(' ')) > 1:
            self.info["installation"] = i[1].replace("(", "").replace(")", "")
        else:
            self.info["installation"] = installation

        try:
            self.icon_path = (
                icon_theme.lookup_icon(
                    self.info["id"], None, 512, 1, direction, 0
                )
                .get_file()
                .get_path()
            )
        except GLib.GError as e:
            print(e)
            icon_path = None


class Remote:
    def __init__(self, name, installation):
        self.name = name
        self.installation = installation

class HostInfo:
    home = home

    # Get all possible installation icon theme dirs
    output = subprocess.run(
        ['flatpak-spawn', '--host',
        'flatpak', '--installations'],
        text=True,
        capture_output=True,
    ).stdout
    lines = output.strip().split("\n")
    for i in lines:
        icon_theme.add_search_path(f"{i}/exports/share/icons")
    
    flatpaks = []
    @classmethod
    def get_flatpaks(this, callback=None):
        # Callback is a function to run after the host flatpaks are found
        this.flatpaks.clear()

        def thread(task, *args):
            output = subprocess.run(
                ['flatpak-spawn', '--host',
                'flatpak', 'list', '--columns=all'],
                text=True,
                capture_output=True,
            ).stdout
            lines = output.strip().split("\n")
            for i in lines:
                this.flatpaks.append(Flatpak(i.split("\t")))

        Gio.Task.new(None, None, callback).run_in_thread(thread)

    remotes = []
    installations = []
    @classmethod
    def get_remotes(this, callback=None):
        # Callback is a function to run after the host remotes are found
        this.remotes.clear()
        this.installations.clear()

        def thread(task, *args):
            
            # Get all config files for any extra installations
            custom_install_config_path = "/run/host/etc/flatpak/installations.d"
            if os.path.exists(custom_install_config_path):
                for file in os.listdir(custom_install_config_path):
                    with open(f"{custom_install_config_path}/{file}", "r") as f:
                        for line in f:
                            if line.startswith("[Installation"):
                                # Get specifically the installation name itself
                                this.installations.append(line.replace("[Installation \"", "").replace("\"]", "").strip())

            def remote_info(installation):
                cmd = ['flatpak-spawn', '--host',
                'flatpak', 'remotes']
                if installation == "user":
                    cmd.append("--user")
                elif installation == "system":
                    cmd.append("--system")
                else:
                    cmd.append(f"--installation={installation}")
                output = subprocess.run(
                    cmd, text=True,
                    capture_output=True,
                ).stdout
                lines = output.strip().split("\n")
                for i in lines:
                    if i != "":
                        this.remotes.append(Remote(i.strip(), installation))
                        if installation == "user" or installation == "system":
                            this.installations.append(installation)

            for i in this.installations:
                remote_info(i)
            remote_info("user")
            remote_info("system")

        Gio.Task.new(None, None, callback).run_in_thread(thread)