import Adw from "gi://Adw?version=1"
import Gdk from "gi://Gdk?version=4.0"
import GLib from "gi://GLib?version=2.0"

import type { MainWindow } from "../window/main_window.js"

export class SharedVars {
	static main_window?: MainWindow
	static readonly local_share_path = GLib.getenv("HOST_XDG_DATA_HOME") || `${GLib.get_home_dir()}/.local/share`
	static readonly is_flatpak = GLib.getenv("FLATPAK_ID") === pkg.app_id
	static readonly user_data_root = `${GLib.get_home_dir()}/.var/app`
	static get clipboard(): Gdk.Clipboard {
		return (Gdk.Display.get_default() ?? new Gdk.Display()).get_clipboard()
	}

	static fancy_copy(title: string, to_copy: string): void {
		this.clipboard.set(to_copy)
		this.main_window?.add_toast(title)
	}

	private constructor() {} // no extends, no instances
}
