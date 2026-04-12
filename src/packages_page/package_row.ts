import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import { Child, GClass, OnSignal, Property, from, next_idle } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/package_row.ui" })
export class PackageRow extends from(Adw.ActionRow, {
	flatpak: Property.gobject(Package, { flags: "CONSTRUCT" }),
	in_selection_mode: Property.bool(),
	selected: Property.bool(),
	_app_icon: Child<Gtk.Image>(),
}) {
	_ready(): void {
		this.#on_flatpak_change()
	}

	@OnSignal("notify::flatpak")
	#on_flatpak_change(): void {
		if (this.flatpak) {
			this._app_icon.set_from_file(this.flatpak.icon_path)
		}
	}
}
