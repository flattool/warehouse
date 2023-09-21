from gi.repository import GLib, Gtk #Adw, Gdk, Gio
import os
import subprocess
import pathlib

class functions():
    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.main_window = window
        self.host_home = str(pathlib.Path.home())
        self.user_data_path = self.host_home + "/.var/app/"

    def trash_folder(self, path):
        if not os.path.exists(path):
            return 1
        try:
            subprocess.run(["flatpak-spawn", "--host", "gio", "trash", path], capture_output=True, check=True)
            return 0
        except subprocess.CalledProcessError:
            return 2

    def get_size_format(self, b):
        factor = 1024
        suffix = "B"
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.1f}{unit}{suffix}"
            b /= factor
        return f"{b:.1f}{suffix}"

    def get_directory_size(self, directory):
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
                        total += self.get_directory_size(entry.path)
                    except FileNotFoundError:
                        pass
        except NotADirectoryError:
            # if `directory` isn't a directory, get the file size then
            return os.path.getsize(directory)
        except PermissionError:
            # if for whatever reason we can't open the folder, return 0
            return 0
        return total

    def find_app_icon(self, app_id):
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