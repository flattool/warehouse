# 🛠️ Flattool GUI

<p align="center">
  <img src="https://github.com/flattool/flattool-cli/raw/main/flattool_logo-name.png" alt="Flattool Logo">
</p>

## Flattool GUI is a versatile toolbox for managing flatpak user data, viewing flatpak app info, and batch managing installed flatpaks.

## 🚀 Main Features:

1. **Viewing Flatpak Info:** 📋 Flattool can display all the information provided by the `flatpak list` command in a user-friendly graphical window. Each item includes a button for easy copying.

2. **Managing User Data:** 🗑️ Flatpaks store user data in a specific system location, often left behind when an app is uninstalled. Flattool can uninstall an app and delete its data, delete data without uninstalling, or simply show if an app has user data.

3. **Batch Actions:** ⚡ Flattool features a batch mode for swift uninstallations, user data deletions, and app ID copying in bulk.

4. **Leftover Data Management:** 📁 Flattool scans the user data folder to check for installed apps associated with the data. If none are found, it can delete the data or attempt to install a matching flatpak.

## ℹ️ Important Notes:
- This project is still in its early stages, developed by a newcomer. Your understanding of potential bugs is greatly appreciated.
- Flattool assumes flatpak user data is located in the default directory: `~/.var/app`.
- Flattool does not aim to replace flatpak; it simply facilitates appropriate flatpak commands for the desired actions.

## 📦 Dependencies:
To use Flattool effectively, ensure the following dependencies are installed on your system:
- GIO
- [GNOME Nightly Flatpak Remote](https://wiki.gnome.org/Apps/Nightly)

## 🛠️ Installation Steps:
1. Make sure you have the above dependencies installed.
2. Visit the [releases](https://github.com/flattool/flattool-gui/releases) page and download `io.github.heliguy4599.FlattoolGUI.flatpak`.
3. Install it using your software store or run the following command:
   ```shell
   $ flatpak install /path/to/io.github.heliguy4599.FlattoolGUI.flatpak
   ```
You're all set! Launch the application by clicking its icon in your app menu or running:
```shell
$ flatpak run io.github.heliguy4599.FlattoolGUI.flatpak
```
