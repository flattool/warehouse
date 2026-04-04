import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import { Child, GClass, OnSignal, Property, from } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"
import GLib from "gi://GLib?version=2.0"

const Base = from(Adw.ActionRow, {
	flatpak: Property.gobject(Package, { flags: "CONSTRUCT" }),
	_app_icon: Child<Gtk.Image>(),
})

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/package_row.ui" })
export class PackageRow extends Base {
	constructor(...args: ConstructorParameters<typeof Base>) {
		super(...args)
		this.#on_flatpak_change()
	}

	@OnSignal("notify::flatpak")
	#on_flatpak_change(): void {
		if (this.flatpak) {
			this._app_icon.set_from_file(this.flatpak.icon_path)
		}
	}
}
