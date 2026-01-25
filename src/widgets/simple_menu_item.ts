import Gtk from "gi://Gtk?version=4.0"

import { GClass, Signal, Property, from } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/simple_menu_item.ui" })
@Signal("chosen")
export class SimpleMenuItem extends from(Gtk.ListBoxRow, {
	label: Property.string({ flags: "CONSTRUCT" }),
}) {}
