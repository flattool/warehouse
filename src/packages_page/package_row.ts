import Gtk from "gi://Gtk?version=4.0"

import { Child, GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/package_row.ui" })
export class PackageRow extends from(Gtk.Box, {
	flatpak: Property.gobject(Package),
	_app_icon: Child<Gtk.Image>(),
}) {}
