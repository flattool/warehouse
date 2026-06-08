import Gtk from "gi://Gtk?version=4.0"

import { GClass, Signal, Property, from } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/simple_menu_item.ui" })
export class SimpleMenuItem extends from(Gtk.ListBoxRow, {
	chosen: Signal(),
	label: Property.readwrite.string(),
}) {}
