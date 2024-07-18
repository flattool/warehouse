import subprocess, os, pathlib

from gi.repository import Gio, Gtk, GLib, Adw, Gdk
# from .app_row import AppRow

home = f"{pathlib.Path.home()}"
icon_theme = Gtk.IconTheme.new()
icon_theme.add_search_path(f"{home}/.local/share/flatpak/exports/share/icons")
direction = Gtk.Image().get_direction()

class Flatpak:

    def open_app(self, callback=None):
        self.failed_app_run = None
        def thread(*args):
            if self.is_runtime:
                self.failed_app_run = "error: cannot open a runtime"
            try:
                subprocess.run(['flatpak-spawn', '--host', 'flatpak', 'run', f"{self.info['ref']}"], capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as cpe:
                self.failed_app_run = cpe
            except Exception as e:
                self.failed_app_run = e

        Gio.Task.new(None, None, callback).run_in_thread(thread)

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
            subprocess.run(['gio', 'trash', f"{self.data_path}"], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as cpe:
            raise cpe
        except Exception as e:
            raise e

    def set_mask(self, should_mask, callback=None):
        self.failed_mask = None
        def thread(*args):
            cmd = ['flatpak-spawn', '--host', 'flatpak', 'mask', self.info["id"]]
            installation = self.info["installation"]
            if installation == "user" or installation == "system":
                cmd.append(f"--{installation}")
            else:
                cmd.append(f"--installation={installation}")
            
            if not should_mask:
                cmd.append("--remove")
            
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as cpe:
                self.failed_mask = cpe
            except Exception as e:
                self.failed_mask = e

        Gio.Task.new(None, None, callback).run_in_thread(thread)

    def set_pin(self, should_pin, callback=None):
        self.failed_pin = None
        if not self.is_runtime:
            self.failed_pin = "Cannot pin an application"
        
        def thread(*args):
            cmd = ['flatpak-spawn', '--host', 'flatpak', 'pin', f"runtime/{self.info['ref']}"]
            installation = self.info["installation"]
            if installation == "user" or installation == "system":
                cmd.append(f"--{installation}")
            else:
                cmd.append(f"--installation={installation}")

            if not should_pin:
                cmd.append("--remove")

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as cpe:
                self.failed_pin = cpe
            except Exception as e:
                self.failed_mask = e

        Gio.Task.new(None, None, callback).run_in_thread(thread)

    def uninstall(self, callback=None):
        self.failed_uninstall = None

        def thread(*args):
            prefix = ['flatpak-spawn', '--host']
            cmd = ['flatpak', 'uninstall', '-y', self.info["ref"]]
            installation = self.info["installation"]
            if installation == "system" or installation == "user":
                cmd.append(f"--{installation}")
            else:
                cmd.append(f"--installation={installation}")

            try:
                subprocess.run(prefix + cmd, check=True, text=True, capture_output=True)
                # print(prefix + cmd)
            except subprocess.CalledProcessError as cpe:
                if installation == "user":
                    self.failed_uninstall = cpe
                    return
                
                try:
                    subprocess.run(prefix + ['pkexec'] + cmd, check=True, text=True)
                except subprocess.CalledProcessError as cpe2:
                    self.failed_uninstall = cpe2
                except Exception as e2:
                    self.failed_uninstall = e2

            except Exception as e:
                self.failed_uninstall = e

        Gio.Task.new(None, None, callback).run_in_thread(thread)

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

        self.cli_info = cli_info
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
        self.cli_info = None
        installation = columns[7]
        if len(i := installation.split(' ')) > 1:
            self.info["installation"] = i[1].replace("(", "").replace(")", "")
        else:
            self.info["installation"] = installation

        self.is_eol = "eol=" in self.info["options"]
        self.dependant_runtime = None
        self.failed_app_run = None
        self.failed_mask = None
        self.failed_uninstall = None
        self.app_row = None

        try:
            self.is_masked = self.info["id"] in HostInfo.masks[self.info["installation"]]
        except KeyError:
            self.is_masked = False

        try:
            self.is_pinned = f"runtime/{self.info['ref']}" in HostInfo.pins[self.info["installation"]]
        except KeyError:
            self.is_pinned = False

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
    def __init__(self, name, title):
        self.name = name
        self.title = title
        if title == "" or title == "-":
            self.title = name

class HostInfo:
    home = home
    clipboard = Gdk.Display.get_default().get_clipboard()

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
    id_to_flatpak = {}
    ref_to_flatpak = {}
    remotes = {}
    installations = []
    masks = {}
    pins = {}
    dependant_runtime_refs = []
    @classmethod
    def get_flatpaks(this, callback=None):
        # Callback is a function to run after the host flatpaks are found
        this.flatpaks.clear()
        this.id_to_flatpak.clear()
        this.ref_to_flatpak.clear()
        this.remotes.clear()
        this.installations.clear()
        this.masks.clear()
        this.pins.clear()
        this.dependant_runtime_refs.clear()

        def thread(task, *args):

            # Remotes
            def remote_info(installation):
                cmd = ['flatpak-spawn', '--host',
                'flatpak', 'remotes', '--columns=name,title']
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
                    remote_list = []
                    for line in lines:
                        line = line.split("\t")
                        remote_list.append(Remote(line[0], line[1]))
                    this.remotes[installation] = remote_list

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

            this.installations.append("user")
            this.installations.append("system")
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
                package = Flatpak(i.split("\t"))
                this.flatpaks.append(package)
                this.id_to_flatpak[package.info["id"]] = package
                this.ref_to_flatpak[package.info["ref"]] = package
            
            # Dependant Runtimes
            output = subprocess.run(
                ['flatpak-spawn', '--host',
                'flatpak', 'list', '--columns=runtime'],
                text=True,
                capture_output=True,
            ).stdout
            lines = output.strip().split("\n")
            for index, runtime in enumerate(lines):
                package = this.flatpaks[index]
                if package.is_runtime:
                    continue
                package.dependant_runtime = this.ref_to_flatpak[runtime]
                if not runtime in this.dependant_runtime_refs:
                    this.dependant_runtime_refs.append(runtime)

            this.flatpaks = sorted(this.flatpaks, key=lambda flatpak: flatpak.info["name"].lower())
            this.dependant_runtime_refs = sorted(this.dependant_runtime_refs)

        Gio.Task.new(None, None, callback).run_in_thread(thread)