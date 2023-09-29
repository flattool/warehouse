# 🛠️ Warehouse

## Warehouse is a versatile toolbox for managing flatpak user data, viewing flatpak app info, and batch managing installed flatpaks.

## 🚀 Main Features:

1. **Viewing Flatpak Info:** 📋 Warehouse can display all the information provided by the `flatpak list` command in a user-friendly graphical window. Each item includes a button for easy copying.

2. **Managing User Data:** 🗑️ Flatpaks store user data in a specific system location, often left behind when an app is uninstalled. Warehouse can uninstall an app and delete its data, delete data without uninstalling, or simply show if an app has user data.

3. **Batch Actions:** ⚡ Warehouse features a batch mode for swift uninstallations, user data deletions, and app ID copying in bulk.

4. **Leftover Data Management:** 📁 Warehouse scans the user data folder to check for installed apps associated with the data. If none are found, it can delete the data or attempt to install a matching flatpak.

5. **Manage Remotes:** 📦 Installed and enabled Flatpak remotes can be deleted, and new remotes can be added.

![Various screenshots of Warehouse's abilities](screenshots.png)

## 💬 Get in Contact
- We have a [Discord Server](https://discord.gg/HVPF9Yg6) and a [Matrix Room](https://matrix.to/#/!SxRiApuHYRpJNgqxso:matrix.org) to discuss and send announcements in!
- You can always open issues, PRs, and use other GitHub features here

## ℹ️ Important Notes:
- Translators, I thank you very much for your interest and contributions, but as of now Warehouse is not accpeting any translation work until proper translation infrastructure is in place.
- This project is still in its early stages, developed by a newcomer. Your understanding of potential bugs is greatly appreciated.
- Warehouse assumes flatpak user data is located in the default directory: `~/.var/app`.
- Warehouse does not aim to replace flatpak; it simply facilitates appropriate flatpak commands for the desired actions.

## 📦 Dependencies:
To use Warehouse effectively, ensure the following dependencies are installed on your system:
- GIO
- GNOME Flatpak Runtime and SDK version 45

## 🛠️ Installation Steps:

Warehouse is now available on Flathub! Visit your software store and search for Warehouse to install it, or click this badge.



1. Make sure you have the above dependencies installed.
2. Visit the [releases](https://github.com/flattool/warehouse/releases) page and download `io.github.flattool.Warehouse.flatpak`.
3. Install it using your software store or run the following command:
   ```shell
   $ flatpak install /path/to/io.github.flattool.Warehouse.flatpak
   ```
You're all set! Launch the application by clicking its icon in your app menu or running:
```shell
$ flatpak run io.github.flattool.Warehouse
```
