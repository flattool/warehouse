import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"

import { Child, GClass, Property, from, next_idle } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/package_row.ui" })
export class PackageRow extends from(Adw.ActionRow, {
	flatpak: Property.gobject(Package, { flags: "CONSTRUCT" }),
	_app_icon: Child<Gtk.Image>(),
}) {
	async _ready(): Promise<void> {
		// await this.#setup_icon()
	}

	// async #setup_icon(): Promise<void> {
	// 	await next_idle()
	// 	if (!this.flatpak?.installation || this.flatpak.is_runtime) return
	// 	this._app_icon.paintable = this.flatpak.installation.icon_theme.lookup_icon(
	// 		this.flatpak.application,
	// 		["application-x-executable-symbolic"],
	// 		512,
	// 		1,
	// 		null,
	// 		Gtk.IconLookupFlags.FORCE_REGULAR,
	// 	)
	// }
}
