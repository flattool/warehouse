![Flattool Logo a simple icon of a tower crane holding a dangling letter F in front of "lattool"](https://github.com/flattool/flattool-cli/raw/main/flattool_logo-name.png)

Flattool GUI is a toolbox for managing flatpak user data, viewing flatpak app info, and batch managing installed flatpaks.

## Main Features:

1. **Viewing Flatpak info:** Flattool can show all of the info that the `flatpak list` command does, in a nice graphical window. Each item has a button to copy it as well.
2. **Managing User Data:** Flatpaks store user data in a specific location on the system, and this data is often not removed when an app is uninstalled. Flattool can uninstall an app and trash its data, just trash the data without uninstalling, or just show you if an app has user data.
3. **Batch Actions:** Flattool has a batch mode that allows fast uninstalls, user data trashing, and app ID copying to be done en mass.
4. **Leftover Data Management:** Flattool can scan the user data folder to check if there are any installed apps for the data, if there is not, then it can trash the data or attempt to install a matching flatpak.

## Important Notes:
- This is still a new project by me, a new developer, I appreciate your understanding if there are any bugs.
- Flattool assumes that flatpak user data is stored within the default location: `~/.var/app`.
- Flattool is not meant to replace flatpak; it simply sends appropriate flatpak commands for the desired actions.

## Dependencies:
To use Flattool effectively, you need to ensure the following dependencies are installed on your system:
- GIO
- [GNOME Nightly Flatpak Remote](https://wiki.gnome.org/Apps/Nightly)

## Installation Steps
1. Make sure you have the above dependencies installed
2. Head to [releases](https://github.com/flattool/flattool-gui/releases) and download `io.github.heliguy4599.FlattoolGUI.flatpak`
3. Click on it to install it with your software store or run `flatpak install /path/to/io.github.heliguy4599.FlattoolGUI.flatpak`
You're all set. Just click its icon in your app menu or run `flatpak run io.github.heliguy4599.FlattoolGUI.flatpak`
