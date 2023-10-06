from gi.repository import GLib, Gtk #Adw, Gdk, Gio
import os
import subprocess
import pathlib

class myUtils:
    def __init__(self, window, **kwargs):
        self.main_window = window
        self.host_home = str(pathlib.Path.home())
        self.user_data_path = self.host_home + "/.var/app/"
        self.install_success = True
        self.uninstall_success = True
        self.new_env = dict( os.environ ) 
        self.new_env['LC_ALL'] = 'C' 
        
    def trashFolder(self, path):
        if not os.path.exists(path):
            return 1
        try:
            subprocess.run(["flatpak-spawn", "--host", "gio", "trash", path], capture_output=True, check=True, env=self.new_env)
            return 0
        except subprocess.CalledProcessError:
            return 2

    def getSizeWithFormat(self, path):
        return self.getSizeFormat(self.getDirectorySize(path))

    def getSizeFormat(self, b):
        factor = 1024
        suffix = "B"
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.1f}{unit}{suffix}"
            b /= factor
        return f"{b:.1f}{suffix}"

    def getDirectorySize(self, directory):
        """Returns the `directory` size in bytes."""
        total = 0
        try:
            # print("[+] Getting the size of", directory)
            for entry in os.scandir(directory):
                if entry.is_symlink():
                    continue  # Skip symlinks
                if entry.is_file():
                    # if it's a file, use stat() function
                    total += entry.stat().st_size
                elif entry.is_dir():
                    # if it's a directory, recursively call this function
                    try:
                        total += self.getDirectorySize(entry.path)
                    except FileNotFoundError:
                        pass
        except NotADirectoryError:
            # if `directory` isn't a directory, get the file size then
            return os.path.getsize(directory)
        except PermissionError:
            # if for whatever reason we can't open the folder, return 0
            return 0
        return total

    def findAppIcon(self, app_id):
        icon_theme = Gtk.IconTheme.new()
        icon_theme.add_search_path("/var/lib/flatpak/exports/share/icons/")
        icon_theme.add_search_path(self.host_home + "/.local/share/flatpak/exports/share/icons")
        
        try:
            icon_path = (icon_theme.lookup_icon(app_id, None, 512, 1, self.main_window.get_direction(), 0).get_file().get_path())
        except GLib.GError:
            icon_path = None
        if icon_path:
            image = Gtk.Image.new_from_file(icon_path)
            image.set_icon_size(Gtk.IconSize.LARGE)
            image.add_css_class("icon-dropshadow")
        else:
            image = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
            image.set_icon_size(Gtk.IconSize.LARGE)
        return image

    def getHostPins(self):
        output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "pin"], capture_output=True, text=True, env=self.new_env).stdout
        data = output.strip().split("\n")
        for i in range(len(data)):
            data[i] = data[i].strip()
        return data

    def getHostRemotes(self):
        output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "remotes", "--columns=all"], capture_output=True, text=True, env=self.new_env).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row)
        try:
            for i in range(len(data)):
                data[i][7] = data[i][7].split(",")
                for j in range(len(data[i])):
                    if data[i][7][j] == "user":
                        data[i][7] = "user"
                        break

                    if data[i][7][j] == "system":
                        data[i][7] = "system"
                        break
        except:
            print("error getting remote installation types")
        return data

    def getHostFlatpaks(self):
        output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "list", "--columns=all"], capture_output=True, text=True, env=self.new_env).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row)

        output = subprocess.run(["flatpak-spawn", "--host", "flatpak", "list", "--columns=runtime"], capture_output=True, text=True, env=self.new_env).stdout
        lines = output.strip().split("\n")
        for i in range(len(lines)):
            data[i].append(lines[i])
        return data

    def uninstallFlatpak(self, ref_arr, type_arr, should_trash):
        self.uninstall_success = True

        to_uninstall = []
        for i in range(len(ref_arr)):
            to_uninstall.append([ref_arr[i], type_arr[i]])

        apps = []
        fails = []
        for i in range(len(to_uninstall)):
            ref = to_uninstall[i][0]
            id = to_uninstall[i][0].split("/")[0]
            app_type = to_uninstall[i][1]
            apps.append([ref, id, app_type])
        # apps array guide: [app_ref, app_id, user_or_system_install]

        for i in range(len(apps)):
            command = ['flatpak-spawn', '--host', 'flatpak', 'remove', '-y', f"--{apps[i][2]}", apps[i][0]]
            try:
                subprocess.run(command, capture_output=False, check=True, env=self.new_env)
            except subprocess.CalledProcessError:
                fails.append(apps[i])

        if len(fails) > 0: # Run this only if there is 1 or more non uninstalled apps
            pk_command = ['flatpak-spawn', '--host', 'pkexec', 'flatpak', 'remove', '-y', '--system']
            print("second uninstall process")
            for i in range(len(fails)):

                if fails[i][2] == "user":
                    self.uninstall_success = False
                    continue # Skip if app is a user install app

                pk_command.append(fails[i][0])
            try:
                print(pk_command)
                subprocess.run(pk_command, capture_output=False, check=True, env=self.new_env)
            except subprocess.CalledProcessError:
                self.uninstall_success = False

        if should_trash:
            host_paks = self.getHostFlatpaks()
            host_refs = []
            for i in range(len(host_paks)):
                host_refs.append(host_paks[i][8])

            for i in range(len(apps)):
                if apps[i][0] in host_refs:
                    print(f"{apps[i][1]} is still installed")
                else:
                    self.trashFolder(f"{self.user_data_path}{apps[i][1]}")

    def installFlatpak(self, app_arr, remote, user_or_system):
        self.install_success = True
        fails = []

        for i in range(len(app_arr)):
            command = ['flatpak-spawn', '--host', 'flatpak', 'install', remote, f"--{user_or_system}", '-y', app_arr[i]]
            try:
                subprocess.run(command, capture_output=False, check=True, env=self.new_env)
            except subprocess.CalledProcessError:
                fails.append(app_arr[i])
        
        if (len(fails) > 0) and (user_or_system == "system"):
            pk_command = ['flatpak-spawn', '--host', 'pkexec', 'flatpak', 'install', remote, f"--{user_or_system}", '-y']
            for i in range(len(fails)):
                pk_command.append(fails[i])
            try:
                subprocess.run(pk_command, capture_output=False, check=True, env=self.new_env)
            except subprocess.CalledProcessError:
                self.install_success = False

        if (len(fails) > 0) and (user_or_system == "user"):
            self.install_success = False