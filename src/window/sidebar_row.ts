import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/window/sidebar_row.ui" })
export class SidebarRow extends from(Gtk.Box, {
	icon_name: Property.string(),
	text: Property.string(),
}) {}
