import GLib from "gi://GLib?version=2.0"

import type { MainWindow } from "../window/main_window.js"

export class SharedVars {
	static main_window?: MainWindow
	static readonly local_share_path = GLib.getenv("HOST_XDG_DATA_HOME") || `${GLib.get_home_dir()}/.local/share`
	static readonly is_flatpak = GLib.getenv("FLATPAK_ID") === pkg.app_id
	static readonly user_data_root = `${GLib.get_home_dir()}/.var/app`

	private constructor() {} // no extends, no instances
}
