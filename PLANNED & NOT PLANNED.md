> This document exists to inform feature requesters, contributors, and anyone else who is curious on the state of Warehouse. Make sure to give this a read before requesting any new features.

### Completed Bug fixes & Small Improvements (Ready to ship in next Minor or Bugfix update)

- Incorrect titles showing for apps with special characters
- Fix issue causing translations to never be updated
- Don't show success toast when installing a package is cancelled
- Refocus search entries upon Ctrl+F

### Planned Bugfixes & Small Improvements for some update

- Deselect All action for list views
- Fix freeze & non-apply when cancelling package version changes
- Fex switching to Install page when cancelling an attempt to install packages
- Fix selection mode being enabled when using action buttons in Data Boxes
- Fix list views resetting selection to first entry upon refresh

# Features Being Worked On

### Completed features (Ready to ship in next Minor update)

- None yet

### Planned features for some update

- Add Warehouse to "Open With" for .flatpak, .flatpakref, and .flatpakrepo
- Uninstall unused flatpaks
- Updating flatpaks
- Installation and configuration of locales
- Filter option to show outdated packages
- Filter option to show unused runtimes
- Remember Show Disabled Remotes action on startup

# Features Being Considered

- Supporting host icon themes
- Filter option for "only verified" Flatpaks
- Creation of new custom installations
- Sorting settings for packages list
- Sorting settings for snapshots list
- General settings
    - Where to save snapshots
    - Restore filters on startup
    - Restore shown page on startup
    - Restore Show Disabled Runtimes on startup

# Features *not* Planned to be Added

### Features that will *never* be added to Warehouse

- Permission management (like Flatseal)
- Full fledge package manager / app store
	- Viewing app icons and screenshots from remotes
	- Reading and leaving app reviews
	- Auto updates
- Management of any non Flatpak packages
- Supporting any repackages (apart from nixpkgs should that arise)
