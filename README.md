# 🛠️ Warehouse

## Warehouse is a versatile toolbox for managing flatpak user data, viewing flatpak app info, and batch managing installed flatpaks.

## 🚀 Main Features:

1. **Viewing Flatpak Info:** 📋 Warehouse can display all the information provided by the `flatpak list` command in a user-friendly graphical window. Each item includes a button for easy copying.

2. **Managing User Data:** 🗑️ Flatpaks store user data in a specific system location, often left behind when an app is uninstalled. Warehouse can uninstall an app and delete its data, delete data without uninstalling, or simply show if an app has user data.

3. **Batch Actions:** ⚡ Warehouse features a batch mode for swift uninstallations, user data deletions, and app ID copying in bulk.

4. **Leftover Data Management:** 📁 Warehouse scans the user data folder to check for installed apps associated with the data. If none are found, it can delete the data or attempt to install a matching flatpak.

5. **Manage Remotes:** 📦 Installed and enabled Flatpak remotes can be deleted, and new remotes can be added.

![Various screenshots of Warehouse's abilities](screenshots.png)

## ⏬ Installation:

Warehouse is now available on Flathub! Visit your software store and search for Warehouse, or click this badge.

<a href=https://flathub.org/apps/io.github.flattool.Warehouse><img width='240' alt='Download on Flathub' src='https://dl.flathub.org/assets/badges/flathub-badge-en.png'/></a>

## 💬 Get in Contact
- We have a [Discord Server](https://discord.gg/Sq85C42Xkt) and a [Matrix Room](https://matrix.to/#/#warehouse:beeper.com) to discuss and send announcements in!
- You can always open issues, PRs, and use other GitHub features here

## ℹ️ Important Notes:
- Translators, I thank you very much for your interest and contributions, but as of now Warehouse is not accpeting any translation work until proper translation infrastructure is in place.
- This project is still in its early stages, developed by a newcomer. Your understanding of potential bugs is greatly appreciated.
- Warehouse assumes flatpak user data is located in the default directory: `~/.var/app`.
- Warehouse does not aim to replace flatpak; it simply facilitates appropriate flatpak commands for the desired actions.

## 🛠️ Installation from Repo Steps:

1. Visit the [releases](https://github.com/flattool/warehouse/releases) page and download `io.github.flattool.Warehouse.flatpak`.
2. Install it using your software store or run the following command:
   ```shell
   flatpak install /path/to/io.github.flattool.Warehouse.flatpak
   ```
You're all set! Launch the application by clicking its icon in your app menu or running:
```shell
flatpak run io.github.flattool.Warehouse
```

# A ToDo list of the current tasks being worked on
- [x] *Add threading to the addition of remotes
- [x] *!Fix no remotes status page not going away when a new remote is added
- [x] *Allow popular remotes window to be closed by pressing Escape
- [x] *Make orphaned data get size in a thread
- [ ] Somehow make installation of apps not freeze the UI
- [x] +Display dependent runtimes in app properties
- [ ]+Filter by runtimes
- [x] +Indicate apps & runtimes that are EOL
[ * = Needed before new release, + = New feature, ! = Bug fix ]
## Ideas that might get added but no promise of happening
- Installing new apps via ID match
- Remember window size
- Pin / unpin runtimes and apps
- Option to uninstall apps when removing a remote
- Make refreshing the main list after install and uninstall happen in a thread