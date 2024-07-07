import subprocess, os, pathlib

from gi.repository import Gio, Gtk, GLib, Adw
# from .app_row import AppRow

home = f"{pathlib.Path.home()}"
icon_theme = Gtk.IconTheme.new()
icon_theme.add_search_path(f"{home}/.local/share/flatpak/exports/share/icons")
direction = Gtk.Image().get_direction()

class Flatpak:

    def open_data(self):
        if not os.path.exists(self.data_path):
            return f"Path '{self.data_path}' does not exist"
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{self.data_path}", None)
        except GLib.GError as e:
            return e

    def get_data_size(self, callback=None):
        size = [None]
        def thread(*args):
            sed = "sed 's/K/ KB/; s/M/ MB/; s/G/ GB/; s/T/ TB/; s/P/ PB/;'"
            size[0] = subprocess.run(['sh', '-c', f"du -sh {self.data_path} | {sed}"], capture_output=True, text=True).stdout.split("\t")[0]
        def on_done(*arg):
            if callback:
                callback(f"~ {size[0]}")
        Gio.Task.new(None, None, on_done).run_in_thread(thread)

    def trash_data(self, callback=None):
        try:
            subprocess.run(['gio', 'trash', f"{self.data_path}"])
        except Exception as e:
            raise e

    def get_cli_info(self):
        cli_info = {}
        cmd = "LC_ALL=C flatpak info "
        installation = self.info["installation"]

        if installation == "user":
            cmd += "--user "
        elif installation == "system":
            cmd += "--system "
        else:
            cmd += f"--installation={installation} "

        cmd += self.info["ref"]

        try:
            output = subprocess.run(['flatpak-spawn', '--host', 'sh', '-c', cmd], text=True, capture_output=True).stdout
        except Exception as e:
            raise e

        lines = output.strip().split("\n")
        for i, word in enumerate(lines):
            word = word.strip().split(": ", 1)
            if len(word) < 2:
                continue

            word[0] = word[0].lower()
            if "installed" in word[0]:
                word[1] = word[1].replace("?", " ")
            cli_info[word[0]] = word[1]

        return cli_info

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
        self.data_path = f"{home}/.var/app/{columns[2]}"
        self.data_size = -1
        installation = columns[7]
        if len(i := installation.split(' ')) > 1:
            self.info["installation"] = i[1].replace("(", "").replace(")", "")
        else:
            self.info["installation"] = installation

        self.is_masked = self.info["id"] in HostInfo.masks[self.info["installation"]]

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
            self.icon_path = None


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
    remotes = []
    installations = []
    masks = {}
    pins = {}
    @classmethod
    def get_flatpaks(this, callback=None):
        # Callback is a function to run after the host flatpaks are found
        this.flatpaks.clear()
        this.remotes.clear()
        this.installations.clear()
        this.masks.clear()
        this.pins.clear()

        def thread(task, *args):

            # Remotes
            def remote_info(installation):
                # cmd = ['flatpak-spawn', '--host',
                # 'flatpak', 'remotes']
                # if installation == "user" or installation == "system":
                #     cmd.append(f"--{installation}")
                # else:
                #     cmd.append(f"--installation={installation}")
                # output = subprocess.run(
                #     cmd, text=True,
                #     capture_output=True,
                # ).stdout
                # lines = output.strip().split("\n")
                # for i in lines:
                #     if i != "":
                #         this.remotes.append(Remote(i.strip(), installation))
                #         if installation == "user" or installation == "system":
                #             this.installations.append(installation)

                # Masks
                cmd = ['flatpak-spawn', '--host',
                'flatpak', 'mask',]
                if installation == "user" or installation == "system":
                    cmd.append(f"--{installation}")
                else:
                    cmd.append(f"--installation={installation}")
                output = subprocess.run(
                    cmd, text=True,
                    capture_output=True,
                ).stdout
                lines = output.strip().replace(" ", "").split("\n")
                if lines[0] != '':
                    this.masks[installation] = lines

                # Pins
                cmd = ['flatpak-spawn', '--host',
                'flatpak', 'pin',]
                if installation == "user" or installation == "system":
                    cmd.append(f"--{installation}")
                else:
                    cmd.append(f"--installation={installation}")
                output = subprocess.run(
                    cmd, text=True,
                    capture_output=True,
                ).stdout
                lines = output.strip().replace(" ", "").split("\n")
                if lines[0] != '':
                    this.pins[installation] = lines

            # Installations
            # Get all config files for any extra installations
            custom_install_config_path = "/run/host/etc/flatpak/installations.d"
            if os.path.exists(custom_install_config_path):
                for file in os.listdir(custom_install_config_path):
                    with open(f"{custom_install_config_path}/{file}", "r") as f:
                        for line in f:
                            if line.startswith("[Installation"):
                                # Get specifically the installation name itself
                                this.installations.append(line.replace("[Installation \"", "").replace("\"]", "").strip())

            for i in this.installations:
                remote_info(i)
            remote_info("user")
            remote_info("system")

            # Packages
            output = subprocess.run(
                ['flatpak-spawn', '--host',
                'flatpak', 'list', '--columns=all'],
                text=True,
                capture_output=True,
            ).stdout
            lines = output.strip().split("\n")
            for i in lines:
                this.flatpaks.append(Flatpak(i.split("\t")))
            this.flatpaks = sorted(this.flatpaks, key=lambda flatpak: flatpak.info["name"].lower())

        Gio.Task.new(None, None, callback).run_in_thread(thread)