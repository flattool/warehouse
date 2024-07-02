from gi.repository import GLib, Gtk, Adw, Gio  # , Gdk
import os
import subprocess
import pathlib
import time


class myUtils:
    def __init__(self, window, **kwargs):
        self.parent_window = window
        self.host_home = str(pathlib.Path.home())
        self.user_data_path = self.host_home + "/.var/app/"
        self.install_success = True
        self.uninstall_success = True
        self.new_env = dict(os.environ)
        self.new_env["LC_ALL"] = "C"
        self.is_dialog_open = False

    def trash_folder(self, path):
        if not os.path.exists(path):
            print("error in common.trashFolder: path does not exists. path =", path)
            return 1
        try:
            subprocess.run(
                ["gio", "trash", path],
                capture_output=False,
                check=True,
                env=self.new_env,
            )
            return 0
        except subprocess.CalledProcessError as e:
            print("error in common.trashFolder: CalledProcessError:", e)
            return 2

    def get_size_with_format(self, path):
        return self.get_size_format(self.get_dir_size(path))

    def get_size_format(self, b):
        factor = 1000
        suffix = "B"
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.1f}{unit}{suffix}"
            b /= factor
        return f"{b:.1f}{suffix}"

    def get_dir_size(self, directory):
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
                        total += self.get_dir_size(entry.path)
                    except FileNotFoundError:
                        pass
        except NotADirectoryError:
            # if `directory` isn't a directory, get the file size then
            return os.path.getsize(directory)
        except PermissionError:
            # if for whatever reason we can't open the folder, return 0
            return 0
        if total == 0:
            return 0
        # Adding 4000 seems to make it more accurate to whatever data we can't scan from within the sandbox
        return total + 4000

    def find_app_icon(self, app_id):
        icon_theme = Gtk.IconTheme.new()
        icon_theme.add_search_path("/var/lib/flatpak/exports/share/icons/")
        icon_theme.add_search_path(
            self.host_home + "/.local/share/flatpak/exports/share/icons"
        )

        try:
            icon_path = (
                icon_theme.lookup_icon(
                    app_id, None, 512, 1, self.parent_window.get_direction(), 0
                )
                .get_file()
                .get_path()
            )
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

    def get_host_updates(self):
        list = []
        output = subprocess.run(
            ["flatpak-spawn", "--host", "flatpak", "update"],
            capture_output=True,
            text=True,
            env=self.new_env,
        ).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row)

        for i in range(len(data)):
            if data[i][0].find(".") == 2:
                list.append(data[i][2])

        return list

    def get_host_system_pins(self):
        output = subprocess.run(
            ["flatpak-spawn", "--host", "flatpak", "pin"],
            capture_output=True,
            text=True,
            env=self.new_env,
        ).stdout
        data = output.strip().split("\n")
        for i in range(len(data)):
            data[i] = data[i].strip()
        return data

    def get_host_user_pins(self):
        output = subprocess.run(
            ["flatpak-spawn", "--host", "flatpak", "pin", "--user"],
            capture_output=True,
            text=True,
            env=self.new_env,
        ).stdout
        data = output.strip().split("\n")
        for i in range(len(data)):
            data[i] = data[i].strip()
        return data

    def get_host_remotes(self):
        output = subprocess.run(
            [
                "flatpak-spawn",
                "--host",
                "flatpak",
                "remotes",
                "--columns=all",
                "--show-disabled",
            ],
            capture_output=True,
            text=True,
            env=self.new_env,
        ).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row)
        return data

    def get_host_flatpaks(self):
        output = subprocess.run(
            ["flatpak-spawn", "--host", "flatpak", "list", "--columns=all"],
            capture_output=True,
            text=True,
            env=self.new_env,
        ).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split("\t")
            data.append(row)

        output = subprocess.run(
            ["flatpak-spawn", "--host", "flatpak", "list", "--columns=runtime"],
            capture_output=True,
            text=True,
            env=self.new_env,
        ).stdout
        lines = output.split("\n")
        for i in range(len(data)):
            data[i].append(lines[i])
        sorted_array = sorted(data, key=lambda item: item[0].lower())
        return sorted_array

    def get_flatpak_info(self, ref, install_type):
        output = subprocess.run(
            [
                "flatpak-spawn", "--host", "sh", "-c",
                f"flatpak info {ref} --{install_type}"
            ],
            capture_output=True,
            text=True
        ).stdout
        lines = output.strip().split("\n")
        columns = lines[0].split("\t")
        data = [columns]
        for line in lines[1:]:
            row = line.split(": ", 1)
            for i in range(len(row)):
                row[i] = row[i].strip()
            data.append(row)
        info = {}
        info["name"] = data[0][0]
        for i in range(2, len(data)):
            if data[i][0] == '':
                continue
            info[data[i][0]] = data[i][1]
        return info

    def get_dependent_runtimes(self):
        paks = self.get_host_flatpaks()
        dependent_runtimes = []
        for i in range(len(paks)):
            current = paks[i]
            try:
                if current[13] not in dependent_runtimes and current[13] != "":
                    dependent_runtimes.append(current[13])
            except:
                print("Could not get dependent runtime")
        return sorted(dependent_runtimes)

    def get_host_masks(self, user_or_system):
        output = subprocess.run(
            ["flatpak-spawn", "--host", "flatpak", "mask", f"--{user_or_system}"],
            capture_output=True,
            text=True,
            env=self.new_env,
        ).stdout
        lines = output.strip().split("\n")
        for i in range(len(lines)):
            lines[i] = lines[i].strip()
        return lines

    def mask_flatpak(self, app_id, user_or_system, remove=False):
        command = [
            "flatpak-spawn",
            "--host",
            "flatpak",
            "mask",
            f"--{user_or_system}",
            app_id,
        ]
        if remove:
            command.append("--remove")
        response = ""
        try:
            response = subprocess.run(
                command, capture_output=True, text=True, env=self.new_env
            )
        except subprocess.CalledProcessError as e:
            print(f"Error setting mask for {app_id}:\n", e)
            return 1
        if len(response.stderr) > 0:
            return 1
        return 0

    def downgrade_flatpak(self, id, ref, commit, install_type="system", mask=False):
        cmd_body = f"flatpak mask --remove --{install_type} {id}; flatpak update {ref} --commit={commit} --{install_type} -y;"
        if mask:
            cmd_body += f"flatpak mask --{install_type} {id}"
        command = [
            "flatpak-spawn",
            "--host", "pkexec",
            "sh", "-c",
            cmd_body,
        ]
        if install_type == "user":
            command.remove("pkexec")
        try:
            response = subprocess.run(
                command, capture_output=False, text=True, env=self.new_env
            ).stderr
        except subprocess.CalledProcessError as e:
            # if "note that" in response.lower():
            #     return 0
            print(f"Error setting mask for {app_id}:\n", e)
            return 1
        print(command)
        print(response)
        return 0

    def uninstall_flatpak(
        self, ref_arr, type_arr, should_trash, progress_bar=None, status_label=None
    ):
        self.uninstall_success = True
        print(ref_arr)
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
            command = [
                "flatpak-spawn",
                "--host",
                "flatpak",
                "remove",
                "-y",
                f"--{apps[i][2]}",
                apps[i][0],
            ]
            try:
                print(apps)
                if status_label:
                    GLib.idle_add(
                        status_label.set_label,
                        _("Working on {}\n{} out of {}").format(
                            apps[i][0], i + 1, len(apps)
                        ),
                    )
                subprocess.run(
                    command, capture_output=False, check=True, env=self.new_env
                )
                if progress_bar:
                    GLib.idle_add(progress_bar.set_visible, True)
                    GLib.idle_add(progress_bar.set_fraction, (i + 1.0) / len(ref_arr))
            except subprocess.CalledProcessError:
                fails.append(apps[i])

        if len(fails) > 0:  # Run this only if there is 1 or more non uninstalled apps
            pk_command = [
                "flatpak-spawn",
                "--host",
                "pkexec",
                "flatpak",
                "remove",
                "-y",
                "--system",
            ]
            print("second uninstall process")
            for i in range(len(fails)):
                if fails[i][2] == "user":
                    self.uninstall_success = False
                    continue  # Skip if app is a user install app

                pk_command.append(fails[i][0])
            try:
                print(pk_command)
                if progress_bar:
                    GLib.idle_add(progress_bar.set_visible, True)
                    GLib.idle_add(progress_bar.set_fraction, 0.9)
                subprocess.run(
                    pk_command, capture_output=False, check=True, env=self.new_env
                )
            except subprocess.CalledProcessError:
                self.uninstall_success = False

        if should_trash:
            host_paks = self.get_host_flatpaks()
            host_refs = []
            for i in range(len(host_paks)):
                host_refs.append(host_paks[i][8])

            for i in range(len(apps)):
                if apps[i][0] in host_refs:
                    print(f"{apps[i][1]} is still installed")
                else:
                    self.trash_folder(f"{self.user_data_path}{apps[i][1]}")

        if progress_bar:
            GLib.idle_add(progress_bar.set_visible, False)
            GLib.idle_add(progress_bar.set_fraction, 0.0)

    def install_flatpak(
        self, app_arr, remote, user_or_system, progress_bar=None, status_label=None
    ):
        self.install_success = True
        fails = []

        for i in range(len(app_arr)):
            command = ["flatpak-spawn", "--host", "flatpak", "install"]
            if remote != None:
                command.append(remote)
            command.append(f"--{user_or_system}")
            command.append("-y")
            command.append(app_arr[i])
            try:
                if status_label:
                    GLib.idle_add(
                        status_label.set_label,
                        _("Working on {}\n{} out of {}").format(
                            app_arr[i], i + 1, len(app_arr)
                        ),
                    )
                subprocess.run(
                    command, capture_output=False, check=True, env=self.new_env
                )
                if progress_bar:
                    GLib.idle_add(progress_bar.set_visible, True)
                    GLib.idle_add(progress_bar.set_fraction, (i + 1.0) / len(app_arr))
            except subprocess.CalledProcessError:
                fails.append(app_arr[i])

        if (len(fails) > 0) and (user_or_system == "system"):
            pk_command = [
                "flatpak-spawn",
                "--host",
                "pkexec",
                "flatpak",
                "install",
                remote,
                f"--{user_or_system}",
                "-y",
            ]
            for i in range(len(fails)):
                pk_command.append(fails[i])
            try:
                if progress_bar:
                    GLib.idle_add(progress_bar.set_visible, True)
                    GLib.idle_add(progress_bar.set_fraction, 0.9)
                subprocess.run(
                    pk_command, capture_output=False, check=True, env=self.new_env
                )
            except subprocess.CalledProcessError:
                self.install_success = False

        if (len(fails) > 0) and (user_or_system == "user"):
            self.install_success = False

        if progress_bar:
            GLib.idle_add(progress_bar.set_visible, False)
            GLib.idle_add(progress_bar.set_fraction, 0.0)

    def run_app(self, ref):
        self.run_app_error = False
        self.run_app_error_message = ""
        try:
            subprocess.run(
                ["flatpak-spawn", "--host", "flatpak", "run", ref],
                check=True,
                env=self.new_env,
                start_new_session=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            self.run_app_error_message = e.stderr.decode()
            self.run_app_error = True

    def get_install_type(self, type_arr):
        if "disabled" in type_arr:
            return "disabled"
        if "user" in type_arr:
            return "user"
        if "system" in type_arr:
            return "system"

    def snapshot_apps(
        self,
        epoch,
        app_snapshot_path_arr,
        app_version_arr,
        app_user_data_arr,
        progress_bar=None,
    ):
        if not (
            len(app_snapshot_path_arr) == len(app_version_arr) == len(app_user_data_arr)
        ):
            print(
                "error in common.snapshotApp: the lengths of app_snapshot_path_arr, app_version_arr, and app_user_data_arr do not match."
            )
            return 1

        fails = []

        for i in range(len(app_snapshot_path_arr)):
            snapshot_path = app_snapshot_path_arr[i]
            version = app_version_arr[i]
            user_data = app_user_data_arr[i]
            command = [
                "tar",
                "cafv",
                f"{snapshot_path}{epoch}_{version}.tar.zst",
                "-C",
                f"{user_data}",
                ".",
            ]

            try:
                if not os.path.exists(snapshot_path):
                    file = Gio.File.new_for_path(snapshot_path)
                    file.make_directory()
                subprocess.run(command, check=True, env=self.new_env)
                if progress_bar:
                    GLib.idle_add(progress_bar.set_visible, True)
                    GLib.idle_add(
                        progress_bar.set_fraction,
                        (i + 1.0) / len(app_snapshot_path_arr),
                    )
            except subprocess.CalledProcessError as e:
                print("error in common.snapshotApp:", e)
                fails.append(user_data)

            if (
                int(time.time()) == epoch
            ):  # Wait 1s if the snapshot is made too quickly, to prevent overriding a snapshot file
                subprocess.run(["sleep", "1s"])

        if progress_bar:
            GLib.idle_add(progress_bar.set_visible, False)
            GLib.idle_add(progress_bar.set_fraction, 0.0)

        if len(fails) > 0:
            print("These paths could not be archived:")
            for i in range(fails):
                print(fails[i])
            print("")
            return 1
        else:
            return 0
