import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import { Child, GClass, OnSignal, PostInit, Property, from, next_idle } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/package_row.ui" })
export class PackageRow extends from(Adw.ActionRow, {
	flatpak: Property.readonly.gobject(Package),
	in_selection_mode: Property.readwrite.bool(),
	selected: Property.readwrite.bool(),
	_app_icon: Child<Gtk.Image>(),
}) {
	@OnSignal("notify::flatpak")
	@PostInit
	#on_flatpak_change(): void {
		if (this.flatpak) {
			this._app_icon.set_from_file(this.flatpak.icon_path)
		}
	}
}
